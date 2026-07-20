#!/usr/bin/env python3
"""Immutable checker — plate-test rehearsal. Pre-registered criteria (question_framing.md S1-S6).

GREEN/YELLOW/RED per gate; overall RED if any red (exit 1), else YELLOW if any yellow (exit 0),
else GREEN (exit 0). Locked via CHECKER.sha256 BEFORE science runs; do not modify during the trial.
"""
import hashlib, json, sys
from pathlib import Path

WS = Path(__file__).resolve().parent
res = []


def gate(name, status, msg):
    res.append((name, status, msg))
    print(f"[{status:6s}] {name}: {msg}")


# G0 checker integrity
sha = hashlib.sha256(open(WS / "check.py", "rb").read()).hexdigest()
lock = (WS / "CHECKER.sha256")
if lock.exists():
    want = lock.read_text().split()[0]
    gate("checker_lock", "GREEN" if sha == want else "RED",
         f"sha {sha[:12]} vs locked {want[:12]}")
else:
    gate("checker_lock", "RED", "CHECKER.sha256 missing")

# G1 gate files
for f in ["priority_deliverables.md", "question_framing.md", "quantity_contracts.md",
          "assumptions_ledger.md", "decisions_log.md", "run_all.sh"]:
    gate(f"file_{f}", "GREEN" if (WS / f).exists() else "RED", f)

# G2 summary + runs exist
sp = WS / "out" / "summary.json"
if not sp.exists():
    gate("summary", "RED", "out/summary.json missing")
    print("OVERALL: RED"); sys.exit(1)
S = json.load(open(sp))
arms = S.get("arms", {})
need = {"A0_1sensor": 8, "A1_12sensor": 8, "A2_20sensor": 8, "A3_12jitter": 8,
        "S_sd04": 2, "S_sd16": 2}
for a, n in need.items():
    got = arms.get(a, {}).get("n_runs", 0)
    st = "GREEN" if got >= n else ("YELLOW" if got >= max(2, n // 2) else "RED")
    gate(f"runs_{a}", st, f"{got}/{n} runs")

A0, A1, A2, A3 = (arms.get(k, {}) for k in
                  ["A0_1sensor", "A1_12sensor", "A2_20sensor", "A3_12jitter"])

# S3 convergence (evaluate FIRST: headline arms must be usable)
for a, d in arms.items():
    nc, nr = d.get("n_converged", 0), d.get("n_runs", 0)
    if nr == 0:
        continue
    st = "GREEN" if nc == nr else ("YELLOW" if nc >= max(2, 6 * nr // 8) else "RED")
    gate(f"S3_convergence_{a}", st,
         f"{nc}/{nr} converged (worst rhat {d.get('worst_rhat')}, min ess {d.get('min_ess')})")

# S1 headline buy-down (A1 median vs 3.5x, vs A0 median)
bf1, bf0 = A1.get("median_band_factor"), A0.get("median_band_factor")
if bf1 is None or bf0 is None:
    gate("S1_buydown", "RED", "missing band factors")
else:
    if bf1 <= 3.5:
        gate("S1_buydown", "GREEN", f"A1 median {bf1}x <= 3.5x (A0 {bf0}x)")
    elif bf1 < bf0:
        gate("S1_buydown", "YELLOW", f"A1 median {bf1}x > 3.5x but < A0 {bf0}x — real, smaller buy-down")
    else:
        gate("S1_buydown", "RED", f"A1 {bf1}x >= A0 {bf0}x — no buy-down")

# S2 calibration (A1 coverage)
mc, k85 = A1.get("mean_weighted_coverage"), A1.get("seeds_cov_ge_085", 0)
nok = A1.get("n_converged", 0)
if mc is None:
    gate("S2_coverage", "RED", "missing")
elif mc >= 0.90 and k85 >= min(6, nok):
    gate("S2_coverage", "GREEN", f"mean {mc}, {k85}/{nok} seeds >= 0.85")
elif mc >= 0.80:
    gate("S2_coverage", "YELLOW", f"mean {mc} in [0.80,0.90) — under-coverage documented")
else:
    gate("S2_coverage", "RED", f"mean {mc} < 0.80 — the band lies")

# S4 integrity: A0 must not falsely sharpen
if bf0 is None:
    gate("S4_integrity", "RED", "missing")
elif bf0 >= 4.5:
    gate("S4_integrity", "GREEN", f"A0 median {bf0}x >= 4.5x (no false sharpening)")
elif bf0 >= 3.5:
    gate("S4_integrity", "YELLOW", f"A0 {bf0}x in [3.5,4.5) — mechanism must be documented")
else:
    gate("S4_integrity", "RED", f"A0 {bf0}x < 3.5x — circularity; withdraw")

# S5 robustness: jitter arm
bf3, mc3 = A3.get("median_band_factor"), A3.get("mean_weighted_coverage")
if bf3 is None or mc3 is None:
    gate("S5_jitter", "RED", "missing")
elif bf3 <= 4.2 and mc3 >= 0.85:
    gate("S5_jitter", "GREEN", f"jitter band {bf3}x <= 4.2x, cov {mc3} >= 0.85")
elif mc3 >= 0.70:
    gate("S5_jitter", "YELLOW", f"degraded (band {bf3}x, cov {mc3}) — document mechanism")
else:
    gate("S5_jitter", "RED", f"cov {mc3} < 0.70 — design fragile")

# S6 pooling checkable: A1 median per-target eta posterior sd
sd = A1.get("median_eta_post_sd")
if sd is None:
    gate("S6_pooling", "RED", "missing")
elif sd <= 0.40:
    gate("S6_pooling", "GREEN", f"median eta posterior sd {sd} <= 0.40 (prior 0.80)")
elif sd <= 0.60:
    gate("S6_pooling", "YELLOW", f"{sd} in (0.40,0.60] — partially constrained")
else:
    gate("S6_pooling", "RED", f"{sd} — data adds ~nothing")

# G3 figures + packet + runtime
for f in ["figures/fig_buydown_rehearsed.png", "figures/fig_bands_vs_truth.png",
          "figures/fig_amp_recovery.png", "figures/fig_sensor_data.png",
          "figures/fig_graphical_model.png", "packet.md", "findings.md", "runtime.json"]:
    p = WS / f
    ok = p.exists() and p.stat().st_size > 500
    gate(f"artifact_{Path(f).name}", "GREEN" if ok else "RED", f)

# overall
worst = "GREEN"
if any(s == "YELLOW" for _, s, _ in res):
    worst = "YELLOW"
if any(s == "RED" for _, s, _ in res):
    worst = "RED"
ng = sum(1 for _, s, _ in res if s == "GREEN"); ny = sum(1 for _, s, _ in res if s == "YELLOW")
nr_ = sum(1 for _, s, _ in res if s == "RED")
print(f"OVERALL: {worst} ({ng}G/{ny}Y/{nr_}R)")
json.dump({"overall": worst, "green": ng, "yellow": ny, "red": nr_,
           "gates": [{"gate": g, "status": s, "msg": m} for g, s, m in res]},
          open(WS / "out" / "checker_report.json", "w"), indent=1)
sys.exit(1 if worst == "RED" else 0)
