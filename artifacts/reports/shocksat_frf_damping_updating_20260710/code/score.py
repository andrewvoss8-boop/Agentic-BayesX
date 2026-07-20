#!/usr/bin/env python3
"""Dev scorer — the ONLY loop-side module that reads the drive caches. Returns SCALARS only.

NO-PER-MODE-LSQ: physics-honest selection (card §4.3). For each candidate/fold: theta_MAP (train-side .ash) +
train-fit LOW-DIM PHYSICAL DAMPING (band zeta / Rayleigh / joint eta, frozen for the dev drive) + ONE global
dB gain per fold (mean log offset on the fold's TRAIN drives). There is NO per-mode and NO per-channel
amplitude/phase/damping fitting anywhere in this file (LOW-DIM-PHYSICAL-DAMPING-ONLY; damping dim <= 10).

Metrics (quantity_contracts):
  P3 (fold)  = median over usable channels of corr(log10|Hpred|, log10|Hmeas|), 45-260 Hz    [raw, comparability]
  P1'(fold)  = same corr but AFTER the TRAIN-side FDAC frequency-alignment warp, over the FDAC-selected band
  P2'(fold)  = median |FRSF-1| at FDAC-aligned matched peaks                                   [amplitude/damping]
  P1' - P3   = the FDAC-alignment gain (quantified, not assumed)
Usable channel = median in-band coherence >= 0.6 (same rule for every candidate).
The FDAC warp + band are computed on TRAIN drives ONLY (never the dev drive).

Budget: HARD <=60 dev-scored candidates per track, counted from out/query_log.jsonl; exceeding raises.
"""
from __future__ import annotations
import json, os, sys, time
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import femdamp as D
import metrics as MET
import femlib as F

WS = D.WS
QLOG = os.path.join(WS, "out", "query_log.jsonl")
COH_MIN = 0.6
BUDGET = 60
MAC_CAL, DF_CAL = 0.50, 0.12
BAND = D.BAND

_caches = None


def load_caches():
    """Dev drive caches only (the vault key is NEVER loaded here; vault.py handles it once, post-freeze)."""
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


def n_queries(track):
    if not os.path.exists(QLOG):
        return 0
    return sum(1 for line in open(QLOG) if line.strip() and json.loads(line).get("track") == track)


def _usable(pkg, cache):
    """(rows, daq) of channels present in the package AND coherent (median in-band coh >= COH_MIN)."""
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


def _train_warp(pkg, theta, damping, train_keys, caches):
    """TRAIN-side FDAC warp: scale rho (fe=rho*fa) + clean-ridge band mask over fc, aggregated across train
    drives. Never touches the dev drive."""
    MAX_SHIFT = 0.06          # physical modal-error window (completed run: 2.5-3.3%)
    MIN_BAND = 25             # don't trust an over-narrow FDAC-selected band; fall back to full band
    rhos, band_masks, ridge_ws = [], None, []
    full_band = None
    for tk in train_keys:
        c = caches[tk]; fc = c["freqs"]; band = c["band"]
        full_band = band.copy()
        rows, cols = _usable(pkg, c)
        if len(rows) < 3:
            continue
        Hp = D.predict_H_damped(pkg, theta, damping, tk, fc)[rows][:, band]        # (n_use, n_bandf)
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
        band_masks = full_band                                    # fall back: full band, warp only
    return rho, band_masks


def _matched_peak_bins(pkg, theta, fc):
    """measured-freq bin indices at frozen-pairing matched peaks (calib_ok convention)."""
    f_el, _ = pkg.modes(theta)
    pairs = np.asarray(pkg.pairs); mfreqs = np.asarray(pkg.mfreqs, float)
    bins = []
    for r, k, mac in pairs:
        fm = mfreqs[int(r)]
        if mac < MAC_CAL or abs(f_el[int(k)] / fm - 1.0) > DF_CAL or fm < BAND[0] or fm > BAND[1]:
            continue
        bins.append(int(np.argmin(np.abs(fc - fm))))
    return bins


def score_candidate(cid, track, damping=None, theta_override=None, rationale="", family="",
                    ablation="", evidence="", enforce_budget=True, label=None):
    """Full LODO dev score for one candidate. ONE budgeted query. Returns SCALARS ONLY.
    damping: spec dict (femdamp) or None -> A0 fixed zeta=1%. label distinguishes candidates sharing a base
    cid (e.g. many damping specs on A0) for resumability/dedup."""
    label = label if label is not None else cid
    if enforce_budget and n_queries(track) >= BUDGET:
        raise RuntimeError(f"BUDGET EXCEEDED: track {track} at {n_queries(track)}/{BUDGET}")
    damping = damping if damping is not None else {"kind": "fixed", "zeta": 0.01}
    if D.damping_dim(damping) > 10:
        raise RuntimeError(f"damping dim {D.damping_dim(damping)} > 10 (amplitude-fit in disguise)")
    pkg = F.Package.load(cid)
    theta = np.asarray(theta_override, float) if theta_override is not None else \
        np.asarray(pkg.theta_map()[0], float)
    caches = load_caches()
    folds = {}
    for dev_key in F.DRIVE_KEYS:
        train_keys = [k for k in F.DRIVE_KEYS if k != dev_key]
        rho, band_mask = _train_warp(pkg, theta, damping, train_keys, caches)
        # global gain (dB) from TRAIN drives only (one scalar) -- NO per-mode/per-channel fit
        offs = []
        for tk in train_keys:
            c = caches[tk]; rows, cols = _usable(pkg, c)
            if len(rows) == 0:
                continue
            logHp = D.predict_logH_damped(pkg, theta, damping, tk, c["freqs"])[rows][:, c["band"]]
            ym = np.log10(np.abs(c["H1"][cols][:, c["band"]]) + 1e-300)
            offs.append(float(np.mean(ym - logHp)))
        gain_db = 20.0 * float(np.mean(offs)) if offs else 0.0
        # dev fold
        c = caches[dev_key]; fc = c["freqs"]; band = c["band"]
        rows, cols = _usable(pkg, c)
        p3s, p1s, frsfs = [], [], []
        if len(rows):
            logHp = D.predict_logH_damped(pkg, theta, damping, dev_key, fc)     # (n_sens, n_f)
            sel = band & band_mask if band_mask.shape[0] == len(fc) else band
            pk = [b for b in _matched_peak_bins(pkg, theta, fc) if sel[b]]
            for r, cidx in zip(rows, cols):
                ym = np.log10(np.abs(c["H1"][cidx][band]) + 1e-300)
                yp = logHp[r][band]
                p3 = MET.frac_corr(yp, ym)
                if not np.isnan(p3):
                    p3s.append(p3)
                # aligned over FDAC-selected band
                ypw = MET.apply_scale_warp(logHp[r], fc, rho)
                p1 = MET.frac_corr(ypw[sel], np.log10(np.abs(c["H1"][cidx][sel]) + 1e-300))
                if not np.isnan(p1):
                    p1s.append(p1)
                if pk:
                    Hm_pk = np.abs(c["H1"][cidx][pk])
                    Hp_pk = 10.0 ** (ypw[pk] + gain_db / 20.0)
                    r_, _, aerr = MET.frsf(Hp_pk, Hm_pk)
                    frsfs.append(aerr)
        folds[dev_key] = {"P3": float(np.median(p3s)) if p3s else None,
                          "P1p": float(np.median(p1s)) if p1s else None,
                          "P2p": float(np.median(frsfs)) if frsfs else None,
                          "n_ch": len(p3s), "rho": round(rho, 4),
                          "n_band": int(sel.sum()) if len(rows) else 0, "gain_dB": round(gain_db, 3)}
    p1 = np.array([folds[k]["P1p"] for k in F.DRIVE_KEYS if folds[k]["P1p"] is not None])
    p3 = np.array([folds[k]["P3"] for k in F.DRIVE_KEYS if folds[k]["P3"] is not None])
    p2 = [folds[k]["P2p"] for k in F.DRIVE_KEYS if folds[k]["P2p"] is not None]
    rec = {"cid": cid, "label": label, "track": track, "family": family, "ablation": ablation,
           "damping": damping, "damping_dim": D.damping_dim(damping),
           "P1p_mean": float(p1.mean()) if len(p1) else None,
           "P1p_folds": [round(float(folds[k]["P1p"]), 4) if folds[k]["P1p"] is not None else None
                         for k in F.DRIVE_KEYS],
           "P1p_se": float(p1.std(ddof=1) / np.sqrt(len(p1))) if len(p1) > 1 else None,
           "P3_mean": float(p3.mean()) if len(p3) else None,
           "P2p_mean": float(np.mean(p2)) if p2 else None,
           "alignment_gain": (float(p1.mean() - p3.mean()) if len(p1) and len(p3) else None),
           "folds": folds, "rationale": rationale, "evidence": evidence,
           "ts": time.strftime("%Y-%m-%dT%H:%M:%S")}
    with open(QLOG, "a") as f:
        f.write(json.dumps(rec) + "\n")
    return rec


def train_proxy(cid, damping=None, theta_override=None):
    """Cheap NO-sampler screening score (NOT a dev query; not logged): in-sample FDAC-aligned FRAC (P1') and
    amplitude error (|FRSF-1|) averaged over ALL loop drives, each predicted-vs-ITSELF (train quality). Used to
    rank proposals before spending the dev budget. Reads no dev-HELD-OUT structure -> no leakage."""
    damping = damping if damping is not None else {"kind": "fixed", "zeta": 0.01}
    pkg = F.Package.load(cid)
    theta = np.asarray(theta_override, float) if theta_override is not None else \
        np.asarray(pkg.theta_map()[0], float)
    caches = load_caches()
    p1s, p2s = [], []
    for k in F.DRIVE_KEYS:
        rho, band_mask = _train_warp(pkg, theta, damping, [k], caches)   # self as its own reference
        c = caches[k]; fc = c["freqs"]; band = c["band"]
        rows, cols = _usable(pkg, c)
        if len(rows) == 0:
            continue
        logHp = D.predict_logH_damped(pkg, theta, damping, k, fc)
        sel = band & band_mask if band_mask.shape[0] == len(fc) else band
        pk = [b for b in _matched_peak_bins(pkg, theta, fc) if sel[b]]
        gains = []
        for r, cidx in zip(rows, cols):
            ym = np.log10(np.abs(c["H1"][cidx][band]) + 1e-300)
            gains.append(np.mean(ym - logHp[r][band]))
        gain_db = 20.0 * float(np.mean(gains)) if gains else 0.0
        for r, cidx in zip(rows, cols):
            ypw = MET.apply_scale_warp(logHp[r], fc, rho)
            p1 = MET.frac_corr(ypw[sel], np.log10(np.abs(c["H1"][cidx][sel]) + 1e-300))
            if not np.isnan(p1):
                p1s.append(p1)
            if pk:
                Hm_pk = np.abs(c["H1"][cidx][pk]); Hp_pk = 10.0 ** (ypw[pk] + gain_db / 20.0)
                p2s.append(MET.frsf(Hp_pk, Hm_pk)[2])
    return {"proxy_P1p": float(np.median(p1s)) if p1s else None,
            "proxy_P2p": float(np.median(p2s)) if p2s else None}


def diagnose_train(cid="A0", damping=None, theta_override=None):
    """TRAIN-side diagnosis field for proposal generation (card §6.1): per-band in-sample amplitude error
    (median |FRSF-1|) + median warp rho, on all loop drives predicted vs themselves. NO held-out/dev read."""
    damping = damping if damping is not None else {"kind": "fixed", "zeta": 0.01}
    pkg = F.Package.load(cid)
    theta = np.asarray(theta_override, float) if theta_override is not None else \
        np.asarray(pkg.theta_map()[0], float)
    caches = load_caches()
    edges = D.BAND_EDGES
    band_frsf = {i: [] for i in range(len(edges) - 1)}
    rhos = []
    for k in F.DRIVE_KEYS:
        c = caches[k]; fc = c["freqs"]
        rows, cols = _usable(pkg, c)
        if len(rows) == 0:
            continue
        rho, _ = _train_warp(pkg, theta, damping, [k], caches)
        rhos.append(rho)
        Hp = np.abs(D.predict_H_damped(pkg, theta, damping, k, fc))
        for bi in range(len(edges) - 1):
            fb = (fc >= edges[bi]) & (fc < edges[bi + 1]) & c["band"]
            if fb.sum() == 0:
                continue
            for r, cidx in zip(rows, cols):
                Hm = np.abs(c["H1"][cidx][fb]); Hpp = Hp[r][fb]
                # gain-invariant amplitude shape mismatch in this band (median log-ratio spread)
                lr = np.log10((Hm + 1e-300) / (Hpp + 1e-300))
                band_frsf[bi].append(float(np.std(lr)))
    field = {"band_edges": edges.tolist(), "median_rho": float(np.median(rhos)) if rhos else 1.0,
             "band_amp_mismatch": {int(bi): (float(np.median(v)) if v else None)
                                   for bi, v in band_frsf.items()},
             "worst_band": int(max(band_frsf, key=lambda b: np.median(band_frsf[b]) if band_frsf[b] else -1))}
    return field


if __name__ == "__main__":
    cid, track = sys.argv[1], sys.argv[2]
    r = score_candidate(cid, track, rationale=" ".join(sys.argv[3:]))
    print(json.dumps({k: r[k] for k in ("cid", "P1p_mean", "P3_mean", "P2p_mean", "alignment_gain",
                                        "P1p_folds")}, indent=1))
