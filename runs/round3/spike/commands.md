# Commands — FEM feasibility spike (round 3)

Machine: macOS, system interpreter `/usr/bin/python3` = **Python 3.9.6** (only interpreter present;
no Homebrew, no pyenv, no Python 3.10+). System torch 2.8.0 available. JAX stack lives in
`.venv_nuts` (jax 0.4.30, numpy 1.26.4, scipy 1.10.1, matplotlib 3.9.4) — the project's NUTS env.

All commands run from repo root `Agentic BayesX/`. Exit codes and wall times as observed.

## A. TensorMesh (PREFERRED) install attempt — FAILED on toolchain
```
python3 -m venv runs/round3/spike/.venv_spike          # exit 0  (Python 3.9.6)
runs/round3/spike/.venv_spike/bin/pip install tensormesh-fem
#   exit 0 but: "Could not find a version that satisfies the requirement tensormesh-fem
#   (from versions: none)"  -> tensormesh-fem 0.1.1 requires_python >=3.10, ~0.7 s
```
PyPI metadata (curl https://pypi.org/pypi/tensormesh-fem/json):
`version 0.1.1`, `requires_python >=3.10`, deps `torch>=2.0, torch-sla>=0.2.1, gmsh, meshio, ...`.

Forced install to probe the real blocker (pure-py3 wheel, so download succeeds):
```
pip download --no-deps --ignore-requires-python tensormesh-fem   # exit 0, wheel is py3-none-any
python3 -m venv --system-site-packages runs/round3/spike/.venv_spike   # reuse system torch/np/scipy
.venv_spike/bin/pip install --ignore-requires-python torch-sla meshio gmsh toml psutil tqdm  # exit 0
.venv_spike/bin/pip install --no-deps --ignore-requires-python <wheel>                       # exit 0
.venv_spike/bin/python -c "import tensormesh"
#   exit 1: TypeError: unsupported operand type(s) for |: 'torch._C._TensorMeta' and '_GenericAlias'
#   (tensormesh/mesh/adjacency.py:111 — PEP-604 'X | Y' annotation evaluated at import; needs py>=3.10)
```
**Conclusion: TensorMesh cannot run on the only available interpreter.** Installing Python 3.10+
(build-from-source / new toolchain) is out of scope for a spike. NO-GO for TensorMesh here.

## B. Fallback: first-principles Euler-Bernoulli beam FEM assembled in JAX — used
Why JAX (not scikit-fem): the project's NUTS sampler is JAX/numpyro, so the differentiability
the real pipeline needs is JAX gradients. scikit-fem assembles K,M but is NOT autodiff, so it
could not satisfy requirement #5. Hand-assembling in JAX is the "assemble K,M yourself" path AND
gives end-to-end gradients.
```
.venv_nuts/bin/python runs/round3/spike/code/beam_fem_spike.py
#   exit 0,  wall 20.06 s  (real),  total compute logged total_runtime_s = 18.44 s
#   (~16 s of that is one-time JAX jit/trace warm-up; per-gradient eval = 0.33 ms after jit)
```
Outputs written:
- `report/results.json` (all numbers)
- `report/figures/modes.png`, `benchmark_overlay.png`, `frf_drivepoint.png`

## One-command replay (JAX beam — default path)
```
.venv_nuts/bin/python runs/round3/spike/code/beam_fem_spike.py
```
(Uses the existing project `.venv_nuts`. No extra install needed for the default path.)

## C. ADDENDUM (2026-06-03 later) — TensorMesh RETEST on Python 3.13
Human installed **Python 3.13.13 via uv** (`~/.local/bin/python3.13`; `python3` still = 3.9.6).
```
source ~/.local/bin/env
python3.13 -m venv runs/round3/spike/.venv_tm313        # exit 0  (Python 3.13.13)
.venv_tm313/bin/pip install tensormesh-fem              # exit 0,  ~5m32s (torch 2.12 download dominates)
#   -> installs tensormesh-fem 0.1.1, torch 2.12.0, torch-sla 0.2.1, gmsh 4.15.2, meshio 5.3.5, ...
.venv_tm313/bin/python -c "from tensormesh.verify_install import main; main()"
#   exit 0:  Poisson 2D L2 error 1.19e-2 OK; note torch-sla native 'eigen' backend not pre-built
#   (needs C++ compiler; clang++ present so it could JIT — not required for this spike)
.venv_tm313/bin/python runs/round3/spike/code/tensormesh_modal.py
#   exit 0,  wall ~14.5 s (plus a separate 154 s probe for the P2 cl=0.005 dense solve, not in script)
#   -> report/tensormesh_results.json, report/figures/tensormesh_convergence.png
```
Replay (TensorMesh path): `runs/round3/spike/.venv_tm313/bin/python runs/round3/spike/code/tensormesh_modal.py`
(requires the py3.13 venv above; not needed for the default JAX path).
