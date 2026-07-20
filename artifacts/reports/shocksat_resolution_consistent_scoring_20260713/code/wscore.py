#!/usr/bin/env python3
"""wscore — LODO dev + vault scorer for the resolution-consistent study (20260713).

Fold logic is copied VERBATIM from the damping run's score.score_candidate (same _usable/_train_warp/
_matched_peak_bins constants and aggregation) so Gate R can certify bit-level pipeline continuity; the only
changes are (i) the forward path is parameterized (naive | window-matched, wforward.predict_H), (ii) metric
P4 (matched-peak height error, dB) is added, (iii) scores append to THIS workspace's out/score_log.jsonl.

NO-PER-MODE-LSQ / LOW-DIM-PHYSICAL-DAMPING-ONLY: theta = reused theta_MAP; damping = fixed pre-registered
spec; ONE global train-side gain (dB) per fold; no per-mode/per-channel amplitude, phase, or damping fitting.
The vault cache is read ONLY by score_vault(), which requires VAULT_FREEZE.sha256 to exist.
"""
from __future__ import annotations
import json, os, sys, time
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import wforward as WF
import metrics as MET                      # damping run's metrics (path via wforward's sys.path insert)
import femlib as F

WS = WF.WS
SLOG = os.path.join(WS, "out", "score_log.jsonl")
COH_MIN = 0.6
MAC_CAL, DF_CAL = 0.50, 0.12
BAND = WF.BAND
MAX_SHIFT, MIN_BAND = 0.06, 25

_caches = None


def load_caches():
    """Dev caches only; the vault key is loaded ONLY inside score_vault (freeze-checked)."""
    global _caches
    if _caches is None:
        _caches = {}
        for key in F.DRIVE_KEYS:
            c = np.load(os.path.join(F.NETCG_DATA, key + ".npz"), allow_pickle=True)
            fc = np.asarray(c["freqs"], float)
            band = (fc >= BAND[0]) & (fc <= BAND[1])
            _caches[key] = {"daq": [int(d) for d in c["daq"]], "H1": np.asarray(c["H1"]),
                            "coh": np.asarray(c["coherence"], float), "freqs": fc, "band": band}
    return _caches


def _usable(pkg, cache):
    rows_of = {d: i for i, d in enumerate(pkg.sens_daq)}
    rows, cols = [], []
    band = cache["band"]
    for i, d in enumerate(cache["daq"]):
        if d not in rows_of:
            continue
        if float(np.median(cache["coh"][i][band])) < COH_MIN:
            continue
        rows.append(rows_of[d]); cols.append(i)
    return np.array(rows, int), np.array(cols, int)


def _train_warp(pkg, theta, damping, windowed, train_keys, caches):
    """Copy of score._train_warp with the forward path parameterized (arm-consistent warp)."""
    rhos, band_masks, ridge_ws = [], None, []
    full_band = None
    for tk in train_keys:
        c = caches[tk]; fc = c["freqs"]; band = c["band"]
        full_band = band.copy()
        rows, cols = _usable(pkg, c)
        if len(rows) < 3:
            continue
        Hp = WF.predict_H(pkg, theta, damping, tk, fc, windowed)[rows][:, band]
        Hm = c["H1"][cols][:, band]
        Fs = MET.fdac_surface(Hp, Hm, cosine=True)
        fa, fes, val = MET.fdac_ridge(Fs, fc[band], fc[band], max_shift=MAX_SHIFT)
        rhos.append(MET.estimate_scale_warp(fa, fes, val, vmin=0.3, max_shift=MAX_SHIFT))
        ridge_ws.append(np.median(val))
        m = np.zeros(len(fc), bool); m[band] = MET.fdac_band_select(fa, fes, val, vmin=0.5)
        band_masks = m if band_masks is None else (band_masks | m)
    if not rhos:
        return 1.0, (full_band if full_band is not None else np.ones(1, bool))
    w = np.clip(np.asarray(ridge_ws), 1e-6, None)
    rho = float(np.sum(w * np.asarray(rhos)) / np.sum(w))
    if band_masks is None or band_masks.sum() < MIN_BAND:
        band_masks = full_band
    return rho, band_masks


def _matched_peak_bins(pkg, theta, fc):
    f_el, _ = pkg.modes(theta)
    pairs = np.asarray(pkg.pairs); mfreqs = np.asarray(pkg.mfreqs, float)
    bins = []
    for r, k, mac in pairs:
        fm = mfreqs[int(r)]
        if mac < MAC_CAL or abs(f_el[int(k)] / fm - 1.0) > DF_CAL or fm < BAND[0] or fm > BAND[1]:
            continue
        bins.append(int(np.argmin(np.abs(fc - fm))))
    return bins


def _grade_channels(logHp, rho, gain_db, sel, band, pk, c, rows, cols):
    """Per-channel P3/P1'/P2'/P4 lists for one drive given a forward log|H| and train-side warp/gain."""
    fc = c["freqs"]
    p3s, p1s, frsfs, p4s = [], [], [], []
    for r, cidx in zip(rows, cols):
        ym = np.log10(np.abs(c["H1"][cidx][band]) + 1e-300)
        p3 = MET.frac_corr(logHp[r][band], ym)
        if not np.isnan(p3):
            p3s.append(p3)
        ypw = MET.apply_scale_warp(logHp[r], fc, rho)
        p1 = MET.frac_corr(ypw[sel], np.log10(np.abs(c["H1"][cidx][sel]) + 1e-300))
        if not np.isnan(p1):
            p1s.append(p1)
        if pk:
            Hm_pk = np.abs(c["H1"][cidx][pk])
            Hp_pk = 10.0 ** (ypw[pk] + gain_db / 20.0)
            frsfs.append(MET.frsf(Hp_pk, Hm_pk)[2])
            dpk_db = 20.0 * (np.log10(Hp_pk + 1e-300) - np.log10(Hm_pk + 1e-300))
            p4s.append(float(np.median(np.abs(dpk_db))))
    return p3s, p1s, frsfs, p4s


def score_dev(arm, cid, damping, windowed, log=True, note=""):
    """Full 4-fold LODO dev score. Appends ONE line to score_log.jsonl (stage='dev') unless log=False
    (log=False is ONLY for the labeled A3 sensitivity variant, which is NOT an arm)."""
    pkg = F.Package.load(cid)
    theta = np.asarray(pkg.theta_map()[0], float)
    caches = load_caches()
    folds = {}
    for dev_key in F.DRIVE_KEYS:
        train_keys = [k for k in F.DRIVE_KEYS if k != dev_key]
        rho, band_mask = _train_warp(pkg, theta, damping, windowed, train_keys, caches)
        offs = []
        for tk in train_keys:
            c = caches[tk]; rows, cols = _usable(pkg, c)
            if len(rows) == 0:
                continue
            lp = WF.predict_logH(pkg, theta, damping, tk, c["freqs"], windowed)[rows][:, c["band"]]
            ym = np.log10(np.abs(c["H1"][cols][:, c["band"]]) + 1e-300)
            offs.append(float(np.mean(ym - lp)))
        gain_db = 20.0 * float(np.mean(offs)) if offs else 0.0
        c = caches[dev_key]; fc = c["freqs"]; band = c["band"]
        rows, cols = _usable(pkg, c)
        logHp = WF.predict_logH(pkg, theta, damping, dev_key, fc, windowed)
        sel = band & band_mask if band_mask.shape[0] == len(fc) else band
        pk = [b for b in _matched_peak_bins(pkg, theta, fc) if sel[b]]
        p3s, p1s, frsfs, p4s = _grade_channels(logHp, rho, gain_db, sel, band, pk, c, rows, cols)
        folds[dev_key] = {"P3": _med(p3s), "P1p": _med(p1s), "P2p": _med(frsfs), "P4": _med(p4s),
                          "n_ch": len(p3s), "rho": round(rho, 4), "gain_dB": round(gain_db, 3)}
    rec = _aggregate(arm, cid, damping, windowed, folds, stage="dev", note=note)
    if log:
        with open(SLOG, "a") as f:
            f.write(json.dumps(rec) + "\n")
    return rec


def score_vault(arm, cid, damping, windowed):
    """The single post-freeze vault grade (warp+gain from ALL 4 dev drives, exactly the damping run's vault
    convention). REQUIRES VAULT_FREEZE.sha256; labels the record as the program's SECOND read of +XY."""
    if not os.path.exists(os.path.join(WS, "VAULT_FREEZE.sha256")):
        raise RuntimeError("VAULT_FREEZE.sha256 missing — vault may not be read before freeze")
    pkg = F.Package.load(cid)
    theta = np.asarray(pkg.theta_map()[0], float)
    caches = load_caches()
    rho, band_mask = _train_warp(pkg, theta, damping, windowed, F.DRIVE_KEYS, caches)
    offs = []
    for tk in F.DRIVE_KEYS:
        c = caches[tk]; rows, cols = _usable(pkg, c)
        if len(rows) == 0:
            continue
        lp = WF.predict_logH(pkg, theta, damping, tk, c["freqs"], windowed)[rows][:, c["band"]]
        ym = np.log10(np.abs(c["H1"][cols][:, c["band"]]) + 1e-300)
        offs.append(float(np.mean(ym - lp)))
    gain_db = 20.0 * float(np.mean(offs)) if offs else 0.0
    z = np.load(os.path.join(F.NETCG_DATA, F.VAULT_KEY + ".npz"), allow_pickle=True)
    fc = np.asarray(z["freqs"], float)
    band = (fc >= BAND[0]) & (fc <= BAND[1])
    c = {"daq": [int(d) for d in z["daq"]], "H1": np.asarray(z["H1"]),
         "coh": np.asarray(z["coherence"], float), "freqs": fc, "band": band}
    rows, cols = _usable(pkg, c)
    logHp = WF.predict_logH(pkg, theta, damping, F.VAULT_KEY, fc, windowed)
    sel = band & band_mask if band_mask.shape[0] == len(fc) else band
    pk = [b for b in _matched_peak_bins(pkg, theta, fc) if sel[b]]
    p3s, p1s, frsfs, p4s = _grade_channels(logHp, rho, gain_db, sel, band, pk, c, rows, cols)
    folds = {F.VAULT_KEY: {"P3": _med(p3s), "P1p": _med(p1s), "P2p": _med(frsfs), "P4": _med(p4s),
                           "n_ch": len(p1s), "rho": round(rho, 4), "gain_dB": round(gain_db, 3)}}
    rec = _aggregate(arm, cid, damping, windowed, folds, stage="vault",
                     note="SECOND program read of +XY (damping run graded it 2026-07-10); zero-search arm set")
    rec["second_program_read"] = True
    with open(SLOG, "a") as f:
        f.write(json.dumps(rec) + "\n")
    return rec


def _med(v):
    return float(np.median(v)) if v else None


def _aggregate(arm, cid, damping, windowed, folds, stage, note=""):
    keys = list(folds)
    p1 = np.array([folds[k]["P1p"] for k in keys if folds[k]["P1p"] is not None])
    p3 = np.array([folds[k]["P3"] for k in keys if folds[k]["P3"] is not None])
    p2 = [folds[k]["P2p"] for k in keys if folds[k]["P2p"] is not None]
    p4 = [folds[k]["P4"] for k in keys if folds[k]["P4"] is not None]
    return {"arm": arm, "cid": cid, "stage": stage, "damping": damping, "windowed": bool(windowed),
            "P1p_mean": float(p1.mean()) if len(p1) else None,
            "P1p_folds": {k: (round(folds[k]["P1p"], 4) if folds[k]["P1p"] is not None else None)
                          for k in keys},
            "P1p_se": float(p1.std(ddof=1) / np.sqrt(len(p1))) if len(p1) > 1 else None,
            "P3_mean": float(p3.mean()) if len(p3) else None,
            "P2p_mean": float(np.mean(p2)) if p2 else None,
            "P4_mean": float(np.mean(p4)) if p4 else None,
            "folds": folds, "note": note,
            "unix_ts": time.time(), "ts": time.strftime("%Y-%m-%dT%H:%M:%S")}


def existing(stage="dev"):
    done = {}
    if os.path.exists(SLOG):
        for line in open(SLOG):
            if line.strip():
                r = json.loads(line)
                if r.get("stage") == stage:
                    done[r["arm"]] = r
    return done
