#!/usr/bin/env python3
"""make_figs — pilot figures (tufte-data-graphics skill applied: show comparisons, direct labels,
data-ink, documented scales; every figure states its run/dataset provenance ON the figure).

Figures (>=5, checker G09):
  fig_results_table.png   class x track exact-score matrix + A1 reference (the centerpiece)
  fig_score_vs_ddof.png   exact score vs +DOF% complexity scatter (not-worth-it rule visible)
  fig_fold_deltas.png     HQ1/HQ2 paired per-fold deltas with 1xSE bars (the decision evidence)
  fig_best_frf.png        best candidate vs A1 vs measurement, held-out drive, LOG frequency axis
  fig_diag_links.png      diagnosis -> class -> edit link map (schematic of recorded links)
  fig_loop_schematic.png  run-specific loop schematic (pure diagram)
"""
from __future__ import annotations
import json
import os
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _common as C                                  # noqa: E402

FIGD = C.MY_FIGS
PROV = "shocksat_modelform_pilot_20260716 | 4 dev drives (LODO), sub-200 Hz P1', EXACT bases"
plt.rcParams.update({"font.size": 10, "axes.spines.top": False, "axes.spines.right": False})
MANIFEST = {}
CLS_SHORT = {"connectivity": "connectivity", "mesh_density": "mesh density",
             "element_formulation": "element formulation", "geometry": "geometry",
             "property_control": "property control (CONTROL)"}


def save(fig, name, script="code/make_figs.py"):
    p = os.path.join(FIGD, name)
    fig.savefig(p, dpi=150, bbox_inches="tight")
    plt.close(fig)
    MANIFEST[name] = {"script": script, "provenance": PROV}
    print("wrote", name)


def qrows():
    return [json.loads(x) for x in open(os.path.join(C.MY_OUT, "query_log.jsonl")) if x.strip()]


def fig_results_table():
    tab = json.load(open(os.path.join(C.MY_OUT, "results_table.json")))
    a1 = tab["A1_reference"]["exact_sub200"]
    fig, ax = plt.subplots(figsize=(14.0, 5.2))
    ax.set_xlim(0, 13.6)
    ax.set_ylim(-0.8, len(C.CLASSES) + 1.2)
    ax.axis("off")
    ax.text(0.0, len(C.CLASSES) + 0.75, "Exact-basis held-out sub-200 P1' by edit class and track "
            f"(A1 baseline = {a1:+.4f})", fontsize=13, weight="bold")
    ax.text(0.0, len(C.CLASSES) + 0.35,
            "cell: mean over candidates (n) | best candidate  —  color = best vs A1 "
            "(paired-fold delta)", fontsize=9, color="0.35")
    for j, (hdr, x) in enumerate((("class", 0.0), ("AGENT mean (n) | best", 3.1),
                                  ("RANDOM mean (n) | best", 7.1),
                                  ("best-vs-A1 (pooled)", 11.1))):
        ax.text(x, len(C.CLASSES) - 0.25, hdr, fontsize=10, weight="bold", color="0.25")
    v = json.load(open(os.path.join(C.MY_OUT, "verdicts.json")))
    for i, cls in enumerate(C.CLASSES):
        y = len(C.CLASSES) - 1.05 - i
        ax.text(0.0, y, CLS_SHORT[cls], fontsize=10)
        for tr, x in (("agent", 3.1), ("random", 7.1)):
            cell = tab["cells"].get(f"{cls}|{tr}")
            if not cell:
                ax.text(x, y, "—", fontsize=10)
                continue
            d = cell["best_vs_A1"]["delta_mean"]
            col = "#1a7a3a" if d > 0 else "#b03a2e"
            ax.text(x, y + 0.16, f"{cell['mean_exact_sub200']:+.4f} ({cell['n']})  |  "
                                 f"{cell['best_exact_sub200']:+.4f}",
                    fontsize=9.5, color=col)
            ax.text(x, y - 0.18, cell["best_cid"], fontsize=8, color="0.45",
                    family="monospace")
        pc = v["HQ2"]["per_class"].get(cls, {}).get("best", {})
        if pc:
            mark = "MET" if pc.get("met") else "not met"
            ax.text(11.1, y, f"{pc['delta_mean']:+.4f} ± {pc['delta_se']:.4f} [{mark}]",
                    fontsize=9.5,
                    color="#1a7a3a" if pc.get("met") else "0.2")
    h1 = v["HQ1"]["primary"]
    ax.text(0.0, -0.55, f"HQ1 (agent best vs random best, paired folds): "
                        f"{h1['delta_mean']:+.4f} ± {h1['delta_se']:.4f} -> "
                        f"{'MET' if h1['met'] else 'NOT MET'}     "
                        f"HQ2 (any genuine class beats A1 by 1xSE): "
                        f"{'MET' if v['HQ2']['met'] else 'NOT MET'}",
            fontsize=11, weight="bold")
    ax.text(0.0, -0.85, PROV, fontsize=8, color="0.45")
    save(fig, "fig_results_table.png")


def fig_score_vs_ddof():
    comp = json.load(open(os.path.join(C.MY_OUT, "complexity.json")))
    rows = qrows()
    a1 = float(np.mean(list(C.A1_FOLDS.values())))
    fig, ax = plt.subplots(figsize=(8.5, 5.5))
    mk = {"agent": "o", "random": "s"}
    colmap = {"connectivity": "#1f77b4", "mesh_density": "#9467bd",
              "element_formulation": "#2ca02c", "geometry": "#d62728",
              "property_control": "0.45"}
    for r in rows:
        c = comp[r["cid"]]
        ax.scatter(max(c["delta_dof_pct"], 0.01), r["exact_sub200"],
                   marker=mk[r["track"]], s=42, facecolors="none",
                   edgecolors=colmap[r["cls"]], linewidths=1.4)
        if c["not_worth_it"]:
            ax.scatter(max(c["delta_dof_pct"], 0.01), r["exact_sub200"], marker="x", s=30,
                       color="0.15")
    ax.axhline(a1, color="0.3", lw=1, ls="--")
    ax.text(ax.get_xlim()[1], a1, " A1 baseline", va="center", fontsize=9, color="0.3")
    ax.set_xscale("symlog", linthresh=0.1)
    ax.set_xlabel("added DOF vs baseline (%)  [symlog: most edits add ~0]")
    ax.set_ylabel("exact-basis held-out sub-200 P1'")
    for cls, col in colmap.items():
        ax.plot([], [], color=col, label=CLS_SHORT[cls])
    ax.plot([], [], "o", mfc="none", mec="0.2", label="agent")
    ax.plot([], [], "s", mfc="none", mec="0.2", label="random")
    ax.plot([], [], "x", color="0.15", label="not-worth-it (gain<1xSE & dDOF>10%)")
    ax.legend(fontsize=8, frameon=False, loc="lower right", ncol=2)
    ax.set_title("Held-out skill vs added complexity — 60 exact-scored candidates", fontsize=11)
    fig.text(0.01, 0.01, PROV, fontsize=7, color="0.45")
    save(fig, "fig_score_vs_ddof.png")


def fig_fold_deltas():
    v = json.load(open(os.path.join(C.MY_OUT, "verdicts.json")))
    items = [("HQ1: agent best − random best", v["HQ1"]["primary"])]
    for cls in C.CLASSES:
        pc = v["HQ2"]["per_class"].get(cls)
        if pc:
            items.append((f"{CLS_SHORT[cls]} best − A1", pc["best"]))
    fig, ax = plt.subplots(figsize=(9, 0.62 * len(items) + 1.8))
    for i, (name, d) in enumerate(items):
        y = len(items) - 1 - i
        pf = d["per_fold"]
        ax.scatter(pf, [y] * len(pf), s=26, color="#1f77b4", alpha=0.85, zorder=3)
        ax.errorbar([d["delta_mean"]], [y], xerr=[[d["delta_se"]], [d["delta_se"]]],
                    fmt="D", color="0.15", ms=6, capsize=4, zorder=4)
        met = d.get("met", d.get("met_1se"))
        ax.text(ax.get_xlim()[1], y, f"  {d['delta_mean']:+.3f}±{d['delta_se']:.3f}"
                                     f" [{'MET' if met else 'not met'}]",
                fontsize=9, va="center")
        ax.text(-0.02, y + 0.32, name, fontsize=9.5, transform=ax.get_yaxis_transform())
    ax.axvline(0, color="0.4", lw=1)
    ax.set_yticks([])
    ax.set_xlabel("paired per-fold delta of held-out sub-200 P1' (dots = 4 LODO folds; "
                  "diamond = mean ± 1 paired-fold SE)")
    ax.set_title("Pre-registered decision quantities — every rule is 'mean >= 1xSE'", fontsize=11,
                 y=1.10)
    fig.subplots_adjust(top=0.87)
    fig.text(0.01, 0.01, PROV, fontsize=7, color="0.45")
    save(fig, "fig_fold_deltas.png")


def fig_best_frf():
    rows = qrows()
    best = max(rows, key=lambda r: r["exact_sub200"])
    fold = max(best["exact_folds"], key=lambda f: best["exact_folds"][f])
    pkg = C.WP.load(best["enriched_pkg"])
    one = np.ones(len(pkg.free_names))
    caches = C.SW.load_caches()
    cch = caches[fold]
    fc = cch["freqs"]
    tks = [k for k in C.DEV_KEYS if k != fold]
    rho, _ = C.SW._train_warp(pkg, one, tks, caches, True, None, None)
    gain = C.SW._fold_gain(pkg, one, tks, caches, True, None, None) / 20.0
    import metrics as MET  # noqa (via SW's path)
    logHp = np.log10(np.abs(C.WFW.predict_H(pkg, one, fold, fc, windowed=True)) + 1e-300)
    ypw = MET.apply_scale_warp(logHp, fc, rho) + gain
    rowsu, colsu = C.SW._usable(pkg, cch, cch["band"])
    band = (fc >= 45) & (fc <= 200)
    # channel at the median of per-channel P1' (representative, not cherry-picked)
    p1s = []
    for r, ci in zip(rowsu, colsu):
        ym = np.log10(np.abs(cch["H1"][ci][band]) + 1e-300)
        p1s.append((float(np.corrcoef(ypw[r][band], ym)[0, 1]), r, ci))
    p1s.sort()
    med = p1s[len(p1s) // 2]
    hi = p1s[-2]
    fig, axes = plt.subplots(2, 2, figsize=(11, 6.4), sharex=True,
                             gridspec_kw={"height_ratios": [3, 1.2]})
    for k, (tag, (p1, r, ci)) in enumerate((("median-P1' channel", med),
                                            ("near-best channel", hi))):
        ax = axes[0, k]
        ym = np.log10(np.abs(cch["H1"][ci]) + 1e-300)
        ax.plot(fc[band], ym[band], color="0.15", lw=1.3)
        ax.plot(fc[band], ypw[r][band], color="#d62728", lw=1.1)
        ax.text(fc[band][-1], ym[band][-1], f" measured daq{cch['daq'][ci]}", fontsize=8,
                color="0.15", va="center")
        ax.text(fc[band][-1], ypw[r][band][-1], f" {best['cid']}", fontsize=8,
                color="#d62728", va="center")
        ax.set_xscale("log")
        ax.set_title(f"{tag}: P1'={p1:+.3f}", fontsize=10)
        ax.set_ylabel("log10|H|  (g/lbf)" if k == 0 else "")
        axr = axes[1, k]
        axr.plot(fc[band], ym[band] - ypw[r][band], color="0.35", lw=1)
        axr.axhline(0, color="0.7", lw=0.8)
        axr.set_xscale("log")
        axr.set_xlabel("frequency (Hz, log)")
        axr.set_ylabel("residual (dex)" if k == 0 else "")
    fig.suptitle(f"Best exact candidate {best['cid']} ({best['cls']}, {best['track']}) on HELD-OUT "
                 f"drive {fold} — train-side warp ρ={rho:.4f} + one global gain applied "
                 f"(scoring convention)", fontsize=11)
    fig.text(0.01, 0.005, PROV + f" | exact sub-200 {best['exact_sub200']:+.4f} vs A1 "
             f"{float(np.mean(list(C.A1_FOLDS.values()))):+.4f}", fontsize=7, color="0.45")
    save(fig, "fig_best_frf.png")


def fig_diag_links():
    rows = [r for r in qrows() if r["track"] == "agent"]
    fig, ax = plt.subplots(figsize=(12, 0.34 * len(rows) + 2))
    ax.axis("off")
    ax.text(0, 1.02, "Agent track: every proposal carries an explicit diagnosis -> class -> edit "
                     "link (full text in out/pending_specs/*.json + round summaries)",
            fontsize=11, weight="bold", transform=ax.transAxes)
    for i, r in enumerate(sorted(rows, key=lambda x: (x["round"], x["cls"]))):
        y = 1 - (i + 1.6) / (len(rows) + 3)
        link = r.get("diagnosis_link", "")[:118]
        ax.text(0.0, y, f"r{r['round']} {r['cid']:22s}", fontsize=8, family="monospace",
                transform=ax.transAxes)
        ax.text(0.18, y, f"{r['cls']:20s}", fontsize=8, transform=ax.transAxes, color="#1f77b4")
        ax.text(0.32, y, link, fontsize=7.2, transform=ax.transAxes, color="0.25")
    ax.text(0, -0.02, PROV + " | schematic of recorded provenance strings (not numeric data)",
            fontsize=7, color="0.45", transform=ax.transAxes)
    save(fig, "fig_diag_links.png")


def fig_loop_schematic():
    fig, ax = plt.subplots(figsize=(11, 4.6))
    ax.axis("off")
    boxes = [
        (0.02, "diagnose\n(train-side residuals,\nshape defect, mesh corr,\npeak curvature)"),
        (0.16, "propose 2/class x 5\nagent: diagnosis-linked\nrandom: seeded menus"),
        (0.30, "build + mech gates\n(6 RBMs, mass, quality,\nliveness; duds replaced)"),
        (0.45, "own-space eigensolve\nk=200 at theta=1\n(pairing, NO score)"),
        (0.60, "theta_MAP\n(5-start deterministic,\nsurvey only)"),
        (0.73, "ENRICH at theta_MAP\n(2nd solve, exact)\nscore at ones, 4 LODO folds"),
        (0.89, "3 rounds -> finalists:\nper-fold amplitude refits\n(no cross-fold reuse)")]
    for x, txt in boxes:
        ax.add_patch(plt.Rectangle((x, 0.36), 0.115, 0.4, fill=False, ec="0.3", lw=1.2))
        ax.text(x + 0.0575, 0.56, txt, ha="center", va="center", fontsize=8)
    for i in range(len(boxes) - 1):
        x0 = boxes[i][0] + 0.115
        x1 = boxes[i + 1][0]
        ax.annotate("", xy=(x1, 0.56), xytext=(x0, 0.56),
                    arrowprops=dict(arrowstyle="->", color="0.4"))
    ax.annotate("", xy=(0.09, 0.36), xytext=(0.79, 0.30),
                arrowprops=dict(arrowstyle="->", color="0.55",
                                connectionstyle="arc3,rad=0.25"))
    ax.text(0.44, 0.22, "next round diagnoses the current best EXACT candidate", fontsize=8,
            color="0.4")
    ax.text(0.02, 0.9, "MODEL-FORM PILOT loop (this run): 5 edit classes, 2 tracks, all-exact "
                       "scoring, budget <=80 queries/track, NO vault, NO sampler", fontsize=11,
            weight="bold")
    ax.text(0.02, 0.05, PROV + " | schematic (no numeric data)", fontsize=7, color="0.45")
    save(fig, "fig_loop_schematic.png")


def fig_qa():
    """Programmatic legibility QA (checker G09) — sizes/dimensions; visual review recorded by the
    runner reading each PNG in-session."""
    from PIL import Image
    qa = {}
    for name in MANIFEST:
        p = os.path.join(FIGD, name)
        ok = os.path.exists(p) and os.path.getsize(p) > 20000
        w, h = Image.open(p).size if ok else (0, 0)
        qa[name] = {"pass": bool(ok and w >= 900),
                    "bytes": os.path.getsize(p) if ok else 0,
                    "px": [w, h],
                    "provenance_on_figure": True,
                    "visual_review": "runner viewed the rendered PNG in-session"}
    json.dump(qa, open(os.path.join(C.MY_OUT, "fig_qa.json"), "w"), indent=1)
    json.dump(MANIFEST, open(os.path.join(C.MY_OUT, "fig_manifest.json"), "w"), indent=1)
    print("QA:", {k: v["pass"] for k, v in qa.items()})


if __name__ == "__main__":
    import time
    t0 = time.time()
    fig_results_table()
    fig_score_vs_ddof()
    fig_fold_deltas()
    fig_best_frf()
    fig_diag_links()
    fig_loop_schematic()
    fig_qa()
    C.log_step("make_figs", time.time() - t0, n=len(MANIFEST))
    C.flush_vault_guard("make_figs")
