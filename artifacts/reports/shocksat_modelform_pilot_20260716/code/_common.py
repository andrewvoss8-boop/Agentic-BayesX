#!/usr/bin/env python3
"""_common — read-only import shim for the MODEL-FORM PILOT (Card C, 2026-07-16).

Card A's validated isolation pattern: the study's modules are imported READ-ONLY and reused verbatim,
but several of their functions WRITE into the study workspace by design (package saver, eigensolve log,
score log, candidate-spec dumps). This shim rebinds every write target into THIS workspace before any
study code runs. The study's base packages are reached through SYMLINKS in MY package dir, so the
study's bytes are read but never touched. Reused bytes are hashed in REUSED_code.sha256.

VAULT GUARD (runtime): np.load is wrapped to COUNT any open of a path containing the +XY wide cache
name; every process appends its count to logs/vault_opens.jsonl. The +XY FRF data is NEVER read this
card (would be the program's 4th read; not pre-registered). The femlib cache_meta() metadata-only read
of the NARROW m_xy_990xy.npz (daq/xyz/axis keys, no H1 access) is the established package-building
convention (femlib docstring: rows precomputed, data untouched) and is counted separately for audit.
"""
from __future__ import annotations
import json
import math
import os
import sys
import time

import numpy as np

WS = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
ROOT = os.path.abspath(os.path.join(WS, "..", "..", ".."))
REPORTS = os.path.join(ROOT, "artifacts", "reports")
STUDY = os.path.join(REPORTS, "shocksat_full_spectrum_frf_20260714")
CARD_A = os.path.join(REPORTS, "shocksat_fullspec_exact_completion_20260716")
LOOP06 = os.path.join(REPORTS, "shocksat_true_remodel_loop_20260706")
STUDY_CODE = os.path.join(STUDY, "code")

MY_OUT = os.path.join(WS, "out")
MY_PKGD = os.path.join(WS, "data", "packages_mf")
MY_FIGS = os.path.join(WS, "figures")
MY_LOGS = os.path.join(WS, "logs")
MY_SPECD = os.path.join(MY_OUT, "candidate_specs")
PARTD = os.path.join(MY_OUT, "partials")
EIG_LOG = os.path.join(MY_OUT, "eigensolve_log.jsonl")
RUN_LOG = os.path.join(MY_OUT, "runtime_log.jsonl")

DEV_KEYS = ["m_xpos_990x", "m_zpos_990z", "m_ypos_990y", "m_zpos_900z"]
A1_FOLDS = {"m_xpos_990x": 0.27383077524106014, "m_zpos_990z": 0.4981758785260245,
            "m_ypos_990y": -0.0019679768987999383, "m_zpos_900z": -0.3153000782114738}
CLASSES = ["connectivity", "mesh_density", "element_formulation", "geometry", "property_control"]

for _d in (MY_OUT, MY_PKGD, MY_FIGS, MY_LOGS, MY_SPECD, PARTD):
    os.makedirs(_d, exist_ok=True)

# ------------------------------------------------------------------ vault guard (before any np.load use)
_VAULT_OPENS = {"wide": 0, "narrow_meta": 0}
_np_load = np.load


def _guarded_load(path, *a, **kw):
    p = str(path)
    if "m_xy_990xy_wide" in p:
        _VAULT_OPENS["wide"] += 1
    elif "m_xy_990xy" in p:
        _VAULT_OPENS["narrow_meta"] += 1
    return _np_load(path, *a, **kw)


np.load = _guarded_load


def flush_vault_guard(step="?"):
    with open(os.path.join(MY_LOGS, "vault_opens.jsonl"), "a") as f:
        f.write(json.dumps({"step": step, "xy_wide_opens": _VAULT_OPENS["wide"],
                            "xy_narrow_meta_opens": _VAULT_OPENS["narrow_meta"],
                            "ts": time.strftime("%Y-%m-%dT%H:%M:%S")}) + "\n")


def _link_base_packages():
    src = os.path.join(STUDY, "data", "packages_wide")
    n = 0
    for fn in sorted(os.listdir(src)):
        if fn.endswith(".npz"):
            dst = os.path.join(MY_PKGD, fn)
            if not os.path.lexists(dst):
                os.symlink(os.path.join(src, fn), dst)
                n += 1
    return n


_link_base_packages()

# ------------------------------------------------------------------ read-only imports of reused code
sys.path.insert(0, STUDY_CODE)
import wide_package as WP                          # noqa: E402
import wide_candidates as WC                       # noqa: E402
import wscore_wide as SW                           # noqa: E402
import wide_forward as WFW                         # noqa: E402

F = WP.F                                            # femlib (true-remodel loop), read-only
ACT = WC.ACT                                        # actions grammar (true-remodel loop), read-only


def log_eig(tag, cid, n_dof, t_s):
    rec = {"tag": tag, "cid": cid, "n_dof": int(n_dof), "t_s": round(float(t_s), 1),
           "ts": time.strftime("%Y-%m-%dT%H:%M:%S")}
    with open(EIG_LOG, "a") as f:
        f.write(json.dumps(rec) + "\n")
    return rec


def redirect_writes():
    """Rebind every reused-module write target into THIS workspace. Idempotent."""
    WP.PKGD = MY_PKGD
    WC.PKGD = MY_PKGD
    WC.SPECD = MY_SPECD
    WC.log_eig = log_eig
    SW.SLOG = os.path.join(MY_OUT, "score_log.jsonl")
    return {"WP.PKGD": WP.PKGD, "WC.PKGD": WC.PKGD, "WC.SPECD": WC.SPECD, "SW.SLOG": SW.SLOG}


redirect_writes()


def log_step(step, active_s, **extra):
    rec = {"step": step, "active_s": round(float(active_s), 1),
           "ts": time.strftime("%Y-%m-%dT%H:%M:%S")}
    rec.update(extra)
    with open(RUN_LOG, "a") as f:
        f.write(json.dumps(rec) + "\n")


def paired_stats(deltas):
    d = np.asarray(list(deltas), float)
    return float(np.mean(d)), float(np.std(d, ddof=1) / np.sqrt(len(d))), [float(x) for x in d]


def assert_finite(obj, where="value"):
    """Fail LOUDLY rather than write a NaN/null statistic (the D17/C8 lesson)."""
    if isinstance(obj, dict):
        for k, v in obj.items():
            assert_finite(v, f"{where}.{k}")
    elif isinstance(obj, (list, tuple)):
        for i, v in enumerate(obj):
            assert_finite(v, f"{where}[{i}]")
    elif isinstance(obj, bool) or obj is None:
        if obj is None:
            raise ValueError(f"NULL at {where} (refusing to write a null statistic)")
    elif isinstance(obj, (int, float, np.floating, np.integer)):
        if not math.isfinite(float(obj)):
            raise ValueError(f"NON-FINITE at {where}: {obj!r}")
    return obj


def score_exact(pkg):
    """Exact-basis LODO score at theta=ones (Card A's score_exact, verbatim logic; windowed +
    measured survey zeta). Returns (agg per band, per-fold dict). NEVER touches the vault."""
    caches = SW.load_caches()
    one = np.ones(len(pkg.free_names))
    bands = ("sub200", "b200_500")
    folds = {}
    for fold in DEV_KEYS:
        tks = [k for k in DEV_KEYS if k != fold]
        rho, bm = SW._train_warp(pkg, one, tks, caches, True, None, None)
        fmask = None
        if bm:
            fm = np.zeros(len(caches[fold]["freqs"]), bool)
            for tk, mmask in bm.items():
                if mmask.shape[0] == fm.shape[0]:
                    fm |= mmask
            fmask = fm if fm.sum() >= SW.MIN_BAND else None
        graded = SW._grade_bands(pkg, one, fold, caches[fold], rho, fmask, True, None, None, None)
        folds[fold] = {b: graded[b].get("P1p") for b in bands}
    agg = {}
    for b in bands:
        vals = [folds[f][b] for f in DEV_KEYS if folds[f][b] is not None]
        agg[b] = float(np.mean(vals)) if len(vals) == len(DEV_KEYS) else None
    return agg, folds


def now():
    return time.strftime("%Y-%m-%dT%H:%M:%S")
