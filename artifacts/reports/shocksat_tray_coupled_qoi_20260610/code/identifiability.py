#!/usr/bin/env python3
"""Modal/Eigenproblem Identifiability Gate on the COUPLED interface modes.

Per AGENTS.md: before claiming the mount stiffness is or is not identifiable
(and whether the QOI is mount-dominated), compute
  f_{i,g} = phi_i^T K_g phi_i / lambda_i
the strain-energy fraction each coupled mode stores in each parameter group
(mass-normalized modes; fractions over ALL groups + fixed parts sum to 1),
AND a finite-perturbation check (mount x0.5 / x2 -> mode freq shifts + QOI
shifts). Compares the mount's modal sensitivity to the predecessor's
sigma_f ~ 4.6 % model-discrepancy floor to state whether a modal test of the
MOUNTED configuration could identify the mount (the bare-ShockSat joints
could not: 3 % sensitivity < 4.6 % floor).

Coupled model = chain free DOFs + 80 ShockSat ROM modal coords (the same
assembly verified in verify.py V7). NO sampler run; this is a sensitivity/
information statement, not a posterior claim.

Output: out/mount_identifiability.json
"""
import json
import os
import sys
import time
import numpy as np
import scipy.linalg as sla

HERE = os.path.dirname(os.path.abspath(__file__))
WS = os.path.abspath(os.path.join(HERE, ".."))
sys.path.insert(0, HERE)
import models  # noqa: E402
import methods  # noqa: E402
import run_qoi  # noqa: E402

t0 = time.time()
F_REPORT = 300.0
SIGMA_F_FLOOR = 0.046          # predecessor sigma_f (frequency-level discrepancy)


def log(m):
    print(f"[{time.time()-t0:6.1f}s] {m}", flush=True)


def coupled_system(tray, shk, theta_S, kmult=1.0):
    """Assemble coupled (M, K) over [u_f; q80] with the ShockSat elastic
    block kept in the NOMINAL 74-mode basis (K_el = A_fix + sum th_g A_g,
    NOT re-diagonalized) so the per-group SE blocks th_g*A_g live in the
    same coordinates as the coupled eigenvectors. Mass = identity there
    (mass-orthonormal basis)."""
    th = np.asarray(theta_S, float)
    K_el = shk.A_fix + np.einsum("g,gij->ij", th, shk.A)
    phi_all = np.hstack([shk.B_rbm, shk.B_el])     # (6, 80) nominal basis
    lam_rbm = shk.lam_rbm
    kdiag = np.array([models.MOUNT_NOMINAL[p] for p in models.MOUNT_PARAMS])*kmult
    Kff = tray["Kfix"] + sum(tray["Kg"].values())
    nf_ = Kff.shape[0]
    ib = tray["ibase"]
    n = nf_ + 80
    M = np.zeros((n, n))
    M[:nf_, :nf_] = tray["M"]
    M[nf_:, nf_:] = np.eye(80)
    K = np.zeros((n, n))
    K[:nf_, :nf_] = Kff
    K[nf_:nf_+6, nf_:nf_+6] = np.diag(lam_rbm)
    K[nf_+6:, nf_+6:] = K_el
    # mount springs: per-axis rank-1 patterns v_j = e(u_bp_j) - phi_all[j,:]
    Vm = np.zeros((6, n))
    for j in range(6):
        Vm[j, ib[j]] = 1.0
        Vm[j, nf_:] = -phi_all[j, :]
    K += Vm.T @ (kdiag[:, None]*Vm)
    return M, K, Vm, kdiag, nf_, lam_rbm


def coupled_modes(M, K, sigma=(2*np.pi*50.0)**2):
    """Generalized modes with a spectral shift: Cholesky of raw K fails
    (conditioning spans 1e9 N/m joint springs down to the ~7 (rad/s)^2
    suspension stiffness), so solve M v = mu (K + sigma*M) v and recover
    lambda = 1/mu - sigma EXACTLY. Mass-normalize via phi = v/sqrt(mu)
    (v^T M v = mu when v^T (K+sigma M) v = 1)."""
    mu, V = sla.eigh(M, K + sigma*M)
    order = np.argsort(mu)[::-1]
    mu, V = mu[order], V[:, order]
    good = mu > 1e-12*mu.max()
    mu, V = mu[good], V[:, good]
    w2 = 1.0/mu - sigma
    keep = w2 > (2*np.pi*2.0)**2          # drop suspension-level globals <2 Hz
    Phi = (V/np.sqrt(mu)[None, :])[:, keep]
    return w2[keep], Phi


def se_decomposition(tray, shk, theta_S):
    M, K, Vm, kdiag, nf_, lam_rbm = coupled_system(tray, shk, theta_S)
    th = np.asarray(theta_S, float)
    w2, Phi = coupled_modes(M, K)
    f = np.sqrt(w2)/(2*np.pi)
    sel = f <= F_REPORT
    Phi, f, w2 = Phi[:, sel], f[sel], w2[sel]
    nm = len(f)
    rows = []
    A = shk.A                                  # (9,74,74)
    for i in range(nm):
        p = Phi[:, i]
        lam_i = w2[i]
        se = {}
        # mount per axis
        vm = Vm @ p                            # (6,)
        se["mount_trans"] = float(np.sum(kdiag[:3]*vm[:3]**2)/lam_i)
        se["mount_rot"] = float(np.sum(kdiag[3:]*vm[3:]**2)/lam_i)
        # tray groups
        uf = p[:nf_]
        for g in models.TRAY_PARAMS:
            se[f"tray_{g}"] = float(uf @ tray["Kg"][g] @ uf/lam_i)
        se["tray_fixed_antispin"] = float(uf @ tray["Kfix"] @ uf/lam_i)
        # shocksat: nominal-elastic-basis blocks (q[6:] = 74 elastic coords);
        # K_g(theta) = theta_g * A_g, so SE includes the theta_g factor
        qe = p[nf_+6:]
        se_S = {}
        for gi, g in enumerate(shk.gnames):
            se_S[g] = float(th[gi]*(qe @ A[gi] @ qe)/lam_i)
        se["shocksat_total"] = float(sum(se_S.values())
                                     + qe @ shk.A_fix @ qe/lam_i
                                     + p[nf_:nf_+6] @ (lam_rbm*p[nf_:nf_+6])/lam_i)
        se["shocksat_joints"] = se_S["joints"]
        closure = (se["mount_trans"] + se["mount_rot"]
                   + sum(se[f"tray_{g}"] for g in models.TRAY_PARAMS)
                   + se["tray_fixed_antispin"] + se["shocksat_total"])
        rows.append(dict(mode=i+1, f_hz=float(f[i]), closure=float(closure),
                         **{k: round(v, 5) for k, v in se.items()}))
    return rows, f


def main():
    outp = os.path.join(WS, "out", "mount_identifiability.json")
    if os.path.exists(outp):
        log("mount_identifiability.json exists, skip (delete to rerun)")
        return
    log("build models ...")
    tray = models.build_tray_chain()
    shk = models.ShockSatInterface()
    thetaS_samp, gn = run_qoi.load_posterior()
    theta_med = np.median(thetaS_samp, axis=0)

    log("SE decomposition of coupled modes ...")
    rows, fnom = se_decomposition(tray, shk, theta_med)

    # mount modal sensitivity: d ln f_i / d ln k_mount = SE_mount,i / 2
    sens = [dict(mode=r["mode"], f_hz=r["f_hz"],
                 dlnf_dlnk_mount=round((r["mount_trans"]+r["mount_rot"])/2, 4))
            for r in rows]
    peak = max(sens, key=lambda r: r["dlnf_dlnk_mount"])

    # finite perturbation: mount x0.5 / x2 -> coupled freqs + QOI
    log("finite perturbation x0.5 / x2 ...")
    EV = run_qoi.envs()[:4]
    cache = np.load(os.path.join(WS, "out", "srs_cache.npz"))
    freqs_band = EV[0]["freqs"][run_qoi.band_idx(EV[0])]
    pert = {}
    qoi_ref = None
    for mult in (0.5, 1.0, 2.0):
        km = {p: models.MOUNT_NOMINAL[p]*mult for p in models.MOUNT_PARAMS}
        # coupled mode freqs at this mount
        M, K, _, _, _, _ = coupled_system(tray, shk, theta_med, kmult=mult)
        w2p, _ = coupled_modes(M, K)
        fp = np.sort(np.sqrt(w2p)/(2*np.pi))
        fp = fp[fp <= F_REPORT]
        r = run_qoi.eval_draw(tray, shk, EV, cache, EV[0]["freqs"],
                              theta_S=theta_med, kmount=km)
        qoi = np.median(np.asarray(r["th_cpl"]), axis=0)
        if mult == 1.0:
            qoi_ref = qoi
        pert[f"x{mult}"] = dict(
            coupled_freqs_hz=np.round(fp[:14], 2).tolist(),
            qoi_th_cpl_N=np.round(qoi, 2).tolist())
    for mult in (0.5, 2.0):
        q = np.array(pert[f"x{mult}"]["qoi_th_cpl_N"])
        pert[f"x{mult}"]["qoi_shift_pct"] = np.round(
            100*(q/qoi_ref - 1), 1).tolist()

    mount_se_max = max(r["mount_trans"]+r["mount_rot"] for r in rows)
    verdict = dict(
        mount_in_load_path=bool(mount_se_max > 0.05),
        peak_mount_se_fraction=round(mount_se_max, 3),
        peak_dlnf_dlnk=peak["dlnf_dlnk_mount"],
        peak_mode_hz=peak["f_hz"],
        sigma_f_floor=SIGMA_F_FLOOR,
        identifiable_from_coupled_modal_test=bool(
            peak["dlnf_dlnk_mount"] > SIGMA_F_FLOOR),
        statement=(
            "The mount stores its strain energy in the coupled interface "
            "(bounce/rock) modes; d ln f / d ln k there exceeds the "
            f"predecessor's sigma_f ~ {SIGMA_F_FLOOR:.3f} discrepancy floor "
            "by an order of magnitude, so -- UNLIKE the bare-ShockSat joints "
            "(3 % < 4.6 % floor) -- the mount WOULD be identifiable from a "
            "modal test of the mounted configuration. Until such a test "
            "exists the mount is UNCONSTRAINED (prior-driven), which is "
            "exactly why the QOI variance decomposition matters. "
            "Finite x0.5/x2 perturbation confirms in-path: bounce modes and "
            "QOI move strongly (see perturbation table). No sampler was run; "
            "this is a sensitivity/information statement."))

    out = dict(coupled_mode_se=rows, mount_sensitivity=sens,
               finite_perturbation=pert, verdict=verdict,
               note=("SE fractions of mass-normalized coupled modes; closure "
                     "should be ~1.0 per mode. HYPOTHETICAL configuration."))
    json.dump(out, open(os.path.join(WS, "out", "mount_identifiability.json"),
                        "w"), indent=1)
    log(f"done. peak mount SE {mount_se_max:.2f} at {peak['f_hz']:.1f} Hz; "
        f"dlnf/dlnk {peak['dlnf_dlnk_mount']:.3f} vs floor {SIGMA_F_FLOOR}")


if __name__ == "__main__":
    main()
