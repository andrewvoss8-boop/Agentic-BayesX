#!/usr/bin/env python3
"""STAGE-3 grid-invariance / over-counting companion trust study.

Refit (with-d) at 1x and 2x base frequency-grid density (reduced draws) and compare the k_pop posterior
sd and sigma_e. If posterior sd keeps shrinking ~1/sqrt(N_f) with grid density -> correlated model error
is being over-counted as independent (fictitious tightness). If it PLATEAUS -> honest. Reads nothing from
the main run; self-contained quick refits. Writes report/blind3_gridinv.json.
"""
from __future__ import annotations
import json
from pathlib import Path
import numpy as np
import jax, jax.numpy as jnp
jax.config.update("jax_enable_x64", True)
import numpyro
import blind3_model as bm
import blind3_infer as bi

REP = Path(__file__).resolve().parents[1] / "report"


def fit_at(n_base, per_peak, draws=200, warmup=250, seed=99):
    obs = bm.load_observations()
    M_src6, m_dome, lf = bm.source_rigid_from_asymptote(obs)
    grid = bi.build_grid(obs, n_base=n_base, per_peak=per_peak)
    grid_j = jnp.asarray(grid)
    re_obs, im_obs, scale = bi.assemble_data(obs, grid)
    L = np.linalg.cholesky(bm.feature_corr() + 1e-9 * np.eye(6))
    fmask = np.ones(len(grid), bool)
    train = [0, 1, 2, 3, 4, 5]
    iv = dict(log_k_pop=np.log(bi.K_NOM), f_dome=93.5, sigma_build=0.04, sigma_e=1.0,
              sigma_d=0.15, d_raw=np.zeros(6), z_b=np.zeros(len(train)))
    model = bi.make_model(grid_j, M_src6, m_dome, L, re_obs, im_obs, scale, train, fmask, learn_d=True)
    mcmc = bi.run_nuts(model, draws, warmup, chains=4, seed=seed, init_vals=iv)
    s = {k: np.asarray(v) for k, v in mcmc.get_samples().items()}
    _, ds = bi.diagnostics(mcmc)
    return dict(n_grid=len(grid), sd_log_k=float(np.std(s["log_k_pop"])),
                k_pop_med=float(np.median(np.exp(s["log_k_pop"]))),
                sigma_e_med=float(np.median(s["sigma_e"])),
                sigma_d_med=float(np.median(s["sigma_d"])), worst_rhat=ds["worst_rhat"])


def main():
    numpyro.set_host_device_count(4)
    r1 = fit_at(36, 7, seed=99)
    r2 = fit_at(72, 11, seed=100)
    ratio_sd = r2["sd_log_k"] / max(r1["sd_log_k"], 1e-12)
    ngrid_ratio = r2["n_grid"] / r1["n_grid"]
    expected_if_independent = 1.0 / np.sqrt(ngrid_ratio)
    out = dict(grid_1x=r1, grid_2x=r2, n_grid_ratio=ngrid_ratio,
               sd_ratio_2x_over_1x=ratio_sd, expected_ratio_if_independent=float(expected_if_independent),
               interpretation=("sd shrinks ~1/sqrt(N_f) => OVER-COUNTING correlated model error as "
                               "independent (fictitious tightness)" if ratio_sd < 0.85 * expected_if_independent + 0.15
                               else "sd ~ plateaus => not dominated by frequency over-counting"))
    (REP / "blind3_gridinv.json").write_text(json.dumps(out, indent=2))
    print(json.dumps(out, indent=2))


if __name__ == "__main__":
    main()
