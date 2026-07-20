#!/usr/bin/env python3
"""wide_distill — wide-band re-distillation of one drive's FRF cache from its raw modal-hammer zip (card §4).

Byte-identical processing to the existing 45-260 Hz caches (REUSES multiref_frf._load_hit and ._spectra —
N=122880 @ 250 kHz, 2 ms force window, exponential response window end=0.05, impact-aligned pre_gap=200,
ensemble H1 = ΣYF*/Σ|F|², multi-hit coherence); ONLY the kept band changes: 45 Hz -> WBAND_TOP.

DISK PROTOCOL (card §4, hard): one .mat member extracted at a time, distilled, deleted. The zip is deleted
by the caller AFTER the drive's overlap validation passes. Per-hit force health -> data/force_health.json
(Test07 lesson: dead force channel = ~1 lb noise; live modal hits are tens-hundreds of lbf).

Usage: python3 wide_distill.py <cache_key>       (m_xpos_990x | m_zpos_990z | m_ypos_990y | m_zpos_900z | m_xy_990xy)
"""
from __future__ import annotations
import json, os, sys, time, zipfile
import numpy as np

WS = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
ROOT = os.path.abspath(os.path.join(WS, "..", "..", ".."))
sys.path.insert(0, os.path.join(ROOT, "artifacts/reports/shocksat_psd_envelope_twin_20260623/code"))
import multiref_frf as mr                          # noqa: E402  (read-only reuse)
import realfrf as rf                               # noqa: E402

FS = rf.FS
N_MODAL = 122880                                   # the caches' actual frame (build_ypos_cache convention)
WBAND = (45.0, 3000.0)                             # kept band; certification decides the SCORED top
PROCK = dict(force_ms=rf.PROC["force_ms"], exp_end=rf.PROC["exp_end"], pre_gap=rf.PROC["pre_gap"])
FORCE_LIVE_LBF = (5.0, 5000.0)                     # dead-channel gate: Test07's dead force was ~1 lb noise
COH_CERT = 0.6                                     # certified-ceiling coherence threshold (Q6)

REG = {
    "m_xpos_990x": dict(zip="Test01_ModalHammer_990x.zip", xyz=(9.0, 7.6, 0.6), axis="X", label="+X (990)"),
    "m_zpos_990z": dict(zip="Test02_ModalHammer_990z.zip", xyz=(9.0, 7.8, 0.0), axis="Z", label="+Z (990)"),
    "m_ypos_990y": dict(zip="Test03_ModalHammer_990y.zip", xyz=(8.5, 9.0, 1.0), axis="Y", label="+Y"),
    "m_zpos_900z": dict(zip="Test06_ModalHammer_900z.zip", xyz=(9.0, 0.0, 0.0), axis="Z", label="+Z (900)"),
    "m_xy_990xy": dict(zip="Test04_ModalHammer_990xy.zip", xyz=(9.0, 9.0, 1.1), axis="XY", label="+XY (990)"),
}
EXISTING = {k: os.path.join(ROOT, "artifacts/reports/shocksat_psd_envelope_twin_20260623/data/multiref_modal",
                            k + ".npz") for k in REG}
EXISTING["m_ypos_990y"] = os.path.join(
    ROOT, "artifacts/reports/shocksat_netcg_method_selection_20260701/data/multiref_modal/m_ypos_990y.npz")


def merge_json(path, key, val):
    d = json.load(open(path)) if os.path.exists(path) else {}
    d[key] = val
    json.dump(d, open(path, "w"), indent=1)


def distill(key):
    t0 = time.time()
    reg = REG[key]
    zp = os.path.join(WS, "data", "zips", reg["zip"])
    if not os.path.exists(zp):
        raise SystemExit(f"zip missing: {zp}")
    tmpd = os.path.join(WS, "data", "tmp"); os.makedirs(tmpd, exist_ok=True)
    outd = os.path.join(WS, "data", "multiref_wide"); os.makedirs(outd, exist_ok=True)
    daqs = [d for d in range(1, rf.N_ACCEL_RECORDERS + 1) if d not in rf.BAD_DAQ]
    freqs = np.fft.rfftfreq(N_MODAL, 1 / FS)
    bm = (freqs >= WBAND[0]) & (freqs <= WBAND[1])
    Sxx = np.zeros(bm.sum())
    Sxy = np.zeros((len(daqs), bm.sum()), complex)
    Syy = np.zeros((len(daqs), bm.sum()))
    used, skipped, ips, health = [], [], [], []
    zf = zipfile.ZipFile(zp)
    mats = sorted(n for n in zf.namelist() if n.lower().endswith(".mat"))
    print(f"{key}: {len(mats)} .mat members in {reg['zip']}", flush=True)
    for name in mats:
        base = os.path.basename(name)
        th = time.time()
        loc = zf.extract(name, tmpd)                       # ONE hit on disk at a time
        try:
            F, Y = mr._load_hit(loc, daqs)
            h = {"hit": base, "force_std_lb": float(np.std(F)), "force_absmax_lb": float(np.abs(F).max()),
                 "impact_idx": int(np.argmax(np.abs(F))), "n_samples": int(len(F))}
            if not (FORCE_LIVE_LBF[0] <= h["force_absmax_lb"] <= FORCE_LIVE_LBF[1]):
                h["status"] = "DROPPED_dead_or_unphysical_force"
                health.append(h); skipped.append(base)
                print(f"  {base}: force absmax {h['force_absmax_lb']:.2f} lb -> DROPPED", flush=True)
                continue
            sp = mr._spectra(F, Y, N_MODAL, PROCK["force_ms"], PROCK["exp_end"], PROCK["pre_gap"])
            if sp is None:
                h["status"] = "skipped_window_does_not_fit"
                health.append(h); skipped.append(base)
                print(f"  {base}: impact too late for window -> skipped", flush=True)
                continue
            Ff, Yf, ip = sp
            Sxx += (np.abs(Ff) ** 2)[bm]
            Sxy += Yf[:, bm] * np.conj(Ff)[bm]
            Syy += (np.abs(Yf) ** 2)[:, bm]
            used.append(base); ips.append(int(ip))
            h["status"] = "used"
            health.append(h)
            print(f"  {base}: used (F max {h['force_absmax_lb']:.1f} lb, {time.time()-th:.0f}s)", flush=True)
        finally:
            os.remove(loc)
    if not used:
        raise SystemExit(f"{key}: no usable hits (all dropped/skipped)")
    H1 = Sxy / Sxx[None, :]
    coh = (np.abs(Sxy) ** 2) / (Sxx[None, :] * Syy + 1e-300)
    outp = os.path.join(outd, key + "_wide.npz")
    np.savez_compressed(outp, freqs=freqs[bm], H1=H1, coherence=coh, daq=np.array(daqs),
                        xyz=np.array(reg["xyz"]), axis=reg["axis"], label=reg["label"],
                        instrument="modal", N=N_MODAL, n_hits_used=len(used), used=np.array(used),
                        impact_idx=np.array(ips), Sxx=Sxx)
    merge_json(os.path.join(WS, "data", "force_health.json"), key,
               {"hits": health, "n_used": len(used), "n_skipped": len(skipped),
                "coh_floor_uncorrelated": 1.0 / len(used)})

    # ---------------- overlap validation vs the existing cache (Q5 hard gate) ----------------
    ex = np.load(EXISTING[key], allow_pickle=True)
    fex = np.asarray(ex["freqs"], float)
    fw = freqs[bm]
    jj = np.array([int(np.argmin(np.abs(fw - f))) for f in fex])
    assert np.abs(fw[jj] - fex).max() < 1e-6, "bin grids differ"
    Hex, Hw = np.asarray(ex["H1"]), H1[:, jj]
    assert list(ex["daq"]) == daqs, "channel sets differ"
    corrs = []
    for i in range(Hex.shape[0]):
        a, b = np.abs(Hex[i]), np.abs(Hw[i])
        corrs.append(float(np.corrcoef(a, b)[0, 1]))
    dlog = np.abs(np.log10(np.abs(Hw) + 1e-300) - np.log10(np.abs(Hex) + 1e-300))
    same_hits = list(ex["used"]) == used
    val = {"pass": bool(np.median(corrs) >= 0.999 and float(np.median(dlog)) <= 0.01),
           "excluded": False, "reason": "",
           "corr_median": float(np.median(corrs)), "corr_min": float(np.min(corrs)),
           "med_abs_dlog10": float(np.median(dlog)), "max_abs_dlog10": float(np.max(dlog)),
           "same_hits_as_existing": bool(same_hits), "n_hits_used": len(used),
           "existing_hits": [str(u) for u in ex["used"]], "wide_hits": used}
    if not val["pass"]:
        val["excluded"], val["reason"] = True, "overlap validation failed; diagnose before use"
    ov_p = os.path.join(WS, "out", "overlap_validation.json")
    d = json.load(open(ov_p)) if os.path.exists(ov_p) else {"drives": {}}
    d["drives"][key] = val
    d["n_wide_drives"] = sum(1 for v in d["drives"].values() if v.get("pass"))
    json.dump(d, open(ov_p, "w"), indent=1)

    # ---------------- certified ceiling (Q6) ----------------
    med_coh = np.median(coh, axis=0)
    above = med_coh >= COH_CERT
    runs = []
    s = None
    for i, a in enumerate(above):
        if a and s is None:
            s = i
        elif not a and s is not None:
            runs.append((s, i - 1)); s = None
    if s is not None:
        runs.append((s, len(above) - 1))
    fwb = freqs[bm]
    ceil_last = float(fwb[runs[-1][1]]) if runs else None
    ceil_first = float(fwb[runs[0][1]]) if runs else None
    frac_below_last = float(above[:runs[-1][1] + 1].mean()) if runs else 0.0
    cert = {"ceiling_hz_last_run": ceil_last, "ceiling_hz_first_run": ceil_first,
            "frac_bins_above_thresh_below_ceiling": frac_below_last,
            "n_runs": len(runs), "coh_threshold": COH_CERT,
            "n_hits": len(used), "coh_floor_uncorrelated": round(1.0 / len(used), 3),
            "med_coh_200_500": float(np.median(med_coh[(fwb >= 200) & (fwb <= 500)])),
            "med_coh_500_1000": float(np.median(med_coh[(fwb >= 500) & (fwb <= 1000)])),
            "med_coh_1000_2000": float(np.median(med_coh[(fwb >= 1000) & (fwb <= 2000)])),
            "med_coh_2000_3000": float(np.median(med_coh[(fwb >= 2000) & (fwb <= 3000)]))}
    merge_json(os.path.join(WS, "out", "certified_ceiling.json"), key, cert)
    with open(os.path.join(WS, "out", "runtime_log.jsonl"), "a") as f:
        f.write(json.dumps({"step": f"wide_distill_{key}", "active_s": round(time.time() - t0, 1)}) + "\n")
    print(json.dumps({"key": key, "validation": {k: val[k] for k in
                      ("pass", "corr_median", "med_abs_dlog10", "same_hits_as_existing")},
                      "ceiling": cert}, indent=1), flush=True)
    return val["pass"]


if __name__ == "__main__":
    ok = distill(sys.argv[1])
    sys.exit(0 if ok else 2)
