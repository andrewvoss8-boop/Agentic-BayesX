#!/usr/bin/env python3
"""Vault grading (card §4.1): the +XY / Test04 drive (m_xy_990xy), excluded from ALL dev queries since run
start, graded ONCE after finalists are SHA-frozen. The FDAC warp + global gain come from the 4 DEV drives
(train); the vault drive is the single held-out grade. Same FDAC-aligned metric (P1'/P3/P2').
  python3 code/vault.py freeze   -> writes VAULT_FREEZE.sha256 (must precede any grade)
  python3 code/vault.py grade    -> reads the vault cache ONCE, writes out/vault_scores.json + download.log
"""
import json, os, sys, glob, hashlib, time
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import femdamp as D
import femlib as F
import metrics as MET
import score as SC

WS = D.WS
VKEY = F.VAULT_KEY
BAND = D.BAND


def freeze():
    fin = json.load(open(os.path.join(WS, "out", "finalists.json")))
    h = hashlib.sha256()
    files = [os.path.join(WS, "out", "finalists.json"), os.path.join(WS, "out", "a0d.json")]
    for cid in sorted(set(fin["freeze"])):
        files.append(os.path.join(WS, "data", "packages", cid + ".npz"))
    lines = []
    for f in files:
        if os.path.exists(f):
            d = hashlib.sha256(open(f, "rb").read()).hexdigest()
            lines.append(f"{d}  {os.path.relpath(f, WS)}")
            h.update(d.encode())
    open(os.path.join(WS, "VAULT_FREEZE.sha256"), "w").write("\n".join(lines) + "\n")
    print("FROZEN finalists:\n" + "\n".join(lines))


def grade():
    fin = json.load(open(os.path.join(WS, "out", "finalists.json")))
    a0d = json.load(open(os.path.join(WS, "out", "a0d.json")))["best_damping"]
    # THE single vault read (log it)
    c = np.load(os.path.join(F.NETCG_DATA, VKEY + ".npz"), allow_pickle=True)
    fc = np.asarray(c["freqs"], float); band = (fc >= BAND[0]) & (fc <= BAND[1])
    coh = np.asarray(c["coherence"], float); H1 = np.asarray(c["H1"]); vdaq = [int(x) for x in c["daq"]]
    open(os.path.join(WS, "out", "vault_download.log"), "w").write(
        f"vault {VKEY} read ONCE at {time.strftime('%Y-%m-%dT%H:%M:%S')} after freeze; "
        f"{len(vdaq)} channels, {int(band.sum())} in-band lines\n")
    dev_caches = SC.load_caches()
    specs = {"A0_enr": ("A0_enr", {"kind": "fixed", "zeta": 0.01}),
             "A0d_enr": ("A0_enr", a0d),
             "c06_enr": ("c06_tb_xface_enr", {"kind": "fixed", "zeta": 0.01}),
             "a04_enr": ("a04_welds_t074_enr", {"kind": "fixed", "zeta": 0.01}),
             "b_c06_enr": ("c06_tb_xface_enr", a0d),
             "rnd003_enr": ("rnd003_enr", {"kind": "fixed", "zeta": 0.01})}
    scores = {}
    for label, (cid, dmp) in specs.items():
        pkg = F.Package.load(cid)
        th = np.asarray(pkg.theta_map()[0], float)
        # train FDAC warp + gain from the 4 DEV drives
        rho, band_mask = SC._train_warp(pkg, th, dmp, F.DRIVE_KEYS, dev_caches)
        offs = []
        for tk in F.DRIVE_KEYS:
            cc = dev_caches[tk]; rows, cols = SC._usable(pkg, cc)
            if len(rows) == 0:
                continue
            lp = D.predict_logH_damped(pkg, th, dmp, tk, cc["freqs"])[rows][:, cc["band"]]
            ym = np.log10(np.abs(cc["H1"][cols][:, cc["band"]]) + 1e-300)
            offs.append(float(np.mean(ym - lp)))
        gain_db = 20.0 * float(np.mean(offs)) if offs else 0.0
        # predict + grade the vault drive
        rows_of = {d: i for i, d in enumerate(pkg.sens_daq)}
        logHp = D.predict_logH_damped(pkg, th, dmp, VKEY, fc)
        sel = band & band_mask if band_mask.shape[0] == len(fc) else band
        p1s, p3s, cohs = [], [], []
        for i, d in enumerate(vdaq):
            if d not in rows_of:
                continue
            if float(np.median(coh[i][band])) < 0.6:
                continue
            cohs.append(float(np.median(coh[i][band])))
            ym = np.log10(np.abs(H1[i][band]) + 1e-300)
            yp = logHp[rows_of[d]][band]
            p3 = MET.frac_corr(yp, ym)
            if not np.isnan(p3):
                p3s.append(p3)
            ypw = MET.apply_scale_warp(logHp[rows_of[d]], fc, rho)
            p1 = MET.frac_corr(ypw[sel], np.log10(np.abs(H1[i][sel]) + 1e-300))
            if not np.isnan(p1):
                p1s.append(p1)
        scores[label] = {"cid": cid, "vault_P1p": round(float(np.median(p1s)), 4) if p1s else None,
                         "vault_P3": round(float(np.median(p3s)), 4) if p3s else None,
                         "n_ch": len(p1s), "median_coh": round(float(np.median(cohs)), 3) if cohs else None,
                         "damping": dmp}
        print(f"  {label:12s} vault P1'={scores[label]['vault_P1p']} P3={scores[label]['vault_P3']} "
              f"(n_ch {len(p1s)}, coh {scores[label]['median_coh']})", flush=True)
    out = {"vault_key": VKEY, "scores": scores,
           "note": "vault = +XY/Test04, held out from ALL selection since run start (label: not never-seen-by-"
                   "any-run; also the 'easy' location per the completed run's uniform dev-vs-vault gap). FDAC "
                   "warp+gain from the 4 dev drives; graded ONCE after freeze."}
    json.dump(out, open(os.path.join(WS, "out", "vault_scores.json"), "w"), indent=2)
    # dev-vs-vault gap
    fin_scores = fin["scores"]
    gap = {lab: {"dev_P1p": fin_scores.get(lab, {}).get("P1p_mean"),
                 "vault_P1p": scores[lab]["vault_P1p"]} for lab in scores if lab in fin_scores}
    json.dump(gap, open(os.path.join(WS, "out", "dev_vs_vault.json"), "w"), indent=2)


if __name__ == "__main__":
    (freeze if sys.argv[1] == "freeze" else grade)()
