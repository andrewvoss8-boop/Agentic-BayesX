#!/usr/bin/env python3
"""_common — read-only import shim for the EXACT-EVIDENCE COMPLETION card.

The study's modules are imported READ-ONLY and reused verbatim (their bytes are hashed in
REUSED_code.sha256; the checker G02 re-verifies them every run). But importing them is NOT enough to be
safe: several of their functions WRITE into the study workspace by design —

  * enrich_wide.enrich()      -> saves packages into wide_candidates.PKGD (the study's data/packages_wide)
  * wide_candidates.log_eig() -> appends to the STUDY's out/eigensolve_log.jsonl
  * wscore_wide.score_*()     -> appends records to the STUDY's out/score_log.jsonl

Calling them unpatched would mutate the reviewed workspace mid-audit. This shim rebinds every write target
into THIS workspace before any of that code runs (decisions_log D0 ambiguity 2). The study's base packages
are reached through SYMLINKS created in MY package dir, so the study's bytes are read but never touched.

Nothing here changes the study's *science* — only where its bytes land.
"""
from __future__ import annotations
import json, os, sys, time

WS = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
ROOT = os.path.abspath(os.path.join(WS, "..", "..", ".."))
REPORTS = os.path.join(ROOT, "artifacts", "reports")
STUDY = os.path.join(REPORTS, "shocksat_full_spectrum_frf_20260714")
REPAIR = os.path.join(REPORTS, "shocksat_full_spectrum_frf_repair_20260716")
STUDY_CODE = os.path.join(STUDY, "code")

MY_OUT = os.path.join(WS, "out")
MY_PKGD = os.path.join(WS, "data", "packages_wide")
MY_FIGS = os.path.join(WS, "figures")
EIG_LOG = os.path.join(MY_OUT, "eigensolve_log.jsonl")
RUN_LOG = os.path.join(MY_OUT, "runtime_log.jsonl")

DEV_KEYS = ["m_xpos_990x", "m_zpos_990z", "m_ypos_990y", "m_zpos_900z"]

for _d in (MY_OUT, MY_PKGD, MY_FIGS):
    os.makedirs(_d, exist_ok=True)


def study_path(*parts):
    """Read-only accessor for study artifacts (never opened for writing anywhere in this card)."""
    return os.path.join(STUDY, *parts)


def repair_path(*parts):
    return os.path.join(REPAIR, *parts)


def _link_base_packages():
    """Symlink the study's theta=1 base packages + its enriched A0 into MY package dir.

    A symlink is created in MY workspace only; the study's .npz bytes are read through it, never written.
    This lets the study's loaders (which resolve packages via PKGD) find the bases while every NEW package
    this card builds lands here.
    """
    src = os.path.join(STUDY, "data", "packages_wide")
    n = 0
    for fn in sorted(os.listdir(src)):
        if not fn.endswith(".npz"):
            continue
        dst = os.path.join(MY_PKGD, fn)
        if not os.path.lexists(dst):
            os.symlink(os.path.join(src, fn), dst)
            n += 1
    return n


_link_base_packages()

# ------------------------------------------------------------------ read-only imports of the study's code
sys.path.insert(0, STUDY_CODE)
import wide_package as WP                          # noqa: E402
import wide_candidates as WC                       # noqa: E402
import wscore_wide as SW                           # noqa: E402
import wide_forward as WFW                         # noqa: E402
import enrich_wide as EW                           # noqa: E402
import arm_c_nuts as AC                            # noqa: E402


def _log_eig(tag, cid, n_dof, t_s):
    """Replacement for wide_candidates.log_eig — same record schema, MY eigensolve log."""
    rec = {"tag": tag, "cid": cid, "n_dof": int(n_dof), "t_s": round(t_s, 1),
           "ts": time.strftime("%Y-%m-%dT%H:%M:%S")}
    with open(EIG_LOG, "a") as f:
        f.write(json.dumps(rec) + "\n")
    return rec


def redirect_writes():
    """Rebind every study write target into THIS workspace. Call before touching study code."""
    WP.PKGD = MY_PKGD                              # package loader + saver
    WC.PKGD = MY_PKGD                              # candidate/enrichment saver
    WC.log_eig = _log_eig                          # eigensolve log
    SW.SLOG = os.path.join(MY_OUT, "score_log.jsonl")   # score records
    return {"WP.PKGD": WP.PKGD, "WC.PKGD": WC.PKGD, "SW.SLOG": SW.SLOG, "WC.log_eig": "_common._log_eig"}


redirect_writes()


def log_step(step, active_s, **extra):
    rec = {"step": step, "active_s": round(active_s, 1), "ts": time.strftime("%Y-%m-%dT%H:%M:%S")}
    rec.update(extra)
    with open(RUN_LOG, "a") as f:
        f.write(json.dumps(rec) + "\n")


def loop_candidates():
    """The 28 loop candidates = the 28 rows of the study's query_log.jsonl (14 agent + 14 random).

    NOT out/candidate_specs/ — that dir holds 29 specs; the extra one (wr3_rnd001) is a recorded BUILD
    FAILURE (out/random_duds.jsonl: "split rule selects no elements of pid 102"). It never produced a
    package or a screening score, so it has no rank to re-order. See decisions_log D0 ambiguity 1.
    """
    rows = []
    with open(study_path("out", "query_log.jsonl")) as f:
        for line in f:
            if line.strip():
                rows.append(json.loads(line))
    return rows


def theta_maps():
    with open(study_path("out", "theta_maps.json")) as f:
        return json.load(f)


def study_exact_freeze():
    with open(study_path("out", "exact_freeze_scores.json")) as f:
        return json.load(f)


def paired_stats(deltas):
    """Paired-fold delta mean and SE, card convention: SE = std(per-fold deltas, ddof=1) / sqrt(4).

    Paired because both arms are scored on the SAME folds, so fold-to-fold difficulty cancels. Verified to
    reproduce the repair's S2 SE (0.0093785) from its 4 per-fold deltas.
    """
    import numpy as np
    d = np.asarray(list(deltas), float)
    return float(np.mean(d)), float(np.std(d, ddof=1) / np.sqrt(len(d))), [float(x) for x in d]


def assert_finite(obj, where="value"):
    """Fail LOUDLY rather than write a NaN. This is the D17/C8 lesson: the study's collector propagated a
    null fold into NaN S1/S2 statistics and its checker validated key-presence, not finiteness."""
    import math
    import numpy as np
    if isinstance(obj, dict):
        for k, v in obj.items():
            assert_finite(v, f"{where}.{k}")
    elif isinstance(obj, (list, tuple)):
        for i, v in enumerate(obj):
            assert_finite(v, f"{where}[{i}]")
    elif isinstance(obj, bool) or obj is None:
        if obj is None:
            raise ValueError(f"NON-FINITE/NULL at {where}: {obj!r} (refusing to write a null statistic)")
    elif isinstance(obj, (int, float, np.floating, np.integer)):
        if not math.isfinite(float(obj)):
            raise ValueError(f"NON-FINITE at {where}: {obj!r} (refusing to write a NaN/Inf statistic)")
    return obj
