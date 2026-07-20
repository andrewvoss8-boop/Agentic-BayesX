#!/usr/bin/env python3
"""Response-limit PROXY QOI (D7; Andrew's vision note 2026-06-10 §2.2).

Industry rarely force-limits; it response-limits. Stand-in deliverable: find
the 1-2 tray accelerometer channels whose response best tracks the net-CG
interface force at the force-driving coupled modes, and report the scale
alpha (N per m/s^2) that converts a force limit into a response limit on
those channels.

For each candidate channel c and axis d (coupled time-history, per draw):
  alpha_cd = <F_d(t) a_c(t)> / <a_c(t)^2>   (least-squares scale)
  rho_cd   = corr(F_d, a_c)                  (quality of the proxy)
computed on the full-band record AND on a band-pass around the bounce/rock
cluster (the force-driving modes). Robustness = spread of alpha/rho over
joint parameter draws (theta_S posterior x theta_T prior x mount prior).

Physics note: F_d = m_tray * a_CG,d EXACTLY (net inertial load), so the ideal
proxy is the mass-weighted average acceleration; a single real accel deviates
through local elastic motion. rho quantifies exactly that degradation.

Output: out/response_limit_proxy.json. HYPOTHETICAL methods demo.
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
import run_qoi  # noqa: E402

t0 = time.time()
N_DRAWS = 32
BP_LO, BP_HI = 60.0, 130.0      # band around the bounce/rock cluster


def log(m):
    print(f"[{time.time()-t0:6.1f}s] {m}", flush=True)


def channels(tray):
    """Candidate accel channels: (name, free-dof index, axis)."""
    meta = tray["meta"]
    xs, ys, nid = meta["xs"], meta["ys"], meta["nid"]
    free = tray["free"]

    def fidx(node, comp):
        gd = 6*node + comp
        i = np.searchsorted(free, gd)
        assert free[i] == gd
        return int(i)

    ixc = int(np.argmin(np.abs(xs)))
    iyc = int(np.argmin(np.abs(ys)))
    locs = {
        "tray_center": nid[("t", ixc, iyc)],
        "tray_corner": nid[("t", 0, 0)],
        "tray_midedge": nid[("t", len(xs)-1, iyc)],
    }
    # apexes: tray nodes at the bipod apex coordinates
    import spec
    for name, a in spec.apex_m().items():
        i = int(np.where(np.isclose(xs, a[0]))[0][0])
        j = int(np.where(np.isclose(ys, a[1]))[0][0])
        locs[f"apex_{name}"] = nid[("t", i, j)]
    ch = []
    for nm, node in locs.items():
        for comp, ax in zip(range(3), "xyz"):
            ch.append((f"{nm}_{ax}", fidx(node, comp), comp))
    for comp, ax in zip(range(3), "xyz"):
        ch.append((f"base_point_{ax}", int(tray["ibase"][comp]), comp))
    return ch


def draw_response(tray, shk, chain, env, bidx, theta_S, ch):
    """Coupled F(t) (N,3) and channel accels (N, nch) for one draw/seed."""
    freqs = env["freqs"]
    fb = freqs[bidx]
    Mch, T_cpl, Ys = run_qoi.transfer_matrices(chain, shk, fb, theta_S)
    af = np.zeros((len(bidx), 6), complex)
    af[:, :3] = env["A"][bidx]
    Fc = np.einsum("fij,fj->fi", T_cpl, af)
    a_b = af - np.einsum("fij,fj->fi", Ys, Fc)   # actual interface accel
    # chain response: a_f = [Psi + Phi D^-1 w^2 Gamma] a_b  (Woodbury pieces)
    w = 2*np.pi*fb
    wk2 = chain["w2"][:, None]
    wk = np.sqrt(chain["w2"])[:, None]
    zs = chain["zeta_struct"]
    D0i = 1.0/(wk2 - w**2 + 2j*(zs+1e-9)*wk*w)   # (nm,nf)
    G = chain["Gamma"]
    U = chain["U"]
    c = chain["cdiag"]
    UtDU = np.einsum("kf,ki,kj->fij", D0i, U, U)
    inner = np.diag(1.0/c)[None]/(1j*w)[:, None, None] + UtDU
    UtDG = np.einsum("kf,ki,kj->fij", D0i, U, G)
    X = np.linalg.solve(inner, UtDG)             # (nf,6,6)
    # eta(w) = D^-1 w^2 G a_b  ->  channel accel rows
    nch = len(ch)
    a_ch = np.zeros((len(fb), nch), complex)
    Psi = chain["Psi"]
    Phi = chain["Phi"]
    for ci, (_, fi, _) in enumerate(ch):
        phc = Phi[fi, :]                          # (nm,)
        t1 = np.einsum("k,kf,ki->fi", phc, D0i, G)        # phc D0i G
        t2 = np.einsum("k,kf,ki->fi", phc, D0i, U)        # phc D0i U
        row = t1 - np.einsum("fi,fij->fj", t2, X)         # (nf,6)
        s_c = Psi[fi, :][None, :] + (w**2)[:, None]*row
        a_ch[:, ci] = np.einsum("fj,fj->f", s_c, a_b)
    # to time domain
    N = env["N"]
    Fs = np.zeros((len(freqs), 3), complex)
    Fs[bidx] = Fc[:, :3]
    Ft = np.fft.irfft(Fs, n=N, axis=0)
    As = np.zeros((len(freqs), nch), complex)
    As[bidx] = a_ch
    At = np.fft.irfft(As, n=N, axis=0)
    # band-passed versions (force-driving cluster)
    bp = (freqs >= BP_LO) & (freqs <= BP_HI)
    Fsb = np.where(bp[:, None], Fs, 0)
    Asb = np.where(bp[:, None], As, 0)
    Ftb = np.fft.irfft(Fsb, n=N, axis=0)
    Atb = np.fft.irfft(Asb, n=N, axis=0)
    return Ft, At, Ftb, Atb


def main():
    outp = os.path.join(WS, "out", "response_limit_proxy.json")
    if os.path.exists(outp):
        log("response_limit_proxy.json exists, skip (delete to rerun)")
        return
    tray = models.build_tray_chain()
    shk = models.ShockSatInterface()
    thetaS_samp, _ = run_qoi.load_posterior()
    theta_med = np.median(thetaS_samp, axis=0)
    ch = channels(tray)
    env = methods.synth_input(seed=0)
    bidx = run_qoi.band_idx(env)
    m_tray = tray["meta"]["mass_total"]

    rows = {nm: dict(alpha=[[] for _ in range(3)], rho=[[] for _ in range(3)],
                     rho_bp=[[] for _ in range(3)]) for nm, _, _ in ch}
    for di in range(N_DRAWS):
        if di == 0:
            tS, tT, km = theta_med, None, None
        else:
            rng = np.random.default_rng([20260610, 99, di])
            tS, tT, km = run_qoi.draw_params(rng, thetaS_samp, "joint")
        chain = models.chain_modal(tray, tT, km)
        Ft, At, Ftb, Atb = draw_response(tray, shk, chain, env, bidx, tS, ch)
        for ci, (nm, _, comp) in enumerate(ch):
            a = At[:, ci]
            ab = Atb[:, ci]
            for d in range(3):
                F = Ft[:, d]
                denom = float(a @ a)
                alpha = float(F @ a)/denom if denom > 0 else 0.0
                rho = float(F @ a)/np.sqrt(float(F @ F)*denom) if denom > 0 else 0.0
                Fb = Ftb[:, d]
                db = float(ab @ ab)
                rho_b = float(Fb @ ab)/np.sqrt(float(Fb @ Fb)*db) if db > 0 else 0.0
                rows[nm]["alpha"][d].append(alpha)
                rows[nm]["rho"][d].append(rho)
                rows[nm]["rho_bp"][d].append(rho_b)
        if di % 8 == 0:
            log(f"draw {di}/{N_DRAWS}")

    table = []
    for nm, _, comp in ch:
        r = rows[nm]
        for d, ax in zip(range(3), "xyz"):
            al = np.array(r["alpha"][d])
            rh = np.abs(r["rho"][d])
            rb = np.abs(r["rho_bp"][d])
            table.append(dict(
                channel=nm, force_axis=f"F{ax}",
                alpha_med_N_per_ms2=round(float(np.median(al)), 3),
                alpha_cv=round(float(np.std(al)/max(abs(np.median(al)), 1e-12)), 3),
                rho_med=round(float(np.median(rh)), 4),
                rho_worst=round(float(np.min(rh)), 4),
                rho_bp_med=round(float(np.median(rb)), 4),
                rho_bp_worst=round(float(np.min(rb)), 4)))
    # top-2 per axis by (band-passed rho worst-case, then full rho)
    picks = {}
    for d, ax in zip(range(3), "xyz"):
        cand = [t for t in table if t["force_axis"] == f"F{ax}"]
        cand.sort(key=lambda t: (t["rho_bp_worst"], t["rho_med"]), reverse=True)
        picks[f"F{ax}"] = cand[:2]
    out = dict(
        label=("HYPOTHETICAL methods demo - response-limit proxy for the "
               "net-CG interface-force limit (vision 2.2 / D7)"),
        m_tray_kg=m_tray,
        ideal_proxy_note=("F_d = m_tray * a_CG,d exactly; a perfect proxy "
                          "would be the mass-weighted average accel with "
                          "alpha = m_tray = %.3f kg" % m_tray),
        band_pass_hz=[BP_LO, BP_HI],
        n_draws=N_DRAWS, seed=0,
        channels=table, picks=picks,
        usage=("response limit on channel c [m/s^2] = F_limit,d [N] / "
               "alpha_cd; trustworthy only where rho ~ 1 and alpha_cv small "
               "across draws"))
    json.dump(out, open(os.path.join(WS, "out", "response_limit_proxy.json"),
                        "w"), indent=1)
    log("done")
    for ax in "xyz":
        p = picks[f"F{ax}"][0]
        log(f"F{ax}: best {p['channel']} rho_bp_worst={p['rho_bp_worst']} "
            f"alpha={p['alpha_med_N_per_ms2']} N/(m/s^2)")


if __name__ == "__main__":
    main()
