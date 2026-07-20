#!/usr/bin/env python3
"""Gate K — synthetic 1-DOF kernel/operator correctness (quantity_contracts; decisions D6).

Test: the window operator W applied to a unit-residue SDOF of known zeta must reproduce the ANALYTIC
apparent-broadening prediction (an SDOF with zeta_app = zeta + zeta_w(fn), zeta_w(f) = 1/(2 pi f tau),
tau = 0.164066 s) at the frame's exact DFT bins, to <= 5% peak-height error. Applied at BOTH zeta = 0.3%
(light, the physical case) and zeta = 5% (broad). D6: the card's 'broad peak ~unchanged' clause was a
Hann-kernel expectation; the ACTUAL exponential window adds zeta_w at every width, so the broad-peak test is
also against the analytic zeta+zeta_w prediction; the 'vs unwindowed' change is REPORTED for transparency.
fn is placed exactly ON a DFT bin so bin-offset sampling does not contaminate the operator test.
"""
import json, os, sys, time
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import wforward as WF

t0 = time.time()
OUT = os.path.join(WF.WS, "out")
df = WF.FS / WF.NFRAME
k100 = int(round(100.0 / df))
fn = k100 * df                                   # 99.69 Hz, exactly a bin
fc = np.arange(max(1, k100 - 25), k100 + 26) * df   # +/- ~51 Hz around the mode, exact bins

res = {"fn_hz": fn, "df_hz": df, "tau_s": WF.TAU_WIN, "sigma_w": WF.SIGMA_W,
       "zeta_w_at_fn": float(WF.zeta_w(fn))}
checks = {}
for name, z in (("light", 0.003), ("broad", 0.05)):
    z_app = z + float(WF.zeta_w(fn))
    Hw = np.abs(WF.sdof_windowed(fn, z, fc))                 # operator output
    Ha = np.abs(WF.sdof_naive(fn, z_app, fc))                # analytic apparent-zeta prediction
    Hn = np.abs(WF.sdof_naive(fn, z, fc))                    # unwindowed (reporting only)
    pw, pa, pn = float(Hw.max()), float(Ha.max()), float(Hn.max())
    err = (pw - pa) / pa
    # curve-level agreement across the peak neighborhood (stronger than peak-only)
    curve_err = float(np.median(np.abs(Hw - Ha) / Ha))
    checks[name] = {"zeta": z, "zeta_app_analytic": z_app,
                    "peak_windowed": pw, "peak_analytic_app": pa, "peak_unwindowed": pn,
                    "peak_err_frac_vs_analytic": err, "median_curve_err_frac": curve_err,
                    "change_vs_unwindowed_frac": (pw - pn) / pn}
    print(f"[{name}] zeta={z:.4f} -> zeta_app={z_app:.4f}; peak W={pw:.4f} analytic={pa:.4f} "
          f"unwindowed={pn:.4f}; err vs analytic {err:+.4%}; vs unwindowed {(pw-pn)/pn:+.2%}")

res.update({
    "light_peak_err_frac": checks["light"]["peak_err_frac_vs_analytic"],
    "broad_peak_change_frac": checks["broad"]["peak_err_frac_vs_analytic"],
    "broad_change_vs_unwindowed_frac_REPORTED": checks["broad"]["change_vs_unwindowed_frac"],
    "checks": checks,
})
res["pass"] = abs(res["light_peak_err_frac"]) <= 0.05 and abs(res["broad_peak_change_frac"]) <= 0.05 \
    and checks["light"]["median_curve_err_frac"] <= 0.05
res["runtime_s"] = round(time.time() - t0, 2)
with open(os.path.join(OUT, "gate_K.json"), "w") as f:
    json.dump(res, f, indent=1)
with open(os.path.join(OUT, "runtime_log.jsonl"), "a") as f:
    f.write(json.dumps({"step": "gate_K", "active_s": res["runtime_s"]}) + "\n")
print("GATE K:", "PASS" if res["pass"] else "FAIL")
