#!/usr/bin/env python3
"""O1: differentiable reduced ROM of the COUPLED (tray-on-ShockSat) system
for the overnight NUTS calibration (D10).

Full coupled coordinates: [u_f (tray+base-point free DOFs); q (80 ShockSat
ROM coords, nominal elastic basis + 6 RBMs)]. Stiffness is LINEAR in every
parameter:
    K(theta) = K_fix + sum_j  k_nom,j*theta_m,j * Vm_j Vm_j^T   (6 mount axes)
                     + sum_g  theta_T,g * K_tray,g              (5 tray groups)
ShockSat block FIXED at theta_S posterior median (ledger A24).

Reduced basis: union of full coupled mode shapes (f <= F_BASIS) at mount
multipliers MOUNT_GRID (spans the x/9.5 prior), M-orthonormalized via SVD,
capped at NB_CAP vectors. Reduction validated against full eigh at every
anchor (gate <= 0.5 % on modes <= F_VALID).

Outputs: out/coupled_rom.npz  (B_fix, B_mount (6,nb,nb), B_tray (5,nb,nb),
         anchors' eigvecs in reduced coords for pairing/tracking, obs rows),
         out/coupled_rom_report.json
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
import run_qoi  # noqa: E402

MOUNT_GRID = [0.05, 0.25, 1.0, 4.0, 20.0]
F_BASIS = 350.0
F_VALID = 300.0
NB_CAP = 160
SIGMA = (2*np.pi*50.0)**2       # spectral shift (identifiability.py finding)
GATE = 0.005

t0 = time.time()


def log(m):
    print(f"[{time.time()-t0:6.1f}s] {m}", flush=True)


# observation channels for pairing (tray channels + 4 ShockSat nodes x 3 transl)
SHK_OBS_GIDS_HINT = 4


def tray_obs_channels(tray):
    import proxy_qoi
    return proxy_qoi.channels(tray)            # (name, free-dof idx, comp)


def shocksat_obs_rows(shk):
    """4 extra ShockSat accel nodes (top plate edge, cross-beam area, bottom
    box corner, mid top-box) -> rows (12, 80) in q coords, SI translations."""
    import scipy.sparse as sp
    T = sp.load_npz(os.path.join(models.SHK, "matrices", "T.npz")).tocsr()
    V = np.load(os.path.join(models.SHK, "matrices", "V_keep.npy"),
                mmap_mode="r")
    g2i = {int(g): i for i, g in enumerate(shk.gids)}
    cand = []
    # pick by geometry: top edge, z~42 crossbeam, bottom corner, mid height
    targets = [(8.0, 0.0, 57.7), (0.0, 8.0, 42.3), (10.0, 10.0, 1.0),
               (-10.0, 0.0, 30.0)]
    xyz = shk.xyz
    for tx, ty, tz in targets:
        d = np.linalg.norm(xyz - np.array([tx, ty, tz]), axis=1)
        cand.append(int(shk.gids[int(np.argmin(d))]))
    rows = []
    for gid in cand:
        i = g2i[gid]
        B = np.asarray(T[6*i:6*i+3, :] @ V)    # translations only (3, 80)
        rows.append(B / np.sqrt(models.SNAIL2KG))
    return np.vstack(rows), cand               # (12, 80)


def main():
    outp = os.path.join(WS, "out", "coupled_rom.npz")
    if os.path.exists(outp):
        log("coupled_rom.npz exists, skip")
        return
    log("build tray + shocksat ...")
    tray = models.build_tray_chain()
    shk = models.ShockSatInterface()
    thetaS, _ = run_qoi.load_posterior()
    th_med = np.median(thetaS, axis=0)

    # ---- full coupled blocks (theta_S FIXED at median; ledger A24)
    K_el = shk.A_fix + np.einsum("g,gij->ij", th_med, shk.A)
    phi_all = np.hstack([shk.B_rbm, shk.B_el])         # (6, 80) SI rows at P
    nf_ = tray["M"].shape[0]
    n = nf_ + 80
    ib = tray["ibase"]
    M = np.zeros((n, n))
    M[:nf_, :nf_] = tray["M"]
    M[nf_:, nf_:] = np.eye(80)
    K_fix = np.zeros((n, n))
    K_fix[:nf_, :nf_] = tray["Kfix"]
    K_fix[nf_:nf_+6, nf_:nf_+6] = np.diag(shk.lam_rbm)
    K_fix[nf_+6:, nf_+6:] = K_el
    K_tray_groups = {}
    for g in models.TRAY_PARAMS:
        Kg = np.zeros((n, n))
        Kg[:nf_, :nf_] = tray["Kg"][g]
        K_tray_groups[g] = Kg
    # mount rank-1 patterns v_j = e(u_bp_j) - phi_all[j,:]
    Vm = np.zeros((6, n))
    for j in range(6):
        Vm[j, ib[j]] = 1.0
        Vm[j, nf_:] = -phi_all[j, :]
    knom = np.array([models.MOUNT_NOMINAL[p] for p in models.MOUNT_PARAMS])

    def K_at(mult):
        K = K_fix + sum(K_tray_groups[g] for g in models.TRAY_PARAMS)
        return K + Vm.T @ ((knom*mult)[:, None]*Vm)

    def full_modes(K, fmax):
        mu, V = sla.eigh(M, K + SIGMA*M)
        order = np.argsort(mu)[::-1]
        mu, V = mu[order], V[:, order]
        good = mu > 1e-12*mu.max()
        mu, V = mu[good], V[:, good]
        w2 = 1.0/mu - SIGMA
        keep = (w2 > (2*np.pi*2.0)**2) & (w2 < (2*np.pi*fmax)**2)
        Phi = (V/np.sqrt(mu)[None, :])[:, keep]        # mass-normalized
        return np.sqrt(w2[keep])/(2*np.pi), Phi

    # ---- union basis over the mount grid
    cols = []
    anchor_modes = {}
    for mult in MOUNT_GRID:
        f, Phi = full_modes(K_at(mult), F_BASIS)
        anchor_modes[mult] = (f, Phi)
        cols.append(Phi)
        log(f"anchor x{mult}: {Phi.shape[1]} modes <= {F_BASIS} Hz, "
            f"f1={f[0]:.1f} Hz")
    U = np.hstack(cols)                                # (n, ncol)
    # M-orthonormalize: G = U^T M U, eigendecompose, keep dominant directions
    G = U.T @ (M @ U)
    s, P = np.linalg.eigh(G)
    order = np.argsort(s)[::-1]
    s, P = s[order], P[:, order]
    keep = s > 1e-10*s[0]
    nb = min(NB_CAP, int(keep.sum()))
    W = U @ (P[:, :nb] / np.sqrt(s[:nb])[None, :])     # (n, nb), W^T M W = I
    log(f"basis: {U.shape[1]} union cols -> nb = {nb} (cap {NB_CAP}); "
        f"sv ratio at cut {s[nb-1]/s[0]:.1e}")

    # ---- reduced blocks
    B_fix = W.T @ (K_fix @ W)
    B_tray = np.stack([W.T @ (K_tray_groups[g] @ W)
                       for g in models.TRAY_PARAMS])
    VmW = Vm @ W                                       # (6, nb)
    # mount block j (unit multiplier) = k_nom,j * vmw_j vmw_j^T
    B_mount = np.stack([knom[j]*np.outer(VmW[j], VmW[j]) for j in range(6)])

    # ---- validation: reduced vs full, EIGENVECTOR-MATCHED (a union basis
    # reproduces each anchor's eigenpairs exactly via Galerkin, but adds
    # interlaced SPURIOUS modes from the foreign anchor directions, so a
    # sorted-prefix frequency comparison misaligns. Match each full mode to
    # the reduced mode with max mass-weighted overlap; also report the
    # spurious modes' max overlap so tracking safety is auditable.)
    MW = M @ W                                          # (n, nb)

    def red_eig(mult, tray_theta=None):
        th_t = tray_theta or {}
        K = B_fix.copy()
        for j in range(6):
            K += mult*B_mount[j]
        for gi, g in enumerate(models.TRAY_PARAMS):
            K += float(th_t.get(g, 1.0))*B_tray[gi]
        lam, Q = np.linalg.eigh(K)
        return np.sqrt(np.clip(lam, 0, None))/(2*np.pi), Q

    def matched_err(f_full, Phi_full, fr, Qr):
        Ov = np.abs(Phi_full.T @ (MW @ Qr))             # (nfull, nb)
        j = np.argmax(Ov, axis=1)
        ov = Ov[np.arange(len(f_full)), j]
        err = np.abs(fr[j] - f_full)/f_full
        return err, ov, j

    report = dict(mount_grid=MOUNT_GRID, f_basis=F_BASIS, f_valid=F_VALID,
                  nb=int(nb), union_cols=int(U.shape[1]), anchors={})
    worst = 0.0
    for mult in MOUNT_GRID:
        ff, Pf = anchor_modes[mult]
        sel = ff <= F_VALID
        ff, Pf = ff[sel], Pf[:, sel]
        fr, Qr = red_eig(mult)
        err, ov, j = matched_err(ff, Pf, fr, Qr)
        n_spur = int(np.sum((fr > 5) & (fr <= F_VALID))) - len(np.unique(j))
        report["anchors"][f"x{mult}"] = dict(
            n_modes=len(ff), max_rel_err=float(err.max()),
            median_rel_err=float(np.median(err)),
            min_match_overlap=float(ov.min()),
            n_spurious_in_band=n_spur)
        worst = max(worst, float(err.max()))
        log(f"validate x{mult}: {len(ff)} modes, max |df|/f = {err.max():.2e},"
            f" min overlap {ov.min():.3f}, spurious in-band {n_spur}")
    # off-anchor probe (mount x0.6, tray theta off-nominal): the honest test
    # of basis SPAN (no anchor eigvecs in the basis here)
    th_probe = {g: v for g, v in zip(models.TRAY_PARAMS,
                                     [1.2, 0.8, 1.15, 0.7, 1.3])}
    Kp = K_fix + sum(th_probe[g]*K_tray_groups[g] for g in models.TRAY_PARAMS)
    Kp = Kp + Vm.T @ ((knom*0.6)[:, None]*Vm)
    fp, Pp = full_modes(Kp, F_VALID)
    frp, Qrp = red_eig(0.6, th_probe)
    errp, ovp, _ = matched_err(fp, Pp, frp, Qrp)
    report["off_anchor_probe"] = dict(
        mount_mult=0.6, tray_theta=th_probe, n_modes=len(fp),
        max_rel_err=float(errp.max()), median_rel_err=float(np.median(errp)),
        min_match_overlap=float(ovp.min()))
    worst = max(worst, float(errp.max()))
    log(f"off-anchor probe: max |df|/f = {errp.max():.2e}, "
        f"min overlap {ovp.min():.3f}")
    report["worst_rel_err"] = worst
    report["gate"] = GATE
    report["gate_status"] = ("green" if worst <= GATE else
                             "yellow" if worst <= 4*GATE else "red")
    log(f"reduction gate: worst {worst:.2e} vs {GATE} -> "
        f"{report['gate_status']}")

    # ---- observation rows for pairing (tray channels + ShockSat nodes)
    ch = tray_obs_channels(tray)
    obs_rows = np.zeros((len(ch)+12, nb))
    obs_names = []
    for ci, (nm, fi, comp) in enumerate(ch):
        obs_rows[ci] = W[fi, :]
        obs_names.append(nm)
    shk_rows, shk_gids = shocksat_obs_rows(shk)        # (12, 80) in q coords
    obs_rows[len(ch):] = shk_rows @ W[nf_:, :]
    for gid in shk_gids:
        for ax in "xyz":
            obs_names.append(f"shk_{gid}_{ax}")

    # ---- anchor eigvecs in reduced coords (for pairing + tracking)
    anchors_red = {}
    for mult in MOUNT_GRID:
        K = B_fix.copy()
        for j in range(6):
            K += mult*B_mount[j]
        for gi in range(5):
            K += B_tray[gi]
        lam, Q = np.linalg.eigh(K)
        anchors_red[f"x{mult}"] = Q
    np.savez_compressed(
        outp, B_fix=B_fix, B_mount=B_mount, B_tray=B_tray,
        knom=knom, nb=nb, obs_rows=obs_rows,
        obs_names=np.array(obs_names),
        theta_S_fixed=th_med,
        **{f"anchorQ_{k}": v for k, v in anchors_red.items()})
    json.dump(report, open(os.path.join(WS, "out", "coupled_rom_report.json"),
                           "w"), indent=1)
    log("coupled_rom.npz written")


if __name__ == "__main__":
    main()
