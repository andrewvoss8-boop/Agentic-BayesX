"""
Pre-test Fisher-Information (FIM) identifiability + experiment-design analysis on
the Opus Phase-1 hexapod tray FEM.

GOAL (plain English): before running any hardware test, answer "how many of our
candidate physical parameters can this scrappy modal test actually pin down, and
which combinations are hopeless?" -- with a NUMBER and a plot, not a guess. We also
ask the experiment-design question: WHERE should we put the accelerometer(s) and
WHERE should we tap to learn the most.

Key objects (defined on first use):
  - theta : vector of dimensionless stiffness multipliers (nominal 1.0). See PARAM_NAMES.
  - J     : sensitivity Jacobian, d(observable feature)/d(theta_g). Rows = features
            (modal frequencies and, for sensor designs, mode-shape components),
            columns = parameters.
  - Sigma : measurement-noise covariance of the features (diagonal here). Encodes how
            noisy each observable is on a real test.
  - FIM   : Fisher Information Matrix = J^T Sigma^{-1} J  (parameters x parameters).
            Large eigenvalue of FIM = a parameter-combination the data pins down hard
            ("stiff" direction); tiny eigenvalue = a combination the data barely sees
            ("sloppy" direction). This is the sloppy-models view of identifiability.
  - QOI   : a load/prediction quantity of interest (payload transmissibility peak).
            The dangerous case = the QOI depends on directions the data CANNOT constrain.

This script writes fim_results.json + arrays_*.npz for the figure script.
NOTE: this is a LOCAL (Fisher / linearized) identifiability analysis; profile_likelihood.py
provides a (semi-)global confirmation. It is NOT a posterior sampler run -- no NUTS claim.
"""
import os
import sys
import json
import time
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import fim_model as fm

OUT = os.path.abspath(os.path.join(HERE, ".."))

# ---------------------------------------------------------------------------
# Assumptions (mirrored in assumptions_ledger.md). All values + units + rationale there.
N_MODES = 8                 # elastic modes kept as candidate observables (fixed-base, no RBMs)
FREQ_REL_NOISE = 0.01       # frequency modal-ID noise sd, 1% of each f_i (relative)
FREQ_ABS_FLOOR_HZ = 0.5     # absolute frequency noise floor (Hz)
LOGRES_NOISE = 0.15         # 1-sensor: sd of log residue (mode-shape amplitude^2), ~15%
RATIO_REL_NOISE = 0.10      # 2-sensor: relative sd of mode-shape ratio (transmissibility), 10%
PRIOR_SD = 0.30             # prior sd on each (relative) theta -> precision 1/0.3^2 = 11.1
IDENT_PRIOR = 1.0 / PRIOR_SD**2      # eig threshold: posterior sd < prior sd
IDENT_WELL = 1.0 / 0.10**2           # eig threshold: posterior sd < 0.10 ("well-identified")
QR_COND_THRESH = 100.0      # subset-selection: keep columns while condition number < this
ZETA = 0.02                 # assumed modal damping ratio for the QOI (2% critical)


def freq_noise(f):
    return np.sqrt((FREQ_REL_NOISE * f) ** 2 + FREQ_ABS_FLOOR_HZ ** 2)


# ---------------------------------------------------------------------------
def build_designs(meta, free, w2, Phi, dF, dPhi):
    """Construct (J, sigma) feature stacks for three observation designs.
    Returns dict name -> (J [nfeat x nparam], sigma [nfeat], feature_labels)."""
    f = np.sqrt(w2) / (2 * np.pi)
    designs = {}

    # ---- Design A: frequencies only (modal-ID of natural frequencies) ----
    sig_f = freq_noise(f)
    designs["freq_only"] = (dF.copy(), sig_f.copy(),
                            [f"f{i+1}" for i in range(len(f))])

    # Pick a default drive-point sensor: tray CORNER, vertical (z). Corners move in
    # most plate-bending and suspension modes, so a corner z-accel is a sane default.
    s_corner = fm.dof_index(meta, free, fm.tray_node(meta, 0, 0), 2)          # node (0,0), uz
    s_center = fm.dof_index(meta, free, fm.tray_node(meta, meta["NX"]//2, meta["NY"]//2), 2)

    # ---- Design B: 1 sensor (drive-point auto-spectrum) = freq + log-residue ----
    # drive-point residue r_i = phi_i(s)^2 (mass-normalized). Feature = log r_i.
    # d log r_i / d theta = 2 * dphi_i(s)/phi_i(s).
    phi_s = Phi[s_corner, :]
    dlogr = np.zeros((len(f), fm.NP))
    for g in range(fm.NP):
        dlogr[:, g] = 2.0 * dPhi[s_corner, :, g] / np.where(np.abs(phi_s) > 1e-9, phi_s, np.nan)
    dlogr = np.nan_to_num(dlogr, nan=0.0)
    Jb = np.vstack([dF, dlogr])
    sig_b = np.concatenate([sig_f, np.full(len(f), LOGRES_NOISE)])
    designs["one_sensor_corner_z"] = (Jb, sig_b,
                                      [f"f{i+1}" for i in range(len(f))] +
                                      [f"logRes{i+1}" for i in range(len(f))])

    # ---- Design C: 2 sensors (transmissibility) = freq + mode-shape ratio ----
    # ratio_i = phi_i(s2)/phi_i(s1); input cancels. Feature = ratio (relative noise).
    s1, s2 = s_center, s_corner
    p1 = Phi[s1, :]; p2 = Phi[s2, :]
    ratio = p2 / np.where(np.abs(p1) > 1e-9, p1, np.nan)
    dratio = np.zeros((len(f), fm.NP))
    for g in range(fm.NP):
        dratio[:, g] = (dPhi[s2, :, g] * p1 - p2 * dPhi[s1, :, g]) / \
                       np.where(np.abs(p1) > 1e-9, p1**2, np.nan)
    dratio = np.nan_to_num(dratio, nan=0.0)
    ratio = np.nan_to_num(ratio, nan=0.0)
    Jc = np.vstack([dF, dratio])
    sig_c = np.concatenate([sig_f, np.maximum(RATIO_REL_NOISE * np.abs(ratio), 1e-3)])
    designs["two_sensor_transmissibility"] = (Jc, sig_c,
                                              [f"f{i+1}" for i in range(len(f))] +
                                              [f"ratio{i+1}" for i in range(len(f))])
    return designs, dict(s_corner=s_corner, s_center=s_center)


def fim_of(J, sigma):
    """FIM = J^T Sigma^{-1} J with diagonal Sigma (sigma = std devs)."""
    W = 1.0 / sigma**2
    return (J * W[:, None]).T @ J


def analyze_fim(FIM):
    """Eigen-decompose FIM. Return eigenvalues (desc), eigenvectors, identifiability counts."""
    evals, evecs = np.linalg.eigh(FIM)
    order = np.argsort(evals)[::-1]
    evals = evals[order]; evecs = evecs[:, order]
    evals_pos = np.clip(evals, 0, None)
    post_sd = 1.0 / np.sqrt(evals_pos + 1e-30)     # FIM-only posterior sd along eigendir
    n_ident = int(np.sum(evals_pos > IDENT_PRIOR))
    n_well = int(np.sum(evals_pos > IDENT_WELL))
    cond = float(evals_pos[0] / max(evals_pos[-1], 1e-30))
    # Honest PER-PARAMETER marginal: regularize the FIM with the prior precision
    # (posterior precision = FIM + prior_prec * I), invert, take sqrt of the diagonal.
    # marginal_sd[k] = posterior sd on theta_k accounting for prior AND correlations.
    # reduction[k] = prior_sd / marginal_sd  (1.0 = data learned nothing about theta_k;
    # large = data sharply constrains it). This avoids overstating a QR-selected column.
    prior_prec = 1.0 / PRIOR_SD**2
    Cov = np.linalg.inv(FIM + prior_prec * np.eye(FIM.shape[0]))
    marg_sd = np.sqrt(np.clip(np.diag(Cov), 0, None))
    reduction = PRIOR_SD / np.where(marg_sd > 0, marg_sd, np.nan)
    n_param_learned = int(np.sum(reduction > 1.5))   # >1.5x tighter than prior
    return dict(evals=evals, evecs=evecs, post_sd=post_sd,
                n_identifiable=n_ident, n_well_identified=n_well, condition_number=cond,
                marginal_sd=marg_sd, prior_to_post_reduction=reduction,
                n_param_learned=n_param_learned)


def qr_subset(J, sigma):
    """Rank-revealing QR (column-pivoted) subset selection on the noise-whitened,
    prior-scaled Jacobian. Returns the ordered list of parameter indices the data
    can resolve while the running condition number stays below QR_COND_THRESH."""
    Jw = J / sigma[:, None]                 # noise-whiten rows
    Jw = Jw * PRIOR_SD                       # prior-scale columns (relative significance)
    # column-pivoted QR
    Q, R, piv = _qr_pivot(Jw)
    diag = np.abs(np.diag(R))
    kept = []
    for k in range(len(diag)):
        cond_k = diag[0] / max(diag[k], 1e-30)
        if cond_k <= QR_COND_THRESH and diag[k] > 1e-12 * diag[0]:
            kept.append(int(piv[k]))
        else:
            break
    return kept, piv.tolist(), diag.tolist()


def _qr_pivot(A):
    import scipy.linalg as sla
    Q, R, P = sla.qr(A, mode='economic', pivoting=True)
    return Q, R, P


# ---------------------------------------------------------------------------
def qoi_value(groups, Kfix, M, free, theta, meta, sensors):
    """Load QOI = peak payload transmissibility (dimensionless acceleration
    amplification) from a unit BASE vertical input to the tray-corner vertical
    response, by modal superposition with damping ZETA, scanned over frequency near
    the kept modes. See quantity_contracts.md for the full contract.
    T(w) = | sum_i phi_i(out) * Gamma_i / (w2_i - w^2 + 2 i zeta w_i w) | * w^2
    where Gamma_i = modal participation to a uniform base z-accel = phi_i^T M r_z,
    r_z = unit rigid vertical translation of the tray nodes. Returns scalar peak."""
    f, w2, Phi = fm.solve_modes(groups, Kfix, M, free, theta, N_MODES)
    wi = np.sqrt(w2)
    Mf = M[np.ix_(free, free)]
    # influence vector r_z: unit z-translation on every tray node (uz dof = comp 2)
    rz = np.zeros(len(free))
    for j in range(meta["NY"]):
        for i in range(meta["NX"]):
            d = fm.dof_index(meta, free, fm.tray_node(meta, i, j), 2)
            if d is not None:
                rz[d] = 1.0
    Gamma = Phi.T @ (Mf @ rz)                # modal participation factors
    out = sensors["s_corner"]
    phi_out = Phi[out, :]
    # frequency scan around the modes
    wscan = np.linspace(0.5*wi[0], 1.2*wi[min(3, len(wi)-1)], 4000)
    H = np.zeros_like(wscan, dtype=complex)
    for i in range(len(wi)):
        denom = (w2[i] - wscan**2) + 2j*ZETA*wi[i]*wscan
        H += phi_out[i] * Gamma[i] / denom
    T = np.abs(H) * wscan**2                  # acceleration transmissibility
    return float(np.max(T))


def qoi_gradient(groups, Kfix, M, free, meta, sensors, h=1e-3):
    base = qoi_value(groups, Kfix, M, free, np.ones(fm.NP), meta, sensors)
    g = np.zeros(fm.NP)
    for k in range(fm.NP):
        tp = np.ones(fm.NP); tp[k] += h
        tm = np.ones(fm.NP); tm[k] -= h
        g[k] = (qoi_value(groups, Kfix, M, free, tp, meta, sensors) -
                qoi_value(groups, Kfix, M, free, tm, meta, sensors)) / (2*h)
    return base, g


# ---------------------------------------------------------------------------
def sensor_sweep(meta, free, w2, Phi, dF, dPhi):
    """Experiment design 'where to measure': for a 1-sensor drive-point design, try
    each tray node's vertical (z) DOF as the sensor and report the resulting FIM
    identifiable-direction count and D-optimality (log det FIM). Returns list."""
    f = np.sqrt(w2)/(2*np.pi)
    sig_f = freq_noise(f)
    results = []
    for j in range(meta["NY"]):
        for i in range(meta["NX"]):
            s = fm.dof_index(meta, free, fm.tray_node(meta, i, j), 2)
            if s is None:
                continue
            phi_s = Phi[s, :]
            dlogr = np.zeros((len(f), fm.NP))
            for g in range(fm.NP):
                dlogr[:, g] = 2.0*dPhi[s, :, g]/np.where(np.abs(phi_s) > 1e-9, phi_s, np.nan)
            dlogr = np.nan_to_num(dlogr, nan=0.0)
            J = np.vstack([dF, dlogr])
            sig = np.concatenate([sig_f, np.full(len(f), LOGRES_NOISE)])
            FIM = fim_of(J, sig)
            a = analyze_fim(FIM)
            sign, logdet = np.linalg.slogdet(FIM + 1e-12*np.eye(fm.NP))
            results.append(dict(i=i, j=j,
                                x=float(meta["coords"][fm.tray_node(meta, i, j)][0]),
                                y=float(meta["coords"][fm.tray_node(meta, i, j)][1]),
                                n_identifiable=a["n_identifiable"],
                                logdet=float(logdet)))
    return results


def excitation_sweep(meta, free, w2, Phi):
    """Experiment design 'where to hit': modal observability of each kept mode is
    proportional to |phi_i(drive)|. For each candidate drive node (tray z), report
    how many modes it excites above a fraction of the best, i.e. which taps light up
    the most modes (a tap on a node line of a mode cannot excite that mode)."""
    f = np.sqrt(w2)/(2*np.pi)
    results = []
    # normalize each mode's shape by its max |z| over tray nodes
    tray_dofs = []
    for j in range(meta["NY"]):
        for i in range(meta["NX"]):
            d = fm.dof_index(meta, free, fm.tray_node(meta, i, j), 2)
            tray_dofs.append((i, j, d))
    modemax = np.array([np.max([abs(Phi[d, m]) for (_, _, d) in tray_dofs if d is not None])
                        for m in range(len(f))])
    for (i, j, d) in tray_dofs:
        if d is None:
            continue
        obs = np.array([abs(Phi[d, m]) / modemax[m] for m in range(len(f))])
        nlit = int(np.sum(obs > 0.2))      # modes excited to >20% of their max
        results.append(dict(i=i, j=j,
                            x=float(meta["coords"][fm.tray_node(meta, i, j)][0]),
                            y=float(meta["coords"][fm.tray_node(meta, i, j)][1]),
                            n_modes_excited=nlit, mean_obs=float(obs.mean())))
    return results


# ---------------------------------------------------------------------------
def main():
    t0 = time.time()
    groups, Kfix, M, meta = fm.build_groups(30.0)
    free = fm.prune_dead(fm.K_of_theta(groups, Kfix, np.ones(fm.NP)), M)
    f, w2, Phi = fm.solve_modes(groups, Kfix, M, free, np.ones(fm.NP), N_MODES)
    Kg = fm.group_blocks(groups, free)
    dF = fm.freq_sensitivity(Kg, w2, Phi)
    dPhi = fm.shape_sensitivity(Kg, w2, Phi)

    # validation vs the Opus JAX build nominal modes
    jax_path = os.path.abspath(os.path.join(HERE, "..", "..", "..", "..",
                                            "runs", "fem_phase1", "opus", "jax", "results.json"))
    jax_modes = json.load(open(jax_path))["frequencies_hz"]
    val_err = float(np.max(np.abs(f[:6] - np.array(jax_modes[:6]))))

    designs, sensors = build_designs(meta, free, w2, Phi, dF, dPhi)

    out = {}
    out["param_names"] = fm.PARAM_NAMES
    out["nominal_freqs_hz"] = [round(float(x), 4) for x in f]
    out["validation_max_abs_freq_err_vs_jax_hz"] = round(val_err, 6)
    out["assumptions"] = dict(N_MODES=N_MODES, FREQ_REL_NOISE=FREQ_REL_NOISE,
                              FREQ_ABS_FLOOR_HZ=FREQ_ABS_FLOOR_HZ, LOGRES_NOISE=LOGRES_NOISE,
                              RATIO_REL_NOISE=RATIO_REL_NOISE, PRIOR_SD=PRIOR_SD,
                              IDENT_PRIOR_eig_threshold=IDENT_PRIOR,
                              IDENT_WELL_eig_threshold=IDENT_WELL,
                              QR_COND_THRESH=QR_COND_THRESH, ZETA=ZETA)
    out["freq_sensitivity_Hz_per_unit"] = {fm.PARAM_NAMES[g]:
                                           [round(float(dF[i, g]), 5) for i in range(len(f))]
                                           for g in range(fm.NP)}

    out["designs"] = {}
    arrays = {}
    for name, (J, sig, labels) in designs.items():
        FIM = fim_of(J, sig)
        a = analyze_fim(FIM)
        kept, piv, rdiag = qr_subset(J, sig)
        out["designs"][name] = dict(
            n_features=int(J.shape[0]),
            fim_eigenvalues=[float(x) for x in a["evals"]],
            fim_posterior_sd_per_direction=[round(float(x), 5) for x in a["post_sd"]],
            n_identifiable_directions=a["n_identifiable"],
            n_well_identified_directions=a["n_well_identified"],
            condition_number=a["condition_number"],
            marginal_posterior_sd={fm.PARAM_NAMES[k]: round(float(a["marginal_sd"][k]), 5)
                                   for k in range(fm.NP)},
            prior_to_post_sd_reduction={fm.PARAM_NAMES[k]: round(float(a["prior_to_post_reduction"][k]), 3)
                                        for k in range(fm.NP)},
            n_individual_params_learned=a["n_param_learned"],
            qr_subset_param_indices=kept,
            qr_subset_param_names=[fm.PARAM_NAMES[k] for k in kept],
            qr_pivot_order=[fm.PARAM_NAMES[k] for k in piv],
            stiff_direction=dict(
                eigenvalue=float(a["evals"][0]),
                loadings={fm.PARAM_NAMES[k]: round(float(a["evecs"][k, 0]), 4)
                          for k in range(fm.NP)}),
            sloppiest_direction=dict(
                eigenvalue=float(a["evals"][-1]),
                loadings={fm.PARAM_NAMES[k]: round(float(a["evecs"][k, -1]), 4)
                          for k in range(fm.NP)}),
        )
        arrays[f"FIM_{name}"] = FIM
        arrays[f"evals_{name}"] = a["evals"]
        arrays[f"evecs_{name}"] = a["evecs"]

    # ---- QOI vs data: which directions does the prediction need? ----
    qoi_base, qoi_grad = qoi_gradient(groups, Kfix, M, free, meta, sensors)
    out["qoi"] = dict(
        definition="peak payload acceleration transmissibility (base-z -> tray-corner-z), "
                   "modal superposition, zeta=%.3f; see quantity_contracts.md" % ZETA,
        nominal_value=round(float(qoi_base), 4),
        d_qoi_d_theta={fm.PARAM_NAMES[g]: round(float(qoi_grad[g]), 5) for g in range(fm.NP)},
    )
    # project the (normalized) QOI gradient onto each design's FIM eigenbasis
    g_unit = qoi_grad / (np.linalg.norm(qoi_grad) + 1e-30)
    for name in designs:
        evecs = arrays[f"evecs_{name}"]; evals = arrays[f"evals_{name}"]
        proj = evecs.T @ g_unit                     # components along each eigendir
        # fraction of QOI-sensitivity (squared) lying in SLOPPY (non-identifiable) dirs
        ident_mask = np.clip(evals, 0, None) > IDENT_PRIOR
        frac_sloppy = float(np.sum(proj[~ident_mask]**2) / (np.sum(proj**2) + 1e-30))
        out["designs"][name]["qoi_grad_proj_on_eigendirs"] = [round(float(x), 4) for x in proj]
        out["designs"][name]["qoi_fraction_in_sloppy_subspace"] = round(frac_sloppy, 4)

    # ---- sensitivity: how many params are learnable vs RESOLVED BAND and NOISE ----
    # (the headline "N identifiable" is conditional on these test-design choices)
    sens_band = []
    for nm in range(3, N_MODES + 1):
        f2, w22, Phi2 = fm.solve_modes(groups, Kfix, M, free, np.ones(fm.NP), nm)
        dF2 = fm.freq_sensitivity(Kg, w22, Phi2)
        sigf2 = freq_noise(f2)
        a2 = analyze_fim(fim_of(dF2, sigf2))
        sens_band.append(dict(n_modes=nm, max_freq_hz=round(float(f2[-1]), 1),
                              n_identifiable=a2["n_identifiable"],
                              n_param_learned=a2["n_param_learned"],
                              marginal_sd={fm.PARAM_NAMES[k]: round(float(a2["marginal_sd"][k]), 4)
                                           for k in range(fm.NP)}))
    sens_noise = []
    for mult in (0.5, 1.0, 2.0, 4.0):
        sigf = freq_noise(f) * mult
        a3 = analyze_fim(fim_of(dF, sigf))
        sens_noise.append(dict(freq_noise_mult=mult, n_identifiable=a3["n_identifiable"],
                               n_param_learned=a3["n_param_learned"]))
    out["sensitivity"] = dict(vs_resolved_band=sens_band, vs_freq_noise=sens_noise,
                              note="identifiable counts are conditional on resolved band and noise")

    # ---- experiment design sweeps ----
    out["experiment_design"] = dict(
        where_to_measure_1sensor=sensor_sweep(meta, free, w2, Phi, dF, dPhi),
        where_to_hit=excitation_sweep(meta, free, w2, Phi),
    )

    out["runtime_s"] = round(time.time() - t0, 3)
    with open(os.path.join(OUT, "fim_results.json"), "w") as fo:
        json.dump(out, fo, indent=2)
    np.savez(os.path.join(OUT, "arrays_fim.npz"),
             dF=dF, freqs=f, **arrays,
             qoi_grad=qoi_grad,
             coords=meta["coords"], NX=meta["NX"], NY=meta["NY"])

    print("validation max |df| vs JAX (Hz):", val_err)
    for name in designs:
        d = out["designs"][name]
        print(f"[{name}] identifiable dirs = {d['n_identifiable_directions']} "
              f"(well: {d['n_well_identified_directions']}), indiv params learned = "
              f"{d['n_individual_params_learned']}, QR basis = "
              f"{d['qr_subset_param_names']}, QOI frac in sloppy = "
              f"{d['qoi_fraction_in_sloppy_subspace']}")
        print(f"        marginal posterior sd: {d['marginal_posterior_sd']}")
    print("runtime_s:", out["runtime_s"])


if __name__ == "__main__":
    main()
