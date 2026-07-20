#!/usr/bin/env python3
"""Posterior / held-out sensitivity arms for the modal twin.

Varies the assumptions most likely to move the held-out QOI (band design):
  A. theta prior width NSIG in {0.15, 0.25, 0.40}   (ledger A8)
  B. likelihood: frequency-only vs frequency+MAC     (ledger A10)
  C. held-in band edge: <=120 Hz vs <=150 Hz         (ledger A12)
Reports held-out predictive coverage, median |err|, and the joints/top_box
posterior medians for each arm. Fewer draws (600/600) -- this is a
decision-sensitivity scan, not the headline run.
"""
import json
import time
import numpy as np
import run_nuts as RN

t0 = time.time()
def log(m): print(f"[{time.time()-t0:7.1f}s] {m}", flush=True)

mfreqs = RN.mfreqs
calib = RN.calib_modes
gnames = [str(g) for g in RN.rb["gnames"]]


def arm(name, nsig, use_mac, fmax):
    RN.NSIG = nsig
    held_in = [t for t in calib if mfreqs[t - 1] <= fmax]
    held_out = [t for t in calib if mfreqs[t - 1] > fmax]
    samples, div = RN.run_nuts(held_in, use_mac, nwarm=600, ndraw=600)
    conv = RN.convergence(samples, div, 600, 4)
    rows = RN.predict(samples, held_out)
    flat = RN.flatten(samples)
    med = {g: float(np.median(flat["theta"][:, i]))
           for i, g in enumerate(gnames)}
    cov = float(np.mean([r["covers_pred"] for r in rows]))
    mederr = float(np.median([abs(r["err_pct"]) for r in rows]))
    log(f"{name}: cov {cov:.2f} med|err| {mederr:.2f}% "
        f"rhat {conv['worst_rhat']:.3f} div {conv['divergences']} "
        f"joints {med['joints']:.2f} top_box {med['top_box']:.2f}")
    return dict(name=name, nsig=nsig, use_mac=use_mac, fmax=fmax,
                n_held_in=len(held_in), n_held_out=len(held_out),
                coverage_pred=cov, median_abs_err_pct=mederr,
                worst_rhat=conv["worst_rhat"], gate_pass=conv["gate_pass"],
                divergences=conv["divergences"], theta_median=med)


ARMS = [
    ("prior_sd_0.15", 0.15, False, 120.0),
    ("baseline_sd_0.25", 0.25, False, 120.0),
    ("prior_sd_0.40", 0.40, False, 120.0),
    ("freq+MAC_sd_0.25", 0.25, True, 120.0),
    ("band_le150_sd_0.25", 0.25, False, 150.0),
]
results = [arm(*a) for a in ARMS]
RN.NSIG = 0.25
json.dump(dict(arms=results), open("sensitivity.json", "w"), indent=1)
log("done -> sensitivity.json")
