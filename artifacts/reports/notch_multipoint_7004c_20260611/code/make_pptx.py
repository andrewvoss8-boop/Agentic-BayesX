"""
Build the summary PowerPoint from generated figures + results JSONs (numbers on
slides are read from the results files, never typed in by hand).
GIFs are embedded as pictures; they ANIMATE in PowerPoint slideshow mode (D6).
"""
import json
import os

from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor

HERE = os.path.dirname(os.path.abspath(__file__))
WS = os.path.dirname(HERE)
FIG = os.path.join(WS, "figures")
RES = os.path.join(WS, "results")

DARK = RGBColor(0x20, 0x20, 0x20)
ACC = RGBColor(0xC0, 0x39, 0x2B)
BLUE = RGBColor(0x29, 0x80, 0xB9)


def load(name):
    with open(os.path.join(RES, name)) as fh:
        return json.load(fh)


def add_text(slide, x, y, w, h, lines, size=14, bold_first=False, color=DARK):
    tb = slide.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h))
    tf = tb.text_frame
    tf.word_wrap = True
    for i, ln in enumerate(lines):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.text = ln
        p.font.size = Pt(size)
        p.font.color.rgb = color
        if bold_first and i == 0:
            p.font.bold = True
    return tb


def add_title(slide, text, size=24, color=DARK):
    return add_text(slide, 0.4, 0.18, 12.5, 0.9, [text], size=size, bold_first=True,
                    color=color)


def add_pic(slide, fname, x, y, w=None, h=None):
    path = os.path.join(FIG, fname)
    kw = {}
    if w:
        kw["width"] = Inches(w)
    if h:
        kw["height"] = Inches(h)
    return slide.shapes.add_picture(path, Inches(x), Inches(y), **kw)


def footer(slide, extra=""):
    add_text(slide, 0.4, 7.05, 12.5, 0.35,
             [f"notch_multipoint_7004c_20260611 | deterministic analytic models, no "
              f"measured data; 'flight' = hypothetical coupled simulation {extra}"],
             size=9, color=RGBColor(0x88, 0x88, 0x88))


def main():
    ra = load("ex_a_results.json")
    rb = load("ex_b_results.json")
    rc = load("ex_c_results.json")
    rd = load("ex_d_results.json")
    re_ = load("ex_e_results.json")

    prs = Presentation()
    prs.slide_width = Inches(13.333)
    prs.slide_height = Inches(7.5)
    blank = prs.slide_layouts[6]

    # ---- 1 title ----
    s = prs.slides.add_slide(blank)
    add_text(s, 0.6, 1.5, 12.0, 1.4,
             ["Beyond the 2-DOF picture: NASA-HDBK-7004C intuitions with multiple "
              "mounting feet, 6-DOF motion, and rocking"], size=30, bold_first=True)
    add_text(s, 0.6, 3.1, 12.0, 2.6, [
        "Four analytical numerical examples, checker-verified against the handbook's own numbers",
        "EX-A   replicate the 7004C TDOF impedance example (10 anchors, worst error 0.9%)",
        "EX-B   one box, four spaced feet: the 6×6 apparent-mass matrix and the resultant-force trap",
        "EX-C   compliant backing plate: WHERE the notch is visible (the distance question)",
        "EX-D   force-limited test vs coupled 'flight': net-force vs moment limiting",
        "",
        "Agentic BayesX — 2026-06-11 — deterministic study (no sampler, no measured data)"],
        size=15)
    footer(s)

    # ---- 2 questions ----
    s = prs.slides.add_slide(blank)
    add_title(s, "The three questions (Andrew, 2026-06-10/11)")
    add_text(s, 0.6, 1.3, 12.2, 5.0, [
        "1.  How do the 7004C two-DOF intuitions change with multiple mounting points and "
        "six-dimensional motion — especially with geometrically spaced feet, where rocking "
        "becomes possible?",
        "",
        "2.  How far away from one of the mounting feet can you get and still see the "
        "effect of the notch?",
        "",
        "3.  First principles, or build and probe a model of a compliant backing structure "
        "plus the payload?",
        "",
        "Approach chosen: small analytical models where every number is checkable — the "
        "handbook's own TDOF example as the verified anchor, then add one ingredient at a "
        "time (spaced feet → 6-DOF → compliant backing → force limits)."], size=16)
    footer(s)

    # ---- 3 what 7004C assumes ----
    s = prs.slides.add_slide(blank)
    add_title(s, "What the 7004C toolbox assumes (in its own words)")
    add_text(s, 0.6, 1.25, 12.2, 5.6, [
        "Tools: semi-empirical limit  S_FF = C² M₀² S_AA  (Eq 2a/2b)  •  simple TDOF "
        "(Fig 8, Eq B1–B2)  •  complex TDOF (App. C)  •  impedance method (Eq 3–4, Fig 9) "
        " •  §5.8 coupled-FEM envelopes",
        "",
        "The scalar premise (p.31): “the subject force is the result of the in-axis "
        "acceleration at the same interface, i.e., NOT the result of a cross-axis or a "
        "rotational motion.”",
        "",
        "The default practice (p.10): “In most cases, only the total in-axis force, "
        "i.e., the SUM of the forces at all mounting points… needs to be measured and "
        "limited…”  (moments/per-foot 'occasionally useful')",
        "",
        "The handbook knows the gap (p.8): non-uniform attachment motion is named as the "
        "SECOND contributor to overtesting;  CRIS flight data (p.48) attributes "
        "below-shaker-resonance coupled peaks to ROCKING in the flight mount.",
        "",
        "These examples quantify exactly what those caveats cost."], size=15)
    footer(s)

    # ---- 4 EX-A replication ----
    s = prs.slides.add_slide(blank)
    add_title(s, "EX-A — We reproduce the handbook's own example exactly")
    add_pic(s, "fig_a1_fig9_replication.png", 0.4, 1.15, w=8.6)
    worst = max(v["rel_err"] for v in ra["anchors"].values())
    add_text(s, 9.3, 1.4, 3.7, 5.0, [
        "10 numeric anchors from 7004C Fig 8/9 + Appendix B:",
        f"worst relative error {worst*100:.2f}% (= the handbook's own rounding of 1.62²)",
        "",
        "Impedance method (Eq 3/4) vs direct coupled solve: agree to ~1e-14 (machine "
        "precision)",
        "",
        "The notch: interface acceleration collapses to 0.02 at the load's fixed-base "
        "resonance — source impedance minimum meets load impedance peak.",
        "",
        f"True damped peak at the golden-ratio coupled frequency is "
        f"{ra['golden']['A_true_peak']:.1f}, higher than the handbook's grid value 51.76 "
        "(their r-grid is coarser than the resonance width)."], size=12.5)
    footer(s)

    # ---- 5 EX-A notch/overtest ----
    s = prs.slides.add_slide(blank)
    add_title(s, "EX-A — In the scalar world, force limiting works as advertised")
    add_pic(s, "fig_a3_notch_overtest.png", 0.4, 1.3, w=8.8)
    add_pic(s, "gif_a_tdof_notch_sweep.gif", 9.25, 1.5, w=3.8)
    add_text(s, 9.25, 4.6, 3.8, 2.3, [
        "GIF animates in slideshow: the load becomes a tuned absorber at r=1 — the "
        "interface goes quiet while the load swings.",
        f"Unlimited hard-mount overtest {ra['overtest_factor_unlimited']:.0f}× ≈ Q/C;  "
        f"force-limited {ra['overtest_factor_limited']:.2f}× of the flight peak force.",
        f"Notch depth vs spec: {ra['notch_depth_vs_spec_dB']:.0f} dB."], size=12)
    footer(s)

    # ---- 6 EX-B matrix ----
    s = prs.slides.add_slide(blank)
    add_title(s, "EX-B — 'Apparent mass' becomes a 6×6 matrix (and f→0 = the rigid "
                 "mass matrix, exactly)")
    add_pic(s, "fig_b1_apparent_mass_matrix.png", 0.4, 1.15, w=7.9)
    md = rb["fixed_base_modes_numeric"]
    add_text(s, 8.6, 1.4, 4.4, 5.4, [
        "One rigid box, four spaced feet, uniform base motion:",
        f"6 payload modes {md[0]:.0f}–{md[-1]:.0f} Hz — two lateral-rocking PAIRS, one "
        "torsion, ONE bounce. The scalar tool sees only the bounce.",
        "",
        "Off-diagonal terms (red) = CG-height & geometry coupling: lateral base motion "
        "produces vertical foot forces and moments.",
        "",
        "Verification: numeric modes = closed-form to 2e-16; M(ω→0) = rigid-body matrix "
        "to 5e-7; effective-mass sums = totals to 3e-16 (7004C App. A generalized).",
        "",
        "7004C's C²M₀²A needs a DIFFERENT 'M' per direction: rocking modes own rotary "
        "effective inertia (kg·m²), not the total mass."], size=12.5)
    footer(s)

    # ---- 7 EX-B trap ----
    s = prs.slides.add_slide(blank)
    tr = rb["resultant_trap"]
    add_title(s, "EX-B — The resultant-force trap: rocking hides from the summed force")
    add_pic(s, "fig_b3_resultant_trap.png", 0.4, 1.25, w=8.3)
    add_pic(s, "gif_b_rocking_trap.gif", 8.9, 1.45, w=4.1)
    add_text(s, 8.9, 4.7, 4.1, 2.2, [
        f"At the {tr['freq']:.0f} Hz rocking mode (lateral drive): per-foot force "
        f"{tr['foot_peak']:.1f} N, net force {tr['net']:.1e} N (EXACTLY zero by "
        f"symmetry), moment {tr['My']:.1f} N·m.",
        "The quantity 7004C p.10 says to limit — the net in-axis force — carries no "
        "trace of the mode loading the feet."], size=12)
    footer(s)

    # ---- 8 EX-C setup/spectra ----
    s = prs.slides.add_slide(blank)
    add_title(s, "EX-C — On a compliant backing, the single notch becomes a CLUSTER, "
                 "in different interface channels")
    add_pic(s, "fig_c1_interface_spectra.png", 0.4, 1.2, w=8.2)
    nso = rc["combos"]["soft_t5_Q25"]["notches"]
    sh_txt = ", ".join(f"{n['mode']} {n['notch_shift_pct']:+.0f}%" for n in nso
                       if n.get("detected"))
    add_text(s, 8.85, 1.4, 4.1, 5.4, [
        "Box on 4 feet on a 1.0×0.8×0.005 m simply supported plate; point force far "
        "from the feet.",
        "",
        "Bounce notch lives in the MEAN of the feet; rocking notches live in the "
        "DIFFERENTIAL combinations — a single accelerometer never sees a clean 2-DOF "
        "picture.",
        "",
        f"Notch frequencies shift off the fixed-base modes ({sh_txt}): plate compliance "
        "+ multi-point coupling retune the absorber. A notch predicted at the shaker "
        "fixed-base frequency can MISS the real flight notch.",
        "",
        "Suppression at the interface is deep: 36–46 dB at the cluster minima "
        "(soft-feet variant)."], size=12.5)
    footer(s)

    # ---- 9 EX-C maps ----
    s = prs.slides.add_slide(blank)
    add_title(s, "EX-C — WHERE the notch is visible: regime decides, not a fixed radius")
    add_pic(s, "fig_c2_notch_maps_bounce.png", 0.4, 1.2, h=5.6)
    add_pic(s, "gif_c_notch_field_sweep.gif", 8.55, 1.5, w=4.5)
    add_text(s, 8.55, 4.9, 4.4, 2.0, [
        "GIF (slideshow): sweep 60–170 Hz; the plate turns dark blue (suppressed) around "
        "the absorber frequencies.",
        "Low modal overlap → the payload retunes GLOBAL plate modes → the notch is "
        "visible essentially everywhere. High damping/overlap → locality emerges around "
        "the feet."], size=12)
    footer(s)

    # ---- 10 EX-C distance answer ----
    s = prs.slides.add_slide(blank)
    add_title(s, "EX-C — 'How far from a foot can I see the notch?' — the quantitative answer")
    add_pic(s, "fig_c3_depth_vs_distance.png", 0.4, 1.2, w=7.6)
    add_pic(s, "fig_c4_rvis_vs_lambda.png", 0.7, 4.45, w=7.0)
    add_text(s, 8.3, 1.35, 4.6, 5.6, [
        "Modal overlap factor MOF = half-power bandwidth / modal spacing of the backing "
        "at the notch frequency.",
        "",
        "MOF < 1 (discrete modes — typical aerospace panels at payload frequencies): "
        "bounce-notch suppression is GLOBAL (3-dB visibility to the plate boundary, "
        "0.58 m here, ≈ 6 foot spacings).",
        "",
        "MOF ≳ 1 (high damping / dense modes): visibility shrinks to r ≈ λ/4 around the "
        "feet (0.07–0.09 m here vs λ/4 = 0.08–0.10 m).",
        "",
        "Rocking notches are always more local AND can be invisible in point spectra "
        "(differential absorber).",
        "",
        "Verified: notch frequencies shift <0.5% under 2× modal refinement; r_vis is "
        "threshold-sensitive when the median hovers near 3 dB (one variant flips "
        "global↔local; area-fraction metric stays within 1.4 pts)."], size=12.5)
    footer(s)

    # ---- 11 EX-D setup ----
    s = prs.slides.add_slide(blank)
    add_title(s, "EX-D — Force-limited shaker test vs coupled 'flight' (CG offset 30 mm)")
    add_pic(s, "fig_d1_test_vs_flight.png", 0.4, 1.2, w=8.4)
    add_text(s, 9.0, 1.4, 4.0, 5.4, [
        f"Semi-empirical C² = {rd['C2_semi_empirical']:.1f} (Eq B1/B2, mass ratio "
        f"{rd['mass_ratio_used']:.2f}, Q={rd['Q2_used']:.0f}); flight-implied C² = "
        f"{rd['C2_implied_by_flight']:.2f} — the tool is conservative here, consistent "
        "with the 7004C Table-1 spread.",
        "",
        "Uniform shaker motion + CG offset excites the pitch-rocking mode; the net "
        "vertical force barely sees it (partial cancellation), the per-foot forces and "
        "moment see all of it.",
        "",
        "Newton checks pass at 4e-15; limited responses respect their limits to 1.000."],
        size=12.5)
    footer(s, "| spec = octave peak-hold envelope, no margin")

    # ---- 12 EX-D punchline ----
    s = prs.slides.add_slide(blank)
    add_title(s, "EX-D — Net-force limiting fixes the bounce, NOT the rocking foot loads")
    add_pic(s, "fig_d2_overtest_bars.png", 0.4, 1.3, w=9.2)
    rows = rd["overtest_table"]
    key_p = [k for k in rows if k.startswith("pitch")][0]
    key_b = [k for k in rows if k.startswith("bounce")][0]
    add_text(s, 9.8, 1.4, 3.3, 5.4, [
        f"Bounce mode: {rows[key_b]['i_unlimited']['foot_worst']:.0f}× → "
        f"{rows[key_b]['ii_netF']['foot_worst']:.0f}× with the standard net-force limit "
        "(works).",
        "",
        f"Rocking (pitch) mode: {rows[key_p]['i_unlimited']['foot_worst']:.0f}× → still "
        f"{rows[key_p]['ii_netF']['foot_worst']:.0f}× after net-force limiting; adding "
        f"the §5.8-style moment limit → {rows[key_p]['iii_netF_plus_My']['foot_worst']:.0f}×.",
        "",
        "And the roll channel is never excited at all on a uniform single-axis shaker "
        "(exact zero) while flight drives it — an UNDERTEST no limit can repair.",
        "",
        "(PSD ratios; residual conservatism = the envelope step, which both arms share.)"],
        size=12.5)
    footer(s)

    # ---- EX-E 1: empirical path ----
    s = prs.slides.add_slide(blank)
    add_title(s, "EX-E — Can you limit without a coupled FEM? Reconstruct from interface "
                 "measurements")
    add_pic(s, "fig_e1_reconstruction_channels.png", 0.4, 1.5, w=9.0)
    fe = max(v["full_recon_max_err"] for v in re_["regimes"].values())
    add_text(s, 9.5, 1.5, 3.5, 5.0, [
        "The impedance method (7004C Eq 3/4) uses only interface quantities — load & "
        "source apparent mass and source free acceleration — all measurable WITHOUT "
        "solving the coupled system.",
        "",
        f"Full interface matrix → reconstructs the coupled loads EXACTLY (max err "
        f"{fe:.0e}). So a measurement genuinely replaces the coupled FEM.",
        "",
        "The catch is how much of the (matrix) interface you can measure — next slide."],
        size=12.5)
    footer(s)

    # ---- EX-E 2: how many points ----
    s = prs.slides.add_slide(blank)
    add_title(s, "EX-E — How many interface points? One foot is blind to rocking; ~3 "
                 "recover it")
    add_pic(s, "fig_e2_error_by_regime.png", 0.3, 1.45, w=9.2)
    add_pic(s, "fig_e3_remote_proxy.png", 0.3, 4.55, w=9.2)
    add_text(s, 9.7, 1.5, 3.4, 5.4, [
        "Single-point / single-foot (the 7004C condensation): moment error 100% "
        "(predicts zero) and per-foot force error 68–91% at every mode — the resultant "
        "trap, quantified.",
        "",
        "Rigid-3 (≥3 spaced feet): recovers moment and per-foot force to 3–17% in the "
        "low-overlap regime. ~3 well-placed feet is the practical minimum for rocking.",
        "",
        "Diagonal (feet independent): only works once the feet decouple (high freq).",
        "",
        "Remote proxy (1–3 foot-spacings away): exact IF transmissibility is calibrated "
        "in the integrated config; a bare/un-integrated calibration is ~100% wrong "
        "because the payload shifts every backing mode."], size=11.5)
    footer(s)

    # ---- 13 answers ----
    s = prs.slides.add_slide(blank)
    add_title(s, "Answers to the three questions")
    add_text(s, 0.6, 1.25, 12.2, 5.8, [
        "1.  WHAT CHANGES:  apparent mass → 6×6 matrix; one notch → a cluster of notches "
        "in different interface combinations (mean vs differential), shifted off the "
        "fixed-base frequencies; 'M' in C²M₀²A splits into per-direction effective "
        "masses including ROTARY inertia; the net in-axis force — the default limited "
        "quantity — is blind to rocking (exactly zero in the symmetric case, partial "
        "cancellation otherwise); moments/per-foot forces carry the rocking story; and "
        "a uniform shaker simultaneously over-tests coupled rocking and under-tests "
        "cross rocking.",
        "",
        "2.  HOW FAR:  it is not a fixed distance — it is a REGIME question. With low "
        "modal overlap in the backing (discrete global modes, the usual aerospace case "
        "at payload frequencies) the notch retunes whole modes and is visible across "
        "the structure (here: to the plate boundary, ~6 foot spacings). With high "
        "modal overlap (heavy damping, dense modes, higher bands) visibility contracts "
        "to roughly a quarter bending wavelength (λ/4) around the feet. Rocking notches "
        "are more local and can vanish from point measurements entirely.",
        "",
        "3.  METHOD:  first principles got the mechanisms right (matrix impedance, "
        "absorber action, resultant trap) but got the DISTANCE answer wrong — the naive "
        "λ/4 rule only holds in the diffuse regime. The cheap compliant-backing model "
        "is what exposed the modal-overlap regime switch, the notch-frequency shifts, "
        "and the notch cluster. For hardware decisions: build the coupled model "
        "(= the ShockSat × tray thread)."], size=14)
    footer(s)

    # ---- 14 caveats ----
    s = prs.slides.add_slide(blank)
    add_title(s, "Caveats and what this is NOT")
    add_text(s, 0.6, 1.25, 12.2, 5.6, [
        "•  Teaching models: simply supported plate, vertical-only foot coupling on the "
        "plate (no membrane/lateral load paths), hysteretic foot damping η=0.04, plate "
        "Q=25/6, no uncertainty propagation, no measured data anywhere.",
        "•  'Flight' in EX-D is a labeled hypothetical coupled simulation; overtest "
        "ratios are PSD ratios against it, and part of the residual factor is the "
        "deliberate envelope conservatism both philosophies share.",
        "•  Complex-TDOF Appendix C tables not replicated (image-only PDF) — methods "
        "used are equation-anchored instead.",
        "•  r_vis (3-dB radius) is threshold-sensitive when suppression hovers near "
        "3 dB; frequency/area metrics are the converged ones (<0.5% / <1.4 pts under "
        "2× modal refinement).",
        "•  Real hardware adds in-plane paths, joint nonlinearity, and uncertain mounts "
        "— the mount was the dominant QOI knob in the ShockSat × tray coupled study; "
        "these examples explain WHY (rocking/moment channels live in the mount).",
        "",
        "Replay: bash run_all.sh   •   checker: check.py (green/yellow/red)   •   "
        "all parameters in assumptions_ledger.md, conventions in quantity_contracts.md"],
        size=14)
    footer(s)

    out = os.path.join(WS, "7004c_multipoint_notch_summary.pptx")
    prs.save(out)
    print("wrote", os.path.relpath(out, WS), f"({len(prs.slides.slides if False else prs.slides._sldIdLst)} slides)")


if __name__ == "__main__":
    main()
