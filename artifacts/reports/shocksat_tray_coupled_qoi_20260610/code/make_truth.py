#!/usr/bin/env python3
"""O2: synthetic TRUTH + mounted-config modal survey data (D10, A21-A28).

Truth = FULL (unreduced) coupled model at parameters drawn ONCE (fixed seeds)
from the honest priors, with an UNMODELED feature: 6x6 mount stiffness with
translation-rotation off-diagonal coupling (rho=0.15 on (tx,ry),(ty,rx),
0.05 on (tx,ty)) that the diagonal-CBUSH inference model cannot represent
-> structured model-form discrepancy. theta_S_true = a predecessor-posterior
DRAW (the inference fixes theta_S at the posterior MEDIAN; A24).

Survey data: coupled modal frequencies <= 240 Hz with 0.3 % relative noise
(one realization) + mode shapes at the obs channels with 2 % noise (used for
PAIRING only). Pairing: best mount-grid anchor by total MAC ("engineer's
coarse pre-match"), Hungarian unique assignment, calib filter MAC >= 0.5 and
|df| <= 12 %.

Outputs:
  out/truth_lock.json   (truth params + SHA of the params payload — the NUTS
                         script never reads this; structural self-blinding A28)
  out/survey_data.npz   (freqs, shapes, noise levels — NO truth params)
  out/pairing_coupled.json
"""
import hashlib
import json
import os
import sys
import time
import numpy as np
import scipy.linalg as sla
from scipy.optimize import linear_sum_assignment

HERE = os.path.dirname(os.path.abspath(__file__))
WS = os.path.abspath(os.path.join(HERE, ".."))
sys.path.insert(0, HERE)
import models  # noqa: E402
import run_qoi  # noqa: E402
import build_coupled_rom as bcr  # noqa: E402

SEED_TRUTH = 77001
F_DATA = 240.0
NOISE_F = 0.003
NOISE_SHAPE = 0.02
SIGMA = bcr.SIGMA

t0 = time.time()


def log(m):
    print(f"[{time.time()-t0:6.1f}s] {m}", flush=True)


def main():
    if os.path.exists(os.path.join(WS, "out", "survey_data.npz")):
        log("survey_data.npz exists, skip")
        return
    rng = np.random.default_rng(SEED_TRUTH)
    tray = models.build_tray_chain()
    shk = models.ShockSatInterface()
    thetaS_samp, gn = run_qoi.load_posterior()

    # ---- truth parameter draws (fixed seed; documented in lock)
    row = int(rng.integers(len(thetaS_samp)))
    thS_true = thetaS_samp[row]
    thT_true = {g: float(v) for g, v in zip(
        models.TRAY_PARAMS, np.exp(rng.normal(0, 0.25, 5)))}
    knom = np.array([models.MOUNT_NOMINAL[p] for p in models.MOUNT_PARAMS])
    mult_true = np.exp(rng.normal(0, 1.15, 6))
    kdiag_true = knom*mult_true
    Km = np.diag(kdiag_true)
    # off-diagonal translation-rotation coupling (A21)
    for (a, b, rho) in [(0, 4, 0.15), (1, 3, 0.15), (0, 1, 0.05)]:
        Km[a, b] = Km[b, a] = rho*np.sqrt(kdiag_true[a]*kdiag_true[b])
    ev = np.linalg.eigvalsh(Km)
    assert ev.min() > 0, "truth mount K not SPD"
    log(f"truth mount multipliers: {np.round(mult_true, 3).tolist()}")
    log(f"truth tray theta: { {k: round(v,3) for k,v in thT_true.items()} }")

    # ---- FULL coupled truth model
    K_el = shk.A_fix + np.einsum("g,gij->ij", thS_true, shk.A)
    phi_all = np.hstack([shk.B_rbm, shk.B_el])
    nf_ = tray["M"].shape[0]
    n = nf_ + 80
    ib = tray["ibase"]
    M = np.zeros((n, n))
    M[:nf_, :nf_] = tray["M"]
    M[nf_:, nf_:] = np.eye(80)
    K = np.zeros((n, n))
    K[:nf_, :nf_] = tray["Kfix"]
    for g in models.TRAY_PARAMS:
        K[:nf_, :nf_] += thT_true[g]*tray["Kg"][g]
    K[nf_:nf_+6, nf_:nf_+6] = np.diag(shk.lam_rbm)
    K[nf_+6:, nf_+6:] = K_el
    Vm = np.zeros((6, n))
    for j in range(6):
        Vm[j, ib[j]] = 1.0
        Vm[j, nf_:] = -phi_all[j, :]
    K += Vm.T @ Km @ Vm

    mu, V = sla.eigh(M, K + SIGMA*M)
    order = np.argsort(mu)[::-1]
    mu, V = mu[order], V[:, order]
    good = mu > 1e-12*mu.max()
    mu, V = mu[good], V[:, good]
    w2 = 1.0/mu - SIGMA
    keep = (w2 > (2*np.pi*5.0)**2) & (w2 < (2*np.pi*F_DATA)**2)
    f_true = np.sqrt(w2[keep])/(2*np.pi)
    Phi = (V/np.sqrt(mu)[None, :])[:, keep]
    log(f"truth: {len(f_true)} coupled modes 5-{F_DATA} Hz; "
        f"first 8: {np.round(f_true[:8],1).tolist()}")

    # ---- observation shapes (same channels as the ROM's obs rows)
    rom = np.load(os.path.join(WS, "out", "coupled_rom.npz"))
    obs_names = [str(s) for s in rom["obs_names"]]
    ch = bcr.tray_obs_channels(tray)
    nch = len(ch)
    O = np.zeros((nch+12, n))
    for ci, (nm, fi, comp) in enumerate(ch):
        O[ci, fi] = 1.0
    shk_rows, shk_gids = bcr.shocksat_obs_rows(shk)
    O[nch:, nf_:] = shk_rows
    shapes_true = O @ Phi                                # (nobs, nm)

    # ---- noisy survey realization
    f_data = f_true*(1.0 + rng.normal(0, NOISE_F, len(f_true)))
    snorm = np.linalg.norm(shapes_true, axis=0, keepdims=True)
    shapes_data = shapes_true + rng.normal(
        0, NOISE_SHAPE, shapes_true.shape)*snorm

    # ---- pairing against the best mount-grid anchor (A27)
    nb = int(rom["nb"])
    obs_rows = rom["obs_rows"]                           # (nobs, nb)
    best = None
    for mult in bcr.MOUNT_GRID:
        Q = rom[f"anchorQ_x{mult}"]
        Bf = rom["B_fix"]
        Kr = Bf.copy()
        for j in range(6):
            Kr += mult*rom["B_mount"][j]
        Kr += rom["B_tray"].sum(0)
        lam = np.linalg.eigvalsh(Kr)
        fA = np.sqrt(np.clip(lam, 1e-12, None))/(2*np.pi)
        shA = obs_rows @ Q                               # (nobs, nb)
        sel = (fA > 5.0) & (fA < F_DATA*1.3)
        idxA = np.where(sel)[0]
        # MAC matrix data-modes x anchor-modes
        a = shapes_data/np.linalg.norm(shapes_data, axis=0, keepdims=True)
        b = shA[:, idxA]/np.linalg.norm(shA[:, idxA], axis=0, keepdims=True)
        MAC = (a.T @ b)**2
        # frequency penalty
        df = np.abs(np.log(f_data[:, None]/fA[idxA][None, :]))
        cost = -MAC + 2.0*df
        ri, ci = linear_sum_assignment(cost)
        total = MAC[ri, ci].sum()
        if best is None or total > best["total"]:
            best = dict(mult=mult, total=float(total), ri=ri, ci=ci,
                        idxA=idxA, fA=fA, MAC=MAC)
    mult_anchor = best["mult"]
    log(f"pairing anchor = x{mult_anchor} (total MAC {best['total']:.2f})")
    pairs = []
    for r_, c_ in zip(best["ri"], best["ci"]):
        m_idx = int(best["idxA"][c_])
        mac = float(best["MAC"][r_, c_])
        fa = float(best["fA"][m_idx])
        dfp = 100*abs(f_data[r_]/fa - 1)
        ok = bool(mac >= 0.5 and dfp <= 12.0)
        pairs.append(dict(data_mode=int(r_), f_data=float(f_data[r_]),
                          anchor_mode=m_idx, f_anchor=fa, mac=round(mac, 3),
                          df_pct=round(dfp, 2), calib_ok=ok))
    n_calib = sum(p["calib_ok"] for p in pairs)
    log(f"pairs: {len(pairs)}; calib_ok: {n_calib}")
    assert n_calib >= 8, f"only {n_calib} calib-ok pairs - aborting (D10)"

    # ---- write artifacts (data file has NO truth params)
    np.savez_compressed(
        os.path.join(WS, "out", "survey_data.npz"),
        f_data=f_data, shapes_data=shapes_data,
        obs_names=np.array(obs_names), noise_f=NOISE_F,
        noise_shape=NOISE_SHAPE, f_max=F_DATA,
        label="SYNTHETIC mounted-config modal survey (D10); truth in "
              "truth_lock.json (not read by the sampler)")
    json.dump(dict(anchor_mult=mult_anchor, pairs=pairs, n_calib=n_calib,
                   rule="MAC>=0.5 & |df|<=12% & Hungarian-unique (A27)"),
              open(os.path.join(WS, "out", "pairing_coupled.json"), "w"),
              indent=1)
    payload = dict(
        seed=SEED_TRUTH, theta_S_row=row,
        theta_S_true={g: float(v) for g, v in zip(gn, thS_true)},
        theta_T_true=thT_true,
        mount_mult_true=mult_true.tolist(),
        mount_kdiag_true=kdiag_true.tolist(),
        mount_K_offdiag=dict(tx_ry=0.15, ty_rx=0.15, tx_ty=0.05,
                             form="rho*sqrt(ki*kj)"),
        mount_K_full=Km.tolist(),
        f_true=f_true.tolist())
    blob = json.dumps(payload, sort_keys=True).encode()
    json.dump(dict(sha256=hashlib.sha256(blob).hexdigest(), payload=payload,
                   note="NOT read by run_nuts_mount.py (A28 structural "
                        "self-blinding); revealed in posterior_qoi.py"),
              open(os.path.join(WS, "out", "truth_lock.json"), "w"), indent=1)
    log("survey_data + truth_lock + pairing written")


if __name__ == "__main__":
    main()
