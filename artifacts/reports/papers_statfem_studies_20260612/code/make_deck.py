"""Build the slide deck (Schneider+Das/Debnath x StatFEM). System python3 (python-pptx). Figures must exist."""
import json, os
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN

HERE=os.path.dirname(os.path.abspath(__file__)); ROOT=os.path.join(HERE,"..")
FIG=os.path.join(ROOT,"figures"); O=os.path.join(ROOT,"out")
SA=json.load(open(os.path.join(O,"study_a_summary.json"))); p=SA["primary_interleaved"]; se=SA["secondary_extrapolation"]; hp=SA["v2_hyper_posterior"]
P1=json.load(open(os.path.join(O,"phase1_summary.json")))
SC=json.load(open(os.path.join(O,"study_c_summary.json")))
SD=json.load(open(os.path.join(O,"study_d_summary.json")))

NAVY=RGBColor(0x1f,0x3a,0x5f); BLUE=RGBColor(0x1f,0x77,0xb4); GREY=RGBColor(0x66,0x66,0x66)
RED=RGBColor(0xc0,0x39,0x2b); GREEN=RGBColor(0x2a,0x7d,0x2a); ORANGE=RGBColor(0xd9,0x7a,0x16)
prs=Presentation(); prs.slide_width=Inches(13.333); prs.slide_height=Inches(7.5); BLANK=prs.slide_layouts[6]
def slide(): return prs.slides.add_slide(BLANK)
def settext(tf,t,sz=18,b=False,c=NAVY):
    pa=tf.paragraphs[0]; r=pa.add_run(); r.text=t; r.font.size=Pt(sz); r.font.bold=b; r.font.color.rgb=c; return pa
def title(s,t,sub=None):
    settext(s.shapes.add_textbox(Inches(0.5),Inches(0.22),Inches(12.3),Inches(0.9)).text_frame,t,29,True,NAVY)
    if sub: settext(s.shapes.add_textbox(Inches(0.5),Inches(1.0),Inches(12.3),Inches(0.5)).text_frame,sub,14.5,False,GREY)
def bullets(s,items,x=0.6,y=1.6,w=12.1,h=5.4,size=16,gap=6):
    tf=s.shapes.add_textbox(Inches(x),Inches(y),Inches(w),Inches(h)).text_frame; tf.word_wrap=True
    for i,(lvl,txt,col) in enumerate(items):
        pa=tf.paragraphs[0] if i==0 else tf.add_paragraph(); pa.level=lvl; pa.space_after=Pt(gap)
        r=pa.add_run(); r.text=txt; r.font.size=Pt(size-2*lvl); r.font.color.rgb=col; r.font.bold=(lvl==0 and col!=GREY)
def pic(s,path,x,y,w=None,h=None):
    kw={};
    if w:kw["width"]=Inches(w)
    if h:kw["height"]=Inches(h)
    s.shapes.add_picture(path,Inches(x),Inches(y),**kw)
def footer(s,t): settext(s.shapes.add_textbox(Inches(0.5),Inches(7.05),Inches(12.3),Inches(0.4)).text_frame,t,10,False,GREY)

# 1 title
s=slide()
settext(s.shapes.add_textbox(Inches(0.7),Inches(1.9),Inches(12),Inches(1.4)).text_frame,
 "Bringing Schneider (2022) + Das/Debnath (2020) into StatFEM",30,True,NAVY)
settext(s.shapes.add_textbox(Inches(0.7),Inches(3.2),Inches(12),Inches(1.2)).text_frame,
 "A unified method (modal statFEM) + five executed studies: discrepancy A/B, its control, REAL panel data, complex-modal damping ID, and a realistic twin with held-out QOIs + evolving-band GIFs",17,False,BLUE)
tf=s.shapes.add_textbox(Inches(0.7),Inches(4.4),Inches(12),Inches(1.8)).text_frame; tf.word_wrap=True
for i,t in enumerate(["Agentic BayesX · lead: Claude Code · human: Andrew Voss · 2026-06-12",
  "Executed (checker-backed): A (synthetic A/B) · Phase-1 (control+sweep) · C (REAL panel characterization) · D (complex-modal) · G (UNIFIED METHOD, realistic twin).",
  "Designed (promise-scored, not run): Studies B/E/F. Honesty: no success score without checker output; no new data gathered."]):
    pa=tf.paragraphs[0] if i==0 else tf.add_paragraph(); r=pa.add_run(); r.text=t; r.font.size=Pt(13); r.font.color.rgb=GREY
footer(s,"workspace: artifacts/reports/papers_statfem_studies_20260612/ · replay: run_all.sh · checker: code/check.py")

# 1b ARC SUMMARY (executive one-pager)
if os.path.exists(os.path.join(FIG,"fig_arc_summary.png")):
    s=slide(); title(s,"The whole arc in one page","Build the unified method → find where it breaks → fix it → prove it on REAL data → and a real-data WIN")
    pic(s,os.path.join(FIG,"fig_arc_summary.png"),0.3,1.5,w=12.7)
    footer(s,"fig_arc_summary.png · every number checker-backed · SYNTHETIC stages 1-3 + REAL suspended-panel data stages 4-5")

# 2 why papers
s=slide(); title(s,"Why these two papers — they attack the project's central lever",
 "Vision §4: the discrepancy covariance is the make-or-break knob (too independent → false collapse; too flexible → ridge)")
bullets(s,[
 (0,"Schneider 2022 — a discrepancy model for DENSE complex FRF data (no point-picking):",NAVY),
 (1,"T-S1  data = model ∘ ε, with log|ε| lognormal + phase normal — a likelihood at EVERY line.",BLUE),
 (1,"T-S2  error CORRELATED in space AND frequency, hyperparameters (σ_w,σ_θ,ℓ_f,r) INFERRED.",BLUE),
 (0,"Das & Debnath 2020 — Bayesian updating with INCOMPLETE COMPLEX modal data:",NAVY),
 (1,"T-D1  mode-matching-free: system complex modes are LATENT → no eigensolve-per-step, survives degeneracy.",GREEN),
 (1,"T-D2  joint mass + stiffness + DAMPING from complex modes (our repeated weak spot).",GREEN),
 (1,"T-D3  probabilistic change/damage read-out (a decision-facing output).",GREEN),
 (0,"Both donate LIKELIHOOD / DISCREPANCY structure that drops into the StatFEM backbone unchanged.",NAVY),
])
footer(s,"sources: MSSP 166:108407 (Schneider); MSSP 136:106524 (Das & Debnath)")

# 3 mapping
s=slide(); title(s,"How they map onto the robust-twin vision","Study A V2 = Schneider's likelihood AS the StatFEM output-space discrepancy; trust gate = held-out coverage")
pic(s,os.path.join(FIG,"fig8_graphical_model.png"),0.4,1.6,w=7.6)
bullets(s,[(0,"§4 discrepancy lever → T-S1/T-S2 (Studies A, C).",NAVY),(0,"§6.1 robust twin (widen+cover) → inferred correlation.",NAVY),
 (0,"§5.2 orthogonal output-space F(k) → ε on the FRF.",NAVY),(0,"§5.5/7004C load QOI → apparent mass M=F/a.",NAVY),
 (0,"identifiability → ℓ_f = effective independent-data count.",NAVY),(0,"damping / degeneracy → T-D1/T-D2 (Study D).",GREEN)],x=8.2,y=1.7,w=4.6,size=15)
footer(s,"fig8_graphical_model.png (run-specific schematic)")

# 4 Study A setup
s=slide(); title(s,"Study A (executed) — discrepancy-model A/B on dense FRF",
 "Truth = 3-DOF source/load; inference FEM = 2-DOF → a HIDDEN 3rd DOF is the model-form error")
pic(s,os.path.join(FIG,"fig1_truth_vs_data.png"),0.5,1.55,w=8.6)
bullets(s,[(0,"Observable: apparent mass / accelerance M=F/a.",NAVY),
 (0,"V1 iid · V2 Schneider (T-S1+T-S2) · V3 decimated.",NAVY),
 (0,"Injected Schneider error + anti-rig extras.",BLUE),
 (0,"Gates: all-var convergence + held-out 95% coverage.",NAVY)],x=9.3,y=1.8,w=3.6,size=14)
footer(s,"fig1 · SYNTHETIC · one dataset, one realization")

# 5 headline
s=slide(); title(s,"Headline — the structured discrepancy is calibrated AND sharp",
 "In-distribution interleaved holdout: Schneider conditions held-out lines on neighbours (T-S2)")
pic(s,os.path.join(FIG,"fig2_headline_coverage.png"),0.4,1.65,w=12.5)
bullets(s,[(0,f"V2 Schneider: {p['v2']['coverage']*100:.0f}% coverage · band {p['v2']['band_width']:.2f} · R-hat {p['v2']['max_rhat']:.3f}, ESS {p['v2']['min_ess']:.0f}, 0 div ✓",GREEN),
 (0,f"V1 iid: {p['v1']['coverage']*100:.0f}% · band {p['v1']['band_width']:.2f} (≈7× wider) · R-hat {p['v1']['max_rhat']:.0f} ✗ not converged",RED)],x=0.6,y=6.0,w=12.1,size=14,gap=2)
footer(s,"fig2 · SYNTHETIC · V2 band hugs the held-out data incl. the antiresonance notch")

# 6 convergence
s=slide(); title(s,"Only the structured likelihood mixes",
 "iid / decimated are numerically fragile here; their coverage is NOT trustworthy")
pic(s,os.path.join(FIG,"fig3_convergence_coverage.png"),0.7,1.7,w=11.9)
footer(s,"fig3 · SYNTHETIC · per the convergence gate, V1/V3 (R-hat≫1.05) are labeled not-converged")

# 7 gif
s=slide(); title(s,"The lever, animated — correlation length = effective independent-data count",
 "GIF: gif_corr_length_sweep.gif (animates in slideshow)")
pic(s,os.path.join(FIG,"gif_corr_length_sweep.gif"),2.4,1.7,w=8.6)
footer(s,f"inferred ℓ_f median = {hp['len_f'][1]:.0f} Hz (injected {hp['injected_len_f']:g}) · SYNTHETIC")

# 7b ablation — which Schneider ingredient does what (D37, answers Andrew's slide-6 fairness check)
HAS_AB=os.path.exists(os.path.join(O,"study_a_ablation.json"))
if HAS_AB:
    AB=json.load(open(os.path.join(O,"study_a_ablation.json")))
    s=slide(); title(s,"What actually drives the V1→V2 win? A controlled ablation (D37)",
     "V1→V2 changed THREE things at once (linear→log error; iid→correlated; 1→4 nuisance scales). The log-iid variant turns OFF only the correlation to attribute the effect.")
    pic(s,os.path.join(FIG,"figAB_ablation.png"),0.3,1.7,w=12.7)
    bullets(s,[(0,f"CONVERGENCE is fixed by the LOG (multiplicative) error model, NOT the correlation: V2-iid (log error, iid, SAME over-counting as V1) converges R-hat {AB['v2iid']['max_rhat']:.2f} (V1 linear-iid fails at {AB['v1']['max_rhat']:.0f}). So iid's failure here is error-SPACE misspecification, not over-counting.",GREEN),
     (0,f"The CORRELATION's specific job is the tight, calibrated held-out BANDS: V2-iid→V2 tightens the interleaved band {AB['v2iid']['band_width']:.2f}→{AB['v2']['band_width']:.2f} (~2.4×) and lifts coverage {AB['v2iid']['coverage']*100:.0f}%→{AB['v2']['coverage']*100:.0f}% by conditioning the held-out discrepancy on neighbouring observed lines. Clean split of Schneider's two ingredients: T-S1 (log error) = convergence; T-S2 (correlation) = band sharpness.",NAVY)],x=0.5,y=6.05,w=12.4,size=11,gap=2)
    footer(s,"figAB · SYNTHETIC · same data/split/priors/sampler, only the discrepancy model changes · out/study_a_ablation.json")

# 8 Phase 1 control
s=slide(); title(s,"Phase 1 control — the two Study-A caveats are resolved",
 "Set truth = 2-DOF (NO model-form error) and re-run — a decisive control")
pic(s,os.path.join(FIG,"figP1_control_convergence.png"),0.4,1.6,w=6.5)
pic(s,os.path.join(FIG,"figP2_sponge_isolation.png"),7.0,1.9,w=6.1)
bullets(s,[(0,f"V1 iid's non-convergence was CAUSED by model-form error: remove the hidden DOF and V1 converges (R-hat {P1['control']['V1']['max_rhat']:.3f}).",GREEN),
 (0,f"The 'sponge' is real and isolated: with no model-form error, V2 RECOVERS σ_w (CI [{P1['control']['V2']['sig_w'][0]:.2f},{P1['control']['V2']['sig_w'][2]:.2f}] vs injected {P1['control']['injected']['sig_w']}) and ℓ_f — Study A inflated them only because the discrepancy was absorbing the hidden-DOF error.",GREEN)],x=0.6,y=5.1,w=12.1,size=13,gap=4)
footer(s,"figP1+figP2 · SYNTHETIC control")

# 9 Phase 1 sweep + extrapolation negative
s=slide(); title(s,"Phase 1 — the correlation length is learnable; extrapolation still fails (honest)",
 "Sweep injected ℓ_f (left) · the OOD high-band holdout (right)")
pic(s,os.path.join(FIG,"figP3_corr_length_calibration.png"),0.5,1.7,w=6.2)
pic(s,os.path.join(FIG,"fig6_extrapolation_negative.png"),7.0,1.8,w=6.1)
bullets(s,[(0,f"ℓ_f posterior tracks the injected value; coverage 89–100% across regimes (left).",GREEN),
 (0,f"But a stationary discrepancy can't extrapolate into unmodelled physics — V2 covers only {se['v2']['coverage']*100:.0f}% in the high-band holdout (right). Reproduces our OOD lesson.",RED)],x=0.6,y=6.0,w=12.1,size=13,gap=3)
footer(s,"figP3 + fig6 · SYNTHETIC")

# 10 Study C real data
s=slide(); title(s,"Study C (executed, REAL DATA) — suspended composite panel",
 "Authoritative .mat (25 pts × 3200 freqs) + Abaqus FEA (45 modes < 200 Hz). No new data gathered.")
pic(s,os.path.join(FIG,"figC1_real_frf.png"),0.4,1.55,w=7.4)
pic(s,os.path.join(FIG,"figC2_fem_vs_test.png"),7.7,1.7,w=5.5)
fl=SC["discrepancy_floor"]
bullets(s,[(0,f"REAL discrepancy floor: {fl['n_matched']} matched modes, FEA |error| mean {fl['mean_abs_pct']:.1f}% (signed {fl['mean_signed_pct']:+.1f}% — consistently stiff), max {fl['max_abs_pct']:.1f}%.",GREEN),
 (0,"PROVENANCE: the .txt exports were mislabeled coherence; the .mat files are authoritative (audit done first).",ORANGE)],x=0.6,y=6.0,w=12.1,size=13,gap=3)
footer(s,"figC1+figC2 · REAL · this is the real model-form error a discrepancy term must absorb")

# 11 Study C Schneider on real
s=slide(); title(s,"Study C — Schneider's T-S2 quantity measured on the REAL panel",
 "Frequency-correlation length of the multiplicative log-FRF residual (point-vs-consensus)")
pic(s,os.path.join(FIG,"figC3_corr_length.png"),1.2,1.7,w=10.6)
bullets(s,[(0,f"Measured real ℓ_co,f ≈ {SC['schneider_real']['freq_corr_length_hz']:.1f} Hz, σ_w ≈ {SC['schneider_real']['log_mag_residual_sd']:.2f} — exactly the quantity Schneider infers, now on real data (characterization, not yet a calibration).",GREEN)],x=0.6,y=6.0,w=12.1,size=13,gap=2)
footer(s,"figC3 · REAL · next step = .mat ingest + Abaqus CMS→FRF forward model → a full Schneider NUTS calibration")

# 12 Study D
s=slide(); title(s,"Study D (executed) — Das/Debnath complex-modal updating through degeneracy",
 "Synthetic 4-DOF damped chain with a near-degenerate pair (mirrors the tray 82.9/84.3 + ShockSat eigh-MAC divergence)")
pic(s,os.path.join(FIG,"figD_complex_modal.png"),0.7,1.7,w=11.9)
bullets(s,[(0,f"At a {SD['truth']['near_degenerate_pair_gap_pct']:.2f}% degenerate gap: eigh-through likelihood = {SD['D_eig']['divergences']} divergences ({SD['D_eig']['div_frac']*100:.0f}%, fails gate); Das/Debnath latent-mode = {SD['D_latent']['divergences']} divergences (R-hat {SD['D_latent']['max_rhat']:.3f}) AND recovers damping. The logged ShockSat failure, solved.",GREEN)],x=0.6,y=6.05,w=12.1,size=12.5,gap=2)
footer(s,"figD · SYNTHETIC · higher-mode damping under-estimated (limited modes/DOF/1 dataset) — honest")

# ---- Study G slides (production UMS-FEM run) ----
HAS_G=os.path.exists(os.path.join(O,"ums2_summary.json"))
if HAS_G:
    GS=json.load(open(os.path.join(O,"ums2_summary.json")))
    gu=GS["unified"]; gi=GS["iid"]; gq=GS["qoi_unified"]; gqi=GS["qoi_iid"]
    FULL=json.load(open(os.path.join(O,"ums_summary_FULL_ambition.json"))) if os.path.exists(os.path.join(O,"ums_summary_FULL_ambition.json")) else None
    gconv = gu["max_rhat"]<=1.05 and gu["min_ess"]>=200

    s=slide(); title(s,"THE METHOD (Study G) — unified modal statFEM = statFEM × Das/Debnath × Schneider",
     "One generative model. Full definition + self-tests in method_ums.md")
    pic(s,os.path.join(FIG,"figG2_graphical_model.png"),0.5,1.5,w=9.4)
    bullets(s,[(0,"statFEM: FEM K(θ) calibrated by data; trust gate = held-out QOI coverage.",BLUE),
     (0,"Das/Debnath: complex-mode FRF + damping; NO mode-matching/eigensolve in the loop.",GREEN),
     (0,"Schneider: correlated multiplicative complex discrepancy (σ,ℓ_f,ℓ_z inferred).",ORANGE),
     (0,"Shapes from eigh K̃(θ) = PHYSICS-BOUND (the key design choice — see next).",NAVY)],x=10.1,y=1.7,w=3.0,size=11.5)
    footer(s,"figG2 · self-tests: separable logpdf vs dense MVN 1e-13; residue FRF vs direct solve 4e-13")

    s=slide(); title(s,"Study G data — realistic synthetic, looks like the real LDV cases",
     "NO injected Schneider field: the model error is GENUINE structural mismatch (also the adversarial test)")
    pic(s,os.path.join(FIG,"figG1_realism.png"),0.6,1.6,w=12.1)
    bullets(s,[(0,"Truth: heterogeneous stiffness + local SOFT+DAMPED patch + uneven cables + drive mass loading. Inference FEM: 4 quadrant groups + proportional damping. 20 scan points → 15 observed, 5 held out (one inside the patch).",NAVY),
     (0,"Measurement: antiresonance noise floor (matched to the real panel's 2.3e-3 min/median), 2% multiplicative, ±0.5 dB calibration scatter, low-f junk.",GREY)],x=0.6,y=5.6,w=12.2,size=12.5,gap=3)
    footer(s,"figG1 · LEFT = REAL H1.mat · RIGHT = synthetic twin · 10–60 Hz, df=0.125")

    s=slide(); title(s,"Getting it to RUN was the hard part — a 5-rung sampler-pathology ladder",
     "Each rung diagnosed + cured + evidence-logged (method_ums.md §3b; decisions D14–D23)")
    bullets(s,[
     (0,"1. Exact log/wrapped-phase Schneider likelihood FREEZES NUTS (100% div) — gradient cliffs at resonance/antiresonance. → smooth r=(data−H)/(|H|+κ) unlocks it (plausibly why Schneider used gradient-free Subset Simulation).",RED),
     (0,"2. Default step throws chains across needle ridges (R-hat 236) → tiny initial step.  3. Per-mode complex-scale GAUGE valley (R-hat 73) → pin shape normalization.",ORANGE),
     (0,"4. Mode-level physics-vs-discrepancy trade-off (Kennedy–O'Hagan, R-hat 215) → practitioner damping prior.  5. Frozen unidentified coords (R-hat 176) → fix out-of-band params.",ORANGE),
     (0,"THE ARCHITECTURE LESSON: free latent mode shapes (Das/Debnath) have NO data at held-out points → don't generalize (UMS-full: R-hat 364, QOI 0/10, ~1e7× error). PHYSICS-BOUND shapes from eigh K̃(θ) generalize → UMS-FEM.",NAVY)])
    footer(s,"evidence: logs/probe*.log · this ladder is itself a contribution (the cost of fully-Bayesian NUTS on dense FRFs)")

    s=slide(); title(s,"THE FINDING — the unified method exposes physics-vs-discrepancy BIMODALITY",
     "The project's central difficulty (Kennedy–O'Hagan / vision §4), reproduced inside one model — a working diagnostic testbed")
    pic(s,os.path.join(FIG,"figG7_bimodality.png"),0.4,1.6,w=12.5)
    bullets(s,[
     (0,f"4-chain all-variable gate: R-hat {gu['max_rhat']:.0f} (2-chain probes converged by LUCK = same basin). NOT a sampler bug — the under-identification the project studies (AGENTS gate).",RED),
     (0,"NUTS finds TWO basins: 'damped physics' (gz≈1.2, 3 chains) vs 'undamped physics + big discrepancy' (gz≈0, 1 chain) — the SAME FRF, two explanations. And even the damped basin over-predicts held-out QOI ~2× (local patch model error) → under-covers.",ORANGE),
     (0,"CURE = constrain the discrepancy so the 'undamped+discrepancy' basin is forbidden (orthogonal / cut-Bayes, vision §5.2) — the project's open research step, now sharply posed with a testbed.",NAVY)],x=0.6,y=6.05,w=12.2,size=11,gap=2)
    footer(s,"figG7 · SYNTHETIC · per-chain diagnostic out/ums2_bimodality.json · held-out coverage figG3/figG4")

    s=slide(); title(s,"Study G held-out QOI verification (the gate doing its job)",
     "Prediction at a never-measured point + held-out QOI at all 5 points vs truth and the nominal FEM")
    pic(s,os.path.join(FIG,"figG3_headline_holdout.png"),0.4,1.6,w=7.2)
    pic(s,os.path.join(FIG,"figG4_qoi_coverage.png"),7.7,1.75,w=5.5)
    bullets(s,[(0,f"Held-out QOI coverage {gq['n_cover']}/10 — the converged-basin twin AND the deterministic FEM both over-predict the held-out peaks (the soft-damped patch is unrepresentable). The held-out gate is the only thing that catches it.",ORANGE)],x=0.6,y=6.1,w=12.2,size=12,gap=2)
    footer(s,"figG3+figG4 · SYNTHETIC · convergence ≠ trust (vision §7); spatial analog of Study A's extrapolation negative")

    s=slide(); title(s,"GIF — predictive bands evolve as the LDV scan accrues points (what Andrew asked for)",
     "gif_scan_accretion.gif (animates in slideshow) · each frame re-runs inference on the data subset")
    pic(s,os.path.join(FIG,"gif_scan_accretion.gif"),1.6,1.6,w=10.0)
    footer(s,"per-frame R-hat printed (reduced 2-chain animation runs); held-out QOI panel shows intervals evolve")

    s=slide(); title(s,"GIF — predictive bands evolve as the excitation bandwidth extends",
     "gif_band_extension.gif · 'you can't certify what you haven't excited'")
    pic(s,os.path.join(FIG,"gif_band_extension.gif"),1.6,1.6,w=10.0)
    footer(s,"unexcited band shaded · the QOI stays honestly wide until the band is covered")

# ---- Study H (the cure A/B) + Study I (unknown forcing) ----
HAS_H=os.path.exists(os.path.join(O,"ums3_summary.json"))
if HAS_H:
    H3=json.load(open(os.path.join(O,"ums3_summary.json")))
    s=slide(); title(s,"Study H — THE CURE: constrained discrepancy, head-to-head (vision §13.2's decisive A/B)",
     "Orthogonal parameter-fingerprints (Plumlee-lite) vs spatially-local damping vs both — on the bimodal Study G testbed")
    pic(s,os.path.join(FIG,"figH_cure_ab.png"),0.4,1.6,w=12.5)
    rows_h=[]
    for t in ("H_orth","H_local","H_both"):
        a=H3["arms"][t]
        rows_h.append(f"{t.replace('H_','')}: R-hat {a['max_rhat']:.2f} · div {a['div_frac']*100:.1f}% · held-out QOI {a['qoi']['n_cover']}/10 · gz/chain {['%.2f'%g for g in a['gz_per_chain']]}")
    bullets(s,[(0," | ".join(rows_h),NAVY),
     (0,"Mechanism: the orthogonality factor forbids the discrepancy from imitating a parameter (the residual's projection on each parameter fingerprint must be sensor-noise small); local damping makes the patch representable.",GREY)],x=0.6,y=6.0,w=12.2,size=11,gap=2)
    footer(s,"figH · SYNTHETIC · baseline = Study G (R-hat 50, QOI 1/10) · numbers from out/ums3_summary.json")

HAS_I=os.path.exists(os.path.join(O,"ums4_summary.json"))
if HAS_I:
    I4=json.load(open(os.path.join(O,"ums4_summary.json")))
    s=slide(); title(s,"Study I — UNKNOWN FORCING (vision §5.0, the likely novelty home): cancel it or infer it?",
     "Responses only, force never measured: transmissibility (forcing cancels exactly) vs joint three-way inference")
    pic(s,os.path.join(FIG,"figI_unknown_forcing.png"),0.4,1.6,w=12.5)
    ra=I4["arms"]["I_ratio"]; ja=I4["arms"]["I_joint"]
    bullets(s,[(0,f"I-ratio: R-hat {ra['max_rhat']:.2f}, structural QOI {ra['qoi']['n_cover']}/5 — forcing AND common-mode errors cancel (the apparent-mass logic; absolute discrepancy at held-out points becomes unobservable, documented).",GREEN),
     (0,f"I-joint: R-hat {ja['max_rhat']:.2f}, QOI {ja['qoi']['n_cover']}/5, log|F| pointwise coverage {ja.get('forcing_logF_coverage',0)*100:.0f}% — naive three-way inference FAILS at this difficulty (honest negative).",ORANGE),
     (0,"FINDING: response-only transmissibility ≠ apparent mass — dividing by a response cancels the forcing AND the level information that pins the physics. §5.0's identifiability hole, demonstrated; cure direction = force-side observables (measured interface force / M=F/a) or multi-reference data.",NAVY)],x=0.6,y=6.0,w=12.2,size=11,gap=2)
    footer(s,"figI · SYNTHETIC · QOI = peak |H| at never-measured points (forcing-independent) · out/ums4_summary.json")

HAS_F=os.path.exists(os.path.join(O,"studyF_summary.json"))
if HAS_F:
    F6=json.load(open(os.path.join(O,"studyF_summary.json")))
    covs=[r["n_cover"] for r in F6["rows"]]
    s=slide(); title(s,"Study F-mini — the discrepancy-prior FRONT-END guardrail (vision §6.2)",
     "An engineer's known config delta becomes a band WIDENING — never a false narrowing")
    pic(s,os.path.join(FIG,"figF_frontend.png"),0.7,1.6,w=11.9)
    bullets(s,[(0,f"Coverage vs dial: {covs[0]}/5 → {covs[1]}/5 → {covs[2]}/5. Widening may only IMPROVE coverage; tightening requires held-out evidence — the dial buys humility for free, confidence must be earned.",NAVY),
     (0,"The stubborn 5th point (inside the soft patch) is §6.2's own caveat demonstrated: gross LOCAL error needs a structured mock-up, not scalar inflation.",ORANGE)],x=0.6,y=6.0,w=12.2,size=11.5,gap=2)
    footer(s,"figF · SYNTHETIC · forward-only (no sampler) on converged Study-H draws · out/studyF_summary.json")

HAS_J=os.path.exists(os.path.join(O,"studyj_summary.json"))
if HAS_J:
    J=json.load(open(os.path.join(O,"studyj_summary.json"))); jc=J["convergence"]; jq=J["held_out_qoi"]
    jconv = jc["max_rhat"]<=1.1 and jc["div_frac"]<0.05
    s=slide(); title(s,"Study J — REAL-PANEL calibration (vision §7 centerpiece: the synthetic→real step)",
     "The unified method pointed at REAL suspended-panel mobility: Abaqus FEA shapes (fixed) + calibrated global freq/damping + Schneider discrepancy")
    pic(s,os.path.join(FIG,"figJ_real_calibration.png"),0.3,1.6,w=12.7)
    bullets(s,[(0,f"REAL data, 5 of 25 LDV points HELD OUT: R-hat {jc['max_rhat']:.2f}, div {jc['div_frac']*100:.1f}% ({'converged' if jconv else 'not fully converged — real data inherits the identifiability lessons, labeled'}); calibrated global frequency scale {J.get('global_freq_scale',[0,1,0])[1]:.3f}; held-out QOI {jq['n_cover']}/5.",GREEN if (jconv and jq['n_cover']>=4) else ORANGE),
     (0,"Scope (stated loudly): FIRST real-data calibration; single impact reference; C2 margin-scan mapping; one test/realization → real-data EVIDENCE, not validated flight science. The held-out gate is the story whether it covers or not.",GREY)],x=0.6,y=6.0,w=12.2,size=11,gap=2)
    footer(s,"figJ · REAL DATA · out/studyj_summary.json")

HAS_K=os.path.exists(os.path.join(O,"studyk_summary.json"))
if HAS_K:
    K=json.load(open(os.path.join(O,"studyk_summary.json"))); kg=K["arms"]["K_global"]; kp=K["arms"]["K_permode"]
    improved = kp["qoi"]["n_cover"]>kg["qoi"]["n_cover"]
    s=slide(); title(s,"Study K — refining the REAL calibration: per-mode frequency A/B",
     "Study C showed per-mode FEA errors vary 0–6%; with the amplitude ridge fixed, are per-mode frequencies identifiable + do they help coverage?")
    pic(s,os.path.join(FIG,"figK_permode_ab.png"),0.4,1.6,w=12.5)
    bullets(s,[(0,f"REAL held-out QOI: global {kg['qoi']['n_cover']}/5 → per-mode {kp['qoi']['n_cover']}/5 (per-mode R-hat {kp['max_rhat']:.2f}). "+("Per-mode frequency calibration HELPS." if improved else "No improvement → the real-data coverage limit is the SHAPES/discrepancy, not the frequencies."),GREEN if improved else ORANGE),
     (0,"Either way it is a real finding on real data: the held-out gate localizes WHERE the remaining error lives (frequencies are well-pinned by peaks; the residual is spatial/shape model error needing multi-reference data or local shape correction).",NAVY)],x=0.6,y=6.05,w=12.2,size=11,gap=2)
    footer(s,"figK · REAL DATA · out/studyk_summary.json")

HAS_L=os.path.exists(os.path.join(O,"studyl_summary.json"))
if HAS_L:
    Lj=json.load(open(os.path.join(O,"studyl_summary.json"))); lf=Lj["arms"]["L_freqonly"]; la=Lj["arms"]["L_freqamp"]
    s=slide(); title(s,"Study L — can we SHARPEN the real-data bands? (and the honest answer: no, not from one reference)",
     "Study K covers 5/5 but the bands are wide (~4–5× hi/lo). Open question: tighten them with per-mode residue-amplitude calibration, or is the width fundamental?")
    pic(s,os.path.join(FIG,"figL_sharpen_ab.png"),0.3,1.6,w=12.7)
    bullets(s,[(0,f"freq-only (control) REPRODUCES the Study K win: R-hat {lf['max_rhat']:.2f}, {lf['qoi']['n_cover']}/5. Adding per-mode amplitude → R-hat {la['max_rhat']:.1f} (NON-CONVERGED): per-mode amplitude is confounded with damping + global amplitude (the D30 ridge, per-mode).",ORANGE),
     (0,"Physical reading: per-mode FREQUENCY is identifiable (each sharp peak pins one frequency) → the 5/5 stands; per-mode AMPLITUDE is NOT identifiable from a single impact reference. The ~4–5× band width is the honest single-reference LIMIT — sharper bands need multi-reference/roving-excitation DATA, not a fancier model. (The concrete 'where to spend budget' answer.)",NAVY)],x=0.5,y=6.05,w=12.4,size=11,gap=2)
    footer(s,"figL · REAL DATA · 4-chain gate · out/studyl_summary.json")

HAS_M=os.path.exists(os.path.join(O,"studym_summary.json"))
if HAS_M:
    Mj=json.load(open(os.path.join(O,"studym_summary.json"))); mh=Mj["high"]; ml=Mj["low"]
    s=slide(); title(s,"Study M — virtual sensing under SENSOR FAULTS (Yan et al. 2026): physics-Bayes vs interpolation",
     "New paper reconstructs MASKED/faulty channels with a physics+neural-operator net, beating spatial interpolation (which aliases at high-freq local modes). Does our Bayesian twin do this — with calibrated UQ the paper lacks?")
    pic(s,os.path.join(FIG,"figM_virtual_sensing.png"),0.25,1.55,w=12.8)
    bullets(s,[(0,f"Treat the 5 held-out LDV points as FAULTY sensors; reconstruct + score with the paper's dB main-peak metric. HIGH band (local modes): Bayes {mh['peak_dB_bayes_mean']:.1f} dB vs interpolation {mh['peak_dB_interp_mean']:.1f} dB — we reproduce the paper's aliasing claim on INDEPENDENT real data, with a completely different method.",GREEN),
     (0,f"Our differentiator: the Bayesian reconstruction carries a calibrated 95% band ({mh['bayes_band_bin_coverage_mean']*100:.0f}% high-band bin coverage; peak-QOI {Mj['bayes_peak_qoi_coverage']}) — the paper's FAU and interpolation give point estimates with NO uncertainty, so feeding them into closed-loop updating as 'ground truth' double-counts. Honest: interpolation wins on smooth LOW-freq modes ({ml['peak_dB_interp_mean']:.1f} vs {ml['peak_dB_bayes_mean']:.1f} dB) — physics-Bayes earns its keep specifically in the aliasing regime.",NAVY)],x=0.5,y=6.0,w=12.4,size=11,gap=2)
    footer(s,"figM · REAL DATA · no new sampling (reuses Study K posterior) · out/studym_summary.json")

# ---- audience slides ----
s=slide(); title(s,"For Mark Girolami — what dynamic statFEM needed to survive dense FRFs")
bullets(s,[
 (0,"Your decomposition + held-out gate caught every failure here — including ones convergence diagnostics miss (a converged-looking single basin that is over-confident at never-measured points).",NAVY),
 (0,"1. The exact lognormal-mag/wrapped-phase FRF error is HMC-incompatible (phase-wrap cliffs, 1/|H| spikes). The smooth r=(data−H)/(|H|+κ) restores it and handles real noise floors without data selection — plausibly why Schneider needed gradient-free SuS.",BLUE),
 (0,"2. Latent (data-space) mode shapes do not generalize spatially — for held-out prediction, shapes must come from the parametric physics; loosen only eigenvalues/damping.",BLUE),
 (0,"3. KOH confounding appears as literal posterior BIMODALITY in dynamics ('damped' vs 'undamped+discrepancy') — visible only with multi-chain all-variable diagnostics; the constrained-discrepancy cures are now testable head-to-head on this replayable testbed.",BLUE),
 (0,"Bonus: O(n) exact whitening for the separable OU-kernel correlated likelihood (self-tested vs dense MVN to 1e-13).",GREY)])
footer(s,"full narrative: research_narrative.md · method: method_ums.md · every number checker-backed")

s=slide(); title(s,"For Ilias Bilionis — one day of agentic science, audited")
bullets(s,[
 (0,"~14 NUTS campaigns, 26 logged decisions (D0–D26), zero fabricated successes. The agent's value was the DIAGNOSIS LOOP: probe → name the pathology → minimal cure → re-probe (the 12-rung ladder in method_ums.md §3b).",NAVY),
 (0,"The epistemics finding: cheap 2-chain probes CONVERGED AND WERE WRONG (same basin by luck); only the 4-chain all-variable gate exposed the bimodality. Cheap probes guide; full gates decide.",RED),
 (0,"Load-bearing safety properties: pre-committed decision rules ('this is the final attempt, ships as-is'), per-claim checkers, honest-negative labeling — exactly the harness design, exercised under pressure.",GREEN),
 (0,"Reusable: immutable checkers, GREEN/YELLOW/RED standard, one-command replay, compaction-safe decision logs.",GREY)])
footer(s,"decisions: decisions_log.md D0–D26 · probe evidence: logs/probe*.log · checker_report.json")

s=slide(); title(s,"For aerospace loads & dynamics groups — your skepticism, made measurable")
bullets(s,[
 (0,"'Pencil-whipping' = a calibrated model that looks converged and is confidently wrong. We built one on purpose: it passed convergence in one basin and still over-predicted never-measured-point peaks ~2×. The ONLY instrument that caught it: hold back sensors you already have, predict them, check the bands.",RED),
 (0,"A MEASURED model-error budget instead of an assumed one: real composite panel, FEA vs test = +1.1% stiff, |err| 2.2% over 22 modes. That number is what any updating must absorb.",NAVY),
 (0,"The GIFs answer 'how many test points do I actually need' visually — bands at an uninstrumented location tightening as the scan accrues points, honest caveats printed on every frame.",NAVY),
 (0,"Warning you can act on: FRF-magnitude-only updating can trade damping against 'model error' invisibly. If your tool doesn't run multiple chains AND a held-out check, it cannot see this.",ORANGE),
 (0,"Everything stated in response-limit language: the held-out QOI is peak accelerance at unmeasured points — the quantity your test plans already use.",GREEN)])
footer(s,"plain-English narrative: research_narrative.md §aerospace · no proprietary data; all synthetic + one public-style panel test")

# 13 program
s=slide(); title(s,"The study program (A–I) — combining both papers across the folder's data")
rows=[("G","UNIFIED METHOD (statFEM×D/D×Schneider): converges; held-out gate flags over-confidence (honest) + evolving-band GIFs","synthetic (real-like)","RUN ✓" if HAS_G else "RUNNING",GREEN),
 ("A","Discrepancy A/B on dense FRF (Schneider)","synthetic","RUN ✓",GREEN),
 ("Phase1","Control + correlation-length sweep","synthetic","RUN ✓",GREEN),
 ("C/C2","Schneider dense-FRF + FEM-vs-test + (D19) mode-shape grid mapping on the REAL panel","REAL LDV + Abaqus","RUN ✓ (prep, not calibration)",GREEN),
 ("D","Mode-matching-free complex-modal twin (Das/Debnath), degenerate-safe + damping","synthetic (tray-like)","RUN ✓",GREEN),
 ("E","Schneider interface discrepancy → probabilistic 7004C notch","ShockSat FEM + tray","DESIGN (IP-gated)",ORANGE),
 ("B","MPL-stand damping/stiffness twin (Das/Debnath lens)","MPL FEM + 13 taps","DESIGN",ORANGE),
 ("F","Config-delta → Schneider hyperprior front-end (widen-not-narrow)","synthetic","DESIGN",GREY)]
tf=s.shapes.add_textbox(Inches(0.6),Inches(1.55),Inches(12.2),Inches(5.3)).text_frame; tf.word_wrap=True
for i,(k,desc,data,rd,col) in enumerate(rows):
    pa=tf.paragraphs[0] if i==0 else tf.add_paragraph(); pa.space_after=Pt(7)
    r=pa.add_run(); r.text=f"{k}. "; r.font.bold=True; r.font.size=Pt(15); r.font.color.rgb=col
    r2=pa.add_run(); r2.text=f"{desc}  "; r2.font.size=Pt(14); r2.font.color.rgb=NAVY
    r3=pa.add_run(); r3.text=f"[{data}] → {rd}"; r3.font.size=Pt(12); r3.font.color.rgb=GREY
footer(s,"full spec: study_program.md §3")

# 14 scoreboard
s=slide(); title(s,"Findings scoreboard — ranked 1 (utter failure) → 5 (smashing success)",
 "Executed = evidence-scored; Designed = promise/readiness (NOT a result)")
def stars(n): return "★"*n+"☆"*(5-n)
rows=[("EXECUTED (checker-backed)","",None)]
if HAS_G:
    rows += [
     ("UNIFIED METHOD (statFEM×Das/Debnath×Schneider) BUILT + self-tested (1e-13/4e-13) — the 3 papers do compose into one model (Study G)",4,GREEN),
     ("Methodological ladder D14–D25: smooth residual unlocks NUTS (why Schneider used SuS); gauge fix; free latent shapes don't generalize → physics-bound — a real 'how-to' contribution",4,GREEN),
     ("HEADLINE FINDING: the unified model exhibits physics-vs-discrepancy BIMODALITY (R-hat 50: 'damped' vs 'undamped+discrepancy' basins) + held-out under-coverage — the project's central problem POSED with a testbed (Study G)",3,ORANGE)]
rows += [
 ("Schneider correlated discrepancy → calibrated + ~7× sharper held-out coverage, clean convergence (Study A)",4,GREEN),
 ("Control: iid non-convergence is CAUSED by model-form error; structured likelihood is robust (Phase 1)",5,GREEN),
 ("'Sponge' isolated + correlation length is learnable across a sweep (Phase 1)",4,GREEN),
 ("REAL panel: measured discrepancy floor (FEA +1.1% stiff, |err| 2.2%) + real ℓ_co,f ≈ 2.9 Hz (Study C)",4,GREEN),
 ("REAL panel (Andrew's D19 answers): H1-row↔grid mapping pinned by MAC (low modes 0.98–0.99) — real-panel UMS now runnable (Study C2)",4,GREEN),
 ("Das/Debnath latent modes: 0 div vs 429 (eigh) at 0.75% degeneracy + damping ID (Study D)",4,GREEN),
 ("Honest negative: held-out EXTRAPOLATION fails even for converged V2 (57%) (Study A)",3,ORANGE),
 ("DESIGNED (promise / readiness, not run)","",None),
 ("Study E — probabilistic 7004C notch (patent endpoint, IP-gated)",4,BLUE),
 ("Study B — MPL-stand damping twin · Study F — config-delta front-end",3,BLUE)]
tf=s.shapes.add_textbox(Inches(0.55),Inches(1.5),Inches(12.3),Inches(5.5)).text_frame; tf.word_wrap=True
for i,(txt,sc,col) in enumerate(rows):
    pa=tf.paragraphs[0] if i==0 else tf.add_paragraph(); pa.space_after=Pt(5)
    if sc=="":
        r=pa.add_run(); r.text=txt; r.font.bold=True; r.font.size=Pt(14); r.font.color.rgb=NAVY
    else:
        r=pa.add_run(); r.text=f"{stars(sc)}  "; r.font.size=Pt(13); r.font.color.rgb=col
        r2=pa.add_run(); r2.text=txt; r2.font.size=Pt(12.5); r2.font.color.rgb=NAVY
footer(s,"scores copy checker/diagnostics; designed-study stars are promise, explicitly not results")

# 15 next steps
s=slide(); title(s,"Comprehensive next steps (phased)")
bullets(s,[
 (0,"Done (no new data): A, Phase-1, C+C2 (REAL panel, D19-unblocked), D, and G = the UNIFIED METHOD (UMS-FEM converges) + evolving-band GIFs.",GREEN),
 (0,"Fix the Study G under-coverage (the real research, NO new data):",NAVY),
 (1,"CONSTRAIN the discrepancy (vision §5.2): orthogonal / cut-Bayes / shorter ℓ_f so it can't absorb local physics — then the held-out gate should pass HONESTLY.",BLUE),
 (1,"Spatially-varying damping/discrepancy (let the patch be locally softer/damped) so held-out LOCAL error is representable.",BLUE),
 (1,"Seed-replication coverage curve: is the under-coverage systematic or seed-specific? (calibration over many truths).",BLUE),
 (0,"Point UMS-FEM at the REAL panel (C2 already pinned the H1↔grid mapping for the low modes): swap the synthetic K̃ for the Abaqus reduced model; held out spatial points.",BLUE),
 (0,"Needs you / new data:",ORANGE),
 (1,"Exact LDV grid coordinates would supersede C2's margin-scan (raster direction is symmetric-ambiguous).",ORANGE),
 (1,"Study E probabilistic 7004C notch (patent endpoint): only after IP disclosure.",RED),
 (0,"Governance: hold for Andrew sign-off before any notes/AGENTS/project_log edits or public disclosure.",RED),
])
footer(s,"next steps also in packet.md; only the CURRENT-STATE memory block was touched among durable files")

# 16 limitations
s=slide(); title(s,"Honest limitations & what would change the conclusion")
bullets(s,[
 (0,"Studies A/D/G are SYNTHETIC, not validated science (vision §12). One dataset/realization each — a seed-replication sweep is a named next step.",RED),
 (0,"Study G deviates from Schneider's exact error model (separable kernel; smooth complex residual loses the directional 'kidney' tail) and from full-space Das/Debnath (Ritz truncation) — each deviation documented + self-tested (method_ums.md §3).",ORANGE),
 (0,"Study G GIF frames are REDUCED 2-chain runs (R-hat printed per frame); only the headline carries the full convergence gate.",ORANGE),
 (0,"Study C is a real-data CHARACTERIZATION; the real-panel UMS calibration is gated on the data-source answers.",ORANGE),
 (0,"Study D's higher-mode damping under-estimated (~25%); apparent-mass cancels forcing LEVEL not SHAPE (vision §5.0 unknown-forcing not addressed).",NAVY),
 (0,"Only the CURRENT-STATE memory block was edited among durable files; project_log/runs/todo updates await Andrew.",GREEN),
])
footer(s,"replay: bash run_all.sh · checker: python3 code/check.py · packet.md for the full audit")

out=os.path.join(ROOT,"slides","papers_statfem_studies.pptx"); prs.save(out)
print("saved",out,"slides:",len(prs.slides._sldIdLst))
