#!/usr/bin/env python3
"""Score the six arms on the PRE-REGISTERED resolutions (question_framing.md) and assemble
out/matrix_scorecard.json for the locked checker.

R1 per-point FRF peak amplitude at HELD-OUT SENSORS (5 drives x 3 splits; one global gain per (arm,fold) on
   observed channels; non-leaky observed-residual sigma, D9; CRPS-skill vs observed-peak climatology).
R2 net-CG QOI bands: global statFEM F(k) band vs the common truth ensemble (netcg convention; hard gate
   0.95/0.5 dB pre-registered) + sharpness vs the COMMON FEM+6dB incumbent + leave-one-DRIVE-out coverage
   (5 folds, measured-FRF answer keys, shear only — normal has no data answer key).
R3 leave-modes-out overconfidence audit (hide top-3 measured QOI-driving modes; widen ratio must be > 1).
Metric traps: NO per-mode amplitude fitting in any score (LSQ only inside the arm-independent answer key,
D2); frozen Hungarian pairing from tier-2 (trap-2). Common references are built ONCE from M0 @ M0S0 MAP.
"""
from __future__ import annotations
import json, sys, time
from pathlib import Path
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import rmodel as RMOD
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent / "shocksat_psd_envelope_twin_20260623" / "code"))
import score as SC

WS = Path(__file__).resolve().parent.parent
NC = RMOD.NC
FGRID = RMOD.FGRID
AXES = [(0, "shear_X"), (1, "shear_Y"), (2, "normal_Z")]
FEM6DB = 10 ** (6 / 20)
COV_MIN, EXC_MAX = 0.95, 0.5           # pre-registered hard gate (stricter than netcg 0.90/1.0; documented)
K_HIDDEN = 3
N_DRAWS_R1 = 40
ARMS = ["M0S0", "M0S1", "M0S2", "M1S0", "M1S1", "M1S2"]
t0 = time.time()


def log(m):
    print(f"[{time.time()-t0:7.1f}s] {m}", flush=True)


def load_arm(arm, diag_all):
    z = np.load(WS / "out" / "arms" / f"{arm}.npz", allow_pickle=True)
    post = {k: np.asarray(z[k]) for k in z.files}
    if "tau" in post:
        post["tau"] = float(post["tau"])
    model = RMOD.CModel(diag_all[arm]["cid"])
    return model, post


def peaks_pred(model, th, dkey, srows_sel, fc=None):
    """(Ns,) predicted peak |H| per selected sensor channel on the cache freq grid (S0/S1: model shapes)."""
    f, Q = model.modes(th)
    fi = f[model.inb].copy()
    su = srows_sel @ Q[:, model.inb]                     # (Ns, nM)
    pd = model.drives[dkey] @ Q[:, model.inb]
    w = 2 * np.pi * fc
    wi = 2 * np.pi * fi
    D = wi[:, None] ** 2 - w[None, :] ** 2 + 2j * RMOD.ZETA * wi[:, None] * w[None, :]
    H = -(w[None, :] ** 2) * np.einsum("si,if->sf", (su * pd[None, :]).astype(complex), 1.0 / D)
    return np.max(np.abs(H), axis=1)


def peaks_pred_beck(model, post, row, dkey, srows_sel, fc):
    """S2 variant: matched modes use the INFERRED shape field for sensor rows, drive rows and freqs."""
    th = post["theta_post"][row]
    f, Q = model.modes(th)
    fi = f[model.inb].copy()
    su = srows_sel @ Q[:, model.inb]
    pd = model.drives[dkey] @ Q[:, model.inb]
    phi = post["phi0"] + post["tau"] * post["raw"][row]
    phi = phi / (np.linalg.norm(phi, axis=0, keepdims=True) + 1e-30)
    K = model.K(th)
    ray = np.einsum("ik,ij,jk->k", phi, K, phi)
    fr = np.sqrt(np.clip(ray, 1e-9, None)) / (2 * np.pi)
    pos_of = {int(k): j for j, k in enumerate(model.inb)}
    for j, k in enumerate(model.femk):
        p = pos_of[int(k)]
        su[:, p] = srows_sel @ phi[:, j]
        pd[p] = model.drives[dkey] @ phi[:, j]
        fi[p] = fr[j]
    w = 2 * np.pi * fc
    wi = 2 * np.pi * fi
    D = wi[:, None] ** 2 - w[None, :] ** 2 + 2j * RMOD.ZETA * wi[:, None] * w[None, :]
    H = -(w[None, :] ** 2) * np.einsum("si,if->sf", (su * pd[None, :]).astype(complex), 1.0 / D)
    return np.max(np.abs(H), axis=1)


def r1_score(model, post, is_beck, caches):
    """Held-out-sensor per-point peak amplitude over 5 drives x 3 splits."""
    theta_post = post["theta_post"]
    rows = np.linspace(0, len(theta_post) - 1, N_DRAWS_R1).astype(int)
    cov, crpss, sigq, skills = [], [], [], []
    for dkey, c in caches.items():
        common = [d for d in c["daq"] if d in model.sens_daq]
        fb = (c["freqs"] >= RMOD.BAND[0]) & (c["freqs"] <= RMOD.BAND[1])
        fc = c["freqs"][fb]
        H1 = np.array([c["H1"][c["daq"].index(d)][fb] for d in common])
        pk_meas = np.max(np.abs(H1), axis=1)
        srows = np.array([model.sens[model.sens_daq.index(d)] for d in common])
        P = np.array([peaks_pred_beck(model, post, r, dkey, srows, fc) if is_beck
                      else peaks_pred(model, theta_post[r], dkey, srows, fc=fc) for r in rows])  # (nd, Ns)
        for split in range(3):
            rng = np.random.default_rng(100 + split)
            perm = rng.permutation(len(common))
            n_obs = int(round(0.9 * len(common)))
            obs, ho = perm[:n_obs], perm[n_obs:]
            med = np.median(P, 0)
            gain = float(np.exp(np.median(np.log(pk_meas[obs] + 1e-30) - np.log(med[obs] + 1e-30))))
            resid_obs = np.log(pk_meas[obs] + 1e-30) - np.log(med[obs] * gain + 1e-30)
            sig = max(float(np.std(resid_obs)), 1e-3)                     # NON-LEAKY sigma (D9)
            drng = np.random.default_rng(7 + split)
            sc = []
            for k in ho:
                ens = P[:, k] * gain * np.exp(drng.normal(0, sig, len(rows)))
                sc.append(SC.score_qoi(ens, pk_meas[k]))
            clim = pk_meas[obs]
            clim_crps = float(np.mean([SC.crps_sample(clim, pk_meas[k]) for k in ho]))
            crps = float(np.mean([x["crps"] for x in sc]))
            cov.append(float(np.mean([x["covered"] for x in sc])))
            crpss.append(crps)
            skills.append(1 - crps / (clim_crps + 1e-30))
            sigq.append(float(np.std(np.log(pk_meas[ho] + 1e-30) - np.log(med[ho] * gain + 1e-30))))
    return {"coverage": round(float(np.mean(cov)), 3),
            "crps_skill": round(float(np.mean(skills)), 3),
            "sigma_qoi": round(float(np.mean(sigq)), 3),
            "sigma_interval_used": "observed-residual (non-leaky, D9)",
            "n_folds": len(cov)}


def main():
    diag_all = json.loads((WS / "out" / "arms_diag.json").read_text())
    caches = {k: RMOD.load_cache(k) for k in RMOD.DRIVE_KEYS}

    # -------- common references from M0 @ M0S0 MAP --------
    m0, post00 = load_arm("M0S0", diag_all)
    th_map0 = np.median(post00["theta_post"], 0)
    fem6, truths, akeys = {}, {}, {}
    for axis, name in AXES:
        nom = m0.spectrum(th_map0, axis)
        fem6[name] = NC.grms(nom * FEM6DB - nom / FEM6DB)
        truths[name] = RMOD.truth_ensemble(m0, axis, th_map0, n=200)
    for axis, name in AXES[:2]:
        for dkey in RMOD.DRIVE_KEYS:
            akeys[(name, dkey)] = RMOD.answer_key(m0, th_map0, axis, dkey, caches[dkey])
    log("common references built (fem6 bars, truth ensembles, 10 answer keys)")

    arms_out = {}
    for arm in ARMS:
        model, post = load_arm(arm, diag_all)
        is_beck = "raw" in post
        theta_post = post["theta_post"]
        th_map = np.median(theta_post, 0)
        rec = {"cid": diag_all[arm]["cid"], "nuts_diag": diag_all[arm]["final"],
               "n_modes_used": diag_all[arm]["n_modes_used"], "R2": {}, "R3_leave_modes_out": {}}

        def fn_of(axis, dkey):
            return RMOD.beck_shapes_fn(model, post, axis, dkey, lambda s: s) if is_beck else None

        glob_bands = {}
        for axis, name in AXES:
            lo, med, hi = RMOD.statfem_fk_band(model, theta_post, axis, None, shapes_fn=fn_of(axis, None))
            glob_bands[name] = (lo, med, hi)
            cov = NC.coverage_vs_truth(lo, hi, truths[name], FGRID)
            covers = cov["weighted_coverage"] >= COV_MIN and cov["energy_wtd_pos_dB_exceed"] <= EXC_MAX
            rec["R2"][name] = {"sharpness_vs_fem6db": round(NC.grms(hi - lo) / (fem6[name] + 1e-300), 3),
                               "weighted_coverage": cov["weighted_coverage"],
                               "peak_coverage": cov["peak_coverage"],
                               "energy_wtd_pos_dB_exceed": cov["energy_wtd_pos_dB_exceed"],
                               "covers_hard_gate": bool(covers)}
        # leave-one-drive-out (5 folds, shear)
        for axis, name in AXES[:2]:
            per_drive, grs = [], []
            for dkey in RMOD.DRIVE_KEYS:
                ans, ncom = akeys[(name, dkey)]
                lo, med, hi = RMOD.statfem_fk_band(model, theta_post, axis, dkey,
                                                   shapes_fn=fn_of(axis, dkey), n_theta=36, n_disc=24)
                gain = NC.grms(NC.octave_smooth(FGRID, ans)) / (NC.grms(NC.octave_smooth(FGRID, med)) + 1e-300)
                cov = NC.coverage_vs_truth(lo * gain, hi * gain, ans[None, :], FGRID)
                per_drive.append({"drive": RMOD.DRIVE_LABEL[dkey], "covered_frac": cov["weighted_coverage"],
                                  "exceed_db": cov["energy_wtd_pos_dB_exceed"],
                                  "answerkey_grms": float(NC.grms(ans))})
                grs.append(float(NC.grms(ans)))
            medg = float(np.median(grs))
            strong = [p for p in per_drive if p["answerkey_grms"] >= 0.15 * medg]
            for p in per_drive:
                p["low_observability"] = bool(p["answerkey_grms"] < 0.15 * medg)
            rec["R2"][name]["heldout_drive"] = {
                "per_drive": per_drive,
                "mean_cov_strong": round(float(np.mean([p["covered_frac"] for p in strong])), 3),
                "min_cov_strong": round(float(np.min([p["covered_frac"] for p in strong])), 3),
                "n_strong": len(strong)}
        # R3 leave-modes-out
        for axis, name in AXES:
            f_, Q_ = model.modes(th_map)
            gg = model.tray[axis] @ Q_[:, model.inb]
            mi = np.where(model.is_meas)[0]
            topK = mi[np.argsort(np.abs(gg[mi]))[::-1][:K_HIDDEN]]
            part = float((np.abs(gg[topK]).sum()) / (np.abs(gg).sum() + 1e-30))
            lo0, _, hi0 = glob_bands[name]
            lo1, _, hi1 = RMOD.statfem_fk_band(model, theta_post, axis, None, hidden=topK,
                                               shapes_fn=fn_of(axis, None), seed=2)
            truths_lmo = RMOD.truth_ensemble(model, axis, th_map, extra_hidden=topK, n=200, seed=11)
            cov = NC.coverage_vs_truth(lo1, hi1, truths_lmo, FGRID)
            widen = NC.grms(hi1 - lo1) / (NC.grms(hi0 - lo0) + 1e-30)
            rec["R3_leave_modes_out"][name] = {
                "hidden_modes_hz": [round(float(f_[model.inb][i]), 1) for i in topK],
                "hidden_participation_frac": round(part, 3), "test_discriminating": bool(part >= 0.10),
                "widen_ratio": round(float(widen), 2),
                "weighted_coverage_after_hiding": cov["weighted_coverage"],
                "verdict": ("PASS_humble" if (widen >= 1.03 and cov["weighted_coverage"] >= 0.85)
                            else "FAIL_overconfident")}
        disq = any(v["verdict"] == "FAIL_overconfident" for v in rec["R3_leave_modes_out"].values()
                   if v["test_discriminating"])
        rec["disqualified"] = bool(disq)
        # R1
        rec["R1"] = r1_score(model, post, is_beck, caches)
        arms_out[arm] = rec
        log(f"[{arm}] R1 cov {rec['R1']['coverage']} skill {rec['R1']['crps_skill']} sig {rec['R1']['sigma_qoi']} | "
            + " ".join(f"{n}:{rec['R2'][n]['sharpness_vs_fem6db']}x/{rec['R2'][n]['weighted_coverage']}"
                       for _, n in AXES) + f" | dq={disq}")

    # -------- delivery selection per QOI (pre-registered rule) --------
    ev = json.loads((WS / "out" / "tier3_evidence.json").read_text())
    delivered = {}
    for qoi, names in [("shear", ["shear_X", "shear_Y"]), ("normal", ["normal_Z"])]:
        elig = []
        for arm in ARMS:
            r = arms_out[arm]
            if r["disqualified"]:
                continue
            if not all(r["R2"][n]["covers_hard_gate"] for n in names):
                continue
            if qoi == "shear" and any(r["R2"][n]["heldout_drive"]["mean_cov_strong"] < 0.90 for n in names):
                continue
            elig.append((float(np.mean([r["R2"][n]["sharpness_vs_fem6db"] for n in names])), arm))
        if elig:
            sharp, win = min(elig)
            d = {"arm": win, "mean_sharpness_vs_fem6db": round(sharp, 3), "best_of_N": len(ARMS),
                 "n_passing_gate": len(elig)}
            if win.startswith("M1"):
                m0c = "M0" + win[2:]
                d["evidence_beats_M0"] = bool(ev["headline"]["ranking"][0] != "baseline")
                d["heldout_beats_M0"] = bool(sharp < float(np.mean(
                    [arms_out[m0c]["R2"][n]["sharpness_vs_fem6db"] for n in names]))
                    or arms_out[win]["R1"]["crps_skill"] > arms_out[m0c]["R1"]["crps_skill"])
            delivered[qoi] = d
        else:
            delivered[qoi] = {"arm": None, "best_of_N": len(ARMS), "n_passing_gate": 0,
                              "note": "NO arm passed the pre-registered hard gate for this QOI"}

    out = {"task": "composite bake-off matrix (M{0,1} x S{0,1,2} + statFEM F(k))",
           "per_mode_amp_fit_in_scores": False,
           "pairing_method": "assignment_hungarian", "pairing_frozen": True,
           "full_inband_mode_set": True,
           "hard_gate": {"weighted_coverage_min": COV_MIN, "exceed_db_max": EXC_MAX,
                         "note": "pre-registered STRICTER than netcg (0.90/1.0); shear also needs "
                                 "strong-drive mean held-out coverage >= 0.90"},
           "baseline_bars": {"statfem_Fk_proven": {"shear_X": 1.508, "shear_Y": 2.301, "normal_Z": 2.526}},
           "m1_candidate": diag_all["m1_candidate"], "m1_evidence_flag": diag_all["m1_evidence_flag"],
           "arms": arms_out, "delivered": delivered}
    (WS / "out" / "matrix_scorecard.json").write_text(json.dumps(out, indent=1))
    log("wrote matrix_scorecard.json")
    log("delivered: " + json.dumps(delivered))


if __name__ == "__main__":
    main()
