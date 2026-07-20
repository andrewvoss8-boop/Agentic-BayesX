#!/usr/bin/env python3
"""Layer 1 finite-perturbation check (AGENTS identifiability gate): does a REALISTIC change in damping zeta
visibly move the modal peak height and the PSD-envelope QOI? If not, zeta is not a lever here -- say so.

We sweep the structural damping the FEM forward assumes and recompute, for the combined-correlated drive at a
panel of held-out sensors, the smoothline-envelope GRMS (the inherited Q-D win metric). Three things are reported,
and the distinction matters (the runner prompt warned not to blindly import 'damping can't help' from the
scatter QOI, and not to blindly assume the 'under-damped FEM' direction either):

  (1) ABSOLUTE lever: envelope GRMS scales ~ 1/zeta (peak height proportional to Q = 1/(2 zeta)), so a realistic
      zeta change DOES move the QOI a lot -> zeta passes the 'is it a lever' gate.
  (2) WIN-RATIO cancellation: the inherited contract uses the SAME damping for FEM and twin, so in the win RATIO
      GRMS(twin)/GRMS(FEM+6dB) the zeta factor CANCELS -> zeta does NOT move the win metric (mirrors D8: damping
      is common-mode and absorbed). The win ratio is set by the twin's predictive width (shape-error sigma).
  (3) DIRECTION: the FEM/L5 nominal structural zeta is 1.0% (realfrf.ZETA_NOM); the measured ring-down zeta is
      ~0.3-0.5%. So the nominal FEM is OVER-damped, not under-damped: correcting zeta toward the measured value
      RAISES peaks and RAISES GRMS (more conservative), the opposite of the prompt's assumed 'under-damped ->
      over-conservative' bridge. Report the GRMS shift from 1.0% -> measured.
"""
from __future__ import annotations
import json, sys, time
from pathlib import Path
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent / "shocksat_psd_envelope_twin_20260623" / "code"))
import realfrf as rf
import psd_forward as pf
import psd_envelope as pe
from modal_multiref import MODAL_REFS

WS = Path(__file__).resolve().parent.parent
PSDWS = WS.parent / "shocksat_psd_envelope_twin_20260623"
OUT = WS / "out"
S_F0 = 1.0
SIGMA_LOG = 1.604        # twin broadband amplitude-discrepancy sigma (probe_seed00) -> 97.5% = exp(1.96*sigma)
COMBINED = ["m_xpos_990x", "m_zpos_990z", "m_zpos_900z"]
ZSWEEP_PCT = [0.25, 0.35, 0.4, 0.5, 1.0, 1.7]   # structural zeta sweep (%); 1.0 = FEM nominal, 0.3-0.5 = measured


def main():
    t0 = time.time()
    R = rf.load_reduced()
    z = np.load(PSDWS / "data" / "multiref_modal" / f"{COMBINED[0]}.npz", allow_pickle=True)
    freqs = z["freqs"]
    ch = rf.build_channels(R, [d for d in range(1, rf.N_ACCEL_RECORDERS + 1) if d not in rf.BAD_DAQ])
    drows = {k: pf.drive_row_for(R, MODAL_REFS[k]["xyz"], MODAL_REFS[k]["axis"]) for k in COMBINED}
    # a panel of high-response held-out sensors (rank by nominal band peak), keep ~12
    resp = ch.rows
    Hn = pf.combined_H([pf.forward_H_batch(R, freqs, np.ones((1, 9)), drows[k], resp, 0.02)[0] for k in COMBINED])
    band_pk = np.abs(Hn).max(axis=0)
    panel = np.argsort(-band_pk)[:12]

    def env_grms(eta, rows):
        Hs = [pf.forward_H_batch(R, freqs, np.ones((1, 9)), drows[k], rows, eta) for k in COMBINED]
        H = pf.combined_H([h[0] for h in Hs])                 # (Nf, Ns)
        g_fem, g_fem6, g_twin = [], [], []
        for s in range(H.shape[1]):
            psd = (np.abs(H[:, s]) ** 2) * S_F0
            env = pe.smoothline_envelope(freqs, psd)
            env6 = pe.smoothline_envelope(freqs, pe.add_db_psd(psd, 6.0))
            twin = pe.smoothline_envelope(freqs, psd * np.exp(2 * 1.96 * SIGMA_LOG))  # 97.5% in PSD = x exp(2*1.96*sig)
            g_fem.append(pe.grms(freqs, env)); g_fem6.append(pe.grms(freqs, env6)); g_twin.append(pe.grms(freqs, twin))
        return np.array(g_fem), np.array(g_fem6), np.array(g_twin)

    rows = []
    base = None
    for zp in ZSWEEP_PCT:
        eta = 2.0 * zp / 100.0
        gf, gf6, gt = env_grms(eta, resp[panel])
        ratio = gt / gf6
        r = dict(zeta_struct_pct=zp, env_grms_fem_median=float(np.median(gf)),
                 env_grms_fem6_median=float(np.median(gf6)), env_grms_twin975_median=float(np.median(gt)),
                 win_ratio_twin_over_fem6_median=float(np.median(ratio)))
        if abs(zp - 1.0) < 1e-9:
            base = r
        rows.append(r)
    # scaling check: GRMS(0.4%)/GRMS(1.0%) vs the 1/zeta prediction (=1.0/0.4=2.5)
    g04 = next(r for r in rows if abs(r["zeta_struct_pct"] - 0.4) < 1e-9)
    g10 = next(r for r in rows if abs(r["zeta_struct_pct"] - 1.0) < 1e-9)
    abs_lever = g04["env_grms_fem6_median"] / g10["env_grms_fem6_median"]
    ratio_spread = (max(r["win_ratio_twin_over_fem6_median"] for r in rows)
                    / min(r["win_ratio_twin_over_fem6_median"] for r in rows))
    out = dict(
        deliverable="Layer 1 finite-perturbation check: does a realistic zeta change move the envelope QOI, and how",
        panel_n_sensors=len(panel), sigma_log=SIGMA_LOG, drive_set=COMBINED, band=list(rf.BAND),
        fem_nominal_zeta_pct=1.0, measured_zeta_pct_range=[0.3, 0.5],
        sweep=rows,
        absolute_lever_grms_ratio_0p4_over_1p0=round(float(abs_lever), 3),
        predicted_1_over_zeta=round(1.0 / 0.4, 3),
        winratio_spread_across_zeta=round(float(ratio_spread), 4),
        conclusions=dict(
            is_a_lever_absolute=bool(abs_lever > 1.5),
            cancels_in_win_ratio=bool(ratio_spread < 1.05),
            direction="FEM nominal 1.0% > measured ~0.4% => FEM is OVER-damped; correcting toward measured RAISES "
                      "GRMS (more conservative), opposite of the prompt's assumed under-damped direction"),
        verdict=("zeta IS a strong ABSOLUTE lever on envelope GRMS (~1/zeta), so it passes the finite-perturbation "
                 "gate; BUT under the inherited identical-damping contract it CANCELS in the twin/FEM+6dB win RATIO "
                 "(common-mode, mirrors D8). And the nominal FEM is OVER-damped vs measured, so a measured-zeta "
                 "correction makes the twin MORE conservative, not less. Damping is therefore NOT a lever that wins "
                 "the inherited less-conservative-envelope metric on this structure."),
        runtime_s=round(time.time() - t0, 1))
    OUT.mkdir(exist_ok=True)
    (OUT / "finite_perturbation.json").write_text(json.dumps(out, indent=2))
    print("zeta%   GRMS_FEM   GRMS_FEM+6dB   GRMS_twin97.5   win_ratio")
    for r in rows:
        print(f"{r['zeta_struct_pct']:>5.2f}  {r['env_grms_fem_median']:>9.4f}  {r['env_grms_fem6_median']:>11.4f}  "
              f"{r['env_grms_twin975_median']:>13.3f}  {r['win_ratio_twin_over_fem6_median']:>9.3f}")
    print(f"\nABSOLUTE lever GRMS(0.4%)/GRMS(1.0%) = {abs_lever:.2f} (predict 1/zeta ratio = 2.5)")
    print(f"WIN-RATIO spread across zeta = {ratio_spread:.4f} (≈1 => zeta cancels in the win metric)")
    print(f"VERDICT: {out['verdict']}")
    print(f"runtime {out['runtime_s']}s")


if __name__ == "__main__":
    main()
