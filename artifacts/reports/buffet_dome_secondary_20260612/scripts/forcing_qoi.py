#!/usr/bin/env python3
"""Max-q buffet (Corcos) random response -> the four QOI sets (D6, D12).

Method (validated in S1 on the analytic plate, here generalized to the
cylinder with a SEPARATE finer load grid):
  pressure CSD on barrel OML  S_pp(x,x',f) = Phi_p(f) * Cx(dz;f) * Ct(ds;f)
    Cx = exp(-ax*w*|dz|/Uc) * exp(i*w*dz/Uc)   (axial: decay + convection)
    Ct = exp(-ay*w*|ds|/Uc), ds = periodic arc  (circumferential: decay)
  modal force CSD never formed: for each QOI row L (a linear functional of
  modal coords) and frequency,
    S_LL(f) = sum_{p,n} lam_x[p] * lam_t[n] * |yhat[p,n]|^2,
    yhat = Ux^H @ (F_all @ g),  g_j = L_j * H_j(f) (*(2*pi*f)^2 for accel)
  with F_all = theta-FFT of area-weighted radial mode shapes on the load
  grid (precomputed once), Dx = Ux diag(lam_x) Ux^H (64x64 eigh per freq),
  lam_t = FFT eigenvalues of the circulant arc kernel (clipped at 0,
  clip fraction recorded).

Load grid: 64 axial x 720 circumferential (arc 19.6 mm = 5.9 nodes per
lateral coherence length at 400 Hz -> S1 G3 rule met at band top).

QOI channels per BC (quantity_contracts Q1-Q4):
  strut_1..6      axial force [N]
  tray_net_F[xyz], tray_net_punch (dome-normal), tray_net_M[xyz] about c_tray
  copv_net_F[xyz], copv_net_punch
  av_acc_[xyz]    avionics-box CG accel (incl. rotation x offset)
  tray_field      49-node out-of-plane accel set (max/median reported)
  copv_field      12-channel radial accel set
Damping: uniform structural eta=0.02 (ledger C1) -> H_j = 1/(wj^2(1+i*eta)-w^2).
Caveat carried everywhere: BUFFET-ONLY forcing (D12) — high band would be
acoustic-co-driven in flight; vehicle numbers are unverified assumptions.

Usage: python3 scripts/forcing_qoi.py [bcA|bcB]
Output: out/qoi_<bc>.npz + out/qoi_<bc>_summary.json
"""
import json
import sys
import time
from pathlib import Path

import numpy as np
import scipy.sparse as sp

WS = Path(__file__).resolve().parent.parent
BC = sys.argv[1] if len(sys.argv) > 1 else "bcA"
T0 = time.time()

# ---------------- parameters (ledger D1-D6, C1) ----------------
q_bar = 30e3          # Pa dynamic pressure at max-q (D1)
Cp_rms = 0.04         # rms fluctuating pressure coefficient (D4)
Uc = 210.0            # m/s convection speed (D3)
ax_c, ay_c = 0.12, 0.72   # Corcos decay (D5)
f0_shape = 50.0       # PSD shape corner (D6): flat to f0, then (f/f0)^-2
eta = 0.02            # structural loss factor (C1)
F_LO, F_HI, NF = 20.0, 400.0, 320
EIG_TRUNC = 1e-4      # keep kernel eigenvalues > trunc*max (recorded)

# variant-aware metadata (tags like bcA_kmlo -> model_meta_kmlo.json)
_suf = ("_" + BC.split("_", 1)[1]) if "_" in BC else ""
_meta_p = WS / "out" / f"model_meta{_suf}.json"
if not _meta_p.exists():
    _meta_p = WS / "out" / "model_meta.json"
meta = json.load(open(_meta_p))
par = meta["par"]; sets = meta["sets"]
_xyz_p = WS / "out" / f"xyz{_suf}.npy"
XYZ = np.load(_xyz_p if _xyz_p.exists() else WS / "out" / "xyz.npy")
R, Lb = par["R"], par["Lbar"]

z = np.load(WS / "out" / f"modes_{BC}.npz")
fs, Phi = z["f"], z["Phi"]
sel = fs < 820.0
fs, Phi = fs[sel], Phi[:, sel]          # float32 shapes (memory; QOI rows fine)
wn = 2 * np.pi * fs
m = len(fs)

# pressure PSD level: integral of shape = 2*f0 -> Phi_p = (Cp*q)^2 * shape/(2 f0)
def Phi_p(f):
    shape = np.where(f <= f0_shape, 1.0, (f / f0_shape) ** -2.0)
    return (Cp_rms * q_bar) ** 2 * shape / (2 * f0_shape)

# ---------------- load grid + interpolated radial shapes ----------------
Nxf, Ntf = 64, 720
zs = -Lb + (np.arange(Nxf) + 0.5) * (Lb / Nxf)
ths = 2 * np.pi * np.arange(Ntf) / Ntf
dA = (Lb / Nxf) * (2 * np.pi * R / Ntf)

bg = np.array(sets["barrel_grid"])           # (Nz+1, Nth) node ids
Nzs, Nths = bg.shape
z_nodes = np.linspace(-Lb, 0.0, Nzs)

rows, cols, vals = [], [], []
for i, zf in enumerate(zs):
    iz = min(int((zf + Lb) / (Lb / (Nzs - 1))), Nzs - 2)
    az = (zf - z_nodes[iz]) / (z_nodes[iz + 1] - z_nodes[iz])
    for j, tf in enumerate(ths):
        jt = int(tf / (2 * np.pi / Nths)) % Nths
        at = (tf - jt * 2 * np.pi / Nths) / (2 * np.pi / Nths)
        ct, st = np.cos(tf), np.sin(tf)
        lp = i * Ntf + j
        for (izz, w1) in ((iz, 1 - az), (iz + 1, az)):
            for (jtt, w2) in ((jt, 1 - at), ((jt + 1) % Nths, at)):
                nid = bg[izz, jtt]
                w = w1 * w2
                rows += [lp, lp]
                cols += [6 * nid + 0, 6 * nid + 1]
                vals += [w * ct, w * st]
P_rad = sp.coo_matrix((vals, (rows, cols)),
                      shape=(Nxf * Ntf, Phi.shape[0])).tocsr()
F_grid = (P_rad @ Phi) * dA                       # (Nxf*Ntf, m) area-weighted
F_grid = F_grid.reshape(Nxf, Ntf, m)
# theta-FFT with 1/sqrt(Ntf) (unitary-in-energy convention used by S_quad)
F_all = (np.fft.fft(F_grid, axis=1) / np.sqrt(Ntf)).astype(np.complex64)
del F_grid

# circulant arc kernel eigenvalues (per freq): lam_t[n] = sum_k C(s_k) e^{-i n th_k}
arc = R * np.minimum(ths, 2 * np.pi - ths)


# ---------------- separable quadform (the ONE math kernel; self-checked) ----
def kernel_factors(zv, arcv, f, axc, ayc, uc, trunc=EIG_TRUNC):
    """Per-frequency kernel factorization. Returns (lx, Ux, lt, clip_frac)."""
    w = 2 * np.pi * f
    dz = zv[:, None] - zv[None, :]
    Dx = np.exp(-axc * w * np.abs(dz) / uc) * np.exp(1j * w * dz / uc)
    lx, Ux = np.linalg.eigh(Dx)
    lx = np.clip(lx, 0, None)
    keep = lx > trunc * lx.max()
    ctr = np.exp(-ayc * w * arcv / uc)
    lt = np.real(np.fft.fft(ctr))
    cf = float((lt < 0).sum()) / len(lt)
    return lx[keep], Ux[:, keep], np.clip(lt, 0, None), cf


def S_quad(Yh, lx, Ux, lt):
    """S = sum_{p,n} lx[p] lt[n] |(Ux^H Yh)[p,n]|^2 with Yh = FFT_theta(y)/sqrt(Nt)."""
    yh = Ux.conj().T @ Yh
    return float(np.real(np.einsum("p,pn,n->", lx, np.abs(yh) ** 2, lt)))


def _self_check():
    """Fast separable path MUST equal brute-force full-CSD quadratic form
    (S1 G2 analog, run every invocation; abort on mismatch)."""
    rng = np.random.default_rng(7)
    nx, nt = 6, 16
    zv = np.linspace(0, 1.0, nx)
    thv = 2 * np.pi * np.arange(nt) / nt
    arcv = 0.8 * np.minimum(thv, 2 * np.pi - thv)
    y = rng.standard_normal((nx, nt)) + 1j * rng.standard_normal((nx, nt))
    f, axc, ayc, uc = 37.0, 0.12, 0.72, 210.0
    w = 2 * np.pi * f
    # brute force full matrix
    Z, TH = np.meshgrid(zv, thv, indexing="ij")
    zf, tf = Z.ravel(), TH.ravel()
    dzf = zf[:, None] - zf[None, :]
    dth = np.abs(tf[:, None] - tf[None, :])
    ds = 0.8 * np.minimum(dth, 2 * np.pi - dth)
    Cfull = (np.exp(-axc * w * np.abs(dzf) / uc) * np.exp(1j * w * dzf / uc)
             * np.exp(-ayc * w * ds / uc))
    yf = y.ravel()
    S_ref = float(np.real(yf.conj() @ Cfull @ yf))
    lx, Ux, lt, _ = kernel_factors(zv, arcv, f, axc, ayc, uc, trunc=0.0)
    Yh = np.fft.fft(y, axis=1) / np.sqrt(nt)
    S_fast = S_quad(Yh, lx, Ux, lt)
    rel = abs(S_fast - S_ref) / abs(S_ref)
    if rel > 1e-8:
        raise RuntimeError(f"separable-path self-check FAILED: rel={rel:.2e}")
    return rel


SELF_CHECK_REL = _self_check()

# ---------------- QOI rows (linear functionals over modal coords) -------
def skew(v):
    return np.array([[0, -v[2], v[1]], [v[2], 0, -v[0]], [-v[1], v[0], 0.]])

L_rows, L_names, L_kind = [], [], []   # kind: 'force' (H) or 'accel' (w^2 H)

# struts
tray_frame = sets["tray_frame"]
n_t = np.array(tray_frame["n"]); c_tray = np.array(tray_frame["c"])
strut_F_rows = []
strut_pts = []
for si, (nt, nd) in enumerate(sets["struts"]):
    info = meta["sanity"]["strut_info"][si]
    ex = np.array(info["ex"]); k_eff = info["k_eff"]
    row = np.zeros(m)
    row += k_eff * (ex @ Phi[6 * nd:6 * nd + 3, :] - ex @ Phi[6 * nt:6 * nt + 3, :])
    L_rows.append(row); L_names.append(f"strut_{si+1}_F"); L_kind.append("force")
    strut_F_rows.append((row, ex, XYZ[nd]))
    strut_pts.append(XYZ[nd])

# tray net force/moment about c_tray (sum of strut interface forces on dome)
netF = np.zeros((3, m)); netM = np.zeros((3, m))
for row, ex, xd in strut_F_rows:
    for c in range(3):
        netF[c] += row * ex[c]
    rxe = np.cross(xd - c_tray, ex)
    for c in range(3):
        netM[c] += row * rxe[c]
for c, nm in enumerate("xyz"):
    L_rows.append(netF[c]); L_names.append(f"tray_net_F{nm}"); L_kind.append("force")
L_rows.append(n_t @ netF); L_names.append("tray_net_punch"); L_kind.append("force")
for c, nm in enumerate("xyz"):
    L_rows.append(netM[c]); L_names.append(f"tray_net_M{nm}"); L_kind.append("force")

# COPV mount forces + net
copv_frame = sets["copv_frame"]; n_c = np.array(copv_frame["n"])
copv_netF = np.zeros((3, m))
for mi, (nc, nd) in enumerate(sets["mounts"]):
    p = 0.5 * (XYZ[nc] + XYZ[nd])
    B = np.zeros((3, 12))
    B[:, 0:3] = np.eye(3);  B[:, 3:6] = -skew(p - XYZ[nc])
    B[:, 6:9] = -np.eye(3); B[:, 9:12] = skew(p - XYZ[nd])
    dofs = np.concatenate([6 * nc + np.arange(6), 6 * nd + np.arange(6)])
    Fm = par["k_mount"] * (B @ Phi[dofs, :])      # (3, m)
    for c, nm in enumerate("xyz"):
        L_rows.append(Fm[c]); L_names.append(f"copv_mount{mi+1}_F{nm}")
        L_kind.append("force")
    copv_netF += Fm
for c, nm in enumerate("xyz"):
    L_rows.append(copv_netF[c]); L_names.append(f"copv_net_F{nm}"); L_kind.append("force")
L_rows.append(n_c @ copv_netF); L_names.append("copv_net_punch"); L_kind.append("force")

# avionics accel at box CG (u + theta x d)
av = sets["av_node"]; d_av = np.array(sets["av_offset"])
Sav = skew(d_av)
for c, nm in enumerate("xyz"):
    row = Phi[6 * av + c, :] - (Sav @ Phi[6 * av + 3:6 * av + 6, :])[c]
    L_rows.append(row); L_names.append(f"av_acc_{nm}"); L_kind.append("accel")

# tray field (49 out-of-plane) + copv field (12 radial-ish)
tg = np.array(sets["tray_grid"])
tray_field_idx = []
for i in range(0, 13, 2):
    for j in range(0, 13, 2):
        nid = tg[i, j]
        row = n_t @ Phi[6 * nid:6 * nid + 3, :]
        L_rows.append(row); L_names.append(f"trayfield_{i}_{j}")
        L_kind.append("accel"); tray_field_idx.append(len(L_rows) - 1)
copv_field_idx = []
b_c = np.cross(n_c, np.array(copv_frame["e_ax"]))
for ni, nid in enumerate(sets["copv_nodes"]):
    for dvec, nm in ((n_c, "n"), (b_c, "b")):
        row = dvec @ Phi[6 * nid:6 * nid + 3, :]
        L_rows.append(row); L_names.append(f"copvfield_{ni}_{nm}")
        L_kind.append("accel"); copv_field_idx.append(len(L_rows) - 1)

Lmat = np.array(L_rows)                 # (nL, m)
nL = len(L_rows)
is_accel = np.array([k == "accel" for k in L_kind])

# ---------------- frequency sweep (batched over QOI rows) ----------------
# layout (Nn, Nxf, m) so negligible circumferential harmonics can be sliced
F_h = np.ascontiguousarray(np.transpose(F_all, (1, 0, 2)))   # (Ntf, Nxf, m)
del F_all
fgrid = np.geomspace(F_LO, F_HI, NF)
PSD = np.zeros((nL, NF))
clip_frac = np.zeros(NF)

for i, f in enumerate(fgrid):
    lx, Ux, lt, cf = kernel_factors(zs, arc, f, ax_c, ay_c, Uc)
    clip_frac[i] = cf
    keep_n = np.where(lt > EIG_TRUNC * lt.max())[0]
    w = 2 * np.pi * f
    H = (1.0 / (wn ** 2 * (1 + 1j * eta) - w ** 2)).astype(np.complex64)
    G = (Lmat * H).T.astype(np.complex64)            # (m, nL)
    G[:, is_accel] *= np.complex64(w ** 2)
    Fk = F_h[keep_n]                                  # (nk, Nxf, m)
    Y = Fk.reshape(-1, m) @ G                         # (nk*Nxf, nL)
    Y = Y.reshape(len(keep_n), Nxf, nL)
    yh = np.einsum("xp,nxr->pnr", Ux.conj(), Y)       # (px, nk, nL)
    S = np.einsum("p,n,pnr->r", lx, lt[keep_n], np.abs(yh) ** 2)
    PSD[:, i] = Phi_p(f) * np.real(S)

# RMS over band
rms = np.sqrt(np.trapz(PSD, fgrid, axis=1))

np.savez_compressed(WS / "out" / f"qoi_{BC}.npz",
                    f=fgrid, PSD=PSD, names=np.array(L_names),
                    kind=np.array(L_kind), rms=rms,
                    tray_field_idx=np.array(tray_field_idx),
                    copv_field_idx=np.array(copv_field_idx),
                    clip_frac=clip_frac, n_modes=m, fs_modes=fs)
summary = dict(bc=BC, n_modes_used=m, fmax_mode=float(fs.max()),
               band=[F_LO, F_HI], n_freq=NF,
               forcing=dict(q_bar=q_bar, Cp_rms=Cp_rms, Uc=Uc, ax=ax_c,
                            ay=ay_c, f0_shape=f0_shape,
                            p_rms_total_Pa=Cp_rms * q_bar),
               eta=eta,
               self_check_rel=SELF_CHECK_REL,
               caveat="BUFFET-ONLY (D12); representative unverified vehicle "
                      "numbers; deterministic nominal (no CI yet)",
               rms_headline={nm: float(rv) for nm, rv in zip(L_names, rms)
                             if "field" not in nm},
               clip_frac_max=float(clip_frac.max()),
               runtime_s=time.time() - T0)
json.dump(summary, open(WS / "out" / f"qoi_{BC}_summary.json", "w"), indent=1)
print(json.dumps({k: v for k, v in summary.items() if k != "rms_headline"},
                 indent=1))
print("headline RMS (N / m/s^2):")
for nm, rv in summary["rms_headline"].items():
    print(f"  {nm:>18s} {rv:10.3f}")
