#!/usr/bin/env python3
"""Parametric MPL-stand FEM forward (reused from the fable rebuild; logic validated vs modes_nominal.json).

K(theta) = sum_g theta_g K_g,  M(theta) = sum_g theta_g M_g  (per-group sparse blocks).
Eigensolve = exact massless static condensation + dense generalized eigh subset_by_value (= the fable's modal.py).
OOP (sensor) axis = +X (shield is a y-z panel at x~61.5). The X-translation amplitude at any grid is read from
the RBE2-expanded mode shapes u_full = T_rbe2 @ Phi_master.

Forward transmissibility (the no-force observable, D-B):
  T_a(w) = |sum_i phi_{a,i} gamma_i / D_i(w)| / |sum_i phi_{ref,i} gamma_i / D_i(w)|,
  D_i(w) = lam_i - w^2 + 2 i zeta_i sqrt(lam_i) w,  gamma_i = phi_i^T f  (assumed load shape f).
The acoustic INPUT SPECTRUM cancels in the ratio; only the load SPATIAL shape f enters (default: uniform OOP
pressure on shield grids), and that residual is absorbed by the log-frequency discrepancy GP downstream.

BLAS pin OMP/VECLIB=1 for the small dense eigh.
"""
from __future__ import annotations
import json, os
from pathlib import Path
import numpy as np
import scipy.linalg as sla
import scipy.sparse as sp
import scipy.sparse.linalg as spla

FEM = Path(__file__).resolve().parents[2] / "mpl_stand_fem_rebuild_20260611" / "out" / "model"
FMARGIN = 620.0  # solve a little past the band edge (same as fable)

# node map (X-DOF = OOP). See assumptions_ledger.md; ANDREW-CONFIRM flags there.
NODE_GRID = {
    "interface": 800071,   # shield top-center (shield_mount)
    "shield":    800016,   # shield middle = transmissibility REFERENCE
    "beam":      1510,     # top-left vertical post (beam_mount)
    "avi-L":     800036,   # electronics_box top-left foot (y=-14.4)
    "avi-R":     800034,   # electronics_box top-right foot (y=-4.8)
    # "valve" resolved below to the valve_panel node nearest the frame centroid
}
REF = "shield"


class FEM_model:
    def __init__(self):
        self.meta = json.load(open(FEM / "meta.json"))
        a = np.load(FEM / "arrays.npz", allow_pickle=False)
        self.gid = a["grid_ids"]; self.X = a["X"]; self.region = a["region"].astype(str)
        self.spc_idx = a["spc_master_idx"]; self.NM = self.meta["ndof_master"]
        self.gpos = {int(g): i for i, g in enumerate(self.gid)}
        self.T = sp.load_npz(FEM / "T_rbe2.npz").tocsr()      # (ndof_full, NM)
        self.KG = {n: sp.load_npz(FEM / "groups" / f"K_{n}.npz") for n in self.meta["K_groups"]}
        self.MG = {n: sp.load_npz(FEM / "groups" / f"M_{n}.npz") for n in self.meta["M_groups"]}
        self.nominal = dict(self.meta["nominal_scalars"])
        # resolve valve node = valve_panel grid nearest the frame centroid
        fr = self.X[self.region == "frame"].mean(0)
        vp = self.gid[self.region == "valve_panel"]; vx = self.X[self.region == "valve_panel"]
        self.NODE_GRID = dict(NODE_GRID)
        self.NODE_GRID["valve"] = int(vp[np.argmin(np.linalg.norm(vx - fr, axis=1))])
        self.shield_grids = self.gid[self.region == "shield"]

    def full_xdof(self, grid):
        return self.gpos[int(grid)] * 6 + 0   # X-translation DOF in full space

    def build(self, scal=None):
        s = dict(self.nominal); s.update(scal or {})
        K = M = None
        for n, A in self.KG.items():
            c = s.get(f"K_{n}", 1.0)
            if c == 0.0: continue
            K = c * A if K is None else K + c * A
        for n, A in self.MG.items():
            c = s.get(f"M_{n}", 1.0)
            if c == 0.0: continue
            M = c * A if M is None else M + c * A
        return K.tocsr(), M.tocsr()

    def solve_modes(self, scal=None, fmax=FMARGIN):
        """Returns freqs_hz (<=fmax), Phi_master (NM, nmodes) mass-normalized."""
        K, M = self.build(scal)
        free = np.setdiff1d(np.arange(self.NM), self.spc_idx)
        kdiag = K.diagonal(); dead = free[kdiag[free] == 0.0]
        if dead.size:
            assert M.diagonal()[dead].max() == 0.0
            free = np.setdiff1d(free, dead)
        Kf = K[np.ix_(free, free)].tocsc(); Mf = M[np.ix_(free, free)].tocsr()
        md = Mf.diagonal(); massive = np.where(md > 0)[0]; massless = np.where(md == 0)[0]
        Koo = Kf[np.ix_(massless, massless)]; Kom = Kf[np.ix_(massless, massive)]
        S = spla.splu(Koo.tocsc()).solve(Kom.toarray())
        Kred = Kf[np.ix_(massive, massive)].toarray() - Kf[np.ix_(massive, massless)].toarray() @ S
        Mred = Mf[np.ix_(massive, massive)].toarray(); Kred = 0.5 * (Kred + Kred.T)
        lam_hi = (2 * np.pi * fmax) ** 2
        w2, V = sla.eigh(Kred, Mred, subset_by_value=(-np.inf, lam_hi), driver="gvx")
        freqs = np.sign(w2) * np.sqrt(np.abs(w2)) / (2 * np.pi)
        Phi = np.zeros((self.NM, V.shape[1]))
        Phi_free = np.zeros((free.size, V.shape[1]))
        Phi_free[massive] = V; Phi_free[massless] = -S @ V
        Phi[free] = Phi_free
        return freqs, Phi

    def oop_shapes(self, Phi):
        """X-DOF (OOP) mode shape at every accel location + the uniform-shield load participation gamma_i.
        Returns dict loc->phi_x(nmodes), and gamma(nmodes)."""
        u_full = self.T @ Phi                                   # (ndof_full, nmodes)
        phix = {loc: u_full[self.full_xdof(g)] for loc, g in self.NODE_GRID.items()}
        shield_rows = [self.full_xdof(g) for g in self.shield_grids]
        gamma = u_full[shield_rows].sum(axis=0)                 # uniform unit OOP force on shield X-dofs
        return phix, gamma


def transmissibility(freqs_hz, phix, gamma, zeta, fgrid_hz, locs, ref=REF):
    """Predicted |T_a(f)| for each location in `locs` on fgrid_hz.
    zeta: scalar or per-mode array. Returns dict loc -> |T| (len fgrid)."""
    w = 2 * np.pi * np.asarray(fgrid_hz)
    lam = (2 * np.pi * np.asarray(freqs_hz)) ** 2
    sq = np.sqrt(np.maximum(lam, 0.0))
    z = np.full(lam.shape, float(zeta)) if np.isscalar(zeta) else np.asarray(zeta)
    # D_i(w): (nmodes, nf)
    D = (lam[:, None] - w[None, :] ** 2) + 1j * (2.0 * z[:, None] * sq[:, None] * w[None, :])
    g = np.asarray(gamma)
    Href = np.sum((phix[ref] * g)[:, None] / D, axis=0)
    out = {}
    for loc in locs:
        Ha = np.sum((phix[loc] * g)[:, None] / D, axis=0)
        out[loc] = np.abs(Ha) / np.maximum(np.abs(Href), 1e-300)
    return out


if __name__ == "__main__":
    os.environ.setdefault("OMP_NUM_THREADS", "1"); os.environ.setdefault("VECLIB_MAXIMUM_THREADS", "1")
    fem = FEM_model()
    freqs, Phi = fem.solve_modes()
    ref = json.load(open(FEM.parent / "modes_nominal.json"))
    f_ref = [m["freq_hz"] for m in ref["modes"][:8]]
    print("nominal f1..f8 (Hz):", [round(float(x), 3) for x in freqs[:8]])
    print("reference        :", f_ref)
    err = max(abs(freqs[i] - f_ref[i]) for i in range(8))
    print(f"max |df| over first 8 modes = {err:.4f} Hz  (validate vs fable modal.py)")
    phix, gamma = fem.oop_shapes(Phi)
    print("valve node grid =", fem.NODE_GRID["valve"])
    print("OOP X-amp at locations (mode 1):", {k: round(float(v[0]), 4) for k, v in phix.items()})
    # self-test: T_ref/T_ref == 1 identically
    fg = np.linspace(20, 260, 400)
    T = transmissibility(freqs, phix, gamma, 0.01, fg, list(fem.NODE_GRID), ref="shield")
    print("max|T_shield-1| (forward ref/ref) =", float(np.max(np.abs(T["shield"] - 1.0))))
    assert err < 0.05, "FEM forward does not reproduce fable nominal frequencies"
    assert np.max(np.abs(T["shield"] - 1.0)) < 1e-9, "ref/ref transmissibility != 1"
    print("mpl_fem self-test PASS")
