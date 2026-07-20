#!/usr/bin/env python3
"""Dive-deeper #3 — DATA-anchored measured-amplitude sigma from the 5 drives (no new hardware).

The per-drive LSQ modal scale a_i^(d) is drive-INDEPENDENT up to a per-drive gain (hammer units + window). So the
cross-drive spread of gain-normalized log|a_i| estimates the EMPIRICAL measured-mode amplitude uncertainty
(vs the hand-assumed SD_A_M=0.35). Also tests whether measured modes share a COMMON scale (pooling justified) or
are independent, and re-runs the shear/normal band with the data-anchored per-mode measured sigma.

Writes out/data_anchored_sigma.json + figures/fig_data_sigma.png.
"""
from __future__ import annotations
import sys, json
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

WS = Path(__file__).resolve().parent.parent
BASE = WS.parent / "shocksat_psd_envelope_twin_20260623"
sys.path.insert(0, str(BASE / "code")); sys.path.insert(0, str(WS / "code"))
import realfrf as rf
import netcg_qoi as NC
import heldout_drive as HD

SD_A_M_ASSUMED, SD_A_U = 0.35, 0.80


def band_factor(model, theta_map, sda, axis, n_mc=300):
    rng = np.random.default_rng(0)
    sdf = np.where(model.is_meas, 0.01, 0.06)
    gr = np.empty(n_mc)
    for t in range(n_mc):
        amp = np.exp(rng.normal(0, 1, model.nM) * sda); fsc = 1 + rng.normal(0, 1, model.nM) * sdf
        gr[t] = NC.grms(NC.octave_smooth(NC.FGRID, model.spectrum(theta_map, axis, amp=amp, fscale=fsc)))
    p = np.percentile(gr, [2.5, 97.5]); return float(p[1] / max(p[0], 1e-30))


def main():
    model = NC.QOIModel()
    z = np.load(WS / "out" / "theta_post_L5.npz", allow_pickle=True)
    theta_map = np.median(z["theta_post"], 0); _, Qmap = model.modes(theta_map)
    meas = rf.reprocess_measured(list(range(1, rf.N_ACCEL_RECORDERS + 1)))
    ch = rf.build_channels(model.R, meas["daq"]); ch_daq = list(ch.daq)
    meas_idx = np.where(model.is_meas)[0]

    # fit a_i for each drive; collect gain-normalized log|a_i| + excitation mask
    logA = []; excited = []          # (n_drive, n_meas)
    drive_labels = []
    for key, (label, dax) in HD.DRIVES.items():
        p = HD.CACHE_DIR / f"{key}.npz"
        if not p.exists():
            continue
        c = np.load(p, allow_pickle=True)
        cdaq = [int(d) for d in c["daq"]]; H1 = np.asarray(c["H1"]); fc = np.asarray(c["freqs"], float)
        dxyz = tuple(float(x) for x in c["xyz"]); common = [d for d in cdaq if d in ch_daq]
        s_rows = np.array([ch.rows[ch_daq.index(d)] for d in common])
        H1c = np.array([H1[cdaq.index(d)] for d in common])
        a, _ = HD.fit_participation(model, Qmap, s_rows, dxyz, dax, H1c.T, fc, meas_idx, model.meas_f)
        aa = np.abs(a); la = np.log(aa + 1e-30) - np.median(np.log(aa + 1e-30))   # remove per-drive gain
        # excitation mask: a drive constrains mode i only if it EXCITES it (|a_i| >= 0.25 * drive median)
        exc = aa >= 0.25 * np.median(aa)
        logA.append(la); excited.append(exc); drive_labels.append(label)
    logA = np.array(logA); excited = np.array(excited)               # (n_drive, n_meas)

    # NAIVE per-mode sigma = std across ALL drives (inflated by poorly-excited modes, per DD1)
    per_mode_sd_naive = logA.std(0)
    # ROBUST per-mode sigma = std across only the drives that EXCITE that mode (>=2 such drives)
    per_mode_sd = np.array([logA[excited[:, i], i].std() if excited[:, i].sum() >= 2 else np.nan
                            for i in range(logA.shape[1])])
    ok = ~np.isnan(per_mode_sd)
    # between-mode vs within-mode on the robust set (pooling test)
    mode_means = np.array([logA[excited[:, i], i].mean() if excited[:, i].sum() >= 2 else np.nan
                           for i in range(logA.shape[1])])
    between_var = float(np.nanvar(mode_means))
    within_var = float(np.nanmean(per_mode_sd[ok] ** 2))
    icc = between_var / (between_var + within_var + 1e-30)

    data_sd_med = float(np.nanmedian(per_mode_sd))
    per_mode_sd = np.where(ok, per_mode_sd, data_sd_med)             # fill unexcitable modes with the median
    # build data-anchored sda: measured modes use their empirical per-mode sd (floored), unmeasured stay SD_A_U
    sda_data = np.where(model.is_meas, SD_A_U, SD_A_U).astype(float)
    sda_data[meas_idx] = np.clip(per_mode_sd, 0.05, 1.5)
    sda_assumed = np.where(model.is_meas, SD_A_M_ASSUMED, SD_A_U)

    bands = {}
    for axis, name in [(0, "shear_X"), (1, "shear_Y"), (2, "normal_Z")]:
        bands[name] = {"assumed_SD_A_M_0.35": round(band_factor(model, theta_map, sda_assumed, axis), 2),
                       "data_anchored": round(band_factor(model, theta_map, sda_data, axis), 2)}

    out = {"n_drives": len(drive_labels), "drives": drive_labels, "n_measured_modes": len(meas_idx),
           "assumed_SD_A_M": SD_A_M_ASSUMED,
           "naive_SD_A_M_median": round(float(np.median(per_mode_sd_naive)), 3),
           "robust_SD_A_M_median": round(data_sd_med, 3),
           "robust_SD_A_M_range": [round(float(per_mode_sd[ok].min()), 3), round(float(per_mode_sd[ok].max()), 3)],
           "n_modes_robustly_estimated": int(ok.sum()),
           "note_robust": "robust = std across only the drives that EXCITE each mode (|a_i|>=0.25*drive median, "
                          ">=2 drives); the naive std is inflated by poorly-excited modes (DD1's +Z@900 73Hz 5x "
                          "outlier is exactly this).",
           "per_mode": [{"hz": round(float(model.meas_f[j]), 1), "emp_sd": round(float(per_mode_sd[i]), 3)}
                        for i, j in enumerate(meas_idx)],
           "pooling_test": {"between_mode_var": round(between_var, 4), "within_drive_var": round(within_var, 4),
                            "ICC": round(icc, 3),
                            "interpretation": ("modes have DISTINCT amplitudes (ICC>0.5) -> a single shared "
                                               "amplitude scale (full pooling) is NOT justified; per-mode or "
                                               "partial pooling only" if icc > 0.5 else
                                               "drive scatter dominates (ICC<0.5) -> a shared amplitude scale "
                                               "(pooling) IS reasonable for the measured modes")},
           "band_factor_assumed_vs_data": bands,
           "verdict": (f"ROBUST empirical measured-mode SD_A_M median {data_sd_med:.2f} (naive "
                       f"{np.median(per_mode_sd_naive):.2f} is inflated by poorly-excited modes) vs assumed 0.35 -> "
                       + ("the 0.35 assumption is roughly OK (shear band stable)" if 0.2 <= data_sd_med <= 0.55 else
                          f"the 0.35 assumption is somewhat OPTIMISTIC; data says ~{data_sd_med:.2f}, widening the "
                          "shear band modestly (see band_factor_assumed_vs_data)")),
           "note": "a_i is the per-drive modal scale (drive-independent up to gain); cross-drive log-spread = the "
                   "empirical amplitude uncertainty. NO NUTS; NO new hardware."}
    (WS / "out" / "data_anchored_sigma.json").write_text(json.dumps(out, indent=2))

    fig, ax = plt.subplots(1, 2, figsize=(12.5, 4.4))
    a0 = ax[0]
    hz = [model.meas_f[j] for j in meas_idx]
    a0.scatter(hz, per_mode_sd, color="#1f4e79", s=28)
    a0.axhline(SD_A_M_ASSUMED, color="#b03030", ls="--", lw=1.2)
    a0.text(hz[0], SD_A_M_ASSUMED + 0.02, "assumed 0.35", color="#b03030", fontsize=8)
    a0.axhline(data_sd_med, color="#2b7a2b", ls="-", lw=1.2)
    a0.text(hz[-1], data_sd_med + 0.02, f"data median {data_sd_med:.2f}", color="#2b7a2b", fontsize=8, ha="right")
    a0.set_xscale("log"); a0.set_xlabel("measured mode frequency [Hz, log]")
    a0.set_ylabel("empirical log-amp sigma (cross-drive)")
    a0.set_xticks([50, 90, 150, 250]); a0.set_xticklabels([50, 90, 150, 250])
    a0.set_title("A. data-anchored measured-amplitude sigma vs assumed", fontsize=10, loc="left")
    a0.spines[["top", "right"]].set_visible(False)
    a1 = ax[1]
    names = list(bands.keys()); x = np.arange(len(names))
    va = [bands[n]["assumed_SD_A_M_0.35"] for n in names]; vd = [bands[n]["data_anchored"] for n in names]
    a1.bar(x - 0.2, va, 0.4, color="#b03030", label="assumed 0.35")
    a1.bar(x + 0.2, vd, 0.4, color="#2b7a2b", label="data-anchored")
    for xi, v in zip(x - 0.2, va):
        a1.text(xi, v + 0.03, f"{v:.2f}", ha="center", fontsize=7.5)
    for xi, v in zip(x + 0.2, vd):
        a1.text(xi, v + 0.03, f"{v:.2f}", ha="center", fontsize=7.5)
    a1.set_xticks(x); a1.set_xticklabels(names); a1.set_ylabel("95% band factor")
    a1.set_title(f"B. band: assumed vs data-anchored (ICC {icc:.2f})", fontsize=10, loc="left")
    a1.legend(fontsize=8); a1.spines[["top", "right"]].set_visible(False)
    cap = (f"Dive-deeper #3: empirical measured-mode amplitude sigma from 5-drive cross-scatter = median "
           f"{data_sd_med:.2f} (range {per_mode_sd.min():.2f}-{per_mode_sd.max():.2f}) vs the hand-assumed 0.35. "
           f"Pooling test ICC={icc:.2f} -> {out['pooling_test']['interpretation'][:70]}. No new hardware.")
    fig.text(0.01, -0.04, cap, fontsize=7.6, va="top", wrap=True)
    fig.tight_layout(rect=[0, 0.03, 1, 1])
    fig.savefig(WS / "figures" / "fig_data_sigma.png", dpi=150, bbox_inches="tight"); plt.close(fig)

    print(f"data-anchored SD_A_M median {data_sd_med:.3f} (range {per_mode_sd.min():.2f}-{per_mode_sd.max():.2f}) "
          f"vs assumed 0.35")
    print(f"pooling ICC {icc:.2f} -> {out['pooling_test']['interpretation'][:70]}")
    for n in names:
        print(f"  {n}: band assumed {bands[n]['assumed_SD_A_M_0.35']}x -> data {bands[n]['data_anchored']}x")


if __name__ == "__main__":
    main()
