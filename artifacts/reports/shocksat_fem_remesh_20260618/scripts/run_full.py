#!/usr/bin/env python3
"""Full-calibration NUTS run: ALL 18 calibration-clean modes held in.

Purpose: (a) the headline theta posterior (the held-out designs answer the
prediction question; this answers "what does ALL usable data say about the
part-group stiffnesses"), (b) the posterior-mean theta for the FEMAP
cross-check deck and the reduced-vs-full posterior validation.
Outputs: nuts_full_samples.npz, convergence_full.json, theta_full.json,
         femap_handoff/theta_posterior_mean.json
"""
import json
import sys
import time
import numpy as np

sys.path.insert(0, "scripts")
import run_nuts as RN

t0 = time.time()
calib = RN.calib_modes
print(f"full calibration on {len(calib)} modes: {calib}", flush=True)
samples, div = RN.run_nuts(calib, use_mac=False, seed=42)
conv = RN.convergence(samples, div, 1000, 4)
flat = RN.flatten(samples)
gnames = [str(g) for g in RN.rb["gnames"]]

rows = RN.predict(samples, calib)          # in-sample fit (labeled as such)
np.savez_compressed("nuts_full_samples.npz", gnames=np.array(gnames), **flat)
json.dump(conv, open("convergence_full.json", "w"), indent=1)

theta_med = {g: float(np.median(flat["theta"][:, i]))
             for i, g in enumerate(gnames)}
theta_mean = {g: float(np.mean(flat["theta"][:, i]))
              for i, g in enumerate(gnames)}
out = dict(design="full_in_sample", held_in=calib,
           in_sample_rows=rows,
           theta_median=theta_med, theta_mean=theta_mean,
           theta_ci={g: [float(np.percentile(flat["theta"][:, i], 2.5)),
                         float(np.percentile(flat["theta"][:, i], 97.5))]
                     for i, g in enumerate(gnames)},
           sigma_f_median=float(np.median(flat["sigma_f"])),
           sigma_f_ci=[float(np.percentile(flat["sigma_f"], 2.5)),
                       float(np.percentile(flat["sigma_f"], 97.5))],
           convergence=dict(worst_rhat=conv["worst_rhat"],
                            min_ess=conv["min_ess"],
                            divergences=conv["divergences"],
                            gate_pass=conv["gate_pass"]),
           runtime_s=round(time.time() - t0, 1))
json.dump(out, open("theta_full.json", "w"), indent=1)
json.dump(theta_mean, open("femap_handoff/theta_posterior_mean.json", "w"),
          indent=1)
print(f"done {out['runtime_s']}s; gate "
      f"{'PASS' if conv['gate_pass'] else 'FAIL'} "
      f"(rhat {conv['worst_rhat']:.4f}, ess {conv['min_ess']:.0f}, "
      f"div {conv['divergences']})", flush=True)
print(json.dumps(theta_med, indent=1))
