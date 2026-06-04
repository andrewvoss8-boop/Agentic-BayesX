#!/usr/bin/env python3
"""Build report/packet.pptx (human review layer) for round 3 (Claude Code Opus 4.8 runner).

Embeds: mesh assembly + mode shapes; key MDOF transfer functions; final interface-PSD-vs-spec frame;
netCG headline; netCG-vs-vibe; forcing overlay; sensitivity; resolution; convergence summary; a few GIF
frames. Reads results.json / nuts_diagnostics.json for the headline numbers.
"""
from __future__ import annotations

import json
from pathlib import Path

from pptx import Presentation
from pptx.util import Inches, Pt

HERE = Path(__file__).resolve().parents[1]
OUT = HERE / "report"
FIG = OUT / "figures"
FRAMES = FIG / "gif_frames"


def _txt(slide, text, size=18, top=0.2, left=0.3, width=9.4, height=0.9, bold=True):
    tb = slide.shapes.add_textbox(Inches(left), Inches(top), Inches(width), Inches(height))
    tf = tb.text_frame; tf.word_wrap = True
    p = tf.paragraphs[0]; p.text = text; p.font.size = Pt(size); p.font.bold = bold
    return tb


def _img(slide, path, top=1.1, left=0.4, width=9.2):
    if Path(path).exists():
        slide.shapes.add_picture(str(path), Inches(left), Inches(top), width=Inches(width))


def main():
    res = json.loads((OUT/"results.json").read_text()) if (OUT/"results.json").exists() else {}
    diag = json.loads((OUT/"nuts_diagnostics.json").read_text()) if (OUT/"nuts_diagnostics.json").exists() else {}
    prs = Presentation(); prs.slide_width = Inches(10); prs.slide_height = Inches(7.5)
    blank = prs.slide_layouts[6]

    # Title
    s = prs.slides.add_slide(blank)
    _txt(s, "Round 3 — MDOF source/load + single-interface coupling + netCG QOI", size=24, top=2.2)
    _txt(s, "Claude Code Opus 4.8 runner — review packet", size=16, top=3.2, bold=False)
    conv = diag.get("converged"); nq = res.get("qoi_netCG_3grms_g", {})
    _txt(s, f"NUTS converged: {conv} | worst R-hat {diag.get('worst_rank_split_rhat',{}).get('value','?'):.4f} | "
            f"min ESS bulk {diag.get('min_ess_bulk',{}).get('value','?'):.0f} | div {diag.get('divergences','?')}",
         size=13, top=4.0, bold=False)
    _txt(s, f"netCG 3·GRMS overall q50={nq.get('overall_q50','?')} g; 95% {nq.get('overall_95ci','?')}; 99% {nq.get('overall_99ci','?')}",
         size=13, top=4.5, bold=False)

    slides = [
        ("FEM assembly mesh (undeformed) — SI metres, X-Z meridional plane", FIG/"mesh_assembly.png"),
        ("Dome (source) mode shapes — pressurized, mode 1 = 93.50 Hz", FIG/"modeshapes_dome.png"),
        ("Tray (load) mode shapes — joint bounce 86.25 Hz + panel flex", FIG/"modeshapes_tray.png"),
        ("Key MDOF transfer functions at the interface (validated)", FIG/"component_frfs.png"),
        ("HEADLINE: coupled INTERFACE accelerance response PSD vs spec (final flight)", FRAMES/"frame_flight_10.png"),
        ("netCG PSD (net CG accel of the load) — antiresonance / force-limiting", FIG/"netcg_psd_headline.png"),
        ("netCG QOI per flight vs vibe reference", FIG/"netcg_vs_vibe_reference.png"),
        ("Flight forcing overlay (−6 dB design envelope; 3 dB f2f)", FIG/"flight_forcing_overlay.png"),
        ("Sensitivity: −6 dB offset + Matérn length-scale", FIG/"sensitivity_offset_ell.png"),
        ("Resolution sensitivity (mode-local refinement)", FIG/"resolution_sensitivity.png"),
        ("Posterior recovery vs synthetic truth", FIG/"posterior_recovery.png"),
    ]
    for title, img in slides:
        s = prs.slides.add_slide(blank)
        _txt(s, title, size=16)
        _img(s, img, top=1.05, width=9.2)

    # a strip of GIF frames
    s = prs.slides.add_slide(blank); _txt(s, "Interface-PSD-vs-spec evolution — selected flight frames", size=16)
    xs = [0.2, 3.4, 6.6]; ys = [1.2, 4.2]
    picks = [0, 3, 5, 7, 9, 10]
    for k, fid in enumerate(picks):
        p = FRAMES/f"frame_flight_{fid:02d}.png"
        if p.exists():
            s.shapes.add_picture(str(p), Inches(xs[k % 3]), Inches(ys[k//3]), width=Inches(3.1))

    prs.save(str(OUT/"packet.pptx"))
    print("wrote", OUT/"packet.pptx")


if __name__ == "__main__":
    main()
