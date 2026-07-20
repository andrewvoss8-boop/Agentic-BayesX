# Parallel runner A — FRF-correlation technique scan (paste into the Claude browser)

> Self-contained: assumes NO repo access. Use web research. Date context: 2026-06.

---

You are a structural-dynamics + model-updating research assistant. I need a rigorous, **source-cited** scan of
techniques for making **frequency-response functions (FRFs)** — not just modal frequencies — correlate between a
finite-element model (FEM) and modal-test data, for a structure where we are **stuck on per-point FRF amplitude**.
Use web search; cite papers/handbooks; clearly separate established methods from speculative ones; and be honest
about what is fundamentally hard.

## The structure and data (real)
- A tall, stacked **thin-wall aluminum box column**, sections joined by **bolted flange joints**, with an **internal
  bolted cross-brace carrying damping material**, suspended **free-free**, modal-hammer tested in multiple drive
  directions. ~84 accelerometers (100k-g shock accels). Band of interest **45–260 Hz**, which holds a **dense modal
  forest (~16–44 modes)**.
- FEM: a vendor-correlated NASTRAN **shell model + CBUSH spring joints**, **mesh-converged** at ~0.25 in. The
  accelerometers map to FEM grids essentially exactly (sub-0.2-in snap).

## What we found / already tried (so don't re-recommend these)
- **Natural frequencies correlate well** (peaks land within a few %; held-out modal-frequency prediction is strong).
- **MAC is ~0.6–0.7**, but the **local per-channel FRFs correlate poorly**: log|H| correlation median ~0.30 even
  after (a) freeing **per-mode damping completely** (measured per-mode ζ) and (b) fitting per-mode participations to
  **all** channels. Per-point peak-amplitude scatter is ~×3–5 (σ≈1.0–1.3 in natural-log amplitude).
- Parameter edits (joint stiffness incl. directional 6-term, per-region modulus, added cable mass) **do not improve
  FRF correlation**; MAC and the per-point FRF metric are **anti-correlated**.
- Mesh is converged and snap is sub-inch, so it is **not** density/placement. A connectivity finding: the internal
  cross is **under-attached** (its edges sit coincident on the walls at ~68 nodes but only ~13 are connected).
- Working physical explanation: per-point response is a **sensitive interference of many overlapping modes**; small
  per-mode local-shape errors (from idealized joints/cross/welds) compound; there is also **cable nonlinearity** and
  **near-field/non-modal** content. Even using the *measured* mode shapes, the per-point scatter only bottoms at
  σ≈0.7.

## Your task — find techniques we have NOT tried that could make the FRFs correlate
Scan the literature and state-of-practice. Cover at least:
1. **FRF-based model updating** — Lin & Ewins Response Function Method (RFM), FRAC/FDAC correlation metrics,
   frequency-domain sensitivity updating; what they assume, what they buy, failure modes on dense-mode structures.
2. **Frequency-domain / spatial model-form error** — e.g., Schneider et al. multiplicative error correlated in space
   **and** frequency, applied to *amplitude* (not just modal screening); Bayesian/Gaussian-process FRF discrepancy.
3. **Substructuring** — treating the **cross/joints as components** characterized from measured FRFs (LM-FBS, de
   Klerk/Rixen/Voormeeren), **virtual-point transformation** (van der Seijs) for multi-DOF joints, **Craig-Bampton
   CMS** with the cross/joints as substructures; transmission-simulator / fixture methods.
4. **Mode-shape expansion / reduction** (SEREP, Guyan, dynamic expansion) to reconcile model and sensor DOF.
5. **Damping** — non-proportional / complex-mode updating (e.g., Das & Debnath incomplete complex modal data),
   structural vs viscous, joint loss-factor models — does correct damping form change FRF correlation materially?
6. **The honest question:** is **per-point FRF amplitude** on a densely-moded, bolted, thin-shell structure a known
   **ill-posed / fundamentally hard** target? If so, what does the field do **instead** at high modal density —
   **band-averaged FRFs, energy/SEA (statistical energy analysis), envelope/MAX metrics, transfer-path/interface
   quantities**? When does the field switch from deterministic FRF matching to statistical/energy descriptions?

## Output (a structured memo)
1. **Ranked candidate techniques** — for each: one-line idea, what it would buy us, key assumptions, cost/difficulty,
   and a citation.
2. **Best fits for our constraints** (coarse-but-correlated FEM, modal-hammer data, dense modes, bolted joints + an
   under-attached cross): which 2–3 to try, and why.
3. **ONE concrete next experiment** we should run, described precisely enough to implement.
4. **Honest verdict** on per-point FRF amplitude: is it worth chasing, or should we switch to a band/energy/interface
   target? Cite the modal-density / SEA crossover guidance if it exists.
5. **Novelty flags** — mark each idea established vs research-frontier; note any that would need a freedom-to-operate
   check if patented.

Be concrete and cite sources. If you cannot verify a claim, say so. Do not pad — a tight, sourced memo is the goal.
