#!/usr/bin/env python3
"""Stage 0 (NO NUTS): QOI sensitivity + validity gate for the net-CG FORCE method-selection bake-off.

Deliverables (all JSON in out/, figure in a separate Tufte-linted script):
  1. stage0_qoi_weights.json  — per-QOI modal PARTICIPATION weights (which modes drive shear vs normal),
     measured flag, cumulative measured (=trust) fraction. QOI = net-CG force on the TOP TRAY (z>=55 in),
     directions separate: tray_shear_X, tray_shear_Y, tray_normal_Z; + base_shear_* + mount_response context.
  2. stage0_observability.json — per-drive (5 drives incl +Y) coherence at each in-band FEM mode; which drives
     coherently observe each mode; the specific 232/254 Hz drumhead-mode observability with vs without +Y.
  3. stage0_trust.json — MC trust table (meas freq 1%/amp 0.35 vs UNMEAS freq SD_F_U/amp SD_A_U) under the
     BASELINE measured set (.ash-matched) vs the +Y-FOLDED set (.ash-matched OR coherently observed by >=1 drive).
  4. stage0_sensitivity.json — sweep the assumed unmeasured-mode sigma (SD_F_U, SD_A_U) up/down ~2x; report how
     the normal-QOI band factor + trust move (bounds how load-bearing those hand-chosen assumptions are).
  5. stage0_validity.json — per-QOI verdict: does discriminating held-out data exist for this QOI?

REUSES realfrf (load_reduced), shape_borrow_diag (.ash MAC match). Uniform-mass proxy over the tray region
(documented; consistent-mass is a sensitivity item). float64. Deterministic (seed 0).
"""
from __future__ import annotations
import json, sys
from pathlib import Path
import numpy as np

WS = Path(__file__).resolve().parent.parent
BASE = WS.parent / "shocksat_psd_envelope_twin_20260623"
sys.path.insert(0, str(BASE / "code"))
import realfrf as rf
import shape_borrow_diag as SB

FEMNPZ = WS.parent / "shocksat_fem_modal_twin_20260609" / "fem_model.npz"
CACHE_DIR = WS / "data" / "multiref_modal"
DRIVES = ["m_xpos_990x", "m_zpos_990z", "m_xy_990xy", "m_zpos_900z", "m_ypos_990y"]
DRIVE_LABEL = {"m_xpos_990x": "+X", "m_zpos_990z": "+Z(990)", "m_xy_990xy": "+XY",
               "m_zpos_900z": "+Z(900)", "m_ypos_990y": "+Y"}
BAND = (45.0, 260.0); ZETA = 0.01
TRAY_Z = 55.0                     # top-plate / tray region floor [in]
MOUNT = (0.0, 0.0, 57.74989)
N_MC = 600
SD_F_M, SD_A_M = 0.01, 0.35       # measured-mode freq / log-amp sigma
SD_F_U, SD_A_U = 0.06, 0.80       # UNMEASURED-mode freq / log-amp sigma (hand-chosen; swept in sensitivity)
COH_OBS = 0.70                    # coherence threshold for "drive coherently observes this mode"
PEAK_TOL_HZ = 3.0                 # mode<->cache-peak match tolerance
OUT = WS / "out"; OUT.mkdir(exist_ok=True)


def cache_peaks(z):
    """modal peaks (Hz) + median-channel coherence at each peak for one drive cache."""
    from scipy.signal import find_peaks
    fb = np.asarray(z["freqs"], float); H1 = np.asarray(z["H1"]); coh = np.asarray(z["coherence"], float)
    mag = np.median(np.abs(H1), axis=0)
    pk, _ = find_peaks(np.log(mag + 1e-300), prominence=0.3, distance=max(1, int(2.0 / (fb[1] - fb[0]))))
    peaks = [(float(fb[i]), float(np.median(coh[:, i]))) for i in pk]
    return peaks, fb, coh


def main():
    R = rf.load_reduced()
    K1 = R.A_fix + R.A.sum(0)
    w2, Q = np.linalg.eigh(K1)
    fmodes = np.sqrt(np.clip(w2, 0, None)) / (2 * np.pi)
    inb = np.where((fmodes >= BAND[0]) & (fmodes <= BAND[1]))[0]
    fb = fmodes[inb]; wi2 = (2 * np.pi * fb) ** 2; nM = len(inb)

    keep_arr = np.empty(len(R.keeprow), np.int64)
    for dof, row in R.keeprow.items():
        keep_arr[row] = dof
    node_of = keep_arr // 6
    axis_of = keep_arr % 6
    U = np.asarray(R.vk[:, :80], np.float64) @ R.T
    field = U @ Q[:, inb]                         # (n_kept_dof, nM) full-field modal displacement
    z_of = R.xyz[node_of, 2]
    tray = z_of >= TRAY_Z

    # --- .ash measured-shape match (drive-independent shape anchor)
    D = SB.build_dofs(R); _, pairs = SB.match_modes(D, Q)
    matched = {int(k): float(D["mfr"][r]) for (r, k, mc) in pairs}   # fem_mode -> measured freq
    is_meas = np.array([int(k) in matched for k in inb])

    # --- QOI coefficient matrices G (n_comp, nM): net-CG force = omega^2 * sum(mass-weighted phi)
    G = {}
    for a, lab in [(0, "tray_shear_X"), (1, "tray_shear_Y"), (2, "tray_normal_Z")]:
        sel = tray & (axis_of == a)
        G[lab] = (wi2 * field[sel].sum(0))[None, :]
    for a, lab in [(0, "base_shear_X"), (1, "base_shear_Y"), (2, "base_shear_Z")]:
        G[lab] = (wi2 * field[axis_of == a].sum(0))[None, :]
    mrow, _, _ = R.reduced_row(MOUNT, "Z"); phim = (mrow @ Q)[inb]
    G["mount_response"] = (-wi2 * phim ** 2)[None, :]

    # --- per-drive observability at each in-band FEM mode
    peaks_by_drive = {}
    for key in DRIVES:
        p = CACHE_DIR / f"{key}.npz"
        if not p.exists():
            continue
        z = np.load(p, allow_pickle=True)
        peaks, _, _ = cache_peaks(z)
        peaks_by_drive[key] = peaks
    obs_rows = []
    observed_any = np.zeros(nM, bool)
    for j, k in enumerate(inb):
        f_i = float(fb[j]); drives_here = {}
        for key, peaks in peaks_by_drive.items():
            best = None
            for (pf, pc) in peaks:
                if abs(pf - f_i) <= PEAK_TOL_HZ and (best is None or pc > best[1]):
                    best = (pf, pc)
            if best is not None:
                drives_here[DRIVE_LABEL[key]] = {"peak_hz": round(best[0], 1), "coh": round(best[1], 2),
                                                 "observed": bool(best[1] >= COH_OBS)}
        obs = any(d["observed"] for d in drives_here.values())
        observed_any[j] = obs
        obs_rows.append({"fem_mode": int(k), "fem_freq_hz": round(f_i, 1),
                         "ash_measured": bool(is_meas[j]), "coherently_observed": bool(obs),
                         "drives": drives_here})
    # observability WITHOUT +Y (to isolate +Y's marginal contribution)
    observed_noY = np.zeros(nM, bool)
    for j, k in enumerate(inb):
        dd = obs_rows[j]["drives"]
        observed_noY[j] = any(v["observed"] for kk, v in dd.items() if kk != "+Y")

    # 3 uncertainty TIERS per mode (D4): 0=shape-measured(.ash), 1=freq-observed-only, 2=prior.
    #   tier0 freq SD 1% + amp SD 0.35 ; tier1 freq 1% (anchored) but amp UNMEAS ; tier2 freq 6% + amp UNMEAS.
    # freq-observability != shape-measurement: a coherent peak anchors FREQUENCY, not the net-CG PARTICIPATION.
    def tiers_for(observed_mask):
        t = np.full(nM, 2, int)
        t[observed_mask & ~is_meas] = 1
        t[is_meas] = 0
        return t
    tiers_shape = tiers_for(np.zeros(nM, bool))       # only .ash shapes anchored; everything else prior
    tiers_noY = tiers_for(observed_noY)               # + freq-observability from the original 4 drives
    tiers_withY = tiers_for(observed_any)             # + freq-observability incl +Y (adds 230.6 Hz uniquely)

    # observability specifically for the drumhead band (>=230 Hz) with vs without +Y
    drum_idx = [j for j in range(nM) if fb[j] >= 228.0]
    def drum_obs(exclude_Y):
        rows = []
        for j in drum_idx:
            dd = obs_rows[j]["drives"]
            drives = {k: v for k, v in dd.items() if not (exclude_Y and k == "+Y")}
            rows.append({"freq_hz": round(float(fb[j]), 1),
                         "observed": any(v["observed"] for v in drives.values()),
                         "by": [k for k, v in drives.items() if v["observed"]]})
        return rows

    # --- MC trust machinery (reuse the validated approach)
    fg = np.linspace(40, 300, 600); w = 2 * np.pi * fg
    bmask = (fg >= BAND[0]) & (fg <= BAND[1])

    def rms(Gc, fmod, amp):
        wi = 2 * np.pi * fmod
        qt = 1.0 / (wi[:, None] ** 2 - w[None, :] ** 2 + 2j * ZETA * wi[:, None] * w[None, :])
        resp = (Gc * amp[None, :]) @ qt
        F = np.sqrt((np.abs(resp) ** 2).sum(0))
        return float(np.sqrt(np.mean(F[bmask] ** 2)))

    rng = np.random.default_rng(0)
    DF = rng.normal(0, 1, (N_MC, nM)); DA = rng.normal(0, 1, (N_MC, nM))

    def trust_row(Gc, tiers, sdfu, sdau):
        # per-tier sigmas: tier0 shape-measured, tier1 freq-observed-only (freq tight, amp wide), tier2 prior
        sdf_t = np.array([SD_F_M, SD_F_M, sdfu]); sda_t = np.array([SD_A_M, sdau, sdau])
        sdf = sdf_t[tiers]; sda = sda_t[tiers]
        shape_meas = tiers == 0
        nom = rms(Gc, fb, np.ones(nM))
        meas_only = rms(Gc, fb, shape_meas.astype(float))    # trust = SHAPE-measured participation only
        def mc(active):
            o = np.empty(N_MC)
            for t in range(N_MC):
                fp = fb * (1 + np.where(active, DF[t] * sdf, 0.0))
                ap = np.exp(np.where(active, DA[t] * sda, 0.0))
                o[t] = rms(Gc, fp, ap)
            return o
        a_all = mc(np.ones(nM, bool)); a_unm = mc(~shape_meas); a_meas = mc(shape_meas)
        p = np.percentile(a_all, [2.5, 50, 97.5])
        vU, vM = np.var(np.log(a_unm)), np.var(np.log(a_meas))
        return {"trust_pct": round(100 * meas_only / (nom + 1e-30), 0),
                "band_pm_pct": round(float((p[2] - p[0]) / 2 / p[1] * 100), 0),
                "band_factor": round(float(p[2] / max(p[0], 1e-9)), 1),
                "var_share_unmeasured_pct": round(100 * float(vU / (vU + vM + 1e-30)), 0)}

    # --- participation weights per QOI (static: |G|-based) + cumulative measured fraction
    qoi_weights = {}
    for lab, Gc in G.items():
        contr = np.sqrt((np.abs(Gc) ** 2).sum(0)); w_n = contr / (contr.sum() + 1e-30)
        order = np.argsort(w_n)[::-1]
        top = [{"hz": round(float(fb[c]), 1), "weight_pct": round(float(w_n[c] * 100), 1),
                "ash_measured": bool(is_meas[c]), "coherently_observed": bool(observed_any[c])}
               for c in order[:8]]
        qoi_weights[lab] = {
            "participation_shape_measured_pct": round(float(100 * w_n[is_meas].sum()), 0),
            "participation_freq_observable_pct": round(float(100 * w_n[observed_any].sum()), 0),
            "top_modes": top}

    # --- trust table: SHAPE-only vs +freq-obs(no Y) vs +freq-obs(with Y). trust_pct is shape-based (same);
    #     the BAND shows how much frequency-observability (esp. +Y's unique 230.6 Hz) tightens it.
    trust = {}
    for lab, Gc in G.items():
        trust[lab] = {"shape_only": trust_row(Gc, tiers_shape, SD_F_U, SD_A_U),
                      "freqobs_noY": trust_row(Gc, tiers_noY, SD_F_U, SD_A_U),
                      "freqobs_withY": trust_row(Gc, tiers_withY, SD_F_U, SD_A_U)}

    # --- sensitivity sweep on unmeasured-mode sigma (normal + one shear for contrast), realistic +Y-folded state
    sens = {}
    for lab in ["tray_normal_Z", "tray_shear_X", "base_shear_Y", "mount_response"]:
        Gc = G[lab]; grid = []
        for sf in (SD_F_U / 2, SD_F_U, SD_F_U * 2):
            for sa in (SD_A_U / 2, SD_A_U, SD_A_U * 2):
                r = trust_row(Gc, tiers_withY, sf, sa)
                grid.append({"SD_F_U": round(sf, 3), "SD_A_U": round(sa, 2),
                             "band_factor": r["band_factor"], "band_pm_pct": r["band_pm_pct"],
                             "trust_pct": r["trust_pct"], "var_unmeas_pct": r["var_share_unmeasured_pct"]})
        sens[lab] = grid

    # --- write JSONs
    n_ash = int(is_meas.sum()); n_obs_noY = int(observed_noY.sum()); n_obs_withY = int(observed_any.sum())
    meta = {"n_inband_modes": int(nM), "inband_freqs_hz": [round(float(x), 1) for x in fb],
            "n_shape_measured_ash": n_ash, "n_freq_observed_noY": n_obs_noY, "n_freq_observed_withY": n_obs_withY,
            "Y_marginal_freq_observed_modes": [round(float(fb[j]), 1) for j in range(nM)
                                               if observed_any[j] and not observed_noY[j]],
            "tray_region": f"z>={TRAY_Z} in ({int(tray.sum())} kept DOFs' nodes)",
            "mass_model": "uniform-mass proxy over tray region (documented; consistent-mass = sensitivity item)",
            "sampler": "NONE (Stage 0 is analytical MC over mode uncertainty)"}
    (OUT / "stage0_qoi_weights.json").write_text(json.dumps(
        {"meta": meta, "qoi_participation": qoi_weights,
         "note": "participation_shape_measured_pct = share of QOI modal participation on .ash-shape-matched modes "
                 "(what we truly know for the net-CG functional); participation_freq_observable_pct additionally "
                 "counts modes with a coherent FRF peak (frequency anchorable, shape NOT resolved). TRUST(dynamic) "
                 "in stage0_trust.json is SHAPE-based."}, indent=2))
    (OUT / "stage0_observability.json").write_text(json.dumps(
        {"meta": {"coh_threshold": COH_OBS, "peak_tol_hz": PEAK_TOL_HZ, "drives": [DRIVE_LABEL[d] for d in DRIVES]},
         "per_mode": obs_rows,
         "drumhead_band_observability_without_Y": drum_obs(exclude_Y=True),
         "drumhead_band_observability_with_Y": drum_obs(exclude_Y=False)}, indent=2))
    (OUT / "stage0_trust.json").write_text(json.dumps(
        {"basis": "flat modal drive; trust = measured-only RMS / all-mode RMS; band = MC over mode uncertainty "
                  f"(meas freq {SD_F_M}/amp {SD_A_M}, UNMEAS freq {SD_F_U}/amp {SD_A_U})",
         "trust": trust, "note": "EXPLORATORY; YELLOW; NO NUTS."}, indent=2))
    (OUT / "stage0_sensitivity.json").write_text(json.dumps(
        {"swept": "unmeasured-mode sigma SD_F_U (freq) and SD_A_U (log-amp), each /2, x1, x2",
         "baseline": {"SD_F_U": SD_F_U, "SD_A_U": SD_A_U}, "grid": sens}, indent=2))

    # --- validity gate verdict per QOI (rule-based on trust + observability)
    def verdict(lab):
        tr = trust[lab]["shape_only"]["trust_pct"]   # shape-based trust (identical across obs scenarios)
        if tr >= 80:
            return "PASS_NUMBER", f"shape-trust {tr:.0f}% (measured modes carry it) -> held-out drives discriminate the number"
        if tr >= 40:
            return "PARTIAL", f"shape-trust {tr:.0f}% -> number partly data-starved (drumhead shape unresolved); band informative, leave-modes-out mechanism test required"
        return "DATA_STARVED_NUMBER", (f"shape-trust {tr:.0f}% -> number data-starved; deliverable = covering band + "
                                       "leave-modes-out mechanism validation + next-test recommendation")
    validity = {lab: dict(zip(["verdict", "why"], verdict(lab))) for lab in G}
    (OUT / "stage0_validity.json").write_text(json.dumps({"per_qoi": validity,
        "leave_modes_out": "the low-trust QOIs keep their place in the bake-off via the leave-modes-out humility "
                           "test (Stage 2/§5): hide measured modes -> band MUST widen to cover them."}, indent=2))

    # --- console summary
    print(f"in-band modes {nM}; shape-measured(.ash) {n_ash}; freq-observed noY {n_obs_noY}; withY {n_obs_withY}")
    print(f"+Y marginal freq-observed modes: {meta['Y_marginal_freq_observed_modes']}")
    print(f"\n{'QOI':<15}{'shpMeas%':>9}{'freqObs%':>9}{'trust%':>8}{'bx_shp':>8}{'bx_+Y':>7}  top modes(*shape,o freqobs,!prior)")
    for lab in ["tray_shear_X", "tray_shear_Y", "tray_normal_Z", "base_shear_X", "base_shear_Y",
                "base_shear_Z", "mount_response"]:
        qw = qoi_weights[lab]; ts = trust[lab]["shape_only"]; tY = trust[lab]["freqobs_withY"]
        tm = " ".join(f"{m['hz']:.0f}{'*' if m['ash_measured'] else ('o' if m['coherently_observed'] else '!')}"
                      f"({m['weight_pct']:.0f})" for m in qw["top_modes"][:4])
        print(f"{lab:<15}{qw['participation_shape_measured_pct']:>9.0f}"
              f"{qw['participation_freq_observable_pct']:>9.0f}{ts['trust_pct']:>8.0f}"
              f"{ts['band_factor']:>8.1f}{tY['band_factor']:>7.1f}  {tm}")
    print("\ndrumhead band (>=228 Hz) observability:")
    print("  without +Y:", drum_obs(True))
    print("  with    +Y:", drum_obs(False))
    print("\nvalidity:")
    for lab in ["tray_shear_X", "tray_shear_Y", "tray_normal_Z"]:
        print(f"  {lab}: {validity[lab]['verdict']} — {validity[lab]['why']}")
    print("\nwrote stage0_*.json")


if __name__ == "__main__":
    main()
