# Decisions log — Task Card E `_Fable`

Runner: Claude Code (lead acting as runner).
Workspace: `artifacts/reports/shocksat_structured_discrepancy_codex_20260722_Fable/`
Card: `docs/agents/structured_discrepancy_codex_review_20260722/task_card_codex_structured_discrepancy.md`

Every entry below was written BEFORE the action it describes, unless explicitly marked `POST-HOC`.

---

## F0 — 2026-07-22 — Dispatch and `_Fable` labelling (HUMAN DECISION)

Andrew: *"execute … task_card_codex_structured_discrepancy.md, labeling everything _Fable to differentiate
from the work being done by another agent."*

Interpretation and action:

- The card is executed as written, INIT → terminal state, with no human-approval pause (the card is
  self-executing; checker-backed gates choose the terminal path).
- The card's proposed workspace is `artifacts/reports/shocksat_structured_discrepancy_codex_20260722/`.
  Because a second agent may be running the same card, this run uses
  `artifacts/reports/shocksat_structured_discrepancy_codex_20260722_Fable/` and every code module,
  script and decision artifact carries a `_fable` marker in its name.
- The card's own un-suffixed workspace directory is NOT created and NOT touched by this run.
- Task Card D's directory (`docs/agents/structured_mean_discrepancy_20260722/`), the closure-brief
  workspaces, all frozen predecessor workspaces and all immutable checkers are read-only inputs.

**Open ambiguity (assumed, flagged for Andrew to overrule):** `_Fable` is applied as a workspace-name and
file-name suffix, not as a separate directory tree outside `artifacts/reports/`.

---

## F1 — 2026-07-22 — Forward model and damping (frozen BEFORE any residual was fitted)

`q_fem` is computed by the frozen in-project reduced-model accelerance forward
`artifacts/reports/shocksat_modelclass_L5_20260619/code/realfrf.py :: fem_logmag`, imported unmodified.

- Reduced model `K(theta) = A_fix + sum_g theta_g A_g` (74x74, mass = I) from the frozen
  `reduced_blocks.npz`; response/drive rows placed by the frozen `Reduced.reduced_row` nearest-kept-DOF rule.
- Structural damping is applied as `eta = 2 zeta` with **zeta = 0.01 fixed**. Rationale: the measured H1
  caches were built with a 0.49 s exponential response window with end value 0.05, which ADDS damping
  `zeta_w(f) = 1/(2 pi f tau)`, `tau = -(N-1)/(FS ln 0.05)`. At the band centre (~100 Hz) `zeta_w ~= 0.0097`,
  so 0.01 is the window-matched value already used by every frozen predecessor on this data.
- `zeta_w` is frequency dependent (~0.019 at 50 Hz, ~0.004 at 250 Hz) while the forward uses a constant.
  The mismatch is a genuine frequency-structured model-form error and is therefore a plausible *source*
  of a learnable frequency main effect. This is preregistered as **sensitivity SENS-1**
  (frequency-dependent `zeta(f) = 0.003 + zeta_w(f)`) so the headline result cannot be an artefact of one
  damping choice that only this study made.

**Open ambiguity (assumed):** using the frozen constant-zeta forward as primary rather than inventing a new
one. Justification: the card forbids model-form edits and requires reuse of frozen inputs.

---

## F2 — 2026-07-22 — Cross-drive structure of the residual GP (frozen BEFORE fitting)

The card fixes `K_fx` over `(f, x)` and says only `c_d` is drive specific, but does not say whether the GP
realisation `u` is shared across drives or drawn independently per drive.

Decision: **`u` is an independent realisation per drive (cross-drive sharing fraction rho = 0)** for the
primary analysis. Consequences, both accepted deliberately:

1. In leave-one-drive-out folds the train-to-test cross-covariance `K_*T` is exactly zero, so **E1 == E0 by
   construction in the drive family**. The drive family therefore tests only the structured mean and the
   per-drive gain, not GP conditioning. This is stated in the preregistration and in every drive-family table.
2. Spatial and frequency transfer are unaffected: within a fold, held-out channels/bands are predicted from
   the retained portion of the *same* drives.

Diagnostic (required by the card's wrong-question trigger): the empirical cross-drive correlation of the
residual field is measured and reported. A high cross-drive correlation would mean the independent-per-drive
choice is conservative; a drive x frequency interaction that dominates triggers the card's
"`(f,x)` framing is inadequate" stop.

---

## F3 — 2026-07-22 — Exact linear algebra (frozen BEFORE fitting)

With rho = 0 the training covariance of one drive on a complete `frequency x channel` grid is

```
Sigma = sigma_u^2 [ r K_f (x) I_x + I_f (x) B_x ] + sigma_e^2 I ,   B_x = (1-r) K_x + D_nugget
```

which is of the form `A (x) I + I (x) B` and is therefore **exactly** diagonalised by
`U_f (x) U_x` from two small eigendecompositions (105x105 and <=84x84). Every split family in the card keeps
a complete sub-grid (whole channels, whole frequency cores, or whole drives are held out), so the structure
survives in every fold. Parameter (theta) uncertainty is added as a low-rank term `G G^T` and handled with
the Woodbury identity. All Gaussian conditionals are exact; no sampler is used in Stage 1, as the card requires.

---

## F4 — 2026-07-22 — Region definition uses design information only (frozen BEFORE fitting)

The card requires "five physical-region indicators". They are assigned by nearest frozen physical feature,
using sensor coordinates only:

`impact/source face`, `bolted joint (9.0, -0.4, 19.1)`, `strut base (8.7, 0.0, 49.6)`,
`dish (1.9, 0.0, 57.0)`, `bulkhead planes z in {12.4, 18.4, 30.4}`.

These four feature points and three bulkhead planes are copied verbatim from the frozen
`shocksat_modelclass_L5_20260619/code/spatial_reanalysis.py`; no response residual was read to choose them.

---

## F5 — 2026-07-22 — Channel set

Only DAQ channels that appear in the frozen `channel_map.csv` `tap_impact` configuration with a usable
structural axis and a kept FEM DOF enter the study (84 of the 111 channels stored in the measured caches).
TestLog-flagged bad channels (29, 30, 31 = 60 Hz noise in band; 101 = bad at installation) are excluded by
the frozen loader. Channels without coordinates cannot support a location-transfer claim, so dropping them
is required by the card's immutable source gate rather than optional.

---

## F6 — 2026-07-22 — POST-HOC entries

Anything discovered during execution that changes an action is appended below with a `POST-HOC` tag and the
UTC time, so the reader can tell preregistered choices from reactions.

---

## F7 — 2026-07-22 — Spatial kernel form corrected to match the frozen implementation (BEFORE fitting)

The card writes `K_x(Δx; l_x)` without naming the form. The frozen in-project implementation
`shocksat_modelclass_L5_20260619/code/schneider_faithful.py :: corr_space` is
**exponential / Ornstein-Uhlenbeck**, `exp(-|d| / l_x)`, while `corr_freq_linear` is squared-exponential in
LINEAR frequency, `exp(-0.5 (Δf / l_f)^2)`.

My first draft used a squared-exponential spatial kernel. It was corrected to the exponential form before any
residual was fitted, so this study is byte-faithful to the frozen Schneider-style kernel the M2/M3 legacy runs
used. Recorded because it changes numbers.

Practical consequence, stated up front so nobody over-reads the spatial arm: with `l_x = 2000 in` and a
structure ~60 in tall, `exp(-|d|/2000) ~ 0.97-1.00` for every sensor pair. The frozen spatial factor is
therefore very nearly an all-ones matrix, i.e. the `(1-r)` term acts as a **single common per-frequency-line
offset shared by all channels**, not as a local spatial smoother. Any spatial transfer it produces is
"the average residual of the retained channels at this frequency line", which is a real but weak mechanism.

---

## F8 — 2026-07-22 — POST-HOC DISCLOSURE: a machinery smoke test read measured folds before the
## preregistration file was written

Honest disclosure, recorded the moment it applied.

While building the exact-conditional engine I ran a two-fold smoke test on MEASURED residuals (spatial
cluster 0 and frequency core 0) to confirm the linear algebra ran and to time it. I therefore saw measured
E0/E1/E2/E3 numbers for those two folds before `preregistration.md` was written to disk.

What this does and does not compromise:

- **Not compromised (all frozen earlier, and by an external author):** the arm definitions, the success bar
  (2 dB median-|error| reduction OR 20% narrower intervals at coverage within 0.02), the CRPS 4-of-5 rule,
  the synthetic acceptance thresholds, the interpretation hierarchy and the automatic transition rules — all
  come from Task Card E, written by a different agent before this run started. The split registry and the
  mean-basis registry were written by `freeze_fable.py` and hashed BEFORE the smoke test.
- **Compromised in principle:** I cannot claim I was blind to the direction of the measured effect when I
  finished writing the reporting code. Nothing was retuned in response — no knot, length scale, prior scale,
  nugget rule or interval rule changed after the smoke test, and the git-tracked file contents show it.
- **Mitigation:** the preregistration file records the smoke-test numbers verbatim so a reviewer can check
  that the final measured numbers were not quietly moved toward a nicer answer.

This is logged as a genuine process defect, not waved away.
