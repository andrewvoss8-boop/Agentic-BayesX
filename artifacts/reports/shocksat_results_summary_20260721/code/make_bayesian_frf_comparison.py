#!/usr/bin/env python3
"""Two-channel FRF comparison for the Bilionis advisor update.

The figure is deliberately a small-multiple comparison: each panel contains the
measured curve and one model curve.  The +X drive is held out from the whole-FRF
and Beck-style fits.  It shows every defensible stored uncertainty object:

* a converged modal-NUTS parameter-propagation envelope (not a calibrated FRF
  predictive interval, because the modal likelihood did not model amplitude
  discrepancy), and
* a whole-FRF posterior-predictive interval including its fitted output-error
  variance, printed as NOT TRUSTWORTHY because that posterior did not converge.

The Beck run retained only a posterior-mean field and its NUTS run did not
converge, so manufacturing a band around its deterministic MAP is prohibited.
"""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from scipy.special import ndtr


HERE = Path(__file__).resolve()
REPORT = HERE.parent.parent
REPORTS = REPORT.parent
STUDY = REPORTS / "shocksat_full_spectrum_frf_20260714"
EXACT = REPORTS / "shocksat_fullspec_exact_completion_20260716"
MODAL = REPORTS / "shocksat_fem_modal_twin_20260609"
FIGDIR = REPORT / "figures_revised"
OUTDIR = REPORT / "out"

sys.path.insert(0, str(STUDY / "code"))
import arm_c_nuts as arm_c  # noqa: E402
import wide_forward as wf  # noqa: E402
import wide_package as wp  # noqa: E402
import wscore_wide as score  # noqa: E402


FOLD = "m_xpos_990x"
TRAIN = [k for k in score.DEV_KEYS if k != FOLD]
INK = "#171717"
GREY = "#8b8b8b"
BLUE = "#2864a5"
ORANGE = "#cf6b2e"
PURPLE = "#7254a3"
GREEN = "#2f7d58"
BAND_CACHE = OUTDIR / "frf_predictive_bands.npz"
BAND_METHOD_VERSION = 1
N_POST_PER_CHAIN = 30


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def log_mae(pred: np.ndarray, measured: np.ndarray, mask: np.ndarray) -> np.ndarray:
    return np.mean(
        np.abs(np.log10(np.abs(pred[:, mask]) + 1e-300)
               - np.log10(np.abs(measured[:, mask]) + 1e-300)),
        axis=1,
    )


def modal_state(pkg, theta: np.ndarray) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Compute eigensolution once so all four drive predictions reuse it."""
    freqs, vecs = pkg.modes(np.asarray(theta, float))
    keep = (freqs >= wf.F_SUPPORT[0]) & (freqs <= wf.F_SUPPORT[1])
    freqs = np.asarray(freqs)[keep]
    vecs = np.asarray(vecs)[:, keep]
    return freqs, vecs, wf.zeta_table(freqs)


def predict_from_state(pkg, state, dkey: str, fc: np.ndarray, rows: np.ndarray) -> np.ndarray:
    freqs, vecs, zeta = state
    us = np.asarray(pkg.sens_rows)[rows] @ vecs
    ud = np.asarray(pkg.drives[dkey]) @ vecs
    residues = us * ud[None, :]
    return wf.WF._windowed_H(residues, freqs, zeta, np.asarray(fc, float)) / wf.G_IN_S2


def gain_from_state(pkg, state, train_keys: list[str], caches: dict) -> float:
    offsets = []
    for key in train_keys:
        cache = caches[key]
        rows, cols = score._usable(pkg, cache, cache["band"])
        if len(rows) == 0:
            continue
        pred = predict_from_state(pkg, state, key, cache["freqs"][cache["band"]], rows)
        lp = np.log10(np.abs(pred) + 1e-300)
        obs = np.log10(np.abs(cache["H1"][cols][:, cache["band"]]) + 1e-300)
        offsets.append(float(np.mean(obs - lp)))
    return 20.0 * float(np.mean(offsets)) if offsets else 0.0


def chain_draws(values: np.ndarray, n_per_chain: int) -> np.ndarray:
    """Deterministically retain equal draws from every chain."""
    if values.ndim < 2:
        raise ValueError("expected a chain and draw axis")
    n_draw = values.shape[1]
    idx = np.linspace(0, n_draw - 1, n_per_chain, dtype=int)
    return values[:, idx].reshape((-1,) + values.shape[2:])


def mixture_quantile(means: np.ndarray, scales: np.ndarray, q: float) -> np.ndarray:
    """Pointwise quantile of an equal-weight univariate Normal mixture."""
    scales = np.maximum(np.asarray(scales, float), 1e-9)[:, None, None]
    lower = np.min(means - 8.0 * scales, axis=0)
    upper = np.max(means + 8.0 * scales, axis=0)
    for _ in range(55):
        mid = 0.5 * (lower + upper)
        cdf = np.mean(ndtr((mid[None, :, :] - means) / scales), axis=0)
        lower = np.where(cdf < q, mid, lower)
        upper = np.where(cdf < q, upper, mid)
    return 0.5 * (lower + upper)


def make_predictive_bands(
    p0, caches: dict, f: np.ndarray, band: np.ndarray, rows0: np.ndarray,
    pick_indices: list[int], daq: np.ndarray,
) -> dict[str, np.ndarray]:
    """Propagate stored modal and whole-FRF posterior draws for two channels."""
    modal_path = MODAL / "nuts_full_samples.npz"
    whole_path = STUDY / "out" / "armB" / f"with_error_term_{FOLD}.npz"
    input_hashes = {"modal": sha256(modal_path), "whole_frf": sha256(whole_path)}
    wanted_meta = {
        "method_version": BAND_METHOD_VERSION,
        "n_per_chain": N_POST_PER_CHAIN,
        "fold": FOLD,
        "daq": [int(daq[i]) for i in pick_indices],
        "input_sha256": input_hashes,
    }
    if BAND_CACHE.exists():
        cached = np.load(BAND_CACHE, allow_pickle=True)
        if json.loads(str(cached["meta"].item())) == wanted_meta:
            return {k: np.asarray(cached[k]) for k in cached.files if k != "meta"}

    pick_rows = np.asarray(rows0)[pick_indices]
    fc = f[band]
    modal_file = np.load(modal_path, allow_pickle=True)
    if list(modal_file["gnames"].astype(str)) != list(np.asarray(p0.free_names).astype(str)):
        raise RuntimeError("modal posterior and wide package parameter orders differ")
    # The original file flattened four 1,000-draw chains in chain-major order.
    theta_modal = modal_file["theta"].reshape(4, -1, len(p0.free_names))
    theta_modal = chain_draws(theta_modal, N_POST_PER_CHAIN)

    modal_log = []
    for theta in theta_modal:
        state = modal_state(p0, theta)
        gain = gain_from_state(p0, state, TRAIN, caches)
        pred = predict_from_state(p0, state, FOLD, fc, pick_rows) * 10 ** (gain / 20.0)
        modal_log.append(np.log10(np.abs(pred) + 1e-300))
    modal_log = np.asarray(modal_log)

    whole_file = np.load(whole_path, allow_pickle=True)
    theta_whole = np.exp(chain_draws(whole_file["t_log_theta"], N_POST_PER_CHAIN))
    sigma_e = chain_draws(whole_file["sigma_e"], N_POST_PER_CHAIN)
    sigma_n = chain_draws(whole_file["sigma_n"], N_POST_PER_CHAIN)
    whole_log_mean = []
    for theta in theta_whole:
        state = modal_state(p0, theta)
        gain = gain_from_state(p0, state, TRAIN, caches)
        pred = predict_from_state(p0, state, FOLD, fc, pick_rows) * 10 ** (gain / 20.0)
        whole_log_mean.append(np.log10(np.abs(pred) + 1e-300))
    whole_log_mean = np.asarray(whole_log_mean)
    whole_scale = np.sqrt(sigma_e ** 2 + sigma_n ** 2)

    payload = {
        "freq": fc,
        "modal_lo": 10 ** np.quantile(modal_log, 0.025, axis=0),
        "modal_med": 10 ** np.quantile(modal_log, 0.5, axis=0),
        "modal_hi": 10 ** np.quantile(modal_log, 0.975, axis=0),
        "whole_lo": 10 ** mixture_quantile(whole_log_mean, whole_scale, 0.025),
        "whole_med": 10 ** mixture_quantile(whole_log_mean, whole_scale, 0.5),
        "whole_hi": 10 ** mixture_quantile(whole_log_mean, whole_scale, 0.975),
    }
    np.savez_compressed(BAND_CACHE, **payload, meta=json.dumps(wanted_meta, sort_keys=True))
    return payload


def main() -> None:
    FIGDIR.mkdir(parents=True, exist_ok=True)
    OUTDIR.mkdir(parents=True, exist_ok=True)

    # A0 is the original reduced FEM.  A1_enr is the same physical class enriched
    # at the survey-frequency MAP, so theta=1 represents that fitted class.
    p0 = wp.load("A0_wide")
    p1 = wp.load("A0_wide__enr")
    caches = score.load_caches()
    cache = caches[FOLD]
    f = np.asarray(cache["freqs"], float)
    band = (f >= 45.0) & (f <= 500.0)

    rows0, cols = score._usable(p0, cache, band)
    rows1_of = {int(d): i for i, d in enumerate(np.asarray(p1.sens_daq))}
    daq = np.asarray([int(cache["daq"][i]) for i in cols], int)
    rows1 = np.asarray([rows1_of[int(d)] for d in daq], int)
    measured = np.asarray(cache["H1"])[cols]

    one0 = np.ones(len(p0.free_names))
    one1 = np.ones(len(p1.free_names))

    # Every amplitude scale below is learned on the other three drives only.
    gain_a0 = score._fold_gain(p0, one0, TRAIN, caches, False, 0.01)
    h_a0 = wf.predict_H(p0, one0, FOLD, f, windowed=False, flat_zeta=0.01)[rows0]
    h_a0 *= 10 ** (gain_a0 / 20.0)

    gain_a1 = score._fold_gain(p1, one1, TRAIN, caches, True, None)
    h_a1 = wf.predict_H(p1, one1, FOLD, f, windowed=True, flat_zeta=None)[rows1]
    h_a1 *= 10 ** (gain_a1 / 20.0)

    # B: leakage-safe, fold-specific deterministic MAP of the correlated
    # whole-FRF likelihood.  Its NUTS posterior did not converge.
    arm_b_summary = json.loads((STUDY / "out" / "armB_summary.json").read_text())
    theta_b = np.asarray(arm_b_summary["with_error_term_amp_map"][FOLD], float)
    gain_b = score._fold_gain(p0, theta_b, TRAIN, caches, True, None)
    h_b = wf.predict_H(p0, theta_b, FOLD, f, windowed=True, flat_zeta=None)[rows0]
    h_b *= 10 ** (gain_b / 20.0)

    # C: leakage-safe exact-basis Beck-style shape MAP, independently refit on
    # the other three drives in the completion audit.  Its NUTS posterior also
    # did not converge.
    c_map_path = EXACT / "out" / "armC_exact_maps" / f"shapes_map_{FOLD}.npz"
    zc = np.load(c_map_path, allow_pickle=True)
    fwd_c = arm_c.shapes_forward(
        p1, one1, np.asarray(zc["raw_mean"]), np.asarray(zc["ks"], int), int(zc["r0"])
    )
    gain_c = score._fold_gain(p1, one1, TRAIN, caches, True, None, fwd=fwd_c)
    h_c = fwd_c(p1, one1, FOLD, f)[rows1]
    h_c *= 10 ** (gain_c / 20.0)

    e0 = log_mae(h_a0, measured, band)
    update_errors = np.vstack([log_mae(h, measured, band) for h in (h_a1, h_b, h_c)])
    best_update = np.min(update_errors, axis=0)
    improvement = e0 - best_update
    good_i = int(np.argmax(improvement))
    # The bad channel is the channel no eligible update predicts well, not a
    # failed sensor: eligibility already requires the study's coherence gate.
    remaining = np.min(np.vstack([e0, update_errors]), axis=0)
    bad_i = int(np.argmax(remaining))
    if bad_i == good_i:
        bad_i = int(np.argsort(remaining)[-2])

    picks = [("GOOD", good_i), ("BAD", bad_i)]
    predictive = make_predictive_bands(p0, caches, f, band, rows0, [good_i, bad_i], daq)

    methods = [
        ("Original FEM\ndeterministic baseline", h_a0, None, GREY),
        ("Modal NUTS\nparameter-only 95%", None, "modal", BLUE),
        ("Whole-FRF NUTS\n95% predictive — not trustworthy", None, "whole", ORANGE),
        ("Beck-style shape MAP\nno defensible band", h_c, None, PURPLE),
    ]
    fig, axes = plt.subplots(2, 4, figsize=(11.0, 5.8), sharex=True, sharey="row")
    fig.subplots_adjust(left=0.075, right=0.99, top=0.87, bottom=0.17, wspace=0.10, hspace=0.27)
    for row, (tag, idx) in enumerate(picks):
        for col, (label, pred, band_key, color) in enumerate(methods):
            ax = axes[row, col]
            ax.plot(f[band], np.abs(measured[idx, band]), color=INK, lw=1.35)
            if band_key is None:
                center = np.abs(pred[idx, band])
            else:
                center = predictive[f"{band_key}_med"][row]
                ax.fill_between(
                    predictive["freq"], predictive[f"{band_key}_lo"][row],
                    predictive[f"{band_key}_hi"][row], color=color, alpha=0.19, lw=0,
                )
            ax.plot(f[band], center, color=color, lw=1.05)
            ax.set_xscale("log")
            ax.set_yscale("log")
            ax.set_xlim(45, 500)
            ax.spines[["top", "right"]].set_visible(False)
            ax.grid(False)
            ax.tick_params(labelsize=7.5, length=2.5, color="#777777")
            err = float(np.mean(np.abs(np.log10(center + 1e-300)
                                       - np.log10(np.abs(measured[idx, band]) + 1e-300))))
            if row == 0:
                ax.set_title(label, fontsize=8.4, color=color, pad=7)
            ax.text(0.03, 0.05, f"error {err:.2f} log10", transform=ax.transAxes,
                    fontsize=7.3, color=color, va="bottom")
            if col == 1:
                ax.text(0.03, 0.96, "converged; R-hat 1.022, ESS 232\nFRF discrepancy not modeled",
                        transform=ax.transAxes, fontsize=6.35, color=BLUE, va="top")
            elif col == 2:
                ax.text(0.03, 0.96, "NOT TRUSTWORTHY\nR-hat 48.8, ESS 2.0",
                        transform=ax.transAxes, fontsize=6.45, color=ORANGE, va="top", fontweight="bold")
            elif col == 3:
                ax.text(0.03, 0.96, "NUTS failed: R-hat 13.95, ESS ~2\ndraws were not retained",
                        transform=ax.transAxes, fontsize=6.25, color=PURPLE, va="top")
        axes[row, 0].set_ylabel(
            f"{tag}: DAQ {daq[idx]}\n|H| [g/lbf, log]", fontsize=8.4, color=INK
        )

    for ax in axes[-1, :]:
        ax.set_xlabel("frequency [Hz, log]", fontsize=8.0)
    fig.suptitle(
        "Updating can repair one channel while leaving another far from the data",
        x=0.075, ha="left", fontsize=12.0, color=INK,
    )
    fig.text(
        0.075, 0.095,
        "Black = measured. Line = center estimate; shading = pointwise 95% envelope where stored draws support one. "
        "GOOD/BAD selection used the leakage-safe point estimates over "
        f"{len(daq)} coherence-qualified +X channels.",
        fontsize=7.6, color="#555555", ha="left",
    )
    fig.text(
        0.075, 0.045,
        "Source: ShockSat leave-one-drive-out studies (45–500 Hz). Blue is parameter propagation only. Orange includes "
        "whole-FRF output discrepancy but is not trustworthy because NUTS did not converge. No Beck band can be reconstructed.",
        fontsize=7.3, color="#555555", ha="left",
    )
    out = FIGDIR / "fig2_bayesian_good_bad_frf.png"
    fig.savefig(out, dpi=230, bbox_inches="tight", facecolor="white")
    plt.close(fig)

    records = []
    for tag, idx in picks:
        rec = {
            "label": tag,
            "daq_channel": int(daq[idx]),
            "original_error_log10": float(e0[idx]),
            "best_update_error_log10": float(best_update[idx]),
            "improvement_log10": float(improvement[idx]),
            "method_errors_log10": {
                "Original FEM": float(e0[idx]),
                "Modal-frequency MAP": float(update_errors[0, idx]),
                "Correlated whole-FRF MAP": float(update_errors[1, idx]),
                "Beck-style shape MAP": float(update_errors[2, idx]),
                "Modal NUTS displayed median": float(np.mean(np.abs(
                    np.log10(predictive["modal_med"][0 if tag == "GOOD" else 1] + 1e-300)
                    - np.log10(np.abs(measured[idx, band]) + 1e-300)))),
                "Whole-FRF NUTS displayed predictive median": float(np.mean(np.abs(
                    np.log10(predictive["whole_med"][0 if tag == "GOOD" else 1] + 1e-300)
                    - np.log10(np.abs(measured[idx, band]) + 1e-300)))),
            },
        }
        records.append(rec)
    metrics = {
        "selection_precommitted_in_code": {
            "good": "largest A0-to-best-update reduction in mean absolute log10 magnitude error",
            "bad": "largest remaining error after the best eligible method",
            "eligibility": "same +X drive, 45-500 Hz, median coherence >= 0.6, present in each package",
        },
        "n_eligible_channels": int(len(daq)),
        "fold": FOLD,
        "train_drives": TRAIN,
        "panels": records,
        "uncertainty_objects": {
            "modal": "120-draw converged NUTS parameter-propagation envelope; not calibrated for FRF discrepancy",
            "whole_frf": "120-draw pointwise posterior-predictive interval including fitted GP+noise marginal variance; NOT TRUSTWORTHY because the +X-fold posterior did not converge (R-hat 48.78, ESS 2.00)",
            "beck": "no band: posterior draws were not retained and NUTS did not converge (R-hat 13.95, ESS about 2)",
        },
        "fold_specific_whole_frf_rhat": 48.779646846796034,
        "fold_specific_whole_frf_ess": 2.0027743107061564,
        "input_sha256": {
            str(c_map_path.relative_to(REPORTS)): sha256(c_map_path),
            "shocksat_full_spectrum_frf_20260714/out/armB_summary.json": sha256(
                STUDY / "out" / "armB_summary.json"
            ),
            "shocksat_full_spectrum_frf_20260714/data/multiref_wide/m_xpos_990x_wide.npz": sha256(
                STUDY / "data" / "multiref_wide" / "m_xpos_990x_wide.npz"
            ),
        },
    }
    (OUTDIR / "bayesian_frf_comparison_metrics.json").write_text(json.dumps(metrics, indent=2) + "\n")
    print(json.dumps(metrics, indent=2))
    print(f"wrote {out}")


if __name__ == "__main__":
    main()
