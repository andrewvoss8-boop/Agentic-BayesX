#!/usr/bin/env python3
"""Forcing-marginalized amplitude-dependent damping toy.

Synthetic truth:
  - 3 DOF primary / secondary / hidden-rattler system.
  - Hidden complex forcing spectrum.
  - Hidden amplitude-dependent equivalent damping and stiffness softening.

Digital twin:
  - 2 DOF primary / secondary system.
  - No force function in the likelihood.
  - One equivalent joint damping ratio per amplitude condition.

Observation:
  T21 = a_secondary / a_primary. For one input force, the force cancels.
"""
from __future__ import annotations

import json
import math
import os
import time
from pathlib import Path

import jax
import jax.numpy as jnp
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import numpyro
import numpyro.distributions as dist
from numpyro.diagnostics import summary as nuts_summary
from numpyro.infer import MCMC, NUTS
from PIL import Image

jax.config.update("jax_enable_x64", True)
numpyro.set_host_device_count(4)

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
OUT = ROOT / "out"
FIG = ROOT / "figures"
OUT.mkdir(exist_ok=True)
FIG.mkdir(exist_ok=True)

RNG = np.random.default_rng(20260612)

# -----------------------------
# Synthetic constants and units
# -----------------------------
M1 = 1.00  # kg, primary
M2 = 0.18  # kg, secondary
M3 = 0.035  # kg, hidden rattler

F1_HZ = 55.0
F12_HZ = 96.0
F23_HZ = 142.0

K1_NOM = M1 * (2 * np.pi * F1_HZ) ** 2
K12_NOM = M2 * (2 * np.pi * F12_HZ) ** 2
K23_NOM = M3 * (2 * np.pi * F23_HZ) ** 2

ZETA_PRIMARY = 0.012
FREQS = np.geomspace(25.0, 240.0, 90)
OMEGA = 2 * np.pi * FREQS
AMP_LEVELS = np.array([0.35, 1.80])
AMP_LABELS = ["low", "high"]
TRAIN_MASK = np.ones(len(FREQS), dtype=bool)
TRAIN_MASK[::4] = False
HELDOUT_MASK = ~TRAIN_MASK
QOI_MASK = HELDOUT_MASK & (FREQS >= 45.0) & (FREQS <= 185.0)

SIG_LOGMAG = 0.035
SIG_PHASE = 0.035


def slip_activation(amp: float) -> float:
    """Hidden slip-like activation. The twin does not know this function."""
    x = amp**1.7
    return float(x / (1.0 + x))


def truth_joint_props(amp: float) -> dict[str, float]:
    """Amplitude-dependent truth joint properties hidden from the twin."""
    slip = slip_activation(amp)
    zeta12 = 0.006 + 0.060 * slip
    zeta23 = 0.018 + 0.030 * slip
    k12 = K12_NOM * (1.0 - 0.10 * slip)
    k23 = K23_NOM * (1.0 - 0.04 * slip)
    mred12 = M1 * M2 / (M1 + M2)
    mred23 = M2 * M3 / (M2 + M3)
    c12 = 2.0 * zeta12 * math.sqrt(k12 * mred12)
    c23 = 2.0 * zeta23 * math.sqrt(k23 * mred23)
    c1 = 2.0 * ZETA_PRIMARY * math.sqrt(K1_NOM * M1)
    return {
        "slip": slip,
        "zeta12": zeta12,
        "zeta23": zeta23,
        "k12": k12,
        "k23": k23,
        "c1": c1,
        "c12": c12,
        "c23": c23,
    }


def assemble_truth(amp: float) -> tuple[np.ndarray, np.ndarray, np.ndarray, dict[str, float]]:
    p = truth_joint_props(amp)
    M = np.diag([M1, M2, M3])
    K = np.zeros((3, 3))
    C = np.zeros((3, 3))

    def add_ground(mat: np.ndarray, i: int, val: float) -> None:
        mat[i, i] += val

    def add_link(mat: np.ndarray, i: int, j: int, val: float) -> None:
        mat[i, i] += val
        mat[j, j] += val
        mat[i, j] -= val
        mat[j, i] -= val

    add_ground(K, 0, K1_NOM)
    add_link(K, 0, 1, p["k12"])
    add_link(K, 1, 2, p["k23"])
    add_ground(C, 0, p["c1"])
    add_link(C, 0, 1, p["c12"])
    add_link(C, 1, 2, p["c23"])
    return M, K, C, p


def solve_truth(amp: float, freqs: np.ndarray = FREQS) -> dict[str, np.ndarray | dict[str, float]]:
    M, K, C, props = assemble_truth(amp)
    b = np.array([1.0, 0.0, 0.0], dtype=complex)
    x = np.zeros((len(freqs), 3), dtype=complex)
    t21 = np.zeros(len(freqs), dtype=complex)
    m12 = np.zeros(len(freqs), dtype=complex)
    for n, f in enumerate(freqs):
        w = 2 * np.pi * f
        D = K + 1j * w * C - (w**2) * M
        xn = np.linalg.solve(D, b)
        x[n] = xn
        a1 = -(w**2) * xn[0]
        f12 = (props["k12"] + 1j * w * props["c12"]) * (xn[1] - xn[0])
        t21[n] = xn[1] / xn[0]
        m12[n] = f12 / a1
    return {"x": x, "t21": t21, "m12": m12, "props": props}


def hidden_force(amp: float, freqs: np.ndarray = FREQS) -> np.ndarray:
    """A deliberately ugly hidden force spectrum. The twin never sees it."""
    logf = np.log(freqs)
    envelope = (
        0.5
        + 1.1 * np.exp(-0.5 * ((logf - np.log(72.0)) / 0.22) ** 2)
        + 0.7 * np.exp(-0.5 * ((logf - np.log(158.0)) / 0.18) ** 2)
        + 0.2 * np.sin(5.0 * logf) ** 2
    )
    phase = RNG.uniform(-np.pi, np.pi, len(freqs))
    return amp * envelope * np.exp(1j * phase)


def make_observations() -> dict[str, np.ndarray]:
    truth_t = []
    truth_m = []
    obs_t = []
    force = []
    forced_ratio_error = []
    truth_props = []
    for amp in AMP_LEVELS:
        sol = solve_truth(float(amp))
        t21 = np.asarray(sol["t21"])
        m12 = np.asarray(sol["m12"])
        f = hidden_force(float(amp))
        a = -(OMEGA[:, None] ** 2) * np.asarray(sol["x"]) * f[:, None]
        ratio_from_forced_responses = a[:, 1] / a[:, 0]
        forced_ratio_error.append(
            float(np.max(np.abs(ratio_from_forced_responses - t21) / (np.abs(t21) + 1e-14)))
        )
        noise = np.exp(
            RNG.normal(0.0, SIG_LOGMAG, len(FREQS))
            + 1j * RNG.normal(0.0, SIG_PHASE, len(FREQS))
        )
        truth_t.append(t21)
        truth_m.append(m12)
        obs_t.append(t21 * noise)
        force.append(f)
        truth_props.append(sol["props"])
    return {
        "truth_t21": np.asarray(truth_t),
        "truth_m12": np.asarray(truth_m),
        "obs_t21": np.asarray(obs_t),
        "force": np.asarray(force),
        "forced_ratio_error": np.asarray(forced_ratio_error),
        "truth_props": truth_props,
    }


DATA = make_observations()

# -----------------------------
# JAX twin forward model
# -----------------------------
FREQS_J = jnp.asarray(FREQS)
TRAIN_IDX_J = jnp.asarray(np.where(TRAIN_MASK)[0])
OBS_TRAIN = jnp.asarray(DATA["obs_t21"][:, TRAIN_MASK])
OBS_LOGMAG = jnp.log(jnp.abs(OBS_TRAIN))


def twin_response(freqs: jnp.ndarray, k1_scale: float, k12_scale: float, zeta12: float):
    k1 = K1_NOM * k1_scale
    k12 = K12_NOM * k12_scale
    mred12 = M1 * M2 / (M1 + M2)
    c1 = 2.0 * ZETA_PRIMARY * jnp.sqrt(k1 * M1)
    c12 = 2.0 * zeta12 * jnp.sqrt(k12 * mred12)
    M = jnp.diag(jnp.array([M1, M2]))
    K = jnp.array([[k1 + k12, -k12], [-k12, k12]])
    C = jnp.array([[c1 + c12, -c12], [-c12, c12]])
    b = jnp.array([1.0 + 0j, 0.0 + 0j])

    def one(f):
        w = 2.0 * jnp.pi * f
        D = K + 1j * w * C - (w**2) * M
        x = jnp.linalg.solve(D, b)
        a1 = -(w**2) * x[0]
        f12 = (k12 + 1j * w * c12) * (x[1] - x[0])
        return x[1] / x[0], f12 / a1

    t21, m12 = jax.vmap(one)(freqs)
    return t21, m12


def model():
    log_k1_scale = numpyro.sample("log_k1_scale", dist.Normal(0.0, 0.18))
    log_k12_scale = numpyro.sample("log_k12_scale", dist.Normal(0.0, 0.22))
    zeta_low = numpyro.sample("zeta_low", dist.LogNormal(math.log(0.018), 0.75))
    zeta_high = numpyro.sample("zeta_high", dist.LogNormal(math.log(0.030), 0.75))
    sigma_model = numpyro.sample("sigma_model", dist.HalfNormal(0.08))
    k1_scale = jnp.exp(log_k1_scale)
    k12_scale = jnp.exp(log_k12_scale)
    zetas = [zeta_low, zeta_high]
    sigma_log = jnp.sqrt(SIG_LOGMAG**2 + sigma_model**2)
    sigma_phase = jnp.sqrt(SIG_PHASE**2 + sigma_model**2)
    pred_train = []
    for i, zeta in enumerate(zetas):
        t21, _ = twin_response(FREQS_J, k1_scale, k12_scale, zeta)
        tt = t21[TRAIN_IDX_J]
        pred_train.append(tt)
        numpyro.sample(
            f"logmag_{AMP_LABELS[i]}",
            dist.Normal(jnp.log(jnp.abs(tt)), sigma_log).to_event(1),
            obs=OBS_LOGMAG[i],
        )
        phase_resid = jnp.angle(OBS_TRAIN[i] / tt)
        numpyro.factor(
            f"phase_{AMP_LABELS[i]}",
            jnp.sum(dist.Normal(0.0, sigma_phase).log_prob(phase_resid)),
        )
    numpyro.deterministic("sigma_log_total", sigma_log)


def run_nuts():
    kernel = NUTS(model, target_accept_prob=0.92, init_strategy=numpyro.infer.init_to_median)
    mcmc = MCMC(
        kernel,
        num_warmup=700,
        num_samples=700,
        num_chains=4,
        chain_method="sequential",
        progress_bar=False,
    )
    mcmc.run(jax.random.PRNGKey(20260612), extra_fields=("diverging",))
    grouped = mcmc.get_samples(group_by_chain=True)
    flat = {k: np.asarray(v).reshape((-1,) + tuple(v.shape[2:])) for k, v in grouped.items()}
    stats = nuts_summary(grouped, group_by_chain=True)
    max_rhat = max(float(np.nanmax(v["r_hat"])) for v in stats.values())
    min_ess = min(float(np.nanmin(v["n_eff"])) for v in stats.values())
    div = int(np.asarray(mcmc.get_extra_fields()["diverging"]).sum())
    return flat, {
        "max_rhat": max_rhat,
        "min_ess": min_ess,
        "divergences": div,
        "div_frac": div / (4 * 700),
    }


def twin_np(freqs: np.ndarray, k1_scale: float, k12_scale: float, zeta: float):
    k1 = K1_NOM * k1_scale
    k12 = K12_NOM * k12_scale
    mred12 = M1 * M2 / (M1 + M2)
    c1 = 2.0 * ZETA_PRIMARY * math.sqrt(k1 * M1)
    c12 = 2.0 * zeta * math.sqrt(k12 * mred12)
    M = np.diag([M1, M2])
    K = np.array([[k1 + k12, -k12], [-k12, k12]], dtype=float)
    C = np.array([[c1 + c12, -c12], [-c12, c12]], dtype=float)
    b = np.array([1.0, 0.0], dtype=complex)
    t21 = np.zeros(len(freqs), dtype=complex)
    m12 = np.zeros(len(freqs), dtype=complex)
    for n, f in enumerate(freqs):
        w = 2 * np.pi * f
        x = np.linalg.solve(K + 1j * w * C - (w**2) * M, b)
        a1 = -(w**2) * x[0]
        f12 = (k12 + 1j * w * c12) * (x[1] - x[0])
        t21[n] = x[1] / x[0]
        m12[n] = f12 / a1
    return t21, m12


def qois_from_curves(t21: np.ndarray, m12: np.ndarray) -> dict[str, float]:
    q_t = t21[QOI_MASK]
    q_m = m12[QOI_MASK]
    return {
        "peak_ratio": float(np.max(np.abs(q_t))),
        "band_rms_ratio": float(np.sqrt(np.mean(np.abs(q_t) ** 2))),
        "peak_interface_mass_kg": float(np.max(np.abs(q_m))),
    }


def interval(x: np.ndarray, probs=(2.5, 50.0, 97.5)) -> list[float]:
    return [float(v) for v in np.percentile(x, probs)]


def posterior_predictions(samples: dict[str, np.ndarray]):
    n = len(samples["zeta_low"])
    pred_t = np.zeros((n, 2, len(FREQS)), dtype=complex)
    pred_m = np.zeros((n, 2, len(FREQS)), dtype=complex)
    qoi = {label: {"peak_ratio": [], "band_rms_ratio": [], "peak_interface_mass_kg": []} for label in AMP_LABELS}
    noisy_log_heldout = []
    for s in range(n):
        k1s = float(np.exp(samples["log_k1_scale"][s]))
        k12s = float(np.exp(samples["log_k12_scale"][s]))
        zetas = [float(samples["zeta_low"][s]), float(samples["zeta_high"][s])]
        sig = float(samples["sigma_log_total"][s])
        for i, z in enumerate(zetas):
            t, m = twin_np(FREQS, k1s, k12s, z)
            pred_t[s, i] = t
            pred_m[s, i] = m
            qq = qois_from_curves(t, m)
            # Include output-space residual inflation in QOI predictive intervals.
            for name, val in qq.items():
                qoi[AMP_LABELS[i]][name].append(float(val * np.exp(RNG.normal(0.0, sig))))
            noisy_log_heldout.append(np.log(np.abs(t[HELDOUT_MASK])) + RNG.normal(0.0, sig, HELDOUT_MASK.sum()))
    return pred_t, pred_m, qoi, np.asarray(noisy_log_heldout).reshape(n, 2, HELDOUT_MASK.sum())


def make_image_qa(paths: list[Path]) -> dict:
    failures = []
    details = []
    for p in paths:
        im = Image.open(p)
        w, h = im.size
        ok = w >= 1200 and h >= 800 and p.stat().st_size > 20_000
        if not ok:
            failures.append(p.name)
        details.append({"file": p.name, "width": w, "height": h, "bytes": p.stat().st_size, "pass": ok})
    report = {"pass": not failures, "failures": failures, "n_figures": len(paths), "figures": details}
    json.dump(report, open(ROOT / "image_qa.json", "w"), indent=2)
    return report


def style_axes(ax):
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.grid(True, which="major", color="0.88", linewidth=0.7)


def make_figures(samples, pred_t, pred_m, qoi_samples, summary):
    paths: list[Path] = []
    colors = {"low": "#2b6cb0", "high": "#b83280"}

    # Figure 1: hidden force exists, but the ratio cancels it.
    fig, axs = plt.subplots(2, 1, figsize=(9.0, 7.0), sharex=True)
    for i, label in enumerate(AMP_LABELS):
        axs[0].plot(FREQS, np.abs(DATA["force"][i]), color=colors[label], lw=1.8)
        axs[0].text(FREQS[-1] * 1.01, np.abs(DATA["force"][i, -1]), f"{label} hidden force", color=colors[label], va="center", fontsize=9)
        axs[1].plot(FREQS, np.abs(DATA["truth_t21"][i]), color=colors[label], lw=2.0)
        axs[1].scatter(FREQS[TRAIN_MASK], np.abs(DATA["obs_t21"][i, TRAIN_MASK]), s=10, color=colors[label], alpha=0.35)
        axs[1].scatter(FREQS[HELDOUT_MASK], np.abs(DATA["obs_t21"][i, HELDOUT_MASK]), s=14, facecolors="none", edgecolors=colors[label], alpha=0.75)
    axs[0].set_ylabel("|F(f)| [hidden units]")
    axs[1].set_ylabel("|a2/a1| [-]")
    axs[1].set_xlabel("frequency [Hz], log scale")
    for ax in axs:
        ax.set_xscale("log")
        style_axes(ax)
    axs[0].set_title("A hidden forcing spectrum is generated but not learned")
    axs[1].set_title(f"Forcing cancellation check: max ratio error {summary['forcing_cancellation']['max_relative_error']:.1e}")
    fig.suptitle("Synthetic primary/secondary toy - response ratio integrates out forcing", fontsize=12)
    fig.tight_layout(rect=[0, 0, 1, 0.96])
    p = FIG / "fig1_forcing_cancellation.png"
    fig.savefig(p, dpi=180)
    plt.close(fig)
    paths.append(p)

    # Figure 2: posterior ratio fit with held-out points.
    fig, axs = plt.subplots(2, 1, figsize=(9.0, 7.3), sharex=True)
    for i, label in enumerate(AMP_LABELS):
        mag = np.abs(pred_t[:, i, :])
        lo, med, hi = np.percentile(mag, [2.5, 50, 97.5], axis=0)
        axs[i].fill_between(FREQS, lo, hi, color=colors[label], alpha=0.22, label="posterior 95%")
        axs[i].plot(FREQS, med, color=colors[label], lw=1.8)
        axs[i].plot(FREQS, np.abs(DATA["truth_t21"][i]), color="black", lw=1.0, alpha=0.75)
        axs[i].scatter(FREQS[TRAIN_MASK], np.abs(DATA["obs_t21"][i, TRAIN_MASK]), s=9, color="0.35", alpha=0.35)
        axs[i].scatter(FREQS[HELDOUT_MASK], np.abs(DATA["obs_t21"][i, HELDOUT_MASK]), s=17, facecolors="none", edgecolors="black", alpha=0.8)
        axs[i].set_ylabel("|a2/a1| [-]")
        axs[i].set_title(f"{label} amplitude: 2-DOF twin fit to force-normalized data")
        axs[i].set_xscale("log")
        style_axes(axs[i])
        axs[i].text(0.02, 0.92, "black = hidden 3-DOF truth; open circles = held out", transform=axs[i].transAxes, fontsize=9)
    axs[-1].set_xlabel("frequency [Hz], log scale")
    fig.tight_layout()
    p = FIG / "fig2_ratio_fit.png"
    fig.savefig(p, dpi=180)
    plt.close(fig)
    paths.append(p)

    # Figure 3: damping posterior.
    fig, ax = plt.subplots(figsize=(9.0, 5.4))
    zlow = samples["zeta_low"]
    zhigh = samples["zeta_high"]
    bins = np.linspace(0.0, max(np.percentile(zhigh, 99), np.percentile(zlow, 99), 0.09), 70)
    ax.hist(zlow, bins=bins, density=True, color=colors["low"], alpha=0.35)
    ax.hist(zhigh, bins=bins, density=True, color=colors["high"], alpha=0.35)
    low_truth = summary["truth"]["low"]["zeta12"]
    high_truth = summary["truth"]["high"]["zeta12"]
    ax.axvline(low_truth, color=colors["low"], lw=2.0)
    ax.axvline(high_truth, color=colors["high"], lw=2.0)
    ax.text(low_truth, ax.get_ylim()[1] * 0.92, "low truth", color=colors["low"], rotation=90, va="top", ha="right", fontsize=9)
    ax.text(high_truth, ax.get_ylim()[1] * 0.92, "high truth", color=colors["high"], rotation=90, va="top", ha="right", fontsize=9)
    ax.text(0.62, 0.85, f"P(high > low) = {summary['damping_learning']['prob_zeta_high_gt_low']:.3f}", transform=ax.transAxes, fontsize=11)
    ax.set_xlabel("equivalent joint damping ratio zeta [-]")
    ax.set_ylabel("posterior density")
    ax.set_title("Twin learns effective damping at the two tested amplitudes, not the hidden slip law")
    style_axes(ax)
    fig.tight_layout()
    p = FIG / "fig3_damping_posterior.png"
    fig.savefig(p, dpi=180)
    plt.close(fig)
    paths.append(p)

    # Figure 4: QOI intervals.
    fig, ax = plt.subplots(figsize=(9.2, 5.8))
    names = []
    meds = []
    los = []
    his = []
    truths = []
    x = []
    k = 0
    for label in AMP_LABELS:
        for qname in ["peak_ratio", "band_rms_ratio", "peak_interface_mass_kg"]:
            vals = np.asarray(qoi_samples[label][qname])
            lo, med, hi = np.percentile(vals, [2.5, 50, 97.5])
            names.append(f"{label}\n{qname.replace('_', ' ')}")
            los.append(med - lo)
            his.append(hi - med)
            meds.append(med)
            truths.append(summary["qois_truth"][label][qname])
            x.append(k)
            k += 1
    x = np.asarray(x)
    ax.errorbar(x, meds, yerr=[los, his], fmt="o", color="#2d3748", capsize=4, label="posterior 95%")
    ax.scatter(x, truths, marker="x", s=70, color="#c53030", label="synthetic truth")
    ax.set_yscale("log")
    ax.set_xticks(x)
    ax.set_xticklabels(names, fontsize=8)
    ax.set_ylabel("QOI value (mixed units; see label)")
    ax.set_title("Held-out damping-dependent QOIs; intervals include output-space residual inflation")
    style_axes(ax)
    ax.legend(frameon=False, loc="best")
    fig.tight_layout()
    p = FIG / "fig4_qoi_posterior.png"
    fig.savefig(p, dpi=180)
    plt.close(fig)
    paths.append(p)

    return paths


def build_summary(samples, diagnostics, pred_t, pred_m, qoi_samples, noisy_log_heldout, runtime_s):
    truth = {}
    for i, label in enumerate(AMP_LABELS):
        props = DATA["truth_props"][i]
        truth[label] = {k: float(v) for k, v in props.items()}

    zlow_ci = interval(samples["zeta_low"])
    zhigh_ci = interval(samples["zeta_high"])
    low_truth = truth["low"]["zeta12"]
    high_truth = truth["high"]["zeta12"]
    prob_high = float(np.mean(samples["zeta_high"] > samples["zeta_low"]))

    clean_log = np.log(np.abs(DATA["truth_t21"][:, HELDOUT_MASK]))
    cover = 0
    n = clean_log.size
    for i in range(2):
        lo = np.percentile(noisy_log_heldout[:, i, :], 2.5, axis=0)
        hi = np.percentile(noisy_log_heldout[:, i, :], 97.5, axis=0)
        cover += int(np.sum((clean_log[i] >= lo) & (clean_log[i] <= hi)))

    q_truth = {}
    q_post = {}
    q_cover = 0
    q_n = 0
    for i, label in enumerate(AMP_LABELS):
        q_truth[label] = qois_from_curves(DATA["truth_t21"][i], DATA["truth_m12"][i])
        q_post[label] = {}
        for qname, vals in qoi_samples[label].items():
            vals = np.asarray(vals)
            ci = interval(vals)
            q_post[label][qname] = {"p025": ci[0], "p50": ci[1], "p975": ci[2]}
            q_n += 1
            if ci[0] <= q_truth[label][qname] <= ci[2]:
                q_cover += 1

    summary = {
        "runtime_s": float(runtime_s),
        "data_count": {
            "synthetic_realizations": 1,
            "amplitude_conditions": len(AMP_LEVELS),
            "frequency_lines": len(FREQS),
            "training_lines_per_condition": int(TRAIN_MASK.sum()),
            "heldout_lines_per_condition": int(HELDOUT_MASK.sum()),
        },
        "forcing_cancellation": {
            "max_relative_error": float(np.max(DATA["forced_ratio_error"])),
            "inference_used_force_function": False,
            "likelihood_quantity": "complex response ratio T21 = a_secondary/a_primary",
        },
        "truth": truth,
        "nuts_diagnostics": diagnostics,
        "posterior": {
            "k1_scale": dict(zip(["p025", "p50", "p975"], interval(np.exp(samples["log_k1_scale"])))),
            "k12_scale": dict(zip(["p025", "p50", "p975"], interval(np.exp(samples["log_k12_scale"])))),
            "sigma_model": dict(zip(["p025", "p50", "p975"], interval(samples["sigma_model"]))),
            "zeta_low": dict(zip(["p025", "p50", "p975"], zlow_ci)),
            "zeta_high": dict(zip(["p025", "p50", "p975"], zhigh_ci)),
        },
        "damping_learning": {
            "truth_low": low_truth,
            "truth_high": high_truth,
            "zeta_low_ci": zlow_ci,
            "zeta_high_ci": zhigh_ci,
            "prob_zeta_high_gt_low": prob_high,
            "truth_low_covered": bool(zlow_ci[0] <= low_truth <= zlow_ci[2]),
            "truth_high_covered": bool(zhigh_ci[0] <= high_truth <= zhigh_ci[2]),
            "interpretation": "equivalent linear damping at tested amplitude levels, not the hidden nonlinear law",
        },
        "heldout_ratio_coverage": {
            "covered": int(cover),
            "n": int(n),
            "coverage_fraction": float(cover / n),
            "quantity": "clean held-out log |T21| under posterior predictive residual bands",
        },
        "qois_truth": q_truth,
        "qois_posterior": q_post,
        "qoi_coverage": {"covered": int(q_cover), "n": int(q_n), "coverage_fraction": float(q_cover / q_n)},
    }
    return summary


def write_packet(summary):
    p = summary["damping_learning"]
    d = summary["nuts_diagnostics"]
    q = summary["qoi_coverage"]
    h = summary["heldout_ratio_coverage"]
    sm = summary["posterior"]["sigma_model"]
    low_cov = "covers" if p["truth_low_covered"] else "misses"
    high_cov = "covers" if p["truth_high_covered"] else "misses"
    text = f"""# Packet - forcing-marginalized damping toy

2026-06-12. Workspace `artifacts/reports/forcing_marginalized_damping_toy_20260612/`.

**One-command replay:** `bash run_all.sh`. **Checker:** `python3 check.py`.

## Method summary

This is a synthetic primary/secondary plumbing study for amplitude-dependent joint damping. The truth is a 3-DOF primary/secondary/hidden-rattler system. Its forcing spectrum, hidden rattler, amplitude-dependent damping law, and amplitude-dependent stiffness softening are not given to the digital twin.

The twin sees only the complex response ratio

```text
T21(f, A) = a_secondary(f, A) / a_primary(f, A)
```

Because both responses come from the same hidden input force, the force cancels. The likelihood never contains a force-function parameter.

The twin is a 2-DOF equivalent model. It infers primary stiffness scale, joint stiffness scale, a low-amplitude equivalent damping ratio, a high-amplitude equivalent damping ratio, and a residual model-error scale.

Data count: one synthetic realization, two amplitude conditions, {summary['data_count']['frequency_lines']} frequency lines, {summary['data_count']['training_lines_per_condition']} training lines and {summary['data_count']['heldout_lines_per_condition']} held-out lines per condition. There is no test-to-test or flight-to-flight variability in this toy.

## Results

- Forcing cancellation check: max relative error between response-derived `a2/a1` and the direct transfer ratio is **{summary['forcing_cancellation']['max_relative_error']:.2e}**.
- NUTS diagnostics: max R-hat **{d['max_rhat']:.3f}**, min ESS **{d['min_ess']:.0f}**, divergence fraction **{d['div_frac']:.3f}**.
- Damping learned: `P(zeta_high > zeta_low) = {p['prob_zeta_high_gt_low']:.3f}`.
- Low-amplitude physical truth `zeta = {p['truth_low']:.4f}`, equivalent-twin posterior 95% interval [{p['zeta_low_ci'][0]:.4f}, {p['zeta_low_ci'][2]:.4f}] -> **{low_cov}** the hidden physical value.
- High-amplitude physical truth `zeta = {p['truth_high']:.4f}`, equivalent-twin posterior 95% interval [{p['zeta_high_ci'][0]:.4f}, {p['zeta_high_ci'][2]:.4f}] -> **{high_cov}** the hidden physical value.
- Residual model-error scale: median **{sm['p50']:.3f}** log/phase units, 95% interval [{sm['p025']:.3f}, {sm['p975']:.3f}].
- Held-out clean log-ratio coverage: **{h['covered']}/{h['n']} = {h['coverage_fraction']:.2f}**.
- Damping-dependent QOI coverage: **{q['covered']}/{q['n']} = {q['coverage_fraction']:.2f}**.

## Figures

- `figures/fig1_forcing_cancellation.png`: hidden forcing exists, but the response ratio cancels it.
- `figures/fig2_ratio_fit.png`: posterior response-ratio bands against train and held-out points.
- `figures/fig3_damping_posterior.png`: low/high equivalent damping posterior.
- `figures/fig4_qoi_posterior.png`: held-out QOI intervals versus synthetic truth.

## Honest interpretation

GREEN claim: the toy demonstrates the plumbing for detecting an amplitude-dependent damping shift and predicting damping-sensitive, force-normalized QOIs while integrating out the forcing function.

YELLOW caveat: the equivalent damping values are biased upward relative to the hidden physical damping because the 2-DOF twin is also absorbing hidden-DOF and stiffness-softening error. The twin does **not** identify the hidden nonlinear slip law, Coulomb friction coefficient, preload, or contact state. A real rattly aerospace joint study would need amplitude sweeps, preload variation, or an explicit friction/contact model before claiming physical joint-law recovery.
"""
    (ROOT / "packet.md").write_text(text)


def main():
    t0 = time.time()
    samples, diagnostics = run_nuts()
    pred_t, pred_m, qoi_samples, noisy_log_heldout = posterior_predictions(samples)
    runtime_s = time.time() - t0
    summary = build_summary(samples, diagnostics, pred_t, pred_m, qoi_samples, noisy_log_heldout, runtime_s)
    json.dump(summary, open(OUT / "summary.json", "w"), indent=2)
    np.savez(
        OUT / "posterior_samples.npz",
        **{k: np.asarray(v) for k, v in samples.items()},
        freqs=FREQS,
        train_mask=TRAIN_MASK,
        heldout_mask=HELDOUT_MASK,
        truth_t21=DATA["truth_t21"],
        obs_t21=DATA["obs_t21"],
        pred_t21=pred_t,
    )
    paths = make_figures(samples, pred_t, pred_m, qoi_samples, summary)
    make_image_qa(paths)
    write_packet(summary)
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
