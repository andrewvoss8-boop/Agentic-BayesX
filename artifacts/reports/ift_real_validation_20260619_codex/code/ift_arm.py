#!/usr/bin/env python3
"""IFT physics-in-prior arm for the real ShockSat held-out-sensor QOI comparison.

This file is NEW for `ift_real_validation_20260619_codex`. It imports the copied
StatFEM real-data helpers (`realfrf.py`, `core.py`, `score.py`) and does not edit
the baseline workspace.

Headline model:
    u(omega) prior proportional to exp(-beta/2 ||Z(theta, omega) u - f||^2)
    Z(theta, omega) = (1+i eta) K(theta) - omega^2 I

The exact Gaussian field marginal is analytic for linear observations of u. The
inherited apples-to-apples observable is log|H|, so this implementation uses the
first-order log-magnitude moment approximation documented in method_ift.md.
"""
from __future__ import annotations

import argparse
import json
import math
import os
import time
from pathlib import Path

os.environ.setdefault("JAX_ENABLE_X64", "1")
os.environ.setdefault("OMP_NUM_THREADS", "1")
os.environ.setdefault("VECLIB_MAXIMUM_THREADS", "1")

import jax
import jax.numpy as jnp
import numpy as np
import numpyro
import numpyro.distributions as dist
from numpyro.diagnostics import summary as nuts_summary
from numpyro.infer import MCMC, NUTS, init_to_median

import realfrf as rf
import score as SC

jax.config.update("jax_enable_x64", True)
numpyro.set_host_device_count(4)

WS = Path(__file__).resolve().parent.parent
OUT = WS / "out"

SIGMA_MEAS = 0.15
NSIG_THETA = 0.25
GAIN_C0 = 5.6
GAIN_SD = 1.5
BETA_LOG_CENTER = math.log(1e3)
BETA_LOGSD = 2.0
LOGVAR_CAP = 25.0
LOGMAG_FLOOR2 = 1e-24
DR_MIN = 30.0
IDENT4 = [2, 4, 6, 8]  # bottom_box, cross_beam, plates, top_box
IDENT4_NAMES = [rf.GNAMES[i] for i in IDENT4]


def _dist(vals):
    v = np.asarray(vals, float)
    return {
        "mean": float(np.mean(v)),
        "med": float(np.median(v)),
        "p5": float(np.percentile(v, 5)),
        "p95": float(np.percentile(v, 95)),
        "min": float(np.min(v)),
        "max": float(np.max(v)),
    }


def _aggregate(scores):
    if not scores:
        return {}
    out = {
        "interval_score_mean": float(np.mean([s["interval_score"] for s in scores])),
        "crps_mean": float(np.mean([s["crps"] for s in scores])),
        "logpd_mean": float(np.mean([s["logpd"] for s in scores])),
        "coverage_frac": float(np.mean([s["covered"] for s in scores])),
        "mean_width_db": float(np.mean([s["width_db"] for s in scores])),
        "n_channels": int(len(scores)),
    }
    out.update(SC.aggregate_pit_z([s["pit"] for s in scores], [s["z"] for s in scores]))
    return out


def load_split(seed=0, obs_frac=0.6):
    """Copied L5 split protocol: dynamic-range eligible channels, seeded permutation."""
    R = rf.load_reduced()
    meas = rf.reprocess_measured(list(range(1, rf.N_ACCEL_RECORDERS + 1)))
    ch = rf.build_channels(R, meas["daq"])
    fr = meas["freqs"]
    fb = (fr >= rf.BAND[0]) & (fr <= rf.BAND[1])
    freqs = fr[fb]
    didx = {d: i for i, d in enumerate(meas["daq"])}
    dr = np.array([meas["dyn_range"][didx[d]] for d in ch.daq])
    elig = np.where(dr >= DR_MIN)[0]
    rng = np.random.default_rng(seed)
    perm = rng.permutation(elig)
    n_obs = int(round(obs_frac * len(perm)))
    obs_pos = np.sort(perm[:n_obs])
    ho_pos = np.sort(perm[n_obs:])
    obs_daqs = [int(ch.daq[p]) for p in obs_pos]
    ho_daqs = [int(ch.daq[p]) for p in ho_pos]
    y_obs = np.log(np.abs(np.array([meas["H"][didx[d]][fb] for d in obs_daqs])) + 1e-300).T
    y_ho = np.log(np.abs(np.array([meas["H"][didx[d]][fb] for d in ho_daqs])) + 1e-300).T
    return {
        "R": R,
        "meas": meas,
        "ch": ch,
        "freqs": freqs,
        "obs_pos": obs_pos,
        "ho_pos": ho_pos,
        "obs_daqs": obs_daqs,
        "ho_daqs": ho_daqs,
        "obs_rows": ch.rows[obs_pos],
        "ho_rows": ch.rows[ho_pos],
        "drive_row": ch.drive_row,
        "y_obs": y_obs,
        "y_ho": y_ho,
        "n_eligible": int(len(elig)),
        "dyn_range_eligible": [float(dr[p]) for p in elig],
    }


def _ift_moments_jax_factory(R, freqs, resp_rows, drive_row, fg=IDENT4):
    """Return (theta_free, log_beta, gain_c) -> (mean_logmag, var_logmag)."""
    A = jnp.asarray(R.A)
    A_fix = jnp.asarray(R.A_fix)
    rows = jnp.asarray(resp_rows)
    drive = jnp.asarray(drive_row)
    omega = jnp.asarray(2.0 * np.pi * np.asarray(freqs))
    fg_arr = jnp.asarray(np.asarray(fg, int))
    eta = 2.0 * float(rf.ZETA_NOM)
    log_g = float(np.log(rf.G_IN_S2))

    def moments(log_theta_free, log_beta, gain_c):
        theta = jnp.ones(9).at[fg_arr].set(jnp.exp(log_theta_free))
        beta = jnp.exp(log_beta)
        K = A_fix + jnp.einsum("g,gij->ij", theta, A)
        lam, Q = jnp.linalg.eigh(K)
        lam = jnp.clip(lam, 1e-9, None)
        Us = rows @ Q
        Ud = drive @ Q
        den = (1.0 + 1j * eta) * lam[None, :] - (omega ** 2)[:, None]
        H = -(omega ** 2)[:, None] * jnp.einsum(
            "sk,k,fk->fs", Us.astype(jnp.complex128), Ud.astype(jnp.complex128), 1.0 / den
        )
        H = H / rf.G_IN_S2
        abs2 = jnp.maximum(jnp.abs(H) ** 2, LOGMAG_FLOOR2)
        inv_abs_den2 = 1.0 / jnp.maximum(jnp.abs(den) ** 2, 1e-300)
        var_h = ((omega ** 4)[:, None] / (rf.G_IN_S2 ** 2)) * jnp.einsum(
            "sk,fk->fs", Us * Us, inv_abs_den2
        )
        var_log = 0.5 * var_h / (beta * abs2)
        var_log = jnp.minimum(var_log, LOGVAR_CAP)
        return jnp.log(jnp.sqrt(abs2)) + gain_c, var_log

    return moments


def _ift_moments_np(R, freqs, resp_rows, drive_row, theta, beta, gain_c):
    K = R.A_fix + np.einsum("g,gij->ij", np.asarray(theta), R.A)
    lam, Q = np.linalg.eigh(K)
    lam = np.clip(lam, 1e-9, None)
    Us = np.asarray(resp_rows) @ Q
    Ud = np.asarray(drive_row) @ Q
    w = 2.0 * np.pi * np.asarray(freqs)
    eta = 2.0 * float(rf.ZETA_NOM)
    den = (1.0 + 1j * eta) * lam[None, :] - (w ** 2)[:, None]
    H = -(w ** 2)[:, None] * np.einsum("sk,k,fk->fs", Us.astype(complex), Ud.astype(complex), 1.0 / den)
    H = H / rf.G_IN_S2
    abs2 = np.maximum(np.abs(H) ** 2, LOGMAG_FLOOR2)
    var_h = ((w ** 4)[:, None] / (rf.G_IN_S2 ** 2)) * np.einsum(
        "sk,fk->fs", Us ** 2, 1.0 / np.maximum(np.abs(den) ** 2, 1e-300)
    )
    var_log = np.minimum(0.5 * var_h / (float(beta) * abs2), LOGVAR_CAP)
    return np.log(np.sqrt(abs2)) + float(gain_c), var_log


def run_split(
    seed=0,
    obs_frac=0.6,
    warmup=600,
    samples=600,
    chains=4,
    pred_draws=300,
    beta_logsd=BETA_LOGSD,
    beta_log_center=BETA_LOG_CENTER,
    max_tree_depth=8,
    force=False,
    tag="headline",
):
    OUT.mkdir(exist_ok=True)
    outp = OUT / f"ift_split_{seed}_{tag}.json"
    samplep = OUT / f"ift_split_{seed}_{tag}_samples.npz"
    if outp.exists() and samplep.exists() and not force:
        print(f"[skip] {outp.name}")
        return json.loads(outp.read_text())

    t0 = time.time()
    split = load_split(seed=seed, obs_frac=obs_frac)
    R = split["R"]
    y_obs = jnp.asarray(split["y_obs"])
    moments = _ift_moments_jax_factory(R, split["freqs"], split["obs_rows"], split["drive_row"])

    def model():
        log_theta = numpyro.sample("log_theta", dist.Normal(0.0, NSIG_THETA).expand([len(IDENT4)]).to_event(1))
        log_beta = numpyro.sample("log_beta", dist.Normal(beta_log_center, beta_logsd))
        beta = numpyro.deterministic("beta", jnp.exp(log_beta))
        gain_c = numpyro.sample("gain_c", dist.Normal(GAIN_C0, GAIN_SD))
        mu, var_log = moments(log_theta, log_beta, gain_c)
        var = SIGMA_MEAS ** 2 + var_log
        numpyro.factor(
            "logmag_likelihood",
            -0.5 * jnp.sum((y_obs - mu) ** 2 / var + jnp.log(2.0 * jnp.pi * var)),
        )

    kernel = NUTS(
        model,
        target_accept_prob=0.9,
        init_strategy=init_to_median,
        dense_mass=True,
        max_tree_depth=max_tree_depth,
    )
    mcmc = MCMC(
        kernel,
        num_warmup=warmup,
        num_samples=samples,
        num_chains=chains,
        chain_method="sequential",
        progress_bar=False,
    )
    mcmc.run(jax.random.PRNGKey(20260619 + seed), extra_fields=("diverging",))
    grouped = mcmc.get_samples(group_by_chain=True)
    flat = {k: np.asarray(v).reshape((-1,) + tuple(v.shape[2:])) for k, v in grouped.items()}
    stats = nuts_summary(grouped, group_by_chain=True)
    max_rhat = max(float(np.nanmax(v["r_hat"])) for v in stats.values())
    min_ess = min(float(np.nanmin(v["n_eff"])) for v in stats.values())
    div = int(np.asarray(mcmc.get_extra_fields()["diverging"]).sum())
    div_frac = div / (chains * samples)
    converged = bool(max_rhat <= 1.05 and min_ess >= 200 and div_frac < 0.02)

    theta = np.ones((flat["log_theta"].shape[0], 9))
    theta[:, IDENT4] = np.exp(flat["log_theta"])
    beta = np.asarray(flat["beta"])
    gain = np.asarray(flat["gain_c"])
    np.savez_compressed(samplep, log_theta=flat["log_theta"], theta=theta, beta=beta, gain_c=gain)

    pred = score_heldout(split, theta, beta, gain, pred_draws=pred_draws, seed=seed)
    beta_log = np.log(beta)
    beta_ci = np.percentile(beta_log, [2.5, 50, 97.5])
    prior_95_width = 2.0 * 1.96 * beta_logsd
    beta_width = float(beta_ci[2] - beta_ci[0])
    weak_beta = bool(beta_width > 0.5 * prior_95_width)

    rec = {
        "arm": "IFT_logmag_moment",
        "split_seed": int(seed),
        "obs_frac": float(obs_frac),
        "n_channels_eligible": split["n_eligible"],
        "n_observed": int(len(split["obs_daqs"])),
        "n_heldout": int(len(split["ho_daqs"])),
        "n_band_freqs": int(len(split["freqs"])),
        "observed_daqs": split["obs_daqs"],
        "heldout_daqs": split["ho_daqs"],
        "free_groups": IDENT4_NAMES,
        "sampler": {
            "name": "NUTS",
            "warmup": warmup,
            "samples": samples,
            "chains": chains,
            "max_tree_depth": max_tree_depth,
        },
        "diagnostic_budget": bool(warmup < 600 or samples < 600 or max_tree_depth < 8),
        "diag": {
            "max_rhat": max_rhat,
            "min_ess": min_ess,
            "divergences": div,
            "div_frac": div_frac,
            "n_chains": chains,
            "draws": int(chains * samples),
        },
        "converged": converged,
        "beta": {
            "prior_log_center": float(beta_log_center),
            "prior_logsd": float(beta_logsd),
            "log_med": float(beta_ci[1]),
            "log_lo": float(beta_ci[0]),
            "log_hi": float(beta_ci[2]),
            "log_ci_width": beta_width,
            "med": float(np.exp(beta_ci[1])),
            "lo": float(np.exp(beta_ci[0])),
            "hi": float(np.exp(beta_ci[2])),
            "weakly_identified": weak_beta,
        },
        "gain_c": {
            "med": float(np.median(gain)),
            "lo": float(np.percentile(gain, 2.5)),
            "hi": float(np.percentile(gain, 97.5)),
        },
        "theta_post": {
            rf.GNAMES[g]: {
                "med": float(np.median(theta[:, g])),
                "lo": float(np.percentile(theta[:, g], 2.5)),
                "hi": float(np.percentile(theta[:, g], 97.5)),
            }
            for g in IDENT4
        },
        "scores": pred["scores"],
        "per_channel": pred["per_channel"],
        "method_warnings": [
            "YELLOW: log-magnitude likelihood uses a first-order moment approximation; exact Gaussian marginal applies to linear complex observations, not log(abs(.))).",
            "YELLOW: one hit and one impact location; split axis only.",
        ],
        "runtime_s": float(time.time() - t0),
    }
    outp.write_text(json.dumps(rec, indent=2))
    print(
        f"IFT split {seed}: conv={converged} R-hat {max_rhat:.3f} ESS {min_ess:.0f} "
        f"div {div_frac:.3f} beta_med {rec['beta']['med']:.3g} "
        f"peak IS {rec['scores']['peak']['interval_score_mean']:.3g}",
        flush=True,
    )
    return rec


def score_heldout(split, theta, beta, gain, pred_draws=300, seed=0):
    rng = np.random.default_rng(9000 + seed)
    n_total = theta.shape[0]
    sub = np.linspace(0, n_total - 1, min(n_total, pred_draws)).astype(int)
    freqs = split["freqs"]
    y_ho = split["y_ho"]
    n_ho = y_ho.shape[1]
    peak = np.zeros((len(sub), n_ho))
    band = np.zeros((len(sub), n_ho))
    for j, s in enumerate(sub):
        mu, var_log = _ift_moments_np(
            split["R"], freqs, split["ho_rows"], split["drive_row"], theta[s], beta[s], gain[s]
        )
        # Predict the measured held-out log magnitude under the same approximation used in the likelihood.
        log_curve = mu + rng.normal(0.0, np.sqrt(var_log + SIGMA_MEAS ** 2))
        mag = np.exp(log_curve)
        for k in range(n_ho):
            peak[j, k] = rf.core.qoi_peak(mag[:, k])
            band[j, k] = rf.core.qoi_band(mag[:, k], freqs)

    truth_mag = np.exp(y_ho)
    truth_peak = np.array([rf.core.qoi_peak(truth_mag[:, k]) for k in range(n_ho)])
    truth_band = np.array([rf.core.qoi_band(truth_mag[:, k], freqs) for k in range(n_ho)])
    peak_scores = []
    band_scores = []
    per_channel = {}
    for k, daq in enumerate(split["ho_daqs"]):
        sp = SC.score_qoi(peak[:, k], truth_peak[k])
        sb = SC.score_qoi(band[:, k], truth_band[k])
        peak_scores.append(sp)
        band_scores.append(sb)
        per_channel[str(int(daq))] = {
            "peak_truth": float(truth_peak[k]),
            "peak_med": float(np.median(peak[:, k])),
            "peak_covered": bool(sp["covered"]),
            "peak_interval_score": float(sp["interval_score"]),
            "band_truth": float(truth_band[k]),
            "band_med": float(np.median(band[:, k])),
            "band_covered": bool(sb["covered"]),
            "band_interval_score": float(sb["interval_score"]),
        }
    return {"scores": {"peak": _aggregate(peak_scores), "band": _aggregate(band_scores)}, "per_channel": per_channel}


def run_mc(
    n_splits=25,
    obs_frac=0.6,
    warmup=600,
    samples=600,
    chains=4,
    pred_draws=300,
    max_tree_depth=8,
    force=False,
    tag="headline",
):
    OUT.mkdir(exist_ok=True)
    outp = OUT / f"ift_mc_{tag}.json"
    if outp.exists() and not force:
        print(f"[skip] {outp.name}")
        return json.loads(outp.read_text())
    t0 = time.time()
    rows = []
    collect = {q: {m: [] for m in ("coverage", "interval", "crps", "logpd", "zstd")} for q in ("peak", "band")}
    for seed in range(n_splits):
        rec = run_split(
            seed=seed,
            obs_frac=obs_frac,
            warmup=warmup,
            samples=samples,
            chains=chains,
            pred_draws=pred_draws,
            max_tree_depth=max_tree_depth,
            force=force,
            tag=tag,
        )
        row = {
            "seed": seed,
            "converged": bool(rec["converged"]),
            "max_rhat": rec["diag"]["max_rhat"],
            "min_ess": rec["diag"]["min_ess"],
            "div_frac": rec["diag"]["div_frac"],
            "beta_med": rec["beta"]["med"],
            "beta_weakly_identified": rec["beta"]["weakly_identified"],
        }
        for q in ("peak", "band"):
            s = rec["scores"][q]
            collect[q]["coverage"].append(s["coverage_frac"])
            collect[q]["interval"].append(s["interval_score_mean"])
            collect[q]["crps"].append(s["crps_mean"])
            collect[q]["logpd"].append(s["logpd_mean"])
            collect[q]["zstd"].append(s["z_std"])
            row[f"{q}_coverage"] = s["coverage_frac"]
            row[f"{q}_interval"] = s["interval_score_mean"]
            row[f"{q}_crps"] = s["crps_mean"]
            row[f"{q}_logpd"] = s["logpd_mean"]
            row[f"{q}_zstd"] = s["z_std"]
        rows.append(row)

    summary = {
        q: {m: _dist(collect[q][m]) for m in ("coverage", "interval", "crps", "logpd", "zstd")}
        for q in ("peak", "band")
    }
    rec_out = {
        "study": "ift_real_validation_20260619_codex",
        "arm": "IFT_logmag_moment",
        "n_splits": int(n_splits),
        "obs_frac": float(obs_frac),
        "split_axis": "channel split only; one hit and one impact location",
        "sampler": {
            "name": "NUTS",
            "warmup": warmup,
            "samples": samples,
            "chains": chains,
            "max_tree_depth": max_tree_depth,
        },
        "diagnostic_budget": bool(warmup < 600 or samples < 600 or max_tree_depth < 8),
        "converged_frac": float(np.mean([r["converged"] for r in rows])),
        "beta_weak_frac": float(np.mean([r["beta_weakly_identified"] for r in rows])),
        "summary": summary,
        "per_split": rows,
        "runtime_s": float(time.time() - t0),
    }
    outp.write_text(json.dumps(rec_out, indent=2))
    print(
        f"IFT MC {n_splits} splits: conv_frac {rec_out['converged_frac']:.2f}, "
        f"peak interval med {summary['peak']['interval']['med']:.3g}"
    )
    return rec_out


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--split", type=int, default=None)
    p.add_argument("--n-splits", type=int, default=25)
    p.add_argument("--obs-frac", type=float, default=0.6)
    p.add_argument("--warmup", type=int, default=600)
    p.add_argument("--samples", type=int, default=600)
    p.add_argument("--chains", type=int, default=4)
    p.add_argument("--pred-draws", type=int, default=300)
    p.add_argument("--max-tree-depth", type=int, default=8)
    p.add_argument("--tag", default="headline")
    p.add_argument("--force", action="store_true")
    args = p.parse_args()
    if args.split is not None:
        run_split(
            seed=args.split,
            obs_frac=args.obs_frac,
            warmup=args.warmup,
            samples=args.samples,
            chains=args.chains,
            pred_draws=args.pred_draws,
            max_tree_depth=args.max_tree_depth,
            force=args.force,
            tag=args.tag,
        )
    else:
        run_mc(
            n_splits=args.n_splits,
            obs_frac=args.obs_frac,
            warmup=args.warmup,
            samples=args.samples,
            chains=args.chains,
            pred_draws=args.pred_draws,
            max_tree_depth=args.max_tree_depth,
            force=args.force,
            tag=args.tag,
        )


if __name__ == "__main__":
    main()
