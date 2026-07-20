# Human-Review Packet — ShockSat FRF-Domain Damping Updating (2026-07-10)

**HEADLINE (copied in spirit from `out/verdicts.json`; never stronger than the checker):**
**The pre-registered claim is FALSIFIED on all four gates.** An FRF-domain agentic loop with a genuine
DAMPING action space (band ζ / Rayleigh / per-joint loss factor), FDAC frequency-shift alignment, and the
proven shape/stiffness edits did NOT improve the inherited ShockSat FEM's held-out per-sensor FRF prediction
beyond its calibration noise (**S1 fail**), lost to an equal-budget random search (**S2 fail**), no arm cleared
the net-CG coverage honesty gate (**S3 fail**), and — the real question — **any gain was NOT attributable to
damping; the damping lever actively hurt held-out prediction (S4 fail, damping share −0.10).** The mechanism is
new and clean: **the 2 Hz distilled FRFs cannot resolve ShockSat's light damping** (half-power bands ≤ ~1 line),
so fitting damping fits the peak-sampling aliasing, not physics — and pushes ζ to the physical gate ceiling.
This is a valid, evidence-backed falsification, reported as such, not a pipeline failure.

Replay: `bash run_all.sh`. Checker: `check.py` (SHA-locked `CHECKER.sha256`, immutable; `checker_report.json`
is the status source of truth). All decisions: `decisions_log.md` D0–D11 (append-only).

## 0. First-pass method summary
- **Question (pre-registered, `question_framing.md`):** can an FRF-domain updating loop with a DAMPING action
  space + FDAC-aligned scoring beat (a) the modal-only baseline A0, (b) the completed run's shape-only result,
  and (c) equal-budget random search on held-out per-sensor FRF amplitude, confirmed on a vault — AND is any
  gain attributable to DAMPING (not shape/θ)?
- **Forward model:** reduced modal-superposition FRF (reused Card-D FE layer, 80/128 modes, own basis),
  H(ω) = −ω²·Σᵢ (U_s,i U_k,i)/Dᵢ, with the **damping action space** entering the resolvent Dᵢ:
  viscous band-ζ / Rayleigh (Dᵢ=ωᵢ²−ω²+2jζᵢωᵢω) or structural per-joint loss factor
  (Dᵢ=ωᵢ²(1+jηᵢ)−ω², ηᵢ=Σ_g η_g·SE_{i,g}, SE = modal strain-energy fraction in CBUSH joint group g). All
  damping is LOW-DIM + PHYSICAL (≤10 params, ζ∈[0.2%,5%], η≤0.2); **no per-mode/per-channel amplitude or
  damping fit** anywhere in selection (checker-audited markers).
- **Likelihood / fitting (selection):** θ_MAP of the modal-frequency posterior (lognormal prior sd 0.25,
  Gaussian on paired eigenvalues sd 5%, frozen Hungarian pairing) + train-fit low-dim damping (frozen for the
  dev drive) + ONE global dB gain per fold. Multi-start deterministic MAP; every decision-relevant score is
  EXACT-BASIS (reused enriched `_enr` packages, spot-checked ~1e-7).
- **Metrics (`quantity_contracts.md`):** **P1′** = FDAC-aligned FRAC (median per-channel corr of log|H| after
  the train-side frequency warp); **P2′** = FRSF amplitude error |FRSF−1|; **P3** = raw log|H| correlation (the
  completed run's metric, for comparability). P1′−P3 = the alignment gain.
- **Data:** TRAIN = 33-mode .ash survey + in-fold drives; DEV = leave-one-drive-out over 4 drives
  (+X/990x, +Z/990z, +Y/990y, +Z@900z), scalar scores, budgets agent 21/60, random 40/60; VAULT = +XY/Test04,
  graded ONCE post-freeze. ~111 channels/drive, 105 lines 45–260 Hz (~2 Hz).
- **Inferred / fixed / not-inferred:** θ per group + band-ζ (NUTS finalists, below); fixed pairing, band,
  free-free BC; deliberately NOT inferred: per-mode/per-channel amplitude, input level (absorbed in gain).
  **Per-mode damping is NOT-inferred by necessity** — unidentifiable at 2 Hz (Gate D2).

## 1. Verdicts (`out/verdicts.json`; exact-basis freeze set)
| gate | result | numbers |
|---|---|---|
| **S1 improvement** | **FAIL** | best agent arm a04_enr (weld-thinning shape) dev P1′ **0.2337** vs A0_enr **0.1969**, margin **+0.037** (needs ≥+0.05 AND ≥2×fold-SE = **0.26**). Nowhere near the noise floor. |
| **S2 intelligence** | **FAIL** | agent best 0.2337 < random best **rnd003_enr 0.2389** — random search wins (same as the completed run). |
| **S3 honesty** | **FAIL** | net-CG statFEM F(k) coverage below the 0.95 hard gate (the +Z@900 shear-gap class, unchanged from the netcg thread); leave-modes-out and physical-damping bounds OK. |
| **S4 attribution** | **FAIL** | **damping-only margin −0.004, shape-only +0.037, damping share −0.10** → "improvement is shape/θ; DAMPING lever unproven." A0d (damping baseline) scores **0.1931, BELOW A0** — damping updating hurts held-out prediction. |
| **Overall** | **pre-registered claim FALSIFIED** | valid, reportable outcome |

**Exact-basis dev P1′ leaderboard:** A0 0.197 · A0d(damping) 0.193 · shape c06 0.228 · shape a04 0.234 ·
shape+damping 0.226 · random 0.239. Raw P3 for A0_enr = **0.2152**, which **reproduces the completed
true-remodel run's exact-basis A0 exactly** (pipeline cross-validation).

## 2. The mechanism (why damping — the new lever — fails)
1. **The 2 Hz caches cannot resolve damping (Gate D2, `out/gate_D2.json`).** Survey modal damping is
   ζ=0.06–1.05% (median 0.32%); half-power bandwidths 2ζf = 0.2–2.5 Hz span **0.1–1.25 frequency lines**
   (all 33 in-band modes < 1.5 lines). On a synthetic FRF at 2 Hz + realistic noise, per-mode ζ recovery error
   is **27% in that regime vs 14% best-resolved** → per-mode/narrow-band ζ is NOT identifiable; only a
   band-average ζ is weakly constrained.
2. **So fitting damping fits the aliasing.** The under-sampled peaks are measured off-peak → the data "looks"
   more damped than it is. The A0d fit drives ζ UP to **1.5–2.5%** (band4), the NUTS FRF-amplitude posterior
   rails ζ to the **5% gate ceiling** — both chasing the aliasing artifact, not physics. It does not generalize:
   A0d's held-out P1′ (0.193) and P2′ are no better than A0.
3. **FDAC global-scale alignment does not help either (real data).** θ_MAP already aligns the modal
   frequencies, so the estimated warp ρ ≈ 0.98–0.99 (≈1% residual) and **alignment gain ≈ −0.01** — the
   completed run's low P1 is NOT a global frequency-misalignment artifact. (Control: on a synthetic 5% shift,
   the same machinery lifts FRAC 0.69→0.997, Gate F — so the tool works; there is just nothing to fix here.)
4. **The residual is reachable, not gross-unobservable (Gate O, `out/gate_O.json`).** Only **7% of measured
   in-band shape content is unobservable** at the 132-DOF sensor set (93% reachable) — so the wall is shape
   fidelity + amplitude, not a rank-deficient sensor set — though self-MAC max off-diag **0.997** and Fisher
   rank **36/40** show the sensors do alias some mode pairs.
5. **Shape stays null.** The best shape edit (a04) gives +0.037, below the +0.05 bar and ≪ 2×fold-SE, and
   loses to random — the same per-node shape wall the completed run found, now a third way.

## 3. Vault (graded once; `out/vault_scores.json`)
| finalist | dev P1′ | vault P1′ | dev→vault gap |
|---|---|---|---|
| A0 (bar) | 0.197 | 0.420 | +0.22 |
| A0d (damping) | 0.193 | 0.456 | +0.26 |
| shape c06 | 0.228 | 0.502 | +0.27 |
| shape a04 (dev winner) | 0.234 | 0.470 | +0.24 |
| shape+damping | 0.226 | 0.526 | +0.30 |
| random | 0.239 | 0.497 | +0.26 |

Every finalist jumps **+0.22 to +0.30** from dev to vault — a **uniform location effect** (the +XY drive is
the "easy" location, same as the completed run's uniform gap), NOT a generalization win for any candidate.
On the vault the ordering even flips (A0d > A0, shape+damping highest), but this is the location effect, not
damping value: **S1 requires the DEV (steering) leg to pass first, and it does not** (winner a04 dev margin
+0.037, vault leg positive 0.470 > 0.420 but the dev leg fails). Median in-band vault coherence 0.88 (usable).
Honest label: the vault is held out from THIS run's selection, not never-seen-by-any-run.

## 4. NUTS finalists (θ + band-ζ; `out/nuts_*.json`)
| finalist | R-hat | ESS | div | band-ζ posterior median | converged |
|---|---|---|---|---|---|
| a04 (dev winner) | 1.002 | 792 | 0 | [4.9%, 5%, 5%, 5%] | **yes** |
| c06 (shape) | 1.005 | 423 | 0 | [2.7%, 5%, 5%, 5%] | **yes** |
| A0 (baseline) | 24.8 | 2 | 0 | [4.9%, 4.0%, 5%, 5%] | **no (YELLOW)** |

Damping enters a differentiable FRF-amplitude likelihood (θ from the modal-frequency likelihood; mode shapes
frozen at MAP — labeled). Two findings: (i) in **every** finalist the band-ζ posterior **rails to the 5% gate
ceiling** — the honest Bayesian statement that the 2 Hz data cannot pin the damping (it wants ever more, chasing
the aliasing); (ii) the **A0 baseline posterior does NOT converge (R-hat 24.8, ESS 2)** — its θ posterior is
**multimodal / under-identified** (the "basin lottery" the completed run documented as D19; a Uniform-ζ re-run
reproduced it, so it is not a parameterization artifact). Per the AGENTS identifiability gate this is reported
as **under-identification, not a sampler bug**, and the A0 intervals are labeled not-trustworthy (YELLOW). The
two shape finalists (incl. the dev winner) converged cleanly.

## 5. Validation + mechanics gates (all GREEN in the checker)
- **D1** damping physics: 1/(2ζ) and 1/η analytic peaks reproduced to <0.2% (≤2% gate).
- **F** FDAC/FRAC/FRSF: all 4 synthetic sub-tests pass (identical, frequency-shift recovery, amplitude-scale,
  phase-flip).
- **D2** identifiability: resolution wall certified (above).
- **O** observability: reachable-headroom bound computed (above).
- **V1–V5**: blocks bit-exact (0.0), eig 1.15e-9; free-free RBM 4.6e-12; refinement null median |df| 0.008%;
  t/t³ thickness exact; frozen-pairing churn-proof.
- **Reduced-basis guard:** all decision scores exact-basis (`_enr`, spot-check ~1e-7); the loop's base-package
  scores (labeled) carry the known inflation and no verdict rests on them.
- **Anti-cheat:** selection score carries one global gain + low-dim physical damping only (dim ≤10); no
  per-mode/channel amplitude or damping LSQ (checker grep).

## 6. Winner's curse + reporting discipline
Agent N=21 dev queries, random N=40. Every "best" is best-of-N; all margins ≤ +0.037 with fold 2×SE ≈ 0.26 —
nothing is distinguishable from A0. The falsification does not hinge on any single comparison; damping-only and
A0d fail under every reading.

## 7. Caveats (complete)
- Vault = +XY/Test04 (held out from THIS run's selection, not never-seen-by-any-run; also the "easy" location);
  report the dev-vs-vault gap, do not read a high vault number as a win.
- Damping likelihood in NUTS uses MAP mode shapes (first-order; θ moves shapes negligibly) and a coarse
  channel/frequency subsample for tractability — labeled; damping is unidentifiable regardless (D2).
- Q-leg spectra use the netcg ζ=1% convention; the shear-coverage failure is the family's +Z@900 gap class,
  not an artifact of this run.
- Tufte lint: 3 advisory flags reviewed (ordered 2-series legend; signed-margin bar around a zero line; the
  D2 x-axis is resolution-in-lines, not frequency) — no truncated/misleading axes.

## 8. What this run delivers (for the replace/keep/buy-data human decision)
No arm earns replacement of the inherited FEM. The durable contributions: (i) the **damping lever — every prior
thread's prime suspect for FRF amplitude — TESTED and found unusable on ShockSat's 2 Hz caches**, with the
resolution mechanism quantified (Gate D2) and cross-checked three ways (A0d worse than A0; NUTS ζ rails to the
ceiling; fitted ζ 2–5% vs survey 0.32%); (ii) confirmation that **FDAC alignment does not rescue the correlation
deficit** (θ_MAP already aligns), so the completed run's null was not a metric artifact; (iii) the
**observability bound** (93% reachable → not data-limited-by-subspace, but sensor-aliased). **Next-lever
recommendation (now strongly evidenced): to use damping for FRF-amplitude correlation you must BUY finer
frequency resolution — re-download + re-distill the NASA raw time histories (deleted here) to resolve the
half-power bands — not do more modeling.** MPL test stand (uncorrelated, real headroom) remains the natural
"can an agent correlate from scratch" follow-on.

---

## Addendum (2026-07-11, POST-RUN) — the damping lever, resolved with re-downloaded raw data
Exploratory follow-up after Andrew re-downloaded ONE drive's raw time histories (`Test07_ImpactHammer_990x`,
250 kHz, 1.0 s, 128 accelerometers + 1 force channel). **This does NOT change the frozen verdicts** (checker
still YELLOW; `verdicts.json`/`checker_report.json` unchanged; the run's `query_log` is untouched). Scratch work
in `scratch_test07/`. It answers *why* the damping lever failed, at the signal-processing level.

1. **ShockSat's true damping is light (~0.3%), confirmed two independent ways from the raw decay:**
   band-pass + Hilbert log-decrement (median ~0.5%, clean modes ~0.3%) and multi-output **ERA** (median
   **0.301%**, matched 27/33 survey modes). Both match the .ash survey (0.317%) and decisively refute the
   5% the run's FRF-fit railed to.
2. **Feeding the *physically-correct* 0.3% into the forward model does NOT help held-out FRF** — it is slightly
   WORSE: dev P1′ 0.186 (physical) vs 0.197 (A0 1%) vs 0.193 (FRF-fit). So the damping lever fails even when
   damping is measured correctly from raw data.
3. **Why (the payoff): the 2 Hz FRFs encode WINDOW-broadening, not damping.** The caches were made with a
   ~0.49 s FFT frame → a spectral window ~2 Hz wide, which broadens every resonance to an *apparent* damping of
   ~1–2.5% (2.5% @ 60 Hz → 0.6% @ 250 Hz) regardless of the true 0.3% (a 0.3%/100 Hz mode has a 0.6 Hz
   half-power band, far narrower than the window). Re-scoring the physical-ζ model **convolved with the same
   window** recovers most of the deficit (in-sample corr 0.229 naive → 0.238 windowed → 0.244 A0 1%), and the
   window-equivalent apparent damping matches both A0's workable 1% and the fit's railed 2–5%. The FRF-fit was
   the model *correctly* compensating for frame-broadening.
4. **Consequence for the pre-registered result:** the S4 falsification ("damping lever unproven") stands and is
   now fully explained — on the 2 Hz FRFs the damping signal is not present to be recovered, and A0's default
   1% already approximates the frame-equivalent apparent damping, so there is nothing to gain.

**Sharpened next-lever recommendation (supersedes §8's "buy finer resolution"):** the binding issue is
**analysis resolution / consistency, not modeling and not naive physical damping.** Two paths, both evidenced,
neither needing more than the raw records already in hand for a proof of concept:
- (i) **Resolution-consistent scoring** — process the model FRF with the *same* FFT frame/window as the
  measurement (or, better, recompute both at a longer frame); then the correct light damping is used correctly.
- (ii) **Time-domain / OMA modal identification** (ERA/SSI, done here for +X) to build a lightly-damped modal
  twin scored in the time domain, sidestepping the FRF-resolution problem entirely.
Establishing all of this took **one** re-downloaded drive — the other three drives are not needed to reach this
conclusion. Artifacts: `scratch_test07/{damp_id.py, era_id.py, rescore.py, window_rescore.py, era_result.npz}`.
