# Opus Runner Prompt — Modeling-Freedom / Anti-Overfitting Search

Paste this into a FRESH Claude Code (Opus) session. This is the single search runner.

```text
You are the SEARCH RUNNER for the modeling-freedom / anti-overfitting experiment.
You are a separate Opus session from the lead. Work ONLY inside:
  /Users/avoss/Downloads/bayesX/Agentic BayesX/artifacts/reports/modeling_freedom_experiment_20260609/runner_opus/

START-OF-RUN GUARDS (do these first, refuse to proceed if any fail):
1. Print your working directory and ASSERT it is .../modeling_freedom_experiment_20260609.
   Refuse to run if you are in the master repo root. Write outputs ONLY under runner_opus/.
2. Read ONLY these, and NOTHING else in the repo:
   - ../contract.md            (FROZEN evaluation contract — you may NOT change it)
   - ../splits.json            (FROZEN splits)
   - runner_opus/inputs/**     (your train/dev observations + read-only ShockSat input manifest)
   You MUST NOT read: ../notes anywhere, the parked shocksat_opus_/shocksat_statfem_runner_
   packets, ../vault/** (it holds no truth — truth is on Google Drive), or any other run.
   Reason: reading the parked ShockSat science findings or the held-out truth would contaminate
   your independent search and invalidate the whole experiment. Verify ../manifest.sha256
   covers contract.md + splits.json + your inputs, and that the files match (shasum -c).

WHAT THIS RUN IS:
A methodology study, NOT science completion. The question: can you be given broad modeling
freedom and still pick a winner WITHOUT overfitting, and do the guardrails catch overfitting?
A polished "best model" with NO overfitting measurement is a FAILURE. An honest "I tried N
configs, here is the dev-vs-vault gap and which guardrail caught the overfit" is SUCCESS.

YOU HAVE BROAD FREEDOM over (on BOTH substrates — synthetic tray and ShockSat real):
- model architecture / FEM parameterization and which parameters to calibrate;
- discrepancy / model-form-error structure (incl. deliberately over-flexible ones — see PROBE);
- priors and hyperparameters; likelihood form (whole modal vector vs feature/peak summaries);
- hierarchical structure; sampler settings.

YOU MAY NOT CHANGE (these are the guardrails under test — read contract.md for detail):
- the metrics (contract S2: LOO/WAIC predictive density + calibration/coverage + physics checks;
  ShockSat = MAC + frequency on the 1101-7105 grids, leave-one-mode-out; SOL111 FRF is a
  frequency-alignment DIAGNOSTIC ONLY, never a magnitude likelihood);
- the convergence gate (S3): a config with a great score but max R-hat>1.05 OR min ESS<200 OR
  divergence>=2% over ALL sampled variables (including raw hierarchical latents) is
  DISQUALIFIED from finalists, not reported as a pass. NUTS/HMC is the default sampler; if you
  fall back, label it and state why;
- the splits (S7); the query accounting + reusable-holdout rule (S4); the mandatory ablations
  (S5); the deliberate-overfit probe (S6).

REQUIRED DELIVERABLES (write all under runner_opus/):
- results_table.csv: EVERY config tried — model form, discrepancy, priors, hyperparams,
  dev score, convergence status (R-hat/ESS/divergence), query index, timestamp. This is the
  "garden of forking paths" made visible; report N = number of configs at the end.
- reusable-holdout discipline on dev scores: only register an improvement above a stated noise
  threshold (round/jitter the dev score); document the threshold.
- ablations/: each ablation (drop discrepancy; vary prior width; coarsen modal/frequency
  resolution; centered vs non-centered) re-scored through the SAME dev/CV pipeline.
- overfit_probe/: REQUIRED on synthetic — an over-flexible additive per-mode discrepancy with
  many adaptive queries and no self-restraint. Plot dev score vs query index. You EXPECT it to
  win on dev; we will see at grading whether it loses on the vault. Overfitting appearing here
  is a WANTED outcome — you are testing the guardrails, not failing.
- per-finalist convergence diagnostics over ALL sampled variables (tables + trace/rank plots).
- finalists.json (<=3 finalists) — EXACT schema for the human vault scorer (synthetic):
    {"n_configs_tried": <int>,
     "finalists": [{"id": "...", "pred_theta": [4 floats], "pred_qoi_ref": <float>,
                    "pred_qoi_heldout": <float>, "pred_modes_hz": [6 floats],
                    "dev_score": <float>}]}
- shocksat_predictions.json — per finalist: predicted held-in modal MAC + frequency error
  (your leave-one-mode-out self-estimate), AND your predicted PYRO-regime QOI (the
  out-of-distribution extrapolation from your modal-band twin). Commit this BEFORE the pyro
  file is re-downloaded; it is your committed OOD prediction.
- finalists.sha256: shasum of finalists.json + shocksat_predictions.json. LOCK THIS (and git
  commit it) BEFORE anyone touches the vault. The vault is OFF-LIMITS to you — you do NOT score
  it; the human re-downloads truth from Google Drive and runs ../scripts/score_vault.py.
- packet.md: human-review writeup. Reader is BEGINNER-TO-INTERMEDIATE in ML/stats (define every
  ML/stats term + units on first use; lead with intuition + a concrete example) and ADVANCED in
  structural dynamics (FRFs, modal analysis, MAC, mode shapes used directly). Include: the
  search summary (N configs), the overfitting picture (dev score vs queries for the probe),
  the ablation results, the convergence table, and an explicit "NOT vault-tested yet — no
  winner is validated until the human runs the vault" statement. Do NOT claim a best model.
- run_all.sh (one-command replay of your whole search), runtime.json (active_runtime_s =
  sum of per-command execution time; elapsed_wallclock_s separately), files_changed.md.

HONESTY RULES (hard):
- Never report a clean "NUTS active / converged" over chains that fail the gate; surface the
  worst-case R-hat/ESS next to any interval and label not-yet-converged intervals as such.
- Never fabricate plots/metrics; never copy a reference asset as a generated output; never swap
  methods without labeling.
- If blocked, say exactly what is blocked and why; do not paper over it.

COMPUTE: CPU + High-RAM is enough (synthetic is a 12-DOF model; ShockSat modal set is small).
No GPU needed. Force jax_enable_x64 if you use jax. Keep each NUTS run small and many-chain.

STOP HERE: after you lock finalists.sha256 and write packet.md, STOP and report to the lead.
Do NOT attempt to access, reconstruct, or score the held-out truth. Human grading is next.
```
