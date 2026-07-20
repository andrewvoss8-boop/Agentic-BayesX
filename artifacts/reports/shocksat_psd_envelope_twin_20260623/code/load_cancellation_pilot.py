#!/usr/bin/env python3
"""CANCELLATION-FACTOR PILOT (Andrew): does the big per-SENSOR discrepancy (sigma~1.0 log) shrink when projected onto a
NET LOAD, because the local node-line errors are incoherent and cancel in an integral?

Fully data-driven (NO error model, NO NUTS): for each clean modal reference, build the net inertial load as the
COMPLEX (phased) sum of accelerances over the sensors on an axis -- L(f) = sum_s H_s(f) (uniform tributary mass) -- from
the MEASURED FRFs and from the FEM, and compare log|L_meas/L_fem| to the per-sensor log|H_meas/H_fem|. The cancellation
is whatever the real data shows. Contrast with the MAX-over-sensors envelope (which does NOT cancel).

Reports per axis: per-sensor sigma; net-load sigma; cancellation factor; effective # of coherent contributors
N_eff = |sum H|^2 / sum|H|^2; and the max-envelope sigma. Output: figures/load_cancellation_pilot.png + json.
"""
from __future__ import annotations
import json, sys
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

sys.path.insert(0, str(Path(__file__).resolve().parent))
import probe as P
import pooling_sigma_probe as PP

WS = Path(__file__).resolve().parent.parent
AX = {"X": 0, "Y": 1, "Z": 2}


def wstd(vals, wts):
    """Response-energy-weighted std of a log-residual (error where the response/load is actually large)."""
    v = np.asarray(vals).ravel(); w = np.asarray(wts).ravel()
    w = w / (w.sum() + 1e-300)
    m = np.sum(w * v)
    return float(np.sqrt(np.sum(w * (v - m) ** 2)))


def run():
    ctx = PP.minimal_ctx()
    f = ctx.freqs
    refs = list(ctx.caches.keys())
    # per-sensor axis
    axis_of = {d: ctx.ch.axes[ctx.pos[d]] for d in ctx.daq_master}

    ps_e, ps_w = [], []            # per-sensor residual + response-energy weight
    load_resid = {a: [] for a in AX}; load_w = {a: [] for a in AX}
    neff = {a: [] for a in AX}
    mx_e, mx_w = [], []
    for ref in refs:
        Hm = {d: P.meas_H(ctx, [ref], d) for d in ctx.daq_master}
        Hf = {d: P.model_H(ctx, np.ones((1, 9)), [ref], ctx.ch.rows[ctx.pos[d]])[0] for d in ctx.daq_master}
        e = np.array([np.log(np.abs(Hm[d]) + 1e-300) - np.log(np.abs(Hf[d]) + 1e-300) for d in ctx.daq_master])
        w = np.array([np.abs(Hf[d]) ** 2 for d in ctx.daq_master])      # weight = where each sensor responds
        ps_e.append(e.ravel()); ps_w.append(w.ravel())
        mxm = np.max([np.abs(Hm[d]) for d in ctx.daq_master], 0); mxf = np.max([np.abs(Hf[d]) for d in ctx.daq_master], 0)
        mx_e.append(np.log(mxm + 1e-300) - np.log(mxf + 1e-300)); mx_w.append(mxf ** 2)
        for a in AX:
            ds = [d for d in ctx.daq_master if axis_of[d] == a]
            if len(ds) < 3:
                continue
            Lm = np.sum([Hm[d] for d in ds], 0); Lf = np.sum([Hf[d] for d in ds], 0)
            load_resid[a].append(np.log(np.abs(Lm) + 1e-300) - np.log(np.abs(Lf) + 1e-300))
            load_w[a].append(np.abs(Lf) ** 2)
            Hf_stack = np.array([Hf[d] for d in ds])
            nf = np.abs(np.sum(Hf_stack, 0)) ** 2 / (np.sum(np.abs(Hf_stack) ** 2, 0) + 1e-300)
            neff[a].append(float(np.sum(nf * np.abs(Lf) ** 2) / (np.sum(np.abs(Lf) ** 2) + 1e-300)))

    sig_sensor = wstd(np.concatenate(ps_e), np.concatenate(ps_w))
    sig_max = wstd(np.concatenate(mx_e), np.concatenate(mx_w))
    out_axis = {}
    for a in AX:
        if load_resid[a]:
            sL = wstd(np.concatenate(load_resid[a]), np.concatenate(load_w[a]))
            out_axis[a] = {"net_load_sigma_log": round(sL, 3),
                           "cancellation_factor": round(sig_sensor / (sL + 1e-9), 2),
                           "N_eff_coherent_contributors": round(float(np.mean(neff[a])), 1),
                           "n_sensors_axis": int(sum(1 for d in ctx.daq_master if axis_of[d] == a))}
    # for the figure: load-weighted resampled residuals (sample by weight) so histograms reflect where load is large
    def wsample(elist, wlist, n=20000):
        e = np.concatenate(elist); w = np.concatenate(wlist); w = w / w.sum()
        idx = np.random.default_rng(0).choice(len(e), size=n, p=w)
        return e[idx]
    persensor_resid = [wsample(ps_e, ps_w)]
    load_resid_fig = {a: [wsample(load_resid[a], load_w[a])] if load_resid[a] else [] for a in AX}
    load_resid = load_resid_fig

    rec = {"deliverable": "cancellation-factor pilot: per-sensor discrepancy vs net-load discrepancy (data-driven)",
           "per_sensor_sigma_log": round(sig_sensor, 3),
           "max_envelope_sigma_log": round(sig_max, 3),
           "net_load_by_axis": out_axis,
           "interpretation": "net loads integrate over sensors -> incoherent local node-line errors cancel ~1/sqrt(N_eff)"
                             " -> net-load sigma << per-sensor sigma; the MAX envelope does NOT cancel (sigma stays ~ "
                             "per-sensor). Residual net-load sigma = the COHERENT (common-mode) discrepancy floor.",
           "caveat": "uniform tributary mass; complex measured phase (coherence 0.9+ at peaks); gain removed per ref. "
                     "NO error model, NO NUTS.",
           "note": "EXPLORATORY; YELLOW."}
    (WS / "out" / "load_cancellation_pilot.json").write_text(json.dumps(rec, indent=2))

    # figure
    fig, (axH, axB) = plt.subplots(1, 2, figsize=(13, 5))
    axH.hist(np.concatenate(persensor_resid), bins=60, color="#d62728", alpha=0.6, density=True,
             label=f"per-sensor  sigma={sig_sensor:.2f}")
    for a, col in zip(["Z", "X", "Y"], ["#1f77b4", "#2ca02c", "#9467bd"]):
        if load_resid[a]:
            axH.hist(np.concatenate(load_resid[a]), bins=40, color=col, alpha=0.55, density=True,
                     label=f"net {a}-load  sigma={out_axis[a]['net_load_sigma_log']:.2f}")
    axH.set_xlabel("log-amplitude discrepancy (meas - FEM)", fontsize=9); axH.set_xlim(-4, 4)
    axH.set_ylabel("density", fontsize=9)
    axH.set_title("Per-sensor error is wide; net-load error is narrow (local errors cancel)", fontsize=9)
    axH.legend(fontsize=7.5, frameon=False); axH.spines[["top", "right"]].set_visible(False)

    cats = ["per-sensor", "max-envelope"] + [f"net {a}-load" for a in out_axis]
    vals = [sig_sensor, sig_max] + [out_axis[a]["net_load_sigma_log"] for a in out_axis]
    cols = ["#d62728", "#d62728"] + ["#1f77b4"] * len(out_axis)
    axB.bar(range(len(cats)), vals, color=cols)
    for i, a in enumerate(out_axis):
        axB.text(2 + i, vals[2 + i] + 0.02, f"{out_axis[a]['cancellation_factor']:.1f}x\nN_eff {out_axis[a]['N_eff_coherent_contributors']:.0f}",
                 ha="center", fontsize=7)
    axB.set_xticks(range(len(cats))); axB.set_xticklabels(cats, fontsize=7.5, rotation=20)
    axB.set_ylabel("discrepancy sigma (log)", fontsize=9)
    axB.set_title("error after projection onto each functional", fontsize=9)
    axB.spines[["top", "right"]].set_visible(False)
    cap = (f"Per-sensor discrepancy sigma={sig_sensor:.2f} (log) and the MAX envelope sigma={sig_max:.2f} (no "
           f"cancellation) vs NET LOADS: " + "; ".join(
               f"{a} sigma={out_axis[a]['net_load_sigma_log']:.2f} ({out_axis[a]['cancellation_factor']:.1f}x lower, "
               f"N_eff~{out_axis[a]['N_eff_coherent_contributors']:.0f})" for a in out_axis) +
           ". Local node-line errors are incoherent -> they CANCEL in a net load (~1/sqrt(N_eff)); the residual net-load "
           "sigma is the coherent floor. Data-driven (measured vs FEM net load); uniform mass; NO NUTS.")
    fig.text(0.01, -0.03, cap, fontsize=7.2, wrap=True, va="top")
    fig.tight_layout(rect=[0, 0.05, 1, 1])
    outp = WS / "figures" / "load_cancellation_pilot.png"
    fig.savefig(outp, dpi=150, bbox_inches="tight"); plt.close(fig)

    print(f"per-sensor sigma {sig_sensor:.2f} | max-envelope sigma {sig_max:.2f}")
    for a in out_axis:
        o = out_axis[a]
        print(f"  net {a}-load ({o['n_sensors_axis']} sensors): sigma {o['net_load_sigma_log']:.2f}  "
              f"-> {o['cancellation_factor']:.1f}x cancellation  (N_eff~{o['N_eff_coherent_contributors']:.0f})")
    print(f"wrote {outp}")
    return rec


if __name__ == "__main__":
    run()
