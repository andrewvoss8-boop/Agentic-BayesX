#!/usr/bin/env python3
"""Identifiability gate (AGENTS.md Modal/Eigenproblem Identifiability Gate) for the FRF observable.

Three pieces, run BEFORE any 'theta_g recovered / not' claim:
 1. modal strain-energy fraction per group, f_{i,g} = phi_i^T K_g phi_i / lambda_i. In the reduced basis at
    theta=1, K_red(1)=Lambda (diagonal), so phi_i=e_i and f_{i,g}=A_g[i,i]/lambda_i (the diagonal of the
    reduced block / nominal eigenvalue). Reported mean & peak over the in-band modes.
 2. FRF-FISHER-INFORMATION eigen-view: J = d vec(log|H_obs|)/d theta at nominal; FIM = J^T Sigma^-1 J in
    log-theta space. Evaluated at BOTH the measurement-noise floor (Sigma=sigma_meas^2 I) AND the REALIZED
    discrepancy floor (Sigma=sigma_meas^2 I + sigma_d^2 C_schneider). Count parameter COMBINATIONS whose FIM
    eigenvalue clears the prior precision (1/0.25^2 = 16); report which groups each combination mixes.
 3. finite-perturbation check: +/-20% per group -> band-QOI shift at a held-out sensor, to distinguish
    in-path-but-below-floor from out-of-path (~zero shift).

Output: out/identifiability.json.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
WS = HERE.parent
sys.path.insert(0, str(HERE))

import core            # noqa: E402
import nuts_arms as na  # noqa: E402

PRIOR_SIGMA = core.NSIG_THETA       # log-theta prior sd
PRIOR_PREC = 1.0 / PRIOR_SIGMA ** 2  # = 16
SIGMA_D_REALIZED = 0.08              # representative realized discrepancy floor (Schneider mid-band, A7)


def strain_energy(model):
    """Per-group SE fraction over the in-band modes. Returns rows + the in-band mode frequencies."""
    lam = np.linalg.eigvalsh(model.A_fix + model.A.sum(0))   # = nominal eigenvalues (K_red(1)=Lambda)
    fk = np.sqrt(np.clip(lam, 0, None)) / (2 * np.pi)
    inband = (fk >= core.BAND[0]) & (fk <= core.BAND[1])
    rows = []
    for gi, g in enumerate(core.GNAMES):
        diag = np.diag(model.A[gi])                # A_g[i,i] (= 2*SE in mode i)
        frac = diag / lam                          # SE fraction per mode
        fr_ib = frac[inband]
        peak_i = int(np.argmax(np.where(inband, frac, -1)))
        rows.append({"group": g,
                     "mean_se_pct": float(100 * np.mean(fr_ib)),
                     "peak_se_pct": float(100 * np.max(fr_ib)),
                     "peak_mode_hz": float(fk[peak_i]),
                     "identified_by_se": bool(np.mean(fr_ib) > 0.05)})  # >5% mean = clears typ. floor
    return rows, fk[inband].tolist()


def fim_view(model, freqs, observed, drive, sigma_d):
    """FIM eigen-decomposition in log-theta space at a given discrepancy floor."""
    J = na.theta_jacobian(model, freqs, observed, drive)     # (N, 9), N = Nf*Ns_obs, d log|H| / d theta
    # at theta=1, d/d log_theta = d/d theta, so J is already the log-theta sensitivity
    coords_obs = model.dof_xyz[np.asarray(observed)]
    N = J.shape[0]
    if sigma_d > 0:
        Cf = na.corr_freq(freqs, core.DISC_LEN_LOGF)
        Cz = na.corr_space(coords_obs, core.DISC_LEN_Z)
        C = np.kron(Cf, Cz)
        Sig = core.SIGMA_MEAS ** 2 * np.eye(N) + sigma_d ** 2 * C
    else:
        Sig = core.SIGMA_MEAS ** 2 * np.eye(N)
    # FIM = J^T Sigma^-1 J  (9x9)
    SinvJ = np.linalg.solve(Sig, J)
    FIM = J.T @ SinvJ
    FIM = 0.5 * (FIM + FIM.T)
    evals, evecs = np.linalg.eigh(FIM)
    order = np.argsort(evals)[::-1]
    evals = evals[order]; evecs = evecs[:, order]
    n_above = int(np.sum(evals > PRIOR_PREC))
    combos = []
    for k in range(len(evals)):
        v = evecs[:, k]
        top = np.argsort(np.abs(v))[::-1][:3]
        combos.append({"eigval": float(evals[k]), "above_prior": bool(evals[k] > PRIOR_PREC),
                       "mixes": [{"group": core.GNAMES[i], "weight": float(v[i])} for i in top]})
    return {"n_above_prior": n_above, "prior_precision": PRIOR_PREC, "sigma_d": sigma_d,
            "eig_combinations": combos}


def finite_perturbation(model, freqs, heldout, drive, delta=0.20):
    """+/-delta per group -> band-QOI rel shift at held-out sensors (in-path vs out-of-path)."""
    base = core.frf_np(model, freqs, np.ones(9), heldout, drive)
    base_band = np.array([core.qoi_band(np.abs(base[:, c]), freqs) for c in range(len(heldout))])
    rows = []
    for gi, g in enumerate(core.GNAMES):
        th = np.ones(9); th[gi] = 1.0 + delta
        H = core.frf_np(model, freqs, th, heldout, drive)
        band = np.array([core.qoi_band(np.abs(H[:, c]), freqs) for c in range(len(heldout))])
        rel = np.abs(band / base_band - 1.0)
        rows.append({"group": g, "mean_band_qoi_rel_shift": float(np.mean(rel)),
                     "max_band_qoi_rel_shift": float(np.max(rel))})
    return rows


def main():
    model = core.load_model()
    ch = core.select_channels(model)
    freqs = core.freq_grid()
    se, inband_hz = strain_energy(model)
    fim_noise = fim_view(model, freqs, ch["observed"], ch["drive"], sigma_d=0.0)
    fim_real = fim_view(model, freqs, ch["observed"], ch["drive"], sigma_d=SIGMA_D_REALIZED)
    fp = finite_perturbation(model, freqs, ch["heldout"], ch["drive"])
    informed = [r["group"] for r in se if r["identified_by_se"]]
    # FIM-identifiable groups: groups dominating an above-prior eigen-combination at the realized floor
    fim_groups = sorted({m["group"] for c in fim_real["eig_combinations"] if c["above_prior"]
                         for m in c["mixes"] if abs(m["weight"]) > 0.4})
    out = {"strain_energy": se, "inband_modes_hz": inband_hz,
           "fim": fim_real, "fim_noise_floor": fim_noise,
           "finite_perturbation": fp,
           "informed_groups_strain_energy": informed,
           "informed_groups_fim": fim_groups,
           "fim_caveat": "The FRF-FIM is a LINEARIZATION at nominal theta. The whole log|H| likelihood is "
                         "hyper-sensitive near resonances (d log|H|/d theta blows up at resonance edges), so the "
                         "FIM over 960 freq x sensor points is INFLATED and reports many theta combinations above "
                         "prior precision -- optimistic. The robust aggregate signal measure is the strain-energy "
                         "table (only 4/9 groups store >5% mean modal SE); the OPERATIVE identifiability test is "
                         "the nonlinear posterior RECOVERY in the sweep cells (covered/informed flags), which "
                         "accounts for theta<->discrepancy confounding the linear FIM misses.",
           "note": "identifiability tied to the realized discrepancy floor (sigma_d~0.08); a group with ample "
                   "strain energy can still fail to separate if its FRF signal sits below that floor. The "
                   "Schneider discrepancy is SMOOTH, so it does not mask the SHARP resonance-shift theta signal "
                   "-- which is why identifiable groups can still be recovered with the discrepancy present."}
    json.dump(out, open(WS / "out" / "identifiability.json", "w"), indent=1)
    print("strain energy (mean%/peak%):")
    for r in se:
        print(f"  {r['group']:15s} mean {r['mean_se_pct']:5.1f}  peak {r['peak_se_pct']:5.1f} "
              f"@ {r['peak_mode_hz']:.0f}Hz  id={r['identified_by_se']}")
    print(f"FIM combos above prior (precision {PRIOR_PREC:.0f}): "
          f"noise-floor {fim_noise['n_above_prior']}, realized-floor {fim_real['n_above_prior']}")
    print("informed (SE):", informed)
    print("informed (FIM, realized floor):", fim_groups)


if __name__ == "__main__":
    main()
