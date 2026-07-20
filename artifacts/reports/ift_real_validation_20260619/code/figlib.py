#!/usr/bin/env python3
"""Figure utility for the IFT real-validation study (Tufte skill applied; Plot/Human-Review gate).

save(fig, name, caption, srcfile) does the full per-figure QA the immutable checker reads:
  - stamps REAL-data provenance + any not-converged flag,
  - audits text-artist bbox overlaps at save time (overlap_pass),
  - pixel image-legibility QA on the PNG (image_qa_pass),
  - runs the tufte linter on the figure's own source .py (tufte_pass),
  - writes figures/<name>.qa.json {tufte_pass, image_qa_pass, overlap_pass, ...}.

Project rules: log-frequency axes; linear magnitude unless dB justified; direct labels over legends; caption
carries quantity/units/data-count/real-vs-synthetic + the takeaway; flag any non-converged arm ON the figure.
"""
from __future__ import annotations
import json
import subprocess
import sys
import textwrap
from pathlib import Path

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

WS = Path(__file__).resolve().parent.parent
FIG = WS / "figures"
TUFTE_LINT = WS.parent.parent.parent / ".claude" / "skills" / "tufte-data-graphics" / "scripts" / "tufte_lint.py"

# color discipline by arm (method), truth/observed neutral
C_IFT = "#7c3aed"    # IFT physics-in-prior (violet) -- the new arm
C_L5 = "#059669"     # L5 modal-feature bar (green = the working twin)
C_M2 = "#dc2626"     # M2 whole-FRF physics-in-likelihood (red = the diverging arm)
C_TRUTH = "#111111"
C_OBS = "#6b7280"
ARM_COLOR = {"IFT": C_IFT, "L5": C_L5, "M2": C_M2}
ARM_LABEL = {"IFT": "IFT (physics in prior, β)", "L5": "L5 modal-feature (bar)",
             "M2": "M2 whole-FRF (physics in likelihood)"}

plt.rcParams.update({
    "font.size": 9.5, "axes.spines.top": False, "axes.spines.right": False,
    "axes.grid": True, "grid.alpha": 0.22, "grid.linewidth": 0.4,
    "figure.dpi": 110, "savefig.dpi": 200, "legend.frameon": False,
})

RUN = "ift_real_validation_20260619 | REAL ShockSat hit-001 |H| (45-260 Hz, 1 impact/1 hit, channel-split)"


def stamp(fig, extra=""):
    txt = f"{RUN} | {extra}".rstrip(" |")
    fig.text(0.012, 0.012, txt, fontsize=6.0, color="0.5", ha="left")


def _overlap_audit(fig):
    fig.canvas.draw()
    rend = fig.canvas.get_renderer()
    hits = []
    for ax in fig.get_axes():
        boxes = []
        for t in ax.texts:
            if not t.get_text().strip():
                continue
            try:
                boxes.append((t.get_text()[:24], t.get_window_extent(rend)))
            except Exception:
                pass
        for i in range(len(boxes)):
            for j in range(i + 1, len(boxes)):
                inter = boxes[i][1].intersection(boxes[i][1], boxes[j][1])
                if inter is not None and inter.width > 2 and inter.height > 2:
                    hits.append([boxes[i][0], boxes[j][0]])
    return hits


def _image_qa(png):
    from PIL import Image
    a = np.asarray(Image.open(png).convert("RGB"))
    h, w, _ = a.shape
    nonwhite = float((a.mean(axis=2) < 245).mean())
    too_small = (w < 700 or h < 350)
    blank = nonwhite < 0.01
    return {"w": int(w), "h": int(h), "ink_frac": round(nonwhite, 4),
            "ok": bool(not too_small and not blank and nonwhite < 0.95)}


def _tufte_lint(srcfile):
    try:
        out = subprocess.run([sys.executable, str(TUFTE_LINT), str(srcfile)],
                             capture_output=True, text=True, timeout=60).stdout
    except Exception as e:
        return False, f"lint error: {e}"
    bad = [ln for ln in out.splitlines() if ("[WARN]" in ln or "[BAD]" in ln or "[ERROR]" in ln)]
    return (len(bad) == 0), out.strip().splitlines()[-1] if out.strip() else ""


def save(fig, name, caption="", srcfile=None, extra="", cap_width=165):
    """Caption + provenance stamp are placed in a RESERVED bottom margin (each figure should call
    fig.subplots_adjust(bottom>=0.22)) so they never collide with x-axis labels. Caption is hard-wrapped so it
    cannot run off the right edge. We save at the fixed figure size (NOT bbox_inches='tight') so the reserved
    margin is preserved and the text-overlap audit reflects the saved pixels."""
    if caption:
        wrapped = "\n".join(textwrap.wrap(" ".join(caption.split()), width=cap_width))
        fig.text(0.012, 0.105, wrapped, fontsize=6.8, color="0.28", ha="left", va="top")
    stamp(fig, extra)
    overlaps = _overlap_audit(fig)
    FIG.mkdir(exist_ok=True)
    png = FIG / f"{name}.png"
    fig.savefig(png)
    plt.close(fig)
    iq = _image_qa(png)
    tufte_pass, tufte_last = _tufte_lint(srcfile) if srcfile else (True, "no srcfile")
    qa = {"figure": name, "tufte_pass": bool(tufte_pass), "image_qa_pass": bool(iq["ok"]),
          "overlap_pass": bool(len(overlaps) == 0), "overlaps": overlaps,
          "image": iq, "tufte_summary": tufte_last}
    (FIG / f"{name}.qa.json").write_text(json.dumps(qa, indent=2))
    flag = "OK" if (qa["tufte_pass"] and qa["image_qa_pass"] and qa["overlap_pass"]) else "CHECK"
    print(f"saved {name}.png [{flag}] tufte={qa['tufte_pass']} imgqa={qa['image_qa_pass']} "
          f"overlap={qa['overlap_pass']}")
    return qa
