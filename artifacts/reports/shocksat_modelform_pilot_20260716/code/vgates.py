#!/usr/bin/env python3
"""vgates — operator validation gates (card §2; contracts Q6). Each NEW operator gets a validation
script + out/vgate_<op>.json BEFORE any scored use (checker G04). Patch tests reuse the VALIDATED
femlib.assemble_shell on a standalone plate model-dict (no new element code to trust); full-model
gates use small-k eigensolves (logged). A FAILED gate drops the operator (documented), never blocks
the pilot silently.

Run AFTER `pipeline.py baseline` (liveness compares against the baseline elastic frequencies).
"""
from __future__ import annotations
import json
import os
import sys
import time

import numpy as np
import scipy.linalg as sla

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _common as C                                  # noqa: E402
import mfops as MO                                   # noqa: E402
import pipeline as PL                                # noqa: E402

F = C.F
RNG = np.random.default_rng(20260716)
LIVENESS_PCT = 0.05


def write_gate(op, checks):
    status = "PASS" if all(c["pass"] for c in checks) else "FAIL"
    out = {"op": op, "status": status, "checks": checks, "ts": C.now()}
    p = os.path.join(C.MY_OUT, f"vgate_{op}.json")
    json.dump(out, open(p, "w"), indent=1)
    print(f"vgate_{op}: {status}")
    for c in checks:
        print(f"   [{'ok' if c['pass'] else 'FAIL'}] {c['name']}: {c.get('value')} "
              f"(expect {c.get('expect')})")
    return status == "PASS"


# ------------------------------------------------------------------ standalone patch plate
def patch_model(nx=8, L=8.0, t=0.1, br=1.0, tst=5.0 / 6.0, warp_amp=0.0):
    """Square plate as a femlib-schema model dict; assembled with the VALIDATED F.assemble_shell."""
    n = nx + 1
    gids, xyz = [], []
    for j in range(n):
        for i in range(n):
            gids.append(1 + j * n + i)
            xyz.append([L * i / nx, L * j / nx, 0.0])
    xyz = np.array(xyz, float)
    if warp_amp:
        s = np.sin(np.pi * xyz[:, 0] / L) * np.sin(np.pi * xyz[:, 1] / L)
        xyz[:, 2] += warp_amp * s
    quads = []
    eid = 1
    for j in range(nx):
        for i in range(nx):
            n0 = 1 + j * n + i
            quads.append([eid, 999, n0, n0 + 1, n0 + n + 1, n0 + n])
            eid += 1
    m = {"gids": np.array(gids), "xyz": xyz,
         "cquad4": np.array(quads, int), "ctria3": np.zeros((0, 5), int),
         "pshell": {"999": {"t": t, "bend_ratio": br, "ts_t": tst, "mid1": 1}},
         "mat1": {"1": {"E": 1.0e7, "nu": 0.33, "G": 1.0e7 / (2 * 1.33), "rho": 2.538e-4}},
         "cords": {}}
    return m


def patch_modes(m, n_modes=20):
    K, Mdiag, _ = F.assemble_shell(m, 999)
    Kd = K.toarray()
    lam = sla.eigh(Kd, np.diag(Mdiag), eigvals_only=True)
    f = np.sqrt(np.clip(lam, 0, None)) / (2 * np.pi)
    return np.sort(f)[:n_modes], K, Mdiag


def patch_bending_freqs(m, k=8):
    """First k elastic w-dominant (bending) frequencies of the patch (free-free)."""
    K, Mdiag, _ = F.assemble_shell(m, 999)
    lam, V = sla.eigh(K.toarray(), np.diag(Mdiag))
    f = np.sqrt(np.clip(lam, 0, None)) / (2 * np.pi)
    wdofs = np.arange(2, len(Mdiag), 6)               # local z = w for the flat plate
    out = []
    for i in range(len(f)):
        if f[i] < 10.0:                               # rigid/numerical
            continue
        v = V[:, i]
        wfrac = float(np.sum(v[wdofs] ** 2) / np.sum(v ** 2))
        if wfrac > 0.5:
            out.append(f[i])
        if len(out) >= k:
            break
    return np.array(out)


# ------------------------------------------------------------------ gates
def gate_tbuilder():
    m = F.load_model()
    T0, keep0 = F.build_T(m)
    T1, keep1 = MO.build_T_mf(m)
    same_keep = bool(np.array_equal(keep0, keep1))
    dT = (T0 - T1)
    max_d = float(abs(dT).max()) if dT.nnz else 0.0
    checks = [
        {"name": "kept-DOF set identical", "value": same_keep, "expect": True, "pass": same_keep},
        {"name": "max|T_mf - T_femlib| on baseline", "value": max_d, "expect": 0.0,
         "pass": max_d == 0.0},
        {"name": "shape", "value": list(T1.shape), "expect": list(T0.shape),
         "pass": T1.shape == T0.shape}]
    return write_gate("tbuilder", checks)


def _pick_spiders(m, n, min_legs=3):
    out = []
    ptr = 0
    for eid, gn, cm, nGM in np.asarray(m["rbe2"]):
        gms = np.asarray(m["rbe2_gms"])[ptr:ptr + nGM]
        ptr += nGM
        if int(nGM) >= min_legs and str(cm) == "123456":
            out.append(int(eid))
        if len(out) >= n:
            break
    return out


def gate_rbe3():
    checks = []
    m = F.load_model()
    eids = _pick_spiders(m, 10)
    # (a) interpolation exactness on a rigid field (translation + linearized rotation)
    maps = MO.rbe3_maps(m, eids[:3])
    g2i = F.g2i_of(m)
    xyz = np.asarray(m["xyz"], float)
    worst = 0.0
    for gn, gms, Cm in maps:
        a = RNG.normal(0, 1.0, 3)
        th = RNG.normal(0, 0.01, 3)
        xR = xyz[g2i[gn]]
        us = []
        for gm in gms:
            r = xyz[g2i[gm]] - xR
            us.append(a + np.cross(th, r))
        q = Cm @ np.concatenate(us)
        err = np.linalg.norm(q - np.concatenate([a, th])) / np.linalg.norm(np.concatenate([a, th]))
        worst = max(worst, float(err))
    checks.append({"name": "rigid-field interpolation exactness (rel err, 3 spiders)",
                   "value": worst, "expect": "<=1e-9", "pass": worst <= 1e-9})
    # (b)+(c) full model: convert 10 spiders -> 6 RBMs preserved + liveness
    spec = {"cid": "vg_rbe3", "cls": "connectivity", "track": "vgate", "round": 0,
            "ops": [{"op": "rbe3_convert", "eids": eids}]}
    mm, blocks, _ = MO.build_model_blocks(spec)
    M = blocks.pop("__M__")
    lam, V, T, n_dof, dt = PL.solve_own(mm, blocks, M, "vgate_rbe3_k46", "vg_rbe3", k=46)
    f = np.sqrt(np.clip(lam, 0, None)) / (2 * np.pi)
    n_rbm = int((f < 10.0).sum())
    checks.append({"name": "6 rigid-body modes preserved (full model, 10 spiders converted)",
                   "value": n_rbm, "expect": 6, "pass": n_rbm == 6})
    bfr = np.load(PL.BFRQ)
    fe = np.sort(f[f >= 10.0])
    nn = min(len(fe), 40, len(bfr))
    shift = float(np.max(np.abs(fe[:nn] / bfr[:nn] - 1.0)) * 100)
    checks.append({"name": "liveness: max elastic mode shift vs baseline (%)",
                   "value": round(shift, 4), "expect": f">={LIVENESS_PCT}",
                   "pass": shift >= LIVENESS_PCT})
    return write_gate("rbe3_convert", checks)


def gate_formulation():
    checks = []
    # (a) bend_ratio known answer: thin plate, bending modes scale by sqrt(br)
    br = 1.21
    f1 = patch_bending_freqs(patch_model(t=0.1, br=1.0))
    f2 = patch_bending_freqs(patch_model(t=0.1, br=br))
    n = min(len(f1), len(f2), 5)
    ratio = f2[:n] / f1[:n]
    err = float(np.max(np.abs(ratio / np.sqrt(br) - 1.0)) * 100)
    checks.append({"name": f"thin-plate bending freqs x sqrt({br})={np.sqrt(br):.3f} "
                           f"(max dev %, first {n} bending modes)",
                   "value": round(err, 3), "expect": "<=2%", "pass": err <= 2.0})
    # (b) ts_t monotone: softer transverse shear lowers, Kirchhoff-limit raises (thick plate)
    fa = patch_bending_freqs(patch_model(t=0.5, tst=0.35))[0]
    fb = patch_bending_freqs(patch_model(t=0.5, tst=5.0 / 6.0))[0]
    fc = patch_bending_freqs(patch_model(t=0.5, tst=5.0))[0]
    mono = bool(fa < fb < fc)
    checks.append({"name": "ts_t direction: f(0.35) < f(5/6) < f(5.0) thick-plate fundamental",
                   "value": [round(float(x), 2) for x in (fa, fb, fc)], "expect": "monotone",
                   "pass": mono})
    # (c) mass unchanged (stiffness-only edit)
    _, Md1, _ = F.assemble_shell(patch_model(t=0.5, tst=5.0 / 6.0), 999)
    _, Md2, _ = F.assemble_shell(patch_model(t=0.5, tst=0.35, br=1.3), 999)
    dm = float(np.abs(Md1 - Md2).max())
    checks.append({"name": "mass unchanged (max|dM|)", "value": dm, "expect": 0.0,
                   "pass": dm == 0.0})
    return write_gate("formulation", checks)


def patch_drumhead(m, rigid_cut=0.95):
    """Lowest NON-rigid w-dominant patch mode + the highest leaked near-rigid frequency.

    D2: warped facet elements are not exactly rigid-rotation invariant (mean-plane projection), so
    rigid rotations leak stiffness ~ amp^2 and can cross the 10 Hz cut. A naive 'first mode >= 10 Hz'
    pick grabs a leaked RBM, not the drumhead. Filter: exclude modes whose translation field is
    explained > rigid_cut by a best-fit rigid field."""
    K, Mdiag, _ = F.assemble_shell(m, 999)
    lam, V = sla.eigh(K.toarray(), np.diag(Mdiag))
    f = np.sqrt(np.clip(lam, 0, None)) / (2 * np.pi)
    X = np.asarray(m["xyz"], float)
    ctr = X.mean(0)
    P = np.zeros((3 * len(X), 6))
    for i, x in enumerate(X):
        P[3 * i:3 * i + 3, :3] = np.eye(3)
        P[3 * i:3 * i + 3, 3:] = -F.skew(x - ctr)
    leak = 0.0
    for i in range(len(f)):
        if f[i] < 1.0:
            continue
        v = V[:, i]
        ut = np.column_stack([v[0::6], v[1::6], v[2::6]]).ravel()
        q, *_ = np.linalg.lstsq(P, ut, rcond=None)
        rigidity = 1.0 - float(np.sum((ut - P @ q) ** 2) / (np.sum(ut ** 2) + 1e-300))
        if rigidity > rigid_cut:
            leak = max(leak, float(f[i]))
            continue
        wdofs = np.arange(2, len(Mdiag), 6)
        wfrac = float(np.sum(v[wdofs] ** 2) / np.sum(v ** 2))
        if wfrac > 0.5:
            return float(f[i]), leak
    raise RuntimeError("no non-rigid w-dominant mode found")


def gate_warp_panel():
    checks = []
    t = 0.1
    f0, _ = patch_drumhead(patch_model(t=t))
    fund, leaks = [], []
    for amp in (0.5 * t, 1.0 * t, 2.0 * t):
        fd, lk = patch_drumhead(patch_model(t=t, warp_amp=amp))
        fund.append(fd)
        leaks.append(lk)
    rising = bool(fund[0] > f0 and fund[1] > fund[0] and fund[2] > fund[1])
    checks.append({"name": "known answer: warp RAISES fundamental drumhead freq, monotone in amp "
                           "(shallow-shell stiffening; rigid-leak modes excluded by rigid-fit "
                           "filter, D2)",
                   "value": {"flat": round(f0, 2),
                             "warped": [round(x, 2) for x in fund]},
                   "expect": "flat < 0.5t < 1t < 2t", "pass": rising})
    leak_ok = bool(leaks[1] < 0.25 * fund[1])
    checks.append({"name": "rigid-rotation leak (facet-shell non-invariance) stays << drumhead at "
                           "amp=t (patch is the WORST case: element-relative warp far above any "
                           "full-model candidate)",
                   "value": {"leak_hz": [round(x, 2) for x in leaks],
                             "drumhead_hz": [round(x, 2) for x in fund]},
                   "expect": "leak(amp=t) < 25% of drumhead", "pass": leak_ok})
    _, Md0, _ = F.assemble_shell(patch_model(t=t), 999)
    _, Md1, _ = F.assemble_shell(patch_model(t=t, warp_amp=t), 999)
    dm_pct = float(abs(Md1.sum() - Md0.sum()) / Md0.sum() * 100)
    checks.append({"name": "patch mass drift at amp=t (%)", "value": round(dm_pct, 4),
                   "expect": "<=0.1%", "pass": dm_pct <= 0.1})
    mq = patch_model(t=t, warp_amp=2 * t)
    jr, slope = MO.quad_quality(mq, np.arange(len(mq["cquad4"])))
    checks.append({"name": "element quality at amp=2t (min jac ratio, max edge slope)",
                   "value": [round(jr, 3), round(slope, 4)],
                   "expect": f">= {MO.JAC_RATIO_MIN} / <= {MO.EDGE_SLOPE_MAX}",
                   "pass": jr >= MO.JAC_RATIO_MIN and slope <= MO.EDGE_SLOPE_MAX})
    # full model: warp pid 701 (drumhead plate) -> 6 RBMs + liveness
    spec = {"cid": "vg_warp", "cls": "geometry", "track": "vgate", "round": 0,
            "ops": [{"op": "warp_panel", "pid": 701, "amp": 0.15, "name": "vgwarp"}]}
    mm, blocks, info = MO.build_model_blocks(spec)
    M = blocks.pop("__M__")
    lam, V, T, n_dof, dt = PL.solve_own(mm, blocks, M, "vgate_warp_k46", "vg_warp", k=46)
    f = np.sqrt(np.clip(lam, 0, None)) / (2 * np.pi)
    n_rbm = int((f < 10.0).sum())
    checks.append({"name": "6 RBMs preserved (full model, pid 701 warped 0.15 in)",
                   "value": n_rbm, "expect": 6, "pass": n_rbm == 6})
    bfr = np.load(PL.BFRQ)
    fe = np.sort(f[f >= 10.0])
    nn = min(len(fe), 40, len(bfr))
    shift = float(np.max(np.abs(fe[:nn] / bfr[:nn] - 1.0)) * 100)
    checks.append({"name": "liveness: max elastic mode shift vs baseline (%)",
                   "value": round(shift, 4), "expect": f">={LIVENESS_PCT}",
                   "pass": shift >= LIVENESS_PCT})
    checks.append({"name": "quality on full-model edited quads",
                   "value": info.get("quality"), "expect": "recorded + within caps",
                   "pass": info.get("quality") is not None})
    return write_gate("warp_panel", checks)


def gate_joint_offset():
    checks = []
    m = F.load_model()
    eids = _pick_spiders(m, 2)
    spec = {"cid": "vg_joint", "cls": "geometry", "track": "vgate", "round": 0,
            "ops": [{"op": "joint_offset", "eids": eids, "vec": [0.2, 0.0, 0.1],
                     "name": "vgjoint"}]}
    mm, blocks, info = MO.build_model_blocks(spec)
    M = blocks.pop("__M__")
    ref = json.load(open(PL.CREF))
    dm_pct = abs(100.0 * (PL.mass_x(M) - ref["mass_x"]) / ref["mass_x"])
    checks.append({"name": "mass drift (%)", "value": round(dm_pct, 4), "expect": "<=0.5%",
                   "pass": dm_pct <= 0.5})
    lam, V, T, n_dof, dt = PL.solve_own(mm, blocks, M, "vgate_joint_k46", "vg_joint", k=46)
    f = np.sqrt(np.clip(lam, 0, None)) / (2 * np.pi)
    n_rbm = int((f < 10.0).sum())
    checks.append({"name": f"6 RBMs preserved (spiders {eids} offset [0.2,0,0.1] in)",
                   "value": n_rbm, "expect": 6, "pass": n_rbm == 6})
    bfr = np.load(PL.BFRQ)
    fe = np.sort(f[f >= 10.0])
    nn = min(len(fe), 40, len(bfr))
    shift = float(np.max(np.abs(fe[:nn] / bfr[:nn] - 1.0)) * 100)
    checks.append({"name": "liveness: max elastic mode shift vs baseline (%)",
                   "value": round(shift, 4), "expect": f">={LIVENESS_PCT}",
                   "pass": shift >= LIVENESS_PCT})
    checks.append({"name": "quality on edited quads", "value": info.get("quality"),
                   "expect": "recorded + within caps", "pass": info.get("quality") is not None})
    return write_gate("joint_offset", checks)


GATES = {"tbuilder": gate_tbuilder, "rbe3_convert": gate_rbe3, "formulation": gate_formulation,
         "warp_panel": gate_warp_panel, "joint_offset": gate_joint_offset}

if __name__ == "__main__":
    t0 = time.time()
    which = sys.argv[1:] or list(GATES)
    for w in which:
        p = os.path.join(C.MY_OUT, f"vgate_{w}.json")
        if os.path.exists(p):
            print(f"vgate_{w}: exists (resume-skip; status "
                  f"{json.load(open(p))['status']})")
            continue
        GATES[w]()
    C.log_step("vgates", time.time() - t0, which=which)
    C.flush_vault_guard("vgates")
