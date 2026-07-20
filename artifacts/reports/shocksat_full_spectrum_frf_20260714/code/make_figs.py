#!/usr/bin/env python3
"""make_figs — the >=6 review figures (card §10), Tufte-linted (.claude/skills/tufte-data-graphics).
Each reads a named out/ artifact and prints its run/dataset label + any non-converged flag ON the figure.
Saved as this .py (lintable/replayable). Robust to a missing arm (draws what exists, notes the gap)."""
import json, os, sys
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

WS = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
FIG = os.path.join(WS, "figures"); os.makedirs(FIG, exist_ok=True)
plt.rcParams.update({"font.size": 10, "axes.spines.top": False, "axes.spines.right": False,
                     "figure.dpi": 130, "savefig.bbox": "tight"})
LABEL = "ShockSat full-spectrum FRF 20260714 (dev = LODO over 4 drives; wide caches, scored <=500 Hz)"
manifest = []


def J(p):
    fp = os.path.join(WS, p)
    return json.load(open(fp)) if os.path.exists(fp) else None


def fig_bands():
    t = J("out/arms_bands_table.json")
    if not t:
        return
    arms = [a for a in ["A0", "A1", "B", "C", "D", "R", "F"] if a in t["arms"]]
    bands = [("sub200", "45-200 Hz"), ("b200_500", "200-500 Hz")]
    fig, ax = plt.subplots(figsize=(7.2, 4.0))
    x = np.arange(len(arms)); w = 0.38
    for i, (b, lab) in enumerate(bands):
        vals, ses = [], []
        for a in arms:
            c = t["arms"][a].get(b, {})
            vals.append(c.get("mean", np.nan)); ses.append(c.get("se") or 0)
        ax.bar(x + (i - 0.5) * w, vals, w, yerr=ses, capsize=3,
               color=["#4477aa", "#cc6677"][i], label=lab)
    a1sub = t["arms"].get("A1", {}).get("sub200", {}).get("mean")
    if a1sub is not None:
        ax.axhline(a1sub, color="#4477aa", ls=":", lw=0.8)
        ax.text(len(arms) - 0.5, a1sub, " A1 sub-200 bar", va="bottom", ha="right",
                fontsize=8, color="#4477aa")
    ax.set_xticks(x); ax.set_xticklabels(arms)
    ax.set_ylabel("held-out per-channel log|H| corr (P1′)")
    ax.set_title("Arms × bands: fold-averaged held-out FRF correlation\n"
                 "(500-1000 Hz not certified — FEM basis credible ~640 Hz)", fontsize=10)
    ax.legend(frameon=False, fontsize=8, loc="upper left")
    ax.text(0.0, -0.16, LABEL, transform=ax.transAxes, fontsize=6, color="grey")
    p = "figures/fig_bands_table.png"; fig.savefig(os.path.join(WS, p)); plt.close(fig)
    manifest.append({"file": p, "script": "code/make_figs.py", "data_label": "out/arms_bands_table.json"})


def fig_identifiability():
    d = J("out/identifiability.json")
    if not d:
        return
    ev = np.array(d["fim_eigenvalues"]); prior = d["prior_precision_logtheta"]
    fig, ax = plt.subplots(figsize=(6.6, 3.8))
    ax.semilogy(np.arange(1, len(ev) + 1), ev, "o-", color="#333", ms=5)
    ax.axhline(prior, color="#cc6677", ls="--", lw=1)
    ax.text(len(ev), prior, " prior precision 1/0.25²=16", va="bottom", ha="right",
            color="#cc6677", fontsize=8)
    ax.set_xlabel("θ-combination (FIM eigen-index)")
    ax.set_ylabel("Fisher information (log-θ)")
    ax.set_title("Arm B: θ is LOCALLY over-identified by amplitudes (all 9 ≫ prior)\n"
                 "→ non-convergence is MULTIMODALITY, not a flat posterior", fontsize=9.5)
    ax.text(0.0, -0.18, f"realized discrepancy floor {d['realized_discrepancy_floor_dex']} dex — " + LABEL,
            transform=ax.transAxes, fontsize=6, color="grey")
    p = "figures/fig_identifiability.png"; fig.savefig(os.path.join(WS, p)); plt.close(fig)
    manifest.append({"file": p, "script": "code/make_figs.py", "data_label": "out/identifiability.json"})


def fig_qoi_sensors():
    q = J("out/qoi_weighted_scores.json"); w = J("out/qoi_sensor_weights.json")
    if not w:
        return
    top = w["top10"]
    daqs = [str(d) for d, _ in top]; wts = [v for _, v in top]
    fig, ax = plt.subplots(figsize=(6.8, 3.6))
    ax.bar(range(len(daqs)), wts, color="#228833")
    ax.set_xticks(range(len(daqs))); ax.set_xticklabels(daqs)
    ax.set_xlabel("sensor DAQ channel (top-10 net-CG shear participation)")
    ax.set_ylabel("QOI weight (norm.)")
    ttl = "Net-CG-shear sensor weights (Andrew's 'sensor B matters more')"
    if q and q.get("sub200_P1p_qoiw_mean_by_arm"):
        ttl += "\nQOI-weighted sub-200 P1′ (screening) per arm: " + ", ".join(
            f"{a} {val:.3f}" for a, val in list(q["sub200_P1p_qoiw_mean_by_arm"].items())[:4])
    ax.set_title(ttl, fontsize=9)
    ax.text(0.0, -0.2, LABEL, transform=ax.transAxes, fontsize=6, color="grey")
    p = "figures/fig_qoi_sensors.png"; fig.savefig(os.path.join(WS, p)); plt.close(fig)
    manifest.append({"file": p, "script": "code/make_figs.py", "data_label": "out/qoi_sensor_weights.json"})


def fig_loop():
    if not os.path.exists(os.path.join(WS, "out", "query_log.jsonl")):
        return
    ag, rn = [], []
    for line in open(os.path.join(WS, "out", "query_log.jsonl")):
        r = json.loads(line)
        (ag if r.get("track") == "agent" else rn).append(r.get("sub200_P1p"))
    if not ag and not rn:
        return
    fig, ax = plt.subplots(figsize=(6.8, 3.8))
    if ag:
        ax.plot(range(1, len(ag) + 1), np.maximum.accumulate([a or -1 for a in ag]),
                "o-", color="#4477aa", label="agent (amplitude compass) best-so-far")
    if rn:
        ax.plot(range(1, len(rn) + 1), np.maximum.accumulate([a or -1 for a in rn]),
                "s-", color="#aa7744", label="equal-budget random best-so-far")
    a1 = J("out/arms_bands_table.json")
    if a1:
        b = a1["arms"].get("A1", {}).get("sub200", {}).get("mean")
        if b:
            ax.axhline(b, color="#cc6677", ls="--", lw=1); ax.text(1, b, " A1 bar", fontsize=8,
                                                                   color="#cc6677", va="bottom")
    ax.set_xlabel("scored query #"); ax.set_ylabel("best dev sub-200 P1′")
    ax.set_title("Arm D (H2): amplitude-compass agent vs equal-budget random", fontsize=10)
    ax.legend(frameon=False, fontsize=8)
    ax.text(0.0, -0.18, LABEL, transform=ax.transAxes, fontsize=6, color="grey")
    p = "figures/fig_loop_trajectory.png"; fig.savefig(os.path.join(WS, p)); plt.close(fig)
    manifest.append({"file": p, "script": "code/make_figs.py", "data_label": "out/query_log.jsonl"})


def fig_selection():
    e = J("out/arm_E.json")
    if not e:
        return
    c = e["candidates"]
    lz = [r.get("logZ_sig0.25") for r in c]; hs = [r.get("heldout_sub200") for r in c]
    fig, ax = plt.subplots(figsize=(6.2, 4.0))
    ax.scatter(lz, hs, color="#333", s=28)
    for r in c:
        ax.annotate(r["arm"], (r.get("logZ_sig0.25"), r.get("heldout_sub200")), fontsize=6,
                    xytext=(3, 2), textcoords="offset points")
    ax.set_xlabel("amplitude-inclusive log-evidence (σ_prior 0.25)")
    ax.set_ylabel("held-out dev sub-200 P1′")
    ax.set_title(f"Arm E (H5): selection score vs held-out — Spearman {e.get('spearman')}", fontsize=10)
    ax.text(0.0, -0.18, LABEL, transform=ax.transAxes, fontsize=6, color="grey")
    p = "figures/fig_selection_scatter.png"; fig.savefig(os.path.join(WS, p)); plt.close(fig)
    manifest.append({"file": p, "script": "code/make_figs.py", "data_label": "out/arm_E.json"})


def fig_netcg():
    n = J("out/netcg_results.json")
    if not n:
        return
    qs = ["shear_x", "shear_y", "normal_z"]; deliv = [1.51, 2.30, 2.53]
    fig, ax = plt.subplots(figsize=(6.6, 3.8))
    x = np.arange(len(qs))
    now = [n[q]["width_ratio"] for q in qs]; cov = [n[q]["coverage"] for q in qs]
    ax.bar(x - 0.2, deliv, 0.4, color="#bbb", label="delivered twin")
    ax.bar(x + 0.2, now, 0.4, color="#4477aa", label="this study")
    for i, q in enumerate(qs):
        ax.text(i + 0.2, now[i], f"cov {cov[i]:.2f}", ha="center", va="bottom", fontsize=7)
    ax.set_xticks(x); ax.set_xticklabels(qs)
    ax.set_ylabel("95%-band GRMS-force width ratio (×FEM+6dB)")
    ax.set_title("Net-CG force bands vs the delivered twin (coverage annotated;\n"
                 "coverage <0.95 = disqualified for delivery)", fontsize=9.5)
    ax.legend(frameon=False, fontsize=8)
    ax.text(0.0, -0.2, LABEL, transform=ax.transAxes, fontsize=6, color="grey")
    p = "figures/fig_netcg_bands.png"; fig.savefig(os.path.join(WS, p)); plt.close(fig)
    manifest.append({"file": p, "script": "code/make_figs.py", "data_label": "out/netcg_results.json"})


def fig_graphical_model():
    fig, ax = plt.subplots(figsize=(7.0, 4.2)); ax.axis("off")
    boxes = {
        "θ (9 group\nstiffness)": (0.12, 0.75), "survey ζ\n(fixed)": (0.12, 0.45),
        "window 𝒲\n(fixed)": (0.12, 0.15), "modes\nλ,φ(θ)": (0.4, 0.75),
        "gain_d\n(per drive)": (0.4, 0.35), "log|H|(θ)\naccelerance": (0.68, 0.55),
        "σ_e, ℓ, σ_n\n(discrepancy)": (0.68, 0.2), "y = measured\nlog|H1|": (0.9, 0.55)}
    for txt, (x, y) in boxes.items():
        obs = txt.startswith("y =")
        ax.add_patch(plt.Rectangle((x - 0.07, y - 0.06), 0.14, 0.12, fill=True,
                                   fc="#dde8f0" if not obs else "#f0d8d8", ec="#333", lw=1))
        ax.text(x, y, txt, ha="center", va="center", fontsize=7.5)
    edges = [((0.19, 0.75), (0.33, 0.75)), ((0.47, 0.75), (0.61, 0.58)),
             ((0.19, 0.45), (0.61, 0.56)), ((0.19, 0.15), (0.61, 0.5)),
             ((0.47, 0.35), (0.61, 0.53)), ((0.75, 0.55), (0.83, 0.55)),
             ((0.75, 0.2), (0.84, 0.5))]
    for (x0, y0), (x1, y1) in edges:
        ax.annotate("", (x1, y1), (x0, y0), arrowprops=dict(arrowstyle="->", color="#555", lw=1))
    ax.text(0.5, 0.97, "Arm B likelihood (run-specific graphical model)", ha="center", fontsize=10)
    ax.text(0.5, 0.02, "y_{d,ch}(f)=log10|𝒲[H](θ)|+gain_d+ε,  ε~GP(σ_e,ℓ)+σ_n I;  "
                       "NUTS multimodal→scored at amplitude-MAP. " + LABEL,
            ha="center", fontsize=6, color="grey")
    p = "figures/fig_graphical_model.png"; fig.savefig(os.path.join(WS, p)); plt.close(fig)
    manifest.append({"file": p, "script": "code/make_figs.py", "data_label": "run-specific schematic"})


def main():
    fig_bands(); fig_identifiability(); fig_qoi_sensors(); fig_loop()
    fig_selection(); fig_netcg(); fig_graphical_model()
    json.dump({"figures": manifest}, open(os.path.join(WS, "out", "fig_manifest.json"), "w"), indent=1)
    print(f"{len(manifest)} figures written")


if __name__ == "__main__":
    main()
