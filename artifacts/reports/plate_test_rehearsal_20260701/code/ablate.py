#!/usr/bin/env python3
"""POST-HOC ablation: which ingredient of the honest delivery destroys the analytic buy-down?

Ladder from the pretest's analytic recipe to the rehearsal's delivery, one ingredient at a time
(all no-NUTS, MC only; median band factor over 8 truth realizations where applicable):
  L0  pretest repro: theta FIXED at MAP, all-lognormal tiers, target sda 0.80, target sdf 6%
  L1  pretest floor: L0 but target sda 0.35              (should reproduce ~5.4 -> ~2.8)
  L2  L1 + theta ~ posterior draws                       (theta-spread effect)
  L3  L2 + target sdf 1% (test measures target freqs)    (freq-tier effect)
  L4  L3 but targets = signed-mixture pinned to truth (c_sd 0.10, d=0)  (distribution effect)
  L5  L4 + d ~ prior (out-of-basis floor)                = the rehearsal delivery at 12 sensors
Writes out/ablation.json. NOT pre-registered; mechanism diagnostic.
"""
from __future__ import annotations
import json, os, sys
from pathlib import Path
os.environ.setdefault("OMP_NUM_THREADS", "1"); os.environ.setdefault("VECLIB_MAXIMUM_THREADS", "1")
import numpy as np

WS = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(WS / "code"))
from rehearsal import Setup, SD_A_M, SD_A_U, SD_F_M, SD_F_U   # noqa: E402
import netcg_qoi as NC                                         # noqa: E402


def run(S, theta_mode, tgt_sda, tgt_sdf, tgt_mode, d_on, n_truth=8, n_th=20, n_rep=25, seed=11):
    m = S.model; kap = S.kappa(0.80)
    rng = np.random.default_rng(seed)
    sdf = np.where(m.is_meas, SD_F_M, SD_F_U).copy(); sdf[S.tgt] = tgt_sdf
    sda = np.where(m.is_meas, SD_A_M, SD_A_U).copy(); sda[S.tgt] = 0.0   # targets handled per mode
    n_t, n_b, n_e = len(S.tgt), len(S.basis), len(S.extra)
    e = np.zeros((n_t, n_b)); e[np.arange(n_t), S.tix] = 1.0
    idx = (np.linspace(0, len(S.theta_post) - 1, n_th).astype(int) if theta_mode == "post"
           else [None] * 1)
    bfs = []
    for _ in range(n_truth if tgt_mode == "mix" else 1):
        c_true = e + rng.normal(0, kap, (n_t, n_b))
        grms_s = []
        ths = idx if theta_mode == "post" else [None] * n_th
        for s in ths:
            th = S.theta_post[s] if s is not None else S.theta_map
            f, Q = m.modes(th); fi = f[m.inb]; gg = m.g_axis(Q, 2)
            wib = 2 * np.pi * fi; w = 2 * np.pi * NC.FGRID
            for _ in range(n_rep):
                amp = np.exp(rng.normal(0, 1, m.nM) * sda)
                if tgt_mode == "lognormal":
                    amp[S.tgt] = np.exp(rng.normal(0, tgt_sda, n_t))
                else:  # signed mixture pinned to truth
                    cd = c_true + rng.normal(0, 0.10, (n_t, n_b))
                    dd = rng.normal(0, kap, (n_t, n_e)) if d_on else np.zeros((n_t, n_e))
                    gt = cd @ S.g_basis + dd @ S.g_extra
                    amp[S.tgt] = gt / (S.g_map[S.tgt] + 1e-30)
                fsc = 1 + rng.normal(0, 1, m.nM) * sdf
                wi = wib * fsc; g = gg * amp
                D = wi[:, None] ** 2 - w[None, :] ** 2 + 2j * NC.ZETA * wi[:, None] * w[None, :]
                sp = np.abs(((g[:, None] * wi[:, None] ** 2) / D).sum(0))
                grms_s.append(NC.grms(NC.octave_smooth(NC.FGRID, sp)))
        p = np.percentile(grms_s, [2.5, 97.5])
        bfs.append(float(p[1] / p[0]))
    return round(float(np.median(bfs)), 2)


def main():
    S = Setup()
    out = {
        "NOTE": "POST-HOC mechanism ablation, not pre-registered; no NUTS (MC only).",
        "L0_pretest_repro_sda080": run(S, "map", 0.80, SD_F_U, "lognormal", False),
        "L1_pretest_floor_sda035": run(S, "map", 0.35, SD_F_U, "lognormal", False),
        "L2_plus_theta_post":      run(S, "post", 0.35, SD_F_U, "lognormal", False),
        "L3_plus_tgt_freq_1pct":   run(S, "post", 0.35, SD_F_M, "lognormal", False),
        "L4_mixture_pinned_d0":    run(S, "post", None, SD_F_M, "mix", False),
        "L5_plus_d_prior":         run(S, "post", None, SD_F_M, "mix", True),
    }
    (WS / "out" / "ablation.json").write_text(json.dumps(out, indent=1))
    print(json.dumps(out, indent=1))


if __name__ == "__main__":
    main()
