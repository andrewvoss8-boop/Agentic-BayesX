"""
Profile-likelihood confirmation of the FIM identifiability story.

WHY (plain English): the FIM is a LOCAL, linearized measure -- it reads the curvature
of the misfit surface right at the nominal parameters. The profile likelihood is a
(semi-)global check: for each parameter, FIX it at a grid of values, RE-OPTIMIZE all
the other parameters to best fit the data, and trace the resulting best misfit. A sharp
valley = the data pins that parameter (identifiable); a flat valley = the data is blind
to it (unidentifiable). If profile and FIM agree, the conclusion is robust.

Data: synthetic noiseless modal frequencies at true theta = 1 (structural-identifiability
view) plus one noisy realization. Misfit = chi-square = sum_i ((f_i(theta)-y_i)/sigma_i)^2,
same 'freq_only' 8-mode feature set the FIM uses. The inner re-optimization uses
least_squares with the EXACT analytic frequency Jacobian (fast, robust). NOT a sampler.
"""
import os
import sys
import json
import time
import numpy as np
import scipy.linalg as sla
from scipy.optimize import least_squares

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import fim_model as fm
import run_fim as rf

OUT = os.path.abspath(os.path.join(HERE, ".."))


def main():
    t0 = time.time()
    groups, Kfix, M, meta = fm.build_groups(30.0)
    free = fm.prune_dead(fm.K_of_theta(groups, Kfix, np.ones(fm.NP)), M)
    nm = rf.N_MODES
    Mf = M[np.ix_(free, free)]
    Kfix_f = Kfix[np.ix_(free, free)]
    Kg = fm.group_blocks(groups, free)        # list of free-restricted K_g
    NB = 40                                    # nominal-mode reduction basis size

    # Build a NOMINAL modal reduction basis T (free x NB), mass-normalized so T^T M T = I.
    # All theta-solves then happen in the tiny NB x NB reduced space (microseconds), and
    # the lowest nm reduced modes reproduce the full modes to the reported tolerance.
    f0, w20, T = fm.solve_modes(groups, Kfix, M, free, np.ones(fm.NP), NB)
    Krfix = T.T @ (Kfix_f @ T)
    Krg = [T.T @ (Kg[g] @ T) for g in range(fm.NP)]      # reduced group matrices

    def solve_reduced(theta):
        Kr = Krfix + sum(theta[g] * Krg[g] for g in range(fm.NP))
        w2, Q = np.linalg.eigh(Kr)             # Mr = I -> standard symmetric eig
        idx = np.argsort(w2)[:nm]
        w2 = np.clip(w2[idx], 1e-30, None); Q = Q[:, idx]
        f = np.sqrt(w2) / (2 * np.pi)
        return f, w2, Q                         # Q^T Q = I (mass-normalized in full space)

    def jac_reduced(theta, cols):
        f, w2, Q = solve_reduced(theta)
        dF = np.zeros((nm, len(cols)))
        for jc, g in enumerate(cols):
            KgQ = Krg[g] @ Q
            for i in range(nm):
                dF[i, jc] = (Q[:, i] @ KgQ[:, i]) / (4 * np.pi * np.sqrt(w2[i]))
        return dF, f

    def solve(theta):                           # frequencies only, via reduced basis
        f, w2, Q = solve_reduced(theta)
        return f, w2, Q

    # reduction-error check vs the full eigensolve (nominal and a +20% stiffened case)
    def full_freqs(theta):
        Kf = Kfix_f + sum(theta[g] * Kg[g] for g in range(fm.NP))
        mu, _ = sla.eigh(Mf, Kf)
        w2 = 1.0 / mu[np.argsort(mu)[::-1][:nm]]
        return np.sqrt(np.sort(w2)) / (2 * np.pi)
    red_err_nom = float(np.max(np.abs(solve(np.ones(fm.NP))[0] - full_freqs(np.ones(fm.NP)))))
    red_err_pert = float(np.max(np.abs(solve(1.2*np.ones(fm.NP))[0] - full_freqs(1.2*np.ones(fm.NP)))))

    f_true, _, _ = solve(np.ones(fm.NP))
    sigma = rf.freq_noise(f_true)
    rng = np.random.default_rng(7)
    y_clean = f_true.copy()
    y_noisy = f_true + sigma * rng.standard_normal(len(f_true))

    grid = np.linspace(0.7, 1.3, 19)          # +/-30%, comparable to the prior width
    profiles = {}
    for p in range(fm.NP):
        others = [k for k in range(fm.NP) if k != p]
        curves = {"clean": [], "noisy": []}
        for tag, y in (("clean", y_clean), ("noisy", y_noisy)):
            # optimize the OTHER params in LOG space (z = log theta) so stiffness
            # scales stay positive and K(theta) stays positive-definite.
            z0 = np.zeros(len(others))
            for v in grid:
                def resid(z, _v=v, _y=y):
                    th = np.ones(fm.NP); th[p] = _v
                    th[others] = np.exp(z)
                    f, _, _ = solve(th)
                    return (f - _y) / sigma

                def jac(z, _v=v):
                    th = np.ones(fm.NP); th[p] = _v
                    th[others] = np.exp(z)
                    dF, _ = jac_reduced(th, others)                  # df/dtheta_others
                    return dF * np.exp(z)[None, :] / sigma[:, None]  # df/dz

                res = least_squares(resid, z0, jac=jac, method="trf",
                                    bounds=(np.log(0.2), np.log(5.0)), max_nfev=200)
                curves[tag].append(float(np.sum(res.fun ** 2)))
                z0 = res.x                       # warm-start next grid point
        c = np.array(curves["clean"])
        mask = np.abs(grid - 1.0) <= 0.08
        if np.sum(mask) >= 3 and np.ptp(c[mask]) > 1e-9:
            a = np.polyfit(grid[mask] - 1.0, c[mask], 2)[0]
            sd_prof = float(1.0 / np.sqrt(a)) if a > 0 else None
        else:
            sd_prof = None
        profiles[fm.PARAM_NAMES[p]] = dict(
            grid=[round(float(x), 4) for x in grid],
            chi2_clean=[round(float(x), 4) for x in curves["clean"]],
            chi2_noisy=[round(float(x), 4) for x in curves["noisy"]],
            profile_implied_sd=(round(sd_prof, 5) if sd_prof is not None else None),
            flat_unidentifiable=bool(np.ptp(c) < 1.0))   # delta-chi2 < 1 across +/-30%
    out = dict(grid_range=[0.7, 1.3], n_modes=nm,
               reduction_basis_modes=NB,
               reduction_max_abs_freq_err_hz=dict(nominal=round(red_err_nom, 6),
                                                  stiffened_1p2=round(red_err_pert, 6)),
               note="chi2 profiles vs each theta_p, others re-optimized in log-space "
                    "(analytic-Jacobian least_squares, 40-mode reduced basis); compare "
                    "profile_implied_sd to FIM marginal_posterior_sd",
               profiles=profiles, runtime_s=round(time.time() - t0, 3))
    with open(os.path.join(OUT, "profile_likelihood.json"), "w") as fo:
        json.dump(out, fo, indent=2)
    for nmn in fm.PARAM_NAMES:
        pr = profiles[nmn]
        print(f"{nmn:14s} profile_sd={pr['profile_implied_sd']} "
              f"flat_unidentifiable={pr['flat_unidentifiable']}")
    print("runtime_s:", out["runtime_s"])


if __name__ == "__main__":
    main()
