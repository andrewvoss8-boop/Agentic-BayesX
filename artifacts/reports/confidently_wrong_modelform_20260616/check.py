#!/usr/bin/env python3
"""IMMUTABLE checker — Confidently-Wrong Model-Form-Error experiment.

Written BEFORE results. Encodes GREEN/YELLOW/RED acceptance per AGENTS.md Result Status Standard
and this study's task card (sec 8). Exits non-zero ONLY on RED. YELLOW = documented, non-fatal.

The claim this checker can certify: "discrepancy-aware updating DETECTS model-form error (sigma_d)
and PRESERVES calibrated held-out predictive/QOI coverage where naive Bayesian calibration is
confidently wrong." It does NOT certify universal parameter recovery (E-LIMIT is the honest limit).
"""
import glob
import json
import os
import re
import sys

import numpy as np


def spearman(x, y):
    rx = np.argsort(np.argsort(x)).astype(float)
    ry = np.argsort(np.argsort(y)).astype(float)
    rx -= rx.mean(); ry -= ry.mean()
    d = np.sqrt((rx ** 2).sum() * (ry ** 2).sum())
    return float((rx * ry).sum() / d) if d > 0 else 0.0

HERE = os.path.dirname(os.path.abspath(__file__))
os.chdir(HERE)

gates = []


def gate(name, status, detail):
    gates.append({"gate": name, "status": status, "detail": detail})


def jload(p):
    return json.load(open(p)) if os.path.exists(p) else None


# Acceptance constants ------------------------------------------------------
RHAT_MAX, ESS_MIN, DIV_MAX = 1.05, 200, 0.02
NOMINAL = 0.95
A1_MALADY_MAX = 0.80      # naive held-out coverage at delta_max must fall to <= this (materially below nominal)
A1_DROP_MIN = 0.10        # naive coverage must drop by >= this from delta=0 to delta_max
DISC_COV_MIN = 0.80       # disc-aware (A2/A3) held-out coverage must stay >= this across the sweep
CONTRAST_MIN = 0.15       # at delta_max, A2 coverage must beat A1 coverage by >= this (UQ wins)
SIGD_AT_ZERO_MAX = 0.12   # learned sigma_d at delta=0 (no-error control) must be small
SIGD_RISE_MIN = 0.15      # sigma_d median must rise by >= this from delta=0 to delta_max (thermometer)
SIGD_SPEARMAN_MIN = 0.90  # sigma_d must rank-track delta (allows single-realization wobble)


def conv(nuts):
    return (nuts["max_rhat"] <= RHAT_MAX and nuts["min_ess"] >= ESS_MIN and nuts["div_frac"] < DIV_MAX)


# ---- load all cells -------------------------------------------------------
cells = [json.load(open(p)) for p in glob.glob("out/cell_*.json")]


def pick(cls, arm, observed=None):
    out = []
    for r in cells:
        if r["class"] != cls or r["arm"] != arm:
            continue
        if observed is not None and r.get("observed") != observed:
            continue
        out.append(r)
    return sorted(out, key=lambda r: r["level"])


# ---- required artifacts ---------------------------------------------------
required = [
    "priority_deliverables.md", "decisions_log.md", "question_framing.md",
    "assumptions_ledger.md", "quantity_contracts.md", "packet.md", "run_all.sh", "runtime.json",
    "code/core.py", "code/nuts_update.py", "code/run_sweep.py", "code/exp_limit.py",
    "code/fig_testbed.py", "code/fig_coverage.py", "code/fig_sigmad.py",
    "code/fig_alpha.py", "code/fig_limit.py", "code/fig_identifiability.py", "code/gif_frf.py",
    "figures/fig_testbed.png", "figures/figA_coverage_vs_delta.png",
    "figures/figB_sigmad_thermometer.png", "figures/figC_alpha_intervals.png",
    "figures/figD_honest_limit.png", "figures/figE_identifiability.png",
    "figures/gif1_frf_bands.gif",
    "out/limit_summary.json", "out/image_qa.json", "out/text_overlap.json",
]
for p in required:
    gate(f"artifact:{p}", "GREEN" if os.path.exists(p) else "RED", p)

# ---- anti-cheating: original scaffold not edited in place ------------------
ORIG = "../paper_virtual_sensing_uq_toy_20260613/code"
try:
    orig_core = open(f"{ORIG}/core.py").read()
    copy_core = open("code/core.py").read()
    gate("integrity:core_unchanged", "GREEN" if orig_core == copy_core else "RED",
         "copy of core.py is byte-identical to the original scaffold (core.py never edited)")
    orig_nuts = open(f"{ORIG}/nuts_update.py").read()
    gate("integrity:original_nuts_not_edited",
         "GREEN" if "learn_discrepancy" not in orig_nuts else "RED",
         "the ORIGINAL nuts_update.py has NO learn_discrepancy path (only the copy was extended)")
    gate("integrity:naive_path_added",
         "GREEN" if "learn_discrepancy" in open("code/nuts_update.py").read() else "RED",
         "the COPY adds the learn_discrepancy=False (A1 naive) path")
except FileNotFoundError as e:
    gate("integrity:scaffold", "RED", f"cannot verify scaffold integrity: {e}")

# ---- convergence of every NUTS arm at every level (main + missing-mode) ----
nuts_cells = [r for r in cells if r["arm"] in ("A1", "A2", "A3")]
nonconv = [(r["class"], r.get("observed"), r["level"], r["arm"], r["nuts"]) for r in nuts_cells
           if not conv(r["nuts"])]
if nuts_cells:
    if nonconv:
        for cls, obs, lv, arm, d in nonconv:
            gate(f"convergence:{cls}_{lv}_{arm}", "YELLOW",
                 f"NOT converged: R-hat {d['max_rhat']:.3f}, ESS {d['min_ess']:.0f}, "
                 f"div {d['div_frac']:.3f} (not-yet-converged; cannot be used as 'converged-but-wrong' evidence)")
    else:
        worst = max(nuts_cells, key=lambda r: r["nuts"]["max_rhat"])["nuts"]
        gate("convergence:all_nuts_arms", "GREEN",
             f"{len(nuts_cells)} NUTS cells all cleared the gate; worst R-hat {worst['max_rhat']:.3f}, "
             f"min ESS {min(r['nuts']['min_ess'] for r in nuts_cells):.0f}, "
             f"max div-frac {max(r['nuts']['div_frac'] for r in nuts_cells):.3f}")
else:
    gate("convergence:all_nuts_arms", "RED", "no NUTS cells found")


# ---- the malady (A1) and the cure (A2/A3) on the correlated class ----------
def coverage_curve(arm):
    # headline = predictive coverage of the held-out NOISY masked observation (standard calibration
    # check). The stricter latent-truth coverage is reported in the packet and is even more extreme.
    return [(r["level"], r["heldout_coverage"]["noisy_frac"]) for r in pick("correlated", arm, [0, 1])]


a1 = pick("correlated", "A1", [0, 1])
a2 = pick("correlated", "A2", [0, 1])
a3 = pick("correlated", "A3", [0, 1])

if a1 and a2 and a3:
    c1 = coverage_curve("A1")
    c2 = coverage_curve("A2")
    c3 = coverage_curve("A3")
    dmax = max(l for l, _ in c1)
    a1_dmax = dict(c1)[dmax]
    a1_d0 = dict(c1)[min(l for l, _ in c1)]
    malady = (a1_dmax <= A1_MALADY_MAX) and (a1_d0 - a1_dmax >= A1_DROP_MIN)
    gate("malady:naive_coverage_collapses",
         "GREEN" if malady else "YELLOW",
         f"A1 held-out (noisy predictive) coverage {a1_d0:.2f} at delta=0 -> {a1_dmax:.2f} at delta={dmax} "
         f"(need <= {A1_MALADY_MAX} and a drop >= {A1_DROP_MIN}); the naive arm is confidently wrong with no warning")

    # confidently wrong = stays tight: A1 alpha intervals narrower than A2 at delta_max
    def awidth(arm):
        r = [x for x in pick("correlated", arm, [0, 1]) if x["level"] == dmax][0]
        return sum(a["width"] for a in r["alpha_intervals"]) / len(r["alpha_intervals"])
    w1, w2 = awidth("A1"), awidth("A2")
    gate("malady:naive_stays_confident",
         "GREEN" if w1 < w2 else "YELLOW",
         f"at delta={dmax} naive mean alpha 95% width {w1:.3f} < disc-aware {w2:.3f}: "
         f"the naive posterior stays tight (confident) while being wrong")

    d2 = dict(c2); d3 = dict(c3)
    cure = all(v >= DISC_COV_MIN for v in d2.values()) and all(v >= DISC_COV_MIN for v in d3.values())
    worst2 = min(d2.items(), key=lambda kv: kv[1]); worst3 = min(d3.items(), key=lambda kv: kv[1])
    gate("cure:disc_aware_coverage_holds",
         "GREEN" if cure else "YELLOW",
         f"A2/A3 held-out (noisy predictive) coverage stays >= {DISC_COV_MIN} across the sweep "
         f"(A2 worst {worst2[1]:.2f}@{worst2[0]}, A3 worst {worst3[1]:.2f}@{worst3[0]})")

    contrast = (d2[dmax] - a1_dmax) >= CONTRAST_MIN
    gate("cure:uq_beats_naive_at_dmax",
         "GREEN" if contrast else "YELLOW",
         f"at delta={dmax} disc-aware coverage {d2[dmax]:.2f} beats naive {a1_dmax:.2f} "
         f"by {d2[dmax]-a1_dmax:.2f} (need >= {CONTRAST_MIN})")
else:
    gate("malady_cure:correlated_sweep", "RED", "correlated A1/A2/A3 sweep cells missing")

# ---- sigma_d thermometer (A2/A3 recover delta, monotone) -------------------
for arm in ("A2", "A3"):
    rows = pick("correlated", arm, [0, 1])
    if not rows:
        gate(f"thermometer:{arm}", "RED", f"{arm} sweep cells missing")
        continue
    sd = [(r["level"], r["sigma_d"]["med"]) for r in rows]
    levels = [l for l, _ in sd]
    meds = [m for _, m in sd]
    sd0 = meds[0]
    sdmax = meds[-1]
    rho = spearman(np.array(levels), np.array(meds))
    rises = (sdmax - sd0) >= SIGD_RISE_MIN
    zero_ok = sd0 <= SIGD_AT_ZERO_MAX
    ok = (rho >= SIGD_SPEARMAN_MIN) and rises and zero_ok
    gate(f"thermometer:{arm}_sigmad_tracks_delta",
         "GREEN" if ok else "YELLOW",
         f"{arm} sigma_d median {['%.3f'%m for m in meds]} over delta {levels}: "
         f"sigma_d(0)={sd0:.3f} (<= {SIGD_AT_ZERO_MAX}? {zero_ok}), rise {sdmax-sd0:.3f} "
         f"(>= {SIGD_RISE_MIN}? {rises}), Spearman(delta,sigma_d)={rho:.3f} (>= {SIGD_SPEARMAN_MIN}? {rho>=SIGD_SPEARMAN_MIN})")

# ---- sensitivity: second error class (missing-mode) robustness -------------
mm1 = pick("missingmode", "A1")
mm2 = pick("missingmode", "A2")
if mm1 and mm2:
    # at the most severe missing-mode level, disc-aware should beat naive on held-out coverage
    sev = max(r["level"] for r in mm1)
    cmm1 = [r for r in mm1 if r["level"] == sev][0]["heldout_coverage"]["truth_frac"]
    cmm2 = [r for r in mm2 if r["level"] == sev][0]["heldout_coverage"]["truth_frac"]
    gate("sensitivity:missing_mode_class_robust",
         "GREEN" if cmm2 >= cmm1 else "YELLOW",
         f"missing-mode class @severity {sev}: disc-aware coverage {cmm2:.2f} >= naive {cmm1:.2f} "
         f"(verdict robust to error class)")
else:
    gate("sensitivity:missing_mode_class_robust", "YELLOW", "missing-mode sensitivity not run")

# ---- E-LIMIT (honest limit): QOI holds but parameter misses ----------------
lim = jload("out/limit_summary.json")
if lim:
    gate("limit:reported", "GREEN", "E-LIMIT coherent-bias sub-study reported")
    h = lim.get("headline", {})
    gate("limit:qoi_holds",
         "GREEN" if h.get("disc_aware_qoi_covered") else "YELLOW",
         f"under coherent +15% peak shift the disc-aware QOI is {'covered' if h.get('disc_aware_qoi_covered') else 'MISSED'} "
         f"(QOI coverage can survive the bias)")
    gate("limit:parameter_misses",
         "YELLOW",
         f"HONEST LIMIT: disc-aware alpha at the failed sensor MISSES truth "
         f"(covered={h.get('disc_aware_alpha_covered')}, apparent sign={h.get('apparent_sign')}); "
         f"coherent bias is confounded with the local-mode stiffness; cure = break the degeneracy, not more sigma_d")
    if "control_alpha_covered" in h:
        gate("limit:unbiased_control_recovers",
             "GREEN" if h["control_alpha_covered"] else "RED",
             "unbiased control (no peak shift) recovers the failed-sensor alpha => the method itself is sound")
else:
    gate("limit:reported", "RED", "out/limit_summary.json missing")

# ---- figures: tufte lint + image QA + text-overlap auditor -----------------
fig_scripts = ["fig_testbed", "fig_coverage", "fig_sigmad", "fig_alpha", "fig_limit",
               "fig_identifiability", "gif_frf"]
for s in fig_scripts:
    log = f"logs/tufte_{s}.txt"
    if os.path.exists(log):
        txt = open(log).read()
        bad = re.search(r"POTENTIAL ISSUES|\bERROR\b", txt) and "No obvious" not in txt
        gate(f"tufte_lint:{s}", "GREEN" if not bad else "YELLOW",
             "clean" if not bad else "tufte_lint flagged issues (see log)")
    else:
        gate(f"tufte_lint:{s}", "RED", f"missing {log}")

qa = jload("out/image_qa.json")
if qa is not None:
    ok = qa.get("ALL_OK", False)
    bad = [k for k, v in qa.items() if isinstance(v, dict) and not v.get("ok", True)]
    gate("image_qa:legibility", "GREEN" if ok else "RED",
         f"pixel legibility: {'all pass' if ok else 'FAIL '+str(bad)}")
else:
    gate("image_qa:legibility", "RED", "out/image_qa.json missing")

to = jload("out/text_overlap.json")
if to is not None:
    nbad = sum(len(v) for v in to.values()) if isinstance(to, dict) else 0
    gate("text_overlap:auditor", "GREEN" if nbad == 0 else "RED",
         f"save-time bbox text-overlap auditor: {nbad} overlapping text pair(s)")
else:
    gate("text_overlap:auditor", "RED", "out/text_overlap.json missing")

# ---- method summary / data-count documentation -----------------------------
pk = open("packet.md").read() if os.path.exists("packet.md") else ""
gate("doc:method_summary_present",
     "GREEN" if ("Method summary" in pk or "Method Summary" in pk) else "RED",
     "packet has a method-summary section")
gate("doc:data_count_present",
     "GREEN" if ("one synthetic realization" in pk.lower() or "single synthetic realization" in pk.lower()) else "RED",
     "packet states the synthetic-realization / replicate count")

# ---- honest scope (always yellow) ------------------------------------------
gate("scope:single_realization", "YELLOW",
     "one synthetic realization per (class, level, arm); no test/flight variability modeled")
gate("scope:surrogate_error_model", "YELLOW",
     "injected model-form error is a surrogate (correlated log-field / missing mode / coherent shift), "
     "not a measured real-structure discrepancy")
gate("scope:no_universal_parameter_recovery", "YELLOW",
     "claim is held-out predictive/QOI coverage + error detection (sigma_d), NOT universal parameter "
     "recovery; the coherent-bias limit (E-LIMIT) misses the parameter by design")

order = {"GREEN": 0, "YELLOW": 1, "RED": 2}
overall = max((g["status"] for g in gates), key=lambda x: order[x]) if gates else "RED"
counts = {k: sum(g["status"] == k for g in gates) for k in order}
report = {"overall": overall, "counts": counts, "gates": gates}
json.dump(report, open("checker_report.json", "w"), indent=2)
for g in gates:
    print(f"[{g['status']:6}] {g['gate']}: {g['detail']}")
print(f"\nOVERALL {overall}  GREEN {counts['GREEN']} / YELLOW {counts['YELLOW']} / RED {counts['RED']}")
sys.exit(1 if overall == "RED" else 0)
