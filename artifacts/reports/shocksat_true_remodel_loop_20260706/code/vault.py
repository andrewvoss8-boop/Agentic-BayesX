#!/usr/bin/env python3
"""VAULT protocol (card §4.1, D1/D4: vault = Test04/+XY cache, excluded from all dev queries since run
start). Checker-enforced ordering:
  1) `freeze`  — write full vault-PREDICTION artifacts for the frozen models to out/finalists_frozen/
                 and record their SHA256 in VAULT_FREEZE.sha256. Uses ONLY the vault cache's metadata
                 (channel list / drive location / freq grid — test-plan info), NEVER H1/coherence.
  2) `grade`   — the ONE permitted read of the vault H1/coherence. Scores the FROZEN predictions
                 (no recomputation), writes out/vault_download.log (first-touch record; mtime must be
                 AFTER the freeze file) + out/vault_scores.json + data/vault_test04.npz (distilled copy).
Honest label: this vault tests generalization to a drive location (+XY corner) never used for selection in
THIS run; prior-run summaries of Test04 exist in the repo (residual risk, labeled in the packet).
"""
from __future__ import annotations
import hashlib, json, os, sys, time
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import femlib as F
import score as SC

WS = F.WS
FROZEN_DIR = os.path.join(WS, "out", "finalists_frozen")
COH_MIN = SC.COH_MIN


def freeze(cids):
    os.makedirs(FROZEN_DIR, exist_ok=True)
    # vault metadata only (freq grid + daq list); H1/coherence NOT read here
    c = np.load(os.path.join(F.NETCG_DATA, F.VAULT_KEY + ".npz"), allow_pickle=True)
    fc = np.asarray(c["freqs"], float)
    vdaq = [int(d) for d in c["daq"]]
    del c
    caches = SC.load_caches()                       # the 4 dev drives (train side for the gain)
    lines = []
    for cid in cids:
        pkg = F.Package.load(cid)
        theta = SC.theta_map_cached(pkg)
        logH = F.predict_logH(pkg, theta, F.VAULT_KEY, fc)
        # global gain (dB) from ALL 4 dev drives (all are train relative to the vault)
        offs = []
        rows_of = {d: i for i, d in enumerate(pkg.sens_daq)}
        for tk in F.DRIVE_KEYS:
            cc = caches[tk]
            lp = F.predict_logH(pkg, theta, tk, cc["freqs"])
            for i, d in enumerate(cc["daq"]):
                if d not in rows_of:
                    continue
                if float(np.median(cc["coh"][i][cc["band"]])) < COH_MIN:
                    continue
                ym = np.log10(np.abs(cc["H1"][i][cc["band"]]) + 1e-300)
                offs.append(float(np.mean(ym - lp[rows_of[d]][cc["band"]])))
        gain_db = 20.0 * float(np.mean(offs))
        # matched measured peak bins (frozen pairing, calib_ok) for vault P2
        f_el, _ = pkg.modes(theta)
        pk = []
        mfreqs = np.asarray(pkg.mfreqs, float)
        for r, k, mac in np.asarray(pkg.pairs):
            fm = mfreqs[int(r)]
            if mac < SC.MAC_CAL or abs(f_el[int(k)] / fm - 1.0) > SC.DF_CAL:
                continue
            if F.BAND[0] <= fm <= F.BAND[1]:
                pk.append(float(fm))
        path = os.path.join(FROZEN_DIR, f"{cid}_vault_pred.npz")
        np.savez_compressed(path, cid=cid, logH_pred=logH, freqs=fc,
                            sens_daq=np.asarray(pkg.sens_daq), gain_dB=gain_db,
                            matched_peak_freqs=np.asarray(pk), theta=theta,
                            frozen_at=time.strftime("%Y-%m-%dT%H:%M:%S"))
        h = hashlib.sha256(open(path, "rb").read()).hexdigest()
        lines.append(f"{h}  out/finalists_frozen/{cid}_vault_pred.npz")
        print(f"[freeze] {cid}: gain {gain_db:+.2f} dB, {len(pk)} matched peaks, sha {h[:12]}", flush=True)
    with open(os.path.join(WS, "VAULT_FREEZE.sha256"), "w") as f:
        f.write("\n".join(lines) + "\n")
    print(f"[freeze] VAULT_FREEZE.sha256 written ({len(cids)} models)")


def grade():
    fz = os.path.join(WS, "VAULT_FREEZE.sha256")
    assert os.path.exists(fz), "INTEGRITY: freeze first"
    # verify frozen artifacts unchanged
    for line in open(fz):
        line = line.strip()
        if not line:
            continue
        h, rel = line.split(None, 1)
        got = hashlib.sha256(open(os.path.join(WS, rel.strip()), "rb").read()).hexdigest()
        assert got == h, f"INTEGRITY: frozen artifact changed: {rel}"
    dl = os.path.join(WS, "out", "vault_download.log")
    assert not os.path.exists(os.path.join(WS, "out", "vault_scores.json")), \
        "INTEGRITY: vault already graded once"
    with open(dl, "w") as f:
        f.write(f"vault source = {F.VAULT_KEY}.npz (Test04/+XY fallback per D1/D4; no download needed)\n"
                f"first read of vault H1/coherence at {time.strftime('%Y-%m-%dT%H:%M:%S')}\n")
    src = os.path.join(F.NETCG_DATA, F.VAULT_KEY + ".npz")
    c = np.load(src, allow_pickle=True)
    fc = np.asarray(c["freqs"], float)
    band = (fc >= F.BAND[0]) & (fc <= F.BAND[1])
    H1 = np.asarray(c["H1"]); coh = np.asarray(c["coh"] if "coh" in c.files else c["coherence"], float)
    vdaq = [int(d) for d in c["daq"]]
    # distilled copy + provenance
    vp = os.path.join(WS, "data", "vault_test04.npz")
    np.savez_compressed(vp, H1=H1, coherence=coh, freqs=fc, daq=np.asarray(vdaq),
                        src_sha=hashlib.sha256(open(src, "rb").read()).hexdigest())
    med_coh = float(np.median(np.median(coh[:, band], axis=1)))
    out = {"vault": F.VAULT_KEY, "median_channel_coherence_inband": round(med_coh, 3),
           "coherence_gate_0.6": bool(med_coh >= 0.6), "models": {}}
    for fn in sorted(os.listdir(FROZEN_DIR)):
        z = np.load(os.path.join(FROZEN_DIR, fn), allow_pickle=True)
        cid = str(z["cid"])
        logH = np.asarray(z["logH_pred"]); daqs = [int(d) for d in z["sens_daq"]]
        gain_db = float(z["gain_dB"])
        rows_of = {d: i for i, d in enumerate(daqs)}
        corrs, resid = [], []
        pkf = np.asarray(z["matched_peak_freqs"], float)
        pk_bins = [int(np.argmin(np.abs(fc - f0))) for f0 in pkf]
        bidx = np.where(band)[0]
        for i, d in enumerate(vdaq):
            if d not in rows_of:
                continue
            if float(np.median(coh[i][band])) < COH_MIN:
                continue
            ym = np.log10(np.abs(H1[i][band]) + 1e-300)
            yp = logH[rows_of[d]][band]
            if np.std(ym) < 1e-12 or np.std(yp) < 1e-12:
                continue
            corrs.append(float(np.corrcoef(ym, yp)[0, 1]))
            pos = [np.searchsorted(bidx, b) for b in pk_bins if b in set(bidx)]
            pos = [p for p in pos if p < len(ym)]
            if pos:
                resid.append(20.0 * (yp[pos] - ym[pos]) + gain_db)
        out["models"][cid] = {
            "P1_vault": float(np.median(corrs)), "n_ch": len(corrs),
            "P2_vault_dB": float(np.sqrt(np.mean(np.concatenate(resid) ** 2))) if resid else None}
        print(f"[vault] {cid}: P1 {out['models'][cid]['P1_vault']:.4f} "
              f"({len(corrs)} ch), P2 {out['models'][cid]['P2_vault_dB']}", flush=True)
    json.dump(out, open(os.path.join(WS, "out", "vault_scores.json"), "w"), indent=1)
    print("[vault] out/vault_scores.json written — the vault has now been graded ONCE.")


if __name__ == "__main__":
    if sys.argv[1] == "freeze":
        freeze(sys.argv[2].split(","))
    elif sys.argv[1] == "grade":
        grade()
    else:
        raise SystemExit("freeze <cid,cid,...> | grade")
