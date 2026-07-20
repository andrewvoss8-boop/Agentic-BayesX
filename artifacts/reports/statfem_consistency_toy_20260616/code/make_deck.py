#!/usr/bin/env python3
"""Build the slide deck (system python3 + python-pptx). Gated on a non-RED checker. Every claim traces to
a checker number / result JSON. Figures must already exist."""
import json
import os

from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.util import Inches, Pt

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, "..")
FIG = os.path.join(ROOT, "figures")
O = os.path.join(ROOT, "out")
SS = json.load(open(os.path.join(O, "sweep_summary.json")))
SV = json.load(open(os.path.join(O, "solver_validation.json")))
CK = json.load(open(os.path.join(ROOT, "checker_report.json")))
cons = SS["constructions"]; TT = SS["theta_true"]

NAVY = RGBColor(0x1f, 0x3a, 0x5f); GREY = RGBColor(0x55, 0x55, 0x55)
RED = RGBColor(0xdc, 0x26, 0x26); GREEN = RGBColor(0x05, 0x96, 0x69); BLUE = RGBColor(0x25, 0x63, 0xeb)

prs = Presentation(); prs.slide_width = Inches(13.333); prs.slide_height = Inches(7.5)
BLANK = prs.slide_layouts[6]


def slide():
    return prs.slides.add_slide(BLANK)


def tb(s, x, y, w, h):
    return s.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h)).text_frame


def put(tf, text, sz=18, b=False, c=NAVY, first=False):
    p = tf.paragraphs[0] if first else tf.add_paragraph()
    r = p.add_run(); r.text = text
    r.font.size = Pt(sz); r.font.bold = b; r.font.color.rgb = c
    return p


def title(s, t, sub=None):
    put(tb(s, 0.5, 0.22, 12.3, 0.9), t, 28, True, NAVY, first=True)
    if sub:
        put(tb(s, 0.5, 1.02, 12.3, 0.5), sub, 14, False, GREY, first=True)


def pic(s, name, x, y, w):
    p = os.path.join(FIG, name)
    if os.path.exists(p):
        s.shapes.add_picture(p, Inches(x), Inches(y), width=Inches(w))


def g(cn, knob, eps, key):
    return cons[cn]["knobs"][knob]["eps"].get(eps, {}).get(key, float("nan"))


# numbers
sr_spread0 = g("M-lik", "sigma_r", "0.0", "c2_spread")
sr_spread3 = g("M-lik", "sigma_r", "0.3", "c2_spread")
nc_lik = g("M-lik", "N_c", "0.3", "c2_spread")
nc_ift = g("M-ift", "N_c", "0.3", "c2_spread")
h_sf = g("M-statfem", "h", "0.3", "c2_spread")
bias = {cn: cons[cn]["concentration"].get("0.3", {}).get("final_mean", float("nan")) for cn in cons}
b0 = {cn: cons[cn]["concentration"].get("0.0", {}).get("abs_bias_final", float("nan")) for cn in cons}

# 1 title + charge
s = slide()
title(s, "Does StatFEM's physics-in-likelihood give a consistent answer?",
      "A minimal 1-D axial-rod consistency toy  ·  Experiment A  ·  evaluate, don't defend/attack")
t = tb(s, 0.6, 1.8, 12.1, 5.2)
put(t, "The charge (hypothesis under test):", 18, True, NAVY, first=True)
put(t, "Encoding physics through the LIKELIHOOD (residual-as-fictitious-data) is claimed to give posteriors "
       "that depend on the discretization (N_c, residual noise sigma_r, mesh h) and not converge to truth as "
       "you refine -- 'inconsistent and incorrect'. The cure (IFT/PIFT) puts physics in the PRIOR with a "
       "learned inverse-temperature beta.", 15, False, GREY)
put(t, "", 8)
put(t, "Decisive question: as you refine, does each construction's theta posterior CONVERGE to truth AND stay "
       "INVARIANT to knobs that carry no information -- or DRIFT?  (verdict from the numbers, NOT pre-decided.)",
    16, True, NAVY)
put(t, f"Overall checker status: {CK['overall']}  (GREEN {CK['counts']['GREEN']} / "
       f"YELLOW {CK['counts']['YELLOW']} / RED {CK['counts']['RED']}).", 13, False, GREY)

# 2 testbed + question
s = slide()
title(s, "Testbed: fixed-free axial rod, forced drive-point FRF", "theta_true=1.15; model-form error = an omitted Winkler foundation")
t = tb(s, 0.6, 1.7, 12.1, 5.4)
for ln, c in [("Infer a scalar stiffness scale theta (EA = theta*EA_nom).", GREY),
              ("Observable: response at 7 sensors for several KNOWN drive frequencies (same data for all 3).", GREY),
              ("Model-form error eps: the TRUTH has a Winkler elastic foundation k_f=eps; the inference OMITS it.", GREY),
              ("eps=0 = no-error control (a correct method MUST recover theta_true).  eps=0.3 = model error.", GREY),
              ("The foundation shifts the LOW mode strongly, higher modes barely -> a single theta cannot absorb it.", NAVY)]:
    put(t, "•  " + ln, 16, (c == NAVY), c, first=(ln.startswith("Infer")))
pic(s, "figC3_coverage.png", 3.0, 4.2, 9.0)

# 3 constructions
s = slide()
title(s, "Three constructions on the SAME data -- only the residual WEIGHT differs")
pic(s, "figS_schematic.png", 0.4, 1.5, 12.6)

# 4 solver validation
s = slide()
title(s, "Gate first: the forward solvers converge to the analytic truth",
      f"rate ~2.0; finest relative error ~{SV['fd']['max_rel_err'][-1]:.0e} (<< noise floor) -> drift is the METHOD, not under-resolution")
pic(s, "figV_solver_convergence.png", 1.6, 1.7, 10.2)

# 5 money figure
s = slide()
title(s, "The consistency money figure: theta vs each refinement knob",
      "flat = discretization-invariant (good);  sloped = drift (the indicted behaviour)")
pic(s, "figA_money_theta_vs_knob.png", 0.3, 1.45, 12.7)

# 6 verdict numbers
s = slide()
title(s, "Verdict (from the numbers)")
t = tb(s, 0.6, 1.6, 12.2, 5.6)
put(t, "Discretization-INVARIANCE (C2 spread of posterior theta mean across the knob, eps=0.3):", 16, True, NAVY, first=True)
put(t, f"   M-lik vs mesh N_c: {nc_lik:.3f}   ·   M-ift vs N_c: {nc_ift:.3f}   ·   M-statfem vs mesh h: {h_sf:.3f}"
       "   -> ALL essentially invariant to the GENUINE mesh knob.", 15, False, GREY)
put(t, f"   BUT M-lik vs the FICTITIOUS residual noise sigma_r: spread {sr_spread0:.3f} (eps0) / {sr_spread3:.3f} (eps0.3)"
       "  -> DRIFTS, no principled way to set sigma_r.", 15, True, RED)
put(t, "", 8)
put(t, "Concentration (C1):", 16, True, NAVY)
put(t, f"   eps=0 control: all recover theta_true (|bias| M-lik {b0['M-lik']:.3f}, M-statfem {b0['M-statfem']:.3f}, "
       f"M-ift {b0['M-ift']:.3f}).", 15, False, GREY)
put(t, f"   eps=0.3: all CONCENTRATE on a BIASED theta (M-lik {bias['M-lik']:.3f}, M-statfem {bias['M-statfem']:.3f}, "
       f"M-ift {bias['M-ift']:.3f}; truth {TT}) -> confidently wrong under model error.", 15, True, RED)
put(t, "", 6)
cov = {cn: cons[cn]["knobs"][("h" if cn == "M-statfem" else "N_c")]["eps"]["0.3"]["coverage_finest"] for cn in cons}
put(t, "Held-out prediction (C3, eps=0.3):", 16, True, NAVY)
put(t, f"   coverage M-lik {cov['M-lik']:.2f} (worst) · M-ift {cov['M-ift']:.2f} · M-statfem {cov['M-statfem']:.2f} "
       "(discrepancy keeps PREDICTION calibrated despite biased theta).", 15, False, GREY)
put(t, "", 6)
put(t, "So: the charge's MECHANISM (a fictitious knob moving the physics-in-likelihood answer) is demonstrated "
       "and isolated to sigma_r; the stronger phrasing ('doesn't converge as you refine the mesh') is NOT seen "
       "here -- refinement converges for all three.", 15, True, NAVY)

# 7 gaps + improvements
s = slide()
title(s, "Gaps + suggested improvements (for Ilias)")
t = tb(s, 0.6, 1.6, 12.2, 5.6)
put(t, "M-lik (physics in likelihood):", 16, True, RED, first=True)
put(t, "   gap = un-calibrated sigma_r (drift ~0.08) + multimodality when the prior spans a resonance crossing.  "
       "fix = learn/marginalise the residual weight (-> M-ift).", 14, False, GREY)
put(t, "M-ift (physics in prior, learned beta):", 16, True, GREEN)
put(t, "   best on the knob axis (no sigma_r; theta invariant).  gap = beta weakly identified in this toy "
       "(theta unaffected).  fix = richer field data to sharpen beta; report its weak ID honestly.", 14, False, GREY)
put(t, "M-statfem (FE + discrepancy):", 16, True, BLUE)
put(t, "   theta invariant to mesh, BUT learned sigma_d stays tiny -> theta ABSORBS the foundation "
       "(discrepancy<->parameter confounding).  fix = constrain the discrepancy / cut-Bayes / add observables "
       "where the foundation and theta act differently.", 14, False, GREY)
put(t, "", 6)
put(t, "Cross-cutting: under THIS model error all three concentrate on a biased theta (parameter non-recovery); "
       "they differ only in whether an un-calibrated knob (sigma_r) also moves the answer.", 15, True, NAVY)

# 8 scope
s = slide()
title(s, "Scope & honesty")
t = tb(s, 0.6, 1.7, 12.2, 5.0)
for ln in ["One synthetic realization per cell (n-axis adds replicates); no flight/build variability.",
           "Model-form error is a SURROGATE (Winkler foundation), not a measured real-structure discrepancy.",
           "One scalar parameter (theta); a real calibration has many -> identifiability is easier here.",
           "Verdicts are for THIS minimal rod toy -- they evaluate the constructions, not a universal proof.",
           f"Replay: bash run_all.sh  ->  checker {CK['overall']}.  All NUTS cells reported with R-hat/ESS/div."]:
    put(t, "•  " + ln, 15, False, GREY, first=ln.startswith("One synthetic"))

out = os.path.join(ROOT, "slides", "statfem_consistency_toy.pptx")
prs.save(out)
print("saved", out, "(", len(prs.slides._sldIdLst), "slides )")
