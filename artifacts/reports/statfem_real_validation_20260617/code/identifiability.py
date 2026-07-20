#!/usr/bin/env python3
"""Modal/Eigenproblem Identifiability Gate for Card A (AGENTS.md), on the plain 9-group ShockSat.

Three required pieces, BEFORE any per-parameter identifiable/not claim:
  1. STRAIN ENERGY  f_{i,g} = (q_i^T A_g q_i)/lambda_i  (reduced mass-normalized modes q_i, lambda_i),
     normalized over the 9 groups -> which calibration modes drive which groups; per-group typical & peak.
  2. FIM eigen-view at the REALIZED discrepancy floor: FIM = J^T Sigma^-1 J, J = d vec(log|H_obs|)/d theta at
     nominal, Sigma = sigma_meas^2 I + sigma_d0^2 C (Schneider freq x space) -> how many parameter COMBINATIONS
     clear the prior precision (1/0.25^2), and which raw groups each strong/weak combo mixes.
  3. FINITE PERTURBATION: +20% per group -> max relative eigenvalue shift (confirms in-load-path vs not).

Output: out/identifiability.json. Uses the same observed channels as a representative split (split 0).
"""
from __future__ import annotations
import json, sys
from pathlib import Path
import numpy as np
import jax, jax.numpy as jnp
jax.config.update("jax_enable_x64", True)

sys.path.insert(0, str(Path(__file__).resolve().parent))
import core
import realfrf as rf
import real_arms as ra
from run_cell import select_split

WS = Path(__file__).resolve().parent.parent
OUT = WS / "out"
PRIOR_PREC = 1.0 / (core.NSIG_THETA ** 2)        # LogNormal(0,0.25) prior precision on log_theta


def strain_energy(R):
    K = R.A_fix + R.A.sum(0)                      # theta = 1
    lam, Q = np.linalg.eigh(K)
    lam = np.clip(lam, 1e-9, None)
    # SE_{i,g} = q_i^T A_g q_i ; fraction over the 9 groups
    SE = np.array([[Q[:, i] @ R.A[g] @ Q[:, i] for g in range(9)] for i in range(len(lam))])  # (Nmode,9)
    frac = SE / np.clip(SE.sum(1, keepdims=True), 1e-30, None)
    # restrict to calibration band modes (<= 260 Hz)
    f_hz = np.sqrt(lam) / (2 * np.pi)
    band = f_hz <= rf.BAND[1] + 20
    fb = frac[band]
    return {g: {"typical_frac": float(np.median(fb[:, i])), "peak_frac": float(fb[:, i].max()),
                "n_modes_dominant": int((fb[:, i] > 0.3).sum())}
            for i, g in enumerate(rf.GNAMES)}, f_hz[band].tolist()


def fim_eigen(R, freqs, resp_rows, drive_row, coords_obs, sigma_meas, sigma_d0, zeta):
    jfwd = rf.jax_fem_logmag_factory(R, freqs, resp_rows, drive_row, zeta=zeta)
    J = np.asarray(jax.jacfwd(jfwd)(jnp.ones(9)))                # (Nf, Ns, 9)
    nf, ns, ng = J.shape
    Jm = J.reshape(nf * ns, ng)
    C = np.kron(ra.corr_freq(freqs, core.DISC_LEN_LOGF), ra.corr_space(coords_obs, core.DISC_LEN_Z))
    Sigma = sigma_meas ** 2 * np.eye(C.shape[0]) + sigma_d0 ** 2 * C
    # FIM = J^T Sigma^-1 J  (solve, do not invert the big matrix explicitly more than needed)
    Si_J = np.linalg.solve(Sigma, Jm)
    FIM = Jm.T @ Si_J                                            # (9,9)
    ev, evec = np.linalg.eigh(FIM)
    ev = ev[::-1]; evec = evec[:, ::-1]
    n_above = int((ev > PRIOR_PREC).sum())
    combos = []
    for k in range(ng):
        mix = {rf.GNAMES[i]: round(float(evec[i, k]), 3) for i in np.argsort(-np.abs(evec[:, k]))[:3]}
        combos.append({"eigval": float(ev[k]), "above_prior": bool(ev[k] > PRIOR_PREC), "top_groups": mix})
    return {"eigvals": ev.tolist(), "prior_precision": float(PRIOR_PREC),
            "n_combos_above_prior": n_above, "combos": combos}


def finite_perturb(R, pct=0.20):
    K0 = R.A_fix + R.A.sum(0)
    lam0 = np.clip(np.linalg.eigvalsh(K0), 1e-9, None)
    out = {}
    for g in range(9):
        th = np.ones(9); th[g] = 1 + pct
        K = R.A_fix + np.einsum("g,gij->ij", th, R.A)
        lam = np.clip(np.linalg.eigvalsh(K), 1e-9, None)
        rel = np.abs(np.sqrt(lam) / np.sqrt(lam0) - 1)
        out[rf.GNAMES[g]] = {"max_rel_freq_shift_pct": float(100 * rel.max()),
                             "median_rel_freq_shift_pct": float(100 * np.median(rel)),
                             "in_load_path": bool(rel.max() > 1e-4)}
    return out


def main():
    R = rf.load_reduced()
    meas = rf.reprocess_measured(list(range(1, rf.N_ACCEL_RECORDERS + 1)))
    ch = rf.build_channels(R, meas["daq"])
    obs, held, didx = select_split(ch, meas, 8, 0)
    fr = meas["freqs"]; bm = (fr >= rf.BAND[0]) & (fr <= rf.BAND[1]); freqs = fr[bm]
    resp_rows = ch.rows[obs]; coords = ch.coords[obs]

    se, modes = strain_energy(R)
    ident = sorted(rf.GNAMES, key=lambda g: -se[g]["peak_frac"])
    n_ident = sum(1 for g in rf.GNAMES if se[g]["peak_frac"] > 0.3)
    # realized discrepancy floor: representative sigma_d0 ~ residual std of nominal FEM vs measured (observed)
    fem1 = rf.fem_logmag(R, freqs, np.ones(9), resp_rows, ch.drive_row, zeta=rf.ZETA_NOM)
    Hobs = np.array([np.abs(meas["H"][didx[ch.daq[k]]][bm]) for k in obs]).T
    resid = np.log(np.maximum(Hobs, 1e-30)) - fem1
    sigma_d0 = float(np.std(resid - np.median(resid)))
    fim = fim_eigen(R, freqs, resp_rows, ch.drive_row, coords, ra.SIGMA_MEAS, sigma_d0, rf.ZETA_NOM)
    fp = finite_perturb(R)
    res = {"strain_energy": se, "n_identifiable_groups": n_ident,
           "identifiability_order_by_peak_SE": ident, "n_calibration_modes": len(modes),
           "realized_discrepancy_floor_sigma_d0": sigma_d0,
           "fim": fim, "finite_perturbation": fp,
           "note": ("Strain energy certifies signal-above-floor per GROUP; FIM eigen-view certifies how many "
                    "parameter COMBINATIONS separate. No real-data ground-truth theta, so this is the pre-test "
                    "identifiability lever, not a recovery claim.")}
    OUT.mkdir(exist_ok=True)
    (OUT / "identifiability.json").write_text(json.dumps(res, indent=2))
    print(f"strain energy: {n_ident} groups peak-SE>0.3; order {ident}")
    print(f"FIM @ realized floor (sigma_d0={sigma_d0:.3f}): {fim['n_combos_above_prior']}/9 combos above prior; "
          f"eigvals {[round(x,1) for x in fim['eigvals'][:5]]}...")
    moved = [g for g, v in fp.items() if v['max_rel_freq_shift_pct'] > 0.5]
    print(f"finite +20%: groups moving modes >0.5%: {moved}")
    print("wrote out/identifiability.json")


if __name__ == "__main__":
    main()
