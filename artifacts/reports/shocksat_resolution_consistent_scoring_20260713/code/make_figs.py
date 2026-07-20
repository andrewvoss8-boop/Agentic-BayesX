#!/usr/bin/env python3
"""Figures for the resolution-consistent scoring run (Tufte skill applied; saved .py for lint/replay).
All panels show MEASURED NASA ShockSat data or scores derived from it; every figure carries a run stamp and
its validity caveats ON the figure. Frequency axes are log-scaled (project rule). Scores are unitless
correlations (linear axes). No dB except P4 (dB is standard for FRF peak-height error); stated on the figure.
Deliberate deviations: none beyond small in-figure tables (Tufte-endorsed words+numbers integration)."""
import json, os, sys
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

MY = os.path.dirname(os.path.abspath(__file__))
WS = os.path.abspath(os.path.join(MY, ".."))
ROOT = os.path.abspath(os.path.join(WS, "..", "..", ".."))
sys.path.insert(0, MY)
import wforward as WF
import wscore as SC
import femlib as F

OUT, FIGS = os.path.join(WS, "out"), os.path.join(WS, "figures")
os.makedirs(FIGS, exist_ok=True)
STAMP = "run shocksat_resolution_consistent_scoring_20260713 | NASA ShockSat measured modal caches"
plt.rcParams.update({"font.size": 10, "axes.spines.top": False, "axes.spines.right": False,
                     "axes.grid": False, "figure.dpi": 150})

dev, vault = {}, {}
for line in open(os.path.join(OUT, "score_log.jsonl")):
    r = json.loads(line)
    (vault if r["stage"] == "vault" else dev)[r["arm"]] = r
vd = json.load(open(os.path.join(OUT, "verdicts.json")))
gw = json.load(open(os.path.join(OUT, "gate_W.json")))
ARMS = ["B0", "B1", "B2", "B3", "B4", "B5"]
DESC = {"B0": "naive\nζ=1%", "B1": "naive\nsurvey ζ", "B2": "window\nsurvey ζ", "B3": "window\nζ=1%",
        "B4": "window\nERA band", "B5": "window\nsurvey ζ\n(c06 shape)"}

# ----------------------------------------------------------------- fig_money
fig, ax = plt.subplots(figsize=(8.6, 5.0))
for i, a in enumerate(ARMS):
    folds = [v for v in dev[a]["P1p_folds"].values() if v is not None]
    ax.plot([i] * len(folds), folds, "o", ms=4, color="0.65", zorder=2)
    ax.plot([i - 0.18, i + 0.18], [dev[a]["P1p_mean"]] * 2, "-", lw=2.4, color="k", zorder=3)
    ax.annotate(f"{dev[a]['P1p_mean']:.3f}", (i + 0.22, dev[a]["P1p_mean"]), fontsize=9, va="center")
    ax.plot(i, vault[a]["P1p_mean"], "D", ms=6, mfc="none", mec="#b3541e", mew=1.4, zorder=3)
ax.axhline(dev["B0"]["P1p_mean"], color="0.8", lw=0.8, zorder=1)
ax.annotate("B0 incumbent", (-0.42, dev["B0"]["P1p_mean"] + 0.006), fontsize=8, color="0.4")
s1 = vd["S1"]
ax.annotate("vault (+XY, open diamonds): SECOND program read; known easy-location\n"
            "offset (+0.22..0.30 in both prior runs) — confirmation only, never a win",
            (0.7, 0.60), fontsize=8, color="#b3541e")
ax.set_xticks(range(6)); ax.set_xticklabels([f"{a}\n{DESC[a]}" for a in ARMS], fontsize=9)
ax.set_ylim(-0.25, 0.66)
ax.set_ylabel("P1' (FDAC-aligned FRAC, unitless)")
ax.set_title("Dev P1' by arm: gray dots = 4 leave-one-drive-out folds, black = fold mean", fontsize=11)
ax.text(0.0, -0.33,
        f"S1 verdict: Δ(B2−B0) = {s1['delta_dev_P1p']:+.4f} ≥ +0.03 ✓ and vault B2>B0 ✓, "
        f"BUT < 2×fold-SE ({2*s1['fold_se_delta']:.4f}) → PRE-REGISTERED CLAIM FALSIFIED (noise-floor rule).\n"
        f"Gate W FAILED → mechanism certification incomplete (see packet §5). {STAMP}",
        transform=ax.transAxes, fontsize=8, va="top", color="0.25")
fig.tight_layout(); fig.savefig(os.path.join(FIGS, "fig_money.png"), bbox_inches="tight"); plt.close(fig)

# ----------------------------------------------------------------- fig_s2_decomp
s2 = vd["S2"]
labels = ["window\nalone\nB3−B0", "damping\nalone\nB1−B0", "inter-\naction\nB2−B1−B3+B0", "total\n\nB2−B0"]
vals = [s2["window_alone"], s2["damping_alone"], s2["interaction"], s2["total"]]
fig, ax = plt.subplots(figsize=(8.4, 4.6))
bars = ax.bar(range(4), vals, width=0.55, color=["#2d5f8a", "#8a2d2d", "#5a8a2d", "0.3"])
ax.axhline(0, color="k", lw=0.8)
for i, v in enumerate(vals):
    ax.annotate(f"{v:+.4f}", (i, v + (0.0015 if v >= 0 else -0.004)), ha="center", fontsize=10)
ax.set_xticks(range(4)); ax.set_xticklabels(labels, fontsize=9)
ax.set_ylabel("Δ dev P1' (unitless)")
ax.set_title("S2 attribution: the gain is the WINDOW, not the damping", fontsize=11)
ax.text(0.0, -0.26, "damping+interaction = +0.0069 < ½·total (+0.0201) → 'consistent processing lets physical "
        f"damping be used\ncorrectly' NOT supported; flat 1% under the window does as well. {STAMP}",
        transform=ax.transAxes, fontsize=8, va="top", color="0.25")
fig.tight_layout(); fig.savefig(os.path.join(FIGS, "fig_s2_decomp.png"), bbox_inches="tight"); plt.close(fig)

# ----------------------------------------------------------------- fig_gateW_overlay
z = np.load(os.path.join(WS, "data", "gateW_overlay.npz"))
fc, Srms, Hs, u = z["freqs"], z["Srms_t07"], np.abs(z["H1_stored"]), z["usable"]
cors = []
for i in u:
    a, b = np.log10(Srms[i] + 1e-300), np.log10(Hs[i] + 1e-300)
    cors.append((float(np.corrcoef(a, b)[0, 1]), int(i)))
best = sorted(cors, reverse=True)[0]
med = sorted(cors, reverse=True)[len(cors) // 2]
fig, axes = plt.subplots(2, 1, figsize=(8.6, 6.4))
ax = axes[0]
i = best[1]
a = np.log10(Hs[i] + 1e-300)
b = np.log10(Srms[i] + 1e-300); b = b - np.median(b) + np.median(a)     # shape-only alignment (no force)
ax.plot(fc, a, "k-", lw=1.2)
ax.plot(fc, b, "-", color="#b3541e", lw=1.0)
ax.annotate("stored cache |H1| (Test01 modal, g/lbf)", (fc[2], a.max() + 0.15), fontsize=9)
ax.annotate("Test07 windowed response spectrum (median-aligned:\nNO force channel → shape-only)",
            (110, b.min() - 0.1), fontsize=9, color="#b3541e")
ax.set_xscale("log"); ax.set_xlabel("frequency [Hz] (log)"); ax.set_ylabel("log10 magnitude")
ax.set_title(f"Gate W overlay — best-corr usable channel (corr {best[0]:.2f}; median over channels "
             f"{gw['t01_t07_shape_bonus']['median_logmag_corr']:.2f})", fontsize=10)
ax2 = axes[1]
pk = gw["window_physics_stored_cache_REPORTED"]["per_peak"]
zp = [p["zeta_pred_apparent"] * 100 for p in pk]; zm = [p["zeta_meas_stored_cache"] * 100 for p in pk]
ax2.plot([0.3, 8], [0.3, 8], "k-", lw=0.8)
ax2.fill_between([0.3, 8], [0.3 * 0.75, 8 * 0.75], [0.3 * 1.25, 8 * 1.25], color="0.9", zorder=0)
ax2.plot(zp, zm, "o", ms=6, color="#2d5f8a")
NUDGE = {75: (6, 4), 120: (6, 4), 163: (-42, -4), 172: (6, -3), 188: (8, -12), 233: (8, 3), 244: (6, 4)}
for p in pk:
    dx, dy = NUDGE.get(int(round(p["f_hz"])), (5, 4))     # hand-placed to avoid the 163/188/233 cluster
    ax2.annotate(f"{p['f_hz']:.0f} Hz", (p["zeta_pred_apparent"] * 100, p["zeta_meas_stored_cache"] * 100),
                 fontsize=8, xytext=(dx, dy), textcoords="offset points")
ax2.set_xscale("log"); ax2.set_yscale("log")
ax2.set_xlabel("predicted apparent ζ = ζ_ERA + ζ_w(f)  [% critical] (log)")
ax2.set_ylabel("measured apparent ζ,\nSTORED cache [%] (log)")
ax2.set_title("Window-physics fit on the stored cache: isolated peaks agree; dense peaks\n"
              "absorb neighbors → GATE W FAILED (±25% band shaded)", fontsize=10)
fig.text(0.02, -0.01, f"GATE W: FAIL (pre-registered thresholds). Test07 force channel DEAD in all 4 hits "
         f"(~1 lb noise vs 1000–1900 g impacts) → direct H1 recompute impossible. {STAMP}", fontsize=8,
         color="#8a2d2d")
fig.tight_layout(); fig.savefig(os.path.join(FIGS, "fig_gateW_overlay.png"), bbox_inches="tight"); plt.close(fig)

# ----------------------------------------------------------------- fig_apparent_zeta
mm = np.load(os.path.join(ROOT, "artifacts/reports/shocksat_fem_remesh_20260618/measured_modes.npz"))
era = np.load(os.path.join(ROOT, "scratch_test07/era_result.npz"))
fgrid = np.geomspace(45, 260, 300)
fig, ax = plt.subplots(figsize=(8.2, 5.2))
ax.plot(fgrid, WF.zeta_w(fgrid) * 100, "-", color="#2d5f8a", lw=1.6)
ax.annotate("ζ_w(f) = 1/(2πfτ): exp-window ADDED damping\n(τ = 0.164 s, recovered from the distiller)",
            (47, 2.6), fontsize=9, color="#2d5f8a")
surv_f, surv_z = np.asarray(mm["freqs"], float), np.asarray(mm["damp"], float)
ax.plot(surv_f, surv_z, "o", ms=4, color="0.45")
ax.annotate("survey per-mode ζ\n(NASA .ash, 33 modes)", (70, 0.135), fontsize=9, color="0.35")
M = np.asarray(era["matched"])
ax.plot(M[:, 2], M[:, 3] * 100, "x", ms=5, color="#5a8a2d")
ax.annotate("ERA ζ (raw Test07\ndecay, 27 matched)", (47, 0.062), fontsize=9, color="#5a8a2d")
zapp = np.interp(fgrid, np.sort(surv_f), surv_z[np.argsort(surv_f)] / 100) + WF.zeta_w(fgrid)
ax.plot(fgrid, zapp * 100, "--", color="k", lw=1.2)
ax.annotate("apparent ζ in the 2 Hz caches\n= survey ζ + ζ_w(f)", (152, 1.55), fontsize=9)
ax.axhline(1.0, color="#b3541e", lw=1.0, ls=":")
ax.annotate("flat 1% (incumbent A0)", (195, 0.86), fontsize=9, color="#b3541e")
ax.set_xscale("log"); ax.set_yscale("log")
ax.set_xlim(45, 262); ax.set_ylim(0.04, 4.5)
ax.set_xlabel("frequency [Hz] (log)"); ax.set_ylabel("ζ [% critical] (log)")
ax.set_title("Why 1% 'worked': the exp window adds ζ_w(f) ≈ 0.4–1.6% to every mode", fontsize=11)
ax.text(0.0, -0.17, "survey (NASA .ash) and ERA agree: true damping ~0.3%; the distillation window\n"
        f"makes it LOOK like 1–2%. {STAMP}", transform=ax.transAxes, fontsize=8, color="0.25")
fig.tight_layout(); fig.savefig(os.path.join(FIGS, "fig_apparent_zeta.png"), bbox_inches="tight"); plt.close(fig)

# ----------------------------------------------------------------- fig_peak_zoom
pkg = F.Package.load("A0_enr")
theta = np.asarray(pkg.theta_map()[0], float)
caches = SC.load_caches()
c = caches["m_xpos_990x"]; fcx = c["freqs"]
rows, cols = SC._usable(pkg, c)
surv = {"kind": "permode_survey_interp"}
# choose 3 MATCHED pairs (MAC>=0.5, |df|<=2%) spread over the band; zoom centered on the MODEL peak so the
# model's peak (2.5-3.3% modal error vs measured) is inside the window — the width/height story, not a dip
f_el, _ = pkg.modes(theta)
pairs = np.asarray(pkg.pairs); mfr = np.asarray(pkg.mfreqs, float)
cand = [(mfr[int(r)], f_el[int(k)], mac) for r, k, mac in pairs
        if mac >= 0.5 and 50 < mfr[int(r)] < 255 and abs(f_el[int(k)] / mfr[int(r)] - 1) <= 0.035]
picks = []
for flo, fhi in ((50, 90), (90, 160), (160, 255)):
    cc = [p for p in cand if flo <= p[0] < fhi]
    if cc:
        picks.append(max(cc, key=lambda p: p[2]))
while len(picks) < 3 and len(cand) > len(picks):          # fill from best remaining if a band is empty
    rest = [p for p in cand if p not in picks]
    picks.append(max(rest, key=lambda p: p[2]))
picks = sorted(picks)[:3]
fig, axes = plt.subplots(1, 3, figsize=(11.0, 4.1), sharey=False)
fine = np.arange(45.0, 262.0, 0.05)
Hn_1 = WF.predict_logH(pkg, theta, {"kind": "fixed", "zeta": 0.01}, "m_xpos_990x", fine, windowed=False)
Hn_s = WF.predict_logH(pkg, theta, surv, "m_xpos_990x", fine, windowed=False)
Hw_s = WF.predict_logH(pkg, theta, surv, "m_xpos_990x", fcx, windowed=True)
for ax, (fm, fe, mac) in zip(axes, picks):
    ctr = 0.5 * (fm + fe)
    lo, hi = ctr - 5.0, ctr + 5.0
    selm = (fcx >= lo) & (fcx <= hi); self_ = (fine >= lo) & (fine <= hi)
    kb = int(np.argmin(np.abs(fcx - fm)))
    j = int(np.argmax([np.abs(c["H1"][ci][kb]) for ci in cols]))
    r, ci = rows[j], cols[j]
    ym = np.log10(np.abs(c["H1"][ci][selm]) + 1e-300)

    def edge_align(y, x, ym=ym, xm=fcx[selm]):
        """align at window EDGES (outer 25% each side) so PEAK-height differences remain visible."""
        edge = (x <= lo + 2.0) | (x >= hi - 2.0)
        edgem = (xm <= lo + 2.0) | (xm >= hi - 2.0)
        return y - np.median(y[edge]) + np.median(ym[edgem])
    ax.plot(fcx[selm], ym, "ko", ms=5)
    ax.plot(fine[self_], edge_align(Hn_s[r][self_], fine[self_]), "-", color="#5a8a2d", lw=1.1)
    ax.plot(fine[self_], edge_align(Hn_1[r][self_], fine[self_]), "-", color="#b3541e", lw=1.1)
    ax.plot(fcx[selm], edge_align(Hw_s[r][selm], fcx[selm]), "s-", color="#2d5f8a", lw=1.4, ms=4, mfc="none")
    ax.axvline(fm, color="0.85", lw=0.8, zorder=0)
    ax.set_xlim(lo, hi); ax.set_xlabel("frequency [Hz]\n(linear: 10 Hz zoom)")
    ax.set_title(f"matched mode: meas {fm:.1f} Hz / model {fe:.1f} Hz\nMAC {mac:.2f}, DAQ ch {c['daq'][ci]}",
                 fontsize=9)
axes[0].set_ylabel("log10 |H| [g/lbf] (edge-aligned)")
axes[2].annotate("measured cache (2 Hz bins)", (0.02, 0.95), xycoords="axes fraction", fontsize=8)
axes[2].annotate("naive + survey ζ~0.3% (0.05 Hz grid)", (0.02, 0.88), xycoords="axes fraction", fontsize=8,
                 color="#5a8a2d")
axes[2].annotate("naive + ζ=1%", (0.02, 0.81), xycoords="axes fraction", fontsize=8, color="#b3541e")
axes[2].annotate("WINDOWED + survey ζ (2 Hz bins)", (0.02, 0.74), xycoords="axes fraction", fontsize=8,
                 color="#2d5f8a")
fig.text(0.02, -0.03, "model curves aligned at the zoom-window EDGES (display only; scoring uses the "
         "train-side global gain), so relative peak heights are preserved.\nGray vertical line = measured "
         f"mode. +X drive, measured NASA cache vs A0_enr model. {STAMP}", fontsize=8, color="0.25")
fig.tight_layout(); fig.savefig(os.path.join(FIGS, "fig_peak_zoom.png"), bbox_inches="tight"); plt.close(fig)

# ----------------------------------------------------------------- heuristic QA + visual-review merge
qa = {}
vis_p = os.path.join(OUT, "fig_qa_visual.json")
vis = json.load(open(vis_p)) if os.path.exists(vis_p) else {}
for f in ("fig_money.png", "fig_s2_decomp.png", "fig_gateW_overlay.png", "fig_apparent_zeta.png",
          "fig_peak_zoom.png"):
    p = os.path.join(FIGS, f)
    auto_ok = os.path.exists(p) and os.path.getsize(p) > 30000
    v = vis.get(f, {})
    qa[f] = {"exists": os.path.exists(p), "size_B": os.path.getsize(p) if os.path.exists(p) else 0,
             "auto_pass": bool(auto_ok),
             "visual_review": v.get("visual_review", "PENDING lead visual check"),
             "pass": bool(auto_ok and v.get("pass", False))}
json.dump(qa, open(os.path.join(OUT, "fig_qa.json"), "w"), indent=1)
print("figures written; QA:", {k: v["pass"] for k, v in qa.items()})
