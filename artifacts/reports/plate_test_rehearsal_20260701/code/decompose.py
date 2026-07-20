#!/usr/bin/env python3
"""POST-HOC mechanism decomposition (clearly labeled: NOT pre-registered; diagnostic only).

Why is the rehearsed 12-sensor band ~6x when the analytic curve promised 3.5x?
Decompose the PRIOR (no NUTS needed — the mechanism lives in the truth/tier model):
  arm P_full : c ~ prior, d ~ prior          (= the no-sensor band, reproduces ~5.8x)
  arm P_cfix : c = truth-centered tight (sd 0.10, the ~12-sensor posterior level), d ~ prior
               -> what the sensors CAN buy (in-basis) with the out-of-basis floor intact
  arm P_dzero: c ~ prior, d = 0              -> how much width the out-of-basis term alone adds
  arm P_both : c tight AND d = 0             -> the in-basis-only promise (analytic-curve regime)
Also reports, for each: the UPPER-edge ratio (97.5%/median GRMS) — the loads-decision-relevant
half of the band — and the share of target-amp log-variance carried by the out-of-basis term.
Writes out/decomposition.json.
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


def band(S, kap, c_sd, d_on, n_truth=8, n_th=20, n_rep=25, seed=9):
    """Per-TRUTH band (truth drawn ONCE per outer loop; the 'posterior' tracks it with sd c_sd) —
    median band factor across truths. This matches how a real per-seed delivery conditions on one
    truth; re-drawing the truth per rep would convolve the prior back in (the bug this replaces)."""
    m = S.model
    rng = np.random.default_rng(seed)
    sdf = np.where(m.is_meas, SD_F_M, SD_F_U).copy(); sdf[S.tgt] = SD_F_M
    sda = np.where(m.is_meas, SD_A_M, SD_A_U).copy()
    n_t, n_b, n_e = len(S.tgt), len(S.basis), len(S.extra)
    e = np.zeros((n_t, n_b)); e[np.arange(n_t), S.tix] = 1.0
    idx = np.linspace(0, len(S.theta_post) - 1, n_th).astype(int)
    bfs, ues = [], []
    for _ in range(n_truth):
        c_true = e + rng.normal(0, kap, (n_t, n_b))          # ONE truth per band
        grms_s = []
        for s in idx:
            th = S.theta_post[s]
            f, Q = m.modes(th); fi = f[m.inb]; gg = m.g_axis(Q, 2)
            wib = 2 * np.pi * fi; w = 2 * np.pi * NC.FGRID
            for _ in range(n_rep):
                amp = np.exp(rng.normal(0, 1, m.nM) * sda)
                if c_sd == "prior":      # no data: posterior == prior, centered at the MODEL (e)
                    cd = e + rng.normal(0, kap, (n_t, n_b))
                else:                    # sensors: posterior tracks THIS truth with width c_sd
                    cd = c_true + rng.normal(0, float(c_sd), (n_t, n_b))
                dd = rng.normal(0, kap, (n_t, n_e)) if d_on else np.zeros((n_t, n_e))
                gt = cd @ S.g_basis + dd @ S.g_extra
                amp[S.tgt] = gt / (S.g_map[S.tgt] + 1e-30)
                fsc = 1 + rng.normal(0, 1, m.nM) * sdf
                wi = wib * fsc; g = gg * amp
                D = wi[:, None] ** 2 - w[None, :] ** 2 + 2j * NC.ZETA * wi[:, None] * w[None, :]
                sp = np.abs(((g[:, None] * wi[:, None] ** 2) / D).sum(0))
                grms_s.append(NC.grms(NC.octave_smooth(NC.FGRID, sp)))
        p = np.percentile(grms_s, [2.5, 50, 97.5])
        bfs.append(float(p[2] / p[0])); ues.append(float(p[2] / p[1]))
    return {"band_factor_97p5_over_2p5": round(float(np.median(bfs)), 2),
            "upper_edge_97p5_over_median": round(float(np.median(ues)), 2),
            "band_factor_range_over_truths": [round(min(bfs), 2), round(max(bfs), 2)]}


def main():
    S = Setup()
    kap = S.kappa(0.80)
    # variance shares of the target-amp perturbation: in-basis (c) vs out-of-basis (d)
    rng = np.random.default_rng(3)
    n_t = len(S.tgt)
    vc = np.var(rng.normal(0, kap, (4000, n_t, len(S.basis))) @ S.g_basis, axis=0)
    vd = np.var(rng.normal(0, kap, (4000, n_t, len(S.extra))) @ S.g_extra, axis=0)
    d_share = vd / (vc + vd)
    out = {
        "NOTE": "POST-HOC diagnostic (not pre-registered); prior-level mechanism decomposition, no NUTS.",
        "kappa": round(float(kap), 4),
        "d_share_of_target_net_perturbation_variance": [round(float(x), 3) for x in d_share],
        "arms": {
            "P_full (no sensors: c=prior, d=prior)": band(S, kap, c_sd="prior", d_on=True),
            "P_cfix (c tight 0.10 on truth, d prior)": band(S, kap, c_sd=0.10, d_on=True),
            "P_dzero (c=prior, d=0)":                band(S, kap, c_sd="prior", d_on=False),
            "P_both (c tight on truth, d=0)":        band(S, kap, c_sd=0.10, d_on=False),
        },
    }
    (WS / "out" / "decomposition.json").write_text(json.dumps(out, indent=1))
    print(json.dumps(out, indent=1))


if __name__ == "__main__":
    main()
