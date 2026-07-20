#!/usr/bin/env python3
"""Card C follow-up (Andrew 2026-06-19): refine L5 mode-matching with MAC, and report L5 sensitivity to (how the
peaks are MATCHED) x (how many modes are KEPT).

L5 currently matches each measured consensus peak to the nearest FEM mode within 12% frequency (no shapes) -- crude
in this dense modal regime (40 FEM modes in 45-260 Hz; +/-12% spans several modes). Here we add a MAC-informed
matcher: at each consensus peak we take the operating-deflection shape (ODS) = complex H across OBSERVED channels at
that frequency, and match to the FEM mode of highest MAC (modal assurance criterion) within a frequency window --
so a peak goes to the FEM mode whose SHAPE it actually resembles, not just the nearest frequency.

Sweep:
  matching: freq-12% (baseline) | freq-5% (tighter) | MAC (highest-MAC within +/-15%)
  modes kept (top-K by channel support): 6 | 8 | 12 | 20 | all
Per config: calibrate L5 (NUTS modal-frequency likelihood) -> predict held-out peak |H| + band-GRMS with the
apples-to-apples PEAK gain -> proper scores. Across N splits. Output: out/l5_matching_sensitivity_summary.json.

Honest note: D20 found single-impact ODS shapes are noisy (dense-mode superposition), so MAC-from-ODS may be weak;
we REPORT the realized MAC values so the reader sees whether MAC actually informs the match.
"""
from __future__ import annotations
import json, sys, time
from pathlib import Path
from types import SimpleNamespace
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import realfrf as rf
import heldout_qoi as hq
import modal_feature as mf
import score as SC

WS = Path(__file__).resolve().parent.parent
CD = WS / "out" / "l5_sens"; CD.mkdir(parents=True, exist_ok=True)
qoi_peak = rf.core.qoi_peak; qoi_band = rf.core.qoi_band


def macv(ods, phi):
    return float(np.abs(np.vdot(phi, ods)) ** 2 / ((np.vdot(ods, ods).real) * (phi @ phi) + 1e-30))


def match_peaks(method, tol_pct, femf, peak_freqs, support, ods=None, phi_fem_obs=None):
    """Greedy match (high-support peaks first). Returns list of (fem_idx, meas_hz, support, mac_or_None)."""
    order = np.argsort(-np.asarray(support))                      # high-support first
    used, pairs = set(), []
    for r in order:
        pf = peak_freqs[r]
        cand = [j for j in range(len(femf)) if abs(femf[j] - pf) / pf <= tol_pct / 100 and j not in used]
        if not cand:
            continue
        if method == "mac":
            macs = [macv(ods[r], phi_fem_obs[:, j]) for j in cand]
            j = cand[int(np.argmax(macs))]; mac = float(np.max(macs))
        else:                                                    # nearest frequency
            j = cand[int(np.argmin([abs(femf[c] - pf) for c in cand]))]; mac = None
        used.add(j); pairs.append((j, float(pf), int(support[r]), mac))
    return pairs


def score_config(seed, method, tol_pct, keep, warmup, samples, chains, n_draws):
    R = rf.load_reduced(); meas = rf.reprocess_measured(list(range(1, rf.N_ACCEL_RECORDERS + 1)))
    ch = rf.build_channels(R, meas["daq"])
    fr = meas["freqs"]; fb = (fr >= rf.BAND[0]) & (fr <= rf.BAND[1]); freqs = fr[fb]
    didx = {d: i for i, d in enumerate(meas["daq"])}
    dr = np.array([meas["dyn_range"][didx[d]] for d in ch.daq]); elig = np.where(dr >= hq.DR_MIN)[0]
    rng = np.random.default_rng(seed); perm = rng.permutation(elig); n_obs = int(round(0.6 * len(perm)))
    obs_pos = np.sort(perm[:n_obs]); ho_pos = np.sort(perm[n_obs:])
    obs_rows = ch.rows[obs_pos]; ho_rows = ch.rows[ho_pos]
    obs_daqs = [ch.daq[p] for p in obs_pos]; ho_daqs = [ch.daq[p] for p in ho_pos]
    n_o, n_ho = len(obs_pos), len(ho_pos)
    pf, support = mf.extract_measured_modes(meas, SimpleNamespace(daq=obs_daqs))
    femf = mf.fem_modes_np(R, np.ones(9))
    K = R.A_fix + R.A.sum(0); lam, Q = np.linalg.eigh(K); phi_fem_obs = obs_rows @ Q       # (n_o, 74)
    ods = np.array([np.array([meas["H"][didx[d]][fb] for d in obs_daqs])[:, int(np.argmin(np.abs(freqs - f)))]
                    for f in pf]) if len(pf) else np.zeros((0, n_o), complex)               # (n_peaks, n_o) complex
    if method == "orig":                                          # the EXACT deployed L5 matcher (mf.match)
        sidx = {round(float(f), 4): int(s) for f, s in zip(pf, support)}
        op, _ = mf.match(R, pf, tol_pct=tol_pct)
        pairs = [(j, mhz, sidx.get(round(float(mhz), 4), 1), None) for (j, mhz) in op]
    else:
        pairs = match_peaks(method, tol_pct, femf, pf, support, ods=ods, phi_fem_obs=phi_fem_obs)
    pairs = sorted(pairs, key=lambda p: -p[2])[:keep]                                        # keep top-K by support
    if len(pairs) < 3:
        return {"seed": seed, "n_modes": len(pairs), "skipped": True}
    omi = np.array([p[0] for p in pairs]); owh = np.array([p[1] for p in pairs])
    macs = [p[3] for p in pairs if p[3] is not None]
    theta, _, cdiag = mf.calibrate_modal(R, omi, owh, seed=20260617, warmup=warmup, samples=samples, chains=chains)
    # held-out peak/band with apples-to-apples PEAK gain
    sub = np.linspace(0, theta.shape[0] - 1, min(theta.shape[0], n_draws)).astype(int)
    all_rows = np.vstack([obs_rows, ho_rows])
    lm = rf.fem_logmag_batch(R, freqs, theta[sub], all_rows, ch.drive_row, zeta=rf.ZETA_NOM)
    lm_obs, lm_ho = lm[:, :, :n_o], lm[:, :, n_o:]
    ptru_o = np.array([qoi_peak(np.abs(meas["H"][didx[d]][fb])) for d in obs_daqs])
    peak_tru = np.array([qoi_peak(np.abs(meas["H"][didx[d]][fb])) for d in ho_daqs])
    band_tru = np.array([qoi_band(np.abs(meas["H"][didx[d]][fb]), freqs) for d in ho_daqs])
    pk_obs0 = np.array([[qoi_peak(np.exp(lm_obs[j, :, k])) for k in range(n_o)] for j in range(len(sub))])
    c = np.array([float(np.median(np.log(ptru_o + 1e-300) - np.log(pk_obs0[j] + 1e-300))) for j in range(len(sub))])
    lm_ho_g = lm_ho + c[:, None, None]; lm_obs_g = lm_obs + c[:, None, None]
    peak_h = np.array([[qoi_peak(np.exp(lm_ho_g[j, :, k])) for k in range(n_ho)] for j in range(len(sub))])
    band_h = np.array([[qoi_band(np.exp(lm_ho_g[j, :, k]), freqs) for k in range(n_ho)] for j in range(len(sub))])
    peak_o = np.array([[qoi_peak(np.exp(lm_obs_g[j, :, k])) for k in range(n_o)] for j in range(len(sub))])
    band_o = np.array([[qoi_band(np.exp(lm_obs_g[j, :, k]), freqs) for k in range(n_o)] for j in range(len(sub))])
    btru_o = np.array([qoi_band(np.abs(meas["H"][didx[d]][fb]), freqs) for d in obs_daqs])
    sig_pk = float(np.std(np.log(np.median(peak_o, 0) + 1e-300) - np.log(ptru_o + 1e-300)))
    sig_bd = float(np.std(np.log(np.median(band_o, 0) + 1e-300) - np.log(btru_o + 1e-300)))
    g2 = np.random.default_rng(seed + 4)
    peak_hd = peak_h * np.exp(g2.normal(0, max(sig_pk, 1e-3), peak_h.shape))
    band_hd = band_h * np.exp(g2.normal(0, max(sig_bd, 1e-3), band_h.shape))
    sp = [SC.score_qoi(peak_hd[:, k], peak_tru[k]) for k in range(n_ho)]
    sb = [SC.score_qoi(band_hd[:, k], band_tru[k]) for k in range(n_ho)]
    return {"seed": seed, "n_modes": len(pairs), "mean_MAC": (float(np.mean(macs)) if macs else None),
            "calib_rhat": cdiag["max_rhat"], "calib_converged": bool(cdiag["converged"]),
            "matched_fem_hz": [round(float(femf[i]), 1) for i in omi],
            "peak_IS": float(np.mean([x["interval_score"] for x in sp])),
            "peak_cov": float(np.mean([x["covered"] for x in sp])),
            "band_IS": float(np.mean([x["interval_score"] for x in sb])),
            "band_cov": float(np.mean([x["covered"] for x in sb])), "skipped": False}


CONFIGS = ([("orig", 12, 999), ("freq", 12, 999), ("freq", 5, 999), ("mac", 15, 999)]
           + [("mac", 15, k) for k in (6, 8, 12, 20)]
           + [("freq", 12, k) for k in (6, 8, 12, 20)])


def run(n_splits=10, warmup=500, samples=500, chains=4, n_draws=150):
    t0 = time.time(); blocks = {}
    for method, tol, keep in CONFIGS:
        name = f"{method}{tol}_keep{'all' if keep > 100 else keep}"
        rows = []
        for s in range(n_splits):
            f = CD / f"{name}_s{s}.json"
            if f.exists():
                rows.append(json.loads(f.read_text()))
            else:
                r = score_config(s, method, tol, keep, warmup, samples, chains, n_draws)
                f.write_text(json.dumps(r)); rows.append(r)
        ok = [r for r in rows if not r.get("skipped")]
        if not ok:
            continue
        mm = [r["mean_MAC"] for r in ok if r.get("mean_MAC") is not None]
        blocks[name] = {"matching": method, "tol_pct": tol, "keep": ("all" if keep > 100 else keep),
                        "n_modes_med": float(np.median([r["n_modes"] for r in ok])),
                        "mean_MAC_med": (float(np.median(mm)) if mm else None),
                        "converged_frac": float(np.mean([r["calib_converged"] for r in ok])),
                        "peak_IS_med": float(np.median([r["peak_IS"] for r in ok])),
                        "peak_cov_med": float(np.median([r["peak_cov"] for r in ok])),
                        "band_IS_med": float(np.median([r["band_IS"] for r in ok])),
                        "n_splits": len(ok)}
        b = blocks[name]
        print(f"  {name:16s}: n_modes {b['n_modes_med']:.0f} MAC {b['mean_MAC_med'] if b['mean_MAC_med'] else float('nan'):.2f} "
              f"conv {b['converged_frac']:.2f} | peak IS {b['peak_IS_med']:.0f} cov {b['peak_cov_med']:.2f} | "
              f"band IS {b['band_IS_med']:.0f}", flush=True)
        (WS / "out" / "l5_matching_sensitivity_summary.json").write_text(json.dumps(
            {"deliverable": "L5_mode_matching_sensitivity (matching x n_modes; apples-to-apples peak gain)",
             "n_splits": n_splits, "configs": blocks, "runtime_s": time.time() - t0}, indent=2))
    print("\nL5 MATCHING SENSITIVITY DONE.")
    return blocks


if __name__ == "__main__":
    run(int(sys.argv[1]) if len(sys.argv) > 1 else 10)
