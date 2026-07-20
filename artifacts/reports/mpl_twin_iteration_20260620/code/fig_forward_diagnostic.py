#!/usr/bin/env python3
"""Phase-0 diagnostic figure: measured vs as-received-FEM-predicted gain-free transmissibility |T_a(f)| at each
held-out accel location, with the log-correlation and band-GRMS in each panel. Small multiples, shared log-f axis.
Shows the KEY FINDING (D6): the nominal FEM transmissibility forward is essentially uncorrelated with the measured
|T| (a dense modal forest + unknown acoustic load), even though the modal frequencies are present. Tufte gate
applied (data-ink, no chartjunk, log frequency, direct labels, caption carries the quantity + takeaway).
"""
from __future__ import annotations
import json, sys
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

sys.path.insert(0, str(Path(__file__).resolve().parent))
import mpl_calibrate as CAL

WS = Path(__file__).resolve().parents[1]; FIG = WS / "figures"; OUT = WS / "out"
FIG.mkdir(exist_ok=True)
HELD = CAL.HELD


def grms(logT, f): return float(np.sqrt(np.trapz(np.exp(logT) ** 2, f)))


def main():
    P = CAL.precompute(); P["groups_used"] = P["groups"]
    f = P["fgrid"]; th = np.ones(len(P["groups"]))
    rows = []
    fig, axes = plt.subplots(2, 3, figsize=(13, 7.2))
    axes = axes.ravel()
    for k, loc in enumerate(HELD):
        ax = axes[k]
        Tm = np.maximum(P["Tmeas"][loc], 1e-6); lm = np.log(Tm)
        lp = CAL.predict_logT_np(P, th, 0.01, loc); Tp = np.exp(lp)
        lc = float(np.corrcoef(lm, lp)[0, 1])
        rows.append({"location": loc, "log_corr": round(lc, 3),
                     "grms_meas": round(grms(lm, f), 3), "grms_pred": round(grms(lp, f), 3)})
        ax.semilogy(f, Tm, color="#222222", lw=1.3)
        ax.semilogy(f, Tp, color="#c1452b", lw=1.1, alpha=0.85)
        ax.set_xscale("log")
        # direct labels at the right edge
        ax.text(f[-1], Tm[-1], " measured", color="#222222", fontsize=8, va="center")
        ax.text(f[-1], Tp[-1], " FEM (nominal)", color="#c1452b", fontsize=8, va="center")
        ax.set_title(f"{loc}   log-corr={lc:+.2f}   GRMS meas {grms(lm,f):.2f} / FEM {grms(lp,f):.2f}",
                     fontsize=9, loc="left")
        ax.set_xlim(f[0], f[-1]); ax.grid(True, which="both", lw=0.3, alpha=0.3)
        for s in ("top", "right"): ax.spines[s].set_visible(False)
        if k % 3 == 0: ax.set_ylabel("|T| = √(PSD_a/PSD_shield)  (–)")
        if k >= 3: ax.set_xlabel("frequency (Hz, log)")
    # summary panel: correlation bar
    ax = axes[5]
    lcs = [r["log_corr"] for r in rows]
    ax.barh(range(len(HELD)), lcs, color=["#777" if abs(v) < 0.3 else "#c1452b" for v in lcs])
    ax.axvline(0, color="k", lw=0.6)
    ax.set_yticks(range(len(HELD))); ax.set_yticklabels(HELD, fontsize=8)
    ax.set_xlim(-1, 1); ax.set_xlabel("log-corr(measured, FEM-nominal |T|)")
    ax.set_title("uncorrelated forward (|corr|≈0 everywhere)", fontsize=9, loc="left")
    for s in ("top", "right"): ax.spines[s].set_visible(False)
    fig.suptitle("MPL twin Phase-0 diagnostic — as-received FEM transmissibility forward vs measured |T| "
                 "(uncoupled, OOP/X axis, band 20–260 Hz)", fontsize=11)
    fig.text(0.5, 0.005,
             "Quantity: gain-free output/output transmissibility |T_a|=√(PSD_a/PSD_shield), dimensionless. "
             "FINDING: nominal FEM forward is ~uncorrelated with measured |T| at every held-out location — a "
             "dense modal forest + unknown diffuse acoustic load make the transmissibility SHAPE unpredictable "
             "by stiffness calibration (modal frequencies ARE present). run mpl_twin_iteration_20260620, θ=1 nominal.",
             ha="center", fontsize=7.5, wrap=True)
    fig.tight_layout(rect=[0, 0.03, 1, 0.96])
    out = FIG / "fig_forward_diagnostic.png"
    fig.savefig(out, dpi=150, bbox_inches="tight"); plt.close(fig)
    (OUT / "forward_diagnostic.json").write_text(json.dumps(
        {"deliverable": "nominal FEM |T| vs measured |T| correlation (Phase-0 key finding D6)",
         "band_hz": list(CAL.__dict__.get("BAND", (20, 260))) if False else [float(f[0]), float(f[-1])],
         "per_location": rows,
         "mean_abs_log_corr": round(float(np.mean([abs(r["log_corr"]) for r in rows])), 3)}, indent=2))
    print("wrote", out)
    for r in rows: print(" ", r)


if __name__ == "__main__":
    main()
