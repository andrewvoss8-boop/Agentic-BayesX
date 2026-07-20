#!/usr/bin/env python3
"""PIVOTAL shape diagnosis (start of the remodeling work): on the CLEAN modal data, is the per-channel amplitude
scatter σ≈1.6 REDUCIBLE by better mode shapes, or is it near-field/non-modal (irreducible)?

Predict each held-out sensor's peak |H| two ways, SAME modal construction / SAME split / SAME measured poles+damping,
differing ONLY in the SHAPE used:
  (i)  FEM shapes      Q[:,k_r]            (what the twin uses now → σ_FEM)
  (ii) measured .ash shapes  psi_r = pinv(G)·meas_shape_r   (the 'shape oracle' → σ_meas)
Per-mode complex modal scales a_r fit by weighted complex LSQ on OBSERVED channels only (held-out FRF never used).
σ = std of the held-out peak log-amplitude error. If σ_meas << σ_FEM → shapes are the reducible lever (remodel
toward measured shapes); if σ_meas ≈ σ_FEM → near-field/irreducible (Card G/D16 finding), remodeling can't close it.
Also reports the FEM-vs-.ash MAC per matched mode (which modes the FEM shape gets wrong = where to remodel).
Reuses Card A ash_match.npz (G, meas_shape, MAC pairs). Output: out/shape_diag.json + console.
"""
from __future__ import annotations
import json, sys
from pathlib import Path
import numpy as np
sys.path.insert(0, str(Path(__file__).resolve().parent))
import realfrf as rf
import psd_forward as pf
from modal_multiref import MODAL_REFS, CACHE, N_MODAL
import multiref_frf as mr

WS = Path(__file__).resolve().parent.parent
CARD_A_OUT = WS.parent / "statfem_real_validation_20260617" / "out"
REF = "m_xpos_990x"


def run(seed=0, obs_frac=0.9, ridge=1e-3):
    R = rf.load_reduced()
    ch = rf.build_channels(R, [d for d in range(1, rf.N_ACCEL_RECORDERS + 1) if d not in rf.BAD_DAQ])
    am = np.load(CARD_A_OUT / "ash_match.npz", allow_pickle=True)
    G = am["G"]; meas_shape = am["meas_shape"]; mfr = am["mfr"]
    pairs = [(int(p[0]), int(p[1]), float(p[2])) for p in am["pairs"]]
    damp = np.load(WS / "data" / "measured_modes.npz", allow_pickle=True)["damp"] / 100.0
    ridx = [r for r, k, _ in pairs]; kidx = [k for r, k, _ in pairs]; macs = np.array([m for _, _, m in pairs])
    psi = np.array([np.linalg.pinv(G) @ meas_shape[:, r] for r in ridx]).T          # (74, nmode) measured shapes
    K = R.A_fix + np.einsum("g,gij->ij", np.ones(9), R.A)
    lam, Q = np.linalg.eigh(K); Qsel = Q[:, kidx]                                    # (74, nmode) FEM shapes (θ=1)

    c = dict(np.load(CACHE / f"{REF}.npz", allow_pickle=True)); c["daq"] = [int(d) for d in c["daq"]]
    freqs = c["freqs"]; w = 2 * np.pi * freqs
    tau = -(N_MODAL - 1) / (rf.FS * np.log(mr.PROC["exp_end"]))
    zr = damp[ridx] + 1.0 / (2 * np.pi * mfr[ridx] * tau)                            # measured ζ + window, per mode
    eta = 2.0 * zr; wr = mfr[ridx] * 2 * np.pi
    drow = pf.drive_row_for(R, tuple(float(x) for x in c["xyz"]), str(c["axis"]))

    # common sensors present in cache + mappable; split (seed) 90/10
    common = [d for d in ch.daq if d in c["daq"]]
    pos = {d: i for i, d in enumerate(ch.daq)}; cidx = {d: c["daq"].index(d) for d in common}
    rng = np.random.default_rng(seed); perm = rng.permutation(len(common))
    n_obs = int(round(obs_frac * len(common)))
    obs = [common[i] for i in perm[:n_obs]]; ho = [common[i] for i in perm[n_obs:]]
    coh = c["coherence"]

    def basis(daqs, shapes):
        rows = np.array([ch.rows[pos[d]] for d in daqs])
        sc = rows @ shapes; dc = drow @ shapes                                       # (Ns,nmode), (nmode,)
        denom = (1 + 1j * eta)[None, :] * (wr ** 2)[None, :] - (w ** 2)[:, None]     # (Nf,nmode)
        return (-(w ** 2)[:, None, None]) * (sc[None, :, :] * dc[None, None, :]) / denom[:, None, :]

    def predict_sigma(shapes):
        M_obs = basis(obs, shapes); M_ho = basis(ho, shapes)
        H_obs = np.array([np.abs(c["H1"][cidx[d]]) * np.exp(1j * np.angle(c["H1"][cidx[d]])) for d in obs]).T  # (Nf,nobs)
        Wq = np.array([coh[cidx[d]] for d in obs]).T
        nm = shapes.shape[1]
        A = M_obs.reshape(-1, nm); b = H_obs.reshape(-1); sw = np.sqrt(np.clip(Wq.reshape(-1), 0, None))
        Aw = A * sw[:, None]; bw = b * sw
        AhA = Aw.conj().T @ Aw + ridge * np.eye(nm) * np.real(np.trace(Aw.conj().T @ Aw)) / nm
        a_r = np.linalg.solve(AhA, Aw.conj().T @ bw)
        H_ho_pred = M_ho @ a_r
        H_ho_tru = np.array([c["H1"][cidx[d]] for d in ho]).T
        err = np.log(np.abs(H_ho_pred).max(0) + 1e-300) - np.log(np.abs(H_ho_tru).max(0) + 1e-300)  # peak log-err
        return float(np.std(err)), float(np.median(np.abs(err)) * 20 / np.log(10))

    s_fem, db_fem = predict_sigma(Qsel)
    s_meas, db_meas = predict_sigma(psi)
    rec = {"deliverable": "PIVOTAL: is per-channel amplitude scatter reducible by better shapes? (clean modal data)",
           "reference": REF, "seed": seed, "obs_frac": obs_frac, "n_modes_matched": len(ridx),
           "n_obs": len(obs), "n_ho": len(ho),
           "MAC_fem_vs_ash": {"median": float(np.median(macs)), "min": float(macs.min()),
                              "n_below_0.7": int((macs < 0.7).sum()), "n_below_0.5": int((macs < 0.5).sum()),
                              "worst_modes_hz": [round(float(mfr[r]), 1) for r in
                                                 [ridx[i] for i in np.argsort(macs)[:5]]]},
           "sigma_FEM_shape": round(s_fem, 2), "sigma_MEASURED_shape": round(s_meas, 2),
           "heldout_median_abs_db_FEM": round(db_fem, 1), "heldout_median_abs_db_MEAS": round(db_meas, 1),
           "reducible_by_shapes": bool(s_meas < 0.6 * s_fem),
           "sigma_needed_to_beat_fem6": 0.35}
    (WS / "out" / "shape_diag.json").write_text(json.dumps(rec, indent=2))
    print(f"PIVOTAL shape diagnosis ({REF}, seed{seed}, {obs_frac*100:.0f}% train): {len(ridx)} matched modes")
    print(f"  FEM-vs-.ash MAC: median {np.median(macs):.2f}, min {macs.min():.2f}, "
          f"{(macs<0.7).sum()} modes <0.7, {(macs<0.5).sum()} <0.5; worst @ {rec['MAC_fem_vs_ash']['worst_modes_hz']} Hz")
    print(f"  held-out peak σ (log):  FEM-shape {s_fem:.2f}   MEASURED-shape {s_meas:.2f}   (need ≲0.35 to beat FEM+6dB)")
    print(f"  held-out median|err|:   FEM {db_fem:.1f} dB     MEASURED {db_meas:.1f} dB")
    print(f"  => shapes are {'a REDUCIBLE lever (remodel toward measured)' if rec['reducible_by_shapes'] else 'NOT the (reducible) lever — near-field/non-modal dominates'}")
    return rec


if __name__ == "__main__":
    run()
