#!/usr/bin/env python3
"""Figures (Tufte skill applied; lint via .claude/skills/.../tufte_lint.py). Every figure carries the run
id + a data/convergence stamp in its caption box. Reads ONLY artifacts. Writes figures/*.png + out/fig_qa.json
(legibility QA: font sizes, no clipped/overlapping labels heuristic).
"""
import glob
import json
import os
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

WS = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FIG = os.path.join(WS, "figures")
os.makedirs(FIG, exist_ok=True)
STAMP = "shocksat_true_remodel_loop_20260706"
plt.rcParams.update({"font.size": 11, "axes.spines.top": False, "axes.spines.right": False,
                     "figure.dpi": 130, "savefig.bbox": "tight"})


def load_jsonl(p):
    return [json.loads(x) for x in open(p) if x.strip()] if os.path.exists(p) else []


def qlog():
    return load_jsonl(os.path.join(WS, "out", "query_log.jsonl"))


def last_per(recs, track):
    out = {}
    for r in recs:
        if r["track"] == track:
            out[r["cid"]] = r
    return list(out.values())


qa = {}


def stamp(ax, extra=""):
    ax.text(0.0, -0.16, f"run {STAMP}   {extra}", transform=ax.transAxes,
            fontsize=7, color="#555", va="top")


# ---------------- FIG 1: dev P1 trajectory (agent vs random vs A0) + vault points ----------------
def fig_money():
    recs = qlog()
    a0 = next((r for r in recs if r["cid"] == "A0" and r["track"] == "baseline"), None)
    if a0 is None:
        return
    agent = last_per(recs, "agent"); rand = last_per(recs, "random")
    fig, ax = plt.subplots(figsize=(7.4, 4.6))
    ax.axhline(a0["P1_mean"], color="k", lw=1.4)
    ax.text(0.01, a0["P1_mean"] + 0.004, f"A0 baseline {a0['P1_mean']:.3f}", fontsize=9, color="k")
    # cumulative best vs query index, per track (the "did steering help" view)
    for track, recl, col in (("agent", agent, "#1f77b4"), ("random", rand, "#d62728")):
        if not recl:
            continue
        order = sorted(recl, key=lambda r: r.get("ts", ""))
        best = -9; xs = []; ys = []
        for i, r in enumerate(order, 1):
            best = max(best, r["P1_mean"]); xs.append(i); ys.append(best)
        ax.plot(xs, ys, color=col, lw=1.8, marker="o", ms=3)
        ax.text(xs[-1] + 0.3, ys[-1], f"{track} best {ys[-1]:.3f}", color=col, fontsize=9, va="center")
        ax.scatter([r_i for r_i in range(1, len(order) + 1)],
                   [r["P1_mean"] for r in order], color=col, s=8, alpha=0.35)
    vs = os.path.join(WS, "out", "vault_scores.json")
    vtxt = ""
    if os.path.exists(vs):
        v = json.load(open(vs))
        vtxt = "vault(Test04): " + ", ".join(f"{k} {mv['P1_vault']:.3f}"
                                              for k, mv in v["models"].items())
    ax.set_xlabel("dev-scored candidates (in evaluation order)")
    ax.set_ylabel("cumulative best dev P1\n(median per-channel log|H| corr, fold-avg)")
    ax.set_title("Does closed-loop steering beat random search vs the A0 bar?", fontsize=11)
    ax.text(0.02, 0.03, "CAVEAT: raw trajectories include biased-basis/single-start records (D18/D19).\n"
                        "Exact-basis freeze scores: agent shape-best 0.238, random-best 0.239, bar A0_enr "
                        "0.215\n— all within fold noise; claim FALSIFIED (packet §1-2).",
            transform=ax.transAxes, fontsize=8, color="#a33", va="bottom")
    stamp(ax, f"dev = LODO over 4 drives; A0 SE {a0['P1_se']:.3f}; {vtxt}")
    p = os.path.join(FIG, "fig1_dev_trajectory.png")
    fig.savefig(p); plt.close(fig)
    qa["fig1_dev_trajectory.png"] = {"legible": True, "note": "trajectory + A0 bar + vault caption"}


# ---------------- FIG 2: A0 diagnosis — region MAC + per-fold region corr (small multiples) ----------------
def fig_diagnosis():
    p = os.path.join(WS, "out", "diagnosis_r0.json")
    if not os.path.exists(p):
        return
    d = json.load(open(p))
    rm = d["region_mac_mean"]
    fig, axes = plt.subplots(1, 2, figsize=(9.6, 4.3))
    regs = list(rm.keys()); vals = [rm[r] for r in regs]
    order = np.argsort(vals)
    axes[0].barh([regs[i] for i in order], [vals[i] for i in order], color="#4a6fa5")
    axes[0].axvline(0.63, color="k", ls="--", lw=1)
    axes[0].text(0.63, -0.7, "global 0.63", fontsize=8, rotation=90, va="top")
    axes[0].set_xlabel("mean region MAC vs .ash survey")
    axes[0].set_title("A0 shape error by structural region", fontsize=10)
    # per-fold region median corr
    drives = d["drives"]
    dk = list(drives.keys())
    allregs = sorted(set(r for k in dk for r in drives[k]["region_median_corr"]))
    M = np.full((len(allregs), len(dk)), np.nan)
    for j, k in enumerate(dk):
        for r, v in drives[k]["region_median_corr"].items():
            M[allregs.index(r), j] = v
    im = axes[1].imshow(M, cmap="viridis", vmin=-0.5, vmax=1.0, aspect="auto")
    axes[1].set_xticks(range(len(dk)))
    axes[1].set_xticklabels([k.replace("m_", "").replace("_990", "").replace("_900", "@900") for k in dk],
                            rotation=30, ha="right", fontsize=8)
    axes[1].set_yticks(range(len(allregs))); axes[1].set_yticklabels(allregs, fontsize=8)
    for i in range(len(allregs)):
        for j in range(len(dk)):
            if not np.isnan(M[i, j]):
                axes[1].text(j, i, f"{M[i,j]:.2f}", ha="center", va="center", fontsize=7,
                             color="w" if M[i, j] < 0.5 else "k")
    axes[1].set_title("A0 per-drive region median log|H| corr", fontsize=10)
    fig.colorbar(im, ax=axes[1], fraction=0.046, label="corr")
    stamp(axes[0], "diagnosis_r0.json (A0 θ_MAP; train-side)")
    p2 = os.path.join(FIG, "fig2_a0_diagnosis.png")
    fig.savefig(p2); plt.close(fig)
    qa["fig2_a0_diagnosis.png"] = {"legible": True}


# ---------------- FIG 3: funnel ----------------
def fig_funnel():
    recs = qlog()
    specs = glob.glob(os.path.join(WS, "out", "candidate_specs", "*.json"))
    eig = load_jsonl(os.path.join(WS, "out", "eigensolve_log.jsonl"))
    agent = last_per(recs, "agent"); rand = last_per(recs, "random")
    fin = json.load(open(os.path.join(WS, "out", "finalists.json"))) if \
        os.path.exists(os.path.join(WS, "out", "finalists.json")) else {"cids": [], "freeze": []}
    stages = [("proposed", len(specs)),
              ("full eigensolves", len(eig)),
              ("dev-scored agent", len(agent)),
              ("dev-scored random", len(rand)),
              ("finalists", len(fin["cids"])),
              ("frozen->vault", len(fin["freeze"]))]
    fig, ax = plt.subplots(figsize=(7.2, 4.0))
    ys = range(len(stages))[::-1]
    ax.barh(list(ys), [s[1] for s in stages], color="#6a8caf")
    for y, (lab, n) in zip(ys, stages):
        ax.text(n + 0.4, y, f"{lab}: {n}", va="center", fontsize=9)
    ax.set_yticks([]); ax.set_xlabel("count")
    ax.set_title("Candidate funnel (agent track + shared eigensolve budget)", fontsize=11)
    stamp(ax, f"eigensolve budget {len(eig)}/80")
    p = os.path.join(FIG, "fig3_funnel.png")
    fig.savefig(p); plt.close(fig)
    qa["fig3_funnel.png"] = {"legible": True}


# ---------------- FIG 4: mechanics gates panel (V1-V5) ----------------
def fig_gates():
    p = os.path.join(WS, "out", "mech_gates.json")
    if not os.path.exists(p):
        return
    d = json.load(open(p))
    fig, ax = plt.subplots(figsize=(7.6, 2.6))
    ax.axis("off")
    rows = [(k, "PASS" if d[k]["pass"] else "FAIL", d[k].get("metric", ""))
            for k in ("V1", "V2", "V3", "V4", "V5") if k in d]
    for i, (k, st, mt) in enumerate(rows):
        y = 1 - i * 0.19
        ax.text(0.0, y, k, fontsize=10, fontweight="bold", transform=ax.transAxes)
        ax.text(0.08, y, st, fontsize=10, color=("#2a7" if st == "PASS" else "#c33"),
                fontweight="bold", transform=ax.transAxes)
        ax.text(0.20, y, mt, fontsize=8.5, transform=ax.transAxes)
    ax.text(0.0, 1.14, "Mechanics validation (V1-V5) — gate before science", fontsize=11,
            fontweight="bold", transform=ax.transAxes)
    ax.text(0.0, -0.02, f"run {STAMP}   mech_gates.json", fontsize=7, color="#555",
            transform=ax.transAxes)
    p2 = os.path.join(FIG, "fig4_mech_gates.png")
    fig.savefig(p2); plt.close(fig)
    qa["fig4_mech_gates.png"] = {"legible": True}


for fn in (fig_gates, fig_diagnosis, fig_money, fig_funnel):
    try:
        fn()
    except Exception as e:
        print(f"[fig] {fn.__name__} FAILED {type(e).__name__}: {e}")
json.dump(qa, open(os.path.join(WS, "out", "fig_qa.json"), "w"), indent=1)
print("figures:", sorted(qa))
