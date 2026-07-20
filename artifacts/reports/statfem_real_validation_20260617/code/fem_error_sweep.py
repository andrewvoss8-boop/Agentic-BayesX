#!/usr/bin/env python3
"""Simulation A — controlled FEM-error sweep: map the whole-FRF convergence boundary (Card A, decisions_log D15).

Why: the whole-FRF magnitude likelihood is multimodal/singular on REAL data (NUTS R-hat 104, TMCMC 129, faithful
M2 2.58) yet the SYNTHETIC companion CONVERGED (R-hat 1.002). The only difference is the FEM-vs-truth model-form
error delta -- the synthetic truth came from the SAME model (delta = 0). This sweep makes delta a CONTROLLED knob.

SYNTHETIC truth (labeled) = FEM(theta=1) accelerance with a per-mode FREQUENCY perturbation:
    lambda_k -> lambda_k * (1 + delta * xi_k)^2 ,   xi_k = +-1 (fixed seed)
i.e. peak-MISALIGNMENT model-form error of magnitude delta, with the SAME mode shapes (so no global-theta escape).
Plain-ShockSat reduced forward. Calibrate the FAITHFUL additive Schneider M2 (whole log|H|) against each delta
with the UNPERTURBED forward, under TMCMC (>=4 independent runs).

Output: out/fem_error_sweep.json -- cross-run R-hat, sigma_w, log-evidence vs delta. delta=0 is the CONTROL
(must reproduce the synthetic-study convergence). The delta where R-hat crosses 1.05 / sigma_w runs away = the
pre-test design number ("the FEM must align peaks within ~delta* for the whole-FRF likelihood to be usable").
"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import realfrf as rf
import schneider_faithful as sf
import tmcmc as T

WS = Path(__file__).resolve().parent.parent
DELTAS = [0.0, 0.01, 0.02, 0.05, 0.10, 0.20]
N_OBS = 8
C_TRUE = sf.GAIN_C0           # synthetic gain = prior center (consistent setup)


def perturbed_truth(R, resp_rows, drive, freqs, delta, xi, zeta, c_true, sigma_meas, seed):
    """log|accelerance g/lbf| from FEM(theta=1) with per-mode frequency perturbation (1+delta*xi)^2, same shapes."""
    K = R.A_fix + R.A.sum(0)                                   # theta = 1
    lam, Q = np.linalg.eigh(K); lam = np.clip(lam, 1e-9, None)
    lam_p = lam * (1.0 + delta * xi) ** 2
    eta = 2.0 * zeta
    Us = resp_rows @ Q; Ud = drive @ Q
    w = 2 * np.pi * np.asarray(freqs)
    g = (1 + 1j * eta) * lam_p[None, :] - (w ** 2)[:, None]
    H = -(w ** 2)[:, None] * np.einsum("sk,k,fk->fs", Us.astype(complex), Ud.astype(complex), 1.0 / g)
    lm = np.log(np.abs(H) / rf.G_IN_S2) + c_true
    rng = np.random.default_rng(seed)
    return lm + rng.normal(0.0, sigma_meas, lm.shape)


def run(n=2000, n_runs=4, force=False):
    outp = WS / "out" / "fem_error_sweep.json"
    if outp.exists() and not force:
        print(f"[skip] {outp.name}"); return json.loads(outp.read_text())
    t0 = time.time()
    fg = sf.IDENT4
    R = rf.load_reduced()
    meas = rf.reprocess_measured(list(range(1, rf.N_ACCEL_RECORDERS + 1)))
    ch = rf.build_channels(R, meas["daq"])
    didx = {d: i for i, d in enumerate(meas["daq"])}
    fr = meas["freqs"]; fb = (fr >= rf.BAND[0]) & (fr <= rf.BAND[1]); freqs = fr[fb]
    dr = np.array([meas["dyn_range"][didx[d]] for d in ch.daq])
    obs_pos = np.argsort(dr)[::-1][:N_OBS]; obs_pos = np.sort(obs_pos)
    resp_obs = ch.rows[obs_pos]; coords_obs = ch.coords[obs_pos]; drive = ch.drive_row
    # fixed per-mode perturbation signs (same across deltas -> isolates magnitude)
    nmode = R.A_fix.shape[0]
    xi = np.where(np.random.default_rng(7).random(nmode) < 0.5, -1.0, 1.0)
    # covariance pieces are delta-independent -> build ONCE
    pieces = sf.build_arm_pieces("M2", R, freqs, coords_obs, resp_obs, drive, fg)
    logprior, sample_prior, d = sf.make_prior("M2", len(fg))

    sweep = []
    for delta in DELTAS:
        tgt = perturbed_truth(R, resp_obs, drive, freqs, delta, xi, sf.ZETA, C_TRUE, sf.SIGMA_MEAS, seed=123)
        loglike = sf.make_loglike("M2", R, freqs, tgt, resp_obs, drive, fg, pieces)
        runs, diag = T.run_independent(loglike, logprior, sample_prior, n=n, n_runs=n_runs)
        S = np.concatenate([r["samples"] for r in runs])
        sw = np.exp(S[:, len(fg) + 1])
        conv = diag["max_rhat"] <= 1.05 and diag["min_ess"] >= 200 and diag["div_frac"] < 0.02
        row = {"delta": delta, "max_rhat": diag["max_rhat"], "min_ess": diag["min_ess"],
               "converged": bool(conv), "sigma_w_med": float(np.median(sw)),
               "sigma_w_lo": float(np.percentile(sw, 2.5)), "sigma_w_hi": float(np.percentile(sw, 97.5)),
               "log_evidence_mean": diag["log_evidence_mean"], "log_evidence_std": diag["log_evidence_std"]}
        sweep.append(row)
        print(f"  delta={delta*100:4.0f}%  R-hat {diag['max_rhat']:7.3f}  ESS {diag['min_ess']:6.0f}  "
              f"sigma_w {row['sigma_w_med']:5.2f}  logZ {diag['log_evidence_mean']:9.1f}  "
              f"converged={conv}", flush=True)

    # convergence boundary delta*: largest delta still converged / first delta that fails
    conv_deltas = [r["delta"] for r in sweep if r["converged"]]
    delta_star = max(conv_deltas) if conv_deltas else None
    rec = {"simulation": "A_controlled_FEM_error_sweep", "synthetic": True,
           "perturbation": "per-mode lambda_k*(1+delta*xi_k)^2, xi=+-1 fixed; same mode shapes (peak misalignment)",
           "n_obs_channels": N_OBS, "n_band_freqs": int(len(freqs)), "free_groups": [rf.GNAMES[i] for i in fg],
           "tmcmc": {"n": n, "n_runs": n_runs}, "deltas_pct": [x * 100 for x in DELTAS],
           "sweep": sweep, "delta_star_converged_pct": (delta_star * 100 if delta_star is not None else None),
           "runtime_s": time.time() - t0}
    (WS / "out").mkdir(exist_ok=True)
    outp.write_text(json.dumps(rec, indent=2))
    print(f"A FEM-error sweep DONE: convergence boundary delta* = "
          f"{rec['delta_star_converged_pct']}% (largest delta still converged) | {rec['runtime_s']:.0f}s -> {outp}")
    return rec


if __name__ == "__main__":
    kw = {}
    for a in sys.argv[1:]:
        if a.startswith("--n="): kw["n"] = int(a.split("=")[1])
        elif a == "--force": kw["force"] = True
    run(**kw)
