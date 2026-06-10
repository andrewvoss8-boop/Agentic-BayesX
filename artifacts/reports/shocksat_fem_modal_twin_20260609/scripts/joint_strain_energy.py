#!/usr/bin/env python3
"""Modal strain-energy (SE) decomposition per part group, to explain WHY the
joints are unidentifiable from the 18 calibration modes.

Sensitivity of an eigenvalue to a group stiffness scale equals twice the modal
strain energy that mode stores in that group:
    d lambda_i / d theta_g = phi_i^T K_g phi_i = 2 * SE_{i,g}
With mass-normalized nominal modes, phi_i^T K_total phi_i = lambda_i, so the
SE FRACTION is
    f_{i,g} = (phi_i^T K_g phi_i) / lambda_i = A[g][i,i] / lambda_i
and these sum to 1 over groups (+ the fixed accel-mount block). A_g = W^T K_g W
is already stored, so A[g][i,i] IS phi_i^T K_g phi_i (no new solve).

Distinguishing the two causes of low SE:
  (a) near-rigid IN the load path  -> low SE at theta=1, but softening the joint
      (theta_g down) moves frequencies a lot (large finite shift).
  (b) out of the load path         -> low SE AND softening does ~nothing.
We read the existing joints_soft probe (joints,contact x0.5) from
reduction_report.json as the finite-softening evidence for (a) vs (b).

Output: joint_strain_energy.json  (+ console table)
"""
import json
import numpy as np

rb = np.load("matrices/reduced_blocks.npz")
gnames = [str(g) for g in rb["gnames"]]
A = np.asarray(rb["A"])                       # (9, 74, 74)
A_fix = np.asarray(rb["A_fix"])               # (74, 74)
lam = np.asarray(rb["nominal_eigvals"])       # (74,)

# SE fraction of every elastic mode in every group + the fixed accel-mount block
diagA = np.stack([np.diag(A[i]) for i in range(A.shape[0])])   # (9, 74)
frac = diagA / lam[None, :]                                    # (9, 74)
fix_frac = np.diag(A_fix) / lam                                # (74,)
# sanity: fractions sum to ~1 per mode
tot = frac.sum(0) + fix_frac

pairing = json.load(open("pairing.json"))
calib = pairing["calib_test_modes"]
pairs = {p["test_mode"]: p for p in pairing["pairs"]}
midx = [pairs[t]["model_mode"] for t in calib]                 # 0-based elastic
fhz = np.sqrt(np.clip(lam, 0, None)) / (2 * np.pi)

print(f"calibration modes: {calib}")
print(f"decomposition closure (mean sum of fractions over calib modes): "
      f"{tot[midx].mean():.6f}  (should be ~1.0)\n")

# per-group summary across the 18 calibration modes
rows = []
print(f"{'group':>14} | {'mean SE%':>8} {'max SE%':>8} | "
      f"{'#modes>1%':>9} {'#modes>5%':>9} | mode of max SE")
print("-" * 78)
order = np.argsort(-frac[:, midx].mean(1))
summary = {}
for gi in order:
    g = gnames[gi]
    fr = frac[gi, midx] * 100
    jmax = midx[int(np.argmax(fr))]
    tmax = calib[int(np.argmax(fr))]
    summary[g] = dict(mean_se_pct=float(fr.mean()), max_se_pct=float(fr.max()),
                      n_modes_gt1pct=int(np.sum(fr > 1)),
                      n_modes_gt5pct=int(np.sum(fr > 5)),
                      max_se_test_mode=int(tmax),
                      max_se_freq_hz=float(fhz[jmax]))
    print(f"{g:>14} | {fr.mean():8.3f} {fr.max():8.3f} | "
          f"{int(np.sum(fr>1)):9d} {int(np.sum(fr>5)):9d} | "
          f"test {tmax} ({fhz[jmax]:.0f} Hz)")
fixfr = fix_frac[midx] * 100
print(f"{'accel_mounts':>14} | {fixfr.mean():8.3f} {fixfr.max():8.3f} | (fixed)")

# finite-softening evidence (near-rigid-in-path vs out-of-path)
red = json.load(open("reduction_report.json"))
js = red["probes"]["joints_soft"]
print(f"\nfinite-softening evidence (joints x0.5, contact x0.5, reduction probe):"
      f"\n  max |df|/f = {js['max_abs_rel_err']*100:.2f}%, "
      f"median = {js['median_abs_rel_err']*100:.2f}%  over "
      f"{js['n_modes_compared']} modes < 280 Hz")

joints_mean = summary.get("joints", {}).get("mean_se_pct", 0)
contact_mean = summary.get("contact", {}).get("mean_se_pct", 0)
top_id = max(summary.items(), key=lambda kv: kv[1]["mean_se_pct"])
verdict = (
    "joints carry NONZERO but small modal SE across the 18 modes -> they ARE in "
    "the load path, just near-rigid (low local sensitivity at theta=1); the "
    "finite x0.5 softening moving frequencies confirms in-path, not "
    "out-of-path." if joints_mean > 0.05 and js["max_abs_rel_err"] > 0.005 else
    "joints carry ~zero modal SE AND softening barely moves frequencies -> "
    "genuinely out of the modal load path.")
print(f"\nVERDICT: {verdict}")

json.dump(dict(calib_modes=calib, group_summary=summary,
               accel_mount_mean_se_pct=float(fixfr.mean()),
               joints_soft_probe=js, closure_mean=float(tot[midx].mean()),
               verdict=verdict),
          open("joint_strain_energy.json", "w"), indent=1)
print("\nwrote joint_strain_energy.json")
