#!/usr/bin/env python3
"""PACKET headline: many per-channel FRF overlays — ORIGINAL FEM vs measured DATA vs UPDATED FEM (straight-up
deterministic; physics modal participations φ_s·φ_d, ONE global gain, NO per-channel fit). +X reference.
  original = FEM frequencies + nominal 1% damping
  updated  = MEASURED frequencies (the frequency calibration) + MEASURED per-mode damping  [validated corrections]
Reuses the saved baseline FEM modes (no eigensolve). Output: figures/frf_comparison_grid.png + out/frf_comparison.json
(per-channel log|H| correlation original vs updated, the value of the corrections)."""
from __future__ import annotations
import json, sys
from pathlib import Path
import numpy as np
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
sys.path.insert(0, str(Path(__file__).resolve().parent))
from modal_multiref import CACHE
WS = Path(__file__).resolve().parent.parent

z = np.load(WS / "out" / "edits" / "baseline" / "modes.npz", allow_pickle=True)
Phi = z["Phi"]; pd = z["pd"]; ffem = z["freqs_fem"]; daq = [int(d) for d in z["daq"]]
c = dict(np.load(CACHE / "m_xpos_990x.npz", allow_pickle=True)); c["daq"] = [int(d) for d in c["daq"]]
f = c["freqs"]; w = 2 * np.pi * f; ci = {d: c["daq"].index(d) for d in daq}
Hdata = np.array([c["H1"][ci[d]] for d in daq]).T                       # (Nf,Nc) measured
mm = np.load(WS / "data" / "measured_modes.npz", allow_pickle=True); mfr = mm["freqs"]; mdp = mm["damp"] / 100.0
j = np.array([int(np.argmin(np.abs(mfr - x))) for x in ffem])
tau = -(122880 - 1) / (250000.0 * np.log(0.05))


def synth(wr, eta):
    den = (1 + 1j * eta)[None, :] * (wr ** 2)[None, :] - (w ** 2)[:, None]
    H = (-(w ** 2)[:, None, None]) * (Phi[None, :, :] * pd[None, None, :]) / den[:, None, :]  # (Nf,Nc,nm)
    H = H.sum(2)                                                         # physics participations (no per-ch fit)
    g = np.median(np.log(np.abs(Hdata) + 1e-30) - np.log(np.abs(H) + 1e-30))   # ONE global gain
    return H * np.exp(g)


H_orig = synth(ffem * 2 * np.pi, 2.0 * (0.01 + 1.0 / (2 * np.pi * ffem * tau)))           # FEM freq + 1% damping
H_upd = synth(mfr[j] * 2 * np.pi, 2.0 * (mdp[j] + 1.0 / (2 * np.pi * mfr[j] * tau)))       # measured freq + damping
def corr(A): return np.array([np.corrcoef(np.log(np.abs(A[:, k])+1e-30), np.log(np.abs(Hdata[:, k])+1e-30))[0, 1] for k in range(len(daq))])
co, cu = corr(H_orig), corr(H_upd)
rec = {"reference": "+X", "n_channels": len(daq), "median_logH_corr_original": round(float(np.median(co)), 3),
       "median_logH_corr_updated": round(float(np.median(cu)), 3),
       "frac_channels_updated_better": round(float(np.mean(cu > co)), 2),
       "note": "deterministic physics participations + 1 global gain; updated = measured freq + damping (calibration)"}
(WS / "out" / "frf_comparison.json").write_text(json.dumps(rec, indent=2))
print(json.dumps(rec, indent=2))

# 12-channel grid spanning the per-channel correlation (worst..best of the updated)
order = np.argsort(cu); pick = order[np.linspace(0, len(daq) - 1, 12).astype(int)]
fig, axes = plt.subplots(3, 4, figsize=(13.5, 8), sharex=True)
for ax, k in zip(axes.ravel(), pick):
    ax.plot(f, np.abs(Hdata[:, k]), color="#222222", lw=1.1, label="data")
    ax.plot(f, np.abs(H_orig[:, k]), color="#1f77b4", lw=0.9, ls="--", label="original FEM")
    ax.plot(f, np.abs(H_upd[:, k]), color="#d2691e", lw=0.9, label="updated FEM")
    ax.set_xscale("log"); ax.set_yscale("log"); ax.set_xlim(45, 260)
    ax.set_title(f"ch {daq[k]}  (log|H| corr: orig {co[k]:.2f} → upd {cu[k]:.2f})", fontsize=7.5)
    ax.spines[["top", "right"]].set_visible(False); ax.tick_params(labelsize=6.5)
axes[0, 0].legend(fontsize=7, frameon=False, loc="lower left")
for a in axes[-1, :]:
    a.set_xlabel("frequency (Hz, log)", fontsize=8)
for a in axes[:, 0]:
    a.set_ylabel("|H| (g/lbf, log)", fontsize=8)
cap = (f"ShockSat +X FRFs: measured DATA vs ORIGINAL FEM (FEM freq + 1% damping) vs UPDATED FEM (measured freq + "
       f"measured per-mode damping). Deterministic — physics modal participations φ_s·φ_d, ONE global units-gain, NO "
       f"per-channel fit. 12 channels spanning the per-channel agreement. Median log|H| correlation: original "
       f"{rec['median_logH_corr_original']} → updated {rec['median_logH_corr_updated']} "
       f"({rec['frac_channels_updated_better']*100:.0f}% of channels improve). The updating aligns the peaks "
       f"(frequency) and sets peak heights (damping); residual per-channel shape error remains the documented wall.")
fig.text(0.01, 0.005, cap, fontsize=7.2, wrap=True, va="bottom")
fig.tight_layout(rect=[0, 0.05, 1, 1])
out = WS / "figures" / "frf_comparison_grid.png"; fig.savefig(out, dpi=145, bbox_inches="tight"); plt.close(fig)
print(f"wrote {out}")
