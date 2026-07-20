#!/usr/bin/env python3
"""Response-limit PROXY for the avionics-accel channel (vision 2.2 / D7).

Industry rarely force-limits; it RESPONSE-limits — it limits an acceleration
that tracks the interface load, because accelerometers are cheap and interface
force gauges are not. This script formally promotes the avionics-box
acceleration to a response-limit proxy for the tray interface load, and says
exactly where it is valid and where it is not.

Method (random-vibration cross-spectral, exact in this linear model):
  For two linear QOI functionals a (avionics accel) and F (interface force),
  build the cross-PSD S_aF(f) with the SAME Corcos buffet machinery used for the
  auto-PSDs (cross-quadform over the kernel eigenpairs). Then
    coherence   gamma^2(f) = |S_aF|^2 / (S_aa S_FF)   in [0,1]
    proxy gain  alpha(f)   = sqrt(S_FF / S_aa)          (force per accel)
  A good proxy: gamma^2 ~ 1 across the band where S_FF peaks (the controlling
  mode), and alpha ~ constant there. The response limit is then
    a_limit = F_allow / alpha(controlling mode).

Robustness (the reason response limiting works, and a robust-twin tie):
  alpha cancels the forcing level EXACTLY (S_FF and S_aa both scale with Phi_p),
  and at an isolated controlling mode it is a pure modal ratio independent of
  damping. We DEMONSTRATE this: alpha at the controlling mode is recomputed for
  a grid of eta and forcing levels and shown invariant -> the proxy gain is a
  STRUCTURAL constant even though the absolute environment (and its CI) is
  highly uncertain.

7004C tie: at the suspension/global mode the avionics rides with the tray, so
  alpha ~ effective mass m_assy (force = m_assy * base accel) -> the proxy IS
  the 7004C effective-mass relation, read through a response sensor.

BC-A, D14 model. Output: out/response_limit_proxy.json (+ data for the figure).
"""
import json
import time
from pathlib import Path

import numpy as np
import scipy.sparse as sp

WS = Path(__file__).resolve().parent.parent
T0 = time.time()

# forcing constants (match forcing_qoi nominal)
q_bar, Cp0, Uc0, ax0, ay0, f00 = 30e3, 0.04, 210.0, 0.12, 0.72, 50.0
EIG_TRUNC = 1e-4

meta = json.load(open(WS / "out" / "model_meta.json"))
par, sets = meta["par"], meta["sets"]
XYZ = np.load(WS / "out" / "xyz.npy")
R, Lb = par["R"], par["Lbar"]

z = np.load(WS / "out" / "modes_bcA.npz")
fs, Phi = z["f"], z["Phi"]
sel = fs < 820.0
fs, Phi = fs[sel], Phi[:, sel]
wn = 2 * np.pi * fs
m = len(fs)

# ---- load grid + F_h (same construction as forcing_qoi) ----
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
                rows += [lp, lp]; cols += [6 * nid + 0, 6 * nid + 1]
                vals += [w1 * w2 * ct, w1 * w2 * st]
P_rad = sp.coo_matrix((vals, (rows, cols)),
                      shape=(Nxf * Ntf, Phi.shape[0])).tocsr()
F_grid = ((P_rad @ Phi) * dA).reshape(Nxf, Ntf, m)
F_h = np.ascontiguousarray(np.transpose(
    (np.fft.fft(F_grid, axis=1) / np.sqrt(Ntf)), (1, 0, 2))).astype(np.complex64)
del F_grid


def skew(v):
    return np.array([[0, -v[2], v[1]], [v[2], 0, -v[0]], [-v[1], v[0], 0.]])


# ---- rows: proxy accel (av_z) + controlled loads (tray punch, worst strut) +
#      tray-assembly CG accel (for the effective-mass reading) ----
n_t = np.array(sets["tray_frame"]["n"])
tray_punch = np.zeros(m)
strut_rows = []
for si, (nt, nd) in enumerate(sets["struts"]):
    info = meta["sanity"]["strut_info"][si]
    ex = np.array(info["ex"]); k_eff = info["k_eff"]
    rr = k_eff * (ex @ Phi[6 * nd:6 * nd + 3, :] - ex @ Phi[6 * nt:6 * nt + 3, :])
    strut_rows.append(rr)
    tray_punch += (ex @ n_t) * rr
strut_idx = int(np.argmax([np.abs(r).sum() for r in strut_rows]))
strut_worst = strut_rows[strut_idx]

av = sets["av_node"]; d_av = np.array(sets["av_offset"]); Sav = skew(d_av)
av_z = Phi[6 * av + 2, :] - (Sav @ Phi[6 * av + 3:6 * av + 6, :])[2]

# tray-assembly CG accel along dome normal (mass-weighted tray plate + avionics)
tg = np.array(sets["tray_grid"]).ravel()
m_av = par["m_avionics"]
m_plate = meta["sanity"]["mass_parts"]["tray"]
w_nodes = (m_plate / len(tg))
cg_acc = np.zeros(m)
for nid in tg:
    cg_acc += w_nodes * (n_t @ Phi[6 * nid:6 * nid + 3, :])
cg_acc += m_av * av_z
cg_acc /= (m_plate + m_av)        # mass-weighted average accel (CG proxy)

ROWS = {"av_acc_z": (av_z, "accel"),
        "tray_punch": (tray_punch, "force"),
        "strut_worst": (strut_worst, "force"),
        "cg_acc": (cg_acc, "accel")}
names = list(ROWS)
L = np.array([ROWS[k][0] for k in names])
is_accel = np.array([ROWS[k][1] == "accel" for k in names])
nL = len(names)


def Phi_p(f, cp=Cp0, f0=f00):
    shape = np.where(f <= f0, 1.0, (f / f0) ** -2.0)
    return (cp * q_bar) ** 2 * shape / (2 * f0)


def cross_psd_matrix(f, eta, uc=Uc0, axc=ax0, ayc=ay0, cp=Cp0, f0=f00):
    """Full nL x nL cross-PSD matrix among the rows at frequency f."""
    w = 2 * np.pi * f
    dz = zs[:, None] - zs[None, :]
    Dx = np.exp(-axc * w * np.abs(dz) / uc) * np.exp(1j * w * dz / uc)
    lx, Ux = np.linalg.eigh(Dx); lx = np.clip(lx, 0, None)
    keep = lx > EIG_TRUNC * lx.max(); lx, Ux = lx[keep], Ux[:, keep]
    ctr = np.exp(-ayc * w * arc / uc)
    lt = np.clip(np.real(np.fft.fft(ctr)), 0, None)
    keep_n = np.where(lt > EIG_TRUNC * lt.max())[0]
    H = (1.0 / (wn ** 2 * (1 + 1j * eta) - w ** 2)).astype(np.complex64)
    G = (L * H).T.astype(np.complex64)               # (m, nL)
    G[:, is_accel] *= np.complex64(w ** 2)
    Y = (F_h[keep_n].reshape(-1, m) @ G).reshape(len(keep_n), Nxf, nL)
    yh = np.einsum("xp,nxr->pnr", Ux.conj(), Y)      # (px, nk, nL)
    wgt = lx[:, None] * lt[keep_n][None, :]          # (px, nk)
    S = np.einsum("pn,pnr,pns->rs", wgt, yh, yh.conj())
    return Phi_p(f, cp, f0) * S                      # complex Hermitian


# ---- band sweep: auto, cross, coherence, gain (nominal eta) ----
eta_nom = 0.02
fgrid = np.geomspace(20.0, 400.0, 200)
ia, iF, iS, iC = (names.index("av_acc_z"), names.index("tray_punch"),
                  names.index("strut_worst"), names.index("cg_acc"))
Saa = np.zeros(len(fgrid)); SFF = np.zeros(len(fgrid)); Sss = np.zeros(len(fgrid))
gam_F = np.zeros(len(fgrid)); gam_S = np.zeros(len(fgrid))
alpha_F = np.zeros(len(fgrid)); alpha_S = np.zeros(len(fgrid))
Scc = np.zeros(len(fgrid)); gam_cgF = np.zeros(len(fgrid)); alpha_cgF = np.zeros(len(fgrid))
for i, f in enumerate(fgrid):
    S = cross_psd_matrix(f, eta_nom)
    Saa[i] = np.real(S[ia, ia]); SFF[i] = np.real(S[iF, iF])
    Sss[i] = np.real(S[iS, iS]); Scc[i] = np.real(S[iC, iC])
    gam_F[i] = np.abs(S[ia, iF]) ** 2 / (Saa[i] * SFF[i] + 1e-300)
    gam_S[i] = np.abs(S[ia, iS]) ** 2 / (Saa[i] * Sss[i] + 1e-300)
    gam_cgF[i] = np.abs(S[iC, iF]) ** 2 / (Scc[i] * SFF[i] + 1e-300)
    alpha_F[i] = np.sqrt(SFF[i] / (Saa[i] + 1e-300))
    alpha_S[i] = np.sqrt(Sss[i] / (Saa[i] + 1e-300))
    alpha_cgF[i] = np.sqrt(SFF[i] / (Scc[i] + 1e-300))

# controlling mode = frequency where the tray punch PSD peaks
ic = int(np.argmax(SFF))
f_ctrl = float(fgrid[ic])
m_assy = m_plate + m_av

# ---- robustness: alpha at controlling freq across eta and forcing ----
robust = {}
for eta in (0.005, 0.01, 0.02, 0.05):
    S = cross_psd_matrix(f_ctrl, eta)
    robust[f"eta_{eta}"] = dict(
        alpha_avF=float(np.sqrt(np.real(S[iF, iF]) / np.real(S[ia, ia]))),
        gamma_avF=float(np.abs(S[ia, iF]) ** 2 /
                        (np.real(S[ia, ia]) * np.real(S[iF, iF]))),
        alpha_cgF=float(np.sqrt(np.real(S[iF, iF]) / np.real(S[iC, iC]))))
# forcing-level invariance (analytic: alpha independent of cp/f0; verify once)
S_lo = cross_psd_matrix(f_ctrl, 0.02, cp=0.02)
S_hi = cross_psd_matrix(f_ctrl, 0.02, cp=0.08)
alpha_lo = np.sqrt(np.real(S_lo[iF, iF]) / np.real(S_lo[ia, ia]))
alpha_hi = np.sqrt(np.real(S_hi[iF, iF]) / np.real(S_hi[ia, ia]))
alpha_forcing_invariance_rel = float(abs(alpha_hi - alpha_lo) /
                                     max(abs(alpha_lo), 1e-30))

# coherence-weighted valid band (gamma^2 > 0.8)
valid = gam_F > 0.8
band_valid = [float(fgrid[valid].min()), float(fgrid[valid].max())] if valid.any() else None
# fraction of the band PSD energy that sits where the proxy is valid
energy_valid = float(np.trapz(SFF * valid, fgrid) / np.trapz(SFF, fgrid))

OUT = dict(
    controlling_freq_hz=f_ctrl,
    coherence_at_ctrl_avF=float(gam_F[ic]),
    coherence_at_ctrl_cgF=float(gam_cgF[ic]),
    alpha_at_ctrl_avF=float(alpha_F[ic]),
    alpha_at_ctrl_cgF=float(alpha_cgF[ic]),
    m_assy_kg=float(m_assy),
    cg_alpha_vs_mass_ratio=float(alpha_cgF[ic] / m_assy),
    valid_band_gamma_gt_0p8=band_valid,
    fraction_punch_energy_in_valid_band=energy_valid,
    alpha_eta_robustness=robust,
    alpha_forcing_invariance_rel=alpha_forcing_invariance_rel,
    response_limit_note=(
        "a_limit = F_allow / alpha(controlling). With alpha forcing-invariant "
        "and ~eta-invariant at the controlling mode, the response limit is a "
        "STRUCTURAL constant -> robust to the (highly uncertain) buffet level "
        "and damping that dominate the CI."),
    interpretation=(
        "avionics-accel is a VALID response-limit proxy for the tray interface "
        "load where coherence>0.8 (the suspension/controlling band); it DECOUPLES "
        "at the avionics-on-tray local mode (coherence drops) -> do not limit "
        "there. The tray-CG accel is the cleaner proxy (alpha ~ m_assy = 7004C "
        "effective mass); the single avionics sensor approximates it in-band."),
    runtime_s=time.time() - T0)

np.savez_compressed(WS / "out" / "response_limit_proxy.npz",
                    f=fgrid, Saa=Saa, SFF=SFF, Sss=Sss, Scc=Scc,
                    gamma_avF=gam_F, gamma_avS=gam_S, gamma_cgF=gam_cgF,
                    alpha_avF=alpha_F, alpha_avS=alpha_S, alpha_cgF=alpha_cgF,
                    f_ctrl=f_ctrl, m_assy=m_assy)
json.dump(OUT, open(WS / "out" / "response_limit_proxy.json", "w"), indent=1)
print(json.dumps(OUT, indent=1))
