# Reader / Web Verification Pass — 2026-06-02 (browsing ENABLED)

Role: READER / VERIFICATION subagent (Opus 4.8), web browsing enabled this session. Scope: confirm or
correct the `[TO-VERIFY]` items the round-1 reader (no web access) could not verify, so the human can
replace placeholder numbers in the gates with source-backed values before round 2.

HARD RULE honored: every numeric claim below is backed by a source I actually fetched and parsed THIS
session (no citing from memory). I did NOT edit AGENTS.md, CLAUDE.md, checkers, or runner code. This
file is evidence + a recommendation for human approval.

## Method / honesty notes
- Fetched with `curl` + parsed text from the live pages/PDFs. Each source is listed with the exact URL,
  HTTP status, and a content hash (first 16 hex of sha256 of the retrieved bytes) for traceability.
- "Supports / does NOT support" is stated per source. Where a number is a spectral *slope* vs a
  *margin*, I flag the distinction (a real trap in GEVS).
- One item (B8, spectral lines per half-power band) could NOT be pinned to a single primary-standard
  number from a retrievable source; it stays `[TO-VERIFY]` and I recommend it remain a documented
  assumption — which matches the task card's own note.

## Sources retrieved this session (raw files in /tmp, not committed)
| key | URL | HTTP | bytes | sha256[:16] | access |
|---|---|---|---|---|---|
| STAN-REF | https://mc-stan.org/docs/reference-manual/analysis.html | 200 | 79615 | 4b3dbd5b160baa93 | public |
| STAN-DIAG | https://mc-stan.org/learn-stan/diagnostics-warnings.html | 200 | 69071 | 5628878d24196f43 | public |
| VEHTARI | https://arxiv.org/abs/1903.08008 (abstract/title) | 200 | 47697 | e4f9873758d878e5 | public preprint (published Bayesian Analysis 2021) |
| IRVINE-PSD | https://www.vibrationdata.com/tutorials2/psd.pdf | 200 | 102826 | 75fc9105d53a5f0c | public PDF |
| IRVINE-RAND | https://www.vibrationdata.com/tutorials2/random.pdf | 200 | 298493 | 658ff59eefceee9d | public PDF |
| IRVINE-HPB | https://www.vibrationdata.com/tutorials2/half_power_bandwidth.pdf | 200 | 150371 | ffa31c8c716c336e | public PDF |
| GEVS | https://snebulos.mit.edu/projects/reference/NASA-Generic/GSFC-STD-7000.pdf (GSFC-STD-7000, Apr 2005, MIT mirror) | 200 | 5086520 | 6e56386c9dcd1443 | public PDF (mirror; supersedes GEVS-SE 1996) |
| ENDAQ | https://blog.endaq.com/vibration-analysis-fft-psd-and-spectrogram | 200 | 74947 | 20048617139c3d40 | public blog (secondary) |

Note on GEVS revision: I retrieved the **base GSFC-STD-7000 (April 2005)** via the MIT snebulos mirror;
the current revision is GSFC-STD-7000A/B. The margin and envelope *language* quoted below is the
long-standing GEVS practice and is unlikely to have changed in revision, but if a checker hard-codes a
GEVS clause, confirm against the **current controlled revision on standards.nasa.gov** (the direct
standards.nasa.gov PDF link I tried 404'd this session).

---

# A. MCMC convergence diagnostics (Convergence Gate)

### A1. R-hat threshold — CONFIRMED: modern threshold is **< 1.01** (not 1.05/1.1)
- **STAN-DIAG** (verbatim): *"We recommend running at least four chains by default and in general only
  fully trust the sample if R-hat is less than 1.01. In early workflow, R-hat below 1.1 is often
  sufficient."* It adds: *"Stan reports R-hat as the maximum of rank normalized split-R-hat and rank
  normalized folded-split-R-hat."*
- **STAN-REF** (verbatim): *"Vehtari et al. (2021) suggest in general to use a threshold 1.01, but
  other thresholds can be used depending on the use case."* Also defines split-R-hat and states
  rank-normalization follows Vehtari et al. (2021).
- **VEHTARI** (title/abstract confirmed): "Rank-normalization, folding, and localization: An improved
  R-hat for assessing convergence of MCMC" — the paper that introduces the rank-normalized split-R-hat
  and the modern recommendations. (I retrieved the arXiv abstract; it confirms the diagnostic but the
  *numeric* 1.01 / >400 recommendations are quoted above from the Stan manual, which attributes them to
  Vehtari et al. 2021.)
- **Disagreement / range:** 1.01 (final, "fully trust") vs 1.1 (early-workflow, weaker) vs the legacy
  Gelman-Rubin 1.05/1.1. No contradiction — these are tiers for different stages.
- **Supports:** a strict final-result gate at max R-hat < 1.01, computed as rank-normalized
  split-R-hat, over all quantities. **Does NOT support:** treating 1.05/1.1 as the *final* bar.

### A2. ESS floor — CONFIRMED: **bulk-ESS > 100 × #chains (≥ 400 for 4 chains)**; tail-ESS too
- **STAN-DIAG** (verbatim): *"For final results, we recommend requiring that the bulk-ESS is greater
  than 100 times the number of chains. For example, when running four chains, this corresponds to
  having a rank-normalized effective sample size of at least 400. In early workflow, ESS > 20 is often
  sufficient."*
- **STAN-DIAG** on tail-ESS (verbatim): *"Tail-ESS computes the minimum of the effective sample sizes
  (ESS) of the 5% and 95% quantiles."* Both bulk- and tail-ESS should clear the floor (bulk for
  location summaries; tail for quantile/interval accuracy).
- **Disagreement / range:** ">400 total (4 chains)" (= 100/chain) for final results vs ">20" early
  workflow. The project's current placeholder "ESS >= 200 for reported parameters" is BETWEEN these and
  is *more lenient than* the Stan final-result recommendation when using 4 chains (400).
- **Supports:** require **both** bulk-ESS and tail-ESS ≥ 100 × #chains for reported parameters.
  **Does NOT support:** a single fixed 200 regardless of chain count — Stan scales it with #chains.

### A3. Divergences — CONFIRMED: target **0**; nonzero implies **bias**, not just inefficiency
- **STAN-DIAG** (verbatim): *"the sampler misses those features and returns biased estimates …
  Even a small number of divergences after warmup cannot be safely ignored if completely reliable
  inference is desired. But if you get only few divergences and you get good Rhat and ESS values, the
  resulting posterior is often good enough to move forward."*
- **STAN-REF / divergence page** (verbatim): a common divergence location is *"the neck of the funnel
  in a centered parameterization"*; fix via smaller step size or *"a reparameterization … so that the
  posterior curvature is more manageable; see the funnel example."*
- **Disagreement / range:** ideal = 0. Practical tolerance: a *few* with good R-hat/ESS *may* be okay,
  but they signal bias risk. A 2%-of-iterations tolerance is a pragmatic engineering threshold, NOT a
  Stan-endorsed number — Stan frames it as "cannot be safely ignored," i.e. investigate, don't
  silently pass.
- **Supports:** treat any divergence as at least a hard-WARN with bias language; ideal target 0.
  **Does NOT support:** silently passing a run with divergences (Codex's 3 divergences should not pass
  clean). The "< 2%" placeholder is defensible as a *fail* line but should be paired with a "0 ideal /
  investigate any" statement.

### A4. Chains ≥ 4 — CONFIRMED
- **STAN-DIAG** (verbatim): *"We recommend running at least four chains by default …"* Split-R-hat
  compares within- vs between-chain variance, so ≥ 4 chains makes the between-chain estimate meaningful.
- **Supports:** the ≥ 4 chains requirement (Cursor's 2 chains is below the recommendation).

### A5. NUTS applicability + funnels / non-centered — CONFIRMED
- **STAN-REF / divergence page** (verbatim, see A3): centered hierarchical "funnels" cause divergences;
  the fix is **reparameterization (non-centered)** or smaller step size. HMC/NUTS simulates Hamiltonian
  dynamics of a continuous, differentiable target; the step size sets the resolution and fails on
  features "too small for this resolution" and where "the log posterior density doesn't have continuous
  derivative everywhere" (i.e. non-differentiable points hurt HMC).
- **Supports:** (a) NUTS/HMC is appropriate for continuous, differentiable posteriors; (b) hierarchical
  variance models need a **non-centered parameterization** unless justified; (c) non-differentiable
  features (peaks/argmax) must be smoothed/relaxed and documented. **Does NOT support** (from these
  sources) any claim about discrete-parameter handling beyond the general HMC-needs-gradients point —
  that is standard but I did not fetch a discrete-marginalization source this session, so leave the
  discrete-parameter wording as general guidance, not a hard-cited rule.

---

# B. Random-vibration quantities + resolution (Discretization Resolution Gate)

### B6. GRMS = sqrt(area under PSD); 3·GRMS = 3σ ≈ 99.73% — CONFIRMED
- **IRVINE-PSD** (verbatim): *"The overall GRMS value can be obtained by integrating the area under the
  power spectral density curve. The GRMS value is then equal to the square root of the area … This is
  equivalent to calculating the 'square root of the sum of the squares.'"* And: *"The RMS value of a
  signal is equal to the standard deviation, assuming a zero mean."* (1σ = GRMS.)
- **IRVINE-RAND** (verbatim, Gaussian zero-mean table): *"-σ < x < +σ 0.6827 68.27% ; -2σ < x < +2σ
  0.9545 95.45% ; -3σ < x < +3σ 0.9973 99.73%."* So **3·GRMS = 3σ ≈ 99.73% peak coverage** for a
  zero-mean Gaussian response.
- **Supports:** the setup's "3·GRMS = three times root-integral of PSD" and its interpretation as the
  3-sigma (~99.73%) peak estimate. **Does NOT support** treating 3·GRMS as a *true max* — random peaks
  exceed 3σ ~0.27% of the time (and the same Irvine doc notes a sample peak of 3.90σ), so 3·GRMS is a
  conventional estimate, not a hard ceiling.

### B7. Half-power (-3 dB) bandwidth Δf = f_n/Q = 2ζ·f_n — CONFIRMED
- **IRVINE-HPB** (verbatim): the -3 dB points are *"the 'half power points' on the transfer magnitude
  curve"*; *"Another damping parameter is the frequency width Δf between the -3 dB points … The
  conversion formula is Q = f_n/Δf"* (i.e. **Δf = f_n / Q**); and *"ξ = 1/(2Q)"* → **Δf = 2ζ·f_n**.
- **Supports:** the half-power-bandwidth definition used in the round-1 resolution analysis exactly.
  No disagreement found.

### B8. Spectral lines within the half-power bandwidth — **NOT VERIFIED to a primary number**
- **What I confirmed:** the resolution *mechanism*. **ENDAQ** (verbatim): frequency bins occur at
  Δf = Fs/N (sample rate / number of samples); longer records → finer Δf. Combined with B7, a lightly
  damped mode at f_n≈86 Hz, ζ≈0.02 has Δf_HP≈3.4 Hz, so a coarse grid clips it (the round-1 mechanism
  is sound).
- **What I could NOT verify:** a specific "≥ N spectral lines within the half-power band" number from a
  retrievable primary standard. The widely-quoted "3–10 lines across the half-power band" rule lives in
  modal-testing texts (e.g. Ewins, *Modal Testing*; B&K/Siemens app notes); I could not open a
  retrievable primary source for the exact number this session (Siemens page was JS-rendered with no
  static text; several candidate Irvine/vendor URLs 404'd).
- **Recommendation:** keep this a **documented assumption**, NOT a hard-coded global density — which
  matches the task card's own note and harness proposal #5. The *requirement* should be: state the
  grid, show the QOI-driving modes are resolved relative to their half-power bandwidth (B7), and run a
  resolution sensitivity check. Do not hard-code "N lines" in the harness until a primary source backs
  the number. Status: `[TO-VERIFY]` (missing: a retrievable modal-testing standard/text page stating
  the exact line count).

---

# C. Qualification vs flight comparison (round-2 task card / quantity contract — NOT a harness rule)

### C9. PSD-envelope comparison + scalar GRMS as summary — CONFIRMED as the defensible check
- **GEVS** (verbatim): the test program is judged by whether *"the previous qualification program has
  adequately enveloped the new mission environments."* GEVS defines **Limit Level** = *"The maximum
  expected flight level (consistent with the minimum probability levels of Table 2.4-2)"* (this is the
  MPE / maximum predicted environment). The random-vibration spec is given as a PSD/ASD shape in g²/Hz
  with an overall GRMS — i.e. the spec is a **spectrum that must envelope the flight environment across
  frequency**, with the overall GRMS as a scalar summary.
- **Supports:** the defensible comparison is the **PSD-envelope** (test/qual spec ASD must envelope the
  flight MPE across frequency); the flight-vs-test **scalar GRMS overlay is a legitimate summary only**
  (a single number can hide a narrow-band exceedance). **Does NOT support** using the scalar GRMS as
  the *sole* acceptance check.

### C10. Qualification margin — CONFIRMED: qual ≈ MPE/acceptance **+ 3 dB** (with caveats)
- **GEVS** (verbatim): *"The qualification (prototype or protoflight) test level is generally 3 dB
  greater than the maximum expected (acceptance) test level. That is not always the case however. If
  the expected level is less than the workmanship level …"* (a workmanship/minimum floor can dominate).
- **Tolerance** (verbatim): random-vibration test control tolerance is *"Accel. Spectral Density ± 3
  dB"* and *"RMS level ± 10%"* — this is the allowed *control band*, distinct from the qual margin.
- **TRAP I checked and ruled out:** the GEVS generalized random-vibration tables show spectral SLOPES
  like *"+3 dB/oct"* and *"+6 dB/oct"* — these are **spectrum slopes, NOT the qualification margin**.
  Do not read the "+6 dB" in the component table as a 6 dB qual margin; it is the low-frequency ASD
  ramp slope. The qual-vs-acceptance margin is the **+3 dB** statement quoted above.
- **Disagreement / range:** GEVS states **+3 dB** as the general qual margin (with exceptions:
  workmanship floor, project-defined cases). A separate **+6 dB** "extra uncertainty / limited data"
  margin is used in some programs/standards, but I did NOT find a +6 dB *qualification-margin* clause in
  this GEVS document — the +6 dB occurrences here are spectral slopes. So **+6 dB as a margin is NOT
  supported by this source**; if round-2 wants it, cite a different standard (e.g. a force-limiting /
  MPE-uncertainty reference) and label it.
- **Note on the setup's -6 dB flight offset:** GEVS supports "flight (acceptance/MPE) sits below the
  qual spec by the margin"; the setup's -6 dB flight-mean offset is consistent in *direction* but its
  magnitude (6 dB) is a **project assumption**, not the GEVS +3 dB number — keep it labeled as such.

---

# Recommended gate values (maps each verified number to the placeholder it should replace)

| # | Quantity | Verified value (source) | Current placeholder in proposed_durable_edits / AGENTS / CLAUDE | Recommendation |
|---|---|---|---|---|
| A1 | R-hat (final) | **< 1.01**, rank-normalized split-R-hat (STAN-DIAG; STAN-REF citing Vehtari 2021) | "max R-hat <= 1.05 (prefer <= 1.01 …)" | Make **< 1.01 the primary gate**; keep 1.05 only as an explicitly-labeled early-workflow fallback, not the default pass bar. |
| A2 | ESS (final) | **bulk- AND tail-ESS ≥ 100 × #chains (≥ 400 for 4 chains)** (STAN-DIAG) | "min ESS >= 200 for reported parameters" | Replace fixed 200 with **≥ 100 × #chains**, and require **tail-ESS** too, not just bulk. (200 is below Stan's 400-for-4-chains final bar.) |
| A3 | Divergences | ideal **0**; nonzero ⇒ **bias**, "cannot be safely ignored" (STAN-DIAG) | "divergence fraction < 2%" | Keep < 2% as the FAIL line but add "0 ideal; investigate/hard-WARN any divergence; describe as bias risk." |
| A4 | Chains | **≥ 4** (STAN-DIAG) | ">= 4 chains" | Confirmed — no change. |
| A5 | Funnel | **non-centered** parameterization for hierarchical variance; smooth non-differentiable features (STAN-REF) | "non-centered parameterization … unless justified" | Confirmed — no change. |
| B6 | GRMS / 3σ | GRMS = √(area under PSD); 3·GRMS = 3σ ≈ **99.73%** (IRVINE-PSD/RAND) | (task-card quantity contract) | Confirmed — use in the quantity contract; label 3·GRMS as estimate, not max. |
| B7 | Half-power BW | **Δf = f_n/Q = 2ζ·f_n** (IRVINE-HPB) | (task-card quantity contract) | Confirmed — use in the resolution check definition. |
| B8 | Lines per half-power band | **NOT verified** to a primary number; 3–10 is a text/vendor rule of thumb | (no hard-coded number — correct) | **Keep as a documented assumption**, not a hard-coded harness density. Status `[TO-VERIFY]`. |
| C9 | Comparison form | **PSD-envelope** (spec envelopes flight MPE across freq); scalar GRMS = summary (GEVS) | (round-2 task card) | Put in the task card as the defensible check; scalar overlay summary-only. |
| C10 | Qual margin | qual ≈ MPE/acceptance **+ 3 dB** (GEVS); ASD control tol ± 3 dB | (round-2 task card; setup uses -6 dB flight offset) | Use **+3 dB** as the GEVS-cited margin. **+6 dB is NOT a margin in GEVS** (those are slope values); if used, cite another standard and label. Setup's -6 dB offset = project assumption. |

## Items left `[TO-VERIFY]` (what is missing)
- **B8** spectral-lines-per-half-power-band exact number: need a retrievable modal-testing primary
  source (Ewins *Modal Testing* page, or a B&K/Siemens application note with static text). Until then,
  keep it a documented assumption + sensitivity check, per harness proposal #5.
- **C10** the **+6 dB** "extra-uncertainty" qualification margin: not found as a margin in GSFC-STD-7000
  (April 2005). If round-2 wants +6 dB, cite a different controlled standard and label its scope.
- **GEVS revision currency:** I used the April-2005 base via an MIT mirror. Before a checker cites a
  GEVS clause, confirm the wording against the current controlled revision (GSFC-STD-7000A/B) on
  standards.nasa.gov.

## What I did NOT do
- Did not edit AGENTS.md, CLAUDE.md, checkers, runner code, or the proposed_durable_edits file. These
  are recommendations for the human to approve before any number is hard-coded.
