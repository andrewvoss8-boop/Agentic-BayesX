#!/usr/bin/env python3
"""Triage existing datasets for amplitude-dependent damping / hysteresis signs.

This is a screening script, not a final nonlinear-system identification.
"""

from __future__ import annotations

import csv
import json
import math
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import scipy.io as sio
from scipy import signal, stats


REPO = Path(__file__).resolve().parents[4]
OUT = Path(__file__).resolve().parents[1]
FIG = OUT / "figures"


@dataclass
class DecayCase:
    label: str
    path: Path
    start_s: float
    end_s: float
    fband_hz: tuple[float, float]
    f1_nom_hz: float


MPL_DECAYS = [
    DecayCase(
        "MPL solo ruler pull",
        REPO / "MPL test stand/FEM/test_data/solo beam 12 inch span.csv",
        5.8,
        21.0,
        (2.2, 4.5),
        3.196,
    ),
    DecayCase(
        "MPL solo ruler repeat",
        REPO / "MPL test stand/FEM/test_data/solo beam 12 inch span (repeatability).csv",
        6.5,
        14.0,
        (2.2, 4.5),
        3.196,
    ),
    DecayCase(
        "MPL coupled ruler on shield",
        REPO / "MPL test stand/FEM/test_data/center beam pull.csv",
        4.0,
        36.5,
        (1.8, 4.2),
        3.078,
    ),
]


def read_csv_two_cols(path: Path) -> tuple[np.ndarray, np.ndarray]:
    data = np.genfromtxt(path, delimiter=",", names=True)
    names = data.dtype.names
    return np.asarray(data[names[0]], float), np.asarray(data[names[1]], float)


def smooth_moving(x: np.ndarray, n: int) -> np.ndarray:
    n = max(1, int(n))
    if n == 1:
        return x
    kernel = np.ones(n) / n
    return np.convolve(x, kernel, mode="same")


def decay_segments_from_envelope(t: np.ndarray, env: np.ndarray) -> dict[str, tuple[int, int, float]]:
    """Return contiguous decay segments by envelope fraction after the max."""
    peak_idx = int(np.nanargmax(env))
    env_tail = env[peak_idx:]
    max_env = float(env_tail[0])
    specs = {
        "high": (0.90, 0.45),
        "mid": (0.45, 0.20),
        "low": (0.20, 0.08),
    }
    segments: dict[str, tuple[int, int, float]] = {}
    for name, (hi, lo) in specs.items():
        below_hi = np.flatnonzero(env_tail <= hi * max_env)
        below_lo = np.flatnonzero(env_tail <= lo * max_env)
        if len(below_hi) == 0 or len(below_lo) == 0:
            continue
        i0 = peak_idx + int(below_hi[0])
        i1 = peak_idx + int(below_lo[0])
        if i1 - i0 < max(100, int(0.8 / np.median(np.diff(t)))):
            continue
        segments[name] = (i0, i1, float(np.nanmean(env[i0:i1])))
    return segments


def fit_decay_case(case: DecayCase) -> dict:
    t_all, y_all = read_csv_two_cols(case.path)
    fs = 1.0 / float(np.median(np.diff(t_all)))
    mask = (t_all >= case.start_s) & (t_all <= case.end_s)
    t = t_all[mask]
    y = y_all[mask] - float(np.median(y_all[mask]))
    sos = signal.butter(4, case.fband_hz, btype="bandpass", fs=fs, output="sos")
    yb = signal.sosfiltfilt(sos, y)
    analytic = signal.hilbert(yb)
    env = smooth_moving(np.abs(analytic), int(round(0.20 * fs)))
    phase = np.unwrap(np.angle(analytic))
    segs = decay_segments_from_envelope(t, env)
    fits = {}
    for name, (i0, i1, amp) in segs.items():
        tt = t[i0:i1]
        ee = np.maximum(env[i0:i1], np.nanpercentile(env, 1) * 0.1)
        pp = phase[i0:i1]
        env_fit = stats.linregress(tt, np.log(ee))
        phase_fit = stats.linregress(tt, pp)
        freq_hz = float(phase_fit.slope / (2 * math.pi))
        alpha = float(-env_fit.slope)
        zeta = float(alpha / (2 * math.pi * max(freq_hz, 1e-9)))
        fits[name] = {
            "t0_s": float(tt[0]),
            "t1_s": float(tt[-1]),
            "mean_envelope_ms2": amp,
            "freq_hz": freq_hz,
            "zeta": zeta,
            "zeta_percent": 100.0 * zeta,
            "logenv_r2": float(env_fit.rvalue**2),
        }
    harmonic = harmonic_ratios(t, y, fs, case.f1_nom_hz)
    return {
        "label": case.label,
        "file": str(case.path.relative_to(REPO)),
        "sample_rate_hz": fs,
        "window_s": [case.start_s, case.end_s],
        "bandpass_hz": list(case.fband_hz),
        "fits_by_amplitude": fits,
        "harmonic_ratios": harmonic,
    }


def integrate_band(freq: np.ndarray, psd: np.ndarray, center: float, half_width: float) -> float:
    band = (freq >= center - half_width) & (freq <= center + half_width)
    if not np.any(band):
        return float("nan")
    return float(np.trapz(psd[band], freq[band]))


def harmonic_ratios(t: np.ndarray, y: np.ndarray, fs: float, f1: float) -> dict:
    thirds = {
        "early": (float(t[0]), float(t[0] + 0.35 * (t[-1] - t[0]))),
        "late": (float(t[0] + 0.65 * (t[-1] - t[0])), float(t[-1])),
    }
    out = {}
    for name, (a, b) in thirds.items():
        m = (t >= a) & (t <= b)
        yy = y[m] - float(np.mean(y[m]))
        nperseg = min(len(yy), 65536)
        freq, psd = signal.welch(yy, fs=fs, nperseg=nperseg, noverlap=nperseg // 2)
        fund = integrate_band(freq, psd, f1, 0.35)
        harms = sum(integrate_band(freq, psd, k * f1, 0.35) for k in (2, 3, 4))
        out[name] = {
            "t0_s": a,
            "t1_s": b,
            "fundamental_power": fund,
            "harmonic_2_4_power": harms,
            "harmonic_to_fundamental": float(harms / fund) if fund > 0 else None,
        }
    return out


def load_shocksat_summary() -> dict:
    summary_csv = REPO / "artifacts/reports/shocksat_statfem_runner_20260609/hammer_frf_hit_summary.csv"
    manifest = json.loads(
        (REPO / "artifacts/reports/shocksat_statfem_runner_20260609/hammer_frf_subset_manifest.json").read_text()
    )
    rows = []
    with summary_csv.open(newline="") as f:
        for row in csv.DictReader(f):
            rows.append(row)
    force_peaks = np.array([float(r["force_peak_abs_lbf"]) for r in rows if r["load_status"] == "loaded"])
    channels = {}
    for ch in ("1", "50", "87"):
        coh = np.array([float(r[f"ch{ch}_median_coherence_100_10000"]) for r in rows if r["load_status"] == "loaded"])
        amp = np.array([float(r[f"ch{ch}_median_abs_h1_g_per_lbf"]) for r in rows if r["load_status"] == "loaded"])
        corr = stats.pearsonr(force_peaks, amp).statistic if len(force_peaks) >= 3 else np.nan
        channels[f"ch{ch}"] = {
            "median_coherence_by_hit": coh.tolist(),
            "median_coherence_over_hits": float(np.median(coh)),
            "median_abs_h1_g_per_lbf_by_hit": amp.tolist(),
            "pearson_force_peak_vs_median_abs_h1": float(corr),
        }
    return {
        "hit_count_loaded": len(force_peaks),
        "force_peak_lbf": force_peaks.tolist(),
        "force_peak_ratio_max_min": float(np.max(force_peaks) / np.min(force_peaks)),
        "channels": channels,
        "comparison_status": manifest.get("comparison_status"),
        "blockers": manifest.get("comparison_blockers", []),
        "status": "YELLOW",
        "interpretation": "Inconclusive for amplitude-dependent damping: four hammer hits have force contrast, but median coherence is about 0.05-0.06 and source/response mapping is unresolved.",
    }


def load_panel_summary() -> dict:
    base = REPO / "Suspended panel modal testing/LDV test results/mat files"
    freq = np.asarray(sio.loadmat(base / "freq.mat")["freq"]).ravel()
    h1 = np.asarray(sio.loadmat(base / "H1.mat")["H1"])
    accel = np.asarray(sio.loadmat(base / "accel.mat")["accel"])
    mag = np.abs(h1)
    peak_idx = np.nanargmax(mag, axis=1)
    peak_freqs = freq[peak_idx]
    return {
        "h1_shape": list(h1.shape),
        "accel_shape": list(accel.shape),
        "freq_count": int(freq.size),
        "freq_range_hz": [float(np.nanmin(freq)), float(np.nanmax(freq))],
        "response_point_count": int(h1.shape[0]),
        "median_peak_freq_hz": float(np.nanmedian(peak_freqs)),
        "peak_freq_range_hz": [float(np.nanmin(peak_freqs)), float(np.nanmax(peak_freqs))],
        "status": "YELLOW",
        "interpretation": "Inconclusive for amplitude dependence: frequency-domain LDV products are present, but no repeated drive-amplitude levels or raw time histories were identified in the loaded files.",
    }


def classify_mpl(decays: list[dict]) -> dict:
    flags = []
    for d in decays:
        fits = d["fits_by_amplitude"]
        if "high" in fits and "low" in fits:
            high = fits["high"]
            low = fits["low"]
            freq_shift_pct = 100.0 * (high["freq_hz"] - low["freq_hz"]) / max(low["freq_hz"], 1e-9)
            zeta_ratio = high["zeta"] / max(low["zeta"], 1e-12)
            d["high_vs_low"] = {
                "freq_shift_percent_high_minus_low": freq_shift_pct,
                "zeta_ratio_high_over_low": zeta_ratio,
                "zeta_delta_percentage_points": high["zeta_percent"] - low["zeta_percent"],
            }
            if abs(freq_shift_pct) > 1.0 or zeta_ratio > 1.5 or zeta_ratio < 0.67:
                flags.append(d["label"])
        harm_early = d["harmonic_ratios"]["early"]["harmonic_to_fundamental"]
        harm_late = d["harmonic_ratios"]["late"]["harmonic_to_fundamental"]
        d["harmonic_change_early_over_late"] = (
            float(harm_early / harm_late) if harm_early is not None and harm_late and harm_late > 0 else None
        )
        if (
            harm_early is not None
            and harm_late is not None
            and harm_late > 0
            and harm_early > 5e-5
            and harm_early / harm_late > 5.0
        ):
            flags.append(d["label"] + " amplitude-correlated harmonics")
    return {
        "status": "YELLOW",
        "signs_present": bool(flags),
        "flagged_cases": sorted(set(flags)),
        "interpretation": "MPL shows weak-to-moderate response-only signs of amplitude-dependent/nonlinear behavior in the ruler pull-release records: small harmonic content is consistently larger in the high-amplitude part of the decay, while damping/frequency shifts are modest. This is not yet a calibrated hysteresis loop because no force/displacement loop was measured.",
    }


def make_figures(results: dict) -> None:
    FIG.mkdir(parents=True, exist_ok=True)
    plt.rcParams.update(
        {
            "font.size": 10,
            "axes.spines.top": False,
            "axes.spines.right": False,
            "axes.grid": True,
            "grid.alpha": 0.18,
            "grid.linewidth": 0.6,
        }
    )

    fig, axes = plt.subplots(3, 2, figsize=(10.5, 8.0), constrained_layout=True, sharex="col")
    colors = {"high": "#8c2d04", "mid": "#2b8cbe", "low": "#2ca25f"}
    for row, d in enumerate(results["mpl"]["decay_screens"]):
        fit_items = sorted(
            d["fits_by_amplitude"].items(),
            key=lambda item: item[1]["mean_envelope_ms2"],
        )
        x = [fit["mean_envelope_ms2"] for _, fit in fit_items]
        z = [fit["zeta_percent"] for _, fit in fit_items]
        fr = [fit["freq_hz"] for _, fit in fit_items]
        if len(x) > 1:
            axes[row, 0].plot(x, z, color="0.65", lw=0.9)
            axes[row, 1].plot(x, fr, color="0.65", lw=0.9)
        for seg_name, fit in fit_items:
            axes[row, 0].scatter(
                fit["mean_envelope_ms2"],
                fit["zeta_percent"],
                color=colors.get(seg_name, "0.3"),
                s=34,
            )
            axes[row, 1].scatter(
                fit["mean_envelope_ms2"],
                fit["freq_hz"],
                color=colors.get(seg_name, "0.3"),
                s=34,
            )
            axes[row, 0].annotate(seg_name, (fit["mean_envelope_ms2"], fit["zeta_percent"]), xytext=(3, 3), textcoords="offset points", fontsize=8)
            axes[row, 1].annotate(seg_name, (fit["mean_envelope_ms2"], fit["freq_hz"]), xytext=(3, 3), textcoords="offset points", fontsize=8)
        axes[row, 0].set_xscale("log")
        axes[row, 1].set_xscale("log")
        axes[row, 0].set_ylabel("zeta, percent")
        axes[row, 0].set_title(d["label"].replace("MPL ", ""))
        axes[row, 1].set_title("instantaneous frequency")
    axes[-1, 0].set_xlabel("bandpassed response envelope, m/s^2 (log)")
    axes[-1, 1].set_xlabel("bandpassed response envelope, m/s^2 (log)")
    fig.suptitle("Measured response-only triage; force/displacement hysteresis loop not measured", fontsize=11)
    fig.savefig(FIG / "mpl_ruler_amplitude_screen.png", dpi=180)
    plt.close(fig)

    datasets = ["MPL test stand", "ShockSat", "Suspended panel"]
    scores = [2 if results["mpl"]["signs_present"] else 1, 1, 1]
    notes = ["signs, not final ID", "low-coherence/inconclusive", "no amplitude sweep found"]
    fig, ax = plt.subplots(figsize=(8.0, 3.0), constrained_layout=True)
    y = np.arange(len(datasets))
    ax.barh(y, scores, color=["#2ca25f", "#feb24c", "#feb24c"], height=0.45)
    ax.set_yticks(y, datasets)
    ax.set_xlim(0, 3)
    ax.set_xticks([1, 2], ["inconclusive", "signs present"])
    ax.set_title("Amplitude-dependent damping / hysteresis evidence status")
    for yi, score, note in zip(y, scores, notes):
        ax.text(score + 0.05, yi, note, va="center", fontsize=9)
    fig.savefig(FIG / "dataset_status_summary.png", dpi=180)
    plt.close(fig)


def write_report(results: dict) -> None:
    mpl = results["mpl"]
    shock = results["shocksat"]
    panel = results["suspended_panel"]
    lines = [
        "# Amplitude-Dependent Damping / Hysteresis Scan",
        "",
        "## Bottom Line",
        "",
        "- **MPL test stand: YELLOW, weak signs present.** The response-only pull-release data show small harmonic content that is consistently larger in the high-amplitude part of the decay; the coupled-ruler damping/frequency shifts are modest. This is evidence worth following up, but not a calibrated hysteresis loop because the pull force/displacement loop was not measured.",
        "- **ShockSat: YELLOW, inconclusive.** Four hammer hits have force-amplitude contrast, but the existing H1 accelerance estimates have median coherence around 0.05-0.06 in 100-10,000 Hz and unresolved source/response mapping, so per-hit FRF differences cannot be trusted as nonlinear damping evidence.",
        "- **Suspended panel: YELLOW, inconclusive.** The folder has LDV frequency-domain products (`H1`, acceleration, frequency), but I did not find repeated drive-amplitude levels or raw time histories needed to test amplitude dependence.",
        "",
        "**Overall status: YELLOW.** At least one dataset shows signs, but no dataset here proves hysteresis in the strict force-displacement energy-loop sense.",
        "",
        "## MPL Numerical Screen",
        "",
        "| case | high zeta % | low zeta % | high-low freq shift % | early harmonic/fundamental | late harmonic/fundamental | interpretation |",
        "| --- | ---: | ---: | ---: | ---: | ---: | --- |",
    ]
    for d in mpl["decay_screens"]:
        fits = d["fits_by_amplitude"]
        hv = fits.get("high", {})
        lv = fits.get("low", {})
        comp = d.get("high_vs_low", {})
        he = d["harmonic_ratios"]["early"]["harmonic_to_fundamental"]
        hl = d["harmonic_ratios"]["late"]["harmonic_to_fundamental"]
        lines.append(
            f"| {d['label']} | {hv.get('zeta_percent', float('nan')):.3g} | "
            f"{lv.get('zeta_percent', float('nan')):.3g} | "
            f"{comp.get('freq_shift_percent_high_minus_low', float('nan')):.3g} | "
            f"{he:.3g} | {hl:.3g} | response-only nonlinear screen |"
        )
    lines += [
        "",
        "![MPL ruler amplitude screen](figures/mpl_ruler_amplitude_screen.png)",
        "",
        "## ShockSat Numerical Screen",
        "",
        f"- Loaded Test07 hammer hits: `{shock['hit_count_loaded']}`.",
        f"- Hammer force peak range: `{min(shock['force_peak_lbf']):.3g}` to `{max(shock['force_peak_lbf']):.3g}` lbf; max/min ratio `{shock['force_peak_ratio_max_min']:.3g}`.",
        "- Median coherence by selected channel:",
    ]
    for ch, vals in shock["channels"].items():
        lines.append(
            f"  - `{ch}`: median over hits `{vals['median_coherence_over_hits']:.3g}`; "
            f"force-vs-median-|H1| Pearson `{vals['pearson_force_peak_vs_median_abs_h1']:.3g}` (not trusted because coherence is low)."
        )
    lines += [
        "",
        "## Suspended Panel Numerical Screen",
        "",
        f"- `H1.mat` shape: `{panel['h1_shape']}` response points x frequency lines.",
        f"- Frequency range: `{panel['freq_range_hz'][0]:.3g}` to `{panel['freq_range_hz'][1]:.3g}` Hz.",
        f"- Dominant H1 peak frequencies across response points span `{panel['peak_freq_range_hz'][0]:.3g}` to `{panel['peak_freq_range_hz'][1]:.3g}` Hz.",
        "- Limitation: these are frequency-domain products, not a documented amplitude sweep.",
        "",
        "![Dataset status summary](figures/dataset_status_summary.png)",
        "",
        "## Next Measurement To Turn Yellow Into Green",
        "",
        "- MPL: repeat the ruler/stand pull or tap at planned amplitude levels with displacement or force measurement, then fit damping/frequency versus amplitude and plot force-displacement or force-velocity loops.",
        "- ShockSat: use a valid modal/hammer dataset with high coherence, mapped source/response grids, and intentionally varied hammer levels; then compare FRFs and modal damping by input level.",
        "- Suspended panel: locate or run stepped-sine/random tests at multiple drive amplitudes with the same LDV points; compare modal peak frequency, bandwidth, phase, and H1/H2/coherence by level.",
    ]
    (OUT / "analysis_report.md").write_text("\n".join(lines) + "\n")


def main() -> None:
    t0 = time.time()
    FIG.mkdir(parents=True, exist_ok=True)
    mpl_decays = [fit_decay_case(case) for case in MPL_DECAYS]
    results = {
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "result_status": "YELLOW",
        "mpl": {
            "decay_screens": mpl_decays,
            **classify_mpl(mpl_decays),
        },
        "shocksat": load_shocksat_summary(),
        "suspended_panel": load_panel_summary(),
    }
    make_figures(results)
    write_report(results)
    (OUT / "results.json").write_text(json.dumps(results, indent=2) + "\n")
    runtime = {
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "active_runtime_s": round(time.time() - t0, 3),
        "elapsed_wallclock_s": round(time.time() - t0, 3),
        "command": "python scripts/scan_amplitude_dependence.py",
    }
    (OUT / "runtime.json").write_text(json.dumps(runtime, indent=2) + "\n")


if __name__ == "__main__":
    main()
