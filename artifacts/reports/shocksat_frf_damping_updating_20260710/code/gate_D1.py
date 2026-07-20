#!/usr/bin/env python3
"""Gate D1 — damping physics. On analytic 1-DOF and 2-mode systems the band-zeta/Rayleigh/structural-eta
forward models must reproduce the analytic FRF peak height (1/(2 zeta) viscous, 1/eta structural) to <=2%,
and Rayleigh zeta_i = alpha/(2 w_i)+beta w_i/2 must match. Failure => run VOID (card §7)."""
import json, os, sys
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import femdamp as D
from femdamp import frf_from_modes

WS = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TOL = 0.02


def fine_grid(fn, half=3.0, n=6001):
    return np.linspace(fn - half, fn + half, n)


def viscous_peak_test():
    errs = []
    for fn in (54.2, 120.0, 250.0):
        for zeta in (0.002, 0.005, 0.01, 0.03):
            fc = fine_grid(fn)
            H = D.analytic_sdof_accelerance(fn, zeta, fc)
            peak = np.abs(H).max()
            errs.append(abs(peak - 1.0 / (2 * zeta)) / (1.0 / (2 * zeta)))
    return float(np.max(errs))


def structural_peak_test():
    errs = []
    for fn in (54.2, 120.0, 250.0):
        for eta in (0.004, 0.01, 0.02, 0.06):
            fc = fine_grid(fn)
            H = D.analytic_sdof_structural(fn, eta, fc)
            peak = np.abs(H).max()
            errs.append(abs(peak - 1.0 / eta) / (1.0 / eta))
    return float(np.max(errs))


def rayleigh_test():
    """(a) closed-form zeta_i matches alpha/(2w)+bw/2; (b) 2-mode FRF peak heights ~ 1/(2 zeta_i)."""
    f = np.array([80.0, 200.0])
    w = 2 * np.pi * f
    alpha, beta = 0.5, 2e-6
    zi_formula = alpha / (2 * w) + beta * w / 2
    zi_func = D.rayleigh_zeta(f, alpha, beta)
    e_form = float(np.max(np.abs(zi_func - zi_formula) / zi_formula))
    # 2-mode FRF, well separated -> each peak height ~ 1/(2 zeta_i) (residue 1 each)
    peak_errs = []
    for i, fn in enumerate(f):
        fc = fine_grid(fn, half=4.0)
        H = frf_from_modes(np.array([[1.0, 1.0]]), w, zi_func, np.array([0.0, 0.0]), fc)[0]
        peak = np.abs(H).max()
        peak_errs.append(abs(peak - 1.0 / (2 * zi_func[i])) / (1.0 / (2 * zi_func[i])))
    return e_form, float(np.max(peak_errs))


def main():
    vp = viscous_peak_test()
    sp = structural_peak_test()
    rz, rp = rayleigh_test()
    passed = (vp <= TOL and sp <= TOL and rz <= TOL and rp <= TOL)
    out = {"pass": bool(passed),
           "viscous_peak_err": round(vp, 5),
           "structural_peak_err": round(sp, 5),
           "rayleigh_zeta_err": round(rz, 6),
           "rayleigh_peak_err": round(rp, 5),
           "tol": TOL,
           "note": "1/(2zeta) viscous, 1/eta structural, Rayleigh zeta_i=a/(2w)+bw/2 all reproduced"}
    os.makedirs(os.path.join(WS, "out"), exist_ok=True)
    json.dump(out, open(os.path.join(WS, "out", "gate_D1.json"), "w"), indent=2)
    print(json.dumps(out, indent=2))
    return 0 if passed else 1


if __name__ == "__main__":
    sys.exit(main())
