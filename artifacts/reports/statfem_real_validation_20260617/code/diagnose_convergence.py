#!/usr/bin/env python3
"""Diagnose the M0/M3 non-convergence on the real FRF and test principled fixes (Card A §6/§12).

Finding so far (split0): M0 & M3 NOT-YET-CONVERGED (R-hat ~104-115, ESS 2, 0 div) = multimodal; M3 sigma_d
ran away to ~9.8. Hypotheses: (A) the discrepancy variance runaway flattens theta -> fix sigma_d at the
realized floor; (B) the under-identified 9-theta is over-parameterised -> downselect to the 4 SE-identifiable
groups (bottom_box, cross_beam, plates, top_box). Short 4-chain runs (400+400) for a real R-hat read.

Output: out/diagnose_convergence.json. Launch detached.
"""
from __future__ import annotations
import json, sys, time
from pathlib import Path
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import realfrf as rf
import real_arms as ra
from run_cell import select_split

WS = Path(__file__).resolve().parent.parent
OUT = WS / "out"
IDENT4 = [2, 4, 6, 8]            # bottom_box, cross_beam, plates, top_box (GNAMES indices)
FLOOR = 1.726                    # realized discrepancy floor sigma_d0 (identifiability.json)


def setup(split=0, nobs=8, zeta=0.01):
    R = rf.load_reduced()
    meas = rf.reprocess_measured(list(range(1, rf.N_ACCEL_RECORDERS + 1)))
    ch = rf.build_channels(R, meas["daq"])
    obs, held, didx = select_split(ch, meas, nobs, split)
    fr = meas["freqs"]; bm = (fr >= rf.BAND[0]) & (fr <= rf.BAND[1]); freqs = fr[bm]
    obs_daq = [ch.daq[k] for k in obs]
    Hobs = np.array([np.abs(meas["H"][didx[d]][bm]) for d in obs_daq]).T
    target = np.log(np.maximum(Hobs, 1e-30))
    rr = ch.rows[obs]; co = ch.coords[obs]
    c0 = float(np.median(target - rf.fem_logmag(R, freqs, np.ones(9), rr, ch.drive_row, zeta=zeta)))
    return R, freqs, target, rr, ch.drive_row, co, c0


def run(label, R, freqs, target, rr, drive, co, c0, **kw):
    t0 = time.time()
    flat, diag = ra.run_arm(R=R, freqs=freqs, target_obs=target, resp_rows_obs=rr, drive_row=drive,
                            coords_obs=co, c0=c0, num_warmup=400, num_samples=400, num_chains=4, **kw)
    conv = diag["max_rhat"] <= 1.05 and diag["min_ess"] >= 200 and diag["div_frac"] < 0.02
    rec = {"label": label, "arm": kw.get("arm"), "free_groups": kw.get("free_groups"),
           "fixed_sigma_d": kw.get("fixed_sigma_d"), "converged": bool(conv), "diag": diag,
           "gain_med": float(np.median(flat["gain"])), "runtime_s": time.time() - t0}
    if "sigma_d" in flat:
        rec["sigma_d_med"] = float(np.median(flat["sigma_d"]))
    print(f"{label:38s} conv={conv} R-hat {diag['max_rhat']:6.2f} ESS {diag['min_ess']:5.0f} "
          f"div {diag['divergences']:3d} sigma_d {rec.get('sigma_d_med', kw.get('fixed_sigma_d', 0)):.2f} "
          f"{rec['runtime_s']:.0f}s")
    return rec


def main():
    R, freqs, target, rr, drive, co, c0 = setup()
    configs = [
        ("M3_full9_sigmad_fixedFloor", dict(arm="M3", fixed_sigma_d=FLOOR)),
        ("M3_ident4_sigmad_sampled",   dict(arm="M3", free_groups=IDENT4)),
        ("M3_ident4_sigmad_fixedFloor", dict(arm="M3", free_groups=IDENT4, fixed_sigma_d=FLOOR)),
        ("M0_ident4",                  dict(arm="M0", free_groups=IDENT4)),
        ("M1_ident4_sigmad_sampled",   dict(arm="M1", free_groups=IDENT4)),
    ]
    res = []
    for label, kw in configs:
        try:
            res.append(run(label, R, freqs, target, rr, drive, co, c0, **kw))
        except Exception as e:
            print(f"{label}: ERROR {type(e).__name__}: {e}")
            res.append({"label": label, "error": f"{type(e).__name__}: {e}"})
    OUT.mkdir(exist_ok=True)
    (OUT / "diagnose_convergence.json").write_text(json.dumps(
        {"split": 0, "nobs": 8, "zeta": 0.01, "realized_floor": FLOOR, "ident4_groups": IDENT4,
         "ident4_names": [rf.GNAMES[i] for i in IDENT4], "configs": res}, indent=2))
    print("wrote out/diagnose_convergence.json")


if __name__ == "__main__":
    main()
