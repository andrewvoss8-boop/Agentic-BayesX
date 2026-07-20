# Priority Deliverables — ShockSat Resolution-Consistent FRF Scoring (20260713)

Card: `docs/lab/shocksat_resolution_consistent_scoring_runner_prompt.md` (dispatched by Andrew 2026-07-13,
"run it"; lead Fable acting as autonomous runner in-session). Restated in my own words, with delivery pointers.

| # | Priority ask (my restatement) | Interpretation / where delivered |
|---|---|---|
| P-1 | Answer ONE pre-registered question: does processing the MODEL FRF through the SAME FFT frame/window as the measured 2 Hz caches let the physically-correct light damping (~0.3%) beat the incumbent convention (naive model + flat ζ=1%) on held-out per-sensor FRF — and is any gain due to the window, the damping, or their interaction? | Arms B0–B5 (fixed a priori), S1/S2/S3 verdicts in `out/verdicts.json`, narrative in `packet.md`. Falsification of S1 is a valid, reportable outcome. |
| P-2 | Gate W: verify the window model against RAW data — recompute the +X H1 from raw Test07 hits using the RECOVERED distillation parameters and compare to the stored `m_xpos_990x` cache; handle the Test01-vs-Test07 target caveat explicitly (label which comparison passed). | `code/gate_w.py`, `out/gate_W.json`, Gate W overlay figure. Distiller source FOUND (not inferred): `shocksat_psd_envelope_twin_20260623/code/{modal_multiref.py, multiref_frf.py, realfrf.py}` — N=122880 @ 250 kHz, exponential response window end=0.05, 2 ms box force window, pre_gap=200, H1=ΣYF*/Σ\|F\|² over hits, band 45–260 Hz. |
| P-3 | Gate K: synthetic 1-DOF kernel-correctness check (windowed known-ζ FRF reproduces analytic apparent broadening ≤5%; broad ζ=5% peak ~unchanged). | `code/gate_k.py`, `out/gate_K.json`. |
| P-4 | Gate R: pipeline-drift guard — B0 reproduces the damping run's A0_enr dev P1′ = 0.1969 ± 0.002; B1 < B0 (naive-physical deficit direction). | `code/gate_r.py` + first score-log rows, `out/gate_R.json`. |
| P-5 | Pre-registration discipline: gate files first; `check.py` SHA-locked BEFORE science; arm set fixed (no additions/drops after first score); freeze (`VAULT_FREEZE.sha256`) before the single vault read; vault labeled as the SECOND program read of +XY. | This file + `question_framing.md` + `quantity_contracts.md` + `assumptions_ledger.md` + `CHECKER.sha256` timestamps; checker encodes ordering. |
| P-6 | Honest reporting: packet.md with method summary up front (window operator equations, plain-English ML/stats terms), money figure + S2 decomposition + Gate W overlay + apparent-ζ curve + peak-zoom small multiples (Tufte + lint + legibility QA); findings never stronger than checker output; runtime accounting; one runs.md entry + one project_log row at the END, status verbatim. | `packet.md`, `findings.md`, `figures/`, `runtime.json`, `checker_report.json`, continuity appends. |
| P-7 | NO-SAMPLER study, stated per the AGENTS Sampler Decision rule: all arms deterministic (pre-registered fixed damping + reused multi-start θ_MAP); nothing inferred. | Stated here, in `question_framing.md`, and in the packet. Any Bayesian follow-up = a new card. |

Ambiguities I resolved myself (autonomy rule; details in `decisions_log.md`):
- D1: the window operator's exact mathematical form (closed-form sampled-pole geometric-sum operator that
  matches the recovered distillation processing by construction).
- D2: mapping the 33 survey per-mode ζ values onto the model's ~80 in-band modes (frequency interpolation of
  measured data; zero free parameters).
- D3: Gate W target handling for the Test01(cache)-vs-Test07(raw) series mismatch (per the card's own note).
