#!/usr/bin/env python3
"""Pre-test design figure (Tufte-linted). Reads out/pretest_figdata.npz + pretest_design.json (no recompute).
A: drumhead mode |Z| over the top plate + current (1) vs recommended plate sensors -> current sits off the antinode.
B: buy-down curve = normal-QOI band factor vs # plate accelerometers, with current + fully-resolved floor.
C: recommended drive by drumhead-band coverage."""
from __future__ import annotations
import json
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

WS = Path(__file__).resolve().parent.parent
d = json.load(open(WS / "out" / "pretest_design.json"))
z = np.load(WS / "out" / "pretest_figdata.npz", allow_pickle=True)
C_SEL, C_CUR, C_BAND, C_FLOOR = "#c8862b", "#b03030", "#1f4e79", "#2b7a2b"

fig, ax = plt.subplots(1, 3, figsize=(15, 4.9))

# A: plate mode shape + sensors
a = ax[0]
xy = z["plate_xy"]; amp = z["plate_absZ"]; amp = amp / (amp.max() + 1e-30)
sc = a.scatter(xy[:, 0], xy[:, 1], c=amp, s=12, cmap="viridis", alpha=0.8)
sel = z["sel_xy"]; cur = z["cur_xy"]
a.scatter(sel[:, 0], sel[:, 1], marker="o", facecolors="none", edgecolors=C_SEL, s=90, linewidths=1.8,
          label=f"recommended plate accels ({len(sel)})")
if cur.size:
    a.scatter(cur[:, 0], cur[:, 1], marker="X", color=C_CUR, s=110, label=f"current plate-Z sensor ({len(cur)})")
a.set_aspect("equal"); a.set_xlabel("x [in]"); a.set_ylabel("y [in]")
a.set_title(f"A. drumhead mode {float(z['top_mode_hz']):.0f} Hz |Z| (norm.) + sensors", fontsize=10, loc="left")
a.legend(fontsize=7.5, loc="upper right", framealpha=0.9)
cb = fig.colorbar(sc, ax=a, fraction=0.046, pad=0.04); cb.set_label("|Z| (normalized)", fontsize=8)

# B: buy-down curve
b = ax[1]
ns = z["ns"]; band = z["band"]; floor = float(z["floor"]); cur_band = float(z["cur_band"])
b.plot(ns, band, "-o", color=C_BAND, ms=5)
b.axhline(floor, color=C_FLOOR, ls="--", lw=1.2)
b.text(ns[-1], floor + 0.06, f"fully-resolved floor {floor:.1f}x", color=C_FLOOR, fontsize=8, ha="right")
b.scatter([0], [cur_band], color=C_CUR, s=70, zorder=5)
b.text(0.3, cur_band, f" current {cur_band:.1f}x (1 sensor)", color=C_CUR, fontsize=8, va="center")
b.text(ns[-1], band[-1] - 0.18, f"{int(ns[-1])} accels -> {band[-1]:.1f}x\n"
       f"({d['buy_down_pct_of_floor_at_12_sensors']:.0f}% of the way to floor)", color=C_BAND, fontsize=8, ha="right")
b.set_xlabel("# added plate accelerometers"); b.set_ylabel("normal-QOI 95% band factor")
b.set_title("B. buy-down: plate accels shrink the NORMAL band", fontsize=10, loc="left")
b.set_ylim(min(floor - 0.4, band.min() - 0.3), cur_band + 0.4)
b.spines[["top", "right"]].set_visible(False)

# C: recommended drive coverage
c = ax[2]
rec = [(s.split(":")[0], int(s.split(":")[1])) for s in z["rec_drives"]]
labels = [r[0] for r in rec]; vals = [r[1] for r in rec]
y = np.arange(len(labels))[::-1]
cols = [C_SEL if labels[i] == "+Y" else "#8aa" for i in range(len(labels))]
c.barh(y, vals, color=cols)
for yi, l, v in zip(y, labels, vals):
    c.text(v + 0.1, yi, f"{l} ({v})", va="center", fontsize=9)
c.set_yticks([]); c.set_xlabel("# drumhead-band peaks the drive coherently excites")
c.set_title("C. recommended DRIVE: +Y best (adds unique 230.6 Hz)", fontsize=10, loc="left")
c.spines[["top", "right", "left"]].set_visible(False)

cap = (f"Pre-test design for the >200 Hz plate/drumhead test (run shocksat_netcg_method_selection_20260701; NO NUTS). "
       f"Net-CG NORMAL is driven by the partial-cancellation drumhead modes {d['target_drumhead_modes_hz']} Hz whose "
       f"SHAPES are unmeasured (current plate = 1 Z-sensor, off the antinode). {int(ns[-1])} well-placed plate accels "
       f"cut the normal band 5.4x->3.5x (~35%, 73% to the fully-resolved floor 2.8x); the modes are not individually "
       f"separable by point sensors (measure their net combination = the QOI). Best drive: +Y. Uniform-mass proxy, "
       f"reduced-model shapes, captured-energy (EfI-style) placement.")
fig.text(0.01, -0.03, cap, fontsize=7.4, va="top", wrap=True)
fig.tight_layout(rect=[0, 0.02, 1, 1])
outp = WS / "figures" / "fig_pretest.png"
fig.savefig(outp, dpi=150, bbox_inches="tight"); plt.close(fig)
print(f"wrote {outp}")
