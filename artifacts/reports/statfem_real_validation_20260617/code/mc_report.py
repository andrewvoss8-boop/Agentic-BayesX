#!/usr/bin/env python3
"""Monte-Carlo held-out report PDF (Andrew 2026-06-18): all 25 splits, every held-out channel graded, panels
sorted by score within a run, runs ordered best->worst, + a PATTERNS analysis (which runs and which physical
locations succeed/fail, and what drives it).

Leads with the analysis (runs ranked; per-LOCATION pass-rate spatial map + drivers), then the per-run FRF grids.
Output: out/mc_report.pdf  +  out/mc_pattern_summary.json. Resumable: caches per-split records to out/mc_cache.npz.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
from matplotlib.patches import Patch
from matplotlib.lines import Line2D

sys.path.insert(0, str(Path(__file__).resolve().parent))
import heldout_report as hr

WS = Path(__file__).resolve().parent.parent


def compute_all(n_splits=25, warmup=600, samples=600, n_draws=150):
    cache = WS / "out" / "mc_cache.npz"
    if cache.exists():
        z = np.load(cache, allow_pickle=True)
        return list(z["splits"]), np.asarray(z["freqs"])
    splits = []; freqs = None
    for s in range(n_splits):
        D = hr.compute(seed=s, n_draws=n_draws, warmup=warmup, samples=samples, chains=4)
        freqs = D["freqs"]
        param = np.exp(np.percentile(D["pred_ho"], [5, 50, 95], axis=0))
        total = np.exp(np.percentile(D["pred_ho"] + D["delta"][:, None, :], [5, 95], axis=0))
        chans = []
        for k in range(len(D["ho_daqs"])):
            gd = D["grades"][k]
            chans.append(dict(daq=int(D["ho_daqs"][k]), x=float(D["coords"][D["ho_pos"][k], 0]),
                              z=float(D["coords"][D["ho_pos"][k], 2]), dr=float(D["dr"][D["ho_pos"][k]]),
                              IS=float(gd["interval"]), CRPS=float(gd["crps"]), covered=bool(gd["covered"]),
                              param=param[:, :, k], total=total[:, :, k], det=D["det_ho"][:, k],
                              tru=np.exp(D["tru_ho"][:, k])))
        run_IS = float(np.median([c["IS"] for c in chans]))
        pass_rate = float(np.mean([c["covered"] for c in chans]))
        splits.append(dict(seed=s, run_IS=run_IS, pass_rate=pass_rate, rhat=float(D["diag"]["max_rhat"]),
                           sig=float(D["sig_pk"]), chans=chans))
        print(f"  split {s:2d}: R-hat {D['diag']['max_rhat']:.3f} | median IS {run_IS:.0f} | "
              f"pass {pass_rate*100:.0f}%  ({sum(c['covered'] for c in chans)}/{len(chans)})", flush=True)
    np.savez(cache, splits=np.array(splits, dtype=object), freqs=freqs)
    return splits, freqs


def patterns(splits):
    # per-location pass rate (over runs where the channel is held out)
    loc = {}
    for s in splits:
        for c in s["chans"]:
            d = c["daq"]; loc.setdefault(d, dict(x=c["x"], z=c["z"], dr=c["dr"], held=0, passed=0, IS=[]))
            loc[d]["held"] += 1; loc[d]["passed"] += int(c["covered"]); loc[d]["IS"].append(c["IS"])
    for d in loc:
        loc[d]["pass_rate"] = loc[d]["passed"] / loc[d]["held"]; loc[d]["med_IS"] = float(np.median(loc[d]["IS"]))
    return loc


def render(splits, freqs, loc, out="out/mc_report.pdf"):
    order = sorted(range(len(splits)), key=lambda i: splits[i]["run_IS"])     # best (low IS) -> worst
    daqs = sorted(loc); pr = np.array([loc[d]["pass_rate"] for d in daqs])
    lx = np.array([loc[d]["x"] for d in daqs]); lz = np.array([loc[d]["z"] for d in daqs])
    ldr = np.array([loc[d]["dr"] for d in daqs])
    with PdfPages(WS / out) as pdf:
        # ---- PATTERNS p1: runs ranked best->worst ----
        fig, ax = plt.subplots(2, 1, figsize=(11, 8.5)); fig.suptitle("Monte-Carlo: runs ranked best->worst", fontsize=13)
        ris = [splits[i]["run_IS"] for i in order]; prr = [splits[i]["pass_rate"] for i in order]
        xr = np.arange(len(order))
        ax[0].bar(xr, ris, color="#1f6fb4"); ax[0].set_yscale("log"); ax[0].set_ylabel("median peak interval score")
        ax[0].set_xticks(xr); ax[0].set_xticklabels([f"s{splits[i]['seed']}" for i in order], fontsize=6, rotation=90)
        ax[0].set_title("lower = better; each bar = one split", fontsize=10)
        ax[1].bar(xr, prr, color="#2a9d3a"); ax[1].axhline(0.95, color="#cc3333", ls="--"); ax[1].set_ylim(0, 1.05)
        ax[1].set_ylabel("held-out PASS rate"); ax[1].set_xticks(xr)
        ax[1].set_xticklabels([f"s{splits[i]['seed']}" for i in order], fontsize=6, rotation=90)
        pdf.savefig(fig, bbox_inches="tight"); plt.close(fig)

        # ---- PATTERNS p2: per-location pass rate (spatial + sorted) ----
        fig, ax = plt.subplots(1, 2, figsize=(12, 7)); fig.suptitle("Where it fails: per-LOCATION held-out pass rate", fontsize=13)
        sc = ax[0].scatter(lx, lz, c=pr, s=90, cmap="RdYlGn", vmin=0, vmax=1, edgecolor="k", lw=0.5)
        for d in daqs:
            ax[0].annotate(str(d), (loc[d]["x"], loc[d]["z"]), fontsize=5, xytext=(3, 2), textcoords="offset points")
        ax[0].set_xlabel("x [in]"); ax[0].set_ylabel("z [in]"); fig.colorbar(sc, ax=ax[0], label="pass rate", fraction=0.05)
        ax[0].set_title("structure (X-Z): green=always covered, red=always missed", fontsize=10)
        o = np.argsort(pr)
        ax[1].barh(np.arange(len(daqs)), pr[o], color=plt.cm.RdYlGn(pr[o]))
        ax[1].set_yticks(np.arange(len(daqs))); ax[1].set_yticklabels([f"ch{daqs[i]}" for i in o], fontsize=5)
        ax[1].axvline(0.95, color="#cc3333", ls="--"); ax[1].set_xlabel("pass rate"); ax[1].set_title("sorted", fontsize=10)
        pdf.savefig(fig, bbox_inches="tight"); plt.close(fig)

        # ---- PATTERNS p3: drivers ----
        fig, ax = plt.subplots(1, 2, figsize=(12, 5.5)); fig.suptitle("What drives pass/fail", fontsize=13)
        for a, feat, lab in [(ax[0], np.log10(ldr), "log10 dynamic range"), (ax[1], lz, "height z [in]")]:
            a.scatter(feat, pr, c=pr, cmap="RdYlGn", vmin=0, vmax=1, edgecolor="k", lw=0.4, s=55)
            cc = np.corrcoef(feat, pr)[0, 1]
            a.set_xlabel(lab); a.set_ylabel("pass rate"); a.set_title(f"corr = {cc:+.2f}", fontsize=10)
        pdf.savefig(fig, bbox_inches="tight"); plt.close(fig)

        # ---- per-run FRF grids (runs best->worst; channels sorted by IS asc) ----
        legend = [Patch(fc="#cfd3d6", label="total unc."), Patch(fc="#9ec6e6", label="param unc."),
                  Line2D([0], [0], color="#c44", label="measured"), Line2D([0], [0], color="k", ls="-.", label="NASA FEM theta=1")]
        PNL = 20
        for rank, i in enumerate(order):
            S = splits[i]; cs = sorted(S["chans"], key=lambda c: c["IS"])    # best (low IS) first
            for pg in range(0, len(cs), PNL):
                fig, axes = plt.subplots(4, 5, figsize=(13, 9)); axes = axes.ravel()
                for a in range(PNL):
                    ax = axes[a]
                    if pg + a >= len(cs):
                        ax.axis("off"); continue
                    c = cs[pg + a]
                    ax.fill_between(freqs, c["total"][0], c["total"][1], color="#cfd3d6", alpha=0.85, lw=0)
                    ax.fill_between(freqs, c["param"][0], c["param"][2], color="#9ec6e6", alpha=0.85, lw=0)
                    ax.plot(freqs, c["det"], color="k", lw=0.5, ls="-."); ax.plot(freqs, c["tru"], color="#c44", lw=0.8)
                    ax.set_xscale("log"); ax.set_yscale("log"); ax.set_xticks([]); ax.set_yticks([])
                    ax.set_title(f"ch{c['daq']} {'P' if c['covered'] else 'M'} IS{c['IS']:.0f}", fontsize=6.5,
                                 color=("#2a7" if c["covered"] else "#c33"))
                fig.legend(handles=legend, loc="upper center", ncol=4, fontsize=8, frameon=False, bbox_to_anchor=(0.5, 1.0))
                fig.suptitle(f"Run rank {rank+1}/{len(order)}  (seed {S['seed']}): median IS {S['run_IS']:.0f}, "
                             f"pass {S['pass_rate']*100:.0f}%, R-hat {S['rhat']:.3f}  — channels sorted best->worst",
                             fontsize=10, y=0.97)
                pdf.savefig(fig, bbox_inches="tight"); plt.close(fig)
    # pattern summary JSON
    always_fail = [d for d in daqs if loc[d]["pass_rate"] <= 0.34]
    always_pass = [d for d in daqs if loc[d]["pass_rate"] >= 0.95]
    summ = {"n_splits": len(splits), "runs_best_to_worst_seed": [splits[i]["seed"] for i in order],
            "run_median_IS_best_to_worst": [round(splits[i]["run_IS"], 1) for i in order],
            "run_pass_rate_best_to_worst": [round(splits[i]["pass_rate"], 2) for i in order],
            "n_locations": len(daqs),
            "consistently_fail_ch": always_fail, "consistently_pass_ch": always_pass,
            "corr_passrate_vs_log10DR": float(np.corrcoef(np.log10(ldr), pr)[0, 1]),
            "corr_passrate_vs_z": float(np.corrcoef(lz, pr)[0, 1]),
            "overall_pass_rate": float(np.mean([c["covered"] for s in splits for c in s["chans"]]))}
    (WS / "out" / "mc_pattern_summary.json").write_text(json.dumps(summ, indent=2))
    print(f"\nwrote out/mc_report.pdf + out/mc_pattern_summary.json")
    print(f"  consistently FAIL (pass<=0.34): {always_fail}")
    print(f"  consistently PASS (pass>=0.95): {len(always_pass)} channels")
    print(f"  pass-rate corr: log10 DR {summ['corr_passrate_vs_log10DR']:+.2f}, z-height {summ['corr_passrate_vs_z']:+.2f}")
    return summ


def run(n_splits=25):
    splits, freqs = compute_all(n_splits)
    loc = patterns(splits)
    return render(splits, freqs, loc)


if __name__ == "__main__":
    n = int(sys.argv[1]) if len(sys.argv) > 1 else 25
    run(n)
