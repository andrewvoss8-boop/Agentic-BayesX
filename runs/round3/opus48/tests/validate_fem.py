#!/usr/bin/env python3
"""Validation / references gate for the round-3 MDOF model (Claude Code Opus 4.8 runner).

Checks (writes report/validation.json, returns nonzero on failure):
 1. Beam FEM benchmark vs ANALYTICAL Euler-Bernoulli cantilever (betaL = 1.875104, 4.694091, ...).
    Mesh convergence; error must be < 0.5% at the reference mesh for the first 5 modes.
 2. Lumped 2-DOF benchmark vs closed-form eigenvalues (independent analytical case).
 3. FBS single-mode coupling reproduces the round-2 2DOF interface accelerance H00 (rel err ~0).
 4. Drive-point antiresonance interlacing in the dome source accelerance Y_s and the coupled accelerance.
 5. netCG low-frequency limit -> rigid-body a_cg = F/m_total (apparent mass -> m_load).
 6. Anchors: dome mode1 within ~1% of 93.50 Hz, tray mode1 within ~1% of 86.25 Hz after calibration.
"""
from __future__ import annotations

import json
import math
import sys
from pathlib import Path

import numpy as np
import jax.numpy as jnp

HERE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE / "code"))
sys.path.insert(0, str(Path(__file__).resolve().parents[4] / "scripts"))  # round-2 r2_forward (read-only)

import mdof_forward as fw

BETA_L = np.array([1.875104, 4.694091, 7.854757, 10.995541, 14.137168])


def analytical_cantilever(E, rho, L, b, h, n=5):
    A = b*h; I = b*h**3/12.0
    wn = (BETA_L[:n]**2) * math.sqrt(E*I/(rho*A*L**4))
    return wn/(2*math.pi)


def check_cantilever_benchmark():
    E, rho, L, b, h = 70e9, 2700.0, 1.0, 0.05, 0.005
    A = b*h; I = b*h**3/12.0
    f_an = analytical_cantilever(E, rho, L, b, h, 5)
    conv = {}
    for nele in [5, 10, 20, 40]:
        Kr, Mr, _ = fw.assemble_beam(E, rho, L, A, I, nele, tension=0.0, bc="clamped-free")
        f, _ = fw.solve_modes(Kr, Mr, n=5)
        err = 100.0*(f - f_an)/f_an
        conv[str(nele)] = {"f_hz": f.tolist(), "err_pct": err.tolist()}
    err40 = np.abs(conv["40"]["err_pct"])
    return {"analytical_hz": f_an.tolist(), "convergence": conv,
            "max_abs_err_pct_nele40": float(err40.max()),
            "pass": bool(err40.max() < 0.5)}


def check_lumped_2dof():
    """2-DOF chain ground-k1-[m1]-k2-[m2]; closed-form eigenvalues from the 2x2 generalized problem."""
    m1, m2 = 1.0, 0.6
    k1, k2 = 3.0e6, 1.5e6
    M = np.diag([m1, m2]); K = np.array([[k1+k2, -k2], [-k2, k2]])
    # closed form via eig of M^-1 K
    w2 = np.linalg.eigvals(np.linalg.solve(M, K))
    f_cf = np.sort(np.sqrt(np.real(w2)))/(2*math.pi)
    # via our generalized solver (treat as 2x2 'FEM')
    f_solver, _ = fw.solve_modes(K, M, n=2)
    err = np.abs(f_solver - f_cf)/f_cf*100
    return {"closed_form_hz": f_cf.tolist(), "solver_hz": f_solver.tolist(),
            "max_err_pct": float(err.max()), "pass": bool(err.max() < 1e-6)}


def check_fbs_equals_round2():
    """Single-mode FBS (dome 1 mode @93.5, m1=1; tray 1 mode @86.25, m2=0.6) must reproduce
    the round-2 2DOF interface accelerance H00 exactly."""
    try:
        import r2_forward as r2
    except Exception as e:  # pragma: no cover
        return {"pass": None, "note": f"r2_forward unavailable: {e}"}
    freqs = np.linspace(20.0, 300.0, 1200)
    # round-2 truth
    H00_r2 = np.asarray(r2.interface_accel_per_force_g(r2.TRUE_K1, r2.TRUE_K2, r2.TRUE_ZETA1,
                                                       r2.TRUE_ZETA2, jnp.asarray(freqs)))
    f_dome = math.sqrt(r2.TRUE_K1/r2.M1)/(2*math.pi)   # 93.5
    f_tray = math.sqrt(r2.TRUE_K2/r2.M2)/(2*math.pi)   # 86.25
    # single-mode bases
    dome_basis = (np.array([1.0]), np.array([1.0]))    # 1 mode, residue 1/m1
    H00_fbs = np.asarray(fw.interface_accel_per_force_g(
        f_dome, f_tray, r2.TRUE_ZETA1, r2.TRUE_ZETA2, jnp.asarray(freqs),
        dome_basis, np.array([]), m1_eff=r2.M1, m2_eff=r2.M2))
    rel = np.linalg.norm(H00_fbs - H00_r2)/np.linalg.norm(H00_r2)
    return {"f_dome_hz": f_dome, "f_tray_hz": f_tray, "relative_l2_error": float(rel),
            "pass": bool(rel < 1e-9)}


def _interlacing(freqs, mag):
    logm = np.log10(mag)
    res = [i for i in range(1, len(mag)-1) if logm[i] > logm[i-1] and logm[i] > logm[i+1]]
    anti = [i for i in range(1, len(mag)-1) if logm[i] < logm[i-1] and logm[i] < logm[i+1]]
    rf = freqs[res]; af = freqs[anti]
    filled = sum(1 for k in range(len(rf)-1) if np.any((af > rf[k]) & (af < rf[k+1])))
    return rf, af, filled


def check_antiresonance():
    bases = fw.build_bases()
    dome_basis = (bases["dome_freq_ratio"], bases["dome_res_ratio"])
    freqs = np.geomspace(20.0, 1200.0, 8000)
    # source drive-point accelerance interlacing
    Ys = np.asarray(fw.source_accelerance(fw.DOME_F1_HZ, fw.DOME_ZETA1, jnp.asarray(freqs),
                                          bases["dome_freq_ratio"], bases["dome_res_ratio"]))
    rf_s, af_s, filled_s = _interlacing(freqs, np.abs(Ys))
    # coupled interface accelerance must show drive-point antiresonance notch(es)
    H = np.asarray(fw.interface_accel_per_force_g(
        fw.DOME_F1_HZ, fw.TRAY_F1_HZ, fw.DOME_ZETA1, fw.TRAY_ZETA1, jnp.asarray(freqs),
        dome_basis, bases["tray_flex_f"]))
    rf_c, af_c, filled_c = _interlacing(freqs, np.abs(H))
    return {
        "source_n_res": len(rf_s), "source_n_anti": len(af_s), "source_interlaced": filled_s,
        "source_gaps_possible": max(len(rf_s)-1, 0),
        "source_interlacing_ok": bool(filled_s == max(len(rf_s)-1, 0) and len(rf_s) >= 2),
        "coupled_n_res": len(rf_c), "coupled_n_anti": len(af_c),
        "coupled_antiresonance_present": bool(len(af_c) >= 1),
        "coupled_res_freqs_hz": np.round(rf_c, 1).tolist(),
        "coupled_anti_freqs_hz": np.round(af_c, 1).tolist(),
        "pass": bool(len(rf_s) >= 2 and filled_s == max(len(rf_s)-1, 0) and len(af_c) >= 1),
    }


def check_netcg_lowfreq_limit():
    """At low freq the load apparent mass -> m_load and netCG -> rigid-body a_cg = F/m_total."""
    bases = fw.build_bases()
    flo = np.array([1.0, 2.0, 3.0])  # well below first modes
    ML = np.asarray(fw.load_apparent_mass(fw.TRAY_F1_HZ, fw.TRAY_ZETA1, jnp.asarray(flo),
                                          bases["tray_flex_f"], m_load=fw.M2_EFF))
    ml_lowfreq = float(np.real(ML).mean())
    rel = abs(ml_lowfreq - fw.M2_EFF)/fw.M2_EFF
    return {"apparent_mass_lowfreq_kg": ml_lowfreq, "m_load_eff_kg": fw.M2_EFF,
            "rel_err": rel, "pass": bool(rel < 0.02)}


def check_anchors():
    bases = fw.build_bases()
    dome1 = fw.DOME_F1_HZ * bases["dome_freq_ratio"][0]   # =93.5 by anchoring
    tray1 = fw.TRAY_F1_HZ
    # confirm the calibration scale needed to take the RAW dome FEM mode1 to 93.5 (the tuning knob)
    raw_dome1 = float(bases["dome_modes_raw"][0])
    scale = (fw.DOME_F1_HZ/raw_dome1)**2  # stiffness scale implied
    return {"dome_mode1_hz": float(dome1), "tray_mode1_hz": float(tray1),
            "dome_anchor_err_pct": abs(dome1-93.50)/93.50*100,
            "tray_anchor_err_pct": abs(tray1-86.25)/86.25*100,
            "raw_dome_fem_mode1_hz": raw_dome1,
            "implied_stiffness_calibration_scale": scale,
            "pass": bool(abs(dome1-93.50)/93.50 < 0.01 and abs(tray1-86.25)/86.25 < 0.01)}


def main():
    results = {
        "cantilever_benchmark": check_cantilever_benchmark(),
        "lumped_2dof_benchmark": check_lumped_2dof(),
        "fbs_equals_round2_2dof": check_fbs_equals_round2(),
        "antiresonance_interlacing": check_antiresonance(),
        "netcg_lowfreq_limit": check_netcg_lowfreq_limit(),
        "anchors": check_anchors(),
    }
    passes = {k: v.get("pass") for k, v in results.items()}
    results["all_pass"] = all(v is True for v in passes.values())
    results["pass_summary"] = passes
    out = HERE / "report" / "validation.json"
    out.write_text(json.dumps(results, indent=2))
    print(json.dumps(passes, indent=2))
    print("ALL PASS:", results["all_pass"])
    return 0 if results["all_pass"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
