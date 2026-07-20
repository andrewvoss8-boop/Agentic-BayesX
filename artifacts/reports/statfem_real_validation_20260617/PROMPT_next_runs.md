# Runner prompt — Card C: harden + extend the validated StatFEM twin (what to run next)

You are a **runner agent** in **Agentic BayesX**. Lead = Claude Code; human = **Andrew Voss**; advisor objective =
**Ilias Bilionis**: *"evaluate the StatFEM approach… build, evaluate, identify its gaps, and suggest improvements."*
Build for correctness, reproducibility, traceability, continuity. **Plain English**; define every ML/stats/sampling
term/acronym/symbol (with units) on first use; never make a result sound stronger than the files + checker output
support. Structural-dynamics terms (FRF, modal, FEM, damping, mode shapes, MAC) need no gloss.

## 0. RE-GROUND FIRST (before any code; re-do after any compaction)
Read, in order: `AGENTS.md` (every gate binds); then in `artifacts/reports/statfem_real_validation_20260617/`:
`decisions_log.md` (D0–D22 — the spine; read ALL), `packet.md` (esp. §2 verdict, §9 assumptions ledger),
`check.py` (IMMUTABLE), `notes/memory.md` lead CURRENT STATE. Then restate goal / last decision / next action /
open ambiguities in one line. Reuse the existing `code/` (COPY-never-edit the byte-identical scaffolds;
`realfrf.py`, `modal_feature.py`, `modal_ash_mac.py`, `modal_beck_ash.py`, `heldout_qoi.py`, `score.py`,
`tmcmc.py`, `schneider_faithful.py` are yours to extend). Env: `.venv_nuts`, float64, `OMP_NUM_THREADS=1
VECLIB_MAXIMUM_THREADS=1`; long jobs detached + resumable.

## 1. Where things stand (all artifact-backed — do NOT re-derive)
- **WORKS:** modal peak-FREQUENCY likelihood (L5) converges (R̂ 1.002) and gives a calibrated held-out-sensor twin
  (25-split MC coverage ~0.86–0.94, z-std~1) — but **calibrated-but-WIDE (~×3 peak amplitude)**.
- **DEAD END:** whole-FRF magnitude likelihood (NUTS R̂ 104, TMCMC 129, faithful Schneider M2 2.58); Sim A shows it
  needs ≤~1% FEM peak alignment. M3 orthogonal-Schneider STARVES the discrepancy (−105 logZ vs M2).
- **THE WORKING SHARPENING LEVER (just validated):** **L8b Beck-on-`.ash`** (`code/modal_beck_ash.py`) — infer the
  system mode-shape FIELD (Rayleigh quotient + orthogonal-MAC on the `.ash` survey shapes), no eigvec gradient.
  **MC (`out/mc_beck_summary.json`, 25 splits): converged 100%, sharper in 25/25 splits, held-out peak interval
  median 1366→773 (~37% sharper), coverage 0.97.** Paper: Beck, Au & Vanik 2001 CACIE 16:1–11.
- Data hygiene done: `realfrf.BAD_DAQ={29,30,31,101}` excluded (TestLog-flagged). Mapping/reduction verified exact.

## 2. NEXT ACTIONS (priority; each detached + resumable; 1-screen summary per phase)
1. **Make Beck-on-`.ash` the HEADLINE twin and harden it.** (a) Score it on the SAME footing as L5 (full QOI: peak
   |H| AND band-GRMS; proper scores; the 25-split MC distribution — extend `mc_beck.py`). (b) Fold in the **measured
   per-mode damping** from `.ash` (`measured_modes.npz['damp']`, currently UNUSED) into the reconstruction instead of
   the single constant ζ=0.01 — does shape-field + measured damping sharpen further (the ×3 ceiling)? (c) Use MORE
   matched modes (currently 12 of ~20; MAC-matched). (d) Build the held-out-FRF figure with the Beck-inferred band
   vs L5 vs measured at the hard channels.
2. **Spatial-kriging held-out discrepancy (the deferred Schneider transfer).** Replace the *marginal* QOI discrepancy
   with the freq×space GP-conditional transfer (observed→held-out) used in the synthetic `predict.py`. Does the
   correlated transfer SHARPEN vs the marginal at fixed calibration? Compare on the 25-split MC.
3. **Quality threshold τ as a SWEPT variable** (Andrew D9, not yet done): sweep band/peak-keep (full band, w>0.3,
   w>0.5, top-K peaks) and report which τ maximizes held-out proper score.
4. **Complex / phase likelihood (L4, Fathi/Zhang Eq 20, deferred):** circular-Gaussian on Ĥ−H(θ). Caveat: single-hit
   phase is noisy — document it; test whether phase adds anything over magnitude/modal.
5. **`.ash` modal data as a second observable (cross-dataset):** calibrate θ on the `.ash` modes+shapes (MAC-matched),
   predict the impact-hammer held-out FRF QOI; compare to FRF-derived calibration.
6. **Re-validate after the mesh-refinement study (Card D).** When Card D delivers a refined-mesh FEM for the hard
   regions, re-run L5 + Beck-on-`.ash` + the MC on it and report the held-out-QOI improvement at the hard channels.

## 3. Constraints / honesty (non-negotiable)
`check.py` IMMUTABLE; plain ShockSat only; no SOL111/mismatched-path FRF likelihood. NUTS retained as diagnostic;
TMCMC for multimodal posteriors with documented justification (don't edit AGENTS.md). Don't call an arm "failed"
for non-convergence without diagnosis; don't let wide-band coverage masquerade as success; don't pre-decide the
verdict. SURFACE (don't self-apply): the `docs/report/project_log.md` row + `notes/*` (status from checker), any
durable-rule/checker/sampler-standard change, and any scoring weighting that materially changes the verdict.

## 4. WIN CONDITION
A held-out-sensor twin that is BOTH calibrated (coverage ≈0.95, z-std≈1) AND meaningfully sharper than L5's ×3
amplitude bands, robustly across the ≥25-split MC — quantified with proper scores, with the sharpening attributed
to a named mechanism (shape-field correction / measured damping / spatial transfer), and every claim traced to a
checker number.
