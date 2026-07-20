# Packet — Confidently-Wrong under Model-Form Error (Bilionis concern, on the FRF testbed)

2026-06-16. Workspace `artifacts/reports/confidently_wrong_modelform_20260616/`.
**One-command replay:** `bash run_all.sh`  ·  **Checker:** `python3 check.py`  ·  **Status:** see §6.

Extends the E1–E4 prior art (`artifacts/reports/paper_virtual_sensing_uq_toy_20260613/`). Same forward
model (`core.py`, unchanged copy). `nuts_update.py` is a COPY with ONE addition: a `learn_discrepancy=False`
path = the naive strawman (the original scaffold is never edited).

---

## 1. The exact concern under test (not broadened)
Ilias Bilionis (Alberts & Bilionis 2023 arXiv:2301.07609; Hao & Bilionis 2024 arXiv:2306.02150):
**a converged, confident Bayesian posterior can be confidently *wrong* under genuine model-form error, with
no signal that the physics is off** — *"Bayesian MCMC converges to the maximum likelihood estimator without
detecting or accounting for underlying model form errors … NUTs, which is not aware of the underlying model
form error, still produces confident posteriors."* Their cure: a learned inverse-temperature β in the prior.
**Our analog:** a learned output-side discrepancy scale σ_d + a held-out trust test (predict masked channels
we never fit; check whether the truth falls in the band — that is our warning signal).

Question: **can we trust a calibrated digital twin under model-form error, and does our UQ warn us when we
cannot?** Claim we may earn (and only this): *discrepancy-aware updating detects model-form error (σ_d) and
preserves calibrated predictive/QOI coverage where naive Bayesian calibration is confidently wrong.* We do
NOT claim universal parameter recovery (§4 E-LIMIT is the honest limit).

## 2. Method summary (read first)
- **Forward model:** modal-ROM FRF `H_c(ω;θ)=γ Σ_i Φ_{c,i}(ΦᵀB)_i / (α_i²ω_i² + jωβ_i²(2ζ_iω_i) − ω²)`
  (Yan et al. 2026 Eqs 4,11,12), mass-normalized modes, fixed Φ, 4 channels. Main sweep = **3 well-resolved
  modes** (18/95/280 Hz); see decisions_log D9 for why the scaffold's 720 Hz mode is excluded here.
- **Likelihood:** Gaussian on **log-amplitude** ln|H| over the whole [5,1000] Hz curve (160 log-spaced lines).
  Inferred: per-mode α (3), per-mode β (3), γ, and the discrepancy scale σ_d. Fixed: Φ, modes, σ_meas=0.05.
- **Truth = (best modal fit) × `correlated_logfield` discrepancy** — a smooth, log-frequency-correlated,
  HF-growing multiplicative field **not representable by any modal α/β/γ scaling** ⇒ genuine model-form error.
- **Observed = Ch1/Ch2 (fit); held-out = Ch3/Ch4 (masked, predicted through the fixed coupling Φ, scored
  post-hoc).** Held-out coverage = the trust test.
- **Arms (same data per cell):** A0 deterministic LSQ (context); **A1 Naive-NoDisc** (NUTS, σ_d≡0, iid σ_meas
  only); **A2 DiscAware-iid** (NUTS, learns σ_d); **A3 DiscAware-correlated** (NUTS, σ_d + Schneider-style
  correlated discrepancy). NUTS = 4 chains, exp-reparam, warmup/samples 1000/1000.
- **Convergence gate (every arm, every level):** max R-hat ≤ 1.05, min ESS ≥ 200, div-frac < 2%.
- **Data count:** **one synthetic realization** per (class, level, arm); no test-to-test / flight-to-flight
  variability. Float64.

## 3. The sweep and the three results (all 29 NUTS cells converged: worst R-hat **1.003**, min ESS **1546**, 0 divergences)

### Result 1 — the malady and the cure (Fig A, money; `figA_coverage_vs_delta.png`)
Held-out predictive coverage of the masked channels at nominal 95%, vs injected error δ ∈ {0,.05,.10,.20,.35,.50}:

| δ | A1 naive (noisy / latent-truth) | A2 iid | A3 corr |
|---|---|---|---|
| 0.00 (control) | 0.94 / 1.00 | 0.94 | 0.94 |
| 0.10 | 0.74 / 0.08 | 0.93 | 0.96 |
| 0.20 | 0.49 / 0.07 | 0.94 | 0.94 |
| 0.50 | **0.24 / 0.02** | 0.85 | 0.85 |

The **naive arm converges and stays confident (α 95%-width flat ~0.002) but its held-out coverage collapses
to 0.24 (noisy) / 0.02 (latent truth)** = confidently wrong with no warning. The discrepancy-aware arms stay
near nominal (≥0.84). At δ=0 (no error) the naive arm is ALSO calibrated ⇒ the collapse at δ>0 is model-form
error, not a sampler artifact (every arm cleared the convergence gate).

### Result 2 — σ_d is a thermometer for model-form error (Fig B; `figB_sigmad_thermometer.png`)
Learned σ_d median vs δ: A2 0.01→0.03→0.06→0.18→0.15→0.34; A3 0.01→0.03→0.07→0.17→0.18→0.36 (Spearman ≈
0.94, rising; the 0.18→0.15 wobble is single-realization noise). At δ=0, σ_d≈0.01 (the control reads "no
error"). The naive arm has **no such mechanism (σ_d≡0, flat)** — it cannot signal that the physics is off.
σ_d is an effective band-average std and tracks the band-average of the injected (heteroscedastic) field.

### Result 3 — confidently (over)certain vs honestly uncertain parameters (Fig C; `figC_alpha_intervals.png`)
Naive α 95%-width stays flat ~0.002 across the whole sweep (never widens = overconfident); A2 widens 6–7×
(0.003→0.020) = honest; A3 stays tight but absorbs the structured error into its **correlated discrepancy
term**, so its held-out coverage still holds (Fig A) by a different mechanism. Under this (roughly symmetric
correlated) error the naive α is overconfident but not strongly *biased*; the coherent-bias case (§4) is
where the parameter is actually missed.

## 4. The honest limit — a coherent confounded bias our cure does NOT fix (Fig D/E; `figD_honest_limit.png`, `figE_identifiability.png`)
E-LIMIT mirrors prior-art E4: `local_mode_modes` (mode 4 = 760 Hz is LOCAL to the masked sensors); the masked
"virtual ground truth" carries a coherent **+15% peak-frequency shift** and is used as a down-weighted fit
target (the paper's closed-loop updating). All four updates converged.
- **Unbiased control** (no shift) recovers α₄ = **[0.842, 0.879]** (covers truth 0.85) ⇒ the method is sound.
- **Biased disc-aware (correlated)** α₄ = **[0.960, 1.017] MISSES** truth (biased toward apparent hardening),
  **yet the held-out amplitude QOI (peak height) stays covered** ⇒ **QOI coverage ≠ parameter recovery.**
- **Identifiability gate:** mode 4 has ~0 participation in the observed channels (Fig E heatmap); its FIM
  eigen-direction is the weakest (~4× prior vs >1000× for modes 1–3), so the **biased masked target dominates
  α₄**; a peak-frequency shift is *algebraically* a stiffness scaling (**cosine of the two sensitivity columns
  = 1.000**). So the bias and α₄ are confounded. **Cure = break the degeneracy** (keep a sensor that sees the
  local mode, or a bias-aware credibility model), **not** more flexible discrepancy. This is the "~15° trim,
  not a pivot": the method's predictive/QOI trust is intact; only the per-parameter claim fails, by design.

## 5. Sensitivity (verdict robust)
- **Error class 2 — missing-mode / hidden DOF** (truth keeps the 280 Hz mode; the fit drops it; Fig A right):
  A1 coverage collapses 0.87→0.37 with severity; A2 holds ≥0.80; A3 holds 0.95→1.00. **Verdict robust to the
  error class.**
- **Held-out channel choice** (fit Ch3/Ch4, hold out Ch1/Ch2, δ=0.20): A1 0.62 vs A2 0.92. **Robust.**
- **Coverage target** (post-hoc): the naive-vs-disc-aware gap holds at the 90/95/99% nominal levels.
- A0 deterministic (context): a point estimate with NO uncertainty — masked-channel QOI error grows to ~2–3 dB
  at δ=0.50 with no band at all (the paper's deferred-UQ baseline).

## 6. Honest status (green / yellow / red) — copied from `check.py`
- **GREEN gates:** every NUTS arm converged at every level; A1 coverage collapses (malady) while staying
  confident; A2 AND A3 coverage hold ≥0.80 across the sweep; A2/A3 σ_d rises monotonically (thermometer);
  E-LIMIT reported with QOI-hold; unbiased control recovers α₄; sensitivity robust; integrity (scaffold not
  edited in place); figures tufte-linted + image-QA + text-overlap-clean.
- **YELLOW (documented, never "success"):** single synthetic realization, no test/flight variability;
  surrogate error model (not a measured real-structure discrepancy); the E-LIMIT parameter miss under coherent
  bias; σ_d tracks the band-average (not the peak HF std).
- **RED:** none expected (see `checker_report.json` for the live count).

## 7. Runtime
`runtime.json`: `active_runtime_s` = sum of run_all stage durations; `nuts_only_active_s` = sum of stored
per-cell + E-LIMIT NUTS runtimes (~7–8 min of NUTS; the resumable replay skips finished cells).

## 8. Figures (each its own saved script + tufte lint + image-QA + save-time text-overlap audit)
`fig_testbed.png`, `figA_coverage_vs_delta.png`, `figB_sigmad_thermometer.png`, `figC_alpha_intervals.png`,
`figD_honest_limit.png`, `figE_identifiability.png`, `gif1_frf_bands.gif`. Gates: `out/image_qa.json`
(pixel legibility, ALL_OK), `out/text_overlap.json` (bbox auditor, 0 overlaps), `logs/tufte_*.txt` (advisory
flags reviewed in decisions_log D11 — all benign: log-freq via the `viz.style` helper; δ/severity axes are
correctly linear; dB only for FRF-magnitude display while the likelihood/coverage is on log-amplitude).

**Deck:** `slides/confidently_wrong_modelform.pptx` (11 slides), built by `python3 code/make_deck.py` (system
python3 + python-pptx; gated on the non-RED checker — every slide number traces to a result JSON / checker
gate). Not in `run_all.sh` because pptx is not in the NUTS venv; rebuild with the one line above after a replay.

## 9. Proposed durable updates (await Andrew — NOT yet applied; human stop point)
- `notes/runs.md`: add a dated row for this thread (status copied verbatim from the checker).
- `docs/report/project_log.md`: add a thread row (Bilionis confidently-wrong test on the FRF testbed).
- `notes/memory.md` CURRENT STATE: add a short entry.
- Candidate follow-ons: (a) bias-aware credibility model; (b) sensor-placement / pre-test design that keeps a
  sensor on each local mode (the E-LIMIT lever); (c) multi-realization repeat to turn single-realization
  YELLOW into a distributional statement.
