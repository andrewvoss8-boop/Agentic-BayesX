# Findings — EXACT-EVIDENCE COMPLETION for the full-spectrum FRF study (2026-07-16)

**Status: copied from THIS workspace's checker (`checker_report.json`), never stronger.**
Checker SHA-locked BEFORE any science (`4a01067c921e`), proven RED science-not-run on the empty workspace,
verified unmodified at the end (G12 GREEN). **No sampler ran in this card** — every number below is a
deterministic optimizer/eigensolve result, not a posterior. **The vault (+XY) was not touched.**

This card closes the three evidence holes the accepted adversarial review (D17) left open. It does not
re-litigate the review; it supplies the missing numbers. **Both pre-registered questions were answered, and
both answers land on the "does not clear the bar" side — which was a valid, pre-registered outcome.**

---

## First-pass method summary (what was actually computed)

| | |
|---|---|
| **Quantity (all scores)** | **P1′** = median-over-channels fractional correlation between predicted and measured **log₁₀\|H1\|** (accelerance, g/lbf), after a TRAIN-side frequency warp and **one global gain per fold**. Dimensionless, gain-invariant. Higher = better. No per-channel/per-mode amplitude least-squares anywhere (checker-grepped, G03 GREEN). |
| **Bands** | sub-200 Hz \[45, 200) — the band the pre-registered S1/S2 bars live in; 200–500 Hz \[200, 500). 500 Hz–ceiling stays `not_certified` (FEM basis credible to 639 Hz; the 1.25× modal-truncation rule caps scoring at 511→500 Hz; study D11). |
| **Data count** | 4 dev drives (LODO folds): `m_xpos_990x`, `m_zpos_990z`, `m_ypos_990y`, `m_zpos_900z`. Measured NASA ShockSat modal-hammer data. Vault `m_xy_990xy` **not read**. |
| **Inferred here** | ONLY the arm-C shape field (T1), by deterministic multi-start L-BFGS-B MAP, refit independently per fold on that fold's 3 TRAIN drives. |
| **Reused verbatim, NOT re-optimized** | every candidate's θ_MAP (study `theta_maps.json`), the scoring machinery, the band definitions, and the S1/S2 bars. This card cannot flatter any candidate by re-tuning it. |
| **Not inferred / unresolved** | posterior uncertainty for arms B and C. Their NUTS was multimodal/non-converged (**worst R-hat 360.6, min ESS 2.0**); they are scored at a MAP point. Per review C2, the amplitude likelihood is *locally stiff* but **globally unidentified** — MAP scores are optimizer results only. |
| **Sampler** | **none** (AGENTS Sampler Decision stated in `decisions_log.md` D0). NUTS/HMC remains the project default for Bayesian updating; this card makes no new posterior claim, so no sampler was required. |
| **Compute** | CPU (Mac, 16 GB, float64), BLAS pinned to 1 thread. 28 sparse shift-invert eigensolves (k=200, 399,510 DOF), strictly serial, one process each. active 7.48 h ≤ elapsed 7.72 h. |

**Assumptions:** inherited wholesale from the study's `assumptions_ledger.md` (window/distillation constants,
survey ζ, band definitions, θ prior σ_log=0.25, coherence mask ≥0.6). This card adds exactly three of its
own, all recorded in `decisions_log.md` D0 and flagged **[ASSUMED, not confirmed]** in
`priority_deliverables.md`:
1. "all 28" = the 28 rows of `query_log.jsonl` (the 29th spec `wr3_rnd001` is a recorded build failure, never
   scored → excluded-with-reason, never substituted);
2. T1 refits the shape field at θ=ones on the enriched basis (θ_MAP folded in), θ itself held at the study's MAP;
3. paired SE = std(per-fold deltas, ddof=1)/√4 — **verified to reproduce the repair's S1 and S2 SEs exactly**.

---

## Q1 — Does an honestly-computed arm-C exact score still beat A1-exact?

### Answer: **"C DENTS"** — yes it beats A1, by **+0.0458 ± 0.0361**, but it MISSES the S1 bar on both criteria.

| | sub-200 P1′ |
|---|---|
| arm C exact, **honest** (4 per-fold refits, leakage-free) | **+0.1595** |
| A1 exact (same enriched basis, same folds) | +0.1137 |
| **paired delta C − A1** | **+0.0458 ± 0.0361** (per-fold: +0.0132, −0.0343, +0.0721, +0.1322) |
| S1 rule (≥ +0.05 **AND** ≥ 2×SE = 0.0722) | **NOT MET** — fails both (+0.0458 < +0.05; delta is 1.27×SE) |
| 200–500 Hz | C +0.0314 vs A1 +0.0335 → −0.0021 ± 0.0244 (no effect) |

Leakage audit GREEN (checker G04): 4 distinct MAP files, no fold's MAP saw its own held-out drive, each
trained on exactly the other 3. **The shape wall stands, dented — now on leakage-free evidence.** The study's
H1 verdict survives; two of its supporting sentences do not.

### Q1 finding 1 — the study's 0.1570 was **right by accident**: two defects nearly cancelled

I reproduced the study's arm-C exact path exactly and decomposed it (`out/leak_probe.json`):

| path | sub-200 |
|---|---|
| the study's actual path (leak **+** basis mismatch) | **+0.1570** ← reproduces their reported 0.1570 exactly |
| **leak only** (fold-1's MAP everywhere, correct basis) | **+0.2417** |
| **honest** (per-fold MAPs, correct basis) | **+0.1595** |

**Leak = +0.0822. Basis mismatch = −0.0847. Net = −0.0025.**

- The leak the review caught (C6) was **not benign** — it inflates the fold-mean by **+0.082** (+0.067/+0.081/+0.180 on the three leaked folds).
- **A second defect the review did NOT catch:** `rescore_freeze.py:78` loads the shape MAP that `arm_c_score.py`
  fit on the **A0_wide θ=1 basis** (r=209, 18 matched modes, r0=106) and applies those raw coefficients to
  the **A0_wide__enr θ_MAP basis** (r=194, 19 modes, r0=108). Shape-field coefficients are **coordinates in a
  specific eigenbasis**; the two bases have different eigenvectors. This transplants coefficients between
  incompatible coordinate systems, deflating the score by **−0.085**. It did not crash — the arrays merely
  broadcast — so it failed **silently**.
- **Why this matters:** had anyone sanity-checked the leaky 0.1570 against an honest 0.1595 and seen
  agreement, they would have concluded the leak was harmless, and the basis mismatch would still be live.
  **Near-agreement between a defective number and a correct one is not evidence that the defect is harmless.**
- *(I got this wrong first: my own D1 concluded "the leak barely mattered." D2 corrects it. The probe, not
  the intuition, caught it.)*

### Q1 finding 2 — "on the exact basis C's lead collapses" is **wrong as stated**

The study wrote that C's lead collapses on the exact basis (0.189→0.157). C's **absolute** score does drop —
but **A1 drops too** (0.145→0.1137). **C's lead over A1 is essentially unchanged: +0.044 screening → +0.046
exact.** The exact basis deflated *both* arms, not C's advantage.

**Corrected statement:** *amplitude-trained shape inference buys a real, basis-robust ~+0.046 sub-200 gain
over A1 that is too imprecise across drives to clear the pre-registered bar.* What fails S1 is **precision,
not collapse** — the per-fold deltas run −0.034 … +0.132.

**Pre-registered falsifier, triggered and reported:** the folds disagree that much, so the fold-mean is a
weak summary. The honest reading is that **C's benefit is drive-dependent, not a scalar** — reported here
rather than hidden inside the mean.

---

## Q2 — Does the agent-ties-random conclusion hold under a full exact re-rank, under both selection conventions?

### Answer: **YES — it holds under BOTH conventions.** Agent does not beat equal-budget random either way.

All **28/28** candidates exact-scored, **0 excluded** (checker G06 GREEN). Pipeline validation: my independent
re-enrichment + re-score reproduces the study's exact **D = 0.1634** and **R = 0.1651** to **0.0000**
(G07 GREEN).

| convention | agent | random | delta ± paired SE | S2 rule (≥1×SE) |
|---|---|---|---|---|
| **(a) screening-selected, exact-scored** (the study's) | `wa2_brackets_soft` | `wr2_rnd001` | **−0.0017 ± 0.0094** | **NOT MET** |
| **(b) exact-selected** (winner's-curse-honest) | `wa2_tbox_xbeam` | `wr2_rnd001` | **+0.0115 ± 0.0158** | **NOT MET** (0.73×SE) |

**(a) reproduces the repair's −0.0017 exactly.** So the study's headline S2 number survives a full re-rank.

**H2 impotence now stands on firmer ground than the study had.** The claim is no longer "the two screening
winners tie" — it is **"the best of 14 agent proposals does not beat the best of 14 random proposals on the
trustworthy basis."** That is a stronger negative result, obtained by removing the reviewer's C1 objection
rather than arguing with it.

### The honest nuance: the sign flips, but not far enough to matter

Under exact selection the agent is **nominally ahead (+0.0115)** rather than behind (−0.0017). I will not
call that a win: it is **0.73×SE**, below the pre-registered 1×SE bar, and a per-track *maximum* over 14
noisy candidates carries selection noise in **both** arms. But it is worth stating plainly, because it means
**the study's −0.0017 was not evidence that the agent is worse than random** — it was evidence that the
particular candidate screening happened to crown was unlucky.

### Rank agreement — screening DID mis-order the agent track

| track | Spearman (screening vs exact) | top-1 agrees? | mean inflation (screening − exact) |
|---|---|---|---|
| agent | **+0.525** | **NO** — screening crowned `wa2_brackets_soft`, exact crowns `wa2_tbox_xbeam` | +0.0052 |
| random | **+0.635** | yes (`wr2_rnd001`) | +0.0086 |

This is the mechanism, and it cuts two ways:
- **Against the study's shortcut:** +0.525 is *moderate*, not high. The θ=1 basis genuinely re-ordered the
  agent field, and **the study's convention (a) crowned the wrong agent candidate** — `wa2_brackets_soft`
  loses 0.0161 on the exact basis and falls from 1st to 5th of 14. The review's C1 objection was
  well-founded: with only 2/28 exact-scored, the study could not have known its agent winner was an artifact.
- **In the study's favour, and this weakens its OWN mechanism:** the reduced-basis distortion is *small in
  magnitude* (mean inflation +0.005 to +0.009; 26 of 28 candidates shift by <0.036). The study's D15 story —
  "the agent's screening lead was reduced-basis inflation" — is **too strong**. Inflation is real but
  modest and hits **both** tracks (random's mean inflation is *larger*, +0.0086). What actually happened is
  better described as **selection noise on a small field**, not a systematic basis bias favouring the agent.

**Scope limitation that Q2 cannot lift (study D16, verified):** all 14 agent candidates were
thickness/scale/split edits — the agent proposed **zero** genuine model-form (mesh/connectivity) changes. So
every H2 statement here means *"the agent tied random within a mostly-parametric edit space,"* **not**
*"agent-proposed geometry/element/connectivity edits were tried and failed."*

---

## Corrected verdicts (`out/verdicts_final.json` — every leaf asserted finite, G05 GREEN)

| criterion | verdict | numbers |
|---|---|---|
| **S1** | **NOT MET** | best eligible arm **D**: +0.0497 ± 0.0174 vs A1-exact. Clears 2×SE (0.0348) but misses the +0.05 bar **by 0.0003**. Arm C's row is now the honest T1 refit. |
| **S2** | **NOT MET under both conventions** | (a) −0.0017 ± 0.0094; (b) +0.0115 ± 0.0158 |
| **S3** | **CANNOT-VERIFY** *(from this card's evidence — see below)* | this card produced no net-CG evidence |
| **S4** | **CANNOT-VERIFY** *(STALE — see below)* | this card produced no net-CG evidence |
| **S5** | **NOT MET**, and **fragile** | Spearman −0.3 at the declared σ=0.25, but +0.139 / +0.367 (finite-only) at σ=0.15 / 0.40; the pre-registered rand10 candidate is absent. The conclusion holds *at the declared width* and must not be stated as width-independent. |
| **arm F** | **= C** by the pre-registered sequential rule | the study collector's **F = R (the random control)** row was invalid and is **deleted** |

### ⚠ S3/S4: my status field is STALE BY SCOPE — Card B has overtaken it
`artifacts/reports/shocksat_netcg_validated_port_20260716/` (runner card B, run in parallel today) has since
made S3/S4 assessable: **N0 GREEN** — driving the ORIGINAL `netcg_qoi.py` + reduced model + reused L5 NUTS
draws reproduces the delivered twin **exactly** (1.508/2.301/2.526, max |err| 0.0000). Its verdicts:
- **S3 = CANNOT-VERIFY-through-this-mapping** (its 3 mapping variants disagree on the rule);
- **S4 = NOT MET / falsified** (normal-Z **widens** to 2.958× vs delivered 2.526×; the rule needed ≤1.9×).

My `verdicts_final.json` still says `CANNOT-VERIFY` for both because **my checker's G05 was SHA-locked on my
card's instruction ("S3/S4 = CANNOT-VERIFY, pointer to Card B") before Card B landed, and a locked checker
must not be edited mid-trial.** Every S3/S4 block therefore carries a `superseded_by_card_B` field with Card
B's real verdict. **This is a checker-scope miss on my part** (`decisions_log.md` D3): I encoded a card
*assumption* as a hard gate instead of the *invariant* the card actually cared about — "this card must not
manufacture S3/S4 evidence." A checker should constrain my conduct, not predict someone else's result.

---

## What this card did NOT do
- **No sampler** → no posterior or uncertainty claim for any arm. Arms B and C remain non-converged
  (R-hat 360.6 / ESS 2.0), and their MAP scores are optimizer points, printed with those diagnostics on
  every figure.
- **No vault read** (+XY untouched); dev drives only.
- **No net-CG work** → S3/S4 unresolved *here* (Card B supersedes; see above).
- **No re-litigation** of the accepted D17 corrections; the repair's S1/S5 numbers are carried, not recomputed.
- **No θ re-optimization** → no candidate was re-tuned by this card.

## Honest limitations
1. **Small field, high fold variance.** 14 candidates/track; the fold-to-fold spread (fold SE ~0.16) dwarfs
   every arm difference. The paired tests cancel that difficulty, but a per-track *maximum* (convention b)
   is still a high-variance statistic. Neither S2 reading should be pushed harder than "no detectable gap."
2. **The 200–500 Hz band is where the real action is** (B +0.197 vs A1 +0.033) and no pre-registered
   criterion tests it. S1/S2 are sub-200 rules. This card did not change that framing, but it is the obvious
   place a future card should look.
3. **Arm C's benefit is drive-dependent** (per-fold deltas −0.034…+0.132), so the +0.046 fold-mean is a weak
   summary of a heterogeneous effect.
4. **A 3-hour swap-thrash inflated wall-clock** (one eigensolve took 11,187 s vs a 506 s median; D4). It cost
   time, not correctness — the affected candidate reproduces the study to 1e-5 with 8.5e-8 % self-consistency.
5. **The exact/screening gap is small**, which means the reduced-basis trap is a *weaker* explanation of the
   study's results than the study claimed — a finding that cuts against the study's own mechanism.

## Replay
`bash run_all.sh` (resumable; ~7.5 h dominated by 28 serial eigensolves, one process each).
Artifacts: `out/armC_exact.json`, `out/leak_probe.json`, `out/exact_rerank.json`, `out/verdicts_final.json`,
`figures/`, `runtime.json`, `checker_report.json`.
