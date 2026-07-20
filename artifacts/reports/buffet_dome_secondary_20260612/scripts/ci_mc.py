#!/usr/bin/env python3
"""CI layer v1 (D7 "CI is key"): propagation Monte Carlo over the documented
forcing + damping priors, per BC. LABELED: propagation MC over PRIORS — there
is NO data and NO sampler here (per AGENTS.md NUTS rule nothing is claimed
about posteriors). Structural-parameter variants (mount stiffness, dome gauge)
are separate re-solves (resolve_variants.py) reported alongside.

Priors (assumptions ledger; every one a documented engineering assumption):
  eta     ~ LogNormal(ln 0.02, 0.50)   damping: THE dominant response lever
  Cp_rms  ~ LogNormal(ln 0.04, 0.40)   buffet level (PSD scales as Cp^2 —
                                       applied analytically, exact)
  Uc      ~ Normal(210, 25) trunc>120  convection speed
  a_scale ~ LogNormal(0, 0.35)         common scale on Corcos alpha_x, alpha_y
  f0      ~ LogNormal(ln 50, 0.35)     buffet spectrum corner (analytic scale
                                       per frequency, exact)
Draws: N_K kernel draws (Uc, a_scale) x N_I inner draws (eta) = N_K*N_I
response sweeps; Cp and f0 layered analytically on top of each sweep.

Output: out/ci_<bc>.npz (per-QOI PSD quantile bands + RMS samples)
        out/ci_<bc>_summary.json
Usage: python3 scripts/ci_mc.py [bcA|bcB]
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
rng = np.random.default_rng(20260612)

N_K, N_I = 12, 12          # 144 sweeps; Cp/f0 analytic on top of each
NF_CI = 96
F_LO, F_HI = 20.0, 400.0
EIG_TRUNC = 1e-4

# nominal forcing constants (must match forcing_qoi.py)
q_bar, Cp0, Uc0, ax0, ay0, f00, eta0 = 30e3, 0.04, 210.0, 0.12, 0.72, 50.0, 0.02

meta = json.load(open(WS / "out" / "model_meta.json"))
par, sets = meta["par"], meta["sets"]
XYZ = np.load(WS / "out" / "xyz.npy")
R, Lb = par["R"], par["Lbar"]

z = np.load(WS / "out" / f"modes_{BC}.npz")
fs, Phi = z["f"], z["Phi"]
sel = fs < 820.0
fs, Phi = fs[sel], Phi[:, sel]
wn = 2 * np.pi * fs
m = len(fs)

# ---- load grid + F_all (same construction as forcing_qoi; headline rows only)
Nxf, Ntf = 64, 720
zs = -Lb + (np.arange(Nxf) + 0.5) * (Lb / Nxf)
ths = 2 * np.pi * np.arange(Ntf) / Ntf
dA = (Lb / Nxf) * (2 * np.pi * R / Ntf)
arc = R * np.minimum(ths, 2 * np.pi - ths)
bg = np.array(sets["barrel_grid"]); Nzs, Nths = bg.shape
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
                rows += [lp, lp]
                cols += [6 * nid + 0, 6 * nid + 1]
                vals += [w1 * w2 * ct, w1 * w2 * st]
P_rad = sp.coo_matrix((vals, (rows, cols)),
                      shape=(Nxf * Ntf, Phi.shape[0])).tocsr()
F_grid = ((P_rad @ Phi) * dA).reshape(Nxf, Ntf, m)
F_all = (np.fft.fft(F_grid, axis=1) / np.sqrt(Ntf)).astype(np.complex64)
F_h = np.ascontiguousarray(np.transpose(F_all, (1, 0, 2)))
del F_grid, F_all

# ---- headline QOI rows (subset of forcing_qoi rows; same constructions)
def skew(v):
    return np.array([[0, -v[2], v[1]], [v[2], 0, -v[0]], [-v[1], v[0], 0.]])

L_rows, L_names, L_kind = [], [], []
tray_frame = sets["tray_frame"]
n_t = np.array(tray_frame["n"]); c_tray = np.array(tray_frame["c"])
netF = np.zeros((3, m))
strut_rows = []
for si, (nt, nd) in enumerate(sets["struts"]):
    info = meta["sanity"]["strut_info"][si]
    ex = np.array(info["ex"]); k_eff = info["k_eff"]
    row = k_eff * (ex @ Phi[6 * nd:6 * nd + 3, :] - ex @ Phi[6 * nt:6 * nt + 3, :])
    L_rows.append(row); L_names.append(f"strut_{si+1}_F"); L_kind.append("force")
    for c in range(3):
        netF[c] += row * ex[c]
L_rows.append(n_t @ netF); L_names.append("tray_net_punch"); L_kind.append("force")
copv_frame = sets["copv_frame"]; n_c = np.array(copv_frame["n"])
copv_netF = np.zeros((3, m))
for mi, (nc, nd) in enumerate(sets["mounts"]):
    p = 0.5 * (XYZ[nc] + XYZ[nd])
    B = np.zeros((3, 12))
    B[:, 0:3] = np.eye(3);  B[:, 3:6] = -skew(p - XYZ[nc])
    B[:, 6:9] = -np.eye(3); B[:, 9:12] = skew(p - XYZ[nd])
    dofs = np.concatenate([6 * nc + np.arange(6), 6 * nd + np.arange(6)])
    copv_netF += par["k_mount"] * (B @ Phi[dofs, :])
L_rows.append(n_c @ copv_netF); L_names.append("copv_net_punch"); L_kind.append("force")
av = sets["av_node"]; d_av = np.array(sets["av_offset"]); Sav = skew(d_av)
for c, nm in enumerate("xyz"):
    row = Phi[6 * av + c, :] - (Sav @ Phi[6 * av + 3:6 * av + 6, :])[c]
    L_rows.append(row); L_names.append(f"av_acc_{nm}"); L_kind.append("accel")
Lmat = np.array(L_rows); nL = len(L_rows)
is_accel = np.array([k == "accel" for k in L_kind])

# ---- kernel + quadform (same math as forcing_qoi, self-checked there)
def kernel_factors(f, axc, ayc, uc):
    w = 2 * np.pi * f
    dz = zs[:, None] - zs[None, :]
    Dx = np.exp(-axc * w * np.abs(dz) / uc) * np.exp(1j * w * dz / uc)
    lx, Ux = np.linalg.eigh(Dx)
    lx = np.clip(lx, 0, None)
    keep = lx > EIG_TRUNC * lx.max()
    ctr = np.exp(-ayc * w * arc / uc)
    lt = np.clip(np.real(np.fft.fft(ctr)), 0, None)
    return lx[keep], Ux[:, keep], lt

fgrid = np.geomspace(F_LO, F_HI, NF_CI)

def sweep(eta, uc, a_scale):
    """unit-Cp, unit-shape PSD sweep (Cp^2 and shape applied analytically)."""
    out = np.zeros((nL, NF_CI))
    for i, f in enumerate(fgrid):
        lx, Ux, lt = kernel_factors(f, ax0 * a_scale, ay0 * a_scale, uc)
        keep_n = np.where(lt > EIG_TRUNC * lt.max())[0]
        w = 2 * np.pi * f
        Hc = (1.0 / (wn ** 2 * (1 + 1j * eta) - w ** 2)).astype(np.complex64)
        G = (Lmat * Hc).T.astype(np.complex64)
        G[:, is_accel] *= np.complex64(w ** 2)
        Fk = F_h[keep_n]
        Y = (Fk.reshape(-1, m) @ G).reshape(len(keep_n), Nxf, nL)
        yh = np.einsum("xp,nxr->pnr", Ux.conj(), Y)
        out[:, i] = np.einsum("p,n,pnr->r", lx, lt[keep_n], np.abs(yh) ** 2)
    return out

# ---- MC
draws = []
PSD_samples = np.zeros((N_K * N_I, nL, NF_CI), dtype=np.float32)
k = 0
for ik in range(N_K):
    uc = float(np.clip(rng.normal(Uc0, 25.0), 120.0, None))
    a_scale = float(np.exp(rng.normal(0.0, 0.35)))
    for ii in range(N_I):
        eta = float(np.exp(rng.normal(np.log(eta0), 0.50)))
        cp = float(np.exp(rng.normal(np.log(Cp0), 0.40)))
        f0 = float(np.exp(rng.normal(np.log(f00), 0.35)))
        base = sweep(eta, uc, a_scale)
        shape = np.where(fgrid <= f0, 1.0, (fgrid / f0) ** -2.0) / (2 * f0)
        PSD_samples[k] = base * (cp * q_bar) ** 2 * shape
        draws.append(dict(eta=eta, Uc=uc, a_scale=a_scale, Cp=cp, f0=f0))
        k += 1
        if k % 24 == 0:
            print(f"draw {k}/{N_K*N_I} ({time.time()-T0:.0f}s)", flush=True)

q05, q50, q95 = np.quantile(PSD_samples, [0.05, 0.5, 0.95], axis=0)
rms_samples = np.sqrt(np.trapz(PSD_samples, fgrid, axis=2))
np.savez_compressed(WS / "out" / f"ci_{BC}.npz",
                    f=fgrid, q05=q05, q50=q50, q95=q95,
                    rms_samples=rms_samples, names=np.array(L_names),
                    draws_json=json.dumps(draws))
summ = dict(bc=BC, n_draws=N_K * N_I, n_freq=NF_CI, n_modes=m,
            label="PROPAGATION MC OVER PRIORS — no data, no sampler, no "
                  "posterior claim (AGENTS.md). Structural params NOT varied "
                  "here (see resolve_variants).",
            rms_q05_q50_q95={nm: [float(np.quantile(rms_samples[:, i], q))
                                  for q in (0.05, 0.5, 0.95)]
                             for i, nm in enumerate(L_names)},
            runtime_s=time.time() - T0)
json.dump(summ, open(WS / "out" / f"ci_{BC}_summary.json", "w"), indent=1)
print(json.dumps(summ, indent=1))
