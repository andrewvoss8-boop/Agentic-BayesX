#!/usr/bin/env python3
"""CHEAP POOLING-SIGMA PROBE (validity gate for the regional/pooled-spec pivot; Andrew approved).

Question: now that we know the per-sensor FEM shape error is sensor-LOCAL (borrow_R2~0, shape_borrow_diag.py), does
aggregating sensors into ZONES shrink the effective amplitude-discrepancy sigma enough that a twin envelope could beat
FEM+6 dB at a REGIONAL granularity? NO NUTS: reuse the FEM forward (theta=1) + measured caches, remove the global
units-gain (it cancels in every spread/ratio used here). Per-sensor residual r_s = log(GRMS_meas/GRMS_FEM).

Three lenses, swept over zone count K (1=global pool ... N=per-sensor), spatial k-means on sensor coords:
  (A) ANOVA: sigma_between(K) (scatter of zone-mean residual) and sigma_within(K) (spread a zone envelope must still
      cover). If sigma_between^2 + sigma_within^2 ~ sigma_sensor^2 = const, the per-sensor scatter is CONSERVED ->
      a max-over-zone ENVELOPE cannot escape it (you pay it as prediction error for small zones OR coverage for big
      zones). Only a zone-MEAN deliverable benefits.
  (B) ENVELOPE deliverable (the real spec form): zone-MAX twin-97.5% PSD vs zone-MAX FEM+6 dB PSD -> smoothline GRMS
      ratio + measured-data exceedance, vs K. Does the ratio cross 1 (twin wins) at any K while still covering?
  (C) MEAN deliverable (best-case pooling, NOT coverage-valid as a spec -> diagnostic only): twin band shrinks to
      sigma_sensor/sqrt(N_zone) (justified by spatial independence) -> zone-mean GRMS ratio vs FEM+6 dB zone-mean.

EXPLORATORY; YELLOW by default; no success claim. Output: out/pooling_sigma_probe.json + console.
"""
from __future__ import annotations
import json, sys
from pathlib import Path
import numpy as np
from scipy.cluster.vq import kmeans2

sys.path.insert(0, str(Path(__file__).resolve().parent))
import realfrf as rf
import psd_forward as pf
import psd_envelope as pe
import probe as P
from modal_multiref import MODAL_REFS

WS = Path(__file__).resolve().parent.parent
OUT = WS / "out"; OUT.mkdir(exist_ok=True)
REF = "m_xpos_990x"
COMBINED = P.COMBINED_REFS
S_F0 = 1.0
DB6 = 10.0 ** (6.0 / 10.0)            # FEM+6 dB multiplier on PSD
Z = 1.96                              # 97.5th-pct one-sided


def minimal_ctx():
    """The non-NUTS part of probe.fit_context: enough to evaluate model_H / meas_H / coords."""
    from types import SimpleNamespace
    R = rf.load_reduced()
    caches = P.load_caches()
    freqs = caches[COMBINED[0]]["freqs"]
    eta = P.zeta_eff(freqs)
    ch = rf.build_channels(R, [d for d in range(1, rf.N_ACCEL_RECORDERS + 1) if d not in rf.BAD_DAQ])
    common = set(ch.daq)
    for c in caches.values():
        common &= set(c["daq"])
    daq_master = [d for d in ch.daq if d in common]
    pos = {d: i for i, d in enumerate(ch.daq)}
    drows = {key: pf.drive_row_for(R, c["xyz"], c["axis"]) for key, c in caches.items()}
    coords = np.array([ch.coords[pos[d]] for d in daq_master])
    return SimpleNamespace(R=R, caches=caches, freqs=freqs, eta=eta, ch=ch, pos=pos,
                           drows=drows, daq_master=daq_master, coords=coords)


def per_sensor_psd(ctx, drive_keys):
    """Return measured PSD(f) and FEM(theta=1) PSD(f) per sensor (dict d-> array)."""
    data, fem = {}, {}
    for d in ctx.daq_master:
        resp = ctx.ch.rows[ctx.pos[d]]
        data[d] = np.abs(P.meas_H(ctx, drive_keys, d)) ** 2 * S_F0
        fem[d] = np.abs(P.model_H(ctx, np.ones((1, 9)), drive_keys, resp)[0]) ** 2 * S_F0
    return data, fem


def analyse(ctx, drive_keys, tag):
    f = ctx.freqs
    data, fem = per_sensor_psd(ctx, drive_keys)
    daqs = ctx.daq_master
    g_meas = np.array([pe.grms(f, data[d]) for d in daqs])
    g_fem = np.array([pe.grms(f, fem[d]) for d in daqs])
    r = np.log(g_meas / (g_fem + 1e-300))           # per-sensor log band-GRMS residual
    gain = float(np.median(r))                      # training-global units-gain (cancels in spreads/ratios)
    sigma_sensor = float(np.std(r - gain))
    fem_gain = np.exp(gain)                          # put FEM on the data scale for coverage checks

    Ks = [k for k in [1, 2, 3, 4, 6, 8, 12, 16, 24, len(daqs)] if k <= len(daqs)]
    anova, env_dec, mean_dec = [], [], []
    for K in Ks:
        if K == 1:
            labels = np.zeros(len(daqs), int)
        elif K == len(daqs):
            labels = np.arange(len(daqs))
        else:
            _, labels = kmeans2(ctx.coords.astype(float), K, seed=0, minit="++", missing="warn")
        zones = [np.where(labels == z)[0] for z in np.unique(labels)]
        zones = [z for z in zones if len(z) > 0]

        # (A) ANOVA decomposition of the per-sensor residual
        zmean = np.array([np.mean((r - gain)[z]) for z in zones])
        within_var = np.mean([np.var((r - gain)[z]) for z in zones if len(z) >= 2]) if any(len(z) >= 2 for z in zones) else 0.0
        # weight zone-means by zone size for between-variance
        w = np.array([len(z) for z in zones], float); w /= w.sum()
        s_between = float(np.sqrt(np.sum(w * (zmean - np.sum(w * zmean)) ** 2)))
        s_within = float(np.sqrt(max(within_var, 0.0)))
        anova.append({"K": K, "n_zones": len(zones), "sigma_between": round(s_between, 3),
                      "sigma_within": round(s_within, 3),
                      "rms_check": round(float(np.sqrt(s_between ** 2 + s_within ** 2)), 3)})

        # (B) ENVELOPE deliverable: zone-MAX twin-97.5% vs zone-MAX FEM+6 dB
        env_ratios, twin_cov, fem_cov = [], [], []
        band = np.exp(Z * sigma_sensor)             # broadband 97.5% multiplier on PSD (amplitude^2 -> exp(2*Z*sig)? no: see note)
        band_psd = np.exp(2 * Z * sigma_sensor)     # PSD multiplier (sigma is in log-amplitude; PSD=amp^2)
        for z in zones:
            dd = [daqs[i] for i in z]
            data_max = np.maximum.reduce([data[d] for d in dd])
            fem_max = np.maximum.reduce([fem[d] * fem_gain for d in dd])
            twin_max = fem_max * band_psd            # twin 97.5% PSD envelope = FEM*gain*PSD-band
            fem6_max = fem_max * DB6
            env_t = pe.smoothline_envelope(f, twin_max); env_f = pe.smoothline_envelope(f, fem6_max)
            env_ratios.append(pe.grms(f, env_t) / pe.grms(f, env_f))
            twin_cov.append(pe.exceedance(f, data_max, env_t)["exceeding_energy_fraction"])
            fem_cov.append(pe.exceedance(f, data_max, env_f)["exceeding_energy_fraction"])
        env_dec.append({"K": K, "median_grms_ratio_twin_vs_fem6": round(float(np.median(env_ratios)), 2),
                        "twin_wins_frac": round(float(np.mean(np.array(env_ratios) < 1.0)), 2),
                        "median_twin_exceed_energy": round(float(np.median(twin_cov)), 3),
                        "median_fem6_exceed_energy": round(float(np.median(fem_cov)), 3)})

        # (C) MEAN deliverable (diagnostic): twin band = sigma_sensor/sqrt(N_zone)
        mratios = []
        for z in zones:
            dd = [daqs[i] for i in z]
            band_mean_psd = np.exp(2 * Z * sigma_sensor / np.sqrt(len(z)))
            fem_gm = np.exp(np.mean([np.log(fem[d] * fem_gain + 1e-300) for d in dd], axis=0))  # geo-mean PSD
            twin_m = fem_gm * band_mean_psd
            fem6_m = fem_gm * DB6
            mratios.append(pe.grms(f, pe.smoothline_envelope(f, twin_m)) /
                           pe.grms(f, pe.smoothline_envelope(f, fem6_m)))
        mean_dec.append({"K": K, "median_grms_ratio_twin_vs_fem6": round(float(np.median(mratios)), 2),
                         "twin_wins_frac": round(float(np.mean(np.array(mratios) < 1.0)), 2)})

    return {"tag": tag, "n_sensors": len(daqs), "units_gain_log": round(gain, 3),
            "sigma_sensor_log": round(sigma_sensor, 3),
            "sigma_implies_band_PSD_dB": round(float(10 * np.log10(np.exp(2 * Z * sigma_sensor))), 1),
            "anova_by_K": anova, "envelope_deliverable_by_K": env_dec, "mean_deliverable_by_K": mean_dec}


def run(write=True):
    ctx = minimal_ctx()
    res = {"deliverable": "POOLING-SIGMA PROBE: does regional aggregation shrink the discrepancy band enough to beat "
                          "FEM+6 dB? (ENVELOPE vs MEAN, ANOVA conservation check). NO NUTS; theta=1 FEM mean.",
           "fem6_PSD_multiplier": round(DB6, 3),
           "references": {"plus_X": analyse(ctx, [REF], "plus_X_modal"),
                          "combined_correlated": analyse(ctx, COMBINED, "combined_correlated")},
           "caveat": "theta=1 FEM mean (no NUTS): the GRMS RATIO is band-vs-+6dB dominated so theta mainly shifts peak "
                     "FREQUENCIES (affects coverage, not the ratio). MEAN deliverable is a diagnostic floor, NOT a "
                     "coverage-valid qualification spec (under-covers ~half the sensors).",
           "note": "EXPLORATORY; YELLOW; no success claim."}
    if write:
        (OUT / "pooling_sigma_probe.json").write_text(json.dumps(res, indent=2))

    for key in ("plus_X", "combined_correlated"):
        a = res["references"][key]
        print(f"\n=== {key}: {a['n_sensors']} sensors, sigma_sensor(log)={a['sigma_sensor_log']} "
              f"(=> band +{a['sigma_implies_band_PSD_dB']} dB PSD; FEM+6dB bar=+6 dB) ===")
        print("  K  | sig_between sig_within rms | ENVELOPE ratio win% | MEAN ratio win%")
        for an, ed, md in zip(a["anova_by_K"], a["envelope_deliverable_by_K"], a["mean_deliverable_by_K"]):
            print(f"  {an['K']:<3d}| {an['sigma_between']:>10} {an['sigma_within']:>10} {an['rms_check']:>4} "
                  f"| {ed['median_grms_ratio_twin_vs_fem6']:>9}x {int(ed['twin_wins_frac']*100):>3}% "
                  f"| {md['median_grms_ratio_twin_vs_fem6']:>6}x {int(md['twin_wins_frac']*100):>3}%")
    return res


if __name__ == "__main__":
    run()
