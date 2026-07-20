#!/usr/bin/env python3
"""
Held-out-SENSOR cross-validation (Andrew's question): is it legitimate to LEARN per-mode amplitude/damping
coefficients on the sensors we DO have and propagate to held-out sensors? Yes — this measures exactly that.

For baseline (inherited FEM) and al_rho_lo (best remesh), using their saved matched modes (Phi, pd, kidx) and
MEASURED per-mode freq+damping to place peaks:
  * fit one complex amplitude+phase per mode by ridge-LSQ on OBS channels (a fold's training sensors),
  * predict the HELD-OUT sensors,
  * report median per-channel log|H| correlation on the HELD-OUT sensors only.
K-fold over channels (K=5), averaged; same construction/gain convention as combine_best.honest_corr.

Contrast with the two numbers already on the deck:
  * honest_corr (no amplitude fit, 1 global gain, ALL channels): baseline 0.338, al_rho_lo 0.267   [blind]
  * correlate_all in-sample (fit amplitudes on ALL channels, score ALL channels): al_rho_lo 0.379       [leaky]
This script is the middle, legitimate case: fit on OBS sensors -> predict HO sensors -> corr on HO.
"""
from __future__ import annotations
import json, sys, time
from pathlib import Path
import numpy as np

PSD = Path("/Users/avoss/Downloads/bayesX/Agentic BayesX/artifacts/reports/shocksat_psd_envelope_twin_20260623")
sys.path.insert(0, str(PSD / "code"))
import rescore_sigma as RSC
from modal_multiref import CACHE

HERE = Path(__file__).resolve().parent.parent
OUT = HERE / "out"; OUT.mkdir(exist_ok=True)
RIDGE = 1e-3
t0 = time.time()
def log(m): print(f"[{time.time()-t0:6.1f}s] {m}", flush=True)


def load_measured():
    c = dict(np.load(CACHE / "m_xpos_990x.npz", allow_pickle=True)); c["daq"] = [int(d) for d in c["daq"]]
    daq = RSC.common
    Hdata = np.array([c["H1"][c["daq"].index(d)] for d in daq]).T          # (Nf, Nc)
    w = 2 * np.pi * c["freqs"]
    return w, Hdata


def build_basis(Phi, pd, kidx, w, wr_hz, eta_extra):
    """Per-mode modal-FRF basis B[f,c,k] = -w^2 * Phi[c,k]*pd[k] / den[f,k]  (measured freq+damping in den)."""
    wr = wr_hz * 2 * np.pi
    eta = 2.0 * (eta_extra + 1.0 / (2 * np.pi * wr_hz * RSC.tau))
    den = (1 + 1j * eta)[None, :] * (wr ** 2)[None, :] - (w ** 2)[:, None]  # (Nf, nm)
    return (-(w ** 2)[:, None, None]) * (Phi[None, :, :] * pd[None, None, :]) / den[:, None, :]  # (Nf,Nc,nm)


def _fit(B, Hdata, cols, nm):
    A = B[:, cols, :].reshape(-1, nm); b = Hdata[:, cols].reshape(-1)
    AhA = A.conj().T @ A + RIDGE * np.eye(nm) * np.real(np.trace(A.conj().T @ A)) / nm
    return np.linalg.solve(AhA, A.conj().T @ b)                              # per-mode complex amp


def cv_corr(modes_npz, w, Hdata, K=5, seed=0):
    z = np.load(modes_npz, allow_pickle=True)
    Phi, pd, kidx, ff = z["Phi"], z["pd"], z["kidx"], z["freqs_fem"]
    mfr = RSC.mm["freqs"]; mdp = RSC.mm["damp"] / 100.0
    j = np.array([int(np.argmin(np.abs(mfr - x))) for x in ff])
    B = build_basis(Phi, pd, kidx, w, mfr[j], mdp[j])                        # (Nf,Nc,nm)
    Nc, nm = Phi.shape[0], len(kidx)
    logHd = np.log(np.abs(Hdata) + 1e-30)
    # --- held-out-SENSOR CV: fit on 90% cols, score the held-out 10% ---
    rng = np.random.default_rng(seed); perm = rng.permutation(Nc)
    ho_corrs = []
    for fold in np.array_split(perm, K):
        ho = np.array(sorted(fold)); obs = np.array(sorted(set(range(Nc)) - set(ho.tolist())))
        a = _fit(B, Hdata, obs, nm); Hpred = B[:, ho, :] @ a
        for k in range(len(ho)):
            ho_corrs.append(np.corrcoef(np.log(np.abs(Hpred[:, k]) + 1e-30), logHd[:, ho[k]])[0, 1])
    ho_corrs = np.array(ho_corrs)
    # --- IN-SAMPLE, SAME single-ref setup: fit on ALL cols, score ALL cols (apples-to-apples w/ the CV) ---
    a_all = _fit(B, Hdata, np.arange(Nc), nm); Hall = B @ a_all
    is_corrs = np.array([np.corrcoef(np.log(np.abs(Hall[:, k]) + 1e-30), logHd[:, k])[0, 1] for k in range(Nc)])
    return {"cv_median": round(float(np.median(ho_corrs)), 3), "cv_frac_gt0.5": round(float(np.mean(ho_corrs > 0.5)), 2),
            "insample_same_setup_median": round(float(np.median(is_corrs)), 3), "nm": int(nm)}


def main():
    w, Hdata = load_measured()
    rec = {"deliverable": "held-out-SENSOR cross-validation: fit per-mode amplitude on OBS sensors, predict HO sensors",
           "K_folds": 5, "measured_freq_damping_for_peaks": True}
    for name, npz in [("baseline_inherited", PSD / "out" / "edits" / "baseline" / "modes.npz"),
                      ("al_rho_lo_best_remesh", PSD / "out" / "edits" / "al_rho_lo" / "modes.npz")]:
        r = cv_corr(npz, w, Hdata); rec[name] = r
        log(f"{name}: CV(held-out sensor)={r['cv_median']:.3f}  in-sample(same setup)={r['insample_same_setup_median']:.3f}  nm={r['nm']}")
    rec["comparison_all_FRF_corr"] = {
        "blind_no_ampfit_1gain (combine_best)": {"baseline": 0.338, "al_rho_lo": 0.267},
        "heldout_SENSOR_CV_ampfit (fit 90%->predict 10%)": {"baseline": rec["baseline_inherited"]["cv_median"],
                                                            "al_rho_lo": rec["al_rho_lo_best_remesh"]["cv_median"]},
        "in_sample_same_setup (fit ALL->score ALL, single ref)": {
            "baseline": rec["baseline_inherited"]["insample_same_setup_median"],
            "al_rho_lo": rec["al_rho_lo_best_remesh"]["insample_same_setup_median"]},
        "in_sample_multiref (correlate_all, leaky, DIFFERENT experiment)": {"al_rho_lo": 0.379}}
    (OUT / "heldout_sensor_cv.json").write_text(json.dumps(rec, indent=2))
    print("\n" + json.dumps(rec["comparison_all_FRF_corr"], indent=2))
    print(f"\nDONE in {time.time()-t0:.1f}s -> out/heldout_sensor_cv.json")


if __name__ == "__main__":
    main()
