"""Full-MCMC style posterior sampling for 2DOF StatFEM-inspired setup."""

from __future__ import annotations

import json
import math
from dataclasses import dataclass
from pathlib import Path

import numpy as np

from src.twodof.model import (
    TwoDofParams,
    apparent_mass_dome_uncoupled,
    apparent_mass_from_drivepoint,
    power_law_force_spectrum,
    tray_accel_from_m1_force,
    tray_base_to_tray_accel_transfer,
)


@dataclass(frozen=True)
class InferenceConfig:
    n_steps: int = 2200
    burn_in: int = 1000
    thin: int = 5
    proposal_scale: float = 0.02
    seed: int = 7
    adapt_proposal: bool = True
    adapt_interval: int = 50
    target_acceptance: float = 0.25
    adapt_gain: float = 1.5
    proposal_block_size: int = 1


def _log_frequency_coordinate(freqs_hz: np.ndarray) -> np.ndarray:
    if np.any(freqs_hz <= 0.0):
        raise ValueError("log-frequency GP requires positive frequencies")
    return np.log(freqs_hz)


def _sqexp_cov(freqs_hz: np.ndarray, sigma_d: float, ell_logfreq: float) -> np.ndarray:
    eta = _log_frequency_coordinate(freqs_hz)
    d = np.subtract.outer(eta, eta)
    return sigma_d**2 * np.exp(-0.5 * (d / ell_logfreq) ** 2) + 1e-8 * np.eye(len(freqs_hz))


def _predict_channels(freqs_hz: np.ndarray, theta: np.ndarray, m1: float = 1.0, m2: float = 0.6) -> dict[str, np.ndarray]:
    # Parameterization in log-space for positive parameters.
    # [k1,k2,c1,c2,force_amp,force_fc,sigma_d,ell_d_logfreq,sigma_n]
    # Coupling uses the tray fixed-base properties: k12 = k2 and c12 = c2.
    vals = np.exp(theta)
    p = TwoDofParams(m1=m1, m2=m2, k1=vals[0], k2=vals[1], k12=vals[1], c1=vals[2], c2=vals[3], c12=vals[3])
    force = power_law_force_spectrum(freqs_hz, amp=vals[4], fc=vals[5])
    return {
        "dome_drive_apparent_mass_modal": apparent_mass_dome_uncoupled(freqs_hz, p.m1, p.k1, p.c1),
        "coupled_interface_apparent_mass_modal": apparent_mass_from_drivepoint(p, freqs_hz, dof=0),
        "coupled_tray_impact_apparent_mass_test": apparent_mass_from_drivepoint(p, freqs_hz, dof=1),
        "tray_standalone_accel_over_base": tray_base_to_tray_accel_transfer(freqs_hz, p),
        "flight_tray_accel_from_unknown_m1_force": tray_accel_from_m1_force(p, freqs_hz, force),
    }


def _log_prior(theta: np.ndarray, prior_mean: np.ndarray, prior_std: np.ndarray) -> float:
    z = (theta - prior_mean) / prior_std
    return -0.5 * float(np.dot(z, z))


def _log_likelihood(
    freqs_hz: np.ndarray,
    obs: dict[str, np.ndarray],
    theta: np.ndarray,
    cov_cache: dict[tuple[float, float, float], tuple[np.ndarray, float]] | None = None,
) -> float:
    pred = _predict_channels(freqs_hz, theta)
    sigma_d = float(np.exp(theta[6]))
    ell_d_logfreq = float(np.exp(theta[7]))
    sigma_n = float(np.exp(theta[8]))

    n = len(freqs_hz)
    cov_key = (float(theta[6]), float(theta[7]), float(theta[8]))
    cached = cov_cache.get(cov_key) if cov_cache is not None else None
    if cached is None:
        kd = _sqexp_cov(freqs_hz, sigma_d=sigma_d, ell_logfreq=ell_d_logfreq)
        cov = kd + (sigma_n**2) * np.eye(n)
        try:
            chol = np.linalg.cholesky(cov)
        except np.linalg.LinAlgError:
            return -np.inf
        whiten = np.linalg.inv(chol)
        logdet_cov = 2.0 * float(np.sum(np.log(np.diag(chol))))
        if cov_cache is not None:
            if len(cov_cache) >= 64:
                cov_cache.clear()
            cov_cache[cov_key] = (whiten, logdet_cov)
    else:
        whiten, logdet_cov = cached

    residual_parts = []
    for k, y in obs.items():
        r = y - pred[k]
        residual_parts.extend([r.real, r.imag])

    residual_matrix = np.column_stack(residual_parts)
    solved = whiten @ residual_matrix
    quad = float(np.sum(solved * solved))
    n_observed_parts = residual_matrix.shape[1]
    ll = -0.5 * (
        quad
        + n_observed_parts * logdet_cov
        + n * n_observed_parts * math.log(2.0 * math.pi)
    )
    return float(ll)


def _validate_config(config: InferenceConfig) -> None:
    if config.n_steps <= 0:
        raise ValueError("n_steps must be positive")
    if config.burn_in < 0 or config.burn_in >= config.n_steps:
        raise ValueError("burn_in must be nonnegative and less than n_steps")
    if config.thin <= 0:
        raise ValueError("thin must be positive")
    if config.proposal_scale <= 0:
        raise ValueError("proposal_scale must be positive")
    if config.adapt_interval <= 0:
        raise ValueError("adapt_interval must be positive")
    if not 0.0 < config.target_acceptance < 1.0:
        raise ValueError("target_acceptance must be between 0 and 1")
    if config.proposal_block_size <= 0:
        raise ValueError("proposal_block_size must be positive")


def _qoi_peak_samples(freqs: np.ndarray, samples_physical: np.ndarray, m1: float, m2: float) -> np.ndarray:
    qoi = np.zeros(len(samples_physical), dtype=float)
    for i, vals in enumerate(samples_physical):
        p = TwoDofParams(
            m1=m1,
            m2=m2,
            k1=vals[0],
            k2=vals[1],
            k12=vals[1],
            c1=vals[2],
            c2=vals[3],
            c12=vals[3],
        )
        force = power_law_force_spectrum(freqs, amp=vals[4], fc=vals[5])
        tray = tray_accel_from_m1_force(p, freqs, force)
        qoi[i] = float(np.max(np.abs(tray)))
    return qoi


def run_mcmc(dataset: dict, config: InferenceConfig = InferenceConfig()) -> dict:
    _validate_config(config)
    freqs = np.asarray(dataset["freqs_hz"], dtype=float)
    obs = {k: np.asarray(v, dtype=np.complex128) for k, v in dataset["channels_obs"].items()}
    truth = dataset["truth"]

    theta0 = np.log(
        np.array(
            [
                truth["params"]["k1"] * 0.9,
                truth["params"]["k2"] * 1.1,
                truth["params"]["c1"] * 0.8,
                truth["params"]["c2"] * 1.2,
                truth["force_amp"] * 1.1,
                truth["force_fc"] * 0.9,
                0.03,
                0.08,
                0.02,
            ],
            dtype=float,
        )
    )
    prior_mean = theta0.copy()
    prior_std = np.array([0.6] * 6 + [0.8, 0.8, 0.8], dtype=float)
    prop_std = np.array([config.proposal_scale] * len(theta0), dtype=float)
    rng = np.random.default_rng(config.seed)

    samples = np.zeros((config.n_steps, len(theta0)), dtype=float)
    logps = np.zeros(config.n_steps, dtype=float)
    adaptation_history: list[dict[str, float]] = []
    cov_cache: dict[tuple[float, float, float], tuple[np.ndarray, float]] = {}

    cur = theta0.copy()
    cur_lp = _log_prior(cur, prior_mean, prior_std) + _log_likelihood(freqs, obs, cur, cov_cache)
    accept = 0
    post_burn_accept = 0
    post_burn_steps = 0
    window_accept = 0
    for i in range(config.n_steps):
        block_size = min(config.proposal_block_size, len(cur))
        block = rng.choice(len(cur), size=block_size, replace=False)
        prop = cur.copy()
        prop[block] += rng.normal(0.0, prop_std[block], size=block_size)
        prop_lp = _log_prior(prop, prior_mean, prior_std) + _log_likelihood(freqs, obs, prop, cov_cache)
        accepted = math.log(rng.uniform()) < (prop_lp - cur_lp)
        if accepted:
            cur = prop
            cur_lp = prop_lp
            accept += 1
            window_accept += 1
            if i >= config.burn_in:
                post_burn_accept += 1
        if i >= config.burn_in:
            post_burn_steps += 1
        samples[i] = cur
        logps[i] = cur_lp

        in_adaptive_burn_in = config.adapt_proposal and (i + 1) <= config.burn_in
        at_adapt_step = (i + 1) % config.adapt_interval == 0
        if in_adaptive_burn_in and at_adapt_step:
            window_rate = window_accept / config.adapt_interval
            adapt_count = len(adaptation_history) + 1
            gain = config.adapt_gain / math.sqrt(adapt_count)
            prop_std *= math.exp(gain * (window_rate - config.target_acceptance))
            adaptation_history.append(
                {
                    "step": float(i + 1),
                    "window_acceptance_rate": float(window_rate),
                    "proposal_scale": float(prop_std[0]),
                }
            )
            window_accept = 0

    kept = samples[config.burn_in :: config.thin]
    params_samples = np.exp(kept)
    mean_params = params_samples.mean(axis=0)
    std_params = params_samples.std(axis=0, ddof=1) if len(params_samples) > 1 else np.zeros_like(mean_params)
    ci_low, ci_high = np.quantile(params_samples, [0.025, 0.975], axis=0)
    qoi_samples = _qoi_peak_samples(
        freqs,
        params_samples,
        m1=truth["params"]["m1"],
        m2=truth["params"]["m2"],
    )
    qoi_ci_low, qoi_ci_high = np.quantile(qoi_samples, [0.025, 0.975])

    p_mean = TwoDofParams(
        m1=truth["params"]["m1"],
        m2=truth["params"]["m2"],
        k1=mean_params[0],
        k2=mean_params[1],
        k12=mean_params[1],
        c1=mean_params[2],
        c2=mean_params[3],
        c12=mean_params[3],
    )
    force_mean = power_law_force_spectrum(freqs, amp=mean_params[4], fc=mean_params[5])
    tray = tray_accel_from_m1_force(p_mean, freqs, force_mean)
    qoi_peak_at_mean_params = float(np.max(np.abs(tray)))
    qoi_peak = float(np.mean(qoi_samples))

    names = ["k1", "k2", "c1", "c2", "force_amp", "force_fc", "sigma_d", "ell_d_logfreq", "sigma_n"]
    std_by_name = {name: float(value) for name, value in zip(names, std_params)}
    std_by_name["k12"] = std_by_name["k2"]
    std_by_name["c12"] = std_by_name["c2"]
    ci_by_name = {
        name: [float(lo), float(hi)]
        for name, lo, hi in zip(names, ci_low, ci_high)
    }
    ci_by_name["k12"] = ci_by_name["k2"]
    ci_by_name["c12"] = ci_by_name["c2"]

    return {
        "acceptance_rate": accept / config.n_steps,
        "post_burn_acceptance_rate": post_burn_accept / max(post_burn_steps, 1),
        "sampler_diagnostics": {
            "proposal_scale_initial": config.proposal_scale,
            "proposal_scale_final": float(prop_std[0]),
            "target_acceptance": config.target_acceptance,
            "proposal_block_size": min(config.proposal_block_size, len(theta0)),
            "adaptation_history": adaptation_history,
        },
        "parameterization": {
            "independent_parameters": names,
            "tied_parameters": {"k12": "k2", "c12": "c2"},
            "reason": "The tray attachment stiffness/damping is modeled with the same properties as the standalone tray fixed-base test.",
        },
        "samples_log": kept.tolist(),
        "samples_physical": params_samples.tolist(),
        "posterior_mean": {
            "k1": mean_params[0],
            "k2": mean_params[1],
            "k12": mean_params[1],
            "c1": mean_params[2],
            "c2": mean_params[3],
            "c12": mean_params[3],
            "force_amp": mean_params[4],
            "force_fc": mean_params[5],
            "sigma_d": mean_params[6],
            "ell_d_logfreq": mean_params[7],
            "sigma_n": mean_params[8],
            "qoi_peak_tray_accel": qoi_peak,
            "qoi_peak_tray_accel_at_mean_params": qoi_peak_at_mean_params,
        },
        "posterior_std": std_by_name,
        "posterior_ci_95": ci_by_name | {"qoi_peak_tray_accel": [float(qoi_ci_low), float(qoi_ci_high)]},
        "qoi_samples": {
            "peak_tray_accel": qoi_samples.tolist(),
        },
        "truth": truth,
    }


def load_dataset(path: Path) -> dict:
    raw = json.loads(path.read_text())
    channels_obs = {}
    channels_clean = {}
    for name, arr in raw["channels_obs"].items():
        channels_obs[name] = np.asarray(arr["real"]) + 1j * np.asarray(arr["imag"])
    for name, arr in raw["channels_clean"].items():
        channels_clean[name] = np.asarray(arr["real"]) + 1j * np.asarray(arr["imag"])
    return {
        "freqs_hz": np.asarray(raw["freqs_hz"], dtype=float),
        "channels_obs": channels_obs,
        "channels_clean": channels_clean,
        "channel_metadata": raw.get("channel_metadata", {}),
        "truth": raw["truth"],
    }


if __name__ == "__main__":
    root = Path(__file__).resolve().parents[2]
    data = load_dataset(root / "artifacts" / "synthetic" / "twodof_dataset.json")
    out = run_mcmc(data)
    out_path = root / "artifacts" / "inference" / "twodof_mcmc_result.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(out, indent=2))
