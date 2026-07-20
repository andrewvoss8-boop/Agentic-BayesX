#!/usr/bin/env python3
"""Immutable checker — ShockSat net-CG force method selection. SHA-locked (see CHECKER.sha256).

Exits NON-ZERO only on RED (missing/fabricated artifact, integrity violation, claim stronger than evidence,
undocumented gate miss). Documented YELLOW findings do NOT abort. Prints GREEN/YELLOW/RED per check + OVERALL.
"""
from __future__ import annotations
import json, sys
from pathlib import Path

WS = Path(__file__).resolve().parent
OUT = WS / "out"; FIG = WS / "figures"
G, Y, R = [], [], []


def g(m): G.append(m)
def y(m): Y.append(m)
def r(m): R.append(m)


def need(p, label):
    if (WS / p).exists() or (OUT / p).exists() or (FIG / p).exists():
        g(f"artifact present: {label} ({p})"); return True
    r(f"MISSING artifact: {label} ({p})"); return False


def jload(p):
    fp = OUT / p
    return json.load(open(fp)) if fp.exists() else None


# ---- Stage 0 ----
for f, lab in [("stage0_qoi_weights.json", "Stage0 QOI weights"),
               ("stage0_observability.json", "Stage0 observability (+Y)"),
               ("stage0_trust.json", "Stage0 trust table"),
               ("stage0_sensitivity.json", "Stage0 unmeasured-sigma sensitivity"),
               ("stage0_validity.json", "Stage0 validity gate")]:
    need(f, lab)

w = jload("stage0_qoi_weights.json")
if w:
    tsx = w["qoi_participation"]["tray_shear_X"]["participation_shape_measured_pct"]
    tnz = w["qoi_participation"]["tray_normal_Z"]["participation_shape_measured_pct"]
    if tsx > tnz:
        g(f"QOI trust contrast holds: shear_X shape-part {tsx}% > normal_Z {tnz}% (shear better-carried)")
    else:
        r(f"trust contrast VIOLATED: shear_X {tsx}% !> normal_Z {tnz}%")

trust = jload("stage0_trust.json")
if trust:
    tz = trust["trust"]["tray_normal_Z"]["shape_only"]["trust_pct"]
    if tz < 80:
        g(f"normal_Z shape-trust {tz}% < 80% -> honestly flagged data-starved (not falsely high)")
    else:
        y(f"normal_Z shape-trust {tz}% unexpectedly high — verify it is not overconfident")

sens = jload("stage0_sensitivity.json")
if sens:
    grid = sens["grid"]["tray_normal_Z"]
    lo = [x["band_factor"] for x in grid if abs(x["SD_A_U"] - 0.40) < 1e-9][0]
    hi = [x["band_factor"] for x in grid if abs(x["SD_A_U"] - 1.60) < 1e-9][0]
    if hi > 2 * lo:
        g(f"sensitivity documented: normal band factor moves {lo}x->{hi}x across SD_A_U (assumption-dominated)")
    else:
        y("sensitivity present but normal band not strongly SD_A_U-dependent — re-read")

obs = jload("stage0_observability.json")
if obs:
    withY = obs["drumhead_band_observability_with_Y"]; noY = obs["drumhead_band_observability_without_Y"]
    y_only = [row["freq_hz"] for row, rn in zip(withY, noY) if row["observed"] and not rn["observed"]]
    if y_only:
        g(f"+Y adds unique drumhead-band frequency observability at {y_only} Hz (documented, not overstated)")
    else:
        y("+Y adds no unique drumhead observability in this run — report honestly")

ms = jload("mesh_screen_summary.json")
partial = sorted((OUT / "mesh_screen").glob("*.json")) if (OUT / "mesh_screen").exists() else []
if ms:
    if "PROXY" in ms.get("proxy", "").upper() and "IMPERFECT" in ms.get("proxy", "").upper():
        g(f"mesh screen COMPLETE + labeled an IMPERFECT PROXY; kept={ms.get('kept_meshes_for_bakeoff')}")
    else:
        r("mesh screen present but not labeled as an imperfect proxy — integrity (§1.1 artifact risk)")
elif partial:
    y(f"mesh screen PENDING (detached, resumable): {len(partial)} edits scored so far, summary not yet written")
else:
    r("MISSING artifact: mesh screen (no partial results either)")

need("fig_stage0_qoi_trust.png", "Stage0 QOI trust figure")

# ---- Stage 2 bake-off (may be pending) ----
sc = jload("bakeoff_scorecard.json"); lmo = jload("leave_modes_out.json")
if sc:
    need("bakeoff_scorecard.json", "Stage2 scorecard")
    conv = sc.get("convergence", {})
    if conv.get("converged"):
        g(f"L5 NUTS CONVERGED (R-hat {conv.get('max_rhat')}, ESS {conv.get('min_ess')}, div {conv.get('divergences')})")
    else:
        y(f"L5 NUTS NOT converged (R-hat {conv.get('max_rhat')}, ESS {conv.get('min_ess')}) — intervals labeled not-trustworthy")
    if lmo:
        # the binding requirement: at least one method must be humble on normal; a falsely-sharp one must be flagged
        nz = lmo["qois"].get("normal_Z", {})
        v_disc = nz.get("L5_freq_discrep", {}).get("verdict"); v_to = nz.get("L5_theta_only", {}).get("verdict")
        if v_disc == "PASS_humble":
            g(f"leave-modes-out: L5_freq_discrep is humble on normal_Z ({v_disc})")
        else:
            y(f"leave-modes-out: no humble method on normal_Z (discrep={v_disc}) — normal delivered as covering band only")
        if v_to == "FAIL_overconfident":
            g("leave-modes-out CAUGHT the false-sharpener (L5_theta_only FAIL_overconfident on normal_Z) = a result")
        else:
            y(f"L5_theta_only leave-modes-out verdict on normal_Z = {v_to} (report honestly)")
    sel = sc.get("selection", {})
    if sel:
        g(f"per-QOI selection recorded (best of N={sc.get('n_configs_compared')}): "
          + ", ".join(f"{k}->{v['winner']}" for k, v in sel.items()))
else:
    y("Stage2 bake-off scorecard not present yet — Stage 0 + harness delivered; bake-off pending (documented)")

# ---- required gate docs ----
for f, lab in [("priority_deliverables.md", "priority deliverables"), ("question_framing.md", "question gate"),
               ("quantity_contracts.md", "quantity contract"), ("assumptions_ledger.md", "assumptions ledger"),
               ("decisions_log.md", "decisions log")]:
    if (WS / f).exists():
        g(f"gate doc present: {lab}")
    else:
        r(f"MISSING gate doc: {lab}")

if (WS / "runtime.json").exists():
    g("runtime.json present")
else:
    y("runtime.json not yet written")

# ---- verdict ----
print("\n=== CHECK RESULTS ===")
for m in G: print(f"  GREEN  {m}")
for m in Y: print(f"  YELLOW {m}")
for m in R: print(f"  RED    {m}")
overall = "RED" if R else ("YELLOW" if Y else "GREEN")
print(f"\nOVERALL {overall}  (green {len(G)} / yellow {len(Y)} / red {len(R)})")
sys.exit(1 if R else 0)
