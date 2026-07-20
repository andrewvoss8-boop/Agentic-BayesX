#!/usr/bin/env python3
"""Dive-deeper #1 — diagnose the +Z(900) shear_Y held-out-drive gap (cov 0.60, peak miss).

Which mode's Y-participation does the FEM mispredict for the end (y~0) +Z drive? The per-drive answer key uses
FEM shapes (g_i^Y tray-Y participation, phi_drive,i) and fits only the scalar modal scale a_i, so answer-key vs
FEM-twin differ ONLY through a_i vs 1 (x per-drive gain) = where the FEM's effective modal Y-participation is wrong.
Decompose honestly:
  - find the peak frequency where the answer key most exceeds the twin (the miss) + the dominant mode there;
  - report that culprit mode: freq (measured vs FEM), measured/unmeasured, |a_i*gain| for +Z(900);
  - CROSS-DRIVE check: is the culprit's a_i an OUTLIER for +Z(900) (a drive-specific/observability effect) or
    consistent across drives but != 1 (a systematic FEM modal-participation error)?
Writes out/diag_shearY_gap.json + figures/fig_shearY_gap.png.
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

AXIS, NAME = 1, "shear_Y"
DR = HD.DRIVES


def fit_all_drives(model, Qmap, ch, meas_idx):
    ch_daq = list(ch.daq); fits = {}
    for key, (label, dax) in DR.items():
        p = HD.CACHE_DIR / f"{key}.npz"
        if not p.exists():
            continue
        c = np.load(p, allow_pickle=True)
        cdaq = [int(d) for d in c["daq"]]; H1 = np.asarray(c["H1"]); fc = np.asarray(c["freqs"], float)
        dxyz = tuple(float(x) for x in c["xyz"]); common = [d for d in cdaq if d in ch_daq]
        s_rows = np.array([ch.rows[ch_daq.index(d)] for d in common])
        H1c = np.array([H1[cdaq.index(d)] for d in common])
        a, phid = HD.fit_participation(model, Qmap, s_rows, dxyz, dax, H1c.T, fc, meas_idx, model.meas_f)
        fits[label] = {"a": a, "phid": phid, "dxyz": dxyz, "dax": dax}
    return fits


def main():
    model = NC.QOIModel()
    z = np.load(WS / "out" / "theta_post_L5.npz", allow_pickle=True)
    theta_post = z["theta_post"]; theta_map = np.median(theta_post, 0)
    _, Qmap = model.modes(theta_map)
    meas = rf.reprocess_measured(list(range(1, rf.N_ACCEL_RECORDERS + 1)))
    ch = rf.build_channels(model.R, meas["daq"]); meas_idx = np.where(model.is_meas)[0]
    fits = fit_all_drives(model, Qmap, ch, meas_idx)

    F = fits["+Z(900)"]; a = F["a"]; phid = F["phid"]
    g = model.g_axis(Qmap, AXIS)
    ans = HD.answer_key(model, AXIS, Qmap, a, phid, meas_idx, model.meas_f)
    lo, med, hi = HD.per_drive_band(model, theta_post, AXIS, F["dxyz"], F["dax"], kind="statfem_fk")
    gain = NC.grms(NC.octave_smooth(NC.FGRID, ans)) / (NC.grms(NC.octave_smooth(NC.FGRID, med)) + 1e-300)
    med_g, hi_g, lo_g = med * gain, hi * gain, lo * gain
    ans_s = NC.octave_smooth(NC.FGRID, ans); hi_s = NC.octave_smooth(NC.FGRID, hi_g)
    # miss = where the answer key has ENERGY and exceeds the band (energy-weighted exceedance) -> the real peak miss
    exceed = np.clip(ans_s - hi_s, 0, None) * ans_s
    miss_k = int(np.argmax(exceed)) if exceed.max() > 0 else int(np.argmax(ans_s))
    miss_hz = float(NC.FGRID[miss_k])

    # dominant measured mode at the miss frequency (by |per-mode measured contribution|)
    w = 2 * np.pi * NC.FGRID[miss_k]; contrib = []
    for ii, j in enumerate(meas_idx):
        wi = 2 * np.pi * model.meas_f[j]
        D = wi ** 2 - w ** 2 + 2j * NC.ZETA * wi * w
        contrib.append(abs(a[ii] * g[j] * phid[j] * wi ** 2 / D))
    contrib = np.array(contrib); order = np.argsort(contrib)[::-1]
    culprit_ii = int(order[0]); culprit_j = int(meas_idx[culprit_ii])

    # cross-drive a_i for the culprit (per-drive gain-normalized) -> outlier vs systematic
    def gainnorm(fit):
        aa = fit["a"]; return np.median(np.abs(aa))
    culprit_a = {}
    for label, fit in fits.items():
        # match culprit mode index within that drive's measured set (same meas_idx ordering)
        culprit_a[label] = float(np.abs(fit["a"][culprit_ii]) / (gainnorm(fit) + 1e-30))
    vals = np.array(list(culprit_a.values())); zscore = (culprit_a["+Z(900)"] - np.median(vals)) / (np.std(vals) + 1e-9)

    fem_hz = float(model.fnom[culprit_j]); meas_hz = float(model.meas_f[culprit_j])
    verdict = ("drive-specific outlier (+Z@900 weakly/anomalously excites this Y-mode -> reconstruction sensitive; "
               "the OTHER drives constrain it, so the delivered shear_Y is reliable except this end-drive)"
               if abs(zscore) > 1.5 else
               "systematic: the FEM mis-scales this mode's net Y-participation across drives (a real model-form "
               "error worth a targeted look, e.g. mass/stiffness asymmetry at the y~0 end)")

    out = {"drive": "+Z(900)", "qoi": NAME, "heldout_drive_coverage": 0.60,
           "miss_frequency_hz": round(miss_hz, 1),
           "culprit_mode": {"fem_hz": round(fem_hz, 1), "measured_hz": round(meas_hz, 1),
                            "measured": True, "freq_err_pct": round(100 * (fem_hz - meas_hz) / meas_hz, 2)},
           "culprit_a_gainnorm_by_drive": {k: round(v, 3) for k, v in culprit_a.items()},
           "plusZ900_zscore_vs_other_drives": round(float(zscore), 2),
           "verdict": verdict,
           "note": "answer key uses FEM shapes (g^Y, phi_drive) + fitted scalar a_i, so the gap localizes to a "
                   "mode whose effective modal Y-participation the FEM gets wrong for this drive; cross-drive a_i "
                   "separates drive-specific from systematic. NO NUTS."}
    (WS / "out" / "diag_shearY_gap.json").write_text(json.dumps(out, indent=2))

    # figure: answer key vs twin band (+Z900 shear_Y) + miss marker + cross-drive a_i
    fig, ax = plt.subplots(1, 2, figsize=(12.5, 4.4))
    a0 = ax[0]
    a0.fill_between(NC.FGRID, lo_g, hi_g, color="#1f4e79", alpha=0.22, lw=0, label="twin 95% band (statFEM F(k))")
    a0.plot(NC.FGRID, med_g, color="#1f4e79", lw=1.4)
    a0.plot(NC.FGRID, ans, color="#b03030", lw=1.6, label="held-out-drive answer key (measured)")
    a0.axvline(miss_hz, color="#c8862b", ls="--", lw=1.2)
    a0.text(miss_hz, ans.max(), f" miss @ {miss_hz:.0f} Hz\n culprit {fem_hz:.0f} Hz", color="#c8862b", fontsize=8, va="top")
    a0.set_xscale("log"); a0.set_yscale("log"); a0.set_xlim(45, 260)
    a0.set_xticks([45, 90, 150, 260]); a0.set_xticklabels([45, 90, 150, 260])
    a0.set_xlabel("frequency [Hz, log]"); a0.set_ylabel("net-CG shear_Y |G| (arb.)")
    a0.set_title("A. +Z(900) shear_Y: twin band vs measured answer key", fontsize=10, loc="left")
    a0.legend(fontsize=7.5, loc="lower center"); a0.spines[["top", "right"]].set_visible(False)
    a1 = ax[1]
    labels = list(culprit_a.keys()); vv = [culprit_a[l] for l in labels]
    y = np.arange(len(labels))[::-1]
    cols = ["#b03030" if l == "+Z(900)" else "#8aa" for l in labels]
    a1.barh(y, vv, color=cols)
    a1.axvline(float(np.median(vv)), color="#333", ls=":", lw=1)
    for yi, l, v in zip(y, labels, vv):
        a1.text(v + 0.02, yi, f"{l} {v:.2f}", va="center", fontsize=8)
    a1.set_yticks([]); a1.set_xlabel(f"culprit mode {fem_hz:.0f} Hz: gain-norm |a_i| per drive")
    a1.set_title(f"B. cross-drive scale (z={zscore:.1f}) -> {'drive-specific' if abs(zscore)>1.5 else 'systematic'}",
                 fontsize=10, loc="left")
    a1.spines[["top", "right", "left"]].set_visible(False)
    cap = (f"Dive-deeper #1: the ONE caught held-out-drive gap (+Z@900 shear_Y, cov 0.60). Miss at {miss_hz:.0f} Hz, "
           f"culprit measured mode {fem_hz:.0f} Hz (freq err {100*(fem_hz-meas_hz)/meas_hz:+.1f}%). Cross-drive "
           f"gain-normalized modal scale z={zscore:.1f} -> {verdict.split('(')[0].strip()}.")
    fig.text(0.01, -0.04, cap, fontsize=7.6, va="top", wrap=True)
    fig.tight_layout(rect=[0, 0.03, 1, 1])
    fig.savefig(WS / "figures" / "fig_shearY_gap.png", dpi=150, bbox_inches="tight"); plt.close(fig)

    print(f"miss @ {miss_hz:.1f} Hz; culprit mode {fem_hz:.1f} Hz (meas {meas_hz:.1f}, err "
          f"{100*(fem_hz-meas_hz)/meas_hz:+.1f}%)")
    print(f"culprit gain-norm |a_i| by drive: {out['culprit_a_gainnorm_by_drive']}")
    print(f"+Z(900) z-score vs other drives: {zscore:.2f} -> {verdict[:60]}...")


if __name__ == "__main__":
    main()
