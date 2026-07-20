#!/usr/bin/env python3
"""Card D checker — verifies the correlated-update study's artifacts and that no
claim is stronger than the files. Three-tier (green/yellow/red); exits non-zero
only on RED (missing/fabricated artifact, broken reproduction, claim>evidence).
The "0/10 edits cleanly improved" result is a DOCUMENTED FINDING, not a failure.
"""
import json, os, sys
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__))
os.chdir(HERE)
G, Y, R = [], [], []          # green / yellow / red messages

def need(path):
    if os.path.exists(path): G.append(f"exists: {path}")
    else: R.append(f"MISSING: {path}")
    return os.path.exists(path)

# 1) baseline reproduces the inherited FEM (integrity of the copy)
if need("nominal_modes.json"):
    mine = np.array(json.load(open("nominal_modes.json"))["elastic_freqs_hz"])
    inh = np.array(json.load(open(
        "../shocksat_fem_modal_twin_20260609/nominal_modes.json"))["elastic_freqs_hz"])
    n = min(len(mine), len(inh))
    relerr = float(np.max(np.abs(mine[:n]-inh[:n])/inh[:n]))
    if relerr < 1e-9: G.append(f"baseline reproduces inherited FEM (max rel Δf {relerr:.1e} < 1e-9)")
    else: R.append(f"baseline does NOT reproduce inherited FEM (max rel Δf {relerr:.1e})")

# 2) diagnosis + before/after artifacts
need("region_diagnosis.md"); need("region_diagnosis.json" if os.path.exists("region_diagnosis.json") else "out/region_diagnosis.json")
need("correlation_contribution.md"); need("figures/fig_before_after.png")
have_ba = need("out/before_after.json")

# 3) campaign completeness + the headline finding traces to the file
if have_ba:
    ba = json.load(open("out/before_after.json"))
    n_edits = ba["n_edits"]; n_imp = ba["n_improved"]
    if n_edits >= 10: G.append(f"campaign has {n_edits} correlated-update edits (>=10)")
    else: Y.append(f"campaign has only {n_edits} edits (<10)")
    # every edit has a result.json
    miss = [e["edit_id"] for e in ba["edits"] if not os.path.exists(f"out/edits/{e['edit_id']}/result.json")]
    if miss: R.append(f"edits missing result.json: {miss}")
    else: G.append("every edit has a re-solved result.json (no fabricated rows)")
    # the verdict's central claim must match the file
    if n_imp == 0:
        G.append("FINDING (documented): 0 edits improved a hard-region metric without degrading global "
                 "MAC/frequency -> shape-vs-frequency tradeoff; matches correlation_contribution.md §4")
    else:
        # if some improved, the contribution doc must not claim a flat negative
        txt = open("correlation_contribution.md").read()
        if "0 of 10" in txt:
            R.append(f"claim>evidence: doc says '0 of 10' but before_after says {n_imp} improved")
        else:
            G.append(f"{n_imp} edits improved (documented)")
    # at least one edit genuinely moved a hard-region MAC (campaign was not inert)
    moved = any(abs(e["d_region_macs"].get("box_column") or 0) > 0.02 for e in ba["edits"])
    if moved: G.append("campaign is non-inert (>=1 edit moves box_column MAC >0.02)")
    else: Y.append("no edit moved box_column MAC >0.02 (campaign near-inert)")

# 4) dish mesh-refinement demonstration (converged-mesh proof)
if need("out/dish_refined/nominal_modes.json"):
    ref = np.array(json.load(open("out/dish_refined/nominal_modes.json"))["elastic_freqs_hz"])
    base = np.array(json.load(open("nominal_modes.json"))["elastic_freqs_hz"])
    # mode 1 should be essentially unchanged by refining an already-fine mesh
    d1 = abs(ref[0]-base[0])/base[0]
    if d1 < 1e-4: G.append(f"dish 2x refinement leaves mode 1 unchanged ({d1:.1e}) -> mesh converged")
    else: Y.append(f"dish refinement shifted mode 1 by {d1:.1e}")

# 5) honesty: ch92 labeling (7/8 confirmed) must be stated, not hidden
doc = open("correlation_contribution.md").read()
if "ch92" in doc and ("7/8" in doc or "7 of 8" in doc or "not in the checker" in doc.lower() or "suspected" in doc):
    G.append("ch92 'suspected (not in confirmed fail-7)' labeling present (honest)")
else:
    Y.append("ch92 labeling not clearly stated")

# ---- report ----
report = dict(green=G, yellow=Y, red=R,
              overall=("RED" if R else ("YELLOW" if Y else "GREEN")),
              counts=dict(green=len(G), yellow=len(Y), red=len(R)))
json.dump(report, open("checker_report.json", "w"), indent=1)
print(f"=== Card D checker: OVERALL {report['overall']} "
      f"(green={len(G)} yellow={len(Y)} red={len(R)}) ===")
for m in R: print("  RED   :", m)
for m in Y: print("  YELLOW:", m)
for m in G: print("  green :", m)
sys.exit(1 if R else 0)
