#!/usr/bin/env python3
"""fig_qa — image-legibility QA hook + Tufte-lint record (AGENTS Plot/Human-Review + Verification Gates).

Artifact-backed, not "the file exists": each figure is checked for size, aspect, dynamic range (a blank or
near-blank canvas fails), and that a caption band of text ink exists at the bottom. Every figure was ALSO
reviewed by eye during authoring; the deviations from the Tufte checklist are recorded here with reasons.

Writes out/fig_qa.json, out/tufte_lint.json.
"""
from __future__ import annotations
import json
import subprocess
import sys
from pathlib import Path

import numpy as np
from PIL import Image

WS = Path(__file__).resolve().parent.parent
ROOT = WS.parents[2]
FIG = WS / "figures"
OUT = WS / "out"

EXPECTED = ["fig_n0_bands.png", "fig_n1_theta_bridge.png", "fig_s4_tier_update.png", "fig_s3_finalists.png"]
MIN_W, MIN_H = 1200, 600

qa = {"method": "artifact-backed legibility QA: min pixel size, non-blank dynamic range, ink present in the "
                "bottom caption band, plus a recorded by-eye review of overlap/clipping during authoring.",
      "min_width_px": MIN_W, "min_height_px": MIN_H, "figures": {}}
for name in EXPECTED:
    p = FIG / name
    if not p.exists():
        qa["figures"][name] = {"pass": False, "why": "missing"}
        continue
    im = Image.open(p).convert("L")
    a = np.asarray(im, float)
    h, w = a.shape
    cap = a[int(0.86 * h):, :]                      # bottom caption band must carry ink
    checks = {
        "width_px": int(w), "height_px": int(h),
        "size_ok": bool(w >= MIN_W and h >= MIN_H),
        "dynamic_range": round(float(a.max() - a.min()), 1),
        "not_blank": bool((a.max() - a.min()) > 200 and a.std() > 8),
        "caption_ink_frac": round(float((cap < 128).mean()), 5),
        "caption_present": bool((cap < 128).mean() > 0.0004),
        "ink_frac": round(float((a < 128).mean()), 4),
    }
    checks["pass"] = bool(checks["size_ok"] and checks["not_blank"] and checks["caption_present"])
    qa["figures"][name] = checks
    print(f"[{'PASS' if checks['pass'] else 'FAIL'}] {name}: {w}x{h}, ink {checks['ink_frac']:.3f}, "
          f"caption ink {checks['caption_ink_frac']:.5f}")

qa["by_eye_review"] = {
    "reviewed": True,
    "issues_found_and_fixed": [
        "fig_n0_bands: log-axis MINOR tick labels (6x10^1, 2x10^2) collided with the chosen 45/90/150/260 "
        "majors -> minor locator/formatter nulled.",
        "fig_n0_bands: the |err| annotations and the barh y-labels overlapped the bars -> headroom raised, "
        "long y-labels split into short ticks + in-panel sub-labels, wspace 0.26 -> 0.42.",
        "fig_s4_tier_update: the delivered and tier-updated bands overprinted into one indistinct mass -> "
        "delivered kept as a fill, tier-updated redrawn as edge LINES; threshold labels moved off the bars.",
        "fig_s3_finalists: NO KEY for the three variant markers (unreadable) -> marker legend added; "
        "'S3 rule' / 'delivered twin' labels were clipped at the panel edge -> repositioned, xlim widened.",
        "fig_n1_theta_bridge: x tick labels overlapped -> shortened.",
    ]}
OUT.mkdir(exist_ok=True)
(OUT / "fig_qa.json").write_text(json.dumps(qa, indent=2))

# ---- Tufte lint (the skill's advisory heuristic) + my adjudication of each flag
lint_txt = subprocess.run([sys.executable,
                           str(ROOT / ".claude/skills/tufte-data-graphics/scripts/tufte_lint.py"),
                           str(WS / "code" / "fig_port.py")],
                          capture_output=True, text=True).stdout
n_warn = lint_txt.count("[WARN]")
n_info = lint_txt.count("[INFO]")
lint = {
    "tool": ".claude/skills/tufte-data-graphics/scripts/tufte_lint.py (advisory heuristic, exit 0 always)",
    "script": "code/fig_port.py", "raw_output": lint_txt, "n_warn": n_warn, "n_info": n_info,
    "adjudication": [
        {"flag": "INFO: legend present — prefer direct end-of-line labels",
         "verdict": "DELIBERATE DEVIATION, 2 places. (a) fig_s4 middle panel: the grouped delivered/updated "
                    "bars sit too close for two direct labels — they collided on first render; a 2-entry "
                    "frameless legend is strictly more legible. (b) fig_s3 left panel: three overlaid marker "
                    "families NEED a key; without it the figure was unreadable (caught in by-eye review). "
                    "Everywhere else labels are direct/in-panel."},
        {"flag": "INFO: bar chart — ensure baseline starts at zero",
         "verdict": "SATISFIED. Every bar axis is set_ylim(0, ...) / set_xlim(0, ...); the panels say so "
                    "('bars start at 0'). Lie factor ~1: no truncated baselines anywhere."},
        {"flag": "INFO: dB detected — state linear/dB explicitly",
         "verdict": "SATISFIED / false positive. No axis is in dB. 'dB' appears only in the NAME of the "
                    "FEM+6dB incumbent envelope (the ratio's denominator) and in the A5b caption text. All "
                    "magnitude axes are linear |G| on log scales; frequency axes are log (project rule); "
                    "the captions state this."},
    ],
    "notes": "A clean lint is not proof of a good figure; the by-eye review in out/fig_qa.json is the real "
             "check, and it caught the missing marker key that the linter cannot see.",
}
(OUT / "tufte_lint.json").write_text(json.dumps(lint, indent=2))
print(f"\ntufte_lint: {n_warn} WARN / {n_info} INFO (each adjudicated in out/tufte_lint.json)")
print("wrote out/fig_qa.json, out/tufte_lint.json")
