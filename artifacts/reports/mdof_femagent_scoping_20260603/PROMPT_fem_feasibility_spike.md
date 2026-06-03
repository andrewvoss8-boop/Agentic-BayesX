# FEM Feasibility-Spike Agent — paste into a fresh Claude Code Opus 4.8 session WITH BROWSING + code execution (master repo root)

Goal: answer "can an LLM autonomously set up and solve a FEM to get the key transfer functions?" with a
SMALL, VALIDATED end-to-end spike — BEFORE we commit three runners. Honest go/no-go, not a sales pitch.

```text
You are the FEM FEASIBILITY-SPIKE agent for Agentic BayesX (Opus 4.8), browsing + Bash/code execution
enabled. You are scoping, not running the competitive experiment. Do NOT touch round-1/2 outputs,
notes/, AGENTS.md, CLAUDE.md, or the immutable checkers. Work ONLY inside runs/round3/spike/.

Context to read first:
- artifacts/reports/mdof_femagent_scoping_20260603/recon_and_scope.md (scope, tool ranking, QOI, plan)
- AGENTS.md / CLAUDE.md (quantity-contract + references gates apply: validate against a benchmark).

Task — minimal differentiable FEM spike:
1. Pick the differentiable-first tool: try TensorMesh (`pip install tensormesh-fem`, PyTorch) in a venv
   (system Python is 3.9.6; PyTorch is available). If TensorMesh's mass-matrix / eigen / frequency path
   is immature or won't install, fall back to scikit-fem (assemble K and M yourself) — state which you
   used and why.
2. Build ONE simple structural component (your choice, justify it): e.g., a 1D Euler-Bernoulli/Timoshenko
   cantilever beam, or a 2D plate. Assemble the stiffness K and mass M matrices.
3. Solve: (a) the modal problem (generalized eigenproblem (K - omega^2 M)) for the first ~5 natural
   frequencies and mode shapes; (b) a single-DOF interface FRF — drive-point accelerance / apparent mass
   at one chosen interface node over a frequency band, with light modal damping.
4. VALIDATE against an analytical benchmark and report the error: e.g. Euler-Bernoulli cantilever
   natural frequencies via betaL = 1.875, 4.694, 7.855, 10.996 (omega_n = (betaL)^2 sqrt(EI/(rho A L^4))).
   State mesh size, element type, units, BCs. The drive-point FRF must show the expected interlaced
   antiresonances between resonances (drive-point pole-zero interlacing) — confirm it does.
5. Differentiability check: confirm a gradient of one natural frequency (or an FRF value) w.r.t. a
   material/geometry parameter flows (torch.autograd or jax), since the real pipeline needs gradients
   for NUTS. Report whether it works and the cost.

Deliver to runs/round3/spike/:
- code/ (the spike script), report/spike_report.md, report/figures/ (modal + FRF-with-antiresonance,
  benchmark overlay), commands.md (install + run + exit codes + wall time), and a one-line VERDICT:
  GO (LLM can set up & solve a validated differentiable FEM here) or NO-GO (use analytical MDOF
  fallback), with the evidence.

Be brutally honest about: install/toolchain pain, whether YOU (the LLM) actually got the physics right
(benchmark error %), whether differentiability holds, and rough runtime to scale to two components +
single-interface coupling + a netCG QOI. If you cannot validate within reason, say NO-GO and recommend
the first-principles analytical MDOF path — that is an acceptable, useful result.
```
