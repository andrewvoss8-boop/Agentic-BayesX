#!/usr/bin/env python3
"""wscore_wide — LODO dev scorer on the WIDE caches with per-band results (cards §7; contracts Q1).

Fold logic mirrors the resolution run's wscore (train-side FDAC warp rho + ONE global gain per fold; no
per-channel/per-mode amplitude fitting anywhere — NO-PER-MODE-LSQ), extended to:
  * per-drive certified band: 45 Hz -> min(ceiling_hz_last_run, 1000 Hz) (decisions D3/D4);
  * per-band reporting: sub200 [45,200), b200_500 [200,500), b500_ceiling [500, top];
  * per-band channel masks (median coherence >= 0.6 within the band; bands with <8 usable bins or <3
    channels report null).
The vault path requires VAULT_FREEZE.sha256 and labels records as the program's THIRD read of +XY.
All records append to THIS workspace's out/score_log.jsonl.
"""
from __future__ import annotations
import json, os, sys, time
import numpy as np

WS = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import wide_forward as WFW                          # noqa: E402
sys.path.insert(0, os.path.abspath(os.path.join(WS, "..", "shocksat_frf_damping_updating_20260710", "code")))
import metrics as MET                               # noqa: E402  (read-only reuse)

DEV_KEYS = ["m_xpos_990x", "m_zpos_990z", "m_ypos_990y", "m_zpos_900z"]
VAULT_KEY = "m_xy_990xy"
WIDE_DIR = os.path.join(WS, "data", "multiref_wide")
SLOG = os.path.join(WS, "out", "score_log.jsonl")
COH_MIN = 0.6
MAX_SHIFT, MIN_BAND = 0.06, 25
SCORED_TOP_CAP = 500.0                               # FEM-credibility cap (D11): basis credible to 639 Hz
# (cross-validated); the card's 1.25x modal-truncation rule => highest scorable freq 639/1.25 = 511 Hz,
# rounded down to 500. The data is certified >1 kHz (source_register) but the inherited FEM twin cannot be
# pushed past ~640 Hz on available compute (dense local-mode forest; k=650 thrashed) -> 500-1000 Hz FRF
# scoring is FEM/compute-limited, NOT data-limited. See decisions D8/D9/D11 and findings H4.
BAND_DEFS = [("sub200", 45.0, 200.0), ("b200_500", 200.0, 500.0), ("b500_ceiling", 500.0, None)]

_caches = None


def scored_top(key):
    c = json.load(open(os.path.join(WS, "out", "certified_ceiling.json")))
    ceil = c[key]["ceiling_hz_last_run"]
    return float(min(ceil, SCORED_TOP_CAP))


def load_caches(keys=None):
    global _caches
    if _caches is None:
        _caches = {}
        for key in DEV_KEYS:
            p = os.path.join(WIDE_DIR, key + "_wide.npz")
            z = np.load(p, allow_pickle=True)
            fc = np.asarray(z["freqs"], float)
            top = scored_top(key)
            band = (fc >= 45.0) & (fc <= top)
            _caches[key] = {"daq": [int(d) for d in z["daq"]], "H1": np.asarray(z["H1"]),
                            "coh": np.asarray(z["coherence"], float), "freqs": fc, "band": band,
                            "top": top}
    return _caches


def _usable(pkg, cache, band_mask):
    """Channels present in the package with median coherence >= COH_MIN over band_mask bins."""
    rows_of = {d: i for i, d in enumerate(pkg.sens_daq)}
    rows, cols = [], []
    for i, d in enumerate(cache["daq"]):
        if d not in rows_of:
            continue
        if float(np.median(cache["coh"][i][band_mask])) < COH_MIN:
            continue
        rows.append(rows_of[d]); cols.append(i)
    return np.array(rows, int), np.array(cols, int)


def default_fwd(windowed, flat_zeta):
    return lambda pkg, theta, dkey, fc: WFW.predict_H(pkg, theta, dkey, fc, windowed, flat_zeta)


def _train_warp(pkg, theta, train_keys, caches, windowed, flat_zeta, fwd=None):
    fwd = fwd or default_fwd(windowed, flat_zeta)
    rhos, ridge_ws = [], []
    band_masks = {}
    for tk in train_keys:
        c = caches[tk]; fc = c["freqs"]; band = c["band"]
        rows, cols = _usable(pkg, c, band)
        if len(rows) < 3:
            continue
        Hp = fwd(pkg, theta, tk, fc[band])[rows]
        Hm = c["H1"][cols][:, band]
        Fs = MET.fdac_surface(Hp, Hm, cosine=True)
        fa, fes, val = MET.fdac_ridge(Fs, fc[band], fc[band], max_shift=MAX_SHIFT)
        rhos.append(MET.estimate_scale_warp(fa, fes, val, vmin=0.3, max_shift=MAX_SHIFT))
        ridge_ws.append(np.median(val))
        m = np.zeros(len(fc), bool); m[band] = MET.fdac_band_select(fa, fes, val, vmin=0.5)
        band_masks[tk] = m
    if not rhos:
        return 1.0, None
    w = np.clip(np.asarray(ridge_ws), 1e-6, None)
    rho = float(np.sum(w * np.asarray(rhos)) / np.sum(w))
    return rho, band_masks


def _fold_gain(pkg, theta, train_keys, caches, windowed, flat_zeta, fwd=None):
    fwd = fwd or default_fwd(windowed, flat_zeta)
    offs = []
    for tk in train_keys:
        c = caches[tk]
        rows, cols = _usable(pkg, c, c["band"])
        if len(rows) == 0:
            continue
        lp = np.log10(np.abs(fwd(pkg, theta, tk, c["freqs"][c["band"]])[rows]) + 1e-300)
        ym = np.log10(np.abs(c["H1"][cols][:, c["band"]]) + 1e-300)
        offs.append(float(np.mean(ym - lp)))
    return 20.0 * float(np.mean(offs)) if offs else 0.0


def _grade_bands(pkg, theta, dkey, cache, rho, fold_mask, windowed, flat_zeta, qoi_w=None, fwd=None):
    """Per-band P1'/P3 medians (and QOI-weighted means if qoi_w = {daq: weight})."""
    fwd = fwd or default_fwd(windowed, flat_zeta)
    fc = cache["freqs"]
    logHp_full = np.log10(np.abs(fwd(pkg, theta, dkey, fc)) + 1e-300)
    ypw_full = MET.apply_scale_warp(logHp_full, fc, rho)
    out = {}
    for bname, flo, fhi in BAND_DEFS:
        top = cache["top"] if fhi is None else min(fhi, cache["top"])
        bm = (fc >= flo) & (fc < top) & cache["band"]
        if bname == "b500_ceiling" and cache["top"] <= 500.0:
            out[bname] = {"status": "not_certified",
                          "reason": "FEM basis credible to 639 Hz (cross-validated); 1.25x modal-truncation "
                                    "rule caps scorable freq at 511 Hz -> 500-1000 Hz is FEM/compute-"
                                    "limited, not data-limited (data certified >1 kHz). D11."}
            continue
        sel = bm & fold_mask if fold_mask is not None else bm
        used_fallback = False
        if sel.sum() < 8:
            sel = bm; used_fallback = True
        rows, cols = _usable(pkg, cache, bm)
        if len(rows) < 3 or sel.sum() < 8:
            out[bname] = {"status": "too_few_channels_or_bins", "n_ch": int(len(rows)),
                          "n_bins": int(sel.sum())}
            continue
        p1s, p3s, daqs = [], [], []
        for r, ci in zip(rows, cols):
            ym = np.log10(np.abs(cache["H1"][ci][sel]) + 1e-300)
            p1 = MET.frac_corr(ypw_full[r][sel], ym)
            p3 = MET.frac_corr(logHp_full[r][sel], ym)
            if not np.isnan(p1):
                p1s.append(p1); p3s.append(p3); daqs.append(cache["daq"][ci])
        rec = {"P1p": float(np.median(p1s)) if p1s else None,
               "P3": float(np.median(p3s)) if p3s else None,
               "n_ch": len(p1s), "n_bins": int(sel.sum()), "mask_fallback": used_fallback}
        if qoi_w:
            wts = np.array([qoi_w.get(d, 0.0) for d in daqs])
            if wts.sum() > 0:
                rec["P1p_qoiw"] = float(np.sum(wts * np.asarray(p1s)) / wts.sum())
        out[bname] = rec
    return out


def score_dev_wide(arm, pkg, theta, note="", windowed=True, flat_zeta=None, log=True, qoi_w=None,
                   track=None, query_meta=None, fwd=None):
    caches = load_caches()
    folds = {}
    for dev_key in DEV_KEYS:
        train_keys = [k for k in DEV_KEYS if k != dev_key]
        rho, bmasks = _train_warp(pkg, theta, train_keys, caches, windowed, flat_zeta, fwd)
        fold_mask = None
        if bmasks:
            fm = np.zeros(len(caches[dev_key]["freqs"]), bool)
            for tk, m in bmasks.items():
                if m.shape[0] == fm.shape[0]:
                    fm |= m
            fold_mask = fm if fm.sum() >= MIN_BAND else None
        gain_db = _fold_gain(pkg, theta, train_keys, caches, windowed, flat_zeta, fwd)  # reported; P1'/P3
        bands = _grade_bands(pkg, theta, dev_key, caches[dev_key], rho, fold_mask,       # are gain-invariant
                             windowed, flat_zeta, qoi_w, fwd)
        folds[dev_key] = {"bands": bands, "rho": round(rho, 4), "gain_dB": round(gain_db, 3),
                          "train_keys": train_keys}
    rec = _aggregate(arm, folds, stage="dev", note=note)
    if track:
        rec["track"] = track
        if query_meta:
            rec.update(query_meta)
    if log:
        with open(SLOG, "a") as f:
            f.write(json.dumps(rec) + "\n")
    return rec


def score_vault_wide(arm, pkg, theta, note="", windowed=True, flat_zeta=None, qoi_w=None, fwd=None):
    """Single post-freeze vault grade on the wide +XY cache. Warp/gain from ALL 4 dev drives."""
    if not os.path.exists(os.path.join(WS, "VAULT_FREEZE.sha256")):
        raise RuntimeError("VAULT_FREEZE.sha256 missing — vault may not be read before freeze")
    caches = load_caches()
    rho, bmasks = _train_warp(pkg, theta, DEV_KEYS, caches, windowed, flat_zeta, fwd)
    gain_db = _fold_gain(pkg, theta, DEV_KEYS, caches, windowed, flat_zeta, fwd)
    z = np.load(os.path.join(WIDE_DIR, VAULT_KEY + "_wide.npz"), allow_pickle=True)
    fc = np.asarray(z["freqs"], float)
    top = scored_top(VAULT_KEY)
    cache = {"daq": [int(d) for d in z["daq"]], "H1": np.asarray(z["H1"]),
             "coh": np.asarray(z["coherence"], float), "freqs": fc,
             "band": (fc >= 45.0) & (fc <= top), "top": top}
    bands = _grade_bands(pkg, theta, VAULT_KEY, cache, rho, None, windowed, flat_zeta, qoi_w, fwd)
    folds = {VAULT_KEY: {"bands": bands, "rho": round(rho, 4), "gain_dB": round(gain_db, 3),
                         "train_keys": DEV_KEYS}}
    rec = _aggregate(arm, folds, stage="vault",
                     note=(note + " | third program read of +XY (damping run 2026-07-10, resolution run "
                                  "2026-07-13 read it before); zero-search pre-registered arm set").strip())
    with open(SLOG, "a") as f:
        f.write(json.dumps(rec) + "\n")
    return rec


def _aggregate(arm, folds, stage, note=""):
    keys = list(folds)
    agg = {}
    for bname, _, _ in BAND_DEFS:
        vals = [folds[k]["bands"][bname].get("P1p") for k in keys
                if folds[k]["bands"].get(bname, {}).get("P1p") is not None]
        v3 = [folds[k]["bands"][bname].get("P3") for k in keys
              if folds[k]["bands"].get(bname, {}).get("P3") is not None]
        agg[bname] = {"P1p_mean": float(np.mean(vals)) if vals else None,
                      "P1p_se": float(np.std(vals, ddof=1) / np.sqrt(len(vals))) if len(vals) > 1 else None,
                      "P3_mean": float(np.mean(v3)) if v3 else None, "n_folds": len(vals)}
    return {"arm": arm, "stage": stage, "bands_agg": agg, "folds": folds, "note": note,
            "unix_ts": time.time(), "ts": time.strftime("%Y-%m-%dT%H:%M:%S")}


def existing(stage="dev"):
    done = {}
    if os.path.exists(SLOG):
        for line in open(SLOG):
            if line.strip():
                r = json.loads(line)
                if r.get("stage") == stage and "bands_agg" in r:
                    done[r["arm"]] = r
    return done
