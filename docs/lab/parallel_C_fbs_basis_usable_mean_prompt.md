# Parallel runner C — a better FBS basis for an industry-usable twin (or: drop the band, deliver a usable mean)

> Self-contained: assumes NO repo access. Use web research + first-principles design. Date context: 2026-06.

---

You are a structural-dynamics digital-twin architect with deep frequency-based-substructuring (FBS) and
spacecraft-vibration (NASA-HDBK-7004) expertise. I'm hitting a wall with one framing of a Bayesian digital twin and I
want you to **redesign the deliverable** so it's actually usable by an aerospace loads engineer. Use web research for
the established methods (cite them) and be honest about novelty and what's hard.

## Project goal (the why)
Build a **digital twin of an aerospace structure** from **limited dynamic test data + a coarse FEM with model-form
error**, robust enough to give value when the model is wrong, and aimed at a **decision quantity**: a force-limiting /
interface-load / **apparent-mass** environment (NASA-HDBK-7004C), i.e. a **response/force-limit (notch) spec** an
engineer would actually run on Monday. The intended backbone is **FBS** (frequency-based substructuring): apparent
mass `M(ω)=F/a` is an FBS primitive, the interface force (the load that matters) comes from the coupled admittance,
and the model-form error can be placed **at the interface admittance** (output space), localizing it where the model
is most wrong and the load lives.

## The wall we hit (honest, evidence-backed)
We tried to predict the **per-point response FRF/PSD at held-out sensors** with a calibrated band:
- **Frequencies correlate excellently** (held-out modal-frequency skill is strong).
- **Per-point FRF/PSD amplitude does not** — log|H| correlation ~0.30 even with full per-mode damping freedom; the
  honest 95% band is **~+27 dB** (far too wide to certify); on a dense-mode (~16–44 modes in 45–260 Hz), bolted,
  thin-shell structure, the per-point response is a **sensitive interference of many imperfect modes** plus near-field
  + bolted-joint/cable nonlinearity. This per-point amplitude target appears **intrinsically hard** for any global
  model. The structure: stacked thin-wall aluminum boxes, bolted flange joints, an internal bolted cross, free-free
  modal-hammer data, ~84 accelerometers, no instrumented force-limited test (response measured, input is hammer).

So: the **per-point-response + wide-uncertainty-band** framing is **not industry-usable**. I want a better one.

## Your task — two intertwined redesigns; develop both, then recommend
**(1) A better FBS / substructuring BASIS for the twin.** Reformulate the twin so its quantity of interest is an
**interface / drive-point apparent-mass or admittance** (an *integrated*, coupled-DOF quantity), NOT a per-point
interior response. Argue (and check against the literature) **why an interface/apparent-mass QOI should correlate far
better** than per-point response — it's an energy-/area-integrated, low-rank interface quantity, so interior per-point
mode-shape errors largely average out, and it's exactly the 7004C load quantity. Develop:
   - the component/interface decomposition (what are the substructures — e.g., box sections, the cross, the load
     item; where are the interfaces);
   - the QOI: drive-point apparent mass `M(ω)`, coupled interface force, or a **net-CG / response-limit proxy**
     (1–2 sensors highly correlated with the net-CG response at the load-driving modes);
   - multi-DOF interface handling (**virtual-point transformation**, van der Seijs/Rixen) and where the inversion is
     ill-conditioned (the place a Bayesian/uncertainty treatment adds value);
   - where the model-form discrepancy lives (interface admittance, output space) and how the existing test data
     (modal-hammer FRFs, the good frequencies) actually constrains it.
   Ground in: LM-FBS (de Klerk/Rixen/Voormeeren 2008), virtual-point transformation, Craig-Bampton CMS, NASA-HDBK-7004C
   force limiting (apparent-mass / two-DOF), and any **uncertainty-in-FBS** prior art (Trainotti/Häussler/Rixen).

**(2) The pragmatic pivot — drop the band, deliver a USABLE MEAN.** If a certifiable tight band is out of reach,
define a **usable mean-function deliverable**: a best-estimate predicted environment (e.g. a smoothed/enveloped **mean
PSD or apparent-mass spec**) that an aero loads engineer would use **in place of, or alongside, "FEM + margin."**
Specify:
   - the exact deliverable + the metric that makes it "usable" (e.g. GRMS, peak levels, where it must be conservative);
   - the **comparison to current practice** (un-updated FEM + 3/6 dB margin): does the *calibrated mean* (frequencies
     corrected, damping from data, interface/averaged quantity) beat the FEM-mean in a way a loads engineer values —
     even without a tight band;
   - how to keep it honest (where it can be non-conservative, what caveats ship with it).

## Output (a design memo)
1. **The FBS-basis twin** — the decomposition, the interface QOI, why it sidesteps the per-point wall (with a
   literature/physics argument), the discrepancy placement, and what test data is needed (does our modal-hammer data
   suffice, or do we need an instrumented apparent-mass / coupled test?).
2. **The usable-mean reframe** — deliverable, metric, comparison-to-FEM+margin, honesty caveats.
3. **Recommendation** — which path is more likely to be **industry-usable soon**, and **one concrete next experiment**
   (described precisely) to test it — ideally one that reuses modal-hammer FRF data + a coarse correlated FEM.
4. **Novelty / FTO flags** — FBS, CMS, virtual-point, 7004C are mature; mark what's established vs the defensible
   combination (e.g. a Bayesian/discrepancy-aware interface apparent-mass / notch, held-out-validated). Note anything
   needing a freedom-to-operate check (there is known transfer-path-analysis patent prior art).

Be concrete, cite sources, and don't overclaim. The win is a redesign a loads engineer would actually adopt.
