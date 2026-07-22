#!/usr/bin/env python3
"""A3 — matched coverage + proper-score (CRPS) table: statFEM vs FEM+6 dB incumbent.

RECOVERY FIRST (known-answer gate): recompute the stored bake-off coverage/width numbers by importing
the FROZEN predecessor modules read-only (decisions_log D3) with the same seeds:
  - scorecard truth-ensemble coverage (netcg bakeoff, seed 7 truths / seed 0 methods)
  - per-drive measured shear answer-key coverage (heldout_drive machinery)
Numbers must match out/bakeoff_scorecard.json + out/heldout_drive.json to rounding, else this study STOPS.

NEW: fair-ensemble CRPS (quantity contract C3) for (i) FEM+6 dB as a stated-width interval predictor
under 3 distributional conventions (log-uniform primary; linear-uniform, Gaussian-95% sensitivity),
(ii) delivered statFEM F(k) band, (iii) parameter-only modal propagation (= L5_theta_only).
Evidence separation: shear_X/shear_Y per-drive columns = MEASURED held-out evidence; normal_Z =
synthetic truth-ensemble self-consistency, NOT validation.

Writes ONLY to this workspace. Output: out/a3_calibration_table.json
"""
import json
import os
import sys
import time
import numpy as np
from scipy.stats import norm

t0 = time.time()
WS = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
REPORTS = os.path.abspath(os.path.join(WS, ".."))
NCWS = os.path.join(REPORTS, "shocksat_netcg_method_selection_20260701")
sys.path.insert(0, os.path.join(REPORTS, "shocksat_psd_envelope_twin_20260623", "code"))
sys.path.insert(0, os.path.join(NCWS, "code"))
import realfrf as rf                      # noqa: E402
import netcg_qoi as NC                    # noqa: E402
import heldout_drive as HD                # noqa: E402  (functions only; its main() is not called)

AXES = [(0, "shear_X"), (1, "shear_Y"), (2, "normal_Z")]
NQ = 512    # deterministic quantile samples for envelope conventions


def smooth_all(curves):
    return np.array([NC.octave_smooth(NC.FGRID, c) for c in np.atleast_2d(curves)])


def pair_term(xs):
    """E|X-X'| (over distinct pairs, fair form) from SORTED samples, O(n)."""
    n = len(xs)
    i = np.arange(n)
    return 2.0 * np.sum((2 * i - n + 1) * xs) / (n * (n - 1))


def crps_curves(samples_s, truths_s, w):
    """Energy-weighted fair CRPS: samples_s (n, Nf) predictive curves, truths_s (T, Nf), w (Nf,)."""
    Nf = samples_s.shape[1]
    vals = np.empty(Nf)
    for k in range(Nf):
        xs = np.sort(samples_s[:, k])
        t1 = np.mean(np.abs(xs[None, :] - truths_s[:, k][:, None]))
        vals[k] = t1 - 0.5 * pair_term(xs)
    return float(np.sum(w * vals))


def env_samples(lo_s, hi_s, convention):
    """(NQ, Nf) deterministic quantile samples for the FEM+6dB envelope band."""
    q = (np.arange(NQ) + 0.5) / NQ
    lo = np.maximum(lo_s, 1e-300)
    if convention == "log_uniform":
        return lo[None, :] * (hi_s / lo)[None, :] ** q[:, None]
    if convention == "linear_uniform":
        return lo[None, :] + (hi_s - lo)[None, :] * q[:, None]
    if convention == "gaussian_95":
        mu = 0.5 * (np.log10(lo) + np.log10(hi_s))
        sd = (np.log10(hi_s) - np.log10(lo)) / (2 * 1.96)
        return 10 ** (mu[None, :] + sd[None, :] * norm.ppf(q)[:, None])
    raise ValueError(convention)


# ================= load posterior + model =================
z = np.load(os.path.join(NCWS, "out", "theta_post_L5.npz"), allow_pickle=True)
theta_post = z["theta_post"]
theta_map = np.median(theta_post, axis=0)
model = NC.QOIModel()
stored = json.load(open(os.path.join(NCWS, "out", "bakeoff_scorecard.json")))["qois"]
stored_hd = json.load(open(os.path.join(NCWS, "out", "heldout_drive.json")))

# ================= PHASE 1a: scorecard known-answer =================
recomp, deviations = {}, []
ens_cache = {}
for axis, name in AXES:
    nom = model.spectrum(theta_map, axis)
    fem6_lo, fem6_hi = nom / HD.__dict__.get("FEM6DB", 10 ** (6 / 20)), nom * 10 ** (6 / 20)
    fem6_lo = nom / 10 ** (6 / 20)
    fem6_grms = NC.grms(fem6_hi - fem6_lo)
    truths = NC.truth_ensemble(model, axis, theta_map, n=200)
    row = {}
    cov6 = NC.coverage_vs_truth(fem6_lo, fem6_hi, truths, NC.FGRID)
    row["baseline_fem+6dB"] = {"weighted_coverage": cov6["weighted_coverage"],
                               "sharpness_band_grms_ratio_vs_fem6db": 1.0}
    for kind, label in [("theta_only", "L5_theta_only"), ("statfem_fk", "statfem_Fk")]:
        meth = NC.Method(model, axis, theta_post, kind=kind, seed=0)
        E = meth.ensemble()
        lo, med, hi = (np.percentile(E, q, axis=0) for q in (2.5, 50, 97.5))
        cov = NC.coverage_vs_truth(lo, hi, truths, NC.FGRID)
        row[label] = {"weighted_coverage": cov["weighted_coverage"],
                      "sharpness_band_grms_ratio_vs_fem6db":
                          round(NC.grms(hi - lo) / (fem6_grms + 1e-300), 3)}
        ens_cache[(name, label)] = E
    ens_cache[(name, "truths")] = truths
    ens_cache[(name, "fem6")] = (fem6_lo, fem6_hi)
    recomp[name] = row
    for label in row:
        for k in ("weighted_coverage", "sharpness_band_grms_ratio_vs_fem6db"):
            dev = abs(row[label][k] - stored[name][label][k])
            deviations.append(dev)
            if dev > 0.0015:
                print(f"KNOWN-ANSWER DEVIATION {name}/{label}/{k}: {row[label][k]} vs stored {stored[name][label][k]}")

# ================= PHASE 1b: held-out drive known-answer =================
_, Qmap = model.modes(theta_map)
meas = rf.reprocess_measured(list(range(1, rf.N_ACCEL_RECORDERS + 1)))
ch = rf.build_channels(model.R, meas["daq"])
ch_daq = list(ch.daq)
meas_idx = np.where(model.is_meas)[0]
hd_recomp, drive_data = {}, {}
for key, (label, dax) in HD.DRIVES.items():
    p = os.path.join(str(HD.CACHE_DIR), f"{key}.npz")
    c = np.load(p, allow_pickle=True)
    cdaq = [int(d) for d in c["daq"]]
    H1 = np.asarray(c["H1"])
    fc = np.asarray(c["freqs"], float)
    dxyz = tuple(float(x) for x in c["xyz"])
    common = [d for d in cdaq if d in ch_daq]
    s_rows = np.array([ch.rows[ch_daq.index(d)] for d in common])
    H1c = np.array([H1[cdaq.index(d)] for d in common])
    a, phid = HD.fit_participation(model, Qmap, s_rows, dxyz, dax, H1c.T, fc, meas_idx, model.meas_f)
    hd_recomp[label] = {}
    for axis, name in [(0, "shear_X"), (1, "shear_Y")]:
        ans = HD.answer_key(model, axis, Qmap, a, phid, meas_idx, model.meas_f)
        lo, med, hi = HD.per_drive_band(model, theta_post, axis, dxyz, dax, kind="statfem_fk")
        gain = NC.grms(NC.octave_smooth(NC.FGRID, ans)) / (NC.grms(NC.octave_smooth(NC.FGRID, med)) + 1e-300)
        cov = NC.coverage_vs_truth(lo * gain, hi * gain, ans[None, :], NC.FGRID)
        hd_recomp[label][name] = cov["weighted_coverage"]
        dev = abs(cov["weighted_coverage"] - stored_hd["drives"][label][name]["covered_frac"])
        deviations.append(dev)
        if dev > 0.0015:
            print(f"HELDOUT DEVIATION {label}/{name}: {cov['weighted_coverage']} vs "
                  f"{stored_hd['drives'][label][name]['covered_frac']}")
        drive_data[(label, name)] = dict(ans=ans, dxyz=dxyz, dax=dax)

max_dev = float(np.max(deviations))
reproduced = bool(max_dev <= 0.0015)
print(f"KNOWN-ANSWER GATE: reproduced={reproduced} max|dev|={max_dev:.5f} over {len(deviations)} numbers")
if not reproduced:
    # STOP per card: still write the gate result so the failure is artifact-backed.
    json.dump({"known_answer_gate": {"reproduced": False, "max_abs_dev": max_dev}},
              open(os.path.join(WS, "out", "a3_calibration_table.json"), "w"), indent=1)
    sys.exit(2)

# ================= PHASE 2: CRPS =================
CONVENTIONS = ["log_uniform", "linear_uniform", "gaussian_95"]
crps_table = {}
env_sens = {c: {} for c in CONVENTIONS}

# --- synthetic axes (truth ensemble; normal_Z labeled self-consistency) ---
for axis, name in AXES:
    truths_s = smooth_all(ens_cache[(name, "truths")])
    wref = np.median(truths_s, 0) ** 2
    w = wref / wref.sum()
    fem6_lo_s = NC.octave_smooth(NC.FGRID, ens_cache[(name, "fem6")][0])
    fem6_hi_s = NC.octave_smooth(NC.FGRID, ens_cache[(name, "fem6")][1])
    row = {}
    for conv in CONVENTIONS:
        v = crps_curves(env_samples(fem6_lo_s, fem6_hi_s, conv), truths_s, w)
        env_sens[conv][name] = round(v, 4)
        if conv == "log_uniform":
            row["fem6db_log_uniform_primary"] = round(v, 4)
    row["statfem_Fk"] = round(crps_curves(smooth_all(ens_cache[(name, "statfem_Fk")]), truths_s, w), 4)
    row["L5_theta_only_param_only"] = round(
        crps_curves(smooth_all(ens_cache[(name, "L5_theta_only")]), truths_s, w), 4)
    row["evidence"] = ("synthetic truth ensemble — self-consistency, NOT validation" if name == "normal_Z"
                       else "synthetic truth ensemble (scorecard grid); measured per-drive evidence below")
    crps_table[name + "_scorecard_grid"] = row

# --- measured shear evidence per drive ---
rng_kinds = {"statfem_fk": "statfem_fk", "theta_only": None}
measured_rows = {}
for (label, name), dd in sorted(drive_data.items()):
    ans_s = NC.octave_smooth(NC.FGRID, dd["ans"])
    w = ans_s ** 2 / (ans_s ** 2).sum()
    truths_s = ans_s[None, :]
    # statFEM F(k) per-drive predictive ensemble (same construction as per_drive_band, gain on median)
    def drive_ensemble(kind):
        rng = np.random.default_rng(0)
        idx = np.linspace(0, len(theta_post) - 1, 60).astype(int)
        sdf = np.where(model.is_meas, NC.SD_F_M, NC.SD_F_U)
        sda = np.where(model.is_meas, NC.SD_A_M, NC.SD_A_U)
        specs = []
        for s in idx:
            th = theta_post[s]
            base = model.spectrum_drive(th, name == "shear_Y" and 1 or 0, dd["dxyz"], dd["dax"])
            if kind == "param_only":
                specs.append(base)
                continue
            f, Q = model.modes(th)
            fi = f[model.inb]
            g = model.g_axis(Q, 1 if name == "shear_Y" else 0) * model.drive_part(Q, dd["dxyz"], dd["dax"])
            wi = 2 * np.pi * fi
            wg = 2 * np.pi * NC.FGRID
            D = wi[:, None] ** 2 - wg[None, :] ** 2 + 2j * NC.ZETA * wi[:, None] * wg[None, :]
            contrib = np.abs((g[:, None] * wi[:, None] ** 2) / D)
            marg = 0.25 + (NC.SD_A_U - 0.25) * (contrib[~model.is_meas].sum(0) / (contrib.sum(0) + 1e-300))
            for _ in range(30):
                zc = np.log(NC.octave_smooth(NC.FGRID, np.exp(rng.normal(0, 1, len(NC.FGRID))), 1.0))
                zc = (zc - zc.mean()) / (zc.std() + 1e-9)
                specs.append(base * np.exp(marg * zc))
        return np.array(specs)

    row = {}
    for kind, colname in [("statfem_fk", "statfem_Fk"), ("param_only", "L5_theta_only_param_only")]:
        E_s = smooth_all(drive_ensemble(kind))
        med = np.percentile(E_s, 50, axis=0)
        gain = NC.grms(ans_s) / (NC.grms(med) + 1e-300)
        row[colname] = round(crps_curves(E_s * gain, truths_s, w), 4)
    # FEM+6dB per drive: nominal per-drive spectrum at theta_map, own gain on its central curve
    nom_d = NC.octave_smooth(NC.FGRID, model.spectrum_drive(theta_map, 1 if name == "shear_Y" else 0,
                                                            dd["dxyz"], dd["dax"]))
    gain6 = NC.grms(ans_s) / (NC.grms(nom_d) + 1e-300)
    lo6, hi6 = nom_d * gain6 / 10 ** (6 / 20), nom_d * gain6 * 10 ** (6 / 20)
    for conv in CONVENTIONS:
        v = crps_curves(env_samples(lo6, hi6, conv), truths_s, w)
        env_sens[conv][f"{name}@{label}"] = round(v, 4)
        if conv == "log_uniform":
            row["fem6db_log_uniform_primary"] = round(v, 4)
    row["evidence"] = "MEASURED held-out drive answer key (LSQ modal participation to this drive's H1)"
    row["low_observability"] = next(
        (r["low_observability"] for r in stored_hd["summary"][name]["per_drive"] if r["drive"] == label), None)
    measured_rows[f"{name}@{label}"] = row

# per-axis measured aggregate (strong drives only, matching stored summary rule)
agg = {}
for name in ("shear_X", "shear_Y"):
    strong = [k for k in measured_rows if k.startswith(name) and not measured_rows[k]["low_observability"]]
    agg[name] = {c: round(float(np.mean([measured_rows[k][c] for k in strong])), 4)
                 for c in ("fem6db_log_uniform_primary", "statfem_Fk", "L5_theta_only_param_only")}
    agg[name]["n_strong_drives"] = len(strong)
    agg[name]["evidence"] = "MEASURED held-out drives (strong-observability mean)"

out = {
    "source_runs": ["shocksat_netcg_method_selection_20260701 (frozen bake-off + heldout machinery, "
                    "theta_post_L5.npz NUTS draws)",
                    "shocksat_netcg_validated_port_20260716 (2.526 reference / 2.958 tier-updated context)"],
    "known_answer_gate": {
        "reproduced": True, "max_abs_dev": max_dev, "n_numbers_checked": len(deviations),
        "stored_targets": {"fem6db_weighted_coverage": {"shear_X": 0.865, "shear_Y": 0.706, "normal_Z": 0.738},
                           "statfem_Fk_shear_Y": {"ratio": 2.301, "coverage": 0.982}},
        "recomputed_scorecard": recomp,
        "recomputed_heldout_covered_frac": hd_recomp},
    "crps": {
        "definition": "fair ensemble CRPS on the 1-octave-smoothed net-CG force spectrum, energy-weighted "
                      "over FGRID (same weights as weighted_coverage); model-internal force units; lower is better",
        "scorecard_grid": crps_table,
        "measured_per_drive": measured_rows,
        "measured_aggregate_strong_drives": agg,
        "envelope_convention_sensitivity": env_sens,
        "envelope_convention_note": "FEM+6dB is an envelope, not a distribution; primary scoring reads it "
                                    "as log-uniform between edges; linear-uniform and Gaussian-95% reported "
                                    "as convention sensitivity"},
    "normal_z_widths": {
        "delivered_reference": 2.526, "tier_updated": 2.958,
        "note": "2.526x is the delivered reference configuration; 2.958x is the tier-updated configuration "
                "after the one matched extended-band mode's OBSERVED cross-drive ln-amplitude scatter (1.393) "
                "exceeded the assumed unmeasured-tier 0.80, honestly widening the band (H4 falsified)."},
    "evidence_separation": {
        "shear_X": "measured held-out evidence", "shear_Y": "measured held-out evidence",
        "normal_Z": "self-consistency, NOT validation (synthetic truth ensemble only)"},
    "runtime_s": round(time.time() - t0, 1),
}
json.dump(out, open(os.path.join(WS, "out", "a3_calibration_table.json"), "w"), indent=1)
print(json.dumps({"crps_agg_measured": agg, "crps_scorecard": crps_table}, indent=1))
print(f"A3 done in {out['runtime_s']}s")
