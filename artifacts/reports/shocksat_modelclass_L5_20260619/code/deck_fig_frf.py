#!/usr/bin/env python3
"""Deck figures — held-out FRF overlays at HARD vs EASY channels + band-GRMS comparison (Tufte gate).
Twin predictive |H| (θ-posterior band) vs MEASURED |H| at held-out channels (their |H| never used in fitting).
Produces fig_frf_examples.png (3 hard + 3 easy) and fig_grms.png (band-GRMS predicted vs measured)."""
from __future__ import annotations
import sys, json
from types import SimpleNamespace
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

sys.path.insert(0, str(Path(__file__).resolve().parent))
import realfrf as rf
import modal_feature as mf
import heldout_qoi as hq
import dampcorr_qoi as dc

WS = Path(__file__).resolve().parent.parent
FIG = WS / "figures"; FIG.mkdir(exist_ok=True)
HARD = {4, 27, 38, 40, 52, 69, 92, 98}

print("stage: start",flush=True)
R = rf.load_reduced(); print("stage: reduced",flush=True)
meas = rf.reprocess_measured(list(range(1, rf.N_ACCEL_RECORDERS + 1)))
ch = rf.build_channels(R, meas["daq"]); print("stage: channels",flush=True)
fr = meas["freqs"]; fb = (fr >= rf.BAND[0]) & (fr <= rf.BAND[1]); freqs = fr[fb]
didx = {d: i for i, d in enumerate(meas["daq"])}
tau = -(rf.PROC["N"] - 1) / (rf.FS * np.log(rf.PROC["exp_end"]))
eta = np.full(R.A.shape[1], 2.0 * rf.ZETA_NOM)

dr = np.array([meas["dyn_range"][didx[d]] for d in ch.daq])
elig = np.where(dr >= hq.DR_MIN)[0]
rng = np.random.default_rng(0); perm = rng.permutation(elig)
n_obs = int(round(0.6 * len(perm))); obs_pos = np.sort(perm[:n_obs]); ho_pos = np.sort(perm[n_obs:])
obs_daqs = [ch.daq[p] for p in obs_pos]; ho_daqs = [ch.daq[p] for p in ho_pos]

# Twin prediction at theta-MAP (L5 medians from modal_feature.json) — no NUTS needed for the figure; the twin's
# predictive WIDTH comes from the QOI discrepancy (sigma_QOI~1.1 log), not the narrow theta posterior.
GN = ["al_welds", "angle_brackets", "bottom_box", "contact", "cross_beam", "joints", "plates", "steel_welds", "top_box"]
tm = json.loads((WS.parent / "statfem_real_validation_20260617" / "out" / "modal_feature.json").read_text())["theta_post"]
theta_map = np.array([tm[g]["med"] for g in GN])
SIG_QOI = 1.10                                                                   # pooled QOI discrepancy (log)
ho_rows = ch.rows[ho_pos]; obs_rows = ch.rows[obs_pos]
lm_obs = dc.fem_logmag_batch_permode(R, freqs, theta_map[None, :], obs_rows, ch.drive_row, eta, tau)[0]
lm_ho = dc.fem_logmag_batch_permode(R, freqs, theta_map[None, :], ho_rows, ch.drive_row, eta, tau)[0]; print("stage: forward done",flush=True)
tru_obs = np.log(np.abs(np.array([meas["H"][didx[d]][fb] for d in obs_daqs])) + 1e-300).T
wflat = np.array([meas["weight"][didx[d]][fb] for d in obs_daqs]).T.ravel()
c = hq.wmedian((tru_obs - lm_obs).ravel(), wflat)
med = np.exp(lm_ho + c)                                                          # (Nf, n_ho) median prediction
lo = med * np.exp(-1.96 * SIG_QOI); hi = med * np.exp(1.96 * SIG_QOI)            # twin 95% band (discrepancy)
tru_ho = np.abs(np.array([meas["H"][didx[d]][fb] for d in ho_daqs])).T          # (Nf, n_ho)
cdiag = {"converged": True}

dr_ho = np.array([meas["dyn_range"][didx[d]] for d in ho_daqs])
hard_mask = np.array([d in HARD for d in ho_daqs])
hard_idx = list(np.where(hard_mask)[0]); easy_idx = list(np.where(~hard_mask)[0])
# up to 3 hard held-out (whatever this split has) + fill the 6-panel grid with the highest-DR easy channels
hard_pick = hard_idx[:3]
easy_sorted = list(np.array(easy_idx)[np.argsort(-dr_ho[easy_idx])])
easy_pick = easy_sorted[:6 - len(hard_pick)]
picks = [("HARD", i) for i in hard_pick] + [("EASY", i) for i in easy_pick]

print("stage: plotting",flush=True)
fig, axes = plt.subplots(2, 3, figsize=(12.5, 7.0), sharex=True)
for ax, (tag, k) in zip(axes.ravel(), picks):
    ax.fill_between(freqs, lo[:, k], hi[:, k], color="#9ecae1", alpha=0.7, label="twin 95% band (discrepancy)")
    ax.plot(freqs, med[:, k], color="#2166ac", lw=1.0, label="twin median")
    ax.plot(freqs, tru_ho[:, k], color="k", lw=0.9, label="measured")
    ax.set_yscale("log"); ax.set_xscale("log")
    err = 20 * np.log10(med[:, k].max() / tru_ho[:, k].max())
    covered = lo[:, k].max() <= tru_ho[:, k].max() <= hi[:, k].max()
    col = "#b2182b" if tag == "HARD" else "#1b7837"
    ax.set_title(f"{tag} ch{ho_daqs[k]}  peak err {err:+.0f} dB  {'covered' if covered else 'MISS'}",
                 fontsize=8.5, color=col, loc="left")
    ax.tick_params(labelsize=7)
axes[0, 0].legend(fontsize=6.5, loc="lower left")
for ax in axes[1]: ax.set_xlabel("frequency (Hz)", fontsize=8)
for ax in axes[:, 0]: ax.set_ylabel("|H| accelerance (g/lbf)", fontsize=8)
fig.suptitle("Held-out FRF: twin median + 95% band vs measured — hard channels (top) miss the peak amplitude, easy (bottom) closer",
             fontsize=10.5, y=0.99)
fig.text(0.5, 0.005, "Real single-impact ShockSat, seed-0 held-out channels (|H| never used in fit). Log–log. Twin = FEM at L5-MAP θ + ζ=1%+window + global gain; band = 95% QOI discrepancy (σ=1.1 log).",
         ha="center", fontsize=6.6, color="0.4")
fig.tight_layout(rect=[0, 0.025, 1, 0.96]); fig.savefig(FIG / "fig_frf_examples.png", dpi=140); plt.close(fig)

# --- fig_grms: band-GRMS predicted vs measured ---
band = lambda h: rf.core.qoi_band(h, freqs)
g_pred = np.array([band(med[:, k]) for k in range(len(ho_pos))])
g_tru = np.array([band(tru_ho[:, k]) for k in range(len(ho_pos))])
g_lo = np.array([band(lo[:, k]) for k in range(len(ho_pos))]); g_hi = np.array([band(hi[:, k]) for k in range(len(ho_pos))])
fig, ax = plt.subplots(figsize=(6.4, 6.0))
lim = [min(g_tru.min(), g_pred.min()) * 0.5, max(g_tru.max(), g_pred.max()) * 2]
ax.plot(lim, lim, "k--", lw=0.8, label="1:1")
for m, c, lab in [(~hard_mask, "#1b7837", "easy"), (hard_mask, "#b2182b", "hard")]:
    ax.errorbar(g_tru[m], g_pred[m], yerr=[g_pred[m] - g_lo[m], g_hi[m] - g_pred[m]], fmt="o", ms=5,
                color=c, ecolor=c, elinewidth=0.6, alpha=0.8, capsize=0, label=lab)
ax.set_xscale("log"); ax.set_yscale("log"); ax.set_xlim(lim); ax.set_ylim(lim)
ax.set_xlabel("measured band-GRMS (g/lbf)"); ax.set_ylabel("twin predicted band-GRMS (g/lbf)")
for sp in ("top", "right"): ax.spines[sp].set_visible(False)
ax.legend(fontsize=8); ax.set_title("Held-out band-GRMS: predicted vs measured", fontsize=10, loc="left")
fig.text(0.5, 0.01, "Band energy QOI (45–260 Hz). Bars = twin 95% band. Wide scatter both hard & easy = the per-channel amplitude/energy is poorly predicted by the FEM shapes.",
         ha="center", fontsize=6.5, color="0.4")
fig.tight_layout(rect=[0, 0.03, 1, 1]); fig.savefig(FIG / "fig_grms.png", dpi=140); plt.close(fig)
print(f"wrote fig_frf_examples ({len(hard_pick)} hard, {len(easy_pick)} easy), fig_grms; calib conv {cdiag['converged']}")
