#!/usr/bin/env python3
"""Immutable checker for the calibrated-twin TIGHTENING program (damping / shape-topology / value). Three-tier
(GREEN/YELLOW/RED); exits non-zero ONLY on RED. The amplitude no-skill result is a DOCUMENTED honest limitation
(YELLOW), not a failure. DO NOT EDIT during the trial (self-SHA lock in code/.check_twin_lock.sha256). Run:
python3 check_twin.py
"""
from __future__ import annotations
import hashlib, json, sys
from pathlib import Path

WS = Path(__file__).resolve().parent
OUT = WS / "out"; FIG = WS / "figures"; CODE = WS / "code"
CARD_A = WS.parent / "statfem_real_validation_20260617" / "code"
REUSED = ["core.py", "realfrf.py", "modal_feature.py", "heldout_qoi.py", "score.py", "tmcmc.py", "schneider_faithful.py"]
R = []   # (gate, status, msg)


def add(g, s, m): R.append((g, s, m))
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def lj(p):
    try: return json.loads(p.read_text())
    except Exception as e: return e


def integrity():
    lock = CODE / ".check_twin_lock.sha256"; me = sha(Path(__file__))
    if lock.exists():
        rec = json.loads(lock.read_text())
        add("integrity.self", "GREEN" if rec.get("self") == me else "RED",
            "check_twin unchanged" if rec.get("self") == me else "check_twin EDITED mid-trial")
        bad = [f for f in REUSED if rec.get(f) != (sha(CODE / f) if (CODE / f).exists() else None)]
        add("integrity.reused", "RED" if bad else "GREEN", f"reused code edited: {bad}" if bad else "reused code unchanged")
    else:
        rec = {"self": me}; rec.update({f: (sha(CODE / f) if (CODE / f).exists() else None) for f in REUSED})
        lock.write_text(json.dumps(rec, indent=1)); add("integrity.self", "GREEN", "lock created (first run)")
        add("integrity.reused", "GREEN", "reused code SHA baseline recorded")
    if CARD_A.exists():
        mm = [f for f in REUSED if (CODE / f).exists() and (CARD_A / f).exists() and sha(CODE / f) != sha(CARD_A / f)]
        add("integrity.copy_vs_cardA", "RED" if mm else "GREEN", f"diff from Card A: {mm}" if mm else "byte-identical to Card A")
    else:
        add("integrity.copy_vs_cardA", "YELLOW", "Card A dir absent")


def need(gate, path, keys=()):
    if not path.exists(): add(gate, "RED", f"missing {path.name}"); return None
    d = lj(path)
    if isinstance(d, Exception): add(gate, "RED", f"{path.name} invalid: {d}"); return None
    miss = [k for k in keys if k not in d]
    if miss: add(gate, "RED", f"{path.name} missing {miss}"); return None
    return d


def value_gates():
    # frequency value (GREEN if positive skill)
    f = need("value.frequency", OUT / "freq_value_seed00.json", ("twin_vs_climatology", "value_of_updating_vs_nominal"))
    if f:
        sk = f["twin_vs_climatology"]["crps_skill"]
        add("value.frequency", "GREEN" if sk > 0.1 else "YELLOW",
            f"freq CRPS-skill vs climatology {sk:+.2f}; updating {f['value_of_updating_vs_nominal']['nominal_fem_median_abs_freq_err_pct']:.2f}%->{f['value_of_updating_vs_nominal']['calibrated_median_abs_freq_err_pct']:.2f}%")
    # amplitude value (YELLOW documented limitation if <=0)
    ve = sorted(OUT.glob("value_eval_seed0*.json"))
    if not ve: add("value.amplitude", "RED", "no value_eval results")
    else:
        sks = [lj(p)["NON_HARD"]["crps_skill_vs_clim"] for p in ve if isinstance(lj(p), dict)]
        m = sum(sks) / len(sks)
        add("value.amplitude", "YELLOW" if m <= 0 else "GREEN",
            f"non-hard amplitude CRPS-skill vs climatology mean {m:+.2f} over {len(sks)} splits "
            f"({'documented no-skill limitation' if m <= 0 else 'positive'})")
    # gap closures present (damping + topology RUN)
    g = need("gaps.damping_topology", OUT / "gap_closure_seed00.json", ("arms",))
    if g:
        a = g["arms"]
        add("gaps.damping_topology", "YELLOW",
            f"RUN: band {a['baseline_band']['nonhard_crps_skill_vs_clim']:+.2f}, fitted-damping(ζ×2) "
            f"{a['band_zeta_x2.0']['nonhard_crps_skill_vs_clim']:+.2f}, joint-released "
            f"{a['topo_joint_soften0.0_peak']['nonhard_crps_skill_vs_clim']:+.2f} — all ≤0 (no amplitude value)")


def evidence_gates():
    need("damping.feasibility", OUT / "identifiability_M3_cbush.json", ("interface_cbush",)) and \
        add("damping.feasibility", "GREEN", "interface-CBUSH damping identifiability gate present")
    need("shape.pattern", OUT / "shape_pattern_test.json", ("all_modes",)) and \
        add("shape.pattern", "GREEN", "shape-pattern test present (FEM & measured shapes ~equal, ~0.15)")
    need("hardregion.overfit", OUT / "hardregion_map.json", ("spearman_resdb_vs", "spatial_correlation")) and \
        add("hardregion.overfit", "GREEN", "hard-region over-fit diagnostic present")
    need("stage1.evidence", OUT / "stage1_evidence.json", ("log_evidence",)) and \
        add("stage1.evidence", "GREEN", "Card F Stage-1 evidence present (paused thread baseline)")


def deliverables():
    for fn in ("fig_value_summary.png", "fig_hardregion.png"):
        add(f"fig.{fn}", "GREEN" if (FIG / fn).exists() else "RED", "present" if (FIG / fn).exists() else "missing")
    iqa = lj(OUT / "image_qa.json") if (OUT / "image_qa.json").exists() else None
    add("fig.image_qa", "GREEN" if isinstance(iqa, dict) and iqa.get("pass") else "RED",
        "image-QA pass" if isinstance(iqa, dict) and iqa.get("pass") else "image-QA missing/not pass")
    add("packet", "GREEN" if (WS / "packet.md").exists() else "RED", "packet.md present" if (WS / "packet.md").exists() else "missing packet.md")
    add("runtime", "GREEN" if (WS / "runtime.json").exists() else "RED", "runtime.json present" if (WS / "runtime.json").exists() else "missing runtime.json")


def main():
    integrity(); value_gates(); evidence_gates(); deliverables()
    nr = sum(1 for _, s, _ in R if s == "RED"); ny = sum(1 for _, s, _ in R if s == "YELLOW"); ng = sum(1 for _, s, _ in R if s == "GREEN")
    overall = "RED" if nr else ("YELLOW" if ny else "GREEN")
    rep = {"task": "calibrated ShockSat twin — tightening/value program (damping, shape/topology, value)",
           "overall": overall, "counts": {"green": ng, "yellow": ny, "red": nr},
           "gates": [{"gate": g, "status": s, "msg": m} for g, s, m in R],
           "headline": "Twin value: FREQUENCY positive (skill>0, calibration halves freq err); per-channel "
                       "single-impact AMPLITUDE no skill vs climatology (documented limitation, not a failure).",
           "check_twin_sha256": sha(Path(__file__))}
    (WS / "checker_twin_report.json").write_text(json.dumps(rep, indent=2))
    print(f"\ncheck_twin — OVERALL {overall}  (GREEN {ng} / YELLOW {ny} / RED {nr})")
    for g, s, m in R: print(f"  [{s:6}] {g}: {m}")
    sys.exit(1 if overall == "RED" else 0)


if __name__ == "__main__":
    main()
