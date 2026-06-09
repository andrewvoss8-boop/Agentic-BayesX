#!/usr/bin/env python3
"""Opus corrected impact-hammer FRF processing for ShockSat Test07.

Why this exists
---------------
The Codex run computed coherence/FRF with Welch segmenting (nperseg=32768)
*inside a single ~1 s impact transient*. A single hammer hit has its energy in
one short window; the other ~14 Welch segments are free-decay/noise, so
magnitude-squared coherence collapses toward ~0.07. That number is a method
artifact, not a data-quality measurement.

This script does standard impact-FRF processing:
  * one analysis frame per hit, force window on the input + exponential window
    on the response;
  * one FFT per hit;
  * ensemble H1 and coherence ACROSS the 4 hits (the only correct axis for
    coherence on impact data);
  * per-hit FRF overlay (the honest few-hit quality metric = repeatability).

It also (a) re-runs the Codex per-transient-Welch coherence on the SAME data so
the contrast is explicit, and (b) parses the NASA SOL 111 free-free FEM FRF
(.pch) and compares FEM vs measured *resonance peak frequencies* in 10-400 Hz,
which is point/unit-independent for a free-free structure.

No StatFEM posterior, no NUTS. Outputs are labeled diagnostic.
"""
from __future__ import annotations

import io
import json
import re
import time
import zipfile
from pathlib import Path

import numpy as np
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from scipy import io as scipy_io
from scipy import signal

# ---------------------------------------------------------------------------
REPO = Path(__file__).resolve().parents[4]
CODEX = REPO / "artifacts/reports/shocksat_statfem_runner_20260609"
OUT = REPO / "artifacts/reports/shocksat_opus_20260609"
FIGS = OUT / "figures"
LOGS = OUT / "logs"
FIGS.mkdir(parents=True, exist_ok=True)
LOGS.mkdir(parents=True, exist_ok=True)

ARCHIVE = CODEX / "sources/Test07_ImpactHammer_990x.zip"
FALLBACK_MAT = CODEX / "extracted/Test07_ImpactHammer_990x"
PCH_11101X = CODEX / "extracted/FEM/Correlation/FRF_Verification/SOL_111_Free_Free_Force_11101X.pch"

FORCE_CH = 116
RESP_CH = [1, 50, 87]          # same channels Codex reported, for apples-to-apples
MODAL_BAND = (10.0, 400.0)     # NASA SOL 111 free-free correlation band
PLOT_BAND = (5.0, 2000.0)
t0 = time.time()
log_lines: list[str] = []


def log(msg: str) -> None:
    print(msg, flush=True)
    log_lines.append(msg)


# ---------------------------------------------------------------------------
# MAT loading (reuses the Codex Recorder{ch} convention)
# ---------------------------------------------------------------------------
def list_hits() -> list[dict]:
    hits = []
    if ARCHIVE.exists() and zipfile.is_zipfile(ARCHIVE):
        with zipfile.ZipFile(ARCHIVE) as zf:
            for m in sorted(n for n in zf.namelist() if n.lower().endswith(".mat")):
                hits.append({"kind": "zip", "member": m})
    if not hits and FALLBACK_MAT.exists():
        for p in sorted(FALLBACK_MAT.glob("*.mat")):
            hits.append({"kind": "file", "path": str(p)})
    return hits


def load_recorders(hit: dict, channels: list[int]) -> dict:
    names = [f"Recorder{c}" for c in channels]
    if hit["kind"] == "zip":
        with zipfile.ZipFile(ARCHIVE) as zf:
            payload = zf.read(hit["member"])
        return scipy_io.loadmat(io.BytesIO(payload), squeeze_me=True,
                                struct_as_record=False, variable_names=names)
    return scipy_io.loadmat(hit["path"], squeeze_me=True,
                            struct_as_record=False, variable_names=names)


def recorder_sample(mat: dict, ch: int):
    rec = mat.get(f"Recorder{ch}")
    if rec is None:
        return None
    try:
        data = rec.Channels.Segments.Data
        s = np.asarray(data.Samples, dtype=float)
        dx = float(data.dXstep)
        return {"samples": s, "fs": 1.0 / dx if dx else None}
    except Exception:
        return None


# ---------------------------------------------------------------------------
# Impact windowing
# ---------------------------------------------------------------------------
def force_window(n: int, peak: int, fs: float, pre_ms=1.0, dur_ms=15.0) -> np.ndarray:
    """Cosine-tapered force window: pass the pulse, zero the rest."""
    pre = int(pre_ms * 1e-3 * fs)
    dur = int(dur_ms * 1e-3 * fs)
    w = np.zeros(n)
    a = max(0, peak - pre)
    b = min(n, peak - pre + dur)
    seg = b - a
    if seg <= 4:
        w[a:b] = 1.0
        return w
    taper = signal.windows.tukey(seg, alpha=0.5)
    w[a:b] = taper
    return w


def expo_window(n: int, fs: float, end_frac=0.05) -> np.ndarray:
    """Exponential decay window over the analysis frame (adds known damping)."""
    t = np.arange(n) / fs
    tau = (n / fs) / (-np.log(end_frac))
    return np.exp(-t / tau)


# ---------------------------------------------------------------------------
# Parse NASA SOL 111 .pch acceleration FRF (magnitude-phase, units g)
# ---------------------------------------------------------------------------
def parse_pch_frf(path: Path) -> dict:
    """Return {point_id: (freq[Hz], complex Tx-accel FRF)} for the X (T1) DOF."""
    if not path.exists():
        return {}
    out: dict[int, dict[str, list]] = {}
    cur_pt = None
    buf: list[float] = []
    cur_freq = None

    def flush():
        nonlocal buf, cur_freq, cur_pt
        if cur_pt is None or cur_freq is None or len(buf) < 7:
            buf = []
            return
        # buf order: magT1,magT2,magT3, magR1,magR2,magR3,
        #            phaT1,phaT2,phaT3, phaR1,phaR2,phaR3 (deg)
        magT1, phaT1 = buf[0], buf[6]
        val = magT1 * np.exp(1j * np.deg2rad(phaT1))
        out.setdefault(cur_pt, {"f": [], "h": []})
        out[cur_pt]["f"].append(cur_freq)
        out[cur_pt]["h"].append(val)
        buf = []

    with open(path) as fh:
        for line in fh:
            if line.startswith("$POINT ID"):
                flush()
                m = re.search(r"\$POINT ID\s*=\s*(\d+)", line)
                cur_pt = int(m.group(1)) if m else None
                cur_freq = None
                buf = []
                continue
            if line.startswith("$"):
                continue
            body = line[:72] if line.startswith("-CONT-") else line[:72]
            nums = re.findall(r"[-+]?\d+\.\d+E[-+]?\d+", body)
            if line.lstrip().startswith("-CONT-"):
                buf.extend(float(x) for x in nums)
            else:
                # data line: freq  G  v1 v2 v3   (the 'G' token splits)
                flush()
                toks = line.split()
                try:
                    cur_freq = float(toks[0])
                except (ValueError, IndexError):
                    cur_freq = None
                buf = [float(x) for x in nums[1:]] if nums else []
        flush()

    result = {}
    for pt, d in out.items():
        f = np.asarray(d["f"])
        h = np.asarray(d["h"])
        order = np.argsort(f)
        result[pt] = (f[order], h[order])
    return result


def find_peaks_band(f: np.ndarray, mag: np.ndarray, band, prom_db=3.0, top=12):
    m = (f >= band[0]) & (f <= band[1])
    fb, mb = f[m], mag[m]
    if fb.size < 5:
        return []
    logm = 20 * np.log10(np.maximum(mb, 1e-30))
    idx, props = signal.find_peaks(logm, prominence=prom_db,
                                   distance=max(1, int(0.01 * fb.size)))
    if idx.size == 0:
        return []
    order = np.argsort(props["prominences"])[::-1][:top]
    pk = sorted(float(fb[i]) for i in idx[order])
    return pk


# ===========================================================================
log(f"REPO={REPO}")
log(f"archive exists={ARCHIVE.exists()} pch exists={PCH_11101X.exists()}")
hits = list_hits()
log(f"hits found: {len(hits)}")

# --- load each hit, build per-hit frames -----------------------------------
fs = None
common = None  # common frequency grid for plotting/ensemble
hit_records = []
for hi, hit in enumerate(hits):
    mat = load_recorders(hit, [FORCE_CH] + RESP_CH)
    fsamp = recorder_sample(mat, FORCE_CH)
    if fsamp is None:
        log(f"hit {hi}: force recorder missing, skip")
        continue
    fsv = fsamp["fs"]
    fs = fsv if fs is None else fs
    force_full = fsamp["samples"].astype(float)
    n = force_full.size
    force_full = force_full - np.mean(force_full[: min(1000, n)])
    peak = int(np.argmax(np.abs(force_full)))
    resp = {}
    for c in RESP_CH:
        rs = recorder_sample(mat, c)
        if rs is None:
            continue
        y = rs["samples"].astype(float)
        y = y - np.mean(y[: min(1000, n)])
        resp[c] = y[:n]
    hit_records.append({"peak": peak, "n": n, "fs": fsv,
                        "force": force_full, "resp": resp,
                        "peak_force": float(np.max(np.abs(force_full)))})
    log(f"hit {hi}: fs={fsv:.0f} n={n} peak@{peak/fsv*1e3:.1f}ms "
        f"Fpk={hit_records[-1]['peak_force']:.3f} lbf")

if not hit_records:
    raise SystemExit("no usable hits")

# common analysis frame length = min available after (peak - pre)
PRE_MS = 1.0
pre = int(PRE_MS * 1e-3 * fs)
L = min(r["n"] - max(0, r["peak"] - pre) for r in hit_records)
# cap frame so df is reasonable and runtime small; keep >= 0.2 s
L = int(min(L, 0.6 * fs))
df = fs / L
log(f"common frame L={L} samples ({L/fs:.3f}s), df={df:.2f} Hz, fs={fs:.0f}")

freqs = np.fft.rfftfreq(L, d=1.0 / fs)
fwin_dummy = None
ewin = expo_window(L, fs)

# --- METHOD B (Opus, correct): per-hit windowed FFT, ensemble H1 -----------
F_hits = []                    # force spectra per hit
Y_hits = {c: [] for c in RESP_CH}
H_hits = {c: [] for c in RESP_CH}
for r in hit_records:
    start = max(0, r["peak"] - pre)
    fw = force_window(r["n"], r["peak"], fs)
    f_fr = (r["force"] * fw)[start:start + L]
    if f_fr.size < L:
        f_fr = np.pad(f_fr, (0, L - f_fr.size))
    F = np.fft.rfft(f_fr)
    F_hits.append(F)
    for c, y in r["resp"].items():
        y_fr = (y * 1.0)[start:start + L]
        if y_fr.size < L:
            y_fr = np.pad(y_fr, (0, L - y_fr.size))
        y_fr = y_fr * ewin
        Y = np.fft.rfft(y_fr)
        Y_hits[c].append(Y)
        with np.errstate(divide="ignore", invalid="ignore"):
            H_hits[c].append(Y / F)

F_arr = np.array(F_hits)
ens = {}
for c in RESP_CH:
    if not Y_hits[c]:
        continue
    Y_arr = np.array(Y_hits[c])
    Sff = np.mean(np.abs(F_arr) ** 2, axis=0)
    Syy = np.mean(np.abs(Y_arr) ** 2, axis=0)
    Sfy = np.mean(np.conj(F_arr) * Y_arr, axis=0)
    with np.errstate(divide="ignore", invalid="ignore"):
        H1 = Sfy / Sff
        coh = np.abs(Sfy) ** 2 / (Sff * Syy)
    ens[c] = {"H1": H1, "coh": coh}

# --- METHOD A (Codex reproduction): per-transient Welch coherence -----------
nperseg = 32768
codex_coh = {}
for c in RESP_CH:
    cohs = []
    for r in hit_records:
        if c not in r["resp"]:
            continue
        seg = min(nperseg, r["n"])
        fA, cA = signal.coherence(r["force"], r["resp"][c], fs=fs,
                                   window="hann", nperseg=seg,
                                   noverlap=seg // 2, detrend=False)
        cohs.append((fA, cA))
    codex_coh[c] = cohs


def band_median_coh(fgrid, cvals, band):
    m = (fgrid >= band[0]) & (fgrid <= band[1]) & np.isfinite(cvals)
    return float(np.nanmedian(cvals[m])) if np.any(m) else float("nan")


# --- FEM SOL111 reference + peak comparison --------------------------------
fem = parse_pch_frf(PCH_11101X)
fem_peaks = []
fem_curve = None
if fem:
    # average |FRF| magnitude over response points -> a global FEM FRF proxy
    fgrid = None
    mags = []
    for pt, (ff, hh) in fem.items():
        if fgrid is None:
            fgrid = ff
        if ff.shape == fgrid.shape and np.allclose(ff, fgrid):
            mags.append(np.abs(hh))
    if mags:
        fem_mag = np.sqrt(np.mean(np.array(mags) ** 2, axis=0))  # RMS over points
        fem_curve = (fgrid, fem_mag)
        fem_peaks = find_peaks_band(fgrid, fem_mag, MODAL_BAND)
    log(f"FEM SOL111 points parsed={len(fem)}; FEM modal peaks (Hz)={['%.1f'%p for p in fem_peaks]}")

# test peaks from ensemble H1 (use ch with strongest modal response)
test_peaks = {}
for c in RESP_CH:
    if c in ens:
        test_peaks[c] = find_peaks_band(freqs, np.abs(ens[c]["H1"]), MODAL_BAND)
log(f"test modal peaks per channel (Hz): "
    f"{ {c:['%.1f'%p for p in v] for c,v in test_peaks.items()} }")

# ===========================================================================
# FIGURES
# ===========================================================================
pmask = (freqs >= PLOT_BAND[0]) & (freqs <= PLOT_BAND[1])

# Fig 1: per-hit FRF repeatability (ch1)
fig, ax = plt.subplots(figsize=(9, 5))
cref = RESP_CH[0]
for hi, H in enumerate(H_hits[cref]):
    ax.semilogx(freqs[pmask], 20 * np.log10(np.abs(H[pmask]) + 1e-12),
                lw=0.8, alpha=0.7, label=f"hit {hi+1}")
ax.semilogx(freqs[pmask], 20 * np.log10(np.abs(ens[cref]["H1"][pmask]) + 1e-12),
            lw=1.8, color="k", label="ensemble H1")
ax.axvspan(MODAL_BAND[0], MODAL_BAND[1], color="C2", alpha=0.08,
           label="SOL111 modal band 10-400 Hz")
ax.set_xlabel("frequency (Hz, log)")
ax.set_ylabel("|accelerance| (dB ref 1 g/lbf)")
ax.set_title(f"Opus per-hit impact FRF repeatability — ch{cref} (grid 9900001, X)")
ax.legend(fontsize=8, ncol=2)
ax.grid(True, which="both", alpha=0.3)
fig.tight_layout()
fig.savefig(FIGS / "opus_frf_repeatability_ch1.png", dpi=160)
plt.close(fig)

# Fig 2: coherence — Method A (Codex) vs Method B (Opus), ch1
fig, ax = plt.subplots(figsize=(9, 5))
for hi, (fA, cA) in enumerate(codex_coh[cref]):
    mA = (fA >= PLOT_BAND[0]) & (fA <= PLOT_BAND[1])
    ax.semilogx(fA[mA], cA[mA], color="C3", lw=0.6, alpha=0.4,
                label="Method A: per-transient Welch (Codex)" if hi == 0 else None)
ax.semilogx(freqs[pmask], ens[cref]["coh"][pmask], color="C0", lw=1.6,
            label="Method B: per-hit ensemble across 4 hits (Opus)")
ax.axhline(0.8, color="0.4", ls="--", lw=0.9, label="0.8 reference")
ax.axvspan(MODAL_BAND[0], MODAL_BAND[1], color="C2", alpha=0.08)
ax.set_ylim(0, 1.05)
ax.set_xlabel("frequency (Hz, log)")
ax.set_ylabel("magnitude-squared coherence")
ax.set_title(f"Coherence method artifact vs corrected — ch{cref}")
ax.legend(fontsize=8)
ax.grid(True, which="both", alpha=0.3)
fig.tight_layout()
fig.savefig(FIGS / "opus_coherence_method_compare_ch1.png", dpi=160)
plt.close(fig)

# Fig 3: FEM vs test resonance-frequency alignment (10-400 Hz)
fig, ax = plt.subplots(figsize=(9, 5))
if fem_curve is not None:
    fg, fm = fem_curve
    mfem = (fg >= MODAL_BAND[0]) & (fg <= MODAL_BAND[1])
    fmn = fm[mfem] / np.nanmax(fm[mfem])
    ax.semilogx(fg[mfem], 20 * np.log10(fmn + 1e-6), color="C1", lw=1.4,
                label="FEM SOL111 11101X (RMS over pts, normalized)")
mtm = (freqs >= MODAL_BAND[0]) & (freqs <= MODAL_BAND[1])
th = np.abs(ens[cref]["H1"])[mtm]
thn = th / np.nanmax(th)
ax.semilogx(freqs[mtm], 20 * np.log10(thn + 1e-6), color="C0", lw=1.2,
            label=f"measured hammer FRF ch{cref} (normalized)")
for p in fem_peaks:
    ax.axvline(p, color="C1", ls=":", lw=0.8, alpha=0.7)
for p in test_peaks.get(cref, []):
    ax.axvline(p, color="C0", ls="--", lw=0.8, alpha=0.7)
ax.set_xlabel("frequency (Hz, log)")
ax.set_ylabel("normalized magnitude (dB)")
ax.set_title("FEM vs measured resonance-frequency alignment (NOT point/unit matched)")
ax.legend(fontsize=8)
ax.grid(True, which="both", alpha=0.3)
fig.tight_layout()
fig.savefig(FIGS / "opus_fem_vs_test_peaks.png", dpi=160)
plt.close(fig)

# ===========================================================================
# SUMMARY JSON
# ===========================================================================
summary = {
    "generated_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    "purpose": "corrected impact-hammer FRF for ShockSat Test07; tests Codex 'low coherence' verdict",
    "n_hits": len(hit_records),
    "fs_sps": fs,
    "frame_len_samples": int(L),
    "freq_resolution_hz": float(df),
    "modal_band_hz": list(MODAL_BAND),
    "force_channel": FORCE_CH,
    "response_channels": RESP_CH,
    "method_A_codex_per_transient_welch": {
        c: {"per_hit_median_coh_10_400": [band_median_coh(fA, cA, MODAL_BAND)
                                          for (fA, cA) in codex_coh[c]]}
        for c in RESP_CH
    },
    "method_B_opus_ensemble": {
        c: {
            "median_coh_10_400": band_median_coh(freqs, ens[c]["coh"], MODAL_BAND),
            "max_coh_10_400": float(np.nanmax(ens[c]["coh"][(freqs >= MODAL_BAND[0]) & (freqs <= MODAL_BAND[1])])),
            "frac_coh_ge_0p8_10_400": float(np.mean(
                ens[c]["coh"][(freqs >= MODAL_BAND[0]) & (freqs <= MODAL_BAND[1])] >= 0.8)),
            "frac_coh_ge_0p9_10_400": float(np.mean(
                ens[c]["coh"][(freqs >= MODAL_BAND[0]) & (freqs <= MODAL_BAND[1])] >= 0.9)),
            "test_modal_peaks_hz": test_peaks.get(c, []),
        }
        for c in RESP_CH if c in ens
    },
    "fem_sol111_11101X": {
        "points_parsed": len(fem),
        "modal_peaks_hz": fem_peaks,
        "units": "g per applied SOL111 load (force amplitude normalization = OPEN; see notes)",
    },
    "caveats": [
        "Only 4 hits at slightly different impact points (TestLog y=8.0-8.75, z=0-1) -> ensemble "
        "coherence has weak statistical power and point variation; per-hit repeatability is the "
        "primary few-hit quality metric.",
        "Exponential response window adds known artificial damping (lowers Q, raises inter-mode "
        "floor); acceptable for peak-location/diagnostic, not for damping extraction.",
        "FEM vs test overlay is resonance-frequency alignment only; response points (FEM 1101 vs "
        "test 9900001) and force amplitude units are NOT yet matched -> no magnitude likelihood.",
        "df ~ %.1f Hz at this frame length merges closely-spaced modes; refine frame for final." % df,
    ],
    "not_claimed": ["StatFEM posterior", "NUTS/HMC active", "validated FEM-test magnitude agreement",
                    "FRF likelihood readiness"],
}
(OUT / "opus_frf_summary.json").write_text(json.dumps(summary, indent=2))
np.savez_compressed(OUT / "opus_frf_estimates.npz",
                    freqs=freqs,
                    **{f"H1_ch{c}": ens[c]["H1"] for c in ens},
                    **{f"coh_ch{c}": ens[c]["coh"] for c in ens})
(LOGS / "run_log.txt").write_text("\n".join(log_lines))

# Headline numbers to stdout
log("\n=== HEADLINE: median coherence in 10-400 Hz ===")
for c in RESP_CH:
    if c not in ens:
        continue
    a = np.nanmedian([band_median_coh(fA, cA, MODAL_BAND) for (fA, cA) in codex_coh[c]])
    b = summary["method_B_opus_ensemble"][c]["median_coh_10_400"]
    mx = summary["method_B_opus_ensemble"][c]["max_coh_10_400"]
    log(f"ch{c}: Method A (Codex per-transient) ~{a:.3f}  |  "
        f"Method B (Opus ensemble) median {b:.3f}, max {mx:.3f}")
log(f"\nFEM peaks (Hz): {['%.1f'%p for p in fem_peaks]}")
log(f"runtime_s={time.time()-t0:.1f}")

runtime = {"active_runtime_s": round(time.time() - t0, 2),
           "elapsed_wallclock_s": round(time.time() - t0, 2)}
(OUT / "runtime.json").write_text(json.dumps(runtime, indent=2))
log("DONE")
