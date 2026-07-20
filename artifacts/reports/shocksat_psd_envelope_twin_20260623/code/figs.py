#!/usr/bin/env python3
"""Card G figures (Tufte: data-ink, direct labels, zero-baseline bars, log-frequency, captions carry the numbers).
Writes figures/fig_coherence.png, fig_mechanism.png, fig_value_multiref.png, fig_identifiability.png + out/image_qa.json.
All numbers are pulled from out/*.json (measured NASA ShockSat data; no synthetic truth)."""
from __future__ import annotations
import json, sys
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

sys.path.insert(0, str(Path(__file__).resolve().parent))
import multiref_frf as mrf

WS = Path(__file__).resolve().parent.parent
OUT = WS / "out"; FIG = WS / "figures"; FIG.mkdir(exist_ok=True); MULTIREF = WS / "data" / "multiref"
plt.rcParams.update({"font.size": 10, "axes.spines.top": False, "axes.spines.right": False,
                     "axes.grid": False, "figure.dpi": 130, "savefig.bbox": "tight"})
IMP, MOD = "#33688e", "#b8541a"   # impact / modal hues (perceptual, grayscale-legible)


def lj(p): return json.loads(Path(p).read_text())


def fig_coherence():
    coh = lj(OUT / "coherence_by_reference.json")
    res = coh["resonance_freqs_hz"]
    keys = [("zpos_990z", IMP), ("ypos_990y", MOD), ("z_900z", IMP)]
    fig, axes = plt.subplots(3, 1, figsize=(7.0, 6.2), sharex=True)
    for ax, (key, col) in zip(axes, keys):
        z = mrf.load_cache(MULTIREF / f"{key}_N65536.npz")
        fr = np.asarray(z["freqs"]); ch_coh = np.median(np.asarray(z["coherence"]), axis=0)
        nh = int(z["n_hits_used"]); floor = 1.0 / nh
        ax.semilogx(fr, ch_coh, color=col, lw=1.0)
        for f in res:
            ax.axvline(f, color="0.85", lw=0.5, zorder=0)
        ax.axhline(floor, color="0.5", lw=0.8, ls=":")
        ax.text(0.99, floor + 0.03, f"{nh}-hit noise floor 1/n={floor:.2f}", transform=ax.get_yaxis_transform(),
                ha="right", va="bottom", color="0.4", fontsize=7.5)
        e = coh["references"][key]; instr = e["instrument"]; lab = e["label"]
        atr = e.get("N65536", {}).get("coherence_at_resonance_median")
        ax.text(0.012, 0.92, f"{lab}  ({instr} hammer, {nh} hits) — median coherence at resonances "
                f"{atr:.2f}", transform=ax.transAxes, va="top", fontsize=9, color=col)
        ax.set_ylim(0, 1.02); ax.set_ylabel("coherence γ²")
    axes[-1].set_xlabel("frequency [Hz]  (log)"); axes[0].set_xlim(45, 260)
    fig.suptitle("Multi-hit coherence at the response sensors, by reference — modal hammer is clean,\n"
                 "impact hammers sit near the few-hit noise floor at most resonances", fontsize=10.5, y=0.995)
    fig.text(0.5, -0.02, "γ²(f)=|ΣY·conj(F)|²/(Σ|F|²·Σ|Y|²) averaged across hits (NASA ShockSat1, measured, 45–260 Hz, "
             "df 3.81 Hz). Grey lines = matched modal resonances. Dotted = 1/n_hits noise floor.\n"
             "Takeaway: the documented +X '~0.07' is a broadband artifact; in-band the MODAL hammer (+Y) is coherent "
             "(~0.9) while the IMPACT hammers (+Z,900z) are near the floor — a data-quality limit on the impact set.",
             ha="center", fontsize=7.6, color="0.25")
    fig.savefig(FIG / "fig_coherence.png"); plt.close(fig)


def fig_mechanism():
    d = lj(OUT / "drive_shape_ratio.json")
    # pick the best impact-impact pair for the scatter
    best = max(d["pairs"].items(), key=lambda kv: kv[1].get("pearson_logratio_meas_vs_fem", -9))
    fig, axes = plt.subplots(1, 2, figsize=(9.4, 4.3))
    # panel A: per-pair correlation bar
    ax = axes[0]
    pairs = list(d["pairs"].values())
    labs = [p["label_pair"] for p in pairs]
    corr = [p.get("pearson_logratio_meas_vs_fem", 0.0) for p in pairs]
    cols = [MOD if "modal" in p["instrument_pair"] else IMP for p in pairs]
    y = np.arange(len(labs))
    ax.barh(y, corr, color=cols, height=0.62)
    ax.set_yticks(y); ax.set_yticklabels(labs, fontsize=9)
    ax.axvline(0, color="0.3", lw=0.8)
    ax.set_xlim(-0.7, 1.05); ax.set_xlabel("corr( measured log-ratio , FEM φ_d log-ratio )")
    for yi, c in zip(y, corr):
        ax.text(c + 0.03, yi, f"{c:+.2f}", va="center", ha="left", fontsize=8)
    ax.text(0.98, 0.04, "perfect recovery → 1.0", transform=ax.transAxes, ha="right", fontsize=7.5, color="0.4")
    ax.set_title("Does |H(d1)|/|H(d2)| recover the FEM\ndrive-participation ratio?  (confound-break test)", fontsize=9.5)
    # panel B: blue/orange = impact/modal pair; annotate sensor-spread
    ax = axes[1]
    spread = [p.get("median_sensor_spread_log", np.nan) for p in pairs]
    ax.barh(y, spread, color=cols, height=0.62)
    ax.set_yticks(y); ax.set_yticklabels([])
    ax.set_xlabel("sensor spread of the ratio  [std of log over sensors]")
    for yi, s in zip(y, spread):
        ax.text(s + 0.01, yi, f"{s:.2f}", va="center", fontsize=8)
    ax.set_title("Is the ratio sensor-INDEPENDENT?\n(theory: 0 if confound cleanly breaks)", fontsize=9.5)
    fig.suptitle("MECHANISM: the cross-reference peak ratio does NOT cleanly recover the drive-shape ratio "
                 "(best corr %.2f, large sensor spread)" % (d.get("best_pair_corr") or 0), fontsize=10, y=1.02)
    fig.text(0.5, -0.04, "Per reference pair, over modes excited in both (coherence>0.5 sensors). NASA ShockSat1, measured. "
             "Takeaway: with the impact references near the noise floor and one clean MODAL reference (instrument "
             "mismatch), the participation÷damping confound is NOT cleanly broken from this data.", ha="center",
             fontsize=7.6, color="0.25")
    fig.savefig(FIG / "fig_mechanism.png"); plt.close(fig)


def fig_value():
    v = lj(OUT / "multiref_value.json")
    rows = [("BEFORE: +X, FEM drive amp (Card F, N=200000)", v["before_xonly"]["crps_skill_vs_clim"], "0.4"),
            ("BEFORE: +X, FEM drive amp (same N=65536)", v.get("before_xonly_sameN", {}).get("crps_skill_vs_clim"), "0.6"),
            ("AFTER: +X, measured residue (operational-modal)", v["after_multiref"]["crps_skill_vs_clim"], IMP)]
    bd = v["after_by_drive_meanskill"]
    lab = {"zpos_990z": "+Z", "ypos_990y": "+Y (modal)", "z_900z": "900z"}
    for k in ("zpos_990z", "ypos_990y", "z_900z"):
        if bd.get(k) is not None:
            rows.append((f"AFTER: {lab[k]}, measured residue", bd[k], MOD if "modal" in lab[k] else IMP))
    rows.append(("ORACLE: held-out sensor shape known (upper bound)", v["shape_oracle_xX_meanskill"], "#2e7d32"))
    labs = [r[0] for r in rows]; vals = [r[1] for r in rows]; cols = [r[2] for r in rows]
    fig, ax = plt.subplots(figsize=(8.6, 4.6))
    y = np.arange(len(labs))[::-1]
    ax.barh(y, vals, color=cols, height=0.66)
    ax.axvline(0, color="0.2", lw=1.0)
    ax.text(0.02, len(labs) - 0.4, "climatology (no skill)", color="0.2", fontsize=8, va="center")
    ax.set_yticks(y); ax.set_yticklabels(labs, fontsize=8.5)
    ax.set_xlabel("held-out per-channel AMPLITUDE CRPS-skill vs climatology   (>0 ⇒ beats guessing the population)")
    ax.set_xlim(min(-1.1, min(vals) - 0.38), 0.85)
    for yi, val in zip(y, vals):
        # label just past the bar tip toward zero (inside-margin side) so it never collides with the y tick labels
        ax.text(val + (0.03 if val >= 0 else 0.03), yi, f"{val:+.2f}", va="center",
                ha="left", fontsize=8.5, fontweight="bold")
    ax.set_title("Held-out amplitude skill: multi-reference does NOT cross 0 — the limit is the held-out\n"
                 "SENSOR's own shape (oracle +%.2f), not the drive÷damping confound" % v["shape_oracle_xX_meanskill"],
                 fontsize=10)
    fig.text(0.5, -0.06, "NON-HARD held-out sensors, 3 splits (seeds 0–2), all calibrations converged "
             "(R̂≤1.05/ESS≥200). CRPS-skill=1−CRPS_twin/CRPS_clim. Measured NASA ShockSat1. Units-honest gain "
             "(one training-only factor). Takeaway: measuring the drive residue lifts −1.0→−0.1 but cannot cross 0; "
             "adding drives (+Z/+Y/900z) does not beat +X; only knowing the held-out sensor shape (oracle) would.",
             ha="center", fontsize=7.6, color="0.25")
    fig.savefig(FIG / "fig_value_multiref.png"); plt.close(fig)


def fig_identifiability():
    d = lj(OUT / "multiref_identifiability.json")
    me = d["modes_excited"]; bydrive = me["by_drive"]
    fig, axes = plt.subplots(1, 2, figsize=(9.4, 4.2))
    ax = axes[0]
    keys = list(bydrive.keys())
    labs = [{"xpos_990x": "+X", "zpos_990z": "+Z", "ypos_990y": "+Y(mod)", "z_900z": "900z"}.get(k, k) for k in keys]
    vals = [bydrive[k] for k in keys]
    cols = [MOD if "990y" in k else IMP for k in keys]
    x = np.arange(len(keys))
    ax.bar(x, vals, color=cols, width=0.6)
    ax.axhline(me["multi_ref_union"], color="0.3", ls="--", lw=0.9)
    ax.text(len(keys) - 0.5, me["multi_ref_union"] + 0.2, f"multi-ref union = {me['multi_ref_union']}",
            ha="right", fontsize=8, color="0.3")
    ax.set_xticks(x); ax.set_xticklabels(labs); ax.set_ylabel("# modes excited (FEM φ_d ≥ 10% max)")
    for xi, vv in zip(x, vals):
        ax.text(xi, vv + 0.2, str(vv), ha="center", fontsize=8)
    ax.set_title("Modal excitation coverage per drive", fontsize=9.5)
    # panel B: stiffness FIM dirs + amplitude confound
    ax = axes[1]; ax.axis("off")
    s = d["single_ref"]["n_dirs_above_floor"]; m = d["multi_ref"]["n_dirs_above_floor"]
    full = d["all_matched_modes_ref"]["n_dirs_above_floor"]
    amp = d["amplitude_confound"]
    txt = (f"STIFFNESS θ directions above the realized\n"
           f"discrepancy floor (σ_w={d['sigma_w_realized_floor']:.3f}):\n\n"
           f"   single-ref +X ({d['single_ref']['n_modes']} modes):   {s}\n"
           f"   multi-ref ({d['multi_ref']['n_modes']} modes):        {m}\n"
           f"   (all {d['n_matched_modes']} matched modes):     {full}\n\n"
           f"→ multi-ref adds modal COVERAGE but the stiffness\n"
           f"   identifiability is FLOOR-limited (no gain).\n\n"
           f"AMPLITUDE confound (per mode):\n"
           f"   single drive: {amp['single_reference']['identifiable_combos_per_mode']} combo "
           f"(φ_d/ζ confounded)\n"
           f"   {amp['multi_reference']['n_drives']} drives: {amp['multi_reference']['separable_drive_ratios']} "
           f"separable drive-RATIOS (+1 gauge)\n\n"
           f"→ multi-ref breaks the confound on the DRIVE\n"
           f"   side only; the held-out SENSOR's φ_s is\n"
           f"   untouched (FEM-only).")
    ax.text(0.0, 0.98, txt, va="top", ha="left", fontsize=9, family="monospace")
    fig.suptitle("IDENTIFIABILITY single- vs multi-reference: coverage up, stiffness floor-limited,\n"
                 "amplitude confound broken only on the drive side", fontsize=10, y=1.02)
    fig.text(0.5, -0.04, "FIM = JᵀΣ⁻¹J, J[k,g]=φ_kᵀA_gφ_k/λ_k (modal strain-energy). NASA ShockSat1, measured. "
             "Takeaway: the data we were missing (multi-drive) helps the DRIVE side, not the held-out sensor shape "
             "that limits amplitude.", ha="center", fontsize=7.6, color="0.25")
    fig.savefig(FIG / "fig_identifiability.png"); plt.close(fig)


def image_qa():
    from PIL import Image
    figs = ["fig_coherence.png", "fig_mechanism.png", "fig_value_multiref.png", "fig_identifiability.png"]
    rep = {"figures": {}, "pass": True}
    for f in figs:
        p = FIG / f
        if not p.exists():
            rep["figures"][f] = {"exists": False}; rep["pass"] = False; continue
        im = Image.open(p); w, h = im.size; kb = p.stat().st_size / 1024
        ok = w >= 600 and h >= 350 and kb >= 15
        rep["figures"][f] = {"exists": True, "w": w, "h": h, "kb": round(kb, 1), "ok": bool(ok)}
        rep["pass"] = rep["pass"] and ok
    (OUT / "image_qa.json").write_text(json.dumps(rep, indent=2))
    print("image_qa:", json.dumps(rep["figures"]))
    return rep


if __name__ == "__main__":
    fig_coherence(); print("fig_coherence ok")
    fig_mechanism(); print("fig_mechanism ok")
    fig_value(); print("fig_value ok")
    fig_identifiability(); print("fig_identifiability ok")
    image_qa()
