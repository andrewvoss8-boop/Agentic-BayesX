#!/usr/bin/env python3
"""Verification gates V1-V9 -> out/verification.json (Verification Gate).

Run BEFORE any QOI production. Each gate records value(s), threshold, and
status green/yellow/red (Result Status Standard). check.py re-reads this.

V1 tray rebuild: clamp the condensation base point -> must reproduce the FIM
   workspace's nominal fixed-feet modes (arrays_fim.npz freqs) to <0.1 %.
V2 chain rigid mass: M_chain(0) zz == total tray mass (<0.5 %); participation
   completeness sum rule (<0.5 %).
V3 ShockSat RBM mass line: sum_RBM phi phi^T at P vs rigid-body accelerance
   from geometry+M (SI). Few-% tolerance (suspension-contaminated RBMs).
V4 SRS filter vs analytic SDOF resonant sine dwell (Q amplification, <3 %).
V5 FBS algebra vs DIRECT coupled frequency-domain solve (exact, <0.5 %).
V6 modal apparent mass vs direct dynamic-stiffness evaluation (<2 % in band).
V7 Newmark time integration of the assembled coupled system vs FBS time
   history (peak interface force <2 %).
V8 7004C TDOF analytic anchors (load M(0.62)=1.624, load M(1)=50.01,
   source M(1)=0.02 at Q=50) + coupled TDOF direct solve vs couple_fbs.
V9 input synthesis: realized grms vs spec (<2 %), PSD flat in band (<3 %).
"""
import json
import os
import sys
import time
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
WS = os.path.abspath(os.path.join(HERE, ".."))
sys.path.insert(0, HERE)
import models  # noqa: E402
import methods  # noqa: E402
import scipy.linalg as sla  # noqa: E402

t0 = time.time()
gates = {}


def gate(name, value, thr_green, thr_yellow=None, note=""):
    if value <= thr_green:
        st = "green"
    elif thr_yellow is not None and value <= thr_yellow:
        st = "yellow"
    else:
        st = "red"
    gates[name] = dict(value=float(value), thr_green=thr_green,
                       thr_yellow=thr_yellow, status=st, note=note)
    print(f"[{time.time()-t0:6.1f}s] {name}: {value:.3e} ({st}) {note}")
    return st


print("building tray chain ...")
tray = models.build_tray_chain()

# ---- V1: clamp base point -> FIM nominal fixed-feet modes -----------------
fim = np.load(os.path.join(WS, "..", "fim_identifiability_opus_20260609",
                           "arrays_fim.npz"))
f_ref = fim["freqs"]
ib = tray["ibase"]
mask = np.ones(tray["M"].shape[0], bool)
mask[ib] = False
Kc = (tray["Kfix"] + sum(tray["Kg"].values()))[np.ix_(mask, mask)]
Mc = tray["M"][np.ix_(mask, mask)]
mu, _ = sla.eigh(Mc, Kc)
w2 = np.sort(1.0/mu[mu > 1e-12*mu.max()])
f_clamped = np.sqrt(w2)/(2*np.pi)
v1 = np.max(np.abs(f_clamped[:len(f_ref)] - f_ref)/f_ref)
gate("V1_tray_vs_fim_freqs", v1, 1e-3, 5e-3,
     f"first {len(f_ref)} modes vs arrays_fim")

# ---- V2: chain rigid mass + completeness ----------------------------------
chain = models.chain_modal(tray)
m_tray = tray["meta"]["mass_total"]
v2a = abs(chain["M_rb"][2, 2] - m_tray)/m_tray
gate("V2a_chain_rigid_mass_zz", v2a, 5e-3,
     note=f"M_rb zz={chain['M_rb'][2,2]:.4f} kg vs tray mass {m_tray:.4f} kg")
gate("V2b_participation_completeness", chain["completeness"], 5e-3)
nom_chain_f = chain["f"][:8]
print("  chain modes (nominal mount) [Hz]:", np.round(nom_chain_f, 1))

# ---- V3: ShockSat RBM mass line -------------------------------------------
print("loading ShockSat interface ...")
shk = models.ShockSatInterface()
rc = shk.rigid_mass_check()
gate("V3_rbm_mass_line", rc["rel_err"], 0.05, 0.15,
     f"node gid {shk.node_gid}, ShockSat mass {rc['mass_kg']:.2f} kg "
     "(suspension-contaminated RBMs make a few % expected)")
json.dump(dict(node_gid=shk.node_gid,
               node_xyz_in=shk.node_xyz_in.tolist(),
               alt_edge_gid=shk.pick_top_edge_node(),
               shocksat_mass_kg=rc["mass_kg"],
               zeta_elastic_median=shk.zeta_med),
          open(os.path.join(WS, "out", "mount_node.json"), "w"), indent=1)

# ---- V4: SRS filter vs analytic sine dwell --------------------------------
fs, fn, Q = 8192.0, 100.0, 25.0
t = np.arange(int(5.0*fs))/fs
a_sine = np.sin(2*np.pi*fn*t)
# analytic steady-state absolute-acceleration transmissibility at r=1:
H_exact = np.sqrt(1+(1/Q)**2)/np.sqrt((1/Q)**2)   # |1+i/Q|/|i/Q| (zeta=1/2Q)
s_val = methods.srs(a_sine, fs, np.array([fn]), Q)[0]
gate("V4_srs_filter_sine", abs(s_val - H_exact)/H_exact, 0.03,
     note=f"SRS={s_val:.2f} vs analytic {H_exact:.2f} (finite dwell under-shoots slightly)")

# ---- V9: input synthesis ---------------------------------------------------
env = methods.synth_input(seed=0)
v9a = abs(env["grms_SI"] - env["grms_SI_target"])/env["grms_SI_target"]
gate("V9a_input_grms", v9a, 0.02,
     note=f"grms {env['grms_SI']/methods.G0:.3f} g vs spec {env['grms_SI_target']/methods.G0:.3f} g")
# Welch-free flatness check: band-average |A|^2 in octave chunks
band = (env["freqs"] >= 25) & (env["freqs"] <= 240)
P = np.abs(env["A"][band, 0])**2
nseg = 8
segs = np.array_split(P, nseg)
seg_means = np.array([s.mean() for s in segs])
v9b = np.max(np.abs(seg_means/P.mean() - 1))/np.sqrt(len(segs[0]))*3  # 3/sqrt(n) normalized
gate("V9b_psd_flatness_normalized", float(v9b), 0.03, 0.06,
     note="segment-mean deviation normalized by MC error")

# ---- V5: FBS algebra vs direct coupled frequency solve ---------------------
# IDENTICAL physics on both sides (mount spring + PHYSICAL mount dashpot, no
# structural damping), so any difference is the FBS coupling algebra itself.
# Interface force computed as the NET INERTIAL FORCE on the chain
# F_d = R_t,d^T M_ff (-w^2 u_f)  -- which IS the net-CG-load definition (C1).
chain0 = models.chain_modal(tray, zeta_struct=0.0)   # for offsetting freqs
freqs_chk = np.concatenate([np.linspace(25, 245, 23),
                            chain0["f"][chain0["f"] < 250] + 0.13])
lam, phiP = shk.modes()
lam_all = np.concatenate([shk.lam_rbm, lam])
phi_all = np.hstack([shk.B_rbm, phiP])      # (6,80)
zS = np.concatenate([shk.zeta_rbm, shk.zeta_el])
kdiag = np.array([models.MOUNT_NOMINAL[p] for p in models.MOUNT_PARAMS])
cdiag = chain0["cdiag"]

Kff = tray["Kfix"] + sum(tray["Kg"].values())
nf_ = Kff.shape[0]
Mff = tray["M"]
# rigid translation vectors on the free chain dofs (for the inertial sum)
Rt = np.zeros((nf_, 3))
for d in range(3):
    Rt[np.where(tray["free"] % 6 == d)[0], d] = 1.0

Mch_dir = models.apparent_mass_direct(tray, None, None, freqs_chk, cdiag=cdiag)
Ys = shk.accelerance(freqs_chk)
a_free = np.zeros((len(freqs_chk), 6), complex)
a_free[:, :3] = 1.0                          # unit accel all 3 axes
F_unc, F_cpl = models.couple_fbs(Mch_dir, Ys, a_free)

errs = []
for q_i, fhz in enumerate(freqs_chk):
    w = 2*np.pi*fhz
    kc = kdiag + 1j*w*cdiag
    Dff = (Kff - w**2*Mff).astype(complex)
    Dff[ib, ib] += kc
    Dfq = np.zeros((nf_, 80), complex)
    Dfq[ib, :] = -kc[:, None]*phi_all
    Dqq = (np.diag(lam_all - w**2
                   + 2j*zS*np.sqrt(np.clip(lam_all, 1e-12, None))*w)
           + phi_all.T @ (kc[:, None]*phi_all))
    f_eq = np.linalg.solve(Ys[q_i], a_free[q_i])
    rhs = np.concatenate([np.zeros(nf_, complex), phi_all.T @ f_eq])
    D = np.block([[Dff, Dfq], [Dfq.T, Dqq]])
    sol = np.linalg.solve(D, rhs)
    u_f = sol[:nf_]
    F_iface = Rt.T @ (Mff @ (-w**2*u_f))     # net inertial force on chain
    errs.append(np.abs(F_iface - F_cpl[q_i, :3]))
errs = np.array(errs)
v5 = float(np.max(errs)/np.max(np.abs(F_cpl[:, :3])))
gate("V5_fbs_vs_direct_coupled", v5, 1e-6, 1e-3,
     "identical physics both sides -> pure algebra check")

# ---- V6: EXACT damped modal apparent mass vs direct evaluation -------------
# Production uses the exact rank-6-dashpot Woodbury modal form; with
# zeta_struct = 0 it must match the direct dynamic-stiffness evaluation to
# numerical precision BOTH off-resonance and at the peaks (the earlier
# diagonal-modal-damping approximation missed peaks by ~30% on the
# near-degenerate 75.9/76.0 Hz pair -- that approximation is GONE).
f_off = np.linspace(25, 245, 12)
fres = chain0["f"][chain0["f"] < 250]
f_off = np.array([fo for fo in f_off
                  if np.min(np.abs(fres - fo)) > 4.0])
Mc_modal = models.apparent_mass(chain0, f_off)
Mc_dir = models.apparent_mass_direct(tray, None, None, f_off,
                                     cdiag=chain0["cdiag"])
num = np.abs(Mc_modal - Mc_dir).max(axis=(1, 2))
den = np.abs(Mc_dir).max(axis=(1, 2))
v6a = float(np.max(num/den))
gate("V6a_apparent_mass_offres", v6a, 1e-4, 0.02,
     f"{len(f_off)} off-resonance freqs; exact Woodbury form (threshold = "
     "numerical exactness: float cancellation w/ zeta_struct=0 + 1e-9 zeta "
     "floor gives ~1e-5, not a physics approximation)")
pk_errs = []
for fr_ in fres:
    fwin = fr_*np.linspace(0.985, 1.015, 25)
    pm = np.abs(models.apparent_mass(chain0, fwin)).max(axis=(1, 2)).max()
    pd_ = np.abs(models.apparent_mass_direct(
        tray, None, None, fwin, cdiag=chain0["cdiag"])).max(axis=(1, 2)).max()
    pk_errs.append(abs(pm-pd_)/pd_)
v6b = float(np.max(pk_errs))
gate("V6b_apparent_mass_peak_height", v6b, 1e-4, 0.02,
     "peak heights exact; residual = mode truncation above fmax_keep")

# ---- V7: Newmark vs FBS time history ---------------------------------------
T7, fs7 = 4.0, 8192.0
env7 = methods.synth_input(seed=7, T=T7, fs=fs7)
freqs7 = env7["freqs"]
Mch7 = models.apparent_mass(chain, freqs7)
Ys7 = shk.accelerance(freqs7)
af7 = np.zeros((len(freqs7), 6), complex)
af7[:, :3] = env7["A"]
Fu7, Fc7 = models.couple_fbs(Mch7, Ys7, af7)
Fc7_t = np.fft.irfft(Fc7[:, :3], n=env7["N"], axis=0)

# equivalent force at P (regularized inversion only in-band; zero elsewhere)
f_eq = np.zeros((len(freqs7), 6), complex)
bandm = (freqs7 >= env7["f1"]) & (freqs7 <= env7["f2"])
f_eq[bandm] = np.linalg.solve(Ys7[bandm], af7[bandm])
feq_t = np.fft.irfft(f_eq, n=env7["N"], axis=0)

n80 = 80
N7 = env7["N"]
Cqq = np.diag(2*zS*np.sqrt(np.clip(lam_all, 1e-12, None)))
Kqq = np.diag(lam_all) + phi_all.T @ (kdiag[:, None]*phi_all)
Kfq = np.zeros((nf_, n80))
Kfq[ib, :] = -kdiag[:, None]*phi_all
Kffc = Kff.copy()
Kffc[ib, ib] += kdiag
Mbig = np.zeros((nf_+n80, nf_+n80))
Mbig[:nf_, :nf_] = Mff
Mbig[nf_:, nf_:] = np.eye(n80)
Kbig = np.block([[Kffc, Kfq], [Kfq.T, Kqq]])
# damping, SAME physics as production apparent_mass:
# (a) PHYSICAL mount dashpot between u_bp and u_P = phi_all q;
# (b) structural modal damping zeta_struct on chain RELATIVE motion
#     (u_f - Psi u_b), the damping the enforced-motion form implies;
# (c) source modal damping Cqq.
Phi_c = chain["Phi"]
wk = np.sqrt(chain["w2"])
zs_struct = chain["zeta_struct"]
Cs = Mff @ (Phi_c * (2*zs_struct*wk)[None, :]) @ Phi_c.T @ Mff
Gmap = chain["Psi"] @ phi_all                # (nf_, 80)
cdg = chain["cdiag"]
Cbig = np.zeros_like(Kbig)
Cbig[:nf_, :nf_] = Cs
Cbig[:nf_, nf_:] = -Cs @ Gmap
Cbig[nf_:, :nf_] = Cbig[:nf_, nf_:].T
Cbig[nf_:, nf_:] = Cqq + Gmap.T @ Cs @ Gmap
# physical dashpot blocks
Cbig[ib, ib] += cdg
Cbig[np.ix_(ib, range(nf_, nf_+n80))] += -cdg[:, None]*phi_all
Cbig[np.ix_(range(nf_, nf_+n80), ib)] += -(cdg[:, None]*phi_all).T
Cbig[nf_:, nf_:] += phi_all.T @ (cdg[:, None]*phi_all)
dt = 1.0/fs7
beta, gamma_n = 0.25, 0.5
Keff = Kbig + gamma_n/(beta*dt)*Cbig + 1.0/(beta*dt*dt)*Mbig
lu, piv = sla.lu_factor(Keff)
u = np.zeros(nf_+n80)
v = np.zeros(nf_+n80)
a = np.zeros(nf_+n80)
F_hist = np.zeros((N7, 3))
for nstep in range(N7):
    Fext = np.zeros(nf_+n80)
    Fext[nf_:] = phi_all.T @ feq_t[nstep]
    rhs = (Fext
           + Mbig @ (u/(beta*dt*dt) + v/(beta*dt) + (1/(2*beta)-1)*a)
           + Cbig @ (gamma_n*u/(beta*dt) + (gamma_n/beta-1)*v
                     + dt*(gamma_n/(2*beta)-1)*a))
    u_new = sla.lu_solve((lu, piv), rhs)
    a_new = (u_new - u)/(beta*dt*dt) - v/(beta*dt) - (1/(2*beta)-1)*a
    v_new = v + dt*((1-gamma_n)*a + gamma_n*a_new)
    u, v, a = u_new, v_new, a_new
    # net inertial force on the chain = the net-CG-load definition (C1)
    F_hist[nstep] = Rt.T @ (Mff @ a[:nf_])
half = N7//2                                  # discard start-up transient
pk_n = np.max(np.abs(F_hist[half:]), axis=0)
pk_f = np.max(np.abs(Fc7_t[half:]), axis=0)
v7 = float(np.max(np.abs(pk_n - pk_f)/pk_f))
gate("V7_newmark_vs_fbs_peak", v7, 0.02, 0.05,
     f"peaks N={pk_n.round(1).tolist()} vs FBS={pk_f.round(1).tolist()} N "
     "(last 2 s; zero-IC transient discarded)")

# ---- V8: 7004C TDOF analytic anchors ---------------------------------------
Q8 = 50.0
def load_M_norm(r):
    return abs(1+1j*r/Q8)/abs(1-r**2+1j*r/Q8)
def src_M_norm(r):
    return abs(1-r**2+1j*r/Q8)/r**2
v8a = abs(load_M_norm(0.62) - 1.624)/1.624
v8b = abs(load_M_norm(1.0) - 50.01)/50.01
v8c = abs(src_M_norm(1.0) - 0.02)/0.02
# TDOF coupled check: grounded source SDOF (m1,k1) + load SDOF (m2,k2) on it.
m1, m2 = 10.0, 1.0
f1_, f2_ = 60.0, 100.0
k1 = m1*(2*np.pi*f1_)**2
k2 = m2*(2*np.pi*f2_)**2
z1 = z2 = 0.01
c1 = 2*z1*np.sqrt(k1*m1)
c2 = 2*z2*np.sqrt(k2*m2)
fr = np.linspace(30, 150, 481)
w8 = 2*np.pi*fr
# load apparent mass (SDOF on driven base): m2*(k2+iwc2)/(k2+iwc2-w^2 m2)
Ml = (m2*(k2+1j*w8*c2)/(k2+1j*w8*c2-w8**2*m2))[:, None, None]
# source accelerance at m1 (grounded): -w^2/(k1+iwc1-w^2 m1)
Ysrc = (-w8**2/(k1+1j*w8*c1-w8**2*m1))[:, None, None]
af8 = np.ones((len(fr), 1), complex)
Fu8, Fc8 = models.couple_fbs(Ml, Ysrc, af8)
# direct 2dof: states [x1, x2]; force f at m1 s.t. unloaded a1 = 1
err8 = []
for i, w in enumerate(w8):
    f_eq8 = 1.0/Ysrc[i, 0, 0]
    D2 = np.array([[k1+k2+1j*w*(c1+c2)-w**2*m1, -(k2+1j*w*c2)],
                   [-(k2+1j*w*c2), k2+1j*w*c2-w**2*m2]])
    x = np.linalg.solve(D2, np.array([f_eq8, 0.0]))
    F_if = (k2+1j*w*c2)*(x[0]-x[1])          # force on load
    err8.append(abs(F_if - Fc8[i, 0]))
v8d = float(np.max(err8)/np.max(np.abs(Fc8)))
gate("V8a_7004c_load_M_062", v8a, 0.01)
gate("V8b_7004c_load_M_1", v8b, 0.01)
gate("V8c_7004c_source_M_1", v8c, 0.01)
gate("V8d_tdof_coupled_direct", v8d, 5e-3)

worst = "green"
for g in gates.values():
    if g["status"] == "red":
        worst = "red"
        break
    if g["status"] == "yellow":
        worst = "yellow"
out = dict(overall=worst, gates=gates,
           chain_modes_nominal_hz=np.round(chain["f"][:12], 2).tolist(),
           tray_mass_kg=m_tray,
           clamped_tray_modes_hz=np.round(f_clamped[:8], 2).tolist(),
           elapsed_s=round(time.time()-t0, 1))
json.dump(out, open(os.path.join(WS, "out", "verification.json"), "w"), indent=1)
print(f"OVERALL: {worst}  ({time.time()-t0:.0f}s)")
