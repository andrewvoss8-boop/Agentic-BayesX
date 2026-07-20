#!/usr/bin/env python3
"""Dev scorer — the ONLY loop-side module that reads the drive caches. Returns SCALARS only.

NO-PER-MODE-LSQ: physics-honest selection (card §4.3). For every candidate/fold: θ_MAP (train-side .ash,
D6) + ONE global real gain per fold = mean log-offset on the fold's TRAIN drives. There is NO per-mode and
NO per-channel amplitude/phase fitting anywhere in this file; P1 (Pearson correlation of log10|H|) is
additionally gain-invariant by construction. Frozen Hungarian pairing (computed once per candidate at θ=1)
is used untouched.

Metrics (quantity_contracts Q2/Q3):
  P1(fold) = median over usable channels of Pearson corr(log10|H_pred|, log10|H_meas|), 45-260 Hz band
  P1       = mean over the 4 LODO folds (dev drives: +X/990x, +Z/990z, +Y/990y, +Z@900z; Test04 = vault)
  P2(fold) = RMSE [dB] of (20 log10|H_pred| + gain_dB - 20 log10|H_meas|) at matched measured peaks
Usable channel = median in-band coherence >= 0.6 (same rule for every candidate incl. A0).

Budget: HARD <=60 dev-scored candidates per track, counted from out/query_log.jsonl; exceeding raises.
"""
from __future__ import annotations
import json, os, sys, time
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import femlib as F

WS = F.WS
QLOG = os.path.join(WS, "out", "query_log.jsonl")
COH_MIN = 0.6
BUDGET = 60
MAC_CAL, DF_CAL = 0.50, 0.12          # matched-peak definition (pairing.py calib_ok convention)

_caches = None


def load_caches():
    """Dev drive caches only (the vault key is NEVER loaded here; vault.py handles it once, post-freeze)."""
    global _caches
    if _caches is None:
        _caches = {}
        for key in F.DRIVE_KEYS:
            c = np.load(os.path.join(F.NETCG_DATA, key + ".npz"), allow_pickle=True)
            fc = np.asarray(c["freqs"], float)
            band = (fc >= F.BAND[0]) & (fc <= F.BAND[1])
            coh = np.asarray(c["coherence"], float)
            _caches[key] = {"daq": [int(d) for d in c["daq"]],
                            "H1": np.asarray(c["H1"]), "coh": coh,
                            "freqs": fc, "band": band}
    return _caches


def n_queries(track):
    if not os.path.exists(QLOG):
        return 0
    n = 0
    for line in open(QLOG):
        if line.strip() and json.loads(line).get("track") == track:
            n += 1
    return n


def theta_map_cached(pkg):
    p = os.path.join(WS, "out", "theta_map", f"{pkg.cid}.json")
    os.makedirs(os.path.dirname(p), exist_ok=True)
    if os.path.exists(p):
        return np.asarray(json.load(open(p))["theta"], float)
    th, fun, ok = pkg.theta_map()
    json.dump({"theta": th.tolist(), "free_names": list(pkg.free_names),
               "nlp": fun, "success": ok}, open(p, "w"), indent=1)
    return th


def _channel_scores(pkg, theta, key, cache):
    """(corr per usable channel, resid dB at matched peaks per usable channel) for one drive."""
    fc = cache["freqs"]; band = cache["band"]
    logH = F.predict_logH(pkg, theta, key, fc)              # (n_sens, n_f) log10
    rows_of = {d: i for i, d in enumerate(pkg.sens_daq)}
    f_el, _ = pkg.modes(theta)
    pairs = np.asarray(pkg.pairs)
    mfreqs = np.asarray(pkg.mfreqs, float)
    # matched measured peaks (frozen pairing; calib_ok convention)
    pk_bins = []
    for r, k, mac in pairs:
        fm = mfreqs[int(r)]
        if mac < MAC_CAL or abs(f_el[int(k)] / fm - 1.0) > DF_CAL:
            continue
        if fm < F.BAND[0] or fm > F.BAND[1]:
            continue
        pk_bins.append(int(np.argmin(np.abs(fc - fm))))
    corrs, resid = [], []
    for i, d in enumerate(cache["daq"]):
        if d not in rows_of:
            continue
        coh_med = float(np.median(cache["coh"][i][band]))
        if coh_med < COH_MIN:
            continue
        ym = np.log10(np.abs(cache["H1"][i][band]) + 1e-300)
        yp = logH[rows_of[d]][band]
        if np.std(ym) < 1e-12 or np.std(yp) < 1e-12:
            continue
        corrs.append(float(np.corrcoef(ym, yp)[0, 1]))
        if pk_bins:
            bidx = np.where(band)[0]
            pos = [np.searchsorted(bidx, b) for b in pk_bins if b in set(bidx)]
            pos = [p for p in pos if p < len(ym)]
            if pos:
                resid.append(20.0 * (yp[pos] - ym[pos]))    # dB, gain added later
    return np.array(corrs), resid, len(pk_bins)


def score_candidate(cid, track, rationale="", family="", evidence="", enforce_budget=True,
                    theta_override=None):
    """Full LODO dev score for one candidate. ONE budgeted query. Returns SCALARS ONLY."""
    if enforce_budget:
        n = n_queries(track)
        if n >= BUDGET:
            raise RuntimeError(f"BUDGET EXCEEDED: track {track} already at {n}/{BUDGET} queries")
    pkg = F.Package.load(cid)
    theta = np.asarray(theta_override, float) if theta_override is not None else theta_map_cached(pkg)
    caches = load_caches()
    folds = {}
    for dev_key in F.DRIVE_KEYS:
        train_keys = [k for k in F.DRIVE_KEYS if k != dev_key]
        # gain (dB) from TRAIN drives only: mean measured-minus-predicted log offset
        offs = []
        for tk in train_keys:
            c = caches[tk]
            logH = F.predict_logH(pkg, theta, tk, c["freqs"])
            rows_of = {d: i for i, d in enumerate(pkg.sens_daq)}
            for i, d in enumerate(c["daq"]):
                if d not in rows_of:
                    continue
                if float(np.median(c["coh"][i][c["band"]])) < COH_MIN:
                    continue
                ym = np.log10(np.abs(c["H1"][i][c["band"]]) + 1e-300)
                offs.append(float(np.mean(ym - logH[rows_of[d]][c["band"]])))
        gain_db = 20.0 * float(np.mean(offs)) if offs else 0.0
        corrs, resid, n_pk = _channel_scores(pkg, theta, dev_key, caches[dev_key])
        p2 = float(np.sqrt(np.mean((np.concatenate(resid) + gain_db) ** 2))) if resid else None
        folds[dev_key] = {"P1": float(np.median(corrs)), "n_ch": int(len(corrs)),
                          "P2_dB": p2, "n_matched_peaks": int(n_pk),
                          "gain_dB": round(gain_db, 3)}
    p1s = np.array([folds[k]["P1"] for k in F.DRIVE_KEYS])
    p2s = [folds[k]["P2_dB"] for k in F.DRIVE_KEYS if folds[k]["P2_dB"] is not None]
    rec = {"cid": cid, "track": track, "family": family,
           "P1_mean": float(p1s.mean()), "P1_folds": [round(float(x), 4) for x in p1s],
           "P1_se": float(p1s.std(ddof=1) / np.sqrt(len(p1s))),
           "P2_mean_dB": float(np.mean(p2s)) if p2s else None,
           "n_matched_peaks_min": int(min(folds[k]["n_matched_peaks"] for k in F.DRIVE_KEYS)),
           "folds": folds, "rationale": rationale, "evidence": evidence,
           "ts": time.strftime("%Y-%m-%dT%H:%M:%S")}
    with open(QLOG, "a") as f:
        f.write(json.dumps(rec) + "\n")
    return rec


if __name__ == "__main__":
    cid, track = sys.argv[1], sys.argv[2]
    r = score_candidate(cid, track, rationale=sys.argv[3] if len(sys.argv) > 3 else "")
    print(json.dumps({k: r[k] for k in ("cid", "P1_mean", "P1_folds", "P1_se", "P2_mean_dB")}, indent=1))
