"""
Assemble the teaching PowerPoint from the generated figures and GIFs.

Schneider et al. (2022), MSSP 166:108407 -- teaching deck.
All embedded visuals are synthetic/conceptual illustrations (see common.STAMP).
Animated GIFs play in PowerPoint slideshow mode; static renderers show frame 1.
"""
from __future__ import annotations
from pathlib import Path
from PIL import Image

from pptx import Presentation
from pptx.util import Inches, Pt, Emu
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR

BASE = Path(__file__).resolve().parent.parent
FIG = BASE / "figures"
GIF = BASE / "gifs"
OUT = BASE / "schneider2022_teaching.pptx"

NAVY = RGBColor(0x15, 0x31, 0x4B)
ORANGE = RGBColor(0xE0, 0x7B, 0x39)
GREEN = RGBColor(0x2E, 0x8B, 0x57)
GREY = RGBColor(0x6B, 0x6B, 0x6B)
WHITE = RGBColor(0xFF, 0xFF, 0xFF)
LIGHT = RGBColor(0xF2, 0xF5, 0xF8)

EMU_PER_IN = 914400

prs = Presentation()
prs.slide_width = Inches(13.333)
prs.slide_height = Inches(7.5)
BLANK = prs.slide_layouts[6]
SW, SH = prs.slide_width, prs.slide_height


def _fit(path, l, t, w, h):
    iw, ih = Image.open(path).size
    ar = iw / ih
    bar = (w / h)
    if ar > bar:
        nw = w; nh = w / ar
    else:
        nh = h; nw = h * ar
    nl = l + (w - nw) / 2
    nt = t + (h - nh) / 2
    return Emu(int(nl)), Emu(int(nt)), Emu(int(nw)), Emu(int(nh))


def add_picture(slide, path, l, t, w, h):
    fl, ft, fw, fh = _fit(path, l, t, w, h)
    slide.shapes.add_picture(str(path), fl, ft, width=fw, height=fh)


def title_bar(slide, text, sub=None):
    box = slide.shapes.add_textbox(Inches(0.45), Inches(0.18),
                                   SW - Inches(0.9), Inches(0.95))
    tf = box.text_frame; tf.word_wrap = True
    p = tf.paragraphs[0]; p.text = text
    p.font.size = Pt(26); p.font.bold = True; p.font.color.rgb = NAVY
    if sub:
        p2 = tf.add_paragraph(); p2.text = sub
        p2.font.size = Pt(14); p2.font.italic = True; p2.font.color.rgb = GREY


def footer(slide):
    box = slide.shapes.add_textbox(Inches(0.3), SH - Inches(0.34),
                                   SW - Inches(0.6), Inches(0.3))
    p = box.text_frame.paragraphs[0]
    p.text = ("Teaching illustration - synthetic/conceptual, NOT the paper's CLT "
              "results  |  Schneider et al. (2022) MSSP 166:108407")
    p.font.size = Pt(8); p.font.color.rgb = GREY


def bullets(slide, items, l, t, w, h, size=16):
    box = slide.shapes.add_textbox(l, t, w, h)
    tf = box.text_frame; tf.word_wrap = True
    for i, it in enumerate(items):
        lvl = 0
        if isinstance(it, tuple):
            it, lvl = it
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.text = ("- " if lvl == 0 else "    . ") + it
        p.font.size = Pt(size if lvl == 0 else size - 2)
        p.font.color.rgb = NAVY if lvl == 0 else GREY
        p.space_after = Pt(5)
    return box


def section_slide(num, title, items):
    s = prs.slides.add_slide(BLANK)
    bg = s.shapes.add_shape(1, 0, 0, SW, SH)
    bg.fill.solid(); bg.fill.fore_color.rgb = NAVY; bg.line.fill.background()
    bg.shadow.inherit = False
    tb = s.shapes.add_textbox(Inches(0.8), Inches(2.4), SW - Inches(1.6), Inches(1.4))
    p = tb.text_frame.paragraphs[0]; p.text = f"Part {num}"
    p.font.size = Pt(22); p.font.color.rgb = ORANGE; p.font.bold = True
    p2 = tb.text_frame.add_paragraph(); p2.text = title
    p2.font.size = Pt(34); p2.font.color.rgb = WHITE; p2.font.bold = True
    bx = s.shapes.add_textbox(Inches(0.85), Inches(4.4), SW - Inches(1.7), Inches(2.5))
    tf = bx.text_frame; tf.word_wrap = True
    for i, it in enumerate(items):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.text = "-  " + it; p.font.size = Pt(16); p.font.color.rgb = LIGHT
        p.space_after = Pt(6)
    return s


def wide_slide(title, sub, image, items, img_h=4.2, size=15):
    """Title, wide image under it, bullets at bottom."""
    s = prs.slides.add_slide(BLANK)
    title_bar(s, title, sub)
    add_picture(s, image, Inches(0.4), Inches(1.15),
                SW - Inches(0.8), Inches(img_h))
    bullets(s, items, Inches(0.55), Inches(1.2 + img_h + 0.05),
            SW - Inches(1.1), SH - Inches(1.2 + img_h + 0.45), size=size)
    footer(s)
    return s


def split_slide(title, sub, image, items, img_left=False, size=16):
    """Title, image on one half, bullets on the other."""
    s = prs.slides.add_slide(BLANK)
    title_bar(s, title, sub)
    top = Inches(1.25); ih = SH - Inches(1.7)
    if img_left:
        add_picture(s, image, Inches(0.35), top, Inches(6.6), ih)
        bullets(s, items, Inches(7.2), Inches(1.4), Inches(5.8), ih, size=size)
    else:
        add_picture(s, image, Inches(6.5), top, Inches(6.6), ih)
        bullets(s, items, Inches(0.5), Inches(1.4), Inches(5.8), ih, size=size)
    footer(s)
    return s


# ===========================================================================
# TITLE
# ===========================================================================
s = prs.slides.add_slide(BLANK)
bg = s.shapes.add_shape(1, 0, 0, SW, SH)
bg.fill.solid(); bg.fill.fore_color.rgb = NAVY; bg.line.fill.background()
bg.shadow.inherit = False
tb = s.shapes.add_textbox(Inches(0.8), Inches(1.9), SW - Inches(1.6), Inches(2.6))
tf = tb.text_frame; tf.word_wrap = True
p = tf.paragraphs[0]
p.text = "Bayesian FRF Updating with Rational Surrogates"
p.font.size = Pt(38); p.font.bold = True; p.font.color.rgb = WHITE
p2 = tf.add_paragraph()
p2.text = "A visual walkthrough of three core ideas"
p2.font.size = Pt(20); p2.font.color.rgb = ORANGE
p3 = tf.add_paragraph()
p3.text = ("1. PCE-rational surrogate of an FRF   2. The complex multiplicative "
           "likelihood   3. BUS + Subset Simulation")
p3.font.size = Pt(15); p3.font.color.rgb = LIGHT
p4 = tf.add_paragraph()
p4.text = "Schneider, Papaioannou, Straub, Winter, Mueller - MSSP 166:108407 (2022)"
p4.font.size = Pt(13); p4.font.italic = True; p4.font.color.rgb = LIGHT
footer(s)

# ===========================================================================
# ROADMAP
# ===========================================================================
s = prs.slides.add_slide(BLANK)
title_bar(s, "Roadmap & how to read this deck")
bullets(s, [
    "The problem: given measured frequency response functions (FRFs) of a "
    "structure, infer uncertain material/damping parameters AND honest "
    "uncertainty on them.",
    "Three machinery pieces, each with figures + animations:",
    ("Part 1 - a fast RATIONAL surrogate replaces the expensive FE model.", 1),
    ("Part 2 - a LIKELIHOOD that compares complex FRFs the right way.", 1),
    ("Part 3 - BUS + Subset Simulation draws posterior samples.", 1),
    "Audience note: structural-dynamics terms (FRF, mode, damping) used freely; "
    "statistics/sampling terms defined in plain English on first use.",
    "HONESTY: every plot here is a small synthetic teaching model. It is NOT a "
    "reproduction of the paper's cross-laminated-timber (CLT) numbers. Public "
    "values reused from the paper are labelled on the figure.",
], Inches(0.6), Inches(1.4), SW - Inches(1.2), Inches(5.5), size=17)
footer(s)

# ===========================================================================
# PART 1
# ===========================================================================
section_slide(1, "A PCE-rational surrogate of an FRF", [
    "An FRF is complex-valued and is naturally a ratio of polynomials.",
    "A single polynomial cannot place resonance peaks; a rational can.",
    "The paper builds R(X)=P(X)/Q(X): two polynomial-chaos expansions with "
    "complex coefficients, one over the numerator, one over the denominator.",
])

split_slide(
    "1.1  An FRF is a COMPLEX number at every frequency",
    "real + imaginary  <->  magnitude + phase",
    FIG / "p1_fig1_complex_nature.png", [
        "FRF h(f) = acceleration response per unit force - one COMPLEX value per "
        "frequency f.",
        "Two equivalent views: real & imaginary part (a+bi), or magnitude |h| and "
        "phase angle.",
        "Each resonance (mode) traces a LOOP in the complex (Nyquist) plane, a PEAK "
        "in magnitude, and a ~180-deg phase drop.",
        "Why it matters: the likelihood (Part 2) must compare these complex numbers, "
        "not just magnitudes.",
        "Mode frequencies here are the paper's public shell-model values (Fig. C.10).",
    ], img_left=True, size=15)

split_slide(
    "1.2  One frequency point: a+bi  =  |h| e^{i*phase}",
    "the two coordinate systems we will use everywhere",
    FIG / "p1_fig2_one_point.png", [
        "Real part a and imaginary part b are Cartesian coordinates of the FRF value.",
        "Magnitude |h| (length) and phase (angle) are the polar coordinates.",
        "The paper's error model lives in the polar view: it puts a distribution on "
        "log-magnitude and on phase (Part 2).",
        "Keep both pictures in mind - we switch between them constantly.",
    ], img_left=False, size=16)

wide_slide(
    "1.3  Why RATIONAL: a polynomial cannot fit resonances",
    "fit OF FREQUENCY using the paper's own linearized rational regression (Eqs. 6-9)",
    FIG / "p1_fig3_poly_vs_rational_freq.png", [
        "A transfer function is literally a ratio of polynomials in frequency, so it "
        "has POLES (the resonance peaks).",
        "Left: rational P/Q (orange) sits on top of truth; a high-degree polynomial "
        "(purple) rings and misses peaks. Right: the rational error is ~10 orders of "
        "magnitude smaller. Same idea works over the PARAMETERS, next slide.",
    ], img_h=4.0, size=14)

split_slide(
    "1.4  The paper's surrogate: rational IN THE PARAMETERS",
    "FRF value at a fixed frequency, as a function of a stiffness input (Hermite-PCE)",
    FIG / "p1_fig4_rational_in_parameter.png", [
        "Polynomial chaos expansion (PCE): write a quantity as a weighted sum of "
        "special polynomials (here Hermite) of the standard-normal inputs - a cheap "
        "stand-in for the FE model.",
        "As stiffness k varies, the FRF at a fixed frequency crosses a resonance = a "
        "POLE in k. A plain Hermite-PCE blows up; the rational PCE (mp=3, mq=4, exactly "
        "the paper's CLT choice) nails it.",
        "Coefficients are found by the linearized least-squares / SVD of Eqs. (6)-(9) - "
        "works with any black-box FE solver.",
    ], img_left=False, size=14)

split_slide(
    "1.5  Surrogate quality in both representations",
    "same surrogate, viewed as complex plane and as magnitude/phase",
    FIG / "p1_fig5_quality_both_reps.png", [
        "The fitted rational surrogate (dotted orange) overlays the truth in the complex "
        "plane, in magnitude, and in phase.",
        "Built from a modest experimental design (black dots) drawn from the prior.",
        "This is the object that gets evaluated MANY times during sampling instead of "
        "the expensive FE model.",
        "Animations (see gifs/): Nyquist sweep, order convergence, parameter sweep.",
    ], img_left=True, size=15)

# animated GIF slide for Part 1
s = prs.slides.add_slide(BLANK)
title_bar(s, "1.6  Animation - surrogate tracks the complex value as k changes",
          "plays in PowerPoint slideshow mode; also in gifs/p1_gif3_param_sweep.gif")
add_picture(s, GIF / "p1_gif3_param_sweep.gif", Inches(0.4), Inches(1.25),
            SW - Inches(0.8), Inches(5.3))
footer(s)

# ===========================================================================
# PART 2
# ===========================================================================
section_slide(2, "The likelihood formulation", [
    "Model error is MULTIPLICATIVE and COMPLEX: data = model x error.",
    "Put a lognormal on the error magnitude and a normal on the error phase.",
    "Correlate the error across SPACE and FREQUENCY - this is the paper's key "
    "novelty and it controls how confident the posterior is allowed to be.",
])

split_slide(
    "2.1  Multiplicative complex error model (Eq. 13-15)",
    "data = model (x) error;  log-error = w + i*theta",
    FIG / "p2_fig1_error_model_build.png", [
        "Error eps is MULTIPLICATIVE: Y_obs = Y_model x eps (Hadamard product).",
        "Write eps = |eps| e^{i*theta}. Model |eps| as LOGNORMAL (so log|eps|=w is "
        "normal) and phase theta as NORMAL.",
        "Taking logs turns the product into a SUM: log Y_obs = log Y_model + (w + i*theta).",
        "Effect on the model value (d): the error both SCALES (magnitude) and ROTATES "
        "(phase) it in the complex plane.",
        "sigma_w, sigma_theta are the magnitude/phase error spreads - learned, not fixed.",
    ], img_left=True, size=14)

split_slide(
    "2.2  'Improper complex normal' = non-circular (Eq. A.9)",
    "joint PDF of real & imaginary error reproduces the paper's Fig. 1",
    FIG / "p2_fig2_joint_pdf_grid.png", [
        "'Improper' / non-circular just means the spread in the real direction differs "
        "from the imaginary direction - the cloud is NOT a symmetric circle.",
        "Small sigma_w, large sigma_theta -> an ARC along the unit circle (phase varies, "
        "magnitude fixed).",
        "Large sigma_w, small sigma_theta -> a RADIAL smear (magnitude varies).",
        "Both large -> the signature KIDNEY shape; mass points away from the origin "
        "because the error is multiplicative.",
        "Cyan + marks the median error eps=1 (no error).",
    ], img_left=False, size=14)

# kidney morph GIF
s = prs.slides.add_slide(BLANK)
title_bar(s, "2.3  Animation - circle -> arc -> kidney as (sigma_w, sigma_theta) change",
          "gifs/p2_gif1_kidney_morph.gif  (and p2_gif2_error_scatter.gif: radial vs tangential spread)")
add_picture(s, GIF / "p2_gif1_kidney_morph.gif", Inches(3.7), Inches(1.25),
            Inches(6.0), Inches(5.3))
footer(s)

split_slide(
    "2.4  The likelihood of ONE observation (Eq. 17-18)",
    "score the model-vs-data mismatch with the error density",
    FIG / "p2_fig3_one_likelihood.png", [
        "Likelihood L(x) = how plausible the data is for parameters x. Eq. 17: evaluate "
        "the error PDF at the leftover mismatch log Y_obs - log Y_model(x).",
        "Left: the error PDF is the kidney, SCALED and ROTATED to sit on the model value; "
        "the likelihood is its height at the measured point.",
        "Right: the SAME thing in (w, theta) coordinates is a plain Gaussian. The mismatch "
        "splits into a LOG-MAGNITUDE error w and a PHASE error theta, each scored "
        "separately (Eq. 18).",
        "Small mismatch -> near the peak -> high likelihood; large mismatch -> tail.",
    ], img_left=True, size=13.5)

split_slide(
    "2.5  Correlating error over SPACE and FREQUENCY (Eq. 19-25)",
    "model error is systematic, so neighbouring points share it",
    FIG / "p2_fig4_correlation_matrices.png", [
        "Model error is not white noise - it is a SYSTEMATIC deficiency (e.g. the "
        "single-ratio damping model). So error at nearby sensors / nearby frequencies is "
        "correlated.",
        "Two exponential kernels: spatial exp(-dz/lz) and frequency exp(-df/lf).",
        "Additive split (Eq. 19): rho = r*rho_f + (1-r)*rho_z. Assembled for every "
        "(sensor, frequency) pair into the big matrix R (block structure, panel c).",
        "Paper writes R via Kronecker products (Eq. 25) so it can be inverted cheaply.",
    ], img_left=False, size=14)

split_slide(
    "2.6  The split factor r and its limits (Eq. 22-23)",
    "how much correlation lives in frequency vs space",
    FIG / "p2_fig5_split_factor.png", [
        "r near 1 -> error is shared across frequency (and across all sensors at a given "
        "frequency); r near 0 -> error is shared across space.",
        "Additive (not multiplicative) link keeps a correlation FLOOR along each axis: "
        "even far apart in frequency, two sensors still share (1-r)*rho_z.",
        "Paper LEARNS r ~ 0.82 and a huge spatial length (>> plate) -> error is "
        "spatially GLOBAL and frequency-structured = fingerprint of the damping-model "
        "deficiency.",
        "Animation: gifs/p2_gif3_correlation_sweep.gif sweeps r.",
    ], img_left=True, size=14)

split_slide(
    "2.7  WHY correlation matters: don't over-count dense data",
    "ignoring it -> over-confident posterior + biased damping (paper Sec. 5.4.1)",
    FIG / "p2_fig6_effective_data.png", [
        "Dense 1-Hz data has ~136 frequency lines, but neighbours carry nearly the same "
        "information.",
        "Treating them as independent (R=I) over-counts -> the EFFECTIVE number of "
        "independent points is far smaller (illustrative AR(1) estimate shown).",
        "Consequence in the paper: neglecting correlation makes the posterior artificially "
        "tight and biases the damping ratio LOW (next panel quantifies the tightening).",
        "Correlation lets you use ALL the data without hand-picking frequency points.",
    ], img_left=False, size=14)

split_slide(
    "2.8  The over-confidence, quantified",
    "same data, correct R vs independence assumption",
    FIG / "p2_fig7_correlated_vs_uncorrelated_posterior.png", [
        "Toy inference of one parameter from 40 correlated residuals.",
        "Correct correlated likelihood (green) gives an honest posterior width.",
        "Pretending independence (red dashed) gives a much narrower, OVER-CONFIDENT "
        "posterior - the same mechanism that biases the paper's damping estimate.",
        "Takeaway: the correlation model is what keeps the uncertainty HONEST.",
    ], img_left=True, size=15)

# ===========================================================================
# PART 3
# ===========================================================================
section_slide(3, "BUS + Subset Simulation", [
    "Recast Bayesian updating as a structural-reliability problem (BUS).",
    "The 'accepted' region in an augmented space IS the posterior.",
    "Subset Simulation reaches that rare region through nested levels - far more "
    "efficient than naive Monte Carlo when the likelihood is peaky.",
])

split_slide(
    "3.1  BUS: turn 'find the posterior' into a keep / toss rule",
    "draw parameters x and a dice-roll p in [0,1]; KEEP the pair if p <= c*L(x)  (Eq. 26)",
    FIG / "p3_fig1_bus_concept.png", [
        "Goal: collect samples from the posterior = the parameter sets that fit the data.",
        "What the symbols mean:",
        ("x  -  the parameters we want to learn (stiffness, damping, ...).", 1),
        ("L(x)  -  the likelihood: how well x reproduces the measured FRF "
         "(higher = better fit).", 1),
        ("p  -  a helper 'dice roll', drawn evenly between 0 and 1.", 1),
        ("c  -  a fixed scaling number that keeps c*L(x) at or below 1.", 1),
        "The rule: draw x from the prior and a dice-roll p; KEEP the pair when "
        "p <= c*L(x), otherwise toss it.",
        "The kept x-values ARE posterior samples: a better fit means a higher c*L(x), "
        "so that x is kept more often.",
        "Catch: when only a few x fit, almost everything is tossed (~0.5% kept here) - "
        "plain random sampling is far too wasteful, so we use Subset Simulation (next).",
        ("Paper's wording: a structural-reliability 'limit state' h = p - c*L(x); the "
         "kept region is the posterior.", 1),
    ], img_left=True, size=13)

# BUS rain GIF
s = prs.slides.add_slide(BLANK)
title_bar(s, "3.2  Animation - BUS 'rain' builds the posterior",
          "gifs/p3_gif1_bus_rain.gif : keep samples under the c*L(x) curve; their histogram = posterior")
add_picture(s, GIF / "p3_gif1_bus_rain.gif", Inches(2.7), Inches(1.25),
            Inches(7.9), Inches(5.3))
footer(s)

split_slide(
    "3.3  Subset Simulation: nested levels (Eq. 27)",
    "march the prior cloud into the posterior, 20% at a time",
    FIG / "p3_fig2_sus_levels.png", [
        "Write the rare acceptance probability as a product of easy conditional "
        "probabilities, each p0 = 0.2.",
        "Level 0: samples from the prior. Keep the best 20% (closest to acceptance); "
        "set an intermediate threshold b.",
        "Run short MCMC chains (here modified Metropolis) from those seeds to refill the "
        "population inside the new level. Repeat.",
        "When the threshold reaches 0 the surviving samples satisfy p <= c*L(x) = the "
        "POSTERIOR.",
        "PROTOTYPE sampler for teaching - not NUTS/HMC, not the paper's adaptive aBUS-SuS.",
    ], img_left=False, size=13.5)

# SuS levels GIF
s = prs.slides.add_slide(BLANK)
title_bar(s, "3.4  Animation - the cloud contracts level by level",
          "gifs/p3_gif2_sus_levels.gif")
add_picture(s, GIF / "p3_gif2_sus_levels.gif", Inches(3.6), Inches(1.25),
            Inches(6.2), Inches(5.3))
footer(s)

split_slide(
    "3.5  It works: posterior recovered & validated",
    "prototype SuS vs the known analytic Gaussian posterior",
    FIG / "p3_fig3_posterior_validation.png", [
        "On a toy with a KNOWN answer, the SuS samples reproduce the analytic posterior "
        "mean and spread to ~1-3%.",
        "This is the validation that lets us trust the mechanics shown in the animations.",
        "In the paper, the same BUS-SuS loop also returns an estimate of the model "
        "evidence (the normalizing constant) for model comparison.",
        "Real runs should use a convergence-checked sampler (the project standard is "
        "NUTS/HMC); this prototype is for intuition only.",
    ], img_left=True, size=14)

# ===========================================================================
# SUMMARY
# ===========================================================================
s = prs.slides.add_slide(BLANK)
title_bar(s, "Putting it together")
bullets(s, [
    "Part 1 - A rational PCE surrogate R(X)=P(X)/Q(X) replaces the expensive FE "
    "model and captures resonance behaviour a polynomial cannot.",
    "Part 2 - A multiplicative complex error model gives a likelihood that "
    "compares FRFs honestly (magnitude AND phase), and a space-frequency "
    "correlation that keeps the posterior uncertainty honest on dense data.",
    "Part 3 - BUS recasts updating as a reliability problem; Subset Simulation "
    "samples the posterior efficiently even when the likelihood is peaky.",
    "The pieces compose: surrogate makes each likelihood call cheap -> the "
    "sampler can afford many calls -> posterior + evidence come out.",
    "Honest-uncertainty theme: the correlation model and full posterior are what "
    "separate this from a deterministic 'best-fit' update.",
], Inches(0.6), Inches(1.4), SW - Inches(1.2), Inches(5.3), size=17)
footer(s)

# REFERENCES / CAVEATS
s = prs.slides.add_slide(BLANK)
title_bar(s, "Sources, scope & caveats")
bullets(s, [
    "Primary source: F. Schneider, I. Papaioannou, D. Straub, C. Winter, "
    "G. Mueller, 'Bayesian parameter updating in linear structural dynamics with "
    "frequency transformed data using rational surrogate models', MSSP 166:108407 "
    "(2022).",
    "Rational surrogate from Schneider et al., Comput. Struct. 233:106223 (2020); "
    "BUS from Straub & Papaioannou (2015); adaptive BUS-SuS from Betz et al. (2018); "
    "Subset Simulation from Au & Beck (2001).",
    "ALL figures/animations here are small synthetic teaching models, generated by "
    "the scripts in scripts/. They are NOT the paper's CLT results.",
    "Reused public values from the paper are labelled on-figure (shell-model "
    "eigenfrequencies; the mp=3, mq=4 surrogate orders; r~0.82).",
    "The BUS-SuS code is a teaching prototype (modified-Metropolis MCMC), validated "
    "against an analytic posterior - not a production, convergence-gated sampler.",
], Inches(0.6), Inches(1.4), SW - Inches(1.2), Inches(5.3), size=14)
footer(s)

prs.save(str(OUT))
print("wrote", OUT.relative_to(BASE), "-", len(prs.slides.__iter__().__length_hint__() if False else list(prs.slides)), "slides")
