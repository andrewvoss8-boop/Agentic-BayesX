#!/usr/bin/env python3
"""Comprehensive held-out report PDF (Andrew 2026-06-18). NO cherry-picking: one split (seed 0), ALL held-out
channels, each with its proper-score GRADE on the panel. Page 1 = the Error-vs-participation FEM graphic (Idea
3+1, AGENTS §8): a structure locator (real FEM geometry coloured by inferred error per group + observed/held-out/
drive sensors, with the area=footprint disclaimer) PAIRED with the non-spatial one-dot-per-group scatter
(x=strain-energy %, y=inferred error %, size=error×participation) + inferred theta bars.

"Calibrated amplitude envelope": the predicted |H| AFTER adding the marginal amplitude DISCREPANCY. The theta-
posterior band alone (blue) is overconfident on amplitude (frequency calibration != amplitude calibration);
multiplying the predicted median by exp(+-1.96 sigma_QOI), sigma_QOI = the log-amplitude model-form scatter
estimated on the OBSERVED channels (~x2.7), gives the band that is actually CALIBRATED (covers ~90% of held-out
peaks). That grey 95% band is the honest predictive interval an engineer would act on.

Output: out/heldout_report.pdf (+ PNG previews of pages 1-2).
"""
from __future__ import annotations

import json
import sys
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages

sys.path.insert(0, str(Path(__file__).resolve().parent))
import realfrf as rf
import modal_feature as mf
import heldout_qoi as hq
import score as SC

WS = Path(__file__).resolve().parent.parent
SYN = WS.parent / "statfem_shocksat_eval_20260616" / "data"
GN = rf.GNAMES
IDENT4 = {"bottom_box", "cross_beam", "plates", "top_box"}
qoi_peak = rf.core.qoi_peak
qoi_band = rf.core.qoi_band


def compute(seed=0, obs_frac=0.6, n_draws=250, warmup=1000, samples=1000, chains=4):
    R = rf.load_reduced()
    meas = rf.reprocess_measured(list(range(1, rf.N_ACCEL_RECORDERS + 1)))
    ch = rf.build_channels(R, meas["daq"])
    fr = meas["freqs"]; fb = (fr >= rf.BAND[0]) & (fr <= rf.BAND[1]); freqs = fr[fb]
    didx = {d: i for i, d in enumerate(meas["daq"])}
    dr = np.array([meas["dyn_range"][didx[d]] for d in ch.daq])
    elig = np.where(dr >= hq.DR_MIN)[0]
    rng = np.random.default_rng(seed); perm = rng.permutation(elig)
    n_obs = int(round(obs_frac * len(perm)))
    obs_pos = np.sort(perm[:n_obs]); ho_pos = np.sort(perm[n_obs:])
    obs_daqs = [ch.daq[p] for p in obs_pos]; ho_daqs = [ch.daq[p] for p in ho_pos]

    meas_f, _ = mf.extract_measured_modes(meas, SimpleNamespace(daq=obs_daqs))
    pairs, _ = mf.match(R, meas_f)
    theta_post, _, diag = mf.calibrate_modal(R, np.array([p[0] for p in pairs]),
                                             np.array([p[1] for p in pairs]),
                                             warmup=warmup, samples=samples, chains=chains)
    sub = np.linspace(0, theta_post.shape[0] - 1, min(theta_post.shape[0], n_draws)).astype(int)

    obs_rows = ch.rows[obs_pos]; ho_rows = ch.rows[ho_pos]
    tru_obs = np.log(np.abs(np.array([meas["H"][didx[d]][fb] for d in obs_daqs])) + 1e-300).T
    tru_ho = np.log(np.abs(np.array([meas["H"][didx[d]][fb] for d in ho_daqs])) + 1e-300).T
    wq_obs = np.array([meas["weight"][didx[d]][fb] for d in obs_daqs]).T
    lm_obs = rf.fem_logmag_batch(R, freqs, theta_post[sub], obs_rows, ch.drive_row, zeta=hq.ZETA)
    lm_ho = rf.fem_logmag_batch(R, freqs, theta_post[sub], ho_rows, ch.drive_row, zeta=hq.ZETA)
    wflat = wq_obs.ravel(); n_ho = len(ho_pos); ns = len(sub)
    pred_ho = np.zeros((ns, len(freqs), n_ho)); peak_ob = np.zeros((ns, len(obs_pos))); c_draws = np.zeros(ns)
    for j in range(ns):
        c = hq.wmedian((tru_obs - lm_obs[j]).ravel(), wflat)
        c_draws[j] = c; pred_ho[j] = lm_ho[j] + c
        po = np.exp(lm_obs[j] + c)
        for k in range(len(obs_pos)):
            peak_ob[j, k] = qoi_peak(po[:, k])
    c_med = float(np.median(c_draws))
    det_ho = np.exp(rf.fem_logmag_batch(R, freqs, np.ones((1, 9)), ho_rows, ch.drive_row, zeta=hq.ZETA)[0] + c_med)
    peak_tru_ob = np.array([qoi_peak(np.exp(tru_obs[:, k])) for k in range(len(obs_pos))])
    sig_pk = float(np.std(np.log(np.median(peak_ob, 0) + 1e-300) - np.log(peak_tru_ob + 1e-300)))

    # ONE combined predictive = parameter spread + a per-draw, frequency-CORRELATED model-form level offset
    # delta ~ N(0, sigma_QOI) (the FEM's amplitude error at a sensor is mostly a level offset). The SAME delta
    # feeds the TOTAL band and the peak-QOI GRADE, so band and score correspond exactly.
    delta = np.random.default_rng(seed + 9).normal(0.0, sig_pk, (ns, n_ho))
    grades = []
    for k in range(n_ho):
        peak_draw = np.array([qoi_peak(np.exp(pred_ho[j, :, k])) for j in range(ns)])
        peak_ens = peak_draw * np.exp(delta[:, k])          # total predictive peak (param x discrepancy)
        pk_t = qoi_peak(np.exp(tru_ho[:, k]))
        s = SC.score_qoi(peak_ens, pk_t)
        grades.append({"interval": s["interval_score"], "crps": s["crps"], "covered": s["covered"],
                       "z": s["z"], "peak_truth": pk_t})

    idn = json.loads((WS / "out" / "identifiability.json").read_text())
    se = {g: idn["strain_energy"][g]["peak_frac"] for g in GN}
    theta = {g: (float(np.median(theta_post[:, i])), float(np.percentile(theta_post[:, i], 2.5)),
                 float(np.percentile(theta_post[:, i], 97.5))) for i, g in enumerate(GN)}
    gg = np.load(SYN / "group_geometry.npz", allow_pickle=True)   # node xyz + group membership (read-only)
    return dict(freqs=freqs, tru_ho=tru_ho, pred_ho=pred_ho, delta=delta, det_ho=det_ho, ho_daqs=ho_daqs,
                ho_pos=ho_pos, obs_pos=obs_pos, coords=ch.coords, dr=dr, sig_pk=sig_pk, diag=diag, se=se,
                theta=theta, seed=seed, n_obs=len(obs_pos), grades=grades, drive_xyz=rf.IMPACT_XYZ,
                node_xyz=np.asarray(gg["xyz"]), node_group=np.asarray(gg["group_idx"]))


def _page1(D, pdf):
    import matplotlib.gridspec as gs
    err = np.array([abs(D["theta"][g][0] - 1.0) * 100 for g in GN])     # inferred error % per group
    part = np.array([D["se"][g] * 100 for g in GN])                     # strain-energy participation %
    fig = plt.figure(figsize=(13, 8.5))
    G = gs.GridSpec(2, 2, width_ratios=[1.05, 1.25], height_ratios=[1.15, 1], wspace=0.28, hspace=0.32)
    fig.suptitle(f"Where the error is vs where we measure — REAL ShockSat, split seed {D['seed']} "
                 f"(L5 twin, R-hat {D['diag']['max_rhat']:.3f})", fontsize=13)

    # (left, tall) STRUCTURE LOCATOR: FEM nodes coloured by inferred group error + sensors
    axS = fig.add_subplot(G[:, 0])
    nx, nz = D["node_xyz"][:, 0], D["node_xyz"][:, 2]
    node_err = err[np.clip(D["node_group"], 0, 8)]
    sc = axS.scatter(nx, nz, c=node_err, s=2, cmap="YlOrRd", vmin=0, vmax=max(err.max(), 1), alpha=0.55, lw=0)
    co = D["coords"][D["obs_pos"]]; czh = D["coords"][D["ho_pos"]]
    axS.scatter(czh[:, 0], czh[:, 2], s=80, facecolors="none", edgecolors="#1769d6", lw=1.7, label=f"held-out ({len(czh)})")
    axS.scatter(co[:, 0], co[:, 2], s=48, c="#117a2b", edgecolors="k", lw=0.4, label=f"observed ({len(co)})")
    axS.scatter([D["drive_xyz"][0]], [D["drive_xyz"][2]], marker="*", s=240, c="k", label="drive")
    axS.set_xlabel("x [in]"); axS.set_ylabel("height z [in]"); axS.legend(fontsize=8, frameon=False, loc="upper left")
    axS.set_title("Structure locator: FEM coloured by INFERRED error per group", fontsize=10)
    fig.colorbar(sc, ax=axS, fraction=0.045, pad=0.02, label="inferred |theta_med-1| [%]")
    axS.text(0.0, -0.10, "area = element FOOTPRINT, NOT error magnitude (use the scatter at right for the "
             "error-vs-identifiability reading). No synthetic truth on real data: colour = INFERRED correction.",
             transform=axS.transAxes, fontsize=7, color="#555", va="top", wrap=True)

    # (right top) NON-SPATIAL one-dot-per-group scatter (lie-factor-free)
    axE = fig.add_subplot(G[0, 1])
    foot = (part / 100) * (err / 100); sizes = 60 + 1500 * foot / max(foot.max(), 1e-9)
    for i, g in enumerate(GN):
        ident = g in IDENT4
        axE.scatter(part[i], err[i], s=sizes[i], c=[err[i]], cmap="YlOrRd",
                    vmin=0, vmax=max(err.max(), 1), edgecolor=("#13456e" if ident else "#555"),
                    lw=1.2 if ident else 0.6, alpha=0.85)
        axE.annotate(g.replace("_", " "), (part[i], err[i]), xytext=(6, 4), textcoords="offset points",
                     fontsize=7.5, color=("#13456e" if ident else "#777"))
    axE.axvline(30, color="#cc6666", ls="--", lw=1)
    axE.set_xlabel("strain-energy participation [%]  (where the modes can see it)")
    axE.set_ylabel("inferred error |theta-1| [%]")
    axE.set_title("One dot per group (equal weight): biased-and-identifiable = lower-right", fontsize=10)

    # (right bottom) inferred theta with CI
    axT = fig.add_subplot(G[1, 1]); x = np.arange(9)
    cols = ["#d7301f" if g in IDENT4 else "#bbb" for g in GN]
    med = [D["theta"][g][0] for g in GN]
    lo = [med[i] - D["theta"][GN[i]][1] for i in range(9)]; hi = [D["theta"][GN[i]][2] - med[i] for i in range(9)]
    axT.errorbar(x, med, yerr=[lo, hi], fmt="none", ecolor="#999", elinewidth=1.4, capsize=3, zorder=2)
    axT.scatter(x, med, c=cols, s=42, edgecolor="k", lw=0.4, zorder=3)
    axT.axhline(1.0, color="#888", ls=":")
    axT.set_ylabel("theta (1 = nominal)"); axT.set_xticks(x)
    axT.set_xticklabels([g.replace("_", "\n") for g in GN], fontsize=6.3)
    axT.set_title("Inferred stiffness: 4 identifiable tight, 5 stay at prior width", fontsize=10)
    fig.savefig(WS / "figures" / "report_setup.png", dpi=110, bbox_inches="tight")
    pdf.savefig(fig, bbox_inches="tight"); plt.close(fig)


def render(D, out="out/heldout_report.pdf"):
    from matplotlib.patches import Patch
    from matplotlib.lines import Line2D
    freqs = D["freqs"]; PNL = 9
    param = np.exp(np.percentile(D["pred_ho"], [5, 50, 95], axis=0))                      # (3,Nf,n_ho)
    total = np.exp(np.percentile(D["pred_ho"] + D["delta"][:, None, :], [5, 95], axis=0))  # (2,Nf,n_ho)
    n_ho = param.shape[2]; order = np.argsort(-D["dr"][D["ho_pos"]])
    legend = [Patch(fc="#cfd3d6", label="total uncertainty (with model-form error)"),
              Patch(fc="#9ec6e6", label="param uncertainty"),
              Line2D([0], [0], color="#1f6fb4", label="twin median"),
              Line2D([0], [0], color="#c44", label="measured |H1|"),
              Line2D([0], [0], color="k", ls="-.", label="as-received NASA FEM (theta=1)"),
              Line2D([0], [0], color="#e8820c", ls=":", label="+3 dB PSD (x1.41)"),
              Line2D([0], [0], color="#cc3333", ls=":", label="+6 dB PSD (x2.0)")]
    with PdfPages(WS / out) as pdf:
        _page1(D, pdf)
        cov = 0
        for pg in range(0, n_ho, PNL):
            fig, axes = plt.subplots(3, 3, figsize=(11, 8.7)); axes = axes.ravel()
            for a in range(PNL):
                ax = axes[a]
                if pg + a >= n_ho:
                    ax.axis("off"); continue
                k = order[pg + a]; gd = D["grades"][k]; tru = np.exp(D["tru_ho"][:, k])
                cov += gd["covered"]
                det = D["det_ho"][:, k]
                ax.fill_between(freqs, total[0, :, k], total[1, :, k], color="#cfd3d6", alpha=0.85, lw=0)
                ax.fill_between(freqs, param[0, :, k], param[2, :, k], color="#9ec6e6", alpha=0.85, lw=0)
                ax.plot(freqs, det, color="k", lw=0.7, ls="-."); ax.plot(freqs, det * 1.4125, color="#e8820c", lw=0.6, ls=":")
                ax.plot(freqs, det * 1.9953, color="#cc3333", lw=0.6, ls=":")
                ax.plot(freqs, param[1, :, k], color="#1f6fb4", lw=1.0); ax.plot(freqs, tru, color="#c44", lw=1.0)
                ax.set_xscale("log"); ax.set_yscale("log")
                ax.set_title(f"ch {D['ho_daqs'][k]} | {'PASS' if gd['covered'] else 'MISS'} | "
                             f"IS {gd['interval']:.0f}  CRPS {gd['crps']:.0f}", fontsize=8,
                             color=("#2a7" if gd["covered"] else "#c33"))
                ax.tick_params(labelsize=6.5)
            fig.legend(handles=legend, loc="upper center", ncol=4, fontsize=8, frameon=False,
                       bbox_to_anchor=(0.5, 1.005))
            fig.suptitle(f"Held-out FRF + peak-QOI grade — page {pg//PNL+1}", fontsize=10, y=0.965)
            fig.text(0.5, 0.004, "x=freq[Hz,log] y=|accelerance|[g/lbf,log]. ONE posterior predictive, split into "
                     "PARAM uncertainty (theta posterior) and TOTAL = param + model-form discrepancy (~x2.7, the "
                     "same delta as the grade). IS=interval(Winkler), CRPS lower=better; PASS = measured peak inside "
                     "the total band. Real ShockSat (1 hit).", ha="center", fontsize=7, color="#555")
            if pg == 0:
                fig.savefig(WS / "figures" / "report_frf_page1.png", dpi=110, bbox_inches="tight")
            pdf.savefig(fig, bbox_inches="tight"); plt.close(fig)
    print(f"wrote out/heldout_report.pdf | {n_ho} held-out channels, peak PASS {cov}/{n_ho} "
          f"(TOTAL band) | sigma_QOI {D['sig_pk']:.2f} (~x{np.exp(D['sig_pk']):.1f})")


if __name__ == "__main__":
    render(compute())
