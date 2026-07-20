"""Value of L5 updating for the MODAL-FREQUENCY QOI (the balancing positive to the amplitude negative, D17).
Two distinct 'value' questions on held-out MODES (random mode split):
  (a) value of the MODEL+updating vs CLIMATOLOGY (guess each held-out mode's freq from the population of OBSERVED
      measured mode freqs) -> CRPS skill.
  (b) value of UPDATING vs the NOMINAL (as-received, theta=1) FEM -> does calibrating theta reduce the held-out
      modal-frequency error?
Output: out/freq_value_seed<seed>.json.
"""
from __future__ import annotations
import json, sys, time
from types import SimpleNamespace
from pathlib import Path
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import realfrf as rf
import modal_feature as mf
import score as SC

WS = Path(__file__).resolve().parent.parent
OUT = WS / "out"


def run(seed=0, obs_frac=0.6, warmup=1000, samples=1000, chains=4, write=True):
    t0 = time.time()
    R = rf.load_reduced()
    meas = rf.reprocess_measured(list(range(1, rf.N_ACCEL_RECORDERS + 1)))
    ch = rf.build_channels(R, meas["daq"])
    meas_f, _ = mf.extract_measured_modes(meas, ch)
    pairs, _ = mf.match(R, meas_f)
    idx = np.array([p[0] for p in pairs]); wmeas = np.array([p[1] for p in pairs])
    rng = np.random.default_rng(seed); perm = rng.permutation(len(idx))
    n_obs = int(round(obs_frac * len(idx)))
    obs = np.sort(perm[:n_obs]); ho = np.sort(perm[n_obs:])

    theta_post, sigw2, cdiag = mf.calibrate_modal(R, idx[obs], wmeas[obs],
                                                  seed=20260617, warmup=warmup, samples=samples, chains=chains)
    sub = np.linspace(0, theta_post.shape[0] - 1, 300).astype(int)
    # twin per held-out mode: calibrated FEM frequency distribution
    fem_post = np.array([mf.fem_modes_np(R, theta_post[s]) for s in sub])     # (300, nmodes)
    fem_nom = mf.fem_modes_np(R, np.ones(9))                                  # nominal FEM
    clim = wmeas[obs]                                                         # climatology = observed mode freqs

    twin_crps, clim_crps, cov, nom_err, cal_err = [], [], [], [], []
    for j in ho:
        mode = idx[j]; truth = wmeas[j]
        tw = fem_post[:, mode]
        s = SC.score_qoi(tw, truth)
        twin_crps.append(s["crps"]); cov.append(s["covered"])
        clim_crps.append(SC.score_qoi(clim, truth)["crps"])
        nom_err.append(abs(fem_nom[mode] - truth) / truth * 100)             # % freq err, nominal FEM
        cal_err.append(abs(np.median(tw) - truth) / truth * 100)             # % freq err, calibrated
    tc, cc = float(np.mean(twin_crps)), float(np.mean(clim_crps))
    rec = {"deliverable": "value of L5 updating for held-out MODAL FREQUENCY",
           "split_seed": seed, "n_observed_modes": int(len(obs)), "n_heldout_modes": int(len(ho)),
           "calib_converged": bool(cdiag["converged"]),
           "twin_vs_climatology": {"twin_crps_hz": tc, "clim_crps_hz": cc, "crps_skill": float(1 - tc / cc),
                                   "twin_coverage": float(np.mean(cov))},
           "value_of_updating_vs_nominal": {"nominal_fem_median_abs_freq_err_pct": float(np.median(nom_err)),
                                            "calibrated_median_abs_freq_err_pct": float(np.median(cal_err))},
           "runtime_s": time.time() - t0}
    if write:
        OUT.mkdir(exist_ok=True)
        (OUT / f"freq_value_seed{seed:02d}.json").write_text(json.dumps(rec, indent=2))
    v = rec["twin_vs_climatology"]; u = rec["value_of_updating_vs_nominal"]
    print(f"seed {seed}: obs {len(obs)} / held-out {len(ho)} modes; calib conv {cdiag['converged']}")
    print(f"  FREQUENCY twin vs climatology: CRPS-skill {v['crps_skill']:+.2f} (twin {v['twin_crps_hz']:.1f} Hz / "
          f"clim {v['clim_crps_hz']:.1f} Hz), coverage {v['twin_coverage']:.2f}")
    print(f"  value of UPDATING: nominal-FEM freq err {u['nominal_fem_median_abs_freq_err_pct']:.2f}% -> "
          f"calibrated {u['calibrated_median_abs_freq_err_pct']:.2f}%")
    print(f"  runtime {rec['runtime_s']:.0f}s")
    return rec


if __name__ == "__main__":
    seed = int(sys.argv[1]) if len(sys.argv) > 1 else 0
    run(seed=seed)
