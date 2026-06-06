#!/usr/bin/env python3
"""BLIND QOI propagation: netCG (3*GRMS) + interface response PSD with FULL uncertainty, vs a test spec.

Uses the posterior from blind_infer.py (report/blind_posterior.npz) + the PUBLISHED flight forcing. Closes
the D13 gap: the QOI band carries parameter (epistemic) + build-to-build & flight-to-flight (aleatory) +
discrepancy d (with its uncertainty).

QOI mapping (MY defensible engineering definition; quantity_contracts.md):
  netCG axial accel a_cg(w) = F(w) / M_app,zz(w)   [driving-point accelerance a = F/M]
  PSD_acg[g^2/Hz] = PSD_F[N^2/Hz] / (|M_app,zz(w)|^2 * g0^2)
  3*GRMS_netCG = 3*sqrt(integral PSD_acg df)
HONEST LIMITATION (measured on published data, blind-allowed): this driving-point mapping yields ~2x the
published 3*GRMS, i.e. the truth's coupled force-transmission attenuates more than a single driving-point
accelerance -> a QOI-mapping model-form bias we REPORT (the master scores vs the sealed truth).

Test spec: design-envelope forcing (published design_force_psd, the +6 dB pre-data conservative envelope)
driven through the predictive-median accelerance, then peak-hold/broadband-enveloped. Flights sit at -6 dB
mean -> large overall margin; a high-side flight draw at a sharp resonance can locally exceed -> the
narrow-band exceedance headline.
"""
from __future__ import annotations
import os, sys, math, json
from pathlib import Path
os.environ.setdefault("MPLCONFIGDIR", "/private/tmp/agentic_bayesx_mpl_blind")
import numpy as np
import jax; jax.config.update("jax_enable_x64", True)
import jax.numpy as jnp
import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
from scipy.ndimage import maximum_filter1d

HERE = Path(__file__).resolve().parents[1]; sys.path.insert(0, str(HERE / "code"))
import blind_model as bm

OUT = HERE / "report"; FIG = OUT / "figures"


def matern32_sdens(omega, sigma, ell):
    return (sigma**2) * (1.0 / ell**3) / (3.0 / ell**2 + omega**2)**2


def predict_appmass_zz(post, P, grid, n=400, rng=None):
    """Posterior samples of axial apparent mass |M_zz| on `grid`, per a NEW build (full uncertainty:
    epistemic k_strut/f_dome + build scatter + discrepancy d). Returns (n, nf) magnitude."""
    rng = rng or np.random.default_rng(0)
    S = post["k_strut_pop"].shape[0]; idx = rng.choice(S, min(n, S), replace=False)
    gridj = jnp.asarray(grid); M_base6 = jnp.asarray(P["M_base6"]); m_dome = float(P["m_dome"])
    # interpolate HSGP basis to `grid` (Phi was on the inference grid); rebuild basis on this grid
    Phi, omega = hsgp_basis(grid, post["beta"].shape[2])
    out = np.empty((len(idx), len(grid)))
    for i, j in enumerate(idx):
        logk = np.log(post["k_strut_pop"][j]) + post["sigma_build"][j] * rng.standard_normal()
        mu = np.asarray(bm.forward_logmag(math.exp(logk), float(post["f_dome"][j]), M_base6, m_dome, gridj))  # (6,nf)
        sd = np.sqrt(matern32_sdens(omega, post["sigma_d"][j], float(P["ell_d"])))
        d = (Phi @ (sd[None, :] * post["beta"][j]).T).T   # (6,nf)
        mu = mu + d
        out[i] = np.exp(mu[2])   # axial |M_zz|
    return out


def hsgp_basis(freqs, M):
    u = np.log(freqs); umid = 0.5 * (u.min() + u.max()); uhalf = 0.5 * (u.max() - u.min())
    un = (u - umid) / uhalf; L = 1.4; jj = np.arange(1, M + 1); omega = np.pi * jj / (2 * L)
    Phi = np.sin(np.outer(un + L, omega)) / np.sqrt(L)
    return Phi, omega


def main():
    obs = bm.load_observations(); f = obs["f"]; g0 = obs["g0"]
    post = dict(np.load(OUT / "blind_posterior.npz"))
    P = {"M_base6": post["M_base6"], "m_dome": float(post["m_dome"]), "ell_d": float(post["ell_d"])}

    # QOI frequency grid: where the response energy lives + the inference band (30-170 Hz), dense
    grid = np.geomspace(30.0, 170.0, 400)
    # predictive axial apparent mass with FULL uncertainty
    Mzz = predict_appmass_zz(post, P, grid, n=400, rng=np.random.default_rng(7))   # (n,nf)
    Mzz_med = np.median(Mzz, axis=0)

    # forcing on the QOI grid (interp published PSDs)
    Fdesign = np.interp(np.log(grid), np.log(f), obs["design_force"])
    Fflights = np.array([np.interp(np.log(grid), np.log(f), obs["flight_force"][k]) for k in range(obs["flight_force"].shape[0])])
    nfl = Fflights.shape[0]

    # ----- test spec: design-envelope accelerance, peak-hold broadband envelope -----
    spec_raw = Fdesign / (Mzz_med**2 * g0**2)
    win = max(5, len(grid) // 25)
    spec = maximum_filter1d(spec_raw, size=win)               # broadband peak-hold envelope (g^2/Hz)

    # ----- predicted per-flight netCG response PSD with full uncertainty -----
    # For each posterior apparent-mass draw, sample a flight (aleatory flight-to-flight forcing) -> response.
    n = Mzz.shape[0]
    rng = np.random.default_rng(8)
    fl_idx = rng.integers(0, nfl, size=n)
    resp = Fflights[fl_idx] / (Mzz**2 * g0**2)               # (n,nf) g^2/Hz, full uncertainty
    resp_med = np.median(resp, axis=0)
    resp_lo = np.quantile(resp, 0.025, axis=0); resp_hi = np.quantile(resp, 0.975, axis=0)
    resp_99hi = np.quantile(resp, 0.995, axis=0)

    # 3*GRMS netCG with full uncertainty
    grms = 3 * np.sqrt(np.trapz(resp, grid, axis=1))         # (n,)
    qoi = {"netcg_3grms_g_q50": float(np.median(grms)),
           "netcg_3grms_g_95ci": [float(np.quantile(grms, .025)), float(np.quantile(grms, .975))],
           "netcg_3grms_g_99ci": [float(np.quantile(grms, .005)), float(np.quantile(grms, .995))]}

    # narrow-band exceedance vs spec (one-sided 99%-hi)
    frac_99hi = float(np.mean(resp_99hi > spec))
    frac_med = float(np.mean(resp_med > spec))
    overall_margin = float(np.median(np.trapz(spec[None, :].repeat(1, 0), grid)) / np.median(np.trapz(resp, grid, axis=1)))

    # published netCG for the held-out QOI comparison (observable; documents the QOI-mapping bias)
    pub = obs["netcg"]
    results = {
        "qoi_mapping": "a_cg = F/M_app,zz (driving-point accelerance); PSD_acg = PSD_F/(|M_zz|^2 g0^2)",
        "qoi_mapping_known_bias": "driving-point mapping ~2x the published 3*GRMS (truth's coupled transmission attenuates more) -> reported model-form bias in the QOI transfer",
        "full_uncertainty_sources": ["parameter k_strut/f_dome (epistemic)", "build-to-build sigma_build (aleatory)",
                                     "flight-to-flight forcing (aleatory)", "discrepancy d (with its uncertainty)", "sensor n/a (QOI is structural)"],
        "netcg_3grms_g_PREDICTED_full_uncertainty": qoi,
        "netcg_3grms_g_PUBLISHED_observed": {"mean": float(pub.mean()), "min": float(pub.min()), "max": float(pub.max())},
        "spec_definition": "design-envelope forcing through predictive-median accelerance, peak-hold broadband envelope",
        "narrow_band_exceedance": {"frac_freqs_99hi_exceeds_spec": frac_99hi,
                                   "frac_freqs_median_exceeds_spec": frac_med,
                                   "overall_scalar_margin_spec_over_pred": overall_margin,
                                   "headline": "a large overall scalar margin can coexist with narrow-band 99%-hi exceedance at a sharp coupled resonance"},
        "qoi_grid": {"band_hz": [30.0, 170.0], "n_points": int(len(grid))},
    }
    (OUT / "blind_qoi_results.json").write_text(json.dumps(results, indent=2))

    # ---- figures ----
    fig, ax = plt.subplots(figsize=(10, 5.8))
    ax.fill_between(grid, resp_lo, resp_hi, color="#1f77b4", alpha=0.25, label="netCG response 95% (full uncertainty)")
    ax.loglog(grid, resp_med, color="#1f77b4", lw=1.6, label="predicted median")
    ax.loglog(grid, resp_99hi, color="#9467bd", lw=1.2, ls="-.", label="predicted 99%-hi")
    ax.loglog(grid, spec, color="#d62728", lw=2.0, label="test spec envelope (design-level)")
    # overlay published responses (observable held-out QOI check)
    for b in range(obs["resp_psd"].shape[0]):
        rb = np.interp(np.log(grid), np.log(f), obs["resp_psd"][b].mean(axis=0))
        ax.loglog(grid, rb, color="gray", lw=0.6, alpha=0.5, label="published response (obs, build-avg)" if b == 0 else None)
    ax.set_xlabel("frequency [Hz] (log)"); ax.set_ylabel("netCG accel PSD [g²/Hz]")
    ax.set_title(f"BLIND netCG QOI vs test spec — full-uncertainty bands; 99%-hi exceeds spec on {100*frac_99hi:.1f}% of the band\n(driving-point mapping ~2x high vs published -> reported QOI-transfer bias)", fontsize=9.5)
    ax.grid(True, which="both", alpha=0.25); ax.legend(fontsize=8, loc="lower center", ncol=2)
    fig.tight_layout(); fig.savefig(FIG / "blind_netcg_psd_vs_spec.png", dpi=145); plt.close(fig)

    fig, ax = plt.subplots(figsize=(8.6, 5.0))
    ax.hist(grms, bins=45, density=True, color="#1f77b4", alpha=0.8, label="predicted 3·GRMS (full uncertainty)")
    ax.axvline(qoi["netcg_3grms_g_q50"], color="#1f77b4", lw=2, label="pred median %.2f g" % qoi["netcg_3grms_g_q50"])
    ax.axvspan(pub.min(), pub.max(), color="#2ca02c", alpha=0.2, label="PUBLISHED observed range %.2f–%.2f g" % (pub.min(), pub.max()))
    ax.set_xlabel("netCG 3·GRMS [g]"); ax.set_ylabel("density")
    ax.set_title("netCG 3·GRMS: predicted (full uncertainty) vs published observed\n(median ~2x high = reported driving-point QOI-mapping bias)", fontsize=9.5)
    ax.legend(fontsize=8.5); ax.grid(True, alpha=0.3)
    fig.tight_layout(); fig.savefig(FIG / "blind_netcg_3grms.png", dpi=145); plt.close(fig)

    print(json.dumps(results, indent=2))


if __name__ == "__main__":
    main()
