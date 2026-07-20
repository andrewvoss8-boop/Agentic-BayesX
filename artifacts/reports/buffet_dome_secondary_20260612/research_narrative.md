# Buffet-Driven Vibration of Dome-Mounted Secondary Structure
### A representative, uncertainty-aware digital-twin study

*Workspace `artifacts/reports/buffet_dome_secondary_20260612/`. Every number
traces to a JSON in `out/`. Replay foundations: `bash run_all.sh`. Heavy
stages: the `scripts/run_*` orchestrators (detached).*

> **Three honesty flags, up front.**
> 1. **Buffet only** (max-q transonic). Liftoff/ascent acoustics are deferred,
>    so above the buffet roll-off (~tens of Hz) these levels are *low* relative
>    to a real flight — the high band would be acoustically co-driven.
> 2. **Representative, not Terran-R.** Every dimension, thickness, material, and
>    forcing number is an engineering assumption with a confidence flag and a
>    `VERIFY` list (`assumptions_ledger.md`). No live web this session; nothing
>    here is a verified vehicle fact.
> 3. **No data, no sampler, no posterior.** This is forward modelling plus
>    prior propagation. Nothing is calibrated; the NUTS/convergence machinery is
>    not invoked and nothing is claimed about it.

---

## Plain-English summary (for anyone)

A launch vehicle in transonic flight is buffeted by a turbulent, fluctuating
pressure field — gusty, broadband, and only *locally* correlated. That pressure
shakes the airframe, and the shaking travels into the avionics trays and
pressurized gas bottles (COPVs) bolted to the propellant-tank dome. We built a
finite-element model of the dome and its mounted hardware, drove it with a
physically-correct random buffet pressure field, and computed the loads and
vibration those secondary structures feel — **with confidence intervals**, so a
reader sees not just a number but how uncertain it is.

The headline engineering takeaways:
- The loads at the **mounts** of each piece of hardware are set by **that
  hardware's own mount stiffness** and by **how flexible the dome is** — not by
  fine details of the rest of the rocket. That is *why* a coarse model of the
  far-away structure is acceptable and a detailed model of the *local* dome is
  not optional.
- The single biggest driver of *how uncertain* the answer is turns out to be
  **structural damping** and the **buffet pressure level** — both genuinely
  uncertain — so the intervals are wide (a factor of ~5), and honestly so.

---

## For the structural dynamicist

**Configuration.** A 58,662-DOF "fine region": a 2.25 m-radius barrel section
cut at the first ring frame, a box-section load-introduction ring, and a √2:1
ellipsoidal dome (all t≈5 mm equivalent Al), carrying (i) a 600 mm avionics tray
on a six-strut hexapod-style mount with an 8 kg offset avionics box, and (ii) a
30 kg COPV on two cradle bushings. Shells reuse a previously-validated
flat-facet library (QM6 membrane + MITC4 bending; CST+DKT trias; drilling
penalty); a 3D Euler-Bernoulli beam/bar element was added and validated here
(≤0.04 % vs analytic bending/axial/torsion/SS).

**The "valid to 400 Hz" question, answered honestly.** A deterministic
full-vehicle modal model to 400 Hz is mid-frequency and not validatable on a
representative vehicle. We instead resolve the *fine region* to 400 Hz (modal
basis carried to ~820 Hz for truncation margin — 2,019 modes, 672 below 400 Hz)
and **bracket** the far-field with two boundaries: BC-A (bottom ring fixed) and
BC-B (bottom ring tied to a stack mass/inertia). The QOI spread between them is
reported *as* the boundary-impedance uncertainty. It came out small (≈6–10 % on
the punch loads), which says the cut at the first ring frame is far enough that
the secondaries don't "feel" the far field much — exactly the substructuring
argument, now demonstrated rather than asserted.

**Forcing.** Corcos convective wall-pressure cross-spectral density on the
barrel: streamwise/lateral exponential coherence decay (α=0.12 / 0.72) with a
convective phase, Uc=210 m/s, level from rms-Cp=0.04 × q̄=30 kPa (p_rms ≈
1200 Pa), flat-to-50-Hz then f⁻² spectrum. The coherence length shrinks with
frequency (Uc/(α·2πf)) — this *is* "patches of random force with
frequency-dependent correlation." The structural coupling is the joint
acceptance; we compute it exactly via the circumferential circulant FFT
(periodic barrel) plus a 64×64 axial eigendecomposition, verified against the
brute-force full-CSD quadratic form to 1e-15.

**Results (BC-A nominal, 20–400 Hz, buffet-only, see `out/qoi_bcA_summary.json`):**
strut loads 25–37 N RMS; tray net-CG "punch" into the dome 45 N; COPV net
punch ≈38 N; avionics-box acceleration ≈0.3 g RMS. ~0.3 g is *low* by flight
random-vibe standards — expected for buffet-only on a smooth body, and the
buffet-only caveat is doing its job, not hiding a problem.

*Worked correction (the gate doing its job).* The mode-gallery image-QA caught a
~0 Hz COPV spin from two purely-translational mounts. Adding the physically
required rotational mount stiffness left tray/strut/avionics unchanged (≤2 %, as
expected) but did two things to the COPV: the net dome-normal *punch* dropped
~15 %, and — the important one — the **per-mount in-plane shear roughly doubled**
(the mounts now carry moment). That per-mount load is exactly what a bracket
designer sizes to, so the pre-fix free-spin model was *non-conservative*. The
fix was a physics correction, not a cosmetic one; rotational mount stiffness is
now a tracked sensitivity variable. (Lesson worth keeping: "it's just a spurious
mode" was wrong — always check the QOI delta, don't assume.)

**Sensitivity (`out/variant_table.md`).** Re-solves of the parameters most
likely to move the QOI:

| variant | strut | tray punch | COPV punch | avionics az |
|---|---|---|---|---|
| COPV mount soft (×0.1) | ×1.00 | ×1.00 | **×0.40** | ×1.00 |
| COPV mount stiff (×10) | ×1.00 | ×1.00 | ×1.10 | ×1.01 |
| tray joints soft (×0.1) | **×0.20** | **×0.31** | ×1.00 | **×0.31** |
| dome thin (5→3 mm) | ×0.57 | ×0.65 | ×0.42 | ×0.74 |

Two clean physics statements fall out: (1) the substructures are **largely
decoupled through the dome** — a mount or joint change is ~90% local to its own
hardware, with a modest ~15% cross-talk through the shared dome; (2) the **dome
gauge moves everything** (40–75 %), which is the quantitative justification for
resolving the local primary host to 400 Hz rather than hanging the secondaries
on a stick.

**Response-limit proxy (how you'd actually control this in a vibe test).**
Industry response-limits — it limits a cheap accelerometer, not a rare interface
force gauge. The avionics-box acceleration is a valid response-limit proxy for
the tray interface load: at the 55 Hz controlling (suspension) mode the
accel-to-punch coherence is 0.9999, and the proxy gain α = 15 N/(m/s²) is
**invariant to damping (0.06%) and exactly invariant to the buffet level** — so
the limit `a_limit = F_allow/α` is a structural constant, robust to the very
uncertainties (damping, forcing) that give the load its 5× confidence band. The
CG-accel gain equals 1.17× the assembly mass — the NASA-HDBK-7004C effective-mass
relation, read through a sensor. The proxy is valid where coherence > 0.8
(32–300 Hz, 77% of the punch energy) and honestly decouples at the
avionics-on-tray local mode (don't limit there).

---

## For the Bayesian / StatFEM reader

The point of this study, in the program's terms, is **a digital twin whose
output is an interval, and whose interval widens honestly when the model is
ignorant** — never a confident wrong number.

**Where the uncertainty lives.** With no test data, there is no likelihood and
no posterior; the confidence intervals are a *propagation* of documented priors
through the forward model (`ci_mc.py`, 144 draws, explicitly labelled "no
sampler"). The priors: structural damping η ~ LogNormal(ln 0.02, 0.5) — the
dominant lever on resonant response; buffet level Cp ~ LogNormal (PSD ∝ Cp²,
applied analytically); convection speed; a common scale on the Corcos decay; and
the spectrum corner. Structural-form uncertainty (mount/joint stiffness, dome
gauge) enters as discrete re-solves.

**The headline interval** (BC-A, tray net punch RMS): 5/50/95 % = 18 / 40 / 87 N
— a ~5× span, dominated by damping and buffet level. That width is the *product*,
not a blemish: it is the honest statement of what a buffet environment is when
damping and forcing are only known to a factor.

**Two model-error stories the program cares about.** (1) The boundary bracket
(BC-A vs BC-B) is a *structural* uncertainty we cannot resolve without far-field
data, so we carry both and report the spread — the robust-twin "widen, don't
fake" behaviour, here only ~6–10 % because the cut is well-placed. (2) The dome
gauge sensitivity (×0.4–0.75) is the model-form lever: a calibration twin that
ingested a scrappy dome modal test would tighten *this* axis, and the FIM /
identifiability machinery from the sibling studies says which modes carry its
signal.

**What is deliberately not claimed.** No parameter is inferred; no convergence
diagnostic is reported because no sampler is run; the avionics-acceleration
channel is flagged as the future *response-limit proxy* (program §2.2) but not
promoted. The modal basis + linear QOI functionals are exactly the
differentiable-forward ingredients a later NUTS calibration would consume.

---

## Honest limitations (the "what would make this the wrong answer" list)

- **Buffet-only** understates the high band; acoustics deferred (D12).
- **Representative numbers** — not a specific vehicle; the `VERIFY` list must be
  run before any external use.
- **Deterministic coupling not yet cross-checked against a monolithic solve**
  (the P2 "trust test"); the substructuring is internally consistent and the
  BC bracket is small, but the held-out-style monolithic comparison is queued.
- **Linear, viscous-equivalent damping**; no amplitude-dependence, no buffet
  spatial inhomogeneity (protuberances/separation lines carry higher rms-Cp than
  the smooth-body 0.04 used here).
- **CI = prior propagation**, not a calibrated posterior — by construction, since
  there is no data.

---

## Figure guide

- **fig1** geometry — the fine region and what is *not* modelled (far field).
- **fig2** mode gallery — dome-normal shapes with a tray/COPV/host kinetic-energy
  split, showing which modes are local-secondary vs host-dome.
- **fig3** buffet field — the frequency-dependent correlation patches + the
  coherence-length law (the "varied correlation" the brief asked for).
- **fig4** QOI PSDs with the BC bracket drawn as the boundary uncertainty.
- **fig5** validity bookkeeping — modal density and mesh-vs-requirement.
