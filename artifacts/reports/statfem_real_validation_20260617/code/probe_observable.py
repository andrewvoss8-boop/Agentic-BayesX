#!/usr/bin/env python3
"""Observable-investigation probe (Task card A, Phase P1, Decision #1).

Question this script answers (artifact-backed, replayable):
  Is the REAL ShockSat impact-hammer FRF a usable matched-path likelihood in the FEM band
  (45-260 Hz), or must we fall back to modal synthesis from the .ash measured modes?

It compares, for the 3 precomputed diagnostic channels (DAQ 1, 50, 87):
  (1) the PRIOR processing = scipy Welch/csd H1 with nperseg=32768 over a single ~1 s impact
      transient (what the prior runner stored as `frf_likelihood_ready=False`, coherence ~0.06); vs
  (2) a PROPER single-impact FRF = force-windowed FFT of force + exponential-windowed FFT of response,
      H1 = Y(f)/F(f) for the single hit, no Welch-over-one-transient averaging.
  We then check how well each product's peaks in 45-260 Hz align with the 33 `.ash` measured modes.

It also reports the hard DATA-AVAILABILITY facts that bound any raw-FRF observable:
  - how many raw response channels exist in hit-001, the force channel, fs, record length;
  - that only 1 of 4 hammer hits is present as raw data locally (the other 3 are summary-only).

Outputs: out/observable_investigation.json  (numbers cited in decisions_log.md D1).
NO calibration, NO NUTS here -- this is the evidence for the SURFACED observable decision.

Run:  ../../.venv_nuts/bin/python code/probe_observable.py
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import scipy.io as sio
from scipy.signal import find_peaks

WS = Path(__file__).resolve().parent.parent
RUNNER = WS.parent / "shocksat_statfem_runner_20260609"
MAT = RUNNER / "extracted/Test07_ImpactHammer_990x/Test07_impacthammer_990x_001_5_20_2021_2_32_37 PM.mat"
NPZ = RUNNER / "hammer_frf_estimates.npz"
TWIN = WS.parent / "shocksat_fem_modal_twin_20260609"

# 33 measured modal frequencies from the .ash (measured_modes_summary.json), the fallback truth
ASH = np.array([54.1909, 69.983, 74.9858, 85.7784, 107.0258, 117.6292, 118.5329, 125.0336,
                137.2454, 142.4419, 151.1867, 158.1749, 165.8802, 167.9877, 172.2596, 174.7749,
                184.3618, 188.6368, 190.2195, 195.7229, 197.8154, 198.8568, 203.0143, 213.9135,
                222.173, 230.7075, 232.6665, 234.2201, 235.3072, 236.1028, 243.9353, 254.2315, 256.7855])
BAND = (45.0, 260.0)
RESP_RECORDER = {"ch1": 1, "ch50": 50, "ch87": 87}
FORCE_RECORDER = 116


def band_mask(f):
    return (f >= BAND[0]) & (f <= BAND[1])


def peak_align(freqs, mag, n=8):
    """Top-n |mag| peaks in band and each peak's nearest-.ash-mode abs error [Hz]."""
    m = band_mask(freqs)
    fb, mb = freqs[m], mag[m]
    if mb.size < 3:
        return [], []
    pks, _ = find_peaks(mb, prominence=mb.max() * 0.05)
    if pks.size == 0:
        return [], []
    top = sorted(pks[np.argsort(mb[pks])[::-1][:n]])
    pf = fb[top].tolist()
    err = [float(np.min(np.abs(p - ASH))) for p in pf]
    return [float(x) for x in pf], err


def prior_welch_summary():
    """Read the prior runner's stored Welch H1/coherence (the not-likelihood-ready product)."""
    z = np.load(NPZ, allow_pickle=True)
    f = z["frequency_hz"]
    out = {"df_hz": float(f[1] - f[0]), "fmax_hz": float(f[-1]), "n_pts_in_band": int(band_mask(f).sum())}
    for ch in ("001", "050", "087"):
        coh = z[f"ch{ch}_coherence_mean"]
        H = z[f"ch{ch}_h1_mean_real_g_per_lbf"] + 1j * z[f"ch{ch}_h1_mean_imag_g_per_lbf"]
        m = band_mask(f)
        pf, err = peak_align(f, np.abs(H))
        out[f"ch{ch}"] = {
            "coh_median_band": float(np.median(coh[m])),
            "coh_max_band": float(coh[m].max()),
            "frac_coh_ge_0p5": float((coh[m] > 0.5).mean()),
            "frac_coh_ge_0p8": float((coh[m] > 0.8).mean()),
            "peaks_hz": pf, "peak_ash_err_hz": err,
        }
    return out


def single_impact_summary(N=131072, force_win_ms=2.0, exp_decay_blocks=8.0):
    """Reprocess hit-001 as a single-impact FRF (no Welch-over-one-transient)."""
    recs = [f"Recorder{FORCE_RECORDER}"] + [f"Recorder{r}" for r in RESP_RECORDER.values()]
    d = sio.loadmat(str(MAT), variable_names=recs, struct_as_record=False, squeeze_me=True)
    fs = 1.0 / 4e-6

    def samp(r):
        return np.asarray(d[f"Recorder{r}"].Channels.Segments.Data.Samples, float)

    F = samp(FORCE_RECORDER)
    ip = int(np.argmax(np.abs(F)))
    start = max(0, ip - 200)
    sl = slice(start, start + N)
    pk = ip - start
    half = int(force_win_ms * 1e-3 * fs)
    fwin = np.zeros(N)
    fwin[max(0, pk - half):pk + half] = 1.0          # rectangular force window around the pulse
    ewin = np.exp(-np.arange(N) / (N / exp_decay_blocks))  # exponential window on the response
    freqs = np.fft.rfftfreq(N, 1 / fs)
    Ff = np.fft.rfft(F[sl] * fwin)
    out = {"fs_sps": float(fs), "block_N": int(N), "df_hz": float(freqs[1] - freqs[0]),
           "force_peak_lbf": float(F[ip]), "force_peak_time_s": float(ip / fs),
           "force_window_ms": force_win_ms, "exp_decay_blocks": exp_decay_blocks}
    for lbl, r in RESP_RECORDER.items():
        y = samp(r)[sl] * ewin
        H = np.fft.rfft(y) / Ff
        pf, err = peak_align(freqs, np.abs(H))
        out[lbl] = {"peaks_hz": pf, "peak_ash_err_hz": err,
                    "median_peak_ash_err_hz": float(np.median(err)) if err else None}
    return out


def data_availability():
    info = sio.whosmat(str(MAT))
    n_rec = len(info)
    # which of the 4 hits are present as raw .mat locally
    hdir = MAT.parent
    raw_hits = sorted(p.name for p in hdir.glob("*.mat"))
    return {
        "raw_mat_present": MAT.name,
        "n_recorders_in_hit001": int(n_rec),
        "raw_hits_present_locally": raw_hits,
        "n_raw_hits_present": len(raw_hits),
        "n_hits_referenced_in_summary": 4,
        "n_channels_with_precomputed_frf": 3,
        "n_channels_in_instrumentation_map": 326,
        "note": ("Held-out-sensor MC over impact-location x split x hit needs many channels and "
                 "multiple impacts/hits; raw FRF supports ~127 channels but only 1 impact/hit."),
    }


def main():
    res = {
        "purpose": "Decision #1 observable resolution: matched-path real FRF vs modal-synthesis fallback",
        "band_hz": list(BAND),
        "n_ash_modes": int(ASH.size),
        "prior_welch_product": prior_welch_summary(),
        "single_impact_reprocess": single_impact_summary(),
        "data_availability": data_availability(),
    }
    outdir = WS / "out"
    outdir.mkdir(exist_ok=True)
    (outdir / "observable_investigation.json").write_text(json.dumps(res, indent=2))
    # console headline
    print("PRIOR Welch coherence in 45-260 Hz (median / max / frac>=0.5):")
    for ch in ("001", "050", "087"):
        c = res["prior_welch_product"][f"ch{ch}"]
        print(f"  ch{ch}: {c['coh_median_band']:.3f} / {c['coh_max_band']:.3f} / {c['frac_coh_ge_0p5']:.2f}")
    print("SINGLE-IMPACT reprocess median peak->.ash-mode error [Hz]:")
    for lbl in RESP_RECORDER:
        s = res["single_impact_reprocess"][lbl]
        print(f"  {lbl}: {s['median_peak_ash_err_hz']:.1f}  peaks={['%.0f' % p for p in s['peaks_hz']]}")
    da = res["data_availability"]
    print(f"DATA: {da['n_recorders_in_hit001']} recorders in hit-001; "
          f"{da['n_raw_hits_present']}/4 raw hits present; "
          f"{da['n_channels_with_precomputed_frf']}/326 channels with FRF.")
    print("wrote out/observable_investigation.json")


if __name__ == "__main__":
    main()
