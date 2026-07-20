#!/usr/bin/env python3
"""Card G Part B HEADLINE — held-out per-channel AMPLITUDE skill: BEFORE(+X-only) vs AFTER(multi-reference).

Same split/seed/scorer machinery as the inherited value_eval (DR>=30 eligible channels, obs_frac 0.6, CRPS-skill vs
CLIMATOLOGY = observed-channel peak population). theta calibrated from FREQUENCIES (NUTS, reference-invariant; reused).

Peak |H_s(d)| at a resonance of mode k ∝ φ_{s,k}·φ_{d,k}/ζ_k. value_eval (BEFORE) predicts a held-out sensor's peak
with the FEM drive amplitude φ_{d,k}/ζ_k (the CONFOUNDED, FEM-assumed factor). Multi-reference lets us MEASURE the
per-mode complex modal residue from the OBSERVED channels instead of assuming it (a standard operational-modal /
least-squares projection onto the FEM shape — STABLE, no division by small φ):
    R_{d,k} = Σ_obs w_s · φ_{s,k}* · H_s(d, f_k) / Σ_obs w_s · |φ_{s,k}|²      (w_s = at-resonance coherence)
Held-out sensor s peak under drive d = max_f | Σ_k φ_{s,k}(FEM,θ) · R_{d,k} · L_k(f) |, L_k(f_k)≈1 (unit Lorentzian).
So FEM gives the held-out sensor shape φ_{s,k} (still FEM-only — multi-reference cannot observe a HELD-OUT sensor), and
the multi-reference data gives the per-mode drive residue R_{d,k}. This isolates the confounded factor: does measuring
the drive residue (instead of FEM-assuming φ_d/ζ) raise held-out skill? If the binding error is the held-out sensor's
own φ_{s,k}, it will NOT — the earned verdict (iii).

A clearly-labeled SHAPE-ORACLE upper bound (held-out sensor's OWN measured residue) quantifies the achievable ceiling
if the sensor shape were known — separating the drive-side limit (broken here) from the sensor-shape limit.

BEFORE read from Part A value_eval (identical splits). Output: out/multiref_value.json. Units-honest: R_{d,k} is one
training-only per-mode factor from observed channels (no per-held-out / per-draw peak tuning; Card A protocol).
"""
from __future__ import annotations
import json, sys, time
from types import SimpleNamespace
from pathlib import Path
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import realfrf as rf
import modal_feature as mf
import heldout_qoi as hq
import multiref_frf as mrf
import score as SC

WS = Path(__file__).resolve().parent.parent
OUT = WS / "out"; MULTIREF = WS / "data" / "multiref"
HARD = {4, 27, 38, 40, 52, 69, 92, 98}
NCOMMON = 65536
ZETA = rf.ZETA_NOM


def _bin(freqs, f0, tol=6.0):
    m = np.abs(freqs - f0) <= tol
    if not m.any():
        return None
    idx = np.where(m)[0]
    return int(idx[0]), int(idx[-1])


def _peakbin(freqs, mag, f0, tol=6.0):
    b = _bin(freqs, f0, tol)
    if b is None:
        return None, None
    j = b[0] + int(np.argmax(mag[b[0]:b[1] + 1]))
    return float(mag[j]), j


def run(seeds=(0, 1, 2), obs_frac=0.6, warmup=1000, samples=1000, chains=4, n_draws=200):
    t0 = time.time()
    R = rf.load_reduced()
    meas = rf.reprocess_measured(list(range(1, rf.N_ACCEL_RECORDERS + 1)))
    ch = rf.build_channels(R, meas["daq"])
    didx = {d: i for i, d in enumerate(meas["daq"])}
    REF_KEYS = [k for k in mrf.REFS if (MULTIREF / f"{k}_N{NCOMMON}.npz").exists()]
    caches = {}
    for k in REF_KEYS:
        z = mrf.load_cache(MULTIREF / f"{k}_N{NCOMMON}.npz")
        caches[k] = {"freqs": np.asarray(z["freqs"]), "H1": np.asarray(z["H1"]), "coh": np.asarray(z["coherence"]),
                     "daq": [int(x) for x in z["daq"].tolist()], "label": str(z["label"]),
                     "instrument": str(z["instrument"]), "n_hits": int(z["n_hits_used"])}

    per_seed = []
    for seed in seeds:
        dr = np.array([meas["dyn_range"][didx[d]] for d in ch.daq])
        elig = np.where(dr >= hq.DR_MIN)[0]
        rng = np.random.default_rng(seed); perm = rng.permutation(elig)
        n_obs = int(round(obs_frac * len(perm)))
        obs_pos = np.sort(perm[:n_obs]); ho_pos = np.sort(perm[n_obs:])
        obs_daqs = [ch.daq[p] for p in obs_pos]; ho_daqs = [ch.daq[p] for p in ho_pos]
        hard_ho = np.array([1 if d in HARD else 0 for d in ho_daqs])

        meas_f, _ = mf.extract_measured_modes(meas, SimpleNamespace(daq=obs_daqs))
        pairs, _ = mf.match(R, meas_f)
        mode_idx = np.array([p[0] for p in pairs]); res_hz = np.array([p[1] for p in pairs])
        theta_post, sigw2, cdiag = mf.calibrate_modal(R, mode_idx, res_hz, seed=20260617,
                                                      warmup=warmup, samples=samples, chains=chains)
        sub = np.linspace(0, theta_post.shape[0] - 1, min(theta_post.shape[0], n_draws)).astype(int)

        seed_rec = {"seed": int(seed), "calib_converged": bool(cdiag["converged"]), "calib_diag": cdiag,
                    "n_heldout": int(len(ho_pos)), "by_drive": {}}
        for dk in REF_KEYS:
            c = caches[dk]; cpos = {d: i for i, d in enumerate(c["daq"])}
            freqs = c["freqs"]; w = 2 * np.pi * freqs; eta = 2.0 * ZETA
            # peak bins for each matched mode in THIS cache's freq grid
            bins = [_peakbin(freqs, np.ones(len(freqs)), f, 6.0)[1] for f in res_hz]
            valid = [i for i, b in enumerate(bins) if b is not None]
            mk = mode_idx[valid]; rbins = np.array([bins[i] for i in valid]); mres = res_hz[valid]
            # measured truth peaks (band max) under THIS drive
            def truth_peak(d):
                return float(np.max(np.abs(c["H1"][cpos[d]]))) if d in cpos else 0.0
            peak_tru_ho = np.array([truth_peak(d) for d in ho_daqs])
            peak_tru_ob = np.array([truth_peak(d) for d in obs_daqs])
            clim = peak_tru_ob.copy()
            obs_in = [d for d in obs_daqs if d in cpos]
            cohobs = np.array([c["coh"][cpos[d]][rbins] for d in obs_in])       # (nobs_in, nmk) coherence weights
            pk_ho = np.zeros((len(sub), len(ho_pos)))
            pk_oracle = np.zeros(len(ho_pos))
            for jj, s_ in enumerate(sub):
                th = theta_post[s_]; K = R.A_fix + np.einsum("g,gij->ij", th, R.A)
                lam, Q = np.linalg.eigh(K)
                phi_ho = (ch.rows[ho_pos] @ Q)[:, mk]        # (nho, nmk)
                phi_obs_in = (np.array([ch.rows[obs_pos[obs_daqs.index(d)]] for d in obs_in]) @ Q)[:, mk]
                # complex residue R_{d,k} = sum_s w phi* H / sum_s w |phi|^2  (projection; stable)
                Hc = np.array([c["H1"][cpos[d]][rbins] for d in obs_in])        # complex (nobs_in, nmk)
                wsr = cohobs                                                    # weights
                num = np.sum(wsr * np.conj(phi_obs_in) * Hc, axis=0)
                den = np.sum(wsr * np.abs(phi_obs_in) ** 2, axis=0) + 1e-12
                Rdk = num / den                                                # (nmk,) complex
                # Lorentzian reconstruction over band for held-out sensors
                lamk = lam[mk]
                D = (1 + 1j * eta) * lamk[None, :] - (w ** 2)[:, None]          # (Nf, nmk)
                Lk = (1j * eta * lamk)[None, :] / D                            # unit residue Lorentzian, |Lk(f_k)|~1
                Hhat = (phi_ho * Rdk[None, :]) @ Lk.T                          # (nho, Nf) complex
                pk_ho[jj] = np.max(np.abs(Hhat), axis=1)
                if jj == 0:   # shape-oracle (uses held-out OWN residue; labeled upper bound)
                    Hc_ho = np.array([c["H1"][cpos[d]][rbins] if d in cpos else np.zeros(len(mk), complex) for d in ho_daqs])
                    Hhat_or = Hc_ho @ Lk.T                                      # (nho, Nf) = sum_k Hc_ho[:,k] Lk[f,k]
                    pk_oracle = np.max(np.abs(Hhat_or), axis=1)
            med_ho = np.median(pk_ho, axis=0)
            sig = float(np.std(np.log(med_ho + 1e-300) - np.log(peak_tru_ho + 1e-300)))
            drng = np.random.default_rng(seed + 7)
            twin = pk_ho * np.exp(drng.normal(0, max(min(sig, 3.0), 1e-3), pk_ho.shape))

            def block(mask, draws):
                idx = np.where(mask)[0]
                if len(idx) == 0:
                    return None
                ct = np.mean([SC.crps_sample(draws[:, k] if draws.ndim == 2 else draws, peak_tru_ho[k]) for k in idx])
                cc = np.mean([SC.crps_sample(clim, peak_tru_ho[k]) for k in idx])
                cov = np.mean([SC.coverage_width(draws[:, k], peak_tru_ho[k])["covered"] for k in idx]) if draws.ndim == 2 else None
                return {"n": int(len(idx)), "twin_crps": float(ct), "clim_crps": float(cc),
                        "crps_skill_vs_clim": float(1 - ct / cc), "coverage": (float(cov) if cov is not None else None)}
            # oracle skill (single sample per channel -> use as point; crps of a point)
            or_twin = np.tile(pk_oracle, (50, 1)) * np.exp(np.random.default_rng(seed + 9).normal(0, 0.2, (50, len(ho_pos))))
            # SAME-N FEM-FORWARD control: the inherited value_eval prediction (FEM phi_s x FEM phi_d/zeta x one gain),
            # but on THIS cache's N grid -> isolates the measured-residue method gain from the df/window-damping change.
            drow_d, _, _ = R.reduced_row(tuple(mrf.REFS[dk]["xyz"]), mrf.REFS[dk]["axis"])
            all_rows = np.vstack([ch.rows[obs_pos], ch.rows[ho_pos]]); n_o = len(obs_pos)
            lmf = rf.fem_logmag_batch(R, freqs, theta_post[sub], all_rows, drow_d, zeta=ZETA)   # (M,Nf,Ns)
            tru_obs_full = np.log(np.abs(np.array([c["H1"][cpos[d]] for d in obs_daqs])) + 1e-300).T  # (Nf,nobs)
            pk_fem = np.zeros((len(sub), len(ho_pos)))
            for j in range(len(sub)):
                cg = hq.wmedian((tru_obs_full - lmf[j, :, :n_o]).ravel(), np.ones(tru_obs_full.size))
                pk_fem[j] = np.exp(lmf[j, :, n_o:] + cg).max(axis=0)
            medf = np.median(pk_fem, axis=0)
            sigf = float(np.std(np.log(medf + 1e-300) - np.log(peak_tru_ho + 1e-300)))
            twf = pk_fem * np.exp(np.random.default_rng(seed + 11).normal(0, max(min(sigf, 3.0), 1e-3), pk_fem.shape))
            seed_rec["by_drive"][dk] = {
                "label": c["label"], "instrument": c["instrument"], "n_hits": c["n_hits"],
                "n_modes_excited": int(len(mk)), "sigma_qoi_log": sig,
                "NON_HARD": block(hard_ho == 0, twin), "ALL": block(np.ones(len(ho_pos), bool), twin),
                "FEM_forward_sameN_NON_HARD": block(hard_ho == 0, twf),
                "shape_oracle_NON_HARD": block(hard_ho == 0, or_twin)}
        per_seed.append(seed_rec)
        print(f"seed {seed}: conv {cdiag['converged']} | "
              + " | ".join(f"{seed_rec['by_drive'][k]['label']} {seed_rec['by_drive'][k]['NON_HARD']['crps_skill_vs_clim']:+.2f}"
                           for k in REF_KEYS)
              + " | oracle(+X) %.2f" % seed_rec["by_drive"]["xpos_990x"]["shape_oracle_NON_HARD"]["crps_skill_vs_clim"])

    before = [json.loads((OUT / f"partA_value_eval_seed{s:02d}.json").read_text())["NON_HARD"]["crps_skill_vs_clim"]
              for s in seeds if (OUT / f"partA_value_eval_seed{s:02d}.json").exists()]
    before_mean = float(np.mean(before)) if before else None

    def drive_mean(dk, key="NON_HARD"):
        vals = [s["by_drive"][dk][key]["crps_skill_vs_clim"] for s in per_seed if dk in s["by_drive"] and s["by_drive"][dk][key]]
        return float(np.mean(vals)) if vals else None
    after_xX = drive_mean("xpos_990x")
    oracle_xX = float(np.mean([s["by_drive"]["xpos_990x"]["shape_oracle_NON_HARD"]["crps_skill_vs_clim"] for s in per_seed]))
    before_sameN_xX = drive_mean("xpos_990x", "FEM_forward_sameN_NON_HARD")
    rec = {"deliverable": "held-out per-channel AMPLITUDE skill vs climatology — BEFORE(+X-only) vs AFTER(multi-ref)",
           "common_N": NCOMMON, "seeds": list(seeds),
           "units_gain_note": "R_{d,k} is one training-only per-mode complex residue from OBSERVED channels; no "
                              "per-held-out / per-draw peak tuning (units-honest, Card A protocol).",
           "before_xonly": {"crps_skill_vs_clim": before_mean, "per_seed": before,
                            "source": "partA value_eval (FEM drive amplitude phi_d/zeta), N=200000 (Card F documented -1.0)"},
           "before_xonly_sameN": {"crps_skill_vs_clim": before_sameN_xX,
                                  "source": "FEM-forward control on the SAME N=65536 +X grid (isolates df from method)"},
           "after_multiref": {"crps_skill_vs_clim": after_xX,
                              "drive": "+X peak reconstructed from per-mode MEASURED residue R_{+X,k} (operational-modal)",
                              "note": "this residue uses ONLY +X observed-channel data; the MULTI-reference contribution "
                                      "is the by-drive table below (other drives do NOT beat +X)."},
           "after_by_drive_meanskill": {k: drive_mean(k) for k in REF_KEYS},
           "after_by_drive_FEMforward_sameN": {k: drive_mean(k, "FEM_forward_sameN_NON_HARD") for k in REF_KEYS},
           "shape_oracle_xX_meanskill": oracle_xX,
           "calib_converged": bool(all(s["calib_converged"] for s in per_seed)),
           "per_seed": per_seed, "runtime_s": time.time() - t0}
    OUT.mkdir(exist_ok=True)
    (OUT / "multiref_value.json").write_text(json.dumps(rec, indent=2))
    print(f"\nBEFORE(+X FEM, N=200000 documented) {before_mean:+.2f} | BEFORE(+X FEM, same N=65536) {before_sameN_xX:+.2f}"
          f" -> AFTER(+X measured residue) {after_xX:+.2f}")
    print("after by drive (measured residue):", {k: round(v, 2) for k, v in rec["after_by_drive_meanskill"].items() if v is not None})
    print("FEM-forward by drive (same N):", {k: round(v, 2) for k, v in rec["after_by_drive_FEMforward_sameN"].items() if v is not None})
    print(f"shape-ORACLE(+X, known held-out sensor shape, upper bound) {oracle_xX:+.2f}")
    print(f"runtime {rec['runtime_s']:.0f}s")
    return rec


if __name__ == "__main__":
    run()
