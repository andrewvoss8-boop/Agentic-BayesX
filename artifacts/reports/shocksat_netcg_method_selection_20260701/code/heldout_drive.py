#!/usr/bin/env python3
"""Follow-on #1 — REAL held-out-DRIVE answer key for the net-CG SHEAR force (hardens the shear win).

For each of the 5 drives held out in turn, reconstruct that drive's per-drive net-CG SHEAR force from its MEASURED
FRFs (independent of the twin's tier model) and check the WINNING method's per-drive band covers it (1-octave):
  - fit per-mode complex participation a_i (MEASURED modes only) by LSQ to the drive's 111-sensor measured FRF,
    reduced-model shapes at theta_map, measured/matched frequencies;
  - answer key  G_ans(w) = |sum_{i meas} a_i * g_i^tray,axis * phi_drive,i * w^2 / D_i(w; meas_f_i)|;
  - twin per-drive band = L5_freq_discrep ensemble WITH the drive participation phi_drive;
  - fit ONE global gain per drive (hammer/mass-norm nuisance; input level cancels), then 1-oct coverage.
SHEAR only: NORMAL has no held-out-drive answer key (drumhead shape unmeasured) -> stays on leave-modes-out.

Reuses realfrf (sensors) + netcg_qoi (fast reduced model) + the cached L5 theta posterior. Writes
out/heldout_drive.json. Run: python3 heldout_drive.py
"""
from __future__ import annotations
import sys, json
from pathlib import Path
import numpy as np

WS = Path(__file__).resolve().parent.parent
BASE = WS.parent / "shocksat_psd_envelope_twin_20260623"
sys.path.insert(0, str(BASE / "code")); sys.path.insert(0, str(WS / "code"))
import realfrf as rf
import netcg_qoi as NC

CACHE_DIR = WS / "data" / "multiref_modal"
DRIVES = {"m_xpos_990x": ("+X", "X"), "m_zpos_990z": ("+Z(990)", "Z"), "m_xy_990xy": ("+XY", "XY"),
          "m_zpos_900z": ("+Z(900)", "Z"), "m_ypos_990y": ("+Y", "Y")}
AXES = [(0, "shear_X"), (1, "shear_Y")]     # SHEAR only (reconstructable answer key)
ZETA = NC.ZETA; RIDGE = 1e-3


def fit_participation(model, Q, sensor_rows, drive_xyz, drive_axis, H1, fc, meas_idx, meas_f):
    """LSQ per-mode complex a_i (measured modes) to the drive's all-sensor measured FRF on cache freqs fc."""
    wc = 2 * np.pi * fc
    Phi = sensor_rows @ Q[:, model.inb]                      # (Ns, nM)
    phid = model.drive_part(Q, drive_xyz, drive_axis)        # (nM,)
    fi = meas_f[meas_idx]; wi = 2 * np.pi * fi
    D = wi[:, None] ** 2 - wc[None, :] ** 2 + 2j * ZETA * wi[:, None] * wc[None, :]   # (nmeas, Nf)
    # basis[f,s,i] = -wc^2 * Phi[s,i]*phid[i] / D[i,f]
    Ps = Phi[:, meas_idx]                                    # (Ns, nmeas)
    basis = (-(wc[None, :, None] ** 2)) * (Ps[:, None, :] * phid[meas_idx][None, None, :]) \
        / D.T[None, :, :]                                    # (Ns, Nf, nmeas)
    A = basis.reshape(-1, len(meas_idx)); b = H1.reshape(-1)
    AhA = A.conj().T @ A + RIDGE * np.eye(len(meas_idx)) * (np.real(np.trace(A.conj().T @ A)) / len(meas_idx))
    a = np.linalg.solve(AhA, A.conj().T @ b)
    return a, phid


def per_drive_band(model, theta_post, axis, dxyz, dax, kind="statfem_fk", n_theta=60, n_disc=30, seed=0):
    """Per-drive net-CG force 95% band for a formulation (statfem_fk = QOI-aware smooth output discrepancy;
    freq_discrep = per-mode amplitude). Uses spectrum_drive (includes phi_drive)."""
    rng = np.random.default_rng(seed); specs = []
    idx = np.linspace(0, len(theta_post) - 1, n_theta).astype(int)
    sdf = np.where(model.is_meas, NC.SD_F_M, NC.SD_F_U); sda = np.where(model.is_meas, NC.SD_A_M, NC.SD_A_U)
    for s in idx:
        th = theta_post[s]
        if kind == "statfem_fk":
            base = model.spectrum_drive(th, axis, dxyz, dax)
            # QOI-aware marginal: wide where UNMEASURED modes drive this per-drive spectrum, tight elsewhere
            f, Q = model.modes(th); fi = f[model.inb]; g = model.g_axis(Q, axis) * model.drive_part(Q, dxyz, dax)
            wi = 2 * np.pi * fi; w = 2 * np.pi * NC.FGRID
            D = wi[:, None] ** 2 - w[None, :] ** 2 + 2j * NC.ZETA * wi[:, None] * w[None, :]
            contrib = np.abs((g[:, None] * wi[:, None] ** 2) / D)
            unm = ~model.is_meas
            marg = 0.25 + (NC.SD_A_U - 0.25) * (contrib[unm].sum(0) / (contrib.sum(0) + 1e-300))
            for _ in range(n_disc):
                zc = np.log(NC.octave_smooth(NC.FGRID, np.exp(rng.normal(0, 1, len(NC.FGRID))), 1.0))
                zc = (zc - zc.mean()) / (zc.std() + 1e-9)
                specs.append(base * np.exp(marg * zc))
        else:
            for _ in range(n_disc):
                amp = np.exp(rng.normal(0, 1, model.nM) * sda); fsc = 1 + rng.normal(0, 1, model.nM) * sdf
                specs.append(model.spectrum_drive(th, axis, dxyz, dax, amp=amp, fscale=fsc))
    specs = np.array(specs)
    return (np.percentile(specs, q, 0) for q in (2.5, 50, 97.5))


def answer_key(model, axis, Q, a, phid, meas_idx, meas_f):
    g = model.g_axis(Q, axis)
    wi = 2 * np.pi * meas_f[meas_idx]; w = 2 * np.pi * NC.FGRID
    D = wi[:, None] ** 2 - w[None, :] ** 2 + 2j * ZETA * wi[:, None] * w[None, :]
    coef = a * g[meas_idx] * phid[meas_idx]
    return np.abs(((coef[:, None] * wi[:, None] ** 2) / D).sum(0))


def main():
    model = NC.QOIModel()
    z = np.load(WS / "out" / "theta_post_L5.npz", allow_pickle=True)
    theta_post = z["theta_post"]; theta_map = np.median(theta_post, axis=0)
    _, Qmap = model.modes(theta_map)
    meas = rf.reprocess_measured(list(range(1, rf.N_ACCEL_RECORDERS + 1)))
    ch = rf.build_channels(model.R, meas["daq"])
    ch_daq = list(ch.daq); meas_idx = np.where(model.is_meas)[0]

    out = {"design": "per-drive net-CG SHEAR force reconstructed from that drive's MEASURED FRFs (LSQ per-mode "
                     "participation, measured modes) vs the SELECTED shear method (statFEM F(k)) per-drive 95% "
                     "band, 1-octave, one global gain per drive. SHEAR only (normal has no data answer key).",
           "n_measured_modes_fit": int(len(meas_idx)), "zeta": ZETA, "drives": {}}
    summary_cov = {name: [] for _, name in AXES}
    for key, (label, dax) in DRIVES.items():
        p = CACHE_DIR / f"{key}.npz"
        if not p.exists():
            continue
        c = np.load(p, allow_pickle=True)
        cdaq = [int(d) for d in c["daq"]]; H1 = np.asarray(c["H1"]); fc = np.asarray(c["freqs"], float)
        dxyz = tuple(float(x) for x in c["xyz"])
        common = [d for d in cdaq if d in ch_daq]
        s_rows = np.array([ch.rows[ch_daq.index(d)] for d in common])
        H1c = np.array([H1[cdaq.index(d)] for d in common])                # (Ns, Nf)
        a, phid = fit_participation(model, Qmap, s_rows, dxyz, dax, H1c.T, fc, meas_idx, model.meas_f)
        out["drives"][label] = {"n_common_sensors": len(common), "drive_axis": dax}
        for axis, name in AXES:
            ans = answer_key(model, axis, Qmap, a, phid, meas_idx, model.meas_f)
            # per-drive band of the SELECTED shear method = statFEM F(k) (QOI-aware smooth discrepancy) WITH phi_drive
            lo, med, hi = per_drive_band(model, theta_post, axis, dxyz, dax, kind="statfem_fk")
            gain = NC.grms(NC.octave_smooth(NC.FGRID, ans)) / (NC.grms(NC.octave_smooth(NC.FGRID, med)) + 1e-300)
            cov = NC.coverage_vs_truth(lo * gain, hi * gain, ans[None, :], NC.FGRID)
            point_ratio = NC.grms(NC.octave_smooth(NC.FGRID, med * gain)) / (NC.grms(NC.octave_smooth(NC.FGRID, ans)) + 1e-300)
            out["drives"][label][name] = {"covered_frac": cov["weighted_coverage"],
                                          "peak_coverage": cov["peak_coverage"],
                                          "energy_wtd_pos_dB_exceed": cov["energy_wtd_pos_dB_exceed"],
                                          "point_grms_ratio_twin_over_answerkey": round(point_ratio, 3),
                                          "global_gain": round(float(gain), 4),
                                          "answerkey_grms_raw": float(NC.grms(ans))}
            summary_cov[name].append((label, cov["weighted_coverage"], float(NC.grms(ans))))
    # summary with a LOW-OBSERVABILITY flag: a drive/component whose answer-key signal is <15% of the median
    # across drives is weakly excited -> its reconstruction is ill-conditioned and its coverage is not meaningful.
    out["summary"] = {}
    for name, v in summary_cov.items():
        if not v:
            continue
        gr = np.array([x[2] for x in v]); med = float(np.median(gr))
        rows = [{"drive": lab, "covered_frac": round(cv, 3), "answerkey_grms_over_median": round(g / (med + 1e-30), 3),
                 "low_observability": bool(g < 0.15 * med)} for lab, cv, g in v]
        strong = [cv for lab, cv, g in v if g >= 0.15 * med]
        out["summary"][name] = {"per_drive": rows,
                                "mean_covered_frac_strong_drives": round(float(np.mean(strong)), 3) if strong else None,
                                "min_covered_frac_strong_drives": round(float(np.min(strong)), 3) if strong else None,
                                "n_strong_drives": len(strong), "n_drives": len(v)}
    (WS / "out" / "heldout_drive.json").write_text(json.dumps(out, indent=2))
    print("HELD-OUT-DRIVE net-CG SHEAR coverage (winning method, per drive):")
    for label in [DRIVES[k][0] for k in DRIVES if (CACHE_DIR / f"{k}.npz").exists()]:
        r = out["drives"][label]
        print(f"  {label:9s} nS={r['n_common_sensors']:3d} | "
              + " | ".join(f"{name}: cov {r[name]['covered_frac']:.2f} peak {r[name]['peak_coverage']:.2f} "
                           f"pt {r[name]['point_grms_ratio_twin_over_answerkey']:.2f}x" for _, name in AXES))
    print("summary:", json.dumps(out["summary"]))


if __name__ == "__main__":
    main()
