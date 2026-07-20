#!/usr/bin/env python3
"""Morning diagnosis of the overnight NUTS non-convergence (D10/D11).

Facts established here (out/multimodality_diagnosis.json):
1. DATA-SPACE convergence, PARAMETER-SPACE multimodality: all 4 chains fit
   the 27 survey frequencies equally well (rms log-residual ~3.4-3.5 %,
   median cross-chain predicted-frequency spread ~0.06 %) while their mount
   parameter medians differ wildly -> 0 divergences + R-hat 5-10 = chains in
   different modes of a sloppy ridge, not a sampler pathology.
2. sigma_f posterior ~3.7 % >> injected 0.3 % noise: the sampler honestly
   measured the STRUCTURED model-form discrepancy (off-diagonal mount truth +
   theta_S median-vs-draw gap + reduction residue).
3. FIM at the ACTUAL discrepancy level (sigma=3.7 %): only 2 of 6 mount
   log-stiffness COMBINATIONS exceed the prior precision (k_ry-dominated
   lateral-rocking combo, eig ~97; pure k_tz via the z-bounce, eig ~15;
   k_rz marginal at ~0.74 vs prior 0.76). The 6-axis decomposition is NOT
   identifiable at this floor.
4. Counterfactual: at the injected noise floor alone (sigma=0.3 %) 5 of 6
   combinations would clear the prior -> THE BINDING CONSTRAINT IS
   MODEL-FORM DISCREPANCY, not sensitivity or mode count. (Same wall as the
   predecessor's sigma_f=4.6 % joints finding.)
Reconciliation with the identifiability gate (packet section 7): the gate's
dlnf/dlnk=0.449 statement concerned the OVERALL mount level - which IS
identified (the 2 strong combinations) - not the per-axis decomposition.
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
pairing = json.load(open(os.path.join(OUT, "pairing_coupled.json")))
calib = [p for p in pairing["pairs"] if p["calib_ok"]]
m_idx = np.array([p["anchor_mode"] for p in calib])
f_data = np.array([p["f_data"] for p in calib])
B_fix, B_mount, B_tray = rom["B_fix"], rom["B_mount"], rom["B_tray"]
Qa = rom[f"anchorQ_x{pairing['anchor_mult']}"]
NAMES = ["k_tx", "k_ty", "k_tz", "k_rx", "k_ry", "k_rz"]


def freqs(theta_m, theta_T=np.ones(5)):
    K = (B_fix + np.einsum("j,jab->ab", theta_m, B_mount)
         + np.einsum("g,gab->ab", theta_T, B_tray))
    lam, Q = np.linalg.eigh(K)
    f = np.sqrt(np.clip(lam, 1e-12, None))/(2*np.pi)
    k = np.argmax(np.abs(Qa.T @ Q)[m_idx, :], axis=1)
    return f[k]


out = {}
# (1) per-chain agreement
for tag in ("base", "remedy"):
    z = np.load(os.path.join(OUT, f"nuts_mount_{tag}_samples.npz"))
    cv = json.load(open(os.path.join(OUT, f"convergence_mount_{tag}.json")))
    nd, nc = cv["settings"]["ndraw"], cv["settings"]["chains"]
    tm = z["theta_m"].reshape(nc, nd, 6)
    tt = z["theta_T"].reshape(nc, nd, 5)
    rows, fp = [], []
    for c in range(nc):
        med_m = np.median(tm[c], 0)
        fpc = freqs(med_m, np.median(tt[c], 0))
        fp.append(fpc)
        res = np.abs(np.log(fpc/f_data))
        rows.append(dict(chain=c, theta_m_median=np.round(med_m, 3).tolist(),
                         rms_log_residual_pct=round(100*float(np.sqrt((res**2).mean())), 2)))
    fp = np.array(fp)
    spread = (fp.max(0)-fp.min(0))/fp.mean(0)
    out[tag] = dict(worst_rhat=cv["worst_rhat"], min_ess=cv["min_ess"],
                    divergences=cv["divergences"], per_chain=rows,
                    cross_chain_pred_freq_spread_pct=dict(
                        max=round(100*float(spread.max()), 2),
                        median=round(100*float(np.median(spread)), 3)))

# (2) FIM combination analysis at the actual and injected floors
th0 = np.ones(6)
f0 = freqs(th0)
J = np.zeros((len(f_data), 6))
h = 1e-4
for j in range(6):
    tp = th0.copy()
    tp[j] = np.exp(h)
    J[:, j] = (np.log(freqs(tp)) - np.log(f0))/h
prior_prec = 1/1.15**2
fim = {}
for label, sig in (("actual_discrepancy_3.7pct", 0.037),
                   ("injected_noise_only_0.3pct", 0.003)):
    ev, evec = np.linalg.eigh(J.T @ J / sig**2)
    fim[label] = dict(
        sigma=sig, eigenvalues=np.round(ev, 3).tolist(),
        prior_precision=round(prior_prec, 3),
        n_identifiable_combos=int(np.sum(ev > prior_prec)),
        eigvectors_by_combo=[
            dict(eig=round(float(ev[i]), 2),
                 vec={n: round(float(evec[j, i]), 2)
                      for j, n in enumerate(NAMES) if abs(evec[j, i]) > 0.1})
            for i in range(6)])
out["fim_combinations"] = fim
out["verdict"] = (
    "Multimodality is GENUINE under-identification of the 6-axis mount "
    "decomposition at the realized model-form discrepancy floor (~3.7 %), "
    "not a sampler bug: chains agree in data space (0.06 % median predicted-"
    "frequency spread) and disagree in parameter space. Only 2 stiffness "
    "COMBINATIONS are identified (k_ry-dominated rocking, k_tz bounce); at "
    "the 0.3 % injected-noise floor 5/6 would be -> the binding constraint "
    "is model-form discrepancy (cross-confirms the predecessor's joints "
    "finding). The packet-7 gate statement (overall mount level "
    "identifiable) HOLDS for those combinations; the per-axis claim does "
    "not. Pre-test lever refined: add observables that break the lateral/"
    "rocking symmetry (mode shapes, FRF amplitudes, interface force gauges) "
    "or reduce discrepancy; frequencies alone cannot split the axes.")
json.dump(out, open(os.path.join(OUT, "multimodality_diagnosis.json"), "w"),
          indent=1)
print(json.dumps({k: v for k, v in out.items() if k == "verdict"}, indent=1))
print("written out/multimodality_diagnosis.json")
