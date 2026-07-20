#!/usr/bin/env python3
"""Gate O — sensor observability / reachable-headroom bound (card §7, NEW).

Uses the delivered modal-test sensor set (76 nodes x 3 = 228 obs DOFs; measured live mask applied) and the
stored inherited-FEM modes at those DOFs (obs_V, computed at theta=1; theta-scaling moves frequencies not
shapes materially). Computes:
  1. self-MAC of the analytical in-band target modes at the sensor set -> max off-diagonal (near 1 => two
     target modes are indistinguishable at the sensors: updating cannot separately correct them);
  2. EfI / Fisher rank of the target-mode partition Phi_s (effective # of modes the sensor set resolves);
  3. representability: fraction of each MEASURED mode's shape captured by the observable target-mode subspace;
     the orthogonal remainder is UNREACHABLE by any theta/damping re-weighting (data-limited, not model-
     limited) -> unobs_resid_frac bounds the reachable headroom;
  4. shape holes: measured modes with best MAC < 0.1 to any FEM target mode.
This is the MODAL-DOMAIN observability bound; it does not need the (heavier) A0 FRF solve and it fundamentally
bounds every S1/S4 outcome. Reported, not pass/fail (a high unobservable fraction is a first-class finding).
"""
import json, os, sys
import numpy as np

WS = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ROOT = os.path.abspath(os.path.join(WS, "..", "..", ".."))
REMESH = os.path.join(ROOT, "artifacts/reports/shocksat_fem_remesh_20260618")
MATD = os.path.join(REMESH, "matrices")
BAND = (45.0, 260.0)


def mac_matrix(A, B):
    """MAC between columns of A and columns of B (real). (nA, nB)."""
    num = (A.T @ B) ** 2
    den = np.outer((A * A).sum(0), (B * B).sum(0)) + 1e-300
    return num / den


def main():
    obs_V = np.load(os.path.join(MATD, "obs_V.npy"))          # (228, 80) FEM modes at obs DOFs
    eigval = np.load(os.path.join(MATD, "eigvals.npy"))       # (80,)
    fem_f = np.sqrt(np.clip(eigval, 0, None)) / (2 * np.pi)
    mm = np.load(os.path.join(REMESH, "measured_modes.npz"))
    shapes = np.asarray(mm["shapes"], float).reshape(33, -1)  # (33, 228)
    meas_f = np.asarray(mm["freqs"], float)
    live = np.asarray(mm["measured"]).reshape(-1)             # (228,) bool
    assert obs_V.shape[0] == shapes.shape[1] == live.shape[0] == 228

    # sensor space = live measured DOFs
    Phi = obs_V[live, :]                                      # (n_live, 80)
    Psi = shapes[:, live].T                                   # (n_live, 33)
    n_live = int(live.sum())

    fem_inb = (fem_f >= BAND[0]) & (fem_f <= BAND[1])
    meas_inb = (meas_f >= BAND[0]) & (meas_f <= BAND[1])
    Phi_b = Phi[:, fem_inb]                                   # (n_live, n_femband)
    Psi_b = Psi[:, meas_inb]                                  # (n_live, n_measband)
    n_target = int(fem_inb.sum())

    # 1. self-MAC of target modes at sensor set
    selfmac = mac_matrix(Phi_b, Phi_b)
    off = selfmac - np.diag(np.diag(selfmac))
    selfmac_max_off = float(off.max())

    # 2. EfI / Fisher rank of the target-mode partition (singular spectrum of Phi_b)
    sv = np.linalg.svd(Phi_b, compute_uv=False)
    rank = int(np.sum(sv > 0.01 * sv.max()))
    # effective independence distribution (Kammer): diag of Phi (Phi^T Phi)^-1 Phi^T -> per-DOF EfI
    G = Phi_b.T @ Phi_b
    Ginv = np.linalg.pinv(G)
    efi = np.einsum("si,ij,sj->s", Phi_b, Ginv, Phi_b)        # per-sensor EfI in [0,1], sum=rank

    # 3. representability: project measured modes onto observable target-mode subspace
    U, s, _ = np.linalg.svd(Phi_b, full_matrices=False)
    U = U[:, s > 0.01 * s.max()]                             # orthonormal basis of observable subspace
    captured = []
    for k in range(Psi_b.shape[1]):
        v = Psi_b[:, k]
        nv = np.linalg.norm(v)
        if nv < 1e-12:
            continue
        proj = U @ (U.T @ v)
        captured.append((np.linalg.norm(proj) / nv) ** 2)
    captured = np.array(captured)
    obs_resid_frac = float(np.mean(captured))
    unobs_resid_frac = float(1.0 - obs_resid_frac)

    # 4. shape holes: measured modes with best MAC < 0.1 to any FEM target mode
    mac_mf = mac_matrix(Psi_b, Phi_b)
    best_mac = mac_mf.max(1)
    shape_holes = int(np.sum(best_mac < 0.1))

    out = {"n_sensor_dofs": n_live, "n_target": n_target, "n_measured_inband": int(meas_inb.sum()),
           "selfmac_max_offdiag": round(selfmac_max_off, 4),
           "fisher_rank": rank, "efi_min": round(float(efi.min()), 4), "efi_max": round(float(efi.max()), 4),
           "obs_resid_frac": round(obs_resid_frac, 4),
           "unobs_resid_frac": round(unobs_resid_frac, 4),
           "captured_frac_median": round(float(np.median(captured)), 4),
           "captured_frac_min": round(float(captured.min()), 4),
           "shape_holes": shape_holes,
           "pass": True,
           "note": ("modal-domain observability bound at the delivered %d-DOF sensor set: %.0f%% of measured "
                    "in-band shape content is UNOBSERVABLE (orthogonal to the inherited-FEM target-mode "
                    "subspace) => that residual is data-limited, NOT fixable by any theta/damping update. "
                    "%d measured modes are shape holes (best MAC<0.1)." )
                   % (n_live, 100 * unobs_resid_frac, shape_holes)}
    os.makedirs(os.path.join(WS, "out"), exist_ok=True)
    json.dump(out, open(os.path.join(WS, "out", "gate_O.json"), "w"), indent=2)
    print(json.dumps(out, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
