#!/usr/bin/env python3
"""Independent recompute of the netCG 3*GRMS QOI from saved posterior draws, scored against the
SEALED CLEAN truth netCG (scoring_key.npz clean_netcg_3grms_g), for both posterior variants.
Mirrors blind3_qoi propagation: parameter + new-build (aleatory) + flight (aleatory)."""
import sys, numpy as np, json
from pathlib import Path
sys.path.insert(0, "runs/round3/opus48/code")
import jax; jax.config.update("jax_enable_x64", True)
import jax.numpy as jnp
import blind3_model as bm

REP = Path("runs/round3/opus48/report")
SEALED = Path("runs/round3/codex_truth/sealed_truth")

obs = bm.load_observations()
M_src6, m_dome, lf = bm.source_rigid_from_asymptote(obs)
m_load = obs["load_mass"]; g0 = obs["g0"]
m_source_z = float(M_src6[2] + m_dome)
print("m_source_z=%.2f  m_load=%.1f  f->0 rigid limit = %.4f" %
      (m_source_z, m_load, m_load/(m_source_z+m_load)))

sk = np.load(SEALED / "scoring_key.npz")
clean = sk["clean_netcg_3grms_g"]           # (8,11)
clean_all = clean.ravel()
clean_train = clean[:6].ravel()
clean_held = clean[6:].ravel()
print("SEALED clean netCG: all min/mean/max = %.3f / %.3f / %.3f" %
      (clean_all.min(), clean_all.mean(), clean_all.max()))

fq = np.geomspace(5.0, 300.0, 500); fqj = jnp.asarray(fq)
flight = np.stack([np.interp(fq, obs["f"], obs["flight_force"][k]) for k in range(obs["flight_force"].shape[0])])
NSUB = 400

def propagate(npz):
    P = np.load(REP / npz)
    k_pop = np.exp(P["log_k_pop"]); f_dome = P["f_dome"]; sb = P["sigma_build"]
    d0 = P["d0"] if "d0" in P.files else np.zeros((len(k_pop), 6))
    nd = len(k_pop); idx = np.linspace(0, nd-1, min(NSUB, nd)).astype(int)
    rng = np.random.default_rng(11)
    grms = []
    for i in idx:
        zb = rng.standard_normal()
        k = k_pop[i]*np.exp(sb[i]*zb)*np.exp(d0[i])
        MLz, MSz = bm.netcg_transfer_z(jnp.asarray(k), float(f_dome[i]), M_src6, m_dome, fqj)
        MLz = np.asarray(MLz); MSz = np.asarray(MSz)
        H = MLz/((MSz+MLz)*m_load*g0)
        Hmag2 = np.abs(H)**2
        for kf in range(flight.shape[0]):
            grms.append(3.0*np.sqrt(np.trapz(Hmag2*flight[kf], fq)))
    return np.array(grms)

def score(grms, target, label):
    qp = np.percentile(grms, [0.5, 2.5, 50, 97.5, 99.5])
    cov95 = float(np.mean((target>=qp[1])&(target<=qp[3])))
    cov99 = float(np.mean((target>=qp[0])&(target<=qp[4])))
    bias = float(np.median(grms)/np.mean(target))
    print(f"  [{label}] pred p50 {qp[2]:.3f} g  95%CI [{qp[1]:.3f},{qp[3]:.3f}]  99%CI [{qp[0]:.3f},{qp[4]:.3f}]")
    print(f"  [{label}] bias {bias:.3f}x  cov95 {cov95:.3f}  cov99 {cov99:.3f}  (target mean {target.mean():.3f})")
    return dict(p50=qp[2], ci95=[qp[1],qp[3]], ci99=[qp[0],qp[4]], bias=bias, cov95=cov95, cov99=cov99)

for npz, tag in [("blind3_posterior.npz","WITH-d"), ("blind3_posterior_nodisc.npz","WITHOUT-d")]:
    grms = propagate(npz)
    print(f"\n=== {tag} netCG vs SEALED CLEAN truth ===")
    score(grms, clean_all, "vs clean ALL builds")
    score(grms, clean_held, "vs clean HELD-OUT builds 6,7")
