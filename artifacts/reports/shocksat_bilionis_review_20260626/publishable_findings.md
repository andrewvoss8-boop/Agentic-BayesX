# The most potent, publishable finding(s)

Andrew's question: *"Across all of this, what is the most potent, publishable finding(s)?"*
This memo ranks them, gives the one-line evidence, the honest novelty/defensibility read, the paper angle,
and the caveats. All numbers trace to the workspaces in `packet.md` / the deck footers.

> Honest framing up front: the **program-level result on the original goal (a sharp, certifiable dynamic
> StatFEM twin) is a NEGATIVE** — we could not make the FRF bands tight enough. The publishable value is
> (a) that negative, stated rigorously with held-out evidence and a quantified cause, and (b) two
> constructive **method** findings that came out of chasing it. A clean, well-evidenced negative + a method
> contribution is a stronger paper than an over-claimed positive.

---

## Finding #1 — "Trustworthy but not sharp": the boundary of dynamic StatFEM on a real, already-correlated aerospace FEM
**MOST DEFENSIBLE. Lead with this.**

**Claim.** On a real, vendor-correlated aerospace FEM, StatFEM/Bayesian updating delivers **trust** but not
**sharpness**: the posterior stays honestly calibrated under large model-form error (held-out **frequency**
coverage good, **+0.93** skill vs a no-skill baseline), but the **FRF-amplitude** bands are irreducibly too
wide to certify (**+27 dB**, ~**10–13×** the FEM+6 dB envelope), and the binding limit is **per-node
mode-shape fidelity** — a *model* problem that **no** statistical lever (damping, inferred shape field,
correlated discrepancy, evidence-based model selection) and **no** agentic remeshing (~30 edits;
0/6000 joint-stiffness points) could close. **Decisive check (ran it):** the best remesh through the actual
Bayesian NUTS on ONE honest metric gives **0.18–0.27**, *below* the inherited FEM + plain calibration (**0.34**)
— the apparent "+0.08" remesh gain was an amplitude-fitting scoring artifact (the generous metric least-squares-fits
one complex amplitude+phase per mode to the measured FRFs; the honest metric fits one global gain). Combining both
best levers does not beat simple calibration; statistics/fitting can mask the shape error, not fix it.

**Why it's potent.**
- It is on **real data**, **held-out validated**, and **honest** — it directly answers the industry
  skeptics' "GIGO / pencil-whipping" charge: the method does not give a confident wrong number; it widens
  and *says so*.
- It quantifies the cause (the mode-shape wall: 54 Hz shape MAC 0.17; shape-oracle σ 1.26→0.70) instead of
  hand-waving "model error."
- The **agentic remeshing boundary** is itself a contribution for Bilionis's autonomous-engineering interest:
  an agent that *proves* mesh/stiffness are not the lever and redirects effort is more valuable than one that
  reports an unverifiable "improved" model.

**Novelty read.** Bayesian FE model updating is mature; StatFEM is mature on benign problems. The novel,
publishable angle is **the regime + the boundary**: StatFEM taken onto real dynamic aerospace data, with a
held-out trust gate, showing *where the wall is and why*. The "already-correlated, relatively simple
structure still needs better shapes for usable FRF bands" is a sobering, citable finding.

**Paper.** *"How far does StatFEM go on a real dynamic aerospace structure — and where the wall is."*
A negative-with-teeth + the new mean-function metric + the agentic-remeshing boundary.

**Caveats.** Single structure; single-impact + clean-multi-ref data; most of the FRF-correlation / wide-CI
work is EXPLORATORY (no immutable checker yet — promote before publication). "Usable" targets (≈+3 dB band,
≈0.7 correlation) are illustrative, not a customer spec.

---

## Finding #2 — The OBSERVABLE and the model-error REGULARIZER (not "where the physics lives") decide well-posedness
**THE METHOD CONTRIBUTION. Honestly scoped after Andrew's 2026-06-26 correction (see "what I removed" below).**

**Claim (corrected), two parts in order of leverage:**
1. **The observable is the primary lever.** A modal-FEATURE likelihood — *physics in the likelihood* — converges
   and predicts held-out modes (L5 R-hat 1.002, 5/5–6/6; Study K R-hat 1.007; Schneider correlated-disc R-hat 1.002
   on synthetic). The **whole-FRF MAGNITUDE** likelihood is **intrinsically multimodal** under real model error
   (Beck–Katafygiotis local identifiability: |H(θ)| is oscillatory, so many θ basins fit the peaks) — for
   **everyone**, IFT included (IFT under NUTS R-hat 264; both IFT and M2 need TMCMC).
2. **On that hard observable, a bounded learned regularizer restores well-posedness.** Holding the whole-FRF
   observable fixed and escalating to TMCMC: IFT's **bounded learned temperature β** converges (cross-run R-hat
   1.0007) and covers (peak 0.97 / band 1.0); M2's **free discrepancy variance σ_d** still fails (R-hat 129,
   σ_d→7.4 variance singularity). The operative cause is the **bounded/learned regularizer**, *not* "prior vs
   likelihood" — an **informative σ_d prior** is the likelihood-side cure (our own StatFEM thread D10 found exactly
   this). IFT/PIFT is one principled way to get the bounded learned knob **and** remove the arbitrary-σ choice (#3).

**Why it's potent.** Practical, mechanism-level guidance for model-form-error-dominated dynamic inversion: pick a
modal/feature observable; if you must use the whole FRF, bound/learn the model-error knob.

**What I removed (the overclaim, per Andrew's catch).** The earlier headline "where you put the physics decides
well-posedness (IFT-in-prior converges vs StatFEM-in-likelihood diverges)" was wrong: physics-in-the-likelihood
converges fine for modal observables, and IFT is *also* multimodal under NUTS. The defensible statement is the
observable + bounded-regularizer one above; the IFT-vs-M2 comparison also confounds prior-vs-likelihood with
bounded-vs-free (the bounded part is the cause).

**Paper.** *"What makes model-form-error-dominated dynamic StatFEM well-posed: observable choice + a bounded learned
model-error regularizer (IFT temperature vs free discrepancy variance)."*

**Caveats.** Both IFT and M2 need TMCMC on the whole FRF; checker-backed YELLOW; the bounded-vs-free attribution is
argued from the σ_d→∞ singularity + the D10 informative-prior cure, not from a fully crossed 2×2 ablation (a clean
follow-up: M2 with an informative σ_d prior vs IFT, same observable).

---

## Finding #3 — A LEARNED model-error knob answers the consistency concern (Bilionis/Alberts/Kairui)
**The clean answer to the stated concern; checker-backed.**

**Claim.** The classical "arbitrary number of physics evaluations / residual-noise σ_r" inconsistency shows up as a
**drift in the posterior θ with σ_r** (controlled toy, truth θ=1.15: θ spread **0.084** across σ_r, vs **0.003**
across the genuine mesh knob). A **learned** model-error knob removes it: both StatFEM's **σ_d** and IFT's **β** are
discretization-invariant (spread ~0.003) and need no hand-set σ. IFT's β additionally reads a quantitative,
**bounded** "distrust" (≈246× below the no-data anchor) rather than running away.

**Honest shared limit (must be stated).** Under genuine model-form error, *none* of the three (classical, StatFEM,
IFT) recovers the physical parameter — all bias θ to ~1.27 (truth 1.15). The discrepancy/temperature **absorbs** the
error rather than **flagging** it (Kennedy–O'Hagan / Brynjarsdottir–O'Hagan confounding). The contribution is
**consistency/robustness**, not "recover true physics from a wrong model."

**Why it's potent.** The direct, numerical reply to the concern Bilionis/Alberts/Kairui raised, with a clean map
(classical → StatFEM → IFT) and a real-data benchmark (Finding #2) behind it.

**Paper.** A section within Finding #2's paper, or a standalone note on consistency of physics-informed inversion.

---

## Cross-cutting (agentic / harness) — convergence ≠ trust
For the autonomous-engineering audience: a converged sampler is **not** a trustworthy twin. Only a **held-out
calibration gate** (and a full 4-chain run) detected over-confidence / under-identification; **cheap 2-chain
probes misled both ways** (a false positive in one synthetic study, a false negative in a real-panel study).
The reusable lesson + the auditable-boundary deliverable are themselves a contribution to "can agents do
trustworthy science."

---

## One-line recommendation
**Lead the review with #1 (defensible, real-data, honest negative + boundary); anchor the method on #2
(observable + bounded learned regularizer — honestly scoped, not "where the physics lives"); #3 is the clean
consistency answer to Bilionis/Alberts/Kairui.** Then decide the next experiment (feature-space discrepancy
and/or a maximally-informative own test) to attack the *model* (shape) wall that Finding #1 isolates — and,
if we want to harden #2, run the missing 2×2: M2 with an informative σ_d prior vs IFT on the same observable.
