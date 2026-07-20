# Question framing — ShockSat FULL-SPECTRUM FRF study (20260714)

Written BEFORE any science. Pre-registered; never edited mid-run (dated addenda only, append-only).

## The engineering decision being supported
Whether to invest further in Bayesian FEM updating / agent-driven remodeling for the ShockSat twin, or to
declare the remaining held-out FRF error unreachable by the levers we own and deliver the inherited FEM +
statFEM honest-band twin as final. Every lever previously blamed for failure is given its fair shot at once:
amplitude TRAINING data (never used for training before), measured damping, window-matched scoring, shape
inference, an amplitude-compass remodeling loop, and the extended >258 Hz band.

## The question
Given every lever we have blamed for past failures, can Bayesian FEM updating and/or agent-driven
remodeling beat the baseline FEM on held-out per-channel FRF amplitude, in EACH band
(sub-200 / 200–500 / 500–ceiling Hz), and improve the net-CG force quantities?

**Objective function / success metric:** fold-averaged held-out per-channel log|H| correlation (P1′
convention, `quantity_contracts.md`) per band; net-CG band width + coverage. What search may choose: θ,
shape perturbations, model edits within the validated action families, under the query budgets. What stays
human judgment: delivery decision, convention changes, any re-basing of thresholds. What would make this the
wrong question: if the caches' certified ceiling is so low that "full spectrum" collapses to the old band —
then the study degrades honestly to the sub-200 portion (§4 fallbacks) and says so.

## The five standing explanations (H) and the arm that challenges each

| H | Standing explanation (from prior runs) | Challenged by | Prior evidence |
|---|---|---|---|
| H1 | The shape wall: per-channel amplitude is capped near 0.34 because mode shapes are wrong and no available lever moves them | Arm C: shape inference TRAINED ON AMPLITUDES (never done) | composite bakeoff: Beck = per-point champion but trained on survey shapes only; deterministic-update median log\|H\| corr ≈ 0.34; measured-shapes reference ≈ 0.70 |
| H2 | Remodeling impotence: the agent loop ties with random because its steering signal (frequency fit / evidence) does not correlate with held-out FRF | Arm D: loop given an amplitude compass (the compass now IS the deliverable metric) | true remodel loop 20260706: agent 0.2376 vs random 0.2389 (tie), S1–S3 falsified |
| H3 | Damping unusable at 2 Hz: fitting damping fits window aliasing | Window-matched scoring + measured ζ is the STANDARD convention for every arm (except A0); gains attributed | resolution run 20260713: +0.040 dev, window not damping (+0.033 window-alone, −0.012 damping-alone), below 2×SE bar |
| H4 | The unmeasured >200 Hz cluster: the normal-force band is wide because the 234–258 Hz plate modes were never measured | Wide-band re-distillation: the cluster's amplitudes at ~111 sensors become measured data (arm F / extended band) | netcg/composite: normal band 2.53× driven by unmeasured drumhead tiers; no data answer key for normal_Z |
| H5 | Selection scores are not validation: Bayesian model-class selection fails under model-form error | Arm E: selection with the amplitude-INCLUSIVE likelihood vs held-out ranking | composite bakeoff: evidence crowned rand10 (+54 logZ) which did NOT improve held-out QOI |

`findings.md` MUST answer each H explicitly, with numbers, GREEN/YELLOW/RED per the Result Status Standard.

## Pre-registered success criteria (verbatim from the card §7; falsification is a valid, reportable outcome)
- **S1 (H1/H3):** some arm beats A1 on fold-averaged SUB-200 per-channel correlation by ≥ +0.05 AND
  ≥ 2×fold-SE, vault direction confirmed.
- **S2 (H2):** the agent track beats the equal-budget random track by ≥ 1×fold-SE on the same metric.
- **S3 (QOI):** a delivered arm narrows net-CG shear while keeping ≥ 0.95 coverage on the held-out-drive keys.
- **S4 (H4):** the normal band narrows by ≥ 25% (2.53× → ≤ 1.90×) while still covering.
- **S5 (H5):** amplitude-inclusive selection score vs held-out ranking: Spearman ≥ 0.5.

## Pinned continuity bars (card §3.4; report all in the packet)
- A0 (historical convention: frozen basis, flat 1% ζ, naive scoring) dev P1′ must reproduce
  **0.1969 ± 0.002** on the same 4-drive leave-one-drive-out folds. **HARD GATE — do not proceed if it fails.**
- A1 (window-matched + measured ζ) must reproduce **0.2371 ± 0.005** (resolution run's result).
- Wall references: deterministic-update median log|H| corr ≈ 0.34; measured-shapes reference ≈ 0.70.
- Vault location effect from prior runs: dev→vault shifts of +0.22–0.30 are a LOCATION effect, not a win.

## Pre-registered splits (card §3.5; never changed mid-run)
- Dev folds = leave-one-drive-out over the 4 dev drives {+X/990x, +Z/990z, +Y/990y, +Z@900z}
  (cache keys m_xpos_990x, m_zpos_990z, m_ypos_990y, m_zpos_900z): train on 3 drives' amplitudes, score the
  4th. Fold-average and report the fold SE (SE = std of fold values / √4).
- VAULT = the ENTIRE +XY/Test04 drive (both bands: existing cache AND its wide-band re-distillation),
  SHA-frozen at build time (`VAULT_FREEZE.sha256` first), never queried during development, graded ONCE on
  the frozen finalist set. Honest label: +XY has been read by TWO prior programs (damping run 2026-07-10;
  resolution run 2026-07-13) — vault numbers are directional confirmation only; mitigation = the arm set is
  fixed by this card before any score (no search against the vault).
- Query budget on dev folds: agent remodeling ≤ 80 scored queries; random control ≤ 80; every dev query
  appended to `out/query_log.jsonl`.
