#!/usr/bin/env python3
"""Gate F — FDAC/FRAC/FRSF correctness on synthetic pairs (card §7):
 (i)   identical FRFs      -> FRAC=1, FRSF=1, FDAC ridge on the diagonal
 (ii)  pure frequency shift-> raw FRAC drops, FDAC ridge tracks the shift, FDAC-aligned FRAC ~ 1
 (iii) pure amplitude scale-> FRAC ~ 1 but FRSF = the scale
 (iv)  180-deg phase flip  -> improved (cosine) FDAC = -1, not +1
"""
import json, os, sys
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import metrics as MET
from femdamp import frf_from_modes

WS = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def synth(fmodes, residues, fc, zeta=0.01):
    """multi-sensor complex FRF: residues (n_sens, n_modes)."""
    wi = 2 * np.pi * np.asarray(fmodes, float)
    zi = np.full(len(fmodes), zeta)
    ei = np.zeros(len(fmodes))
    return frf_from_modes(np.asarray(residues, float), wi, zi, ei, fc)  # (n_sens, n_freq)


def main():
    rng = np.random.default_rng(20260710)
    fc = np.linspace(45, 260, 431)                  # ~0.5 Hz fine grid for the gate
    fmodes = np.array([60., 95., 140., 190., 235.])
    ns = 12
    residues = rng.normal(0, 1, (ns, len(fmodes)))
    Hm = synth(fmodes, residues, fc)
    Lm = MET.logmag(Hm)

    res = {}

    # (i) identical
    Lp = MET.logmag(synth(fmodes, residues, fc))
    corr = np.median([MET.frac_corr(Lp[i], Lm[i]) for i in range(ns)])
    r, rdb, aerr = MET.frsf(synth(fmodes, residues, fc), Hm)
    F = MET.fdac_surface(synth(fmodes, residues, fc), Hm, cosine=True)
    fa, fes, val = MET.fdac_ridge(F, fc, fc)
    diag_frac = float(np.mean(np.abs(fes - fa) <= (fc[1] - fc[0]) * 1.5))
    res["identical"] = {"pass": bool(corr > 0.999 and aerr < 1e-3 and diag_frac > 0.9),
                        "frac": round(float(corr), 4), "frsf_abs_err": round(aerr, 5),
                        "ridge_on_diag_frac": round(diag_frac, 3)}

    # (ii) pure frequency shift: predicted peaks at rho*fmodes. Success = raw corr drops, the FDAC ridge
    # recovers the shift (rho_est ~ 1/rho), and the aligned corr climbs back near 1.
    rho = 1.05
    Hp = synth(rho * fmodes, residues, fc)
    Lp = MET.logmag(Hp)
    raw = np.median([MET.frac_corr(Lp[i], Lm[i]) for i in range(ns)])
    F = MET.fdac_surface(Hp, Hm, cosine=True)
    fa, fes, val = MET.fdac_ridge(F, fc, fc)
    rho_est = MET.estimate_scale_warp(fa, fes, val, vmin=0.3)   # ~ 1/rho
    Lp_w = MET.apply_scale_warp(Lp, fc, rho_est)
    aligned = np.median([MET.frac_corr(Lp_w[i], Lm[i]) for i in range(ns)])
    res["freq_shift"] = {"pass": bool(raw < 0.9 and aligned > 0.98 and (aligned - raw) > 0.1
                                      and abs(rho_est - 1.0 / rho) < 0.02),
                         "raw_frac": round(float(raw), 4), "aligned_frac": round(float(aligned), 4),
                         "alignment_gain": round(float(aligned - raw), 4),
                         "rho_true_inv": round(1 / rho, 4), "rho_est": round(float(rho_est), 4)}

    # (iii) pure amplitude scale: Hp = Hm / c  (predicted c-x too small) -> FRSF = c
    c = 2.5
    Hp = Hm / c
    Lp = MET.logmag(Hp)
    corr = np.median([MET.frac_corr(Lp[i], Lm[i]) for i in range(ns)])
    r, rdb, aerr = MET.frsf(Hp, Hm)                 # median |Hm|/|Hp| = c
    res["amp_scale"] = {"pass": bool(corr > 0.999 and abs(r - c) / c < 1e-3),
                        "frac": round(float(corr), 4), "frsf": round(r, 4), "c_true": c}

    # (iv) 180-deg phase flip: cosine FDAC diagonal = -1
    Hp = -Hm
    F = MET.fdac_surface(Hp, Hm, cosine=True)
    diag = float(np.median(np.diag(F)))
    res["phase_flip"] = {"pass": bool(diag < -0.99), "cosine_fdac_diag": round(diag, 4)}

    passed = all(v["pass"] for v in res.values())
    res["pass"] = bool(passed)
    os.makedirs(os.path.join(WS, "out"), exist_ok=True)
    json.dump(res, open(os.path.join(WS, "out", "gate_F.json"), "w"), indent=2)
    print(json.dumps(res, indent=2))
    return 0 if passed else 1


if __name__ == "__main__":
    sys.exit(main())
