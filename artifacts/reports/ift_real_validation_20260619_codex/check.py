#!/usr/bin/env python3
"""Checker for IFT real ShockSat validation.

Exit non-zero only on RED. YELLOW findings are documented caveats or honest
negative results that do not get dressed up as success.
"""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

WS = Path(__file__).resolve().parent
REPO = WS.parents[2]
SRC = REPO / "artifacts/reports/statfem_real_validation_20260617"


def sha(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def status_rank(s):
    return {"GREEN": 0, "YELLOW": 1, "RED": 2}.get(s, 2)


checks = []


def add(name, status, detail):
    checks.append({"name": name, "status": status, "detail": detail})


def exists(rel):
    return (WS / rel).exists()


def compare_file(rel):
    a = SRC / rel
    b = WS / rel
    if not a.exists() or not b.exists():
        return False, f"missing source/dest for {rel}"
    ok = sha(a) == sha(b)
    return ok, f"{rel} sha {'matches' if ok else 'differs'}"


for rel in ["code/core.py", "code/score.py"]:
    ok, detail = compare_file(rel)
    add(f"provenance_{rel}", "GREEN" if ok else "RED", detail)

data_files = sorted([p.relative_to(SRC).as_posix() for p in (SRC / "data").glob("*") if p.is_file()])
bad = []
for rel in data_files:
    ok, detail = compare_file(rel)
    if not ok:
        bad.append(detail)
add("provenance_data", "GREEN" if not bad else "RED", "all copied data files byte-identical" if not bad else "; ".join(bad[:5]))

for rel in ["decisions_log.md", "priority_deliverables.md", "method_ift.md", "assumptions_ledger.md", "quantity_contracts.md"]:
    add(f"doc_{rel}", "GREEN" if exists(rel) else "RED", f"{rel} exists")

scorecard_p = WS / "out/scorecard.json"
if scorecard_p.exists():
    sc = json.loads(scorecard_p.read_text())
    add("scorecard_exists", "GREEN", "out/scorecard.json exists")
    add("verdict_generated", "GREEN" if sc.get("verdict") in {"WIN", "ROBUSTNESS-WIN", "TIE", "HONEST_NEGATIVE"} else "RED",
        f"verdict={sc.get('verdict')}")
    add("scorecard_status", sc.get("status", "RED"), sc.get("verdict_reason", "missing reason"))
    ift = sc.get("IFT")
    if ift and ift.get("kind") == "mc" and ift.get("n_splits", 0) >= 25:
        add("ift_25_splits", "GREEN", f"IFT has {ift.get('n_splits')} splits")
    else:
        add("ift_25_splits", "RED", "IFT >=25 split scorecard is missing")
else:
    add("scorecard_exists", "RED", "out/scorecard.json missing")

split_files = sorted((WS / "out").glob("ift_split_*_headline.json"))
mc_file = WS / "out/ift_mc_headline.json"
if mc_file.exists():
    mc = json.loads(mc_file.read_text())
    add("ift_mc_exists", "GREEN", f"IFT MC exists with {mc.get('n_splits')} splits")
    if mc.get("converged_frac", 0) < 1:
        add("ift_convergence", "YELLOW", f"documented non-convergence fraction {1-mc.get('converged_frac', 0):.2f}")
    else:
        add("ift_convergence", "GREEN", "all IFT split runs satisfy convergence gate")
elif split_files:
    add("ift_mc_exists", "RED", f"only split files exist ({len(split_files)}); MC summary missing")
else:
    add("ift_mc_exists", "RED", "no IFT headline result exists")

conv_p = WS / "out/convergence_table.json"
if conv_p.exists():
    conv = json.loads(conv_p.read_text())
    add("convergence_table", "GREEN", f"convergence table exists for arms: {', '.join(conv.get('arms', {}).keys())}")
else:
    add("convergence_table", "RED", "out/convergence_table.json missing")

disc_p = WS / "out/discretization_sensitivity.json"
if disc_p.exists():
    disc = json.loads(disc_p.read_text())
    status = disc.get("status", "RED")
    if disc.get("posterior_invariance_certified") is False and status == "YELLOW":
        add("discretization_sensitivity", "YELLOW", "post-hoc split-0 frequency-grid QOI diagnostic exists; not a certified posterior-invariance rerun")
    else:
        add("discretization_sensitivity", "GREEN" if status == "GREEN" else status, disc.get("reason", "diagnostic exists"))
else:
    add("discretization_sensitivity", "RED", "out/discretization_sensitivity.json missing")

if exists("method_ift.md"):
    txt = (WS / "method_ift.md").read_text()
    add("method_logmag_adaptation", "YELLOW" if "first-order log-magnitude" in txt else "RED",
        "log-magnitude approximation is explicitly documented")

need_figs = [
    "figA_scorecard.png",
    "figB_beta_thermometer.png",
    "figC_heldout_frf_overlay.png",
    "figD_discretization_invariance.png",
    "figE_convergence_table.png",
]
missing_figs = [f for f in need_figs if not (WS / "figures" / f).exists()]
add("figures_exist", "GREEN" if not missing_figs else "RED",
    "required figures exist" if not missing_figs else f"missing figures: {missing_figs}")
qa_p = WS / "out/image_qa.json"
if qa_p.exists():
    qa = json.loads(qa_p.read_text())
    add("image_qa", "GREEN" if qa.get("ALL_OK") else "RED", "image QA ALL_OK" if qa.get("ALL_OK") else "image QA failed")
else:
    add("image_qa", "RED", "out/image_qa.json missing")
overlap_p = WS / "out/text_overlap.json"
if overlap_p.exists():
    overlap = json.loads(overlap_p.read_text())
    add("text_overlap", "GREEN" if not overlap else "RED", "no text overlap hits" if not overlap else f"text overlaps: {list(overlap)}")
else:
    add("text_overlap", "RED", "out/text_overlap.json missing")

deck_p = WS / "slides/ift_real_validation_honest_negative.pptx"
if deck_p.exists() and deck_p.stat().st_size > 0:
    add("deck_pptx", "GREEN", f"deck exists ({deck_p.stat().st_size} bytes)")
else:
    add("deck_pptx", "RED", "slides/ift_real_validation_honest_negative.pptx missing or empty")
deck_manifest_p = WS / "slides/deck_manifest.json"
if deck_manifest_p.exists():
    dm = json.loads(deck_manifest_p.read_text())
    add("deck_manifest", "GREEN" if dm.get("slide_count") == 9 else "RED", f"slide_count={dm.get('slide_count')}")
else:
    add("deck_manifest", "RED", "slides/deck_manifest.json missing")
preview_files = sorted((WS / "slides/preview").glob("slide-*.png"))
montage_p = WS / "slides/deck_preview_montage.webp"
contact_p = WS / "slides/preview/contact_sheet.png"
qa_txt = WS / "slides/visual_qa.txt"
add("deck_rendered_preview", "GREEN" if len(preview_files) == 9 and montage_p.exists() and contact_p.exists() and qa_txt.exists() else "RED",
    f"{len(preview_files)} slide previews; montage exists={montage_p.exists()}; contact sheet exists={contact_p.exists()}; visual QA exists={qa_txt.exists()}")

add("single_hit_scope", "YELLOW", "single hit / single impact; channel-split-only validation")

report = {
    "overall": "GREEN",
    "green": sum(c["status"] == "GREEN" for c in checks),
    "yellow": sum(c["status"] == "YELLOW" for c in checks),
    "red": sum(c["status"] == "RED" for c in checks),
    "checks": checks,
}
if any(c["status"] == "RED" for c in checks):
    report["overall"] = "RED"
elif any(c["status"] == "YELLOW" for c in checks):
    report["overall"] = "YELLOW"

(WS / "checker_report.json").write_text(json.dumps(report, indent=2))
print(f"OVERALL {report['overall']} green={report['green']} yellow={report['yellow']} red={report['red']}")
for c in checks:
    print(f"[{c['status']}] {c['name']}: {c['detail']}")
sys.exit(1 if report["overall"] == "RED" else 0)
