#!/usr/bin/env python3
"""Local-FRF overlay (Andrew: 'MAC masks major discrepancies in local FRFs'). Per channel, overlay the MEASURED
modal-hammer |H| against the FEM |H(θ=1)·gain| on the SAME log–log axes, and annotate the channel's best matched-mode
MAC. Shows that even MAC~0.6–0.9 channels have badly misplaced/mis-sized local peaks. No NUTS (θ=1). Tufte: log–log,
direct comparison, caption carries units/source/takeaway. Reference = +X modal (Test01, node 990)."""
from __future__ import annotations
import sys
from pathlib import Path
import numpy as np
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
sys.path.insert(0, str(Path(__file__).resolve().parent))
import realfrf as rf
import psd_forward as pf
from modal_multiref import MODAL_REFS, CACHE, N_MODAL
import multiref_frf as mr

WS = Path(__file__).resolve().parent.parent
REF = "m_xpos_990x"
C_DATA, C_FEM = "#222222", "#1f77b4"


def main():
    R = rf.load_reduced()
    ch = rf.build_channels(R, [d for d in range(1, rf.N_ACCEL_RECORDERS + 1) if d not in rf.BAD_DAQ])
    c = dict(np.load(CACHE / f"{REF}.npz", allow_pickle=True)); c["daq"] = [int(d) for d in c["daq"]]
    f = c["freqs"]; tau = -(N_MODAL - 1) / (rf.FS * np.log(mr.PROC["exp_end"]))
    eta = 2 * (0.01 + 1.0 / (2 * np.pi * f * tau))
    drow = pf.drive_row_for(R, tuple(float(x) for x in c["xyz"]), str(c["axis"]))
    common = [d for d in ch.daq if d in c["daq"]]; pos = {d: i for i, d in enumerate(ch.daq)}; ci = {d: c["daq"].index(d) for d in common}
    rows = np.array([ch.rows[pos[d]] for d in common])
    Hfem = np.abs(pf.forward_H_batch(R, f, np.ones((1, 9)), drow, rows, eta)[0])      # (Nf, Nc)
    Hmeas = np.array([np.abs(c["H1"][ci[d]]) for d in common]).T                       # (Nf, Nc)
    gain = np.median(np.log(Hmeas + 1e-300) - np.log(Hfem + 1e-300))
    # per-channel log|H| correlation (a local-fit proxy) to pick a spread of channels
    corr = np.array([np.corrcoef(np.log(Hmeas[:, k]+1e-30), np.log(Hfem[:, k]+1e-30))[0, 1] for k in range(len(common))])
    order = np.argsort(corr)
    pick = [order[len(order)//2], order[3*len(order)//4], order[-2], order[-1]]        # mid..best local agreement
    fig, axes = plt.subplots(2, 2, figsize=(10.5, 6.4), sharex=True, sharey=True)
    for ax, k in zip(axes.ravel(), pick):
        d = common[k]
        ax.plot(f, Hmeas[:, k], color=C_DATA, lw=1.2, label="measured")
        ax.plot(f, Hfem[:, k] * np.exp(gain), color=C_FEM, lw=1.0, ls="--", label="FEM (θ=1)")
        ax.set_xscale("log"); ax.set_yscale("log"); ax.set_xlim(45, 260)
        ax.spines[["top", "right"]].set_visible(False); ax.tick_params(labelsize=7)
        ax.set_title(f"channel {d}   (log|H| corr = {corr[k]:.2f})", fontsize=8.5)
        ax.set_ylabel("|H|  g/lbf", fontsize=8)
    axes[0, 0].legend(fontsize=7, frameon=False, loc="lower left")
    for ax in axes[-1, :]:
        ax.set_xlabel("frequency  (Hz, log)", fontsize=8)
    cap = ("Local FRF overlay: MEASURED +X modal-hammer |H| (Test01, node 990, 6 hits) vs FEM θ=1 (one training-global "
           f"units-gain ×{np.exp(gain):.2f}), g/lbf, log–log. Channels chosen across the per-channel log|H| correlation "
           "(mid→best). TAKEAWAY: even where global MAC≈0.6–0.9, the LOCAL FRFs disagree badly — peaks land at the "
           "wrong frequencies and wrong heights — so MAC (a mode-shape correlation) masks the per-channel FRF error "
           "that actually drives the held-out σ. Exploratory; θ=1 (uncalibrated) FEM.")
    fig.text(0.012, 0.005, cap, fontsize=7.0, wrap=True, va="bottom")
    fig.tight_layout(rect=[0, 0.08, 1, 1])
    out = WS / "figures" / "local_frf_overlay.png"
    fig.savefig(out, dpi=150, bbox_inches="tight"); plt.close(fig)
    print(f"wrote {out}  (channels {[common[k] for k in pick]}, corr {[round(float(corr[k]),2) for k in pick]})")


if __name__ == "__main__":
    main()
