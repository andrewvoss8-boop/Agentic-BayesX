#!/usr/bin/env python3
"""Main experiment: model-form-error sweep delta x arms (the confidently-wrong test).

For each error CLASS and each injected-error level, fit the SAME synthetic data with:
  A0  deterministic LSQ        (context only; the paper's deferred-UQ point estimate)
  A1  Naive-NoDisc  (NUTS)     sigma_d FIXED 0, iid measurement noise only  <- Bilionis's arm
  A2  DiscAware-iid  (NUTS)    learns sigma_d, iid discrepancy
  A3  DiscAware-corr (NUTS)    learns sigma_d + Schneider-style correlated discrepancy

Records per cell: all-variable NUTS diagnostics; held-out (masked) predictive coverage of the
noisy observation AND of the clean truth; per-mode alpha intervals + truth-covered; learned
sigma_d; held-out peak-amplitude QOI interval + covered. Resumable: skips finished cells.

Channels Ch1/Ch2 = observed (fit); Ch3/Ch4 = masked (held out, predicted, scored post-hoc).
Float64; BLAS threads pinned by run_all.sh.
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
WS = HERE.parent
OUT = WS / "out"
OUT.mkdir(exist_ok=True)
sys.path.insert(0, str(HERE))

import core  # noqa: E402
import nuts_update as nu  # noqa: E402

# ------------------------------------------------------------------
# Fixed design constants
# ------------------------------------------------------------------
SIGMA_MEAS = 0.05
# Main "correlated" class uses a 3-mode, well-resolved modal set (18/95/280 Hz). The default
# scaffold's 4th mode (720 Hz) is intrinsically weakly identified from the 2 observed channels
# (it goes bimodal even at delta=0, with NO discrepancy) -> that is HF under-identification, a
# DIFFERENT phenomenon from the model-form-error malady we isolate here. The HF local mode is
# reserved for E-LIMIT and the identifiability gate, where under-identification is the point.
# See decisions_log.md D9.
ALPHA_TRUE = np.array([0.95, 0.95, 0.95])
BETA_TRUE = np.array([1.0, 1.0, 1.0])
GAMMA_TRUE = core.GAMMA0
DELTAS = [0.0, 0.05, 0.10, 0.20, 0.35, 0.50]
MM_SEVERITIES = [0.0, 0.5, 1.0]  # missing-mode class: relative strength of the dropped mode in truth


def modes3():
    """3 well-resolved modes (18/95/280 Hz), all 4 channels. The main-sweep modal set."""
    m = core.default_modes()
    return core.Modes(f=m.f[:3].copy(), zeta=m.zeta[:3].copy(),
                      Phi=m.Phi[:, :3].copy(), Binput=m.Binput.copy())
NWARM = 1000
NSAMP = 1000
NCHAIN = 4
QOI_BAND = (10.0, 900.0)
NOISE_REPS = 8  # noise draws per posterior sample for predictive bands


# ------------------------------------------------------------------
# Data generation (shared across arms at a given level => "same data")
# ------------------------------------------------------------------
def make_modes_missingmode(severity):
    """Missing-mode (hidden-DOF) error class: TRUTH has 3 modes (18/95/280 Hz) with the 280 Hz
    mode (index 2) scaled by `severity`; the FIT model DROPS that mode (keeps 18/95 Hz only).
    severity=0 => the 280 Hz mode is absent from truth too (control, no model-form error)."""
    m = modes3()
    Phi = m.Phi.copy()
    Phi[:, 2] = Phi[:, 2] * np.sqrt(max(severity, 0.0))  # scale 280 Hz contribution ~ severity
    truth_modes = core.Modes(f=m.f.copy(), zeta=m.zeta.copy(), Phi=Phi, Binput=m.Binput.copy())
    keep = [0, 1]
    fit_modes = core.Modes(f=m.f[keep].copy(), zeta=m.zeta[keep].copy(),
                           Phi=m.Phi[:, keep].copy(), Binput=m.Binput.copy())
    return truth_modes, fit_modes


def gen_data(cls, level, seed_base=20260616):
    """Return (truth_modes, fit_modes, truth, measured, alpha_truth_fit) for a cell.
    The same call (deterministic seeds) gives identical data for every arm."""
    freqs = core.freq_grid()
    if cls == "correlated":
        modes = modes3()
        rng_t = np.random.default_rng(seed_base + int(round(level * 1000)))
        lo = level / 6.0
        hi = max(level, 1e-9)
        td = core.make_truth(freqs, modes, ALPHA_TRUE, BETA_TRUE, GAMMA_TRUE, rng_t,
                             disc_std_lo=lo, disc_std_hi=hi)
        truth = td["truth"]
        truth_modes = fit_modes = modes
        alpha_truth_fit = ALPHA_TRUE.copy()
    elif cls == "missingmode":
        truth_modes, fit_modes = make_modes_missingmode(level)
        rng_t = np.random.default_rng(seed_base + 7000 + int(round(level * 1000)))
        # small fixed discrepancy floor so the dominant error is the missing mode
        td = core.make_truth(freqs, truth_modes, ALPHA_TRUE, BETA_TRUE, GAMMA_TRUE, rng_t,
                             disc_std_lo=0.02, disc_std_hi=0.05)
        truth = td["truth"]
        alpha_truth_fit = ALPHA_TRUE[[0, 1]].copy()  # truth alpha for the 2 kept modes
    else:
        raise ValueError(cls)
    rng_m = np.random.default_rng(seed_base + 99 + int(round(level * 1000)))
    measured = core.measure(truth, core.MASKED, rng_m, sigma_meas=SIGMA_MEAS, sigma_phase=SIGMA_MEAS)
    return freqs, truth_modes, fit_modes, truth, measured, alpha_truth_fit


# ------------------------------------------------------------------
# Predictive bands + coverage
# ------------------------------------------------------------------
def predictive_bands(samples, freqs, fit_modes, idx, sigma_d_samp, rng):
    """Return clean predictive log-mag (S,Nf,Nc) and per-sample sigma_d for the retained draws."""
    clean = np.zeros((len(idx), len(freqs), fit_modes.nc))
    for j, s in enumerate(idx):
        alpha = np.exp(samples["log_alpha"][s])
        beta = np.exp(samples["log_beta"][s])
        gamma = float(np.exp(samples["log_gamma"][s]))
        H = core.frf_np(freqs, alpha, beta, gamma, fit_modes)
        clean[j] = np.log(np.abs(H))
    return clean


def coverage_from_clean(clean, sd, target_logmag, channels, bmask, sigma_add, rng, reps=NOISE_REPS,
                        probs=(2.5, 97.5)):
    """Pooled predictive coverage: for each posterior sample add Gaussian noise with std
    sqrt(sigma_add^2 + sd^2), pool reps, take central interval, count covered held-out lines."""
    S, Nf, Nc = clean.shape
    total = np.sqrt(sigma_add ** 2 + np.asarray(sd) ** 2)  # (S,)
    noise = rng.standard_normal((S, reps, Nf, Nc)) * total[:, None, None, None]
    pred = (clean[:, None, :, :] + noise).reshape(S * reps, Nf, Nc)
    lo = np.percentile(pred, probs[0], axis=0)
    hi = np.percentile(pred, probs[1], axis=0)
    covered = 0
    ntot = 0
    for c in channels:
        m = bmask
        inside = (target_logmag[m, c] >= lo[m, c]) & (target_logmag[m, c] <= hi[m, c])
        covered += int(inside.sum())
        ntot += int(m.sum())
    return covered, ntot, lo, hi


def qoi_interval(clean, sd, channel, bmask, rng, reps=NOISE_REPS, probs=(2.5, 97.5)):
    """Predictive interval of the held-out peak |H| on `channel`, from the truth-flavoured
    (discrepancy-only) predictive (clean + sigma_d). Returns (lo, med, hi) in linear amplitude."""
    S, Nf, Nc = clean.shape
    total = np.asarray(sd)
    noise = rng.standard_normal((S, reps, Nf)) * total[:, None, None]
    pred = clean[:, None, :, channel] + noise  # (S,reps,Nf) log-mag
    mag = np.exp(pred[:, :, bmask])
    peak = mag.max(axis=2).ravel()
    return float(np.percentile(peak, probs[0])), float(np.median(peak)), float(np.percentile(peak, probs[1]))


# ------------------------------------------------------------------
# One cell
# ------------------------------------------------------------------
def run_cell(cls, level, arm, observed=None, masked=None, peakshift=0.0, seed=20260616):
    observed = core.OBSERVED if observed is None else np.asarray(observed)
    masked = core.MASKED if masked is None else np.asarray(masked)
    freqs, truth_modes, fit_modes, truth, measured, alpha_truth_fit = gen_data(cls, level)
    bmask = core.band_mask(freqs, *QOI_BAND)
    rng = np.random.default_rng(seed + hash((cls, round(level, 4), arm)) % (2 ** 31))

    # optional coherent peak shift on the MASKED truth (only used by exp_limit; kept here for reuse)
    truth_used = truth.copy()
    if peakshift != 0.0:
        truth_used = core.reconstruct_virtual(truth, masked, np.random.default_rng(seed + 5),
                                              recon_std_lo=0.0, recon_std_hi=0.0,
                                              bias_peakshift=peakshift, modes=truth_modes, freqs=freqs)

    obs_logmag = np.log(np.abs(measured))            # noisy observation, all channels
    truth_logmag = np.log(np.abs(truth_used))        # clean truth, all channels
    rec = {"class": cls, "level": float(level), "arm": arm,
           "observed": observed.tolist(), "masked": masked.tolist(),
           "nm_fit": int(fit_modes.nm), "alpha_truth_fit": alpha_truth_fit.tolist(),
           "sigma_meas": SIGMA_MEAS}

    if arm == "A0":  # deterministic point estimate
        cw = np.zeros(truth_modes.nc); cw[observed] = 1.0
        sol = core.deterministic_update(freqs, fit_modes, measured, cw, rng)
        H = sol["H"]
        rec["alpha_point"] = sol["alpha"].tolist()
        qoi = {}
        for c in masked.tolist():
            pk_pred = core.peak_qoi(H, freqs, c, bmask)
            pk_true = core.peak_qoi(truth_used, freqs, c, bmask)
            qoi[str(c)] = {"pred": pk_pred, "truth": pk_true,
                           "err_db": float(20 * np.log10(max(pk_pred, 1e-12) / max(pk_true, 1e-12)))}
        rec["det_qoi"] = qoi
        return rec

    # NUTS arms ----------------------------------------------------
    t0 = time.time()
    learn = (arm != "A1")
    correlated = (arm == "A3")
    dense = correlated
    sig_per_ch = np.full(truth_modes.nc, SIGMA_MEAS)
    samples, diag = nu.run_nuts(
        freqs, fit_modes, obs_logmag, observed, sig_per_ch,
        correlated=correlated, corr_logf=0.25, corr_channels=observed, dense_mass=dense,
        learn_discrepancy=learn, num_warmup=NWARM, num_samples=NSAMP, num_chains=NCHAIN,
        seed=seed)
    rec["runtime_s"] = round(time.time() - t0, 2)
    rec["nuts"] = diag
    rec["converged"] = bool(diag["max_rhat"] <= 1.05 and diag["min_ess"] >= 200 and diag["div_frac"] < 0.02)

    n = len(samples["log_gamma"])
    idx = np.arange(0, n, 4)
    sd_full = samples.get("sigma_d", np.zeros(n))
    sd = np.asarray(sd_full)[idx]
    clean = predictive_bands(samples, freqs, fit_modes, idx, sd, rng)

    # held-out predictive coverage (masked channels) -- noisy observation and clean truth
    cov_noisy, ntot, _, _ = coverage_from_clean(clean, sd, obs_logmag, masked.tolist(), bmask,
                                                sigma_add=SIGMA_MEAS, rng=rng)
    cov_truth, _, _, _ = coverage_from_clean(clean, sd, truth_logmag, masked.tolist(), bmask,
                                             sigma_add=0.0, rng=rng)
    rec["heldout_coverage"] = {
        "noisy_covered": cov_noisy, "noisy_n": ntot, "noisy_frac": cov_noisy / max(ntot, 1),
        "truth_covered": cov_truth, "truth_n": ntot, "truth_frac": cov_truth / max(ntot, 1),
        "nominal": 0.95}

    # held-out peak-amplitude QOI per masked channel
    qoi = {}
    for c in masked.tolist():
        lo, med, hi = qoi_interval(clean, sd, c, bmask, rng)
        pk_true = core.peak_qoi(truth_used, freqs, c, bmask)
        qoi[str(c)] = {"lo": lo, "med": med, "hi": hi, "truth": pk_true,
                       "covered": bool(lo <= pk_true <= hi)}
    rec["heldout_qoi"] = qoi
    rec["qoi_covered"] = int(sum(v["covered"] for v in qoi.values()))
    rec["qoi_n"] = len(qoi)

    # per-mode alpha intervals + truth-covered
    la = np.asarray(samples["log_alpha"])
    alpha = np.exp(la)
    a_int = []
    for i in range(fit_modes.nm):
        lo, med, hi = (float(np.percentile(alpha[:, i], 2.5)), float(np.median(alpha[:, i])),
                       float(np.percentile(alpha[:, i], 97.5)))
        a_int.append({"mode": i, "lo": lo, "med": med, "hi": hi,
                      "truth": float(alpha_truth_fit[i]),
                      "covered": bool(lo <= alpha_truth_fit[i] <= hi), "width": hi - lo})
    rec["alpha_intervals"] = a_int

    # learned sigma_d
    if learn:
        sdf = np.asarray(sd_full)
        rec["sigma_d"] = {"lo": float(np.percentile(sdf, 2.5)), "med": float(np.median(sdf)),
                          "hi": float(np.percentile(sdf, 97.5))}
    else:
        rec["sigma_d"] = {"lo": 0.0, "med": 0.0, "hi": 0.0, "fixed": True}
    return rec


# ------------------------------------------------------------------
# Driver (resumable)
# ------------------------------------------------------------------
def cell_path(cls, level, arm, tag=""):
    return OUT / f"cell_{cls}{tag}_{level:.2f}_{arm}.json"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--smoke", action="store_true", help="tiny draws to validate plumbing")
    ap.add_argument("--only", default="all", help="correlated|missingmode|altchannel|all")
    args = ap.parse_args()

    global NWARM, NSAMP
    if args.smoke:
        NWARM, NSAMP = 150, 150

    jobs = []
    arms = ["A0", "A1", "A2", "A3"]
    if args.only in ("correlated", "all"):
        for d in DELTAS:
            for a in arms:
                jobs.append(("correlated", d, a, {}))
    if args.only in ("missingmode", "all"):
        for s in MM_SEVERITIES:
            for a in arms:
                jobs.append(("missingmode", s, a, {}))
    if args.only in ("altchannel", "all"):
        # held-out channel-choice sensitivity at delta=0.20: fit Ch3/Ch4, hold out Ch1/Ch2
        for a in ["A1", "A2"]:
            jobs.append(("correlated", 0.20, a, {"observed": [2, 3], "masked": [0, 1], "tag": "_alt"}))

    t_all = time.time()
    for cls, level, arm, kw in jobs:
        tag = kw.pop("tag", "")
        p = cell_path(cls, level, arm, tag)
        if p.exists():
            print(f"[skip] {p.name}", flush=True)
            continue
        print(f"[run ] {cls}{tag} level={level} arm={arm} ...", flush=True)
        rec = run_cell(cls, level, arm, observed=kw.get("observed"), masked=kw.get("masked"))
        json.dump(rec, open(p, "w"), indent=1)
        msg = rec.get("nuts", {})
        print(f"       done {p.name}  rhat={msg.get('max_rhat','-')} ess={msg.get('min_ess','-')} "
              f"div={msg.get('div_frac','-')} cov={rec.get('heldout_coverage',{}).get('truth_frac','-')}",
              flush=True)
    print(f"ALL CELLS in {time.time()-t_all:.1f}s", flush=True)


if __name__ == "__main__":
    main()
