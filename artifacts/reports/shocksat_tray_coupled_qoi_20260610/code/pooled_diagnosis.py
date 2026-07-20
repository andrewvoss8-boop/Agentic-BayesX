#!/usr/bin/env python3
"""Diagnosis of the POOLED-mount sampler runs (D15/D16) -> out/pooled_diagnosis.json

Facts established:
1. Convergence ladder matches the FIM ordering: 6-param R-hat 5.03 ->
   p3b 1.52 -> p2 1.24 (all 4x(1000+1000) d8, 0 divergences everywhere).
2. Even p2 (t_all, r_all) misses the gate. Per-variable: worst R-hat moves to
   theta_T/t_all mixing; chains overlap in range (not separated modes).
3. The dominant ridge is t_all <-> r_all (corr(log) ~ -0.74): the rocking
   modes price a COMBINATION of lateral translation + rotation stiffness
   (CG-offset rocking), so the pair trades.
4. t_all samples span the whole prior (0.05-39): STIFF-SIDE SATURATION --
   once the mount is stiffer than the tray (sweep: f1 pins at 84.8 Hz above
   ~5x nominal), frequencies stop moving and the likelihood goes flat ->
   one-sided identifiability; the upper tail is prior-dominated.
5. LOCAL-vs-GLOBAL lesson: the prior-whitened JOINT (mount+tray) FIM at
   nominal says p2 is fine (2 informed combos, tray params cleanly
   prior-bound) -- the saturation/banana is invisible to a local Jacobian.
   This is exactly why the D12 gate names profile-likelihood/posterior
   analysis as the companion to FIM.
"""
import json
import os
import sys
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
WS = os.path.abspath(os.path.join(HERE, ".."))
OUT = os.path.join(WS, "out")
sys.path.insert(0, HERE)

rom = np.load(os.path.join(OUT, "coupled_rom.npz"))
pr = json.load(open(os.path.join(OUT, "pairing_coupled.json")))
calib = [p for p in pr["pairs"] if p["calib_ok"]]
m_idx = np.array([p["anchor_mode"] for p in calib])
Bf, Bm, Bt = rom["B_fix"], rom["B_mount"], rom["B_tray"]
Qa = rom[f"anchorQ_x{pr['anchor_mult']}"]
NAMES = ["t_all", "r_all", "tray_E", "strut_EA", "strut_EI",
         "joint_ax", "joint_lat"]


def freqs(th6, thT):
    K = Bf + np.einsum("j,jab->ab", th6, Bm) + np.einsum("g,gab->ab", thT, Bt)
    lam, Q = np.linalg.eigh(K)
    f = np.sqrt(np.clip(lam, 1e-12, None))/(2*np.pi)
    return f[np.argmax(np.abs(Qa.T @ Q)[m_idx, :], axis=1)]


def joint_p2_fim(sig=0.037):
    h = 1e-4
    f0 = freqs(np.ones(6), np.ones(5))
    J = np.zeros((len(m_idx), 11))
    for j in range(6):
        t = np.ones(6); t[j] = np.exp(h)
        J[:, j] = (np.log(freqs(t, np.ones(5))) - np.log(f0))/h
    for g in range(5):
        t = np.ones(5); t[g] = np.exp(h)
        J[:, 6+g] = (np.log(freqs(np.ones(6), t)) - np.log(f0))/h
    Bp = np.zeros((11, 7))
    Bp[0:3, 0] = 1; Bp[3:6, 1] = 1
    for g in range(5):
        Bp[6+g, 2+g] = 1
    Jp = J @ Bp
    prior_prec = np.array([1/1.15**2]*2 + [1/0.25**2]*5)
    W = np.diag(1/np.sqrt(prior_prec))
    ev, evec = np.linalg.eigh(W @ (Jp.T @ Jp/sig**2) @ W)
    return [dict(eig=round(float(ev[i]), 2),
                 mix={n: round(float(evec[j, i]), 2)
                      for j, n in enumerate(NAMES) if abs(evec[j, i]) > 0.25})
            for i in range(7)]


def sampler_facts():
    out = {}
    for tag in ("p2", "p3b"):
        cv = json.load(open(os.path.join(OUT, f"convergence_pooled_{tag}.json")))
        z = np.load(os.path.join(OUT, f"nuts_pooled_{tag}_samples.npz"))
        tp = z["theta_pool"]
        row = dict(worst_rhat=round(cv["worst_rhat"], 3),
                   min_ess=round(cv["min_ess"], 1),
                   divergences=cv["divergences"],
                   per_variable={k: round(v["r_hat_max"], 3)
                                 for k, v in cv["per_variable"].items()})
        if tag == "p2":
            lt = np.log(tp[:, 0])
            row["corr_log_tall_rall"] = round(
                float(np.corrcoef(lt, np.log(tp[:, 1]))[0, 1]), 3)
            tt = z["theta_T"]
            row["corr_log_tall_tray"] = {
                n: round(float(np.corrcoef(lt, np.log(tt[:, i]))[0, 1]), 3)
                for i, n in enumerate(["tray_E", "strut_EA", "strut_EI",
                                       "joint_ax", "joint_lat"])}
            row["t_all_sample_range"] = [round(float(tp[:, 0].min()), 2),
                                         round(float(tp[:, 0].max()), 2)]
        out[tag] = row
    # remedy (if finished)
    prem = os.path.join(OUT, "convergence_pooled_p2r.json")
    if os.path.exists(prem):
        cv = json.load(open(prem))
        out["p2r_remedy_2000x2000_d9"] = dict(
            worst_rhat=round(cv["worst_rhat"], 3),
            min_ess=round(cv["min_ess"], 1), divergences=cv["divergences"],
            gate_pass=cv["gate_pass"])
    return out


if __name__ == "__main__":
    out = dict(verdict=__doc__.strip(),
               joint_p2_fim_prior_whitened=joint_p2_fim(),
               sampler=sampler_facts())
    json.dump(out, open(os.path.join(OUT, "pooled_diagnosis.json"), "w"),
              indent=1)
    print("written out/pooled_diagnosis.json")
    print(json.dumps(out["sampler"], indent=1))
