# Compute Protocol

Where to run multi-hour NUTS / TMCMC / FEM jobs, and the rules that keep the
results trustworthy. This file lists only the compute we will actually use.
Plain-English note for the sampler terms: **NUTS/HMC** = the gradient-based
Markov-chain Monte Carlo sampler we use to draw from the posterior; a **chain**
is one sampler trajectory; **TMCMC** (Transitional MCMC, Ching & Chen 2007) is a
population sampler that moves many "particles" at once and handles ridges /
multiple modes that a single chain struggles with.

Decision date: 2026-06-06. Status: working protocol, not a durable harness rule
yet (scaling to GPU is gated on a validated method — see below).

## The two-and-a-half things we use

### 1. CPU + High-RAM (default — Mac or Colab) — use this NOW
- For the **current regime**: small 2DOF/MDOF models, single-chain or few-chain
  NUTS that finishes in ~6-10 minutes, all development, debugging, and the
  **final reproducible replay** that produces checker hashes.
- The Mac + git stays the **source of truth**. CPU is always full float64, so the
  arithmetic near resonances/eigenvalues is never in question.
- Why not a GPU yet: a single NUTS chain is **sequential** (each leapfrog step
  depends on the previous one), so for a tiny model a GPU is no faster and often
  slower (launch overhead). Also, we do not yet trust the synthetic FEMs /
  Stage-3 results — do not spend GPU time on results we are not ready to trust.

### 2. Colab Pro A100 GPU + High-RAM + float64 — use this WHEN the work is parallel-shaped AND the method is validated
Switch to A100 only when BOTH are true:
- **(a) the method/result is validated** (held-out calibration on real/validated
  inputs — not synthetic recovery or convergence alone), AND
- **(b) the bottleneck is genuinely parallel-shaped**, i.e. one of:
  - **vectorized many-chain NUTS** (`chain_method="vectorized"`, e.g. 8-64 chains
    at ~the cost of one),
  - **TMCMC** (hundreds-thousands of particles — embarrassingly parallel, the
    strongest GPU case),
  - a **genuinely large differentiable FEM** forward model.
- A100 is chosen because it has **real float64** (FP64 + FP64 tensor cores).
  This is non-negotiable for FRF/eigen math near resonance: in float32, HMC
  gradients go bad and you get spurious divergences — you would be debugging the
  arithmetic, not the physics.

### 2.5 Colab Pro H100 GPU — reserve only
- Use H100 ONLY after you have measured A100 and it is the demonstrated wall.
  H100 burns Colab compute units fastest; do not reach for it speculatively.

## Hardware we explicitly do NOT use for the Bayesian/eigen math
- **T4, L4, (and "G4" if it appears)** GPUs: crippled float64 (~1/32-1/64 rate).
  Fine only for float32 prototyping, plotting, or surrogate *inference* — never
  the posterior/eigen math.
- **TPUs (v5e/v6e)**: effectively no float64 (bfloat16/float32 machines). Avoid;
  they break the resonance-conditioning argument above.

## Non-negotiables for ANY remote / GPU run
These keep a faster machine from quietly producing untrustworthy results:
1. **Force float64 and verify it**: `from jax import config;
   config.update("jax_enable_x64", True)`, then assert an array is actually
   `float64`. (Easy to silently run float32 on GPU.)
2. **Benchmark before booking hours**: prove the GPU is actually faster for *our*
   model (CPU vs A100, 4 vs 32 vectorized chains) before a multi-hour run.
3. **Checkpoint** long runs — Colab kills long sessions; an un-checkpointed
   3-hour TMCMC job that dies at hour 2 is a total loss.
4. **Pin the environment** (match `.venv_nuts`: jax 0.4.30 / numpyro 0.15.3 /
   numpy 1.26.4 / scipy 1.10.1) and **sync artifacts + `runtime.json` back to
   git**. The Colab filesystem is ephemeral and is **never** the source of truth.
5. **Reproduce the immutable checker hashes** on the remote machine before any
   result is believed.
6. **Report all-variable convergence** (R-hat, ESS, divergence fraction over ALL
   sampled variables incl. raw hierarchical latents) per the Convergence Gate —
   faster hardware does not relax that bar.

## Smarter-than-hardware levers (try before scaling up)
- Modal truncation / sparse partial eigensolve (solve only in-band modes) — legit
  only if you show those modes resolve the QOI and report bounded truncation
  error (Discretization Resolution Gate).
- A validated differentiable surrogate (rational surrogate / GP emulator) for the
  expensive FEM inner loop — must stay differentiable for NUTS and be validated
  against the full FEM on held-out points, and labeled honestly.

## Runtime accounting
Record `runtime.json` with `active_runtime_s` and `elapsed_wallclock_s` as usual,
and note which machine (CPU / A100 / H100) produced each timing.
