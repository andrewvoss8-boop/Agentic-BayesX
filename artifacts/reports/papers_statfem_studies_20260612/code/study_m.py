"""Study M — virtual sensing under SENSOR FAULTS: calibrated physics-Bayes vs spatial interpolation (REAL panel).

Motivated by Yan et al. 2026 (AST), "Physics-Informed Digital Twin ... Virtual Sensing via a Frequency Attention
U-Net and Closed-Loop Model Updating." That paper reconstructs MASKED (faulty) sensor channels' frequency responses
with a physics-prior + neural-operator network, beating a SPATIAL INTERPOLATION baseline (which fails by up to 48 dB
at high-frequency LOCAL modes). Its headline metric is the log-amplitude main-peak error in dB. Its gap: the
reconstruction is a DETERMINISTIC point estimate with NO uncertainty, and the closed loop feeds it back as if it were
measured (double-counting). Our Bayesian statFEM twin already does physics-informed virtual sensing WITH calibrated
bands — the trustworthy-V&V piece that paper lacks.

This study (REAL panel, NO new sampling) treats Study K's 5 held-out LDV points as FAULTY/masked sensors and
reconstructs them two ways, scored with the paper's EXACT dB metrics, split low vs high frequency band:
  (1) SPATIAL INTERPOLATION (paper's baseline): per-frequency griddata(20 observed pts -> 5 masked pts), complex FRF.
  (2) BAYESIAN physics virtual sensing (ours): Study K posterior-predictive (median + 95% band).
Reports: main-peak dB error, channel RMSE(dB), low(8-25)/high(25-60) split, and the Bayesian band COVERAGE the paper
omits. Outputs -> ../out/studym_*.  (Reuses run_studyj data + studyk_permode.npz; no MCMC here.)
"""
from __future__ import annotations
import json, os
import numpy as np
from scipy.interpolate import griddata
import run_studyj as J

OUT = J.OUT
EPS = 1e-12
LOW = (8.0, 25.0); HIGH = (25.0, 60.0); FULL = (8.0, 60.0)


def dBmag(m):
    return 20.0 * np.log10(np.maximum(np.abs(m), EPS))


def band_idx(lo, hi):
    return np.where((J.FB >= lo) & (J.FB <= hi))[0]


def peak_err(mag_pred, mag_true, idx):
    """Paper Eq.18: |HdB_pred(w*) - HdB_true(w*)|, w* = measured-spectrum peak bin in the window. Per channel."""
    e = []
    for c in range(mag_true.shape[0]):
        pk = idx[int(np.argmax(mag_true[c, idx]))]
        e.append(abs(dBmag(mag_pred[c, pk]) - dBmag(mag_true[c, pk])))
    return np.array(e)


def rmse_db(mag_pred, mag_true, idx):
    d = dBmag(mag_pred[:, idx]) - dBmag(mag_true[:, idx])
    return np.sqrt(np.mean(d ** 2, axis=1))


def main():
    # ---- truth at the 5 masked (held-out / "faulty") LDV channels ----
    HOLD = list(J.HOLD); OBSP = list(J.OBSP)
    Htrue = J.YOBS[HOLD]                                   # (5, nf) complex
    mag_true = np.abs(Htrue)
    nf = J.FB.shape[0]

    # ---- (1) spatial interpolation baseline (paper's): per-frequency complex griddata ----
    obs_xy = J.PTS[OBSP]; hold_xy = J.PTS[HOLD]
    Hinterp = np.zeros((5, nf), complex)
    for fi in range(nf):
        col = J.YOBS[OBSP, fi]
        vr = griddata(obs_xy, col.real, hold_xy, method="linear")
        vi = griddata(obs_xy, col.imag, hold_xy, method="linear")
        vrn = griddata(obs_xy, col.real, hold_xy, method="nearest")
        vin = griddata(obs_xy, col.imag, hold_xy, method="nearest")
        vr[np.isnan(vr)] = vrn[np.isnan(vr)]; vi[np.isnan(vi)] = vin[np.isnan(vi)]
        Hinterp[:, fi] = vr + 1j * vi
    mag_interp = np.abs(Hinterp)

    # ---- (2) Bayesian physics virtual sensing (ours): Study K posterior-predictive ----
    Z = np.load(os.path.join(OUT, "studyk_permode.npz"))
    magpred = Z["magpred"]                                 # (S, 5, nf) draws of |Y| at masked pts
    mag_bayes = np.median(magpred, axis=0)                 # (5, nf)
    lo = np.percentile(magpred, 2.5, axis=0); hi = np.percentile(magpred, 97.5, axis=0)

    bands = {"full": band_idx(*FULL), "low": band_idx(*LOW), "high": band_idx(*HIGH)}
    res = {"n_masked": 5, "HOLD": HOLD, "bands_hz": {"low": LOW, "high": HIGH, "full": FULL}}
    for bk, idx in bands.items():
        pe_i = peak_err(mag_interp, mag_true, idx); pe_b = peak_err(mag_bayes, mag_true, idx)
        rm_i = rmse_db(mag_interp, mag_true, idx); rm_b = rmse_db(mag_bayes, mag_true, idx)
        # coverage: fraction of freq bins in this band where the 95% band brackets the true magnitude (per channel, then mean)
        cov_bins = np.mean((mag_true[:, idx] >= lo[:, idx]) & (mag_true[:, idx] <= hi[:, idx]), axis=1)
        res[bk] = dict(
            peak_dB_interp=pe_i.tolist(), peak_dB_bayes=pe_b.tolist(),
            peak_dB_interp_mean=float(pe_i.mean()), peak_dB_bayes_mean=float(pe_b.mean()),
            rmse_dB_interp_mean=float(rm_i.mean()), rmse_dB_bayes_mean=float(rm_b.mean()),
            bayes_band_bin_coverage=cov_bins.tolist(), bayes_band_bin_coverage_mean=float(cov_bins.mean()))

    # peak-QOI coverage (the K result, restated as virtual-sensing coverage)
    qpk_true = mag_true.max(1)
    qlo = np.percentile(magpred.max(2), 2.5, 0); qhi = np.percentile(magpred.max(2), 97.5, 0)
    peak_cover = [bool(l <= t <= h) for l, t, h in zip(qlo, qpk_true, qhi)]
    res["bayes_peak_qoi_coverage"] = f"{sum(peak_cover)}/5"; res["bayes_peak_cover"] = peak_cover

    # verdict (honest, pre-registered)
    hi_better = res["high"]["peak_dB_bayes_mean"] < res["high"]["peak_dB_interp_mean"]
    lo_better = res["low"]["peak_dB_bayes_mean"] < res["low"]["peak_dB_interp_mean"]
    res["verdict"] = (
        f"HIGH band (local modes): Bayes {res['high']['peak_dB_bayes_mean']:.1f} dB vs interp "
        f"{res['high']['peak_dB_interp_mean']:.1f} dB -> " + ("Bayes wins (confirms paper's aliasing claim) + adds calibrated bands"
        if hi_better else "interp competitive here") +
        f"; LOW band (global modes): Bayes {res['low']['peak_dB_bayes_mean']:.1f} vs interp "
        f"{res['low']['peak_dB_interp_mean']:.1f} dB -> " + ("Bayes wins" if lo_better else "interp competitive (smooth, well-sampled)"))
    res["uq_note"] = ("Spatial interpolation gives a POINT reconstruction with no uncertainty; feeding it into closed-loop "
                      "updating as 'virtual ground truth' (the paper's loop) treats reconstruction error as exact = "
                      "double-counting/overconfidence. The Bayesian reconstruction carries a 95% band an updater can weight by.")

    np.savez(os.path.join(OUT, "studym_arrays.npz"),
             FB=J.FB, mag_true=mag_true, mag_interp=mag_interp, mag_bayes=mag_bayes,
             lo=lo, hi=hi, HOLD=np.array(HOLD), PTS=J.PTS, OBSP=np.array(OBSP))
    json.dump(res, open(os.path.join(OUT, "studym_summary.json"), "w"), indent=2)
    print("Study M (virtual sensing under sensor faults) — paper dB main-peak error, REAL panel:")
    for bk in ("low", "high", "full"):
        b = res[bk]
        print(f"  {bk:4s}: interp {b['peak_dB_interp_mean']:6.1f} dB | Bayes {b['peak_dB_bayes_mean']:6.1f} dB | "
              f"RMSE interp {b['rmse_dB_interp_mean']:5.1f} / Bayes {b['rmse_dB_bayes_mean']:5.1f} dB | "
              f"Bayes band-bin cover {b['bayes_band_bin_coverage_mean']*100:4.0f}%")
    print("  Bayes peak-QOI coverage:", res["bayes_peak_qoi_coverage"])
    print("  VERDICT:", res["verdict"])
    print("saved studym_summary.json")


if __name__ == "__main__":
    main()
