#!/usr/bin/env python3
"""EXPLORATORY (not a formal study): bandwidth / resolution scan of the raw Test07 +X impact records.

QUESTION (Andrew, 2026-07-14): how HIGH in frequency and how FINE in resolution can honestly
re-distilled FRFs go, using raw data we already own? Feeds the sub-200-Hz amplitude-trained runner card.

What this measures, per hit (4 hits, 128 recorders, fs from file):
  A. Record geometry: fs, record length, impact time, pre-trigger noise segment, force-channel status.
  B. SNR vs frequency: post-impact response PSD / pre-impact noise PSD, per channel; median + 25th pct
     across channels -> usable EXCITATION ceiling (where hammer energy dies into the noise floor).
  C. Cross-hit spectral coherence: hits are the averaged realizations (n=4, small-n bias noted);
     reference = top-energy channel -> where the response is repeatable structure vs noise.
  D. Ring-down duration per octave band (Hilbert envelope vs band noise floor) vs available record
     length -> which one binds the usable frame length -> achievable frequency spacing df = 1/T.
  E. Damping resolvability: for each sub-200 survey mode, half-power bandwidth = 2*zeta*f (survey zeta);
     count modes with >= 3 lines across the half-power band at achievable df vs at the current 2 Hz.

CAVEATS (stated up front): Test07 force channel is DEAD (established 2026-07-13 run) -> response-only;
excitation ceiling is inferred from response SNR, not input-referenced coherence. One drive (+X) only —
other drives' raw records may differ; treat the ceiling as a lower-bound existence proof, not a fleet spec.
Outputs: bandwidth_scan.json + fig_bandwidth_scan.png (both in scratch_test07/).
"""
import os, glob, json
import numpy as np
import scipy.io as sio
from scipy import signal

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, ".."))
MATS = sorted(glob.glob(os.path.join(HERE, "Test07_impacthammer_990x_0*.mat")))
mm = np.load(os.path.join(ROOT, "artifacts/reports/shocksat_fem_remesh_20260618/measured_modes.npz"))
mfreq = np.asarray(mm["freqs"], float)
mdamp = np.asarray(mm["damp"], float) / 100.0     # percent -> ratio (same convention as damp_id.py D7)

FS_TARGET = 12800.0        # decimated rate for all spectral work (Nyquist 6.4 kHz >> any plausible ceiling)
SNR_DB_GATE = 10.0         # "usable" = median SNR above this
COH_GATE = 0.90            # cross-hit coherence gate (n=4 -> pure-noise bias ~0.25, so 0.90 is safe)
OCT_EDGES = [45, 90, 180, 355, 710, 1400, 2800, 5600]   # octave-ish bands for ring-down timing


def load_hit(path):
    """Return dict: fs, accel (nch x n), names, impact index, force-channel report."""
    m = sio.loadmat(path, squeeze_me=True, struct_as_record=False)
    fs = None,
    acc, names, force_rep = [], [], []
    for i in range(1, 129):
        key = f"Recorder{i}"
        if key not in m:
            continue
        r = m[key]
        ci = r.Channels.ChannelInfos.ChannelInfo
        d = r.Channels.Segments.Data
        f = 1.0 / float(np.atleast_1d(d.dXstep).ravel()[0])
        x = np.asarray(d.Samples, float).ravel()
        yu = str(ci.YUnits).strip().lower()
        if yu == "g":
            fs = f
            acc.append(x)
            names.append(str(ci.Name))
        else:
            force_rep.append((str(ci.Name), yu, float(np.std(x)), float(np.abs(x).max())))
    A = np.array(acc)
    imp = int(np.argmax(np.abs(A[np.argmax(A.var(axis=1))])))
    return dict(fs=fs, A=A, names=names, imp=imp, force=force_rep, n=A.shape[1])


def welch_psd(x, fs, nperseg):
    f, p = signal.welch(x, fs=fs, nperseg=nperseg, noverlap=nperseg // 2, detrend="constant")
    return f, p


results = dict(hits=[], caveats=["Test07 force channel dead -> response-only; ceiling inferred from "
                                 "response SNR, not input-referenced coherence",
                                 "one drive (+X); n=4 hits for coherence (pure-noise bias ~1/n=0.25)"])
DEC = {}      # per-hit decimated accel matrices, aligned at impact
fs = None
for path in MATS:
    hid = os.path.basename(path).split("_")[3]
    h = load_hit(path)
    fs = h["fs"]
    q = int(round(fs / FS_TARGET))
    fs_d = fs / q
    pre_s = h["imp"] / fs
    rec_s = h["n"] / fs
    post_s = rec_s - pre_s
    print(f"hit {hid}: fs={fs:.0f} Hz, record {rec_s:.3f} s, impact at {pre_s*1000:.1f} ms, "
          f"post-impact {post_s:.3f} s, {h['A'].shape[0]} accel ch", flush=True)
    for nm, yu, sd, mx in h["force"]:
        print(f"    non-g channel: {nm} [{yu}] std={sd:.3g} max|x|={mx:.3g}", flush=True)
    # decimate all channels (whole record, then split at impact)
    Ad = np.array([signal.decimate(x, q, ftype="fir", zero_phase=True) for x in h["A"]])
    imp_d = int(h["imp"] / q)
    DEC[hid] = dict(Ad=Ad, imp=imp_d, fs=fs_d)
    results["hits"].append(dict(hit=hid, fs=fs, record_s=rec_s, pre_trigger_s=pre_s,
                                post_impact_s=post_s, n_accel=h["A"].shape[0],
                                force_channels=[dict(name=n, units=u, std=s, absmax=m)
                                                for n, u, s, m in h["force"]]))
    del h

fs_d = DEC[list(DEC)[0]]["fs"]

# ---------------------------------------------------------------- B. SNR vs frequency (per hit, all ch)
print("\n--- SNR vs frequency ---", flush=True)
nper_noise = 2048          # pre-trigger is short; coarse df ok for a noise FLOOR
nper_sig = 4096
snr_med, snr_q25 = {}, {}
fgrid = None
for hid, d in DEC.items():
    Ad, imp = d["Ad"], d["imp"]
    if imp < nper_noise + 64:
        print(f"hit {hid}: pre-trigger too short for noise PSD ({imp} samples) -> skipped", flush=True)
        continue
    snrs = []
    for x in Ad:
        fN, pN = welch_psd(x[:imp - 32], fs_d, min(nper_noise, imp - 64))
        fS, pS = welch_psd(x[imp:], fs_d, nper_sig)
        pN_i = np.interp(fS, fN, pN)
        snrs.append(10 * np.log10((pS + 1e-30) / (pN_i + 1e-30)))
    snrs = np.array(snrs)
    fgrid = fS
    snr_med[hid] = np.median(snrs, axis=0)
    snr_q25[hid] = np.percentile(snrs, 25, axis=0)

snr_med_all = np.median(np.array(list(snr_med.values())), axis=0)
snr_q25_all = np.median(np.array(list(snr_q25.values())), axis=0)
# ceiling = highest f below which median SNR stays >= gate (allow isolated dips via 5-bin smoothing)
sm = np.convolve(snr_med_all, np.ones(5) / 5, mode="same")
ok = np.where((fgrid > 40) & (sm >= SNR_DB_GATE))[0]
ceiling_med = float(fgrid[ok].max()) if len(ok) else float("nan")
ok25 = np.where((fgrid > 40) & (np.convolve(snr_q25_all, np.ones(5) / 5, "same") >= SNR_DB_GATE))[0]
ceiling_q25 = float(fgrid[ok25].max()) if len(ok25) else float("nan")
print(f"median-channel SNR>={SNR_DB_GATE:.0f} dB ceiling: {ceiling_med:.0f} Hz "
      f"(25th-pct channel: {ceiling_q25:.0f} Hz)", flush=True)

# ---------------------------------------------------------------- C. cross-hit coherence (hits = realizations)
print("\n--- cross-hit coherence ---", flush=True)
Tcom = min(d["Ad"].shape[1] - d["imp"] for d in DEC.values())
X = {}          # rfft per hit of the aligned post-impact decay, all channels
for hid, d in DEC.items():
    seg = d["Ad"][:, d["imp"]:d["imp"] + Tcom]
    X[hid] = np.fft.rfft(seg, axis=1)
fcoh = np.fft.rfftfreq(Tcom, 1 / fs_d)
hits = list(X)
ref_ch = int(np.argmax(np.var(DEC[hits[0]]["Ad"], axis=1)))
Sxy = np.zeros((X[hits[0]].shape[0], len(fcoh)), complex)
Sxx = np.zeros_like(Sxy, dtype=float)
Syy = np.zeros(len(fcoh))
for hid in hits:
    Xc = X[hid]
    Sxy += Xc * np.conj(Xc[ref_ch])
    Sxx += np.abs(Xc) ** 2
    Syy += np.abs(Xc[ref_ch]) ** 2
coh = np.abs(Sxy) ** 2 / (Sxx * Syy[None, :] + 1e-30)          # (nch, nf), n=4 realizations
coh_med = np.median(coh, axis=0)
# smooth to octave-fraction bands for a readable summary
def band_summary(f, y, edges):
    return [float(np.median(y[(f >= lo) & (f < hi)])) for lo, hi in zip(edges[:-1], edges[1:])]
coh_bands = band_summary(fcoh, coh_med, OCT_EDGES)
okc = np.where((fcoh > 40) & (np.convolve(coh_med, np.ones(9) / 9, "same") >= COH_GATE))[0]
coh_ceiling = float(fcoh[okc].max()) if len(okc) else float("nan")
print(f"median cross-hit coherence >= {COH_GATE} up to ~{coh_ceiling:.0f} Hz "
      f"(n={len(hits)} hits; per-octave medians {['%.2f' % c for c in coh_bands]})", flush=True)

# ---------------------------------------------------------------- D. ring-down duration per band
print("\n--- ring-down duration per octave band ---", flush=True)
hid0 = hits[0]
Ad, imp = DEC[hid0]["Ad"], DEC[hid0]["imp"]
top16 = np.argsort(Ad.var(axis=1))[::-1][:16]
post = Ad[top16, imp:]
pre = Ad[top16, :max(imp - 32, 1)]
T_avail = post.shape[1] / fs_d
band_T = []
for lo, hi in zip(OCT_EDGES[:-1], OCT_EDGES[1:]):
    hi_n = min(hi, 0.45 * fs_d)
    if lo >= hi_n:
        band_T.append(None)
        continue
    sos = signal.butter(4, [lo / (fs_d / 2), hi_n / (fs_d / 2)], btype="band", output="sos")
    Ts = []
    for k in range(post.shape[0]):
        xb = signal.sosfiltfilt(sos, post[k])
        nb = signal.sosfiltfilt(sos, pre[k])
        floor = 2.0 * np.std(nb) + 1e-20
        env = np.abs(signal.hilbert(xb))
        env = np.convolve(env, np.ones(64) / 64, "same")
        above = np.where(env > floor)[0]
        Ts.append((above.max() + 1) / fs_d if len(above) else 0.0)
    tmed = float(np.median(Ts))
    truncated = tmed >= 0.98 * T_avail
    band_T.append(dict(band=[lo, hi], ring_s=tmed, truncated_by_record=bool(truncated)))
    print(f"  {lo:5d}-{hi:5d} Hz: signal above noise for {tmed:.3f} s of {T_avail:.3f} s available"
          f"{'  << TRUNCATED by record length' if truncated else ''}", flush=True)

# achievable df: usable frame = min(ring-down, record); take the 45-180 Hz bands (the sub-200 target)
t_low = [b["ring_s"] for b in band_T if b and b["band"][1] <= 200]
T_use = min(min(t_low), T_avail)
df_ach = 1.0 / T_use
print(f"usable frame for sub-200 work: {T_use:.3f} s -> achievable df = {df_ach:.2f} Hz "
      f"(current caches: 2.03 Hz)", flush=True)

# ---------------------------------------------------------------- E. damping resolvability, sub-200 modes
sub = mfreq < 200
hp = 2.0 * mdamp[sub] * mfreq[sub]                    # half-power bandwidth per mode, Hz
n_res_now = int((hp / 2.03 >= 3).sum())
n_res_ach = int((hp / df_ach >= 3).sum())
need_df = np.percentile(hp / 3.0, 50)
print(f"\nsub-200 survey modes: {int(sub.sum())}; half-power bands {hp.min():.2f}-{hp.max():.2f} Hz "
      f"(median {np.median(hp):.2f})")
print(f"resolvable (>=3 lines across half-power): {n_res_now}/{int(sub.sum())} at 2.03 Hz -> "
      f"{n_res_ach}/{int(sub.sum())} at {df_ach:.2f} Hz; median mode needs df<={need_df:.2f} Hz", flush=True)

results.update(dict(
    fs_hz=fs, fs_decimated=fs_d,
    snr_gate_db=SNR_DB_GATE, ceiling_median_ch_hz=ceiling_med, ceiling_q25_ch_hz=ceiling_q25,
    coherence_gate=COH_GATE, coherence_ceiling_hz=coh_ceiling, coherence_octave_medians=coh_bands,
    octave_edges=OCT_EDGES, ringdown=band_T, usable_frame_s=T_use, achievable_df_hz=df_ach,
    cache_df_hz=2.03, sub200_modes=int(sub.sum()),
    sub200_halfpower_hz=dict(min=float(hp.min()), median=float(np.median(hp)), max=float(hp.max())),
    resolvable_at_cache=n_res_now, resolvable_at_achievable=n_res_ach,
    median_mode_needs_df_hz=float(need_df)))
with open(os.path.join(HERE, "bandwidth_scan.json"), "w") as fjson:
    json.dump(results, fjson, indent=1)
print("saved bandwidth_scan.json", flush=True)
np.savez(os.path.join(HERE, "bandwidth_scan_curves.npz"),
         fgrid=fgrid, snr_med=snr_med_all, snr_q25=snr_q25_all,
         fcoh=fcoh, coh_med=coh_med, sub_f=mfreq[sub], sub_hp=hp)
print("saved bandwidth_scan_curves.npz (for cheap replots)", flush=True)

# ---------------------------------------------------------------- figure (Tufte: small multiples, direct labels)
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

fig, axes = plt.subplots(1, 3, figsize=(13.5, 4.4), constrained_layout=True)
ax = axes[0]
ax.semilogx(fgrid, snr_med_all, color="k", lw=1.1)
ax.semilogx(fgrid, snr_q25_all, color="0.55", lw=0.9)
ax.axhline(SNR_DB_GATE, color="0.75", lw=0.8)
ax.axvline(ceiling_med, color="0.75", lw=0.8)
ymax = float(np.nanmax(snr_med_all[(fgrid > 40) & (fgrid < 6000)])) + 6
ax.set_ylim(-12, ymax)
ax.text(45, SNR_DB_GATE + 1.5, f"{SNR_DB_GATE:.0f} dB gate", fontsize=9, color="0.4")
ax.text(ceiling_med * 0.92, ymax - 2, f"ceiling ~{ceiling_med:.0f} Hz", fontsize=9,
        rotation=90, va="top", ha="right", color="0.3")
ax.text(60, float(snr_med_all[np.searchsorted(fgrid, 60)]) + 4, "median channel", fontsize=9)
ax.text(60, float(snr_q25_all[np.searchsorted(fgrid, 60)]) - 7, "25th-pct channel",
        fontsize=9, color="0.45")
ax.set_xlabel("frequency (Hz, log)")
ax.set_ylabel("response SNR (dB re pre-trigger noise)")
ax.set_xlim(40, 6000)
ax.set_title("A. how high the hammer excites", fontsize=11)

ax = axes[1]
ax.semilogx(fcoh, np.convolve(coh_med, np.ones(9) / 9, "same"), color="k", lw=1.0)
ax.axhline(COH_GATE, color="0.75", lw=0.8)
ax.axhline(0.25, color="0.85", lw=0.8)
ax.text(45, 0.27, "pure-noise bias (n=4)", fontsize=9, color="0.5")
ax.text(45, COH_GATE - 0.06, f"{COH_GATE} gate", fontsize=9, color="0.4")
ax.set_xlabel("frequency (Hz, log)")
ax.set_ylabel("median cross-hit coherence")
ax.set_xlim(40, 6000)
ax.set_ylim(0, 1.02)
ax.set_title("B. repeatable structure across 4 hits", fontsize=11)

ax = axes[2]
ax.loglog(mfreq[sub], hp / 3.0, "o", ms=4.5, color="k", mfc="none",
          label="_")  # each point: one sub-200 survey mode
ax.axhline(2.03, color="0.35", lw=1.0)
ax.axhline(df_ach, color="0.35", lw=1.0, ls="--")
ax.set_xlim(48, 220)
ax.set_ylim(0.04, 4.0)
ax.text(50, 2.03 * 1.18, "current cache spacing 2.03 Hz", fontsize=9, color="0.25")
ax.text(50, df_ach * 0.70, f"best any re-distillation can do: {df_ach:.2f} Hz\n"
        "(record truncates the ring-down)", fontsize=9, color="0.25", va="top")
ax.text(52, 0.05, "circles: df each mode NEEDS (half-power/3)\nfrom survey zeta", fontsize=9,
        color="0.35", va="bottom")
ax.set_xlabel("survey mode frequency (Hz, log)")
ax.set_ylabel("frequency spacing df (Hz, log)")
ax.set_title("C. damping resolvability, sub-200 modes", fontsize=11)

fig.suptitle("Raw Test07 (+X, 4 hits, response-only: force channel dead) — bandwidth & resolution scan. "
             "EXPLORATORY, one drive; source: Test07_ImpactHammer_990x.zip, fs 250 kHz, 1.0 s records",
             fontsize=10)
out = os.path.join(HERE, "fig_bandwidth_scan.png")
fig.savefig(out, dpi=150)
print("saved", out, flush=True)
