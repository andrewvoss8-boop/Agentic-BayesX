#!/usr/bin/env python3
"""Discretization-resolution gate (NEW file). The QOI is the held-out peak/band accelerance; we resolve it on
the same reduced 74-mode basis as the companion (SHA-matched reduced_blocks.npz).

This study is INTERNALLY EXACT — truth and inference both use the SAME 74-mode reduced model — so the reduced-
vs-full modal-TRUNCATION error does NOT affect the collapse/plateau verdict (it would shift truth and model
identically). We therefore:
  (1) compute FRESH, here: a modal-truncation refinement WITHIN the reduced basis (74 vs fewer retained modes)
      and a frequency-grid-density refinement (Nf vs 2Nf), both as QOI-value shifts at a held-out sensor;
  (2) INHERIT (cited, not recomputed) the companion's reduced-vs-full FRF number, which used a 399510-DOF
      full-order eigensolve on the IDENTICAL SHA-matched reduced_blocks.npz — re-running that here is forbidden
      by the card ("do NOT re-assemble the 67k FEM"). Clearly labeled as inherited provenance + internal-exact.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
WS = HERE.parent
COMP = WS.parent / "statfem_shocksat_eval_20260616"
sys.path.insert(0, str(HERE))

import core  # noqa: E402


def frf_trunc(model, freqs, theta, sensors, drive, n_modes, zeta=core.ZETA_NOM):
    """Reduced-basis FRF using only the lowest n_modes eigenpairs of K_red(theta)."""
    K = model.A_fix + np.einsum("g,gij->ij", np.asarray(theta), model.A)
    lam, Q = np.linalg.eigh(K)
    lam = np.clip(lam, 1e-9, None)
    order = np.argsort(lam)[:n_modes]
    lam = lam[order]; Q = Q[:, order]
    eta = 2.0 * float(zeta)
    omega = 2.0 * np.pi * np.asarray(freqs)
    U = model.obs_V[sensors, :] @ Q
    ud = model.obs_V[drive, :] @ Q
    g = (1.0 + 1j * eta) * lam[None, :] - (omega ** 2)[:, None]
    return -(omega ** 2)[:, None] * np.einsum("sk,k,fk->fs", U.astype(complex), ud.astype(complex), 1.0 / g)


def main():
    model = core.load_model()
    ch = core.select_channels(model, n_observed=18)
    drive = ch["drive"]; hs = ch["heldout"][0]
    theta = core.theta_vector(core.COMBOS[3]["theta"])

    # modal-truncation refinement (within the 74-mode reduced basis)
    f160 = core.freq_grid(160)
    ref = frf_trunc(model, f160, theta, [hs], drive, model.r)        # all 74
    trunc = {}
    for k in (40, 60, 70, model.r):
        Hk = frf_trunc(model, f160, theta, [hs], drive, k)
        pk_e = abs(core.qoi_peak(np.abs(Hk[:, 0])) / core.qoi_peak(np.abs(ref[:, 0])) - 1)
        bd_e = abs(core.qoi_band(np.abs(Hk[:, 0]), f160) / core.qoi_band(np.abs(ref[:, 0]), f160) - 1)
        trunc[str(k)] = {"peak_rel_err": float(pk_e), "band_rel_err": float(bd_e)}
    max_trunc = max(max(v["peak_rel_err"], v["band_rel_err"]) for k, v in trunc.items() if k != str(model.r))

    # frequency-grid-density refinement: QOI at Nf vs 2Nf (same band), as a QOI-value shift
    grid = {}
    for nf in (80, 160, 320, 640):
        H = frf_trunc(model, core.freq_grid(nf), theta, [hs], drive, model.r)
        f = core.freq_grid(nf)
        grid[str(nf)] = {"peak": float(core.qoi_peak(np.abs(H[:, 0]))),
                         "band": float(core.qoi_band(np.abs(H[:, 0]), f))}
    # max QOI rel shift between successive densities
    nfs = [80, 160, 320, 640]
    gshift = max(max(abs(grid[str(b)]["peak"] / grid[str(a)]["peak"] - 1),
                     abs(grid[str(b)]["band"] / grid[str(a)]["band"] - 1))
                 for a, b in zip(nfs[:-1], nfs[1:]))

    # inherited reduced-vs-full (cited; identical SHA-matched reduced_blocks; not recomputed here)
    comp_dz = json.load(open(COMP / "out" / "discretization.json"))
    inh = comp_dz["reduced_vs_full"]["max_rel_err_at_peaks"]

    out = {
        "qoi": "held-out peak/band accelerance on the reduced 74-mode basis",
        "reduced_vs_full": {
            "max_rel_err_at_peaks": float(inh),
            "diagnosis": "INHERITED (cited, not recomputed) from the companion statfem_shocksat_eval_20260616, "
                         "which solved a 399510-DOF full-order eigensolve on the IDENTICAL SHA-matched "
                         "reduced_blocks.npz; re-running the full solve is forbidden by the card ('do NOT "
                         "re-assemble the 67k FEM'). This is the 74-mode modal-TRUNCATION error (fmax 321 Hz "
                         "≈ 1.2× band). It does NOT affect the collapse/plateau verdict: this study is "
                         "INTERNALLY EXACT (truth and model share the 74-mode reduced model), so the truncation "
                         "shifts truth and model identically and cancels in the residual the likelihood sees.",
            "inherited_from": "statfem_shocksat_eval_20260616/out/discretization.json",
            "internally_exact_here": True},
        "modal_truncation_within_reduced": {"by_n_modes": trunc, "max_rel_err_below_74": float(max_trunc)},
        "grid_refine": {"by_nfreq": grid, "max_qoi_rel_shift": float(gshift),
                        "note": "QOI-value shift across the N_freq ladder grids; the ladder densifies the SAME "
                                "fixed truth, so these are the resolution levels the collapse sweep walks."},
    }
    json.dump(out, open(WS / "out" / "discretization.json", "w"), indent=1)
    print(f"reduced_vs_full (inherited) max_rel_err_at_peaks = {inh:.4f}")
    print(f"modal-truncation max rel err below 74 modes = {max_trunc:.4f}")
    print(f"grid-density max QOI rel shift (80->640) = {gshift:.4f}")


if __name__ == "__main__":
    main()
