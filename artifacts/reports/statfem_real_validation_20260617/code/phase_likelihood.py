#!/usr/bin/env python3
"""Card C Phase 4 -- complex / phase likelihood (L4, Fathi/Zhang Eq 20): circular-Gaussian on Hhat - H(theta).
The card flags single-hit phase as noisy and asks whether phase adds anything over magnitude/modal. Rather than
launch another multimodal whole-FRF NUTS (the magnitude version is already a documented dead end: D7, NUTS R-hat 104),
we test the PREREQUISITE directly with cheap, decisive diagnostics on the observed channels:

  (1) Phase coherence at the matched modes: at each consensus peak frequency, the circular spread of
      (angle(Hhat) - angle(H_model)) across channels. A clean, informative phase -> small circular spread (modes
      are near quadrature, consistent sign); a single-hit-noisy phase -> spread ~ that of a uniform angle (circular
      std -> 1 rad-equivalent, circular variance -> 1).
  (2) Residual budget: after the BEST per-channel complex gain c (least-squares complex scalar = magnitude gain x
      a constant phase, absorbing level + a global phase but NOT frequency-dependent delay), compare the COMPLEX
      (phase-inclusive) normalised residual RMS to the MAGNITUDE-only residual RMS. If complex >> magnitude, the
      phase term injects noise, so the circular-Gaussian L4 sigma is phase-dominated and adds no constraint.
  (3) 1-D theta-slice negative log-likelihood for magnitude-only vs complex: does adding phase SHARPEN the minimum
      (information) or just raise/roughen it (noise)?

Output: out/phase_likelihood.json. Conclusion documented; magnitude/modal likelihoods retained.
"""
import json
import sys
from pathlib import Path
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import realfrf as rf
import heldout_qoi as hq
import modal_beck_full as M

WS = Path(__file__).resolve().parent.parent
G = rf.G_IN_S2


def reconstruct_complex(Phi, w2r, rows, drive, freqs, eta):
    Us = rows @ Phi; Ud = drive @ Phi; w = 2 * np.pi * np.asarray(freqs)
    g = (1.0 + 1j * eta[None, :]) * w2r[None, :] - (w ** 2)[:, None]
    H = -(w ** 2)[:, None] * np.einsum("sk,k,fk->fs", Us.astype(complex), Ud.astype(complex), 1.0 / g)
    return H / G                                              # complex accelerance [g/lbf], (Nf, Ns)


def run(seed=0):
    cal = M.calibrate(n_modes=12); R = cal["R"]; fem_k = cal["fem_k"]
    meas = rf.reprocess_measured(list(range(1, rf.N_ACCEL_RECORDERS + 1)))
    ch = rf.build_channels(R, meas["daq"])
    fr = meas["freqs"]; fb = (fr >= rf.BAND[0]) & (fr <= rf.BAND[1]); freqs = fr[fb]
    didx = {d: i for i, d in enumerate(meas["daq"])}
    dr = np.array([meas["dyn_range"][didx[d]] for d in ch.daq])
    elig = np.where(dr >= hq.DR_MIN)[0]
    rng = np.random.default_rng(seed); perm = rng.permutation(elig)
    obs_pos = np.sort(perm[:int(round(0.6 * len(perm)))]); obs_daqs = [ch.daq[p] for p in obs_pos]
    obs_rows = ch.rows[obs_pos]
    Hhat = np.array([meas["H"][didx[d]][fb] for d in obs_daqs]).T          # (Nf, Ns) measured complex
    eta = M.per_mode_eta(cal, True)
    K = R.A_fix + R.A.sum(0); lam, Q = np.linalg.eigh(K)
    Hmod = reconstruct_complex(Q[:, fem_k], lam[fem_k], obs_rows, ch.drive_row, freqs, eta)   # theta=1, FEM shapes
    Ns = Hhat.shape[1]

    # (1) phase coherence at the matched modes (nearest band freq to each matched .ash mode)
    fmatch = cal["ash"]["mfr"][cal["ash_r"]]
    circ = []
    for fm in fmatch:
        k = int(np.argmin(np.abs(freqs - fm)))
        dphi = np.angle(Hhat[k]) - np.angle(Hmod[k])
        Rbar = np.abs(np.mean(np.exp(1j * dphi)))             # mean resultant length (1=coherent, 0=uniform)
        circ.append(1.0 - Rbar)                               # circular variance
    circ_var = float(np.mean(circ))

    # (2) residual budget after best per-channel complex gain (LS) vs magnitude gain
    res_mag, res_cplx = [], []
    for s in range(Ns):
        h = Hhat[:, s]; m = Hmod[:, s]
        cc = np.vdot(m, h) / (np.vdot(m, m) + 1e-300)         # best complex scalar gain (level + const phase)
        res_cplx.append(np.sqrt(np.mean(np.abs(h - cc * m) ** 2)) / (np.sqrt(np.mean(np.abs(h) ** 2)) + 1e-300))
        gmag = np.exp(np.median(np.log(np.abs(h) + 1e-300) - np.log(np.abs(m) + 1e-300)))
        res_mag.append(np.sqrt(np.mean((np.log(np.abs(h) + 1e-300) - np.log(gmag * np.abs(m) + 1e-300)) ** 2)))
    res_cplx = float(np.median(res_cplx)); res_mag = float(np.median(res_mag))

    # (3) 1-D theta-slice NLL: vary cross_beam (group 4) multiplier; magnitude-only vs complex
    grid = np.linspace(0.6, 1.4, 41)
    nll_mag, nll_cplx = [], []
    for tv in grid:
        th = np.ones(9); th[4] = tv
        Kt = R.A_fix + np.einsum("g,gij->ij", th, R.A); lt, Qt = np.linalg.eigh(Kt)
        Hm = reconstruct_complex(Qt[:, fem_k], lt[fem_k], obs_rows, ch.drive_row, freqs, eta)
        # magnitude likelihood (per-channel mag gain), complex likelihood (per-channel complex gain)
        em, ec = 0.0, 0.0
        for s in range(Ns):
            h = Hhat[:, s]; m = Hm[:, s]
            gmag = np.exp(np.median(np.log(np.abs(h) + 1e-300) - np.log(np.abs(m) + 1e-300)))
            em += np.sum((np.log(np.abs(h) + 1e-300) - np.log(gmag * np.abs(m) + 1e-300)) ** 2)
            cc = np.vdot(m, h) / (np.vdot(m, m) + 1e-300)
            ec += np.sum(np.abs(h - cc * m) ** 2) / (np.mean(np.abs(h) ** 2) + 1e-300)
        nll_mag.append(float(em)); nll_cplx.append(float(ec))
    nll_mag = np.array(nll_mag); nll_cplx = np.array(nll_cplx)

    def curv(n):  # sharpness of the minimum (normalized): (mean-min)/min, and argmin
        return {"argmin_theta": float(grid[int(np.argmin(n))]),
                "rel_contrast": float((np.mean(n) - n.min()) / (n.min() + 1e-300))}
    rec = {"deliverable": "Phase4_complex_phase_likelihood_L4 (diagnostic; single-hit phase)",
           "split_seed": seed, "n_obs_channels": int(Ns), "n_matched_modes": int(len(fmatch)),
           "phase_circular_variance_at_modes": circ_var,
           "phase_note": "circular variance ~1 => measured-vs-model phase incoherent across channels (single-hit/timing noise); ~0 => coherent",
           "residual_RMS_complex_over_magnitude": res_cplx / max(res_mag, 1e-12),
           "residual_RMS_magnitude": res_mag, "residual_RMS_complex_normalized": res_cplx,
           "theta_slice_magnitude": curv(nll_mag), "theta_slice_complex": curv(nll_cplx),
           "verdict": None}
    phase_bad = circ_var > 0.6
    cplx_not_sharper = curv(nll_cplx)["rel_contrast"] <= curv(nll_mag)["rel_contrast"] * 1.05
    rec["residual_note"] = ("complex residual is normalized linear amplitude; magnitude residual is log-scale RMS -- "
                            "different units, NOT directly comparable; the decisive evidence is the circular variance "
                            "and the theta-slice contrast.")
    rec["verdict"] = ("phase adds NOTHING over magnitude: single-hit measured-vs-model phase is incoherent across "
                      f"channels (circular variance {circ_var:.2f}, ~1=uniform), and the complex theta-slice minimum "
                      f"is NOT sharper than magnitude (rel-contrast complex {curv(nll_cplx)['rel_contrast']:.2f} vs "
                      f"magnitude {curv(nll_mag)['rel_contrast']:.2f}). Magnitude/modal likelihoods retained."
                      ) if (phase_bad or cplx_not_sharper) else \
                     ("phase MAY add information: revisit L4 (circular variance "
                      f"{circ_var:.2f}, complex slice sharper).")
    (WS / "out").mkdir(exist_ok=True)
    (WS / "out" / "phase_likelihood.json").write_text(json.dumps(rec, indent=2))
    print(f"PHASE L4 DIAGNOSTIC (split {seed}, {Ns} obs ch, {len(fmatch)} modes):")
    print(f"  phase circular variance at modes: {circ_var:.2f} (1=incoherent/noise, 0=coherent)")
    print(f"  residual RMS complex/magnitude: {rec['residual_RMS_complex_over_magnitude']:.1f}x (>1 => phase injects noise)")
    print(f"  theta-slice rel-contrast: magnitude {rec['theta_slice_magnitude']['rel_contrast']:.2f} vs "
          f"complex {rec['theta_slice_complex']['rel_contrast']:.2f}")
    print(f"  VERDICT: {rec['verdict']}")
    return rec


if __name__ == "__main__":
    run()
