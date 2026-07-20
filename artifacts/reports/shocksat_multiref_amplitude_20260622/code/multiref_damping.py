#!/usr/bin/env python3
"""Card G follow-up — replace the flat global ζ=1% with NASA's MEASURED per-mode modal damping (+ window), and
re-score the held-out per-channel AMPLITUDE skill. Flat 1% is unphysical: the NASA modal survey measured per-mode
ζ over a ~0.06-1.05% range (~17x), and peak height ∝ 1/ζ. We use the measured per-mode ζ (measured_modes.npz['damp'])
with the exponential-window artifact added correctly (η_k = η_struct,k + 2·ζ_w(f_k), via Card F's
dampcorr_qoi.fem_logmag_batch_permode), on the SAME splits/scorer as the headline.

Arms (FEM-forward held-out peak |H| under +X; θ from frequencies, NUTS; gain on observed; CRPS-skill vs climatology):
  flat1pct   — uniform ζ=1% (the unacceptable baseline)
  flat1pct_w — uniform ζ=1% + window
  permode_w  — NASA measured per-mode ζ + window   (the proper model)
Output: out/multiref_damping.json.
"""
from __future__ import annotations
import json, sys, time
from types import SimpleNamespace
from pathlib import Path
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import realfrf as rf
import modal_feature as mf
import heldout_qoi as hq
import dampcorr_qoi as dc
import score as SC

WS = Path(__file__).resolve().parent.parent
OUT = WS / "out"
HARD = {4, 27, 38, 40, 52, 69, 92, 98}


def run(seeds=(0, 1, 2), obs_frac=0.6, warmup=1000, samples=1000, chains=4, n_draws=300):
    t0 = time.time()
    R = rf.load_reduced()
    meas = rf.reprocess_measured(list(range(1, rf.N_ACCEL_RECORDERS + 1)))
    ch = rf.build_channels(R, meas["daq"])
    fr = meas["freqs"]; fb = (fr >= rf.BAND[0]) & (fr <= rf.BAND[1]); freqs = fr[fb]
    didx = {d: i for i, d in enumerate(meas["daq"])}
    tau = -(rf.PROC["N"] - 1) / (rf.FS * np.log(rf.PROC["exp_end"]))
    zeta_struct, used = dc.build_zeta_struct(R, meas, SimpleNamespace(daq=ch.daq))
    eta_uniform = np.full(R.A.shape[1], 2.0 * rf.ZETA_NOM)
    eta_struct = 2.0 * zeta_struct
    qoi_peak = rf.core.qoi_peak

    per_seed = []
    for seed in seeds:
        dr = np.array([meas["dyn_range"][didx[d]] for d in ch.daq])
        elig = np.where(dr >= hq.DR_MIN)[0]
        rng = np.random.default_rng(seed); perm = rng.permutation(elig)
        n_obs = int(round(obs_frac * len(perm)))
        obs_pos = np.sort(perm[:n_obs]); ho_pos = np.sort(perm[n_obs:])
        obs_daqs = [ch.daq[p] for p in obs_pos]; ho_daqs = [ch.daq[p] for p in ho_pos]
        hard_ho = np.array([1 if d in HARD else 0 for d in ho_daqs])

        meas_f, _ = mf.extract_measured_modes(meas, SimpleNamespace(daq=obs_daqs))
        pairs, _ = mf.match(R, meas_f)
        idx = np.array([p[0] for p in pairs]); whz = np.array([p[1] for p in pairs])
        theta_post, _, cdiag = mf.calibrate_modal(R, idx, whz, seed=20260617, warmup=warmup, samples=samples, chains=chains)
        sub = np.linspace(0, theta_post.shape[0] - 1, min(theta_post.shape[0], n_draws)).astype(int)
        thsub = theta_post[sub]
        allr = np.vstack([ch.rows[obs_pos], ch.rows[ho_pos]]); n_o = len(obs_pos)

        tru_obs = np.log(np.abs(np.array([meas["H"][didx[d]][fb] for d in obs_daqs])) + 1e-300).T
        wflat = np.array([meas["weight"][didx[d]][fb] for d in obs_daqs]).T.ravel()
        peak_tru_ob = np.array([qoi_peak(np.exp(tru_obs[:, k])) for k in range(n_o)])
        peak_tru_ho = np.array([qoi_peak(np.abs(meas["H"][didx[d]][fb])) for d in ho_daqs])
        clim = peak_tru_ob.copy()

        def arm(eta, use_tau):
            lm = dc.fem_logmag_batch_permode(R, freqs, thsub, allr, ch.drive_row, eta, tau if use_tau else None)
            peak_ho = np.zeros((len(sub), len(ho_pos))); peak_ob = np.zeros((len(sub), n_o))
            for j in range(len(sub)):
                c = hq.wmedian((tru_obs - lm[j, :, :n_o]).ravel(), wflat)
                po = np.exp(lm[j, :, :n_o] + c); ph = np.exp(lm[j, :, n_o:] + c)
                for k in range(n_o): peak_ob[j, k] = qoi_peak(po[:, k])
                for k in range(len(ho_pos)): peak_ho[j, k] = qoi_peak(ph[:, k])
            sig = float(np.std(np.log(np.median(peak_ob, 0) + 1e-300) - np.log(peak_tru_ob + 1e-300)))
            drng = np.random.default_rng(seed + 5)
            twin = peak_ho * np.exp(drng.normal(0, sig, peak_ho.shape))
            m = hard_ho == 0
            ct = np.mean([SC.crps_sample(twin[:, k], peak_tru_ho[k]) for k in np.where(m)[0]])
            cc = np.mean([SC.crps_sample(clim, peak_tru_ho[k]) for k in np.where(m)[0]])
            cov = np.mean([SC.coverage_width(twin[:, k], peak_tru_ho[k])["covered"] for k in np.where(m)[0]])
            # median absolute peak bias (dB) vs measured, held-out
            bias_db = float(np.median([abs(20 * np.log10(np.median(peak_ho[:, k]) / peak_tru_ho[k])) for k in np.where(m)[0]]))
            return {"crps_skill_vs_clim": float(1 - ct / cc), "coverage": float(cov),
                    "sigma_qoi_log": sig, "median_abs_peak_bias_db": bias_db}
        res = {"flat1pct": arm(eta_uniform, False), "flat1pct_w": arm(eta_uniform, True),
               "permode_w": arm(eta_struct, True)}
        per_seed.append({"seed": int(seed), "calib_converged": bool(cdiag["converged"]),
                         "n_modes_with_measured_zeta": len(used), "arms": res})
        print(f"seed {seed}: conv {cdiag['converged']} | flat1% {res['flat1pct']['crps_skill_vs_clim']:+.2f} "
              f"| flat1%+win {res['flat1pct_w']['crps_skill_vs_clim']:+.2f} "
              f"| PER-MODE+win {res['permode_w']['crps_skill_vs_clim']:+.2f} "
              f"(bias dB {res['flat1pct']['median_abs_peak_bias_db']:.1f}->{res['permode_w']['median_abs_peak_bias_db']:.1f})")

    def mean(arm, key="crps_skill_vs_clim"):
        return float(np.mean([s["arms"][arm][key] for s in per_seed]))
    rec = {"deliverable": "held-out amplitude skill: flat 1% vs NASA measured PER-MODE modal damping (+window)",
           "zeta_measured_range_pct": [float(np.min(zeta_struct[zeta_struct < rf.ZETA_NOM]) * 100) if (zeta_struct < rf.ZETA_NOM).any() else None,
                                       float(np.max(zeta_struct) * 100)],
           "n_modes_with_measured_zeta": len(used),
           "mean_skill": {a: mean(a) for a in ("flat1pct", "flat1pct_w", "permode_w")},
           "mean_coverage": {a: mean(a, "coverage") for a in ("flat1pct", "flat1pct_w", "permode_w")},
           "mean_peak_bias_db": {a: mean(a, "median_abs_peak_bias_db") for a in ("flat1pct", "flat1pct_w", "permode_w")},
           "per_seed": per_seed, "runtime_s": time.time() - t0,
           "note": "FEM-FORWARD arm (a blind prediction model). The measured-RESIDUE headline method already carries "
                   "per-mode damping implicitly via R_{d,k}, so this isolates the value of measured ζ for the forward."}
    (OUT / "multiref_damping.json").write_text(json.dumps(rec, indent=2))
    print(f"\nMEAN held-out skill: flat1% {rec['mean_skill']['flat1pct']:+.2f} | flat1%+win "
          f"{rec['mean_skill']['flat1pct_w']:+.2f} | PER-MODE+win {rec['mean_skill']['permode_w']:+.2f}")
    print(f"MEAN |peak bias| dB: flat1% {rec['mean_peak_bias_db']['flat1pct']:.1f} -> PER-MODE "
          f"{rec['mean_peak_bias_db']['permode_w']:.1f} | runtime {rec['runtime_s']:.0f}s")
    return rec


if __name__ == "__main__":
    run()
