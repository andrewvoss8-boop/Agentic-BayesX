#!/usr/bin/env python3
"""Card G — animated evolving posterior FRF (sequential Bayesian updating) for ONE held-out sensor.

Frames = the twin observing more measured modal frequencies (k = 0 prior, then 1,2,... matched modes). At each k we
NUTS-calibrate the 9 stiffness multipliers θ on the first k observed modes (extracted from the OTHER, observed
channels), then plot the posterior-predictive accelerance |H| for a HELD-OUT channel (never used in fitting):
  - measured |H| (truth, +X impact, 45–260 Hz)
  - original nominal FEM |H| (θ=1, deterministic) — the as-received twin
  - posterior median + 95% band = percentiles over θ draws of log|H(θ)| + one training-only gain c + the QOI-level
    discrepancy σ_QOI (the SAME predictive we score). The band that we actually score.
Title carries the scores (peak CRPS-skill vs climatology, 95%-band coverage, max R̂). Legend carries band-GRMS
[g/lbf·√Hz] for measured / nominal-FEM / posterior-median. Honest example: the peaks SNAP into place as θ calibrates
(the +0.93 frequency win) while the amplitude band stays wide (the documented amplitude limitation).

Output: figures/evolving_posterior_frf.gif  (+ figures/evolving_posterior_frf_final.png a static last frame).
"""
from __future__ import annotations
import sys, time, json
from pathlib import Path
from types import SimpleNamespace
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation, PillowWriter

sys.path.insert(0, str(Path(__file__).resolve().parent))
import realfrf as rf
import modal_feature as mf
import heldout_qoi as hq
import score as SC

WS = Path(__file__).resolve().parent.parent
FIG = WS / "figures"; FIG.mkdir(exist_ok=True)
HARD = {4, 27, 38, 40, 52, 69, 92, 98}
G = rf.G_IN_S2
NSIG = float(rf.core.NSIG_THETA)


def predictive(R, freqs, theta_draws, resp_row, drive_row, c_draws, sigma_qoi, rng):
    """log|H| predictive samples (Ndraw, Nf): forward over θ draws + per-draw gain c + per-draw QOI-level scatter."""
    lm = rf.fem_logmag_batch(R, freqs, theta_draws, resp_row[None, :], drive_row, zeta=rf.ZETA_NOM)[:, :, 0]  # (M,Nf)
    eta = rng.normal(0.0, max(sigma_qoi, 1e-3), size=lm.shape[0])[:, None]
    return lm + c_draws[:, None] + eta


def run(seed=0, n_draws=160, warmup=600, samples=600, chains=4, fps=1.6):
    t0 = time.time()
    R = rf.load_reduced()
    meas = rf.reprocess_measured(list(range(1, rf.N_ACCEL_RECORDERS + 1)))
    ch = rf.build_channels(R, meas["daq"])
    fr = meas["freqs"]; fb = (fr >= rf.BAND[0]) & (fr <= rf.BAND[1]); freqs = fr[fb]
    didx = {d: i for i, d in enumerate(meas["daq"])}
    dr = np.array([meas["dyn_range"][didx[d]] for d in ch.daq])
    elig = np.where(dr >= hq.DR_MIN)[0]
    rng = np.random.default_rng(seed); perm = rng.permutation(elig)
    n_obs = int(round(0.6 * len(perm)))
    obs_pos = np.sort(perm[:n_obs]); ho_pos = np.sort(perm[n_obs:])
    obs_daqs = [ch.daq[p] for p in obs_pos]; ho_daqs = [ch.daq[p] for p in ho_pos]

    grms = lambda mag: float(np.sqrt(np.trapz(mag ** 2, freqs)))
    # observed-channel measured logs + the consensus matched modes (ordered low->high freq)
    obs_rows = ch.rows[obs_pos]
    tru_obs = np.array([np.log(np.abs(meas["H"][didx[d]][fb]) + 1e-300) for d in obs_daqs])   # (nobs, Nf)
    meas_f, _ = mf.extract_measured_modes(meas, SimpleNamespace(daq=obs_daqs))
    pairs, _ = mf.match(R, meas_f)
    order = np.argsort([p[1] for p in pairs])
    mode_idx = np.array([pairs[i][0] for i in order]); res_hz = np.array([pairs[i][1] for i in order])
    n_modes = len(mode_idx)

    # --- select a GOOD, honest REPRESENTATIVE held-out channel: run ONE full calibration, then pick the
    #     NON-hard held-out channel (DR>=40) whose calibrated 95% band best covers its measured FRF (tie-break skill).
    th_sel, _, _ = mf.calibrate_modal(R, mode_idx, res_hz, seed=20260617, warmup=warmup, samples=samples, chains=chains)
    sub = np.linspace(0, th_sel.shape[0] - 1, min(th_sel.shape[0], n_draws)).astype(int); th_sel = th_sel[sub]
    c_sel = np.array([hq.wmedian((tru_obs.T - rf.fem_logmag_batch(R, freqs, th_sel[j:j+1], obs_rows, ch.drive_row)[0]).ravel(),
                                 np.ones(tru_obs.size)) for j in range(len(th_sel))])
    cand = [(p, d) for p, d in zip(ho_pos, ho_daqs) if d not in HARD and dr[p] >= 40]
    best = None
    for p, d in cand:
        pr = predictive(R, freqs, th_sel, ch.rows[p], ch.drive_row, c_sel, 0.5, np.random.default_rng(99))
        lo, hi = np.percentile(pr, [2.5, 97.5], axis=0)
        tl = np.log(np.abs(meas["H"][didx[d]][fb]) + 1e-300)
        cov = float(np.mean((tl >= lo) & (tl <= hi)))
        if best is None or cov > best[2]:
            best = (p, d, cov)
    ho_p, ho_d = best[0], best[1]
    resp_row = ch.rows[ho_p]
    tru_log = np.log(np.abs(meas["H"][didx[ho_d]][fb]) + 1e-300)
    meas_mag = np.exp(tru_log); grms_meas = grms(meas_mag)
    print(f"selected held-out example channel {ho_d} (DR {dr[ho_p]:.0f}, full-calib band coverage {best[2]:.2f})")

    # nominal FEM (theta=1) with the same training gain (fit on observed channels)
    def gain_for(theta_draws):
        lm_obs = rf.fem_logmag_batch(R, freqs, theta_draws, obs_rows, ch.drive_row, zeta=rf.ZETA_NOM)  # (M,Nf,nobs)
        c = np.array([hq.wmedian((tru_obs.T - lm_obs[j]).ravel(), np.ones(tru_obs.size)) for j in range(len(theta_draws))])
        return c, lm_obs
    nom = np.ones((1, 9))
    c_nom, _ = gain_for(nom)
    nom_log = rf.fem_logmag(R, freqs, np.ones(9), resp_row[None, :], ch.drive_row)[:, 0] + c_nom[0]
    grms_nom = grms(np.exp(nom_log))

    # build the frame sequence: k = 0 (prior) then a subsampled climb to all modes (~13 frames), holding the last.
    steps = sorted(set([0, 1, 2, 3, 4, 6, 8, 11, 14, 18, max(22, n_modes // 2), n_modes]))
    ks = [k for k in steps if k <= n_modes]
    ks = ks + [n_modes, n_modes]   # hold the final posterior a couple extra frames
    frames = []
    for k in ks:
        if k == 0:
            th = np.exp(np.random.default_rng(7).normal(0, NSIG, (n_draws, 9)))   # prior draws
            rhat = np.nan; tag = "prior (0 modes)"
        else:
            th_post, _, diag = mf.calibrate_modal(R, mode_idx[:k], res_hz[:k], seed=20260617,
                                                  warmup=warmup, samples=samples, chains=chains)
            sub = np.linspace(0, th_post.shape[0] - 1, min(th_post.shape[0], n_draws)).astype(int)
            th = th_post[sub]; rhat = diag["max_rhat"]; tag = f"{k} of {n_modes} modes observed"
        c, lm_obs = gain_for(th)
        # sigma_QOI from observed-channel peak residual (same as value_eval), at these draws
        po = np.exp(lm_obs + c[:, None, None])                       # (M,Nf,nobs)
        peak_ob_pred = np.median(po.max(axis=1), axis=0)             # (nobs,)
        peak_ob_meas = np.exp(tru_obs).max(axis=1)
        sigma_qoi = float(np.std(np.log(peak_ob_pred + 1e-300) - np.log(peak_ob_meas + 1e-300)))
        pred = predictive(R, freqs, th, resp_row, ch.drive_row, c, sigma_qoi, np.random.default_rng(k + 1))
        lo, med, hi = np.percentile(pred, [2.5, 50, 97.5], axis=0)
        cover = float(np.mean((tru_log >= lo) & (tru_log <= hi)))
        # peak CRPS-skill vs climatology (observed-channel peaks)
        pk_pred = np.exp(pred).max(axis=1)                           # predictive peak draws
        pk_tru = float(meas_mag.max())
        clim = peak_ob_meas
        skill = float(1 - SC.crps_sample(pk_pred, pk_tru) / SC.crps_sample(clim, pk_tru))
        frames.append({"k": k, "tag": tag, "lo": lo, "med": med, "hi": hi, "rhat": rhat,
                       "cover": cover, "skill": skill, "grms_med": grms(np.exp(med)), "sigma": sigma_qoi})
        print(f"  frame k={k}: skill {skill:+.2f} cover {cover:.2f} Rhat {rhat if k==0 else round(rhat,3)}")

    # ---- render ----
    fig, ax = plt.subplots(figsize=(8.2, 4.8))
    plt.rcParams.update({"axes.spines.top": False, "axes.spines.right": False})
    ymin = 10 ** np.floor(np.log10(max(np.exp(tru_log).min(), 1e-4)))
    ymax = 10 ** np.ceil(np.log10(np.exp(tru_log).max() * 1.5))

    def draw(i):
        ax.clear()
        f = frames[i]
        ax.fill_between(freqs, np.exp(f["lo"]), np.exp(f["hi"]), color="#9ecae1", alpha=0.55, lw=0,
                        label="posterior 95% band")
        ax.semilogy(freqs, np.exp(f["med"]), color="#08519c", lw=1.6,
                    label=f"posterior median   (GRMS {f['grms_med']:.2g})")
        ax.semilogy(freqs, np.exp(nom_log), color="#cc5500", lw=1.2, ls="--",
                    label=f"original nominal FEM   (GRMS {grms_nom:.2g})")
        ax.semilogy(freqs, meas_mag, color="0.15", lw=1.1,
                    label=f"measured (held-out ch {ho_d})   (GRMS {grms_meas:.2g})")
        ax.set_xscale("log"); ax.set_xlim(45, 260); ax.set_ylim(ymin, ymax)
        ax.set_xlabel("frequency [Hz]  (log)"); ax.set_ylabel("|accelerance| [g/lbf]  (log)")
        rh = "n/a (prior)" if f["k"] == 0 else f"{f['rhat']:.3f}"
        ax.set_title(f"Evolving posterior FRF — held-out channel {ho_d} (+X) — {f['tag']}\n"
                     f"peak CRPS-skill vs climatology {f['skill']:+.2f}   |   95%-band coverage {f['cover']*100:.0f}%"
                     f"   |   max R̂ {rh}", fontsize=9.5)
        ax.legend(loc="upper right", fontsize=7.6, framealpha=0.9)
        ax.text(0.012, 0.03, "GRMS = √∫|H|²df over 45–260 Hz [g/lbf·√Hz]. Measured NASA ShockSat1. SELECTED "
                "well-covered held-out channel (1 of 31) — one of the BETTER cases; the population-mean held-out "
                "amplitude skill is −1.0 (see packet).\nPeaks align as θ calibrates (the +0.93 frequency win); the "
                "amplitude band stays wide and the median under-predicts tall peaks (the documented amplitude limit).",
                transform=ax.transAxes, fontsize=6.4, color="0.3", va="bottom")
        return []

    anim = FuncAnimation(fig, draw, frames=len(frames), blit=False)
    gif = FIG / "evolving_posterior_frf.gif"
    anim.save(gif, writer=PillowWriter(fps=fps))
    draw(len(frames) - 1); fig.savefig(FIG / "evolving_posterior_frf_final.png", dpi=130, bbox_inches="tight")
    plt.close(fig)
    meta = {"held_out_channel_daq": int(ho_d), "split_seed": seed, "n_frames": len(frames),
            "n_modes_total": int(n_modes), "n_observed_channels": int(n_obs), "n_heldout_channels": int(len(ho_pos)),
            "final_skill": frames[-1]["skill"], "final_coverage": frames[-1]["cover"],
            "grms_measured": grms_meas, "grms_nominal_fem": grms_nom, "grms_posterior_median_final": frames[-1]["grms_med"],
            "runtime_s": time.time() - t0}
    (WS / "out" / "evolving_gif_meta.json").write_text(json.dumps(meta, indent=2))
    print(f"\nwrote {gif.name} ({len(frames)} frames, ch {ho_d}); final skill {frames[-1]['skill']:+.2f} "
          f"cover {frames[-1]['cover']*100:.0f}% | {meta['runtime_s']:.0f}s")
    return meta


if __name__ == "__main__":
    run()
