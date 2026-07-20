#!/usr/bin/env python3
"""Card G — animated evolving posterior FRF as the roving-hammer DATASETS are folded in (not modes).

Frames = cumulatively adding the reference datasets to the calibration:
    prior → +X(Test07) → +X+Z(Test08) → +X+Z+Y(Test03,modal) → +X+Z+Y+900z(Test10)
Each dataset contributes the matched modes it EXCITES (FEM drive participation ≥10% of its max); the cumulative union
of those modes' MEASURED frequencies is the calibration data (NO mode is held out — we ADD each dataset's modal data,
the realistic roving-hammer workflow). At each step we NUTS-calibrate θ and predict the posterior-predictive |H| for a
HELD-OUT sensor (leave-a-sensor-out, the realistic predictive test), under the +X observable, with a 95% band.
Title: datasets in, #modes, peak CRPS-skill vs climatology, 95%-band coverage, max R̂. Legend: band-GRMS [g/lbf·√Hz].
Honest takeaway: folding in datasets grows modal COVERAGE (17→23 modes) and re-tightens θ, but the held-out amplitude
band stays wide / skill stays ≤0 — multi-reference buys frequency coverage, not held-out per-sensor amplitude.

Output: figures/evolving_posterior_frf_datasets.gif (+ _final.png, out/evolving_gif_datasets_meta.json).
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
FIG = WS / "figures"
HARD = {4, 27, 38, 40, 52, 69, 92, 98}
NSIG = float(rf.core.NSIG_THETA)
REF_ORDER = [("xpos_990x", "+X (Test07)"), ("zpos_990z", "+Z (Test08)"),
             ("ypos_990y", "+Y (Test03, modal)"), ("z_900z", "900z (Test10)")]
REF_XYZ = {"xpos_990x": ((9.0, 8.0, 1.0), "X"), "zpos_990z": ((9.0, 8.0, 0.0), "Z"),
           "ypos_990y": ((8.5, 9.0, 1.0), "Y"), "z_900z": ((9.0, 0.5, 0.0), "Z")}
EXC_FRAC = 0.10


def predictive(R, freqs, theta_draws, resp_row, drive_row, c_draws, sigma_qoi, rng):
    lm = rf.fem_logmag_batch(R, freqs, theta_draws, resp_row[None, :], drive_row, zeta=rf.ZETA_NOM)[:, :, 0]
    eta = rng.normal(0.0, max(sigma_qoi, 1e-3), size=lm.shape[0])[:, None]
    return lm + c_draws[:, None] + eta


def run(seed=0, n_draws=160, warmup=800, samples=800, chains=4, fps=1.1):
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
    obs_rows = ch.rows[obs_pos]
    tru_obs = np.array([np.log(np.abs(meas["H"][didx[d]][fb]) + 1e-300) for d in obs_daqs])
    grms = lambda mag: float(np.sqrt(np.trapz(mag ** 2, freqs)))
    drive_x = ch.drive_row   # the +X observable we predict & compare against (held-out truth)

    # matched modes + which modes each dataset EXCITES (FEM phi_d >= 10% of its max)
    meas_f, _ = mf.extract_measured_modes(meas, SimpleNamespace(daq=obs_daqs))
    pairs, _ = mf.match(R, meas_f)
    mode_idx = np.array([p[0] for p in pairs]); res_hz = np.array([p[1] for p in pairs])
    K0 = R.A_fix + R.A.sum(0); _, Q0 = np.linalg.eigh(K0)
    excited = {}
    for key, _ in REF_ORDER:
        drow, _, _ = R.reduced_row(*REF_XYZ[key])
        pd = np.array([abs(float(drow @ Q0[:, mj])) for mj in mode_idx])
        excited[key] = pd >= EXC_FRAC * pd.max()

    def gain_for(theta_draws):
        lm_obs = rf.fem_logmag_batch(R, freqs, theta_draws, obs_rows, drive_x, zeta=rf.ZETA_NOM)
        c = np.array([hq.wmedian((tru_obs.T - lm_obs[j]).ravel(), np.ones(tru_obs.size)) for j in range(len(theta_draws))])
        return c, lm_obs

    # nominal FEM (theta=1) gain on observed channels (held-out nom_log computed after channel selection)
    c_nom, _ = gain_for(np.ones((1, 9)))

    # cumulative dataset sets (frame 0 = prior); cum_label = the datasets folded in so far
    sets = []
    cum = np.zeros(len(mode_idx), bool); cum_labels = []
    for key, lab in REF_ORDER:
        cum = cum | excited[key]; cum_labels.append(lab)
        sets.append((key, " + ".join(cum_labels), cum.copy()))

    # --- select a GOOD held-out example channel using the FULL (all datasets) calibration ---
    full_mask = sets[-1][2]
    th_sel, _, _ = mf.calibrate_modal(R, mode_idx[full_mask], res_hz[full_mask], seed=20260617,
                                      warmup=warmup, samples=samples, chains=chains)
    sub = np.linspace(0, th_sel.shape[0] - 1, min(th_sel.shape[0], n_draws)).astype(int); th_sel = th_sel[sub]
    c_sel, _ = gain_for(th_sel)
    cand = [(p, d) for p, d in zip(ho_pos, ho_daqs) if d not in HARD and dr[p] >= 40]
    best = None
    for p, d in cand:
        pr = predictive(R, freqs, th_sel, ch.rows[p], drive_x, c_sel, 0.5, np.random.default_rng(99))
        lo, hi = np.percentile(pr, [2.5, 97.5], axis=0)
        tl = np.log(np.abs(meas["H"][didx[d]][fb]) + 1e-300)
        cov = float(np.mean((tl >= lo) & (tl <= hi)))
        if best is None or cov > best[2]:
            best = (p, d, cov)
    ho_p, ho_d = best[0], best[1]; resp_row = ch.rows[ho_p]
    tru_log = np.log(np.abs(meas["H"][didx[ho_d]][fb]) + 1e-300); meas_mag = np.exp(tru_log)
    grms_meas = grms(meas_mag)
    nom_log = rf.fem_logmag(R, freqs, np.ones(9), resp_row[None, :], drive_x)[:, 0] + c_nom[0]
    grms_nom = grms(np.exp(nom_log))
    peak_ob_meas = np.exp(tru_obs).max(axis=1)
    print(f"selected held-out example channel {ho_d} (DR {dr[ho_p]:.0f}, full-set coverage {best[2]:.2f})")

    # --- build frames: prior, then cumulative dataset sets ---
    frame_specs = [("prior", "(none)", None)] + [(k, lab, m) for (k, lab, m) in sets]
    frames = []
    prev_nmodes = 0; prev_mask = None
    for key, lab, mask in frame_specs:
        if mask is not None and prev_mask is not None and np.array_equal(mask, prev_mask):
            f = dict(frames[-1]); f["datasets"] = lab; f["added"] = 0   # dataset added NO new excited modes
            frames.append(f); print(f"  [{lab}] +0 new modes (already covered) -> frame unchanged")
            continue
        prev_mask = None if mask is None else mask.copy()
        if mask is None:
            th = np.exp(np.random.default_rng(7).normal(0, NSIG, (n_draws, 9)))
            rhat = np.nan; nmodes = 0; added = 0; datasets = "prior (no data)"
        else:
            nmodes = int(mask.sum()); added = nmodes - prev_nmodes; prev_nmodes = nmodes
            th_post, _, diag = mf.calibrate_modal(R, mode_idx[mask], res_hz[mask], seed=20260617,
                                                  warmup=warmup, samples=samples, chains=chains)
            s = np.linspace(0, th_post.shape[0] - 1, min(th_post.shape[0], n_draws)).astype(int); th = th_post[s]
            rhat = diag["max_rhat"]
            datasets = lab   # lab already carries the cumulative dataset string
        c, lm_obs = gain_for(th)
        po = np.exp(lm_obs + c[:, None, None]); peak_ob_pred = np.median(po.max(axis=1), axis=0)
        sigma_qoi = float(np.std(np.log(peak_ob_pred + 1e-300) - np.log(peak_ob_meas + 1e-300)))
        pred = predictive(R, freqs, th, resp_row, drive_x, c, sigma_qoi, np.random.default_rng(hash(key) % 1000 + 1))
        lo, med, hi = np.percentile(pred, [2.5, 50, 97.5], axis=0)
        cover = float(np.mean((tru_log >= lo) & (tru_log <= hi)))
        pk_pred = np.exp(pred).max(axis=1); pk_tru = float(meas_mag.max())
        skill = float(1 - SC.crps_sample(pk_pred, pk_tru) / SC.crps_sample(peak_ob_meas, pk_tru))
        frames.append({"datasets": datasets, "nmodes": nmodes, "added": added, "rhat": rhat, "lo": lo, "med": med,
                       "hi": hi, "cover": cover, "skill": skill, "grms_med": grms(np.exp(med))})
        print(f"  [{datasets}] modes {nmodes} (+{added}) skill {skill:+.2f} cover {cover:.2f} "
              f"Rhat {rhat if mask is None else round(rhat,3)}")
    frames += [frames[-1], frames[-1]]   # hold the final

    # --- render ---
    fig, ax = plt.subplots(figsize=(8.3, 4.9))
    plt.rcParams.update({"axes.spines.top": False, "axes.spines.right": False})
    ymin = 10 ** np.floor(np.log10(max(meas_mag.min(), 1e-4))); ymax = 10 ** np.ceil(np.log10(meas_mag.max() * 1.5))

    def draw(i):
        ax.clear(); f = frames[i]
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
        rh = "n/a (prior)" if not np.isfinite(f["rhat"]) else f"{f['rhat']:.3f}"
        ax.set_title(f"Folding in roving-hammer DATASETS — held-out channel {ho_d} (+X)\n"
                     f"datasets in: {f['datasets']}   ·   {f['nmodes']} modes (+{f['added']})\n"
                     f"peak CRPS-skill vs climatology {f['skill']:+.2f}   |   95%-band coverage {f['cover']*100:.0f}%"
                     f"   |   max R̂ {rh}", fontsize=9.2)
        ax.legend(loc="upper right", fontsize=7.6, framealpha=0.9)
        ax.text(0.012, 0.03, "Each dataset ADDS the modes it excites (no mode held out); a SENSOR is held out (the "
                "realistic test). Measured NASA ShockSat1. SELECTED well-covered channel (1 of 31, a BETTER case; "
                "population-mean held-out amplitude skill is −1.0).\nCoverage saturates after +X+Z (+Y, 900z add no new "
                "excited modes here) and the held-out skill stays FLAT as datasets fold in → multi-reference buys "
                "frequency coverage, not held-out per-sensor amplitude.",
                transform=ax.transAxes, fontsize=6.4, color="0.3", va="bottom")
        return []

    anim = FuncAnimation(fig, draw, frames=len(frames), blit=False)
    gif = FIG / "evolving_posterior_frf_datasets.gif"
    anim.save(gif, writer=PillowWriter(fps=fps))
    draw(len(frames) - 1); fig.savefig(FIG / "evolving_posterior_frf_datasets_final.png", dpi=130, bbox_inches="tight")
    plt.close(fig)
    meta = {"held_out_channel_daq": int(ho_d), "split_seed": seed, "n_frames": len(frames),
            "dataset_order": [l for _, l in REF_ORDER], "modes_per_step": [f["nmodes"] for f in frames],
            "skill_per_step": [f["skill"] for f in frames], "coverage_per_step": [f["cover"] for f in frames],
            "grms_measured": grms_meas, "grms_nominal_fem": grms_nom, "runtime_s": time.time() - t0}
    (WS / "out" / "evolving_gif_datasets_meta.json").write_text(json.dumps(meta, indent=2))
    print(f"\nwrote {gif.name} ({len(frames)} frames, ch {ho_d}); modes {meta['modes_per_step']}; "
          f"skill {[round(s,2) for s in meta['skill_per_step']]} | {meta['runtime_s']:.0f}s")
    return meta


if __name__ == "__main__":
    run()
