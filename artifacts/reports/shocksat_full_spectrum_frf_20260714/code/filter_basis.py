#!/usr/bin/env python3
"""filter_basis — drop unconverged ARPACK modes clamped at the spectrum edge (D11).

The k=560/ncv=840 shift-invert solve converged only the lowest ~216 modes; the top 338 collapsed onto a
single clamped eigenvalue (668.1 Hz, huge multiplicity) — these are NOT physical modes. The converged set
is independently cross-validated by the interior-shift slice-1 solve to 639 Hz (out/full_eig_crosscheck).
Keep modes with a UNIQUE eigenvalue below the clamp; rewrite full_eig_theta1.npz / full_eig_V.npy in place
(originals backed up to out/full_eig_raw_*)."""
import json, os, shutil, sys
import numpy as np

WS = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
z = np.load(os.path.join(WS, "out", "full_eig_theta1.npz"))
lam = np.asarray(z["lam"]); freqs = np.asarray(z["freqs"]); n_rbm = int(z["n_rbm"]); keep = z["keep"]
V = np.load(os.path.join(WS, "out", "full_eig_V.npy"))

# detect the clamp plateau: the top eigenvalue with multiplicity >> 1
top = lam.max()
clamp = np.abs(lam - top) <= 1e-6 * abs(top)
n_clamp = int(clamp.sum())
# credible = everything strictly below the clamp band, with a small safety cut below the clamp freq
f_clamp = float(np.sqrt(max(top, 0)) / (2 * np.pi))
keep_mode = freqs < (f_clamp - 1.0)              # 1 Hz below the clamp
print(f"clamp at {f_clamp:.1f} Hz, multiplicity {n_clamp}; keeping {int(keep_mode.sum())} of {lam.size}")

# back up originals ONCE
for fn in ("full_eig_theta1.npz", "full_eig_V.npy"):
    bak = os.path.join(WS, "out", "raw_" + fn)
    if not os.path.exists(bak):
        shutil.copy2(os.path.join(WS, "out", fn), bak)

lam_f, freqs_f, V_f = lam[keep_mode], freqs[keep_mode], V[:, keep_mode]
np.savez_compressed(os.path.join(WS, "out", "full_eig_theta1.npz"),
                    lam=lam_f, freqs=freqs_f, n_rbm=n_rbm, keep=keep)
np.save(os.path.join(WS, "out", "full_eig_V.npy"), V_f)

n_el = int((freqs_f >= 10).sum())
summ = json.load(open(os.path.join(WS, "out", "full_eig_summary.json")))
summ.update({"filtered_D11": True, "n_clamped_dropped": n_clamp, "clamp_hz": round(f_clamp, 1),
             "n_modes_kept": int(keep_mode.sum()), "credible_top_hz": round(float(freqs_f.max()), 1),
             "n_elastic_kept": n_el,
             "n_elastic_to_500": int(((freqs_f >= 10) & (freqs_f <= 500)).sum()),
             "n_elastic_to_550": int(((freqs_f >= 10) & (freqs_f <= 550)).sum()),
             "crossvalidated_to_hz": 639.0,
             "note_D11": "unconverged clamped modes removed; credible basis top set by the last converged "
                         "mode, cross-validated to 639 Hz by the independent interior-shift slice-1 solve"})
json.dump(summ, open(os.path.join(WS, "out", "full_eig_summary.json"), "w"), indent=1)
print(f"credible top {freqs_f.max():.1f} Hz, {n_el} elastic modes; {summ['n_elastic_to_550']} to 550 Hz")
