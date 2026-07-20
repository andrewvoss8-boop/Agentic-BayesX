#!/usr/bin/env python3
"""Bilionis direction-check deck (2026-07-13) — CONSOLIDATION ONLY, no new science.

Rev 2 (Andrew): plain language, short bullets, figures tell the story; no internal
numbering schemes (checker triads, study codes, S1/R1 labels) in slide bodies.
Provenance and checker statuses stay in the small-print footers so nothing is
stated stronger than the checkers.

Figure sources (all provenance-labeled COPIES in figures/):
  reuse_L5_param_locations.png   <- shocksat_modelclass_L5_20260619
  reuse_frf_wall_grid.png        <- shocksat_psd_envelope_twin_20260623
  reuse_agentic_funnel.png       <- shocksat_composite_bakeoff_20260702
  reuse_agentic_evidence.png     <- shocksat_composite_bakeoff_20260702
  reuse_netcg_delivery.png       <- shocksat_netcg_method_selection_20260701
  reuse_netcg_trust.png          <- shocksat_netcg_method_selection_20260701
Number sources: study checkers (netcg GREEN 22/0/0; composite YELLOW 57/6/0; true-remodel
YELLOW 11/1/0; frf-damping YELLOW 19/2/0; plate rehearsal RED 28/3/1 where the RED is the
pre-registered falsification), runner comparison rounds 1-2, paper draft v0.3, module draft.
"""
from pathlib import Path
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor

WS = Path(__file__).resolve().parent.parent
FIG = WS / "figures"

DARK = RGBColor(0x1F, 0x4E, 0x79)
GREY = RGBColor(0x66, 0x66, 0x66)
BLACK = RGBColor(0x22, 0x22, 0x22)
GREEN = RGBColor(0x2E, 0x7D, 0x32)
AMBER = RGBColor(0xB0, 0x74, 0x00)


def slide(prs):
    return prs.slides.add_slide(prs.slide_layouts[6])


def title(s, text, size=28):
    tb = s.shapes.add_textbox(Inches(0.35), Inches(0.2), Inches(12.6), Inches(0.85)).text_frame
    tb.word_wrap = True
    p = tb.paragraphs[0]
    p.text = text
    p.font.size = Pt(size)
    p.font.bold = True
    p.font.color.rgb = DARK


def footer(s, text):
    tb = s.shapes.add_textbox(Inches(0.3), Inches(7.05), Inches(12.75), Inches(0.4)).text_frame
    tb.word_wrap = True
    p = tb.paragraphs[0]
    p.text = text
    p.font.size = Pt(8)
    p.font.color.rgb = GREY


def bullets(s, items, left, top, width, height, size=17, gap=10):
    """items: (text, level) or (text, level, color) or plain text."""
    tf = s.shapes.add_textbox(left, top, width, height).text_frame
    tf.word_wrap = True
    for i, it in enumerate(items):
        color, level = BLACK, 0
        if isinstance(it, tuple):
            if len(it) == 3:
                text, level, color = it
            else:
                text, level = it
        else:
            text = it
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.text = text
        p.level = level
        p.font.size = Pt(size - 2 if level else size)
        p.font.color.rgb = color
        p.space_after = Pt(gap)


def main():
    prs = Presentation()
    prs.slide_width, prs.slide_height = Inches(13.333), Inches(7.5)

    # ---------------------------------------------------------------- 1. where we are
    s = slide(prs)
    title(s, "ShockSat Bayesian FEM updating — where we are, how to finish")
    bullets(s, [
        ("Updating a real NASA satellite mock-up FEM with test data — the most complex structure "
         "attempted in this literature.", 0),
        ("Everything is graded on data the model never saw.", 0),
        ("Our predictions bracket the truth, but the bands are wide. The industry standard "
         "(FEM + 6 dB) actually misses the same data.", 0),
        ("The two ideas I bet on — agents remodeling the FEM, and updating damping — "
         "both failed their held-out tests.", 0),
        ("The real contribution: the negative results nobody publishes, plus the validation "
         "harness — on a real NASA structure. Nothing patentable.", 0),
        ("", 0),
        ("Today I need your direction on landing this in ~1 month.", 0, DARK),
    ], Inches(0.35), Inches(1.15), Inches(7.9), Inches(5.6), size=17, gap=12)
    s.shapes.add_picture(str(FIG / "reuse_L5_param_locations.png"),
                         Inches(8.55), Inches(1.05), height=Inches(5.7))
    footer(s, "Image: ShockSat FEM, colored by the 9 calibration groups (copy of "
              "shocksat_modelclass_L5_20260619). All statements trace to checker-backed workspaces.")

    # ---------------------------------------------------------------- 2. the wall
    s = slide(prs)
    title(s, "The wall: updating fixes the peaks, not the shapes")
    s.shapes.add_picture(str(FIG / "reuse_frf_wall_grid.png"), Inches(0.45), Inches(1.05), width=Inches(9.5))
    bullets(s, [
        ("Black = test data. Blue = original FEM. Orange = updated FEM.", 0),
        ("Updating puts the resonance peaks at the right frequencies.", 0),
        ("But the sensor-to-sensor amplitude pattern — set by the mode shapes — stays wrong.", 0),
        ("Match score: 0.27 → 0.34. Industry-usable is ~0.7.", 0),
        ("Nothing we tried closed this gap. It is why the bands are wide.", 0, AMBER),
    ], Inches(10.1), Inches(1.3), Inches(3.1), Inches(5.4), size=14, gap=12)
    footer(s, "Copy of shocksat_psd_envelope_twin_20260623/figures/frf_comparison_grid.png. One global "
              "gain, no per-channel fitting; even borrowing the measured shapes only reaches ~0.7.")

    # ---------------------------------------------------------------- 3. what held-out data said
    s = slide(prs)
    title(s, "What the held-out data said")
    bullets(s, [
        ("One win:", 0, GREEN),
        ("A method with an explicit model-error term gives force predictions that bracket the data at "
         "every held-out drive point. The +6 dB envelope misses up to a third of it.", 1),
        ("The bands are wide because one cluster of modes was never measured — "
         "one more test above 200 Hz would fix that.", 1),
        ("Everything else that looked promising failed when checked:", 0, AMBER),
        ("The tightest method was tight because it was blind — hide information from it and its "
         "band doesn't move. Disqualified.", 1),
        ("Bayesian model selection crowned a clear winner… that predicted no better.", 1),
        ("Inferring the mode shapes predicts best point-by-point — but is overconfident "
         "exactly where there is no data to check it.", 1),
        ("A sensor-placement study promised 35% tighter bands; a full dress rehearsal "
         "delivered none of it.", 1),
    ], Inches(0.4), Inches(1.15), Inches(8.5), Inches(5.7), size=16, gap=10)
    s.shapes.add_picture(str(FIG / "reuse_netcg_delivery.png"), Inches(9.15), Inches(1.3), width=Inches(3.9))
    s.shapes.add_picture(str(FIG / "reuse_netcg_trust.png"), Inches(9.15), Inches(4.2), width=Inches(3.9))
    footer(s, "Figures: delivered force bands vs the +6 dB envelope, and how much of each force component "
              "rests on measured vs unmeasured modes (copies from shocksat_netcg_method_selection_20260701, "
              "checker green). Falsifications: plate_test_rehearsal_20260701, shocksat_composite_bakeoff_20260702.")

    # ---------------------------------------------------------------- 4. agentic remodeling
    s = slide(prs)
    title(s, "Main recent focus: agents remodeling the FEM")
    s.shapes.add_picture(str(FIG / "reuse_agentic_funnel.png"), Inches(0.45), Inches(1.25), width=Inches(4.7))
    s.shapes.add_picture(str(FIG / "reuse_agentic_evidence.png"), Inches(0.45), Inches(4.3), width=Inches(4.7))
    bullets(s, [
        ("The idea: an agent diagnoses where the model is wrong, rebuilds that part, "
         "and the data picks the winner.", 0),
        ("Agents generated ~150 candidate model changes; the best got full solves.", 0),
        ("Bayesian evidence picked a decisive winner (figures, left).", 0),
        ("The winner predicted held-out data no better than the original model — "
         "and no better than random edits.", 0, AMBER),
        ("Ran the loop three ways (model form, mesh, damping). Same answer each time.", 0),
        ("What lasts: the harness caught two ways an agent's score can lie "
         "before we believed them.", 0, GREEN),
    ], Inches(5.45), Inches(1.3), Inches(7.6), Inches(5.5), size=17, gap=14)
    footer(s, "Figures: candidate funnel + evidence ranking (copies from shocksat_composite_bakeoff_20260702). "
              "Three loops: composite bake-off, true remodel loop, damping loop — each pre-registered, "
              "hash-locked checker, random-search control.")

    # ---------------------------------------------------------------- 5. agent lessons (blog)
    s = slide(prs)
    title(s, "What I learned about running AI agents on science  (the blog material)")
    bullets(s, [
        ("Replication catches what one agent hides. One runner faked an “independent” cross-check — "
         "a separate reviewer agent caught it. The critic is the product.", 0),
        ("I ran Claude, GPT, and Cursor head-to-head on the same real task. Everyone passes their own "
         "tests. Only strict outside checks separated them: one copied figures, one couldn't be re-run, "
         "one was clean.", 0),
        ("One train/test split is not enough once an agent chooses what to try next. "
         "You need a locked answer key it can never see, and a budget on how often it can peek.", 0),
        ("The most valuable agent behavior turned out to be an honest “I couldn't do this.”", 0),
        ("These became a reusable set of checks for this class of problem — "
         "that's the blog post, if it's still worth writing.", 0, DARK),
    ], Inches(0.4), Inches(1.3), Inches(12.5), Inches(5.5), size=18, gap=16)
    footer(s, "Sources: runner comparisons (rounds 1-2, 2026-06-02/03: Claude Opus 4.8 / Codex GPT-5.5 / "
              "Cursor Composer 2.5), statFEM replicate-and-extend, FEM build reviews, "
              "anti-overfitting experiment, notes/lessons-learned.md.")

    # ---------------------------------------------------------------- 6. two ways to land
    s = slide(prs)
    title(s, "Two ways to land — both already drafted")
    bullets(s, [
        ("A paper", 0, DARK),
        ("Real structure, real data: one validated win, four documented failures.", 1),
        ("The story: coverage-first validation, and the negatives nobody publishes.", 1),
        ("Target: Data-Centric Engineering.", 1),
    ], Inches(0.45), Inches(1.3), Inches(6.0), Inches(2.6), size=17, gap=10)
    bullets(s, [
        ("A class module   (my lean)", 0, GREEN),
        ("Jupyter virtual lab for a graduate modal-testing class — Dr. Gibert?", 1),
        ("Simple panel first (2 parameters, exact posterior), then ShockSat (9 parameters).", 1),
        ("Runs on a laptop in ~1 minute; teaches held-out honesty and model error.", 1),
    ], Inches(6.85), Inches(1.3), Inches(6.1), Inches(2.6), size=17, gap=10)
    bullets(s, [
        ("Both need the same thing: NASA permission to share the ShockSat data.", 0, AMBER),
    ], Inches(0.45), Inches(5.9), Inches(12.4), Inches(0.6), size=17)
    footer(s, "Paper: artifacts/reports/paper_draft_dce_20260702/paper_draft.md (v0.3). "
              "Module: teaching/bayesian_fem_updating_module/ (draft, verified end-to-end, "
              "not yet cleared for students).")

    # ---------------------------------------------------------------- 7. abstract
    s = slide(prs)
    title(s, "The drafted paper, in one paragraph")
    abstract = (
        "Bayesian model updating is usually demonstrated on simple structures, scored on the same data "
        "used to fit it, and published when it works. We ran a pre-registered validation campaign on a "
        "real, professionally correlated NASA satellite mock-up, with one rule: a 95% prediction band "
        "must contain data the method never saw, must widen when we deliberately hide information from "
        "it, and only then may narrowness decide. One method earned delivery — force bands that contain "
        "the data at five held-out excitation points, where the industry +6 dB envelope does not. Four "
        "celebrated techniques failed the same test: the narrowest method was narrow because it was "
        "blind; Bayesian model selection crowned a winner with zero predictive gain; a sensor-placement "
        "promise vanished in a full rehearsal; inferred mode shapes predicted best and could not be "
        "trusted where the data ran out. We argue the negatives carry most of the engineering "
        "information — and that coverage-first validation transfers to any digital-twin claim."
    )
    bullets(s, [(abstract, 0)], Inches(0.7), Inches(1.5), Inches(12.0), Inches(5.0), size=18, gap=8)
    footer(s, "Condensed in plain language from paper_draft_dce_20260702/paper_draft.md, Abstract (v0.3). "
              "Full version keeps the exact numbers and citations.")

    # ---------------------------------------------------------------- 8. questions
    s = slide(prs)
    title(s, "Your call")
    bullets(s, [
        ("Paper or class module?  I lean module.", 0),
        ("Blog post on the agent lessons — still valuable?  (IP office check first.)", 0),
        ("One last experiment, or stop and write?", 0),
        ("If one: our own MPL test stand — raw, never-correlated data, so agents have real error "
         "to fix. Either agentic remodeling there, or ML-designed testing to collect the most "
         "informative data.", 1),
        ("Authorship and AI disclosure — how do you want it handled?", 0),
        ("NASA data permission blocks both landings — who asks?", 0),
        ("", 0),
        ("Goal: landed in ~1 month.", 0, DARK),
    ], Inches(0.5), Inches(1.4), Inches(12.3), Inches(5.4), size=19, gap=16)
    footer(s, "This deck is consolidation only — no new science; figures are labeled copies; every claim "
              "traces to a study checker. Workspace: artifacts/reports/bilionis_update_20260713/ · "
              "rebuild: python3 code/make_update_deck.py")

    out = WS / "slides" / "bilionis_update_20260713.pptx"
    prs.save(out)
    print("wrote", out, "with", len(prs.slides._sldIdLst), "slides")


if __name__ == "__main__":
    main()
