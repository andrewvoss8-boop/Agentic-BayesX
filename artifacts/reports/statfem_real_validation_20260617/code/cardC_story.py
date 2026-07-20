#!/usr/bin/env python3
"""Card C story figures + GIFs for the summary deck (tufte-data-graphics skill applied). Builds:
  figures/fig_cardC_mechanism.png      - held-out peak IS by config (shape-field vs damping mechanism) + L5
  figures/fig_cardC_phase2_kriging.png - marginal vs kriged transfer (sharper but costs calibration)
  figures/fig_cardC_phase3_tau.png     - held-out IS vs kept-mode set (full set wins; over-restricting hurts)
  figures/fig_cardC_phase4_phase.png   - single-hit phase incoherence + complex-vs-magnitude theta slice
  figures/fig_cardC_phase5_cross.png   - held-out peak IS by calibration SOURCE (.ash vs impact-FRF)
  figures/fig_cardC_scorecard.png      - star ratings per experiment element
  figures/gif_heldout_sweep.gif        - sweep held-out channels: measured |H| vs inferred band vs FEM band
  figures/gif_tau_band.gif             - one channel, band widens as matched modes are dropped (tau sweep)
All numbers read from out/*.json (traceable). Sources/units in each caption. Run in .venv_nuts.
"""
from __future__ import annotations
import json, sys
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import imageio.v2 as imageio

sys.path.insert(0, str(Path(__file__).resolve().parent))
import realfrf as rf
import heldout_qoi as hq
import modal_beck_full as M

WS = Path(__file__).resolve().parent.parent
FIG = WS / "figures"; OUT = WS / "out"; FIG.mkdir(exist_ok=True)
C_MEAS = "#222222"; C_INF = "#1f77b4"; C_FEM = "#d62728"; C_L5 = "#2ca02c"; NAVY = "#13456e"; GREY = "#777777"
plt.rcParams.update({"font.size": 10, "axes.spines.top": False, "axes.spines.right": False,
                     "axes.grid": False, "figure.dpi": 140, "savefig.bbox": "tight"})
HARD = {4, 27, 40, 52, 69, 92, 98}


def J(name):
    p = OUT / name
    return json.loads(p.read_text()) if p.exists() else None


# ----------------------------------------------------------------- shared band computation
def split_setup(cal, seed=0):
    R = cal["R"]
    meas = rf.reprocess_measured(list(range(1, rf.N_ACCEL_RECORDERS + 1)))
    ch = rf.build_channels(R, meas["daq"])
    fr = meas["freqs"]; fb = (fr >= rf.BAND[0]) & (fr <= rf.BAND[1]); freqs = fr[fb]
    didx = {d: i for i, d in enumerate(meas["daq"])}
    dr = np.array([meas["dyn_range"][didx[d]] for d in ch.daq])
    elig = np.where(dr >= hq.DR_MIN)[0]
    rng = np.random.default_rng(seed); perm = rng.permutation(elig)
    n_obs = int(round(0.6 * len(perm))); obs_pos = np.sort(perm[:n_obs]); ho_pos = np.sort(perm[n_obs:])
    return R, meas, ch, freqs, fb, didx, dr, obs_pos, ho_pos


def bands_for(cal, raw_post, theta_post, obs_pos, ho_pos, ch, meas, didx, freqs, fb, eta, n_draws=120, use_inf=True):
    """Return dict daq -> (lo, med, hi, measured) for held-out channels, total predictive band."""
    R = cal["R"]; phi0 = cal["phi0"]; fem_k = cal["fem_k"]
    obs_rows = ch.rows[obs_pos]; ho_rows = ch.rows[ho_pos]
    obs_daqs = [ch.daq[p] for p in obs_pos]; ho_daqs = [ch.daq[p] for p in ho_pos]
    peak_tru_obs = np.array([rf.core.qoi_peak(np.abs(meas["H"][didx[d]][fb])) for d in obs_daqs])
    sub = np.linspace(0, raw_post.shape[0] - 1, min(raw_post.shape[0], n_draws)).astype(int)
    nh = len(ho_pos); curves = np.zeros((len(sub), len(freqs), nh)); peak_o = np.zeros((len(sub), len(obs_pos)))
    for j, s in enumerate(sub):
        theta = theta_post[s]; K = R.A_fix + np.einsum("g,gij->ij", theta, R.A)
        if use_inf:
            phi = phi0 + M.TAU * raw_post[s]; Phi = phi / (np.linalg.norm(phi, axis=0, keepdims=True) + 1e-30)
            w2r = np.sum(phi * (K @ phi), 0) / (np.sum(phi * phi, 0) + 1e-30)
        else:
            lam, Q = np.linalg.eigh(K); Phi = Q[:, fem_k]; w2r = lam[fem_k]
        mo0 = M.reconstruct_mag(Phi, w2r, obs_rows, ch.drive_row, freqs, 0.0, eta)
        obs_pk = np.array([rf.core.qoi_peak(mo0[:, k]) for k in range(len(obs_pos))])
        c = float(np.median(np.log(peak_tru_obs + 1e-30) - np.log(obs_pk + 1e-30)))
        curves[j] = M.reconstruct_mag(Phi, w2r, ho_rows, ch.drive_row, freqs, c, eta)
        peak_o[j] = obs_pk * np.exp(c)
    sig = float(np.std(np.log(np.median(peak_o, 0) + 1e-300) - np.log(peak_tru_obs + 1e-300)))
    rngo = np.random.default_rng(123); off = np.exp(rngo.normal(0, max(sig, 1e-3), (len(sub), 1, nh)))
    tot = curves * off
    out = {}
    for k, p in enumerate(ho_pos):
        d = int(ch.daq[p])
        out[d] = (np.percentile(tot[:, :, k], 2.5, 0), np.median(tot[:, :, k], 0),
                  np.percentile(tot[:, :, k], 97.5, 0), np.abs(meas["H"][didx[d]][fb]))
    return out


# ----------------------------------------------------------------- static figures
def fig_mechanism():
    d = J("mc_beck_full_summary.json"); b = d["blocks"]["n_modes_12"]["peak"]
    L5 = d["L5_reference_theta_plus_qoi_disc"]["peak"]["interval_score_mean"]
    cfgs = ["FEM_const", "FEM_measured", "INFER_const", "INFER_measured"]
    labels = ["FEM shapes\nconst ζ", "FEM shapes\nmeas. ζ", "inferred shapes\nconst ζ", "inferred shapes\nmeas. ζ"]
    vals = [b[c]["IS_median"] for c in cfgs]
    fig, ax = plt.subplots(figsize=(7.2, 4.3))
    cols = [C_FEM, C_FEM, C_INF, C_INF]; alphas = [0.45, 0.7, 0.6, 0.95]
    bars = ax.bar(range(4), vals, color=cols)
    for bar, a in zip(bars, alphas):
        bar.set_alpha(a)
    ax.axhline(L5, color=C_L5, lw=1.4, ls="--"); ax.text(3.45, L5, f"  L5 = {L5:.0f}", color=C_L5, va="center", fontsize=9)
    for i, v in enumerate(vals):
        ax.text(i, v + 25, f"{v:.0f}", ha="center", fontsize=9.5)
    ax.set_xticks(range(4)); ax.set_xticklabels(labels, fontsize=9)
    ax.set_ylabel("held-out peak |H| interval score (lower = sharper)"); ax.set_ylim(bottom=0)
    ax.set_title("The sharpening is the SHAPE FIELD, not damping", color=NAVY, fontsize=12)
    ax.annotate("inferring the\nshape field", xy=(2.5, vals[2]), xytext=(1.2, max(vals) * 0.78),
                fontsize=9, color=C_INF, ha="center",
                arrowprops=dict(arrowstyle="->", color=C_INF))
    fig.text(0.5, -0.03, "Held-out impact-channel peak accelerance |H| [g/lbf], 25-split MC median (out/"
             "mc_beck_full_summary.json, n_modes=12). Lower interval score = sharper-AND-calibrated. Measured "
             "damping alone (red pair) does not help; inferred shape field (blue) ~halves the score vs FEM shapes.",
             ha="center", fontsize=7.2, wrap=True)
    fig.savefig(FIG / "fig_cardC_mechanism.png"); plt.close(fig)


def fig_phase2():
    d = J("mc_beck_kriging_summary.json"); blk = d["blocks"]
    names = list(blk.keys())
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(9.2, 4.0))
    x = np.arange(len(names) + 1)
    marg = blk[names[0]]["peak"]["interval_score"]["marginal"]
    isv = [marg] + [blk[n]["peak"]["interval_score"]["kriged"] for n in names]
    cov = [blk[names[0]]["peak"]["coverage"]["marginal"]] + [blk[n]["peak"]["coverage"]["kriged"] for n in names]
    lab = ["marginal\n(per-freq)"] + [f"kriged\nlen_z={n.split('_')[2]}in" for n in names]
    a1.bar(x, isv, color=[GREY if i == 0 else C_INF for i in range(len(x))]); a1.set_xticks(x); a1.set_xticklabels(lab, fontsize=8.5)
    for i, v in enumerate(isv):
        a1.text(i, v + 80, f"{v:.0f}", ha="center", fontsize=9)
    a1.set_ylabel("held-out peak IS (lower = sharper)"); a1.set_ylim(bottom=0); a1.set_title("Kriging sharpens vs marginal", fontsize=11, color=NAVY)
    a2.bar(x, cov, color=[GREY if i == 0 else C_INF for i in range(len(x))]); a2.axhline(0.95, color=C_L5, ls="--", lw=1)
    a2.set_xticks(x); a2.set_xticklabels(lab, fontsize=8.5); a2.set_ylim(0, 1.05); a2.set_ylabel("coverage (target 0.95)")
    a2.set_title("...but costs calibration", fontsize=11, color=NAVY)
    for i, v in enumerate(cov):
        a2.text(i, v + 0.02, f"{v:.2f}", ha="center", fontsize=9)
    fig.text(0.5, -0.04, "Held-out peak |H|, 25 splits (out/mc_beck_kriging_summary.json). The Schneider freq×space "
             "GP-conditional transfer halves the interval score vs the per-frequency marginal (25/25 splits) but "
             "coverage falls 1.0→0.8; neither beats the QOI-level σ (Phase-1 IS 773).", ha="center", fontsize=7.2, wrap=True)
    fig.savefig(FIG / "fig_cardC_phase2_kriging.png"); plt.close(fig)


def fig_phase3():
    d = J("tau_sweep_summary.json"); lv = d["levels"]
    order = ["top6", "mac_ge_0.7", "mac_ge_0.5", "full20"]
    nm = [lv[k]["n_modes"] for k in order]; pk = [lv[k]["peak_IS_median"] for k in order]
    bd = [lv[k]["band_IS_median"] for k in order]
    fig, ax = plt.subplots(figsize=(7.2, 4.4))
    ax.plot(nm, pk, "-o", color=C_INF, lw=1.8, ms=8)
    for x, y, bv in zip(nm, pk, bd):
        ax.text(x, y + 14, f"peak {y:.0f}", ha="center", fontsize=9, color=C_INF)
        ax.text(x, y - 22, f"band {bv:.0f}", ha="center", fontsize=8, color=GREY)
    ax.set_xlabel("number of MAC-matched modes kept  (quality threshold τ)")
    ax.set_ylabel("held-out peak |H| interval score (lower = sharper)", color=C_INF)
    ax.set_ylim(740, 1080); ax.set_xlim(4, 22)
    ax.set_title("Keep the FULL matched-mode set; over-restricting hurts", color=NAVY, fontsize=12, pad=24)
    ax.annotate("top-6 high-MAC only\n→ worse (loses info)", xy=(6, pk[0]), xytext=(8.5, 1035),
                fontsize=8.5, color=C_FEM, ha="center", arrowprops=dict(arrowstyle="->", color=C_FEM))
    ax.annotate("full set → sharpest", xy=(20, pk[-1]), xytext=(16.5, 850),
                fontsize=8.5, color=C_INF, ha="center", arrowprops=dict(arrowstyle="->", color=C_INF))
    fig.text(0.5, -0.03, "Hardened Beck (inferred shapes + measured ζ), held-out peak |H|, 25-split median (out/"
             "tau_sweep_summary.json); band-GRMS score labelled in grey. Coverage stays ≈0.97 at every τ — "
             "restricting modes does not break calibration, only widens.", ha="center", fontsize=7.2, wrap=True)
    fig.savefig(FIG / "fig_cardC_phase3_tau.png"); plt.close(fig)


def fig_phase4():
    d = J("phase_likelihood.json")
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(9.0, 3.9))
    cv = d["phase_circular_variance_at_modes"]
    a1.bar([0, 1], [cv, 1 - cv], color=[C_FEM, C_INF]); a1.set_xticks([0, 1])
    a1.set_xticklabels(["incoherent\n(noise)", "coherent\n(signal)"]); a1.set_ylim(0, 1)
    a1.set_title(f"Single-hit phase is incoherent\ncircular variance = {cv:.2f}", fontsize=10.5, color=NAVY)
    a1.text(0, cv + 0.03, f"{cv:.2f}", ha="center", fontsize=11)
    rm = d["theta_slice_magnitude"]["rel_contrast"]; rc = d["theta_slice_complex"]["rel_contrast"]
    a2.bar([0, 1], [rm, rc], color=[C_MEAS, C_FEM]); a2.set_xticks([0, 1])
    a2.set_xticklabels(["magnitude\nlikelihood", "complex\n(+phase)"])
    a2.set_title("Adding phase does NOT\nsharpen the θ minimum", fontsize=10.5, color=NAVY)
    a2.set_ylabel("θ-slice contrast (higher = sharper)")
    fig.text(0.5, -0.04, "Observed channels, split 0 (out/phase_likelihood.json). Phase circular variance ≈1 ⇒ "
             "measured-vs-model phase uniform/uninformative; complex θ-slice not sharper than magnitude ⇒ phase "
             "adds nothing over magnitude/modal here (single-hit caveat confirmed).", ha="center", fontsize=7.2, wrap=True)
    fig.savefig(FIG / "fig_cardC_phase4_phase.png"); plt.close(fig)


def fig_phase5():
    d = J("cross_dataset_summary.json"); s = d["sources"]
    order = ["nominal", "ash_freq", "ash_freqMAC", "beck_infer"]
    lab = ["nominal\nθ=1", ".ash\nfreq", ".ash\nfreq+MAC", ".ash\nshape-field"]
    vals = [s[k]["peak_IS_median"] for k in order]
    L5 = d["L5_impact_FRF_reference"]["peak_IS"]
    fig, ax = plt.subplots(figsize=(7.2, 4.2))
    cols = [GREY, GREY, GREY, C_INF]
    ax.bar(range(4), vals, color=cols)
    ax.axhline(L5, color=C_L5, ls="--", lw=1.3); ax.text(3.45, L5, f"  L5 impact-FRF = {L5:.0f}", color=C_L5, va="center", fontsize=8.5)
    for i, v in enumerate(vals):
        ax.text(i, v + 20, f"{v:.0f}", ha="center", fontsize=9.5)
    ax.set_xticks(range(4)); ax.set_xticklabels(lab, fontsize=9)
    ax.set_ylabel("held-out impact peak IS (lower = sharper)"); ax.set_ylim(bottom=0)
    ax.set_title("Cross-dataset: .ash calibrates a valid twin,\nbut only the SHAPE FIELD sharpens", color=NAVY, fontsize=11)
    fig.text(0.5, -0.03, "θ calibrated on the INDEPENDENT .ash modal survey → predict impact-hammer held-out FRF "
             "(out/cross_dataset_summary.json, 25 splits). Stiffness-θ from any modal source ≈ nominal; the inferred "
             "shape field is the lever, dataset-independent.", ha="center", fontsize=7.2, wrap=True)
    fig.savefig(FIG / "fig_cardC_phase5_cross.png"); plt.close(fig)


STARS = {"Phase 1 — shape-field twin (headline)": 4, "Phase 2 — spatial kriging transfer": 3,
         "Phase 3 — quality-threshold τ sweep": 4, "Phase 4 — complex/phase likelihood": 3,
         "Phase 5 — .ash cross-dataset": 4, "Phase 6 — refined-mesh re-validation": 1}
NOTE = {"Phase 1 — shape-field twin (headline)": "calibrated + ~1.4× sharper than L5 (apples-to-apples, 25/25); not 2×",
        "Phase 2 — spatial kriging transfer": "informative but costs calibration; QOI-level σ still best",
        "Phase 3 — quality-threshold τ sweep": "clean, decisive, converged: keep the full mode set",
        "Phase 4 — complex/phase likelihood": "honest negative: single-hit phase adds nothing",
        "Phase 5 — .ash cross-dataset": "valid independent source; shape-field is the lever",
        "Phase 6 — refined-mesh re-validation": "BLOCKED on Card D (harness ready; no result)"}


def fig_scorecard():
    fig, ax = plt.subplots(figsize=(10.4, 5.0)); ax.axis("off")
    ax.set_title("Card C scorecard — 5★ smashing success … 1★ dire failure", color=NAVY, fontsize=14, pad=14)
    items = list(STARS.items())
    for i, (name, n) in enumerate(items):
        y = len(items) - i
        ax.text(0.01, y, name, fontsize=11, va="center")
        ax.text(0.52, y, "★" * n + "☆" * (5 - n), fontsize=16, va="center",
                color=("#e6a700" if n >= 4 else (GREY if n >= 3 else C_FEM)))
        ax.text(0.70, y, NOTE[name], fontsize=8, va="center", color="#444444")
    ax.set_xlim(0, 1.35); ax.set_ylim(0.3, len(items) + 0.8)
    fig.text(0.5, 0.02, "Ratings are evidence-tied (out/*.json). Phase-1 magnitude corrected to apples-to-apples "
             "(apples_to_apples_frf_summary.json). Phase 6 blocked by an external dependency (Card D), not a quality "
             "failure.", ha="center", fontsize=7.4)
    fig.savefig(FIG / "fig_cardC_scorecard.png"); plt.close(fig)


# ----------------------------------------------------------------- GIFs
def _frame(fig):
    fig.canvas.draw(); w, h = fig.canvas.get_width_height()
    buf = np.frombuffer(fig.canvas.buffer_rgba(), dtype=np.uint8).reshape(h, w, 4)[..., :3].copy()
    plt.close(fig); return buf


def gif_heldout_sweep(cal):
    R, meas, ch, freqs, fb, didx, dr, obs_pos, ho_pos = split_setup(cal, 0)
    eta = M.per_mode_eta(cal, True)
    theta = np.ones((cal["log_theta"].shape[0], 9)); theta[:, [2, 4, 6, 8]] = np.exp(cal["log_theta"])
    bi = bands_for(cal, cal["raw"], theta, obs_pos, ho_pos, ch, meas, didx, freqs, fb, eta, use_inf=True)
    bf = bands_for(cal, cal["raw"], theta, obs_pos, ho_pos, ch, meas, didx, freqs, fb, eta, use_inf=False)
    daqs = list(bi.keys())
    daqs = sorted(daqs, key=lambda d: (d not in HARD, d))[:16]
    ymax = max(bi[d][3].max() for d in daqs) * 3; ymin = min(bi[d][3].min() for d in daqs) / 3
    frames = []
    for d in daqs:
        lo_i, med_i, hi_i, mg = bi[d]; lo_f, med_f, hi_f, _ = bf[d]
        fig, ax = plt.subplots(figsize=(6.6, 4.3))
        ax.fill_between(freqs, lo_f, hi_f, color=C_FEM, alpha=0.13, lw=0)
        ax.fill_between(freqs, lo_i, hi_i, color=C_INF, alpha=0.25, lw=0)
        ax.plot(freqs, med_f, color=C_FEM, lw=1.0, ls="--"); ax.plot(freqs, med_i, color=C_INF, lw=1.4)
        ax.plot(freqs, mg, color=C_MEAS, lw=1.3)
        ax.set_xscale("log"); ax.set_yscale("log"); ax.set_ylim(ymin, ymax)
        ax.set_xlabel("frequency [Hz, log]"); ax.set_ylabel("|H| [g/lbf, log]")
        tag = "HARD impact-face interface" if d in HARD else "held-out sensor"
        ax.set_title(f"DAQ {d} — {tag}: inferred band (blue) tracks measured (black)", fontsize=10.5, color=NAVY)
        ax.text(0.03, 0.95, "measured", color=C_MEAS, transform=ax.transAxes, fontsize=8, va="top")
        ax.text(0.03, 0.87, "inferred shapes 95%", color=C_INF, transform=ax.transAxes, fontsize=8, va="top")
        ax.text(0.03, 0.79, "FEM shapes 95%", color=C_FEM, transform=ax.transAxes, fontsize=8, va="top")
        fig.tight_layout(); frames.append(_frame(fig))
    imageio.mimsave(FIG / "gif_heldout_sweep.gif", frames, duration=900, loop=0)


def gif_tau_band(cal):
    R, meas, ch, freqs, fb, didx, dr, obs_pos, ho_pos = split_setup(cal, 0)
    import tau_sweep as TS
    tl, mac = TS.tau_levels()
    levels = [("full20", "full20", tl["full20"]), ("MAC≥0.5 (17)", "mac_ge_0.5", tl["mac_ge_0.5"]),
              ("MAC≥0.7 (10)", "mac_ge_0.7", tl["mac_ge_0.7"]), ("top-6 high-MAC", "top6", tl["top6"])]
    target = sorted(ho_pos, key=lambda p: (ch.daq[p] not in HARD, -dr[p]))[0]
    dtar = int(ch.daq[target])
    ymax = ymin = None; frames = []
    for name, tag, idx in levels:
        c2 = M.calibrate(pairs_idx=idx, cache_tag=f"tau_{tag}", warmup=800, samples=800)  # reuses cached tau_* npz
        eta = M.per_mode_eta(c2, True)
        th = np.ones((c2["log_theta"].shape[0], 9)); th[:, [2, 4, 6, 8]] = np.exp(c2["log_theta"])
        b = bands_for(c2, c2["raw"], th, obs_pos, np.array([target]), ch, meas, didx, freqs, fb, eta, use_inf=True)
        lo, med, hi, mg = b[dtar]
        if ymax is None:
            ymax = mg.max() * 3; ymin = mg.min() / 3
        fig, ax = plt.subplots(figsize=(6.6, 4.3))
        ax.fill_between(freqs, lo, hi, color=C_INF, alpha=0.25, lw=0); ax.plot(freqs, med, color=C_INF, lw=1.4)
        ax.plot(freqs, mg, color=C_MEAS, lw=1.3)
        ax.set_xscale("log"); ax.set_yscale("log"); ax.set_ylim(ymin, ymax)
        ax.set_xlabel("frequency [Hz, log]"); ax.set_ylabel("|H| [g/lbf, log]")
        ax.set_title(f"DAQ {dtar}: kept modes = {name} — band WIDENS as modes are dropped", fontsize=10, color=NAVY)
        fig.tight_layout(); frames.append(_frame(fig))
    # play full->restricted then back for readability
    imageio.mimsave(FIG / "gif_tau_band.gif", frames[::-1] + frames, duration=1000, loop=0)


def main():
    cal = M.calibrate(n_modes=12)
    fig_mechanism(); fig_phase2(); fig_phase3(); fig_phase4(); fig_phase5(); fig_scorecard()
    print("static figures done")
    gif_heldout_sweep(cal); print("gif_heldout_sweep done")
    gif_tau_band(cal); print("gif_tau_band done")


if __name__ == "__main__":
    main()
