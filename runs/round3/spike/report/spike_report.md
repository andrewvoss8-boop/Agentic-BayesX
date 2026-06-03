# FEM Feasibility Spike — Report (round 3)

**Date:** 2026-06-03 · **Agent:** FEM feasibility-spike (Opus 4.8) · **Scope:** `runs/round3/spike/` only.
Did NOT touch round-1/2 outputs, `notes/`, `AGENTS.md`, `CLAUDE.md`, or immutable checkers
(`git status` shows only `runs/` is new).

## VERDICT
**GO** — an LLM can set up and solve a *validated, differentiable* FEM here. **Two validated paths now
exist** (see the 2026-06-03 Python-3.13 addendum, §8):
1. **First-principles Euler–Bernoulli beam FEM in JAX** — the project's NUTS stack. Benchmark err
   **< 0.0011 %**, drive-point FRF interlacing 4/4, autograd 1.2e-9, **0.33 ms/grad**. *Recommended default.*
2. **TensorMesh (PyTorch)** — now runs after Python 3.13 was installed via uv. Continuum P2 cantilever
   matches EB to **−0.026 %**; material-parameter autograd recovered (relerr 9e-7) but at **~1.3 s/grad**
   with caveats (no beam element; built-in `E=` arg detaches; dense solve scales poorly).

> Original spike VERDICT (Python 3.9.6 only): GO via JAX, TensorMesh **NO-GO** because it needs ≥3.10.
> Addendum VERDICT (Python 3.13 now available): TensorMesh **runs and is validated**, but the **JAX beam
> remains the recommended path for round 3** — faster gradients, exact benchmark match, no element/locking
> caveats, and it is the project's actual sampler stack. Use TensorMesh only if real 2D/3D continuum
> geometry is required.

Evidence (JAX path): natural frequencies match the analytical cantilever benchmark to **< 0.0011 %**
(nele=40); drive-point accelerance shows **all 4 antiresonances interlaced** between the 5 resonances;
autograd gradient of f₁ w.r.t. E and thickness h matches the **exact closed-form** derivative to **1.2e-9**.

---

## 1. Tool decision (brutally honest on toolchain)
| Tool | Result | Why |
|---|---|---|
| **TensorMesh** (PyTorch, PREFERRED) | **NO-GO on this box** | `tensormesh-fem 0.1.1` requires `python>=3.10`; pip refuses on Python **3.9.6**. Forced install (pure-py3 wheel) then `import tensormesh` → `TypeError: unsupported operand type(s) for \|` at `mesh/adjacency.py:111` — a PEP-604 `X \| Y` annotation evaluated at import. Genuinely needs ≥3.10. No brew/pyenv/3.10+ on the machine. |
| scikit-fem | not used | Assembles K,M but is **not autodiff** → can't satisfy the differentiability requirement (#5) the NUTS pipeline needs. |
| **First-principles Euler-Bernoulli FEM in JAX** | **USED** | "Assemble K,M yourself", but in **JAX** so `jax.grad` flows. Matches the project's actual sampler stack (JAX/numpyro in `.venv_nuts`). |

Full install transcript + exit codes: [commands.md](../commands.md).

## 2. Component, model, and contract
- **Component:** 1-D Euler–Bernoulli **cantilever** (clamped–free) beam. Chosen because it has a
  closed-form benchmark (βL roots), is the simplest model with a meaningful multi-mode interface FRF,
  and the drive-point apparent-mass/accelerance framing is exactly the round-3 netCG interface quantity.
- **Element:** 2-node Hermite-cubic beam element, DOFs `[w, θ]` per node, **consistent mass matrix**.
- **Units (strict SI):** m, kg, s, Pa, N.
- **Properties:** steel `E=210 GPa`, `ρ=7850 kg/m³`, `L=1.0 m`, rectangular section `b=0.050 m`,
  `h=0.005 m` → `A=2.5e-4 m²`, `I=5.208e-10 m⁴`.
- **BC:** node 0 clamped (`w₀=θ₀=0`, DOFs removed). Free tip is the interface DOF.
- **Modal damping:** ζ = 2 % (light), applied per mode.

### Quantity contract — drive-point accelerance A(f)
- Numerator = tip transverse acceleration response `a` (m/s²); Denominator = tip transverse force `F` (N)
  → units **(m/s²)/N**. Input DOF = output DOF = tip `w` (**drive point**).
- Modal form (mass-normalized modes φ_r, φ_rᵀMφ_r=1):
  `A(ω) = −ω² Σ_r φ_r[o]·φ_r[i] / (ω_r² − ω² + 2 i ζ ω_r ω)`.
- Drive-point ⇒ residues `φ_r[o]·φ_r[i] = φ_r²[o] ≥ 0` ⇒ **guaranteed pole–zero interlacing**
  (one antiresonance between each pair of resonances). Expected limits: low-f mass-line rise to mode 1;
  deep antiresonance notches between modes; resonance peaks bounded by ζ. **All observed** (Fig. 3).

## 3. Modal solve & benchmark validation
Generalized eigenproblem `Kφ=ω²Mφ` solved differentiably via Cholesky whitening
`M=LcLcᵀ, A=Lc⁻¹KLc⁻ᵀ, eigh(A)` (`jnp.linalg.eigh` is differentiable). float64 enabled.

Analytical benchmark (clamped-free Euler-Bernoulli):
`ωₙ=(βLₙ)² √(EI/(ρAL⁴))`, βL = 1.875104, 4.694091, 7.854757, 10.995541, 14.137168.

| mode | analytical (Hz) | FEM nele=40 (Hz) | error |
|---|---|---|---|
| 1 | 4.178 | 4.178 | +0.00001 % |
| 2 | 26.180 | 26.180 | +0.00002 % |
| 3 | 73.306 | 73.306 | +0.0001 % |
| 4 | 143.651 | 143.652 | +0.0004 % |
| 5 | 237.465 | 237.467 | +0.0011 % |

**Mesh / resolution sensitivity** (worst mode = mode 5): nele=5 → +1.58 %, nele=10 → +0.25 %,
nele=20 → +0.017 %, nele=40 → +0.0011 %. Convergence is monotone O(h²)-like; nele=40 is far past
adequate for the first 5 modes. Mode 1 is essentially exact at every mesh.
Figures: [modes.png](figures/modes.png) (correct nodal patterns, clamped end), 
[benchmark_overlay.png](figures/benchmark_overlay.png) (all meshes overlay analytical).

## 4. Drive-point FRF — interlacing confirmed
Resonances (Hz): 4.18, 26.18, 73.43, 144.0, 238.4 (match the modal frequencies).
Antiresonances (Hz): 18.34, 59.63, 125.0, 215.8 — **exactly one in each of the 4 gaps**
→ `interlacing_ok = true` (4/4 gaps filled). See [frf_drivepoint.png](figures/frf_drivepoint.png).
Axes log–log per the structural-dynamics plotting rule; scale is linear accelerance (not dB).

## 5. Differentiability (the requirement that matters for NUTS)
`jax.grad(f₁)` w.r.t. (E, h), jit-compiled:
| ∂f₁/∂· | autograd | closed-form (exact) | rel. err |
|---|---|---|---|
| ∂f₁/∂E | 9.94663e-12 Hz/Pa | 9.94663e-12 (f₁/2E) | **1.17e-9** |
| ∂f₁/∂h | 835.517 Hz/m | 835.517 (f₁/h) | **1.17e-9** |

Closed forms follow from f₁ ∝ √E and f₁ ∝ h. **Gradients flow cleanly through Cholesky + `eigh`.**
Cost: **0.33 ms per gradient** after a one-time ~16 s jit warm-up. (Note: central finite-difference on
E is roundoff-limited because E~2e11, so autograd is judged against the exact closed form — autograd is
actually *more* accurate than FD.) This is the green light for NUTS: a differentiable f(θ)→{ωₙ, FRF}
exists and is cheap to differentiate.

## 6. Scaling estimate → two components + single-interface coupling + netCG QOI
- Per component (≤40 elements, 5 modes): assemble + eig + FRF is **sub-second** after jit; one gradient
  0.33 ms. Two independent components ≈ 2×, trivial.
- **Single-interface coupling** (frequency-based substructuring / impedance: combine the two interface
  FRFs at one scalar DOF) is a per-frequency 1×1 (or small) complex assembly — negligible cost and
  differentiable (complex arithmetic + reciprocal are autodiff-friendly in JAX).
- **netCG QOI** = `F_interface(ω)/m_load` → PSD/GRMS integral over the band: smooth in θ, differentiable.
- Expected NUTS cost driver is the number of frequency points × modes per gradient, all O(1 ms)-scale
  here. **No scaling blocker foreseen.** Risk to watch: (a) eigure-derivative stability if two modes get
  near-degenerate (eigh grad blows up on repeated eigenvalues — non-centered / mode-tracking mitigations
  may be needed); (b) non-differentiable peak/argmax features in the QOI must be smoothed (per CLAUDE.md).

## 7. Honest limitations / residual risk
- This validates **one** simple component (1-D beam), **not** the full two-component MDOF + coupling +
  netCG chain. Those are scoped above but **not yet built or checked**.
- TensorMesh remains unevaluated on its merits (mass matrix / eigen / FRF API) because it would not run;
  if a Python ≥3.10 environment is provisioned, re-test it before discarding for round 3.
- `eigh` gradient near repeated/clustered eigenvalues is a known fragility for the NUTS step — flag for
  the real run.
- Damping is ad-hoc modal ζ=2 %; real flight damping/forcing carry over from round 2 and are not
  exercised here.

## Reproduce
`/.venv_nuts/bin/python runs/round3/spike/code/beam_fem_spike.py` → regenerates `results.json` + 3 figures.
Numbers: [results.json](results.json). Code: [code/beam_fem_spike.py](../code/beam_fem_spike.py).

---

## 8. Addendum (2026-06-03, later) — TensorMesh RETESTED on Python 3.13
The human installed **Python 3.13.13 via uv** (no Homebrew). This removes the only blocker, so I
re-evaluated TensorMesh on its merits. Code: [code/tensormesh_modal.py](../code/tensormesh_modal.py);
data: [tensormesh_results.json](tensormesh_results.json); figure:
[tensormesh_convergence.png](figures/tensormesh_convergence.png).

**Install:** `python3.13 -m venv` then `pip install tensormesh-fem` → **success**, exit 0, **~5.5 min**
wall (dominated by the torch 2.12 download). Pulls torch-sla, gmsh, meshio. Built-in smoke test passes
(Poisson 2D L2 err 1.19e-2). One note: torch-sla's native **sparse `eigen` backend is not built**
("requires a C++ compiler" — clang++ IS present, so it could JIT on demand, but I did not need it).

**What TensorMesh is / isn't (verified, honest):**
- It is a **continuum** differentiable FEM: elements Line/Tri/Quad/Tet/Hex via gmsh; `LinearElasticity`
  and `Mass` assemblers; sparse matrices with `solve`, `eigsh` (standard, not generalized), and time
  integrators (`ode`). **No Euler–Bernoulli beam or C1 shell element** in 0.1.1 — so a "beam" must be a
  slender 2D/3D continuum.
- **Designed differentiability is w.r.t. geometry** (`mesh.points`): grad of K w.r.t. points flows
  (finite, verified). **The convenience `from_mesh(E=...)` DETACHES E** → material-parameter gradient is
  **0** through it (verified `dK.sum()/dE = 0`, with a torch detach warning). **Workaround used:** linear
  elastic K is *exactly* linear in E (verified `max|K(2E)−2K(E)| = 0`) and M is density-independent, so I
  assemble unit K, M and scale by `(E, ρ)` tensors → **material autograd fully recovered**.
- DOF order is **interleaved** `[uxᵢ, uyᵢ]` (rigid x-translation lies in K's kernel — verified).

**Modal validation (slender 2D plane-stress cantilever, L/H=50, ν=0 for clean EB reduction):**
| mesh | free DOF | mode-1 (Hz) | err vs EB (16.71 Hz) | t (assemble+dense eig) |
|---|---|---|---|---|
| P1 (linear tri) cl=0.02 | ~300 | 24.33 | **+45.6 %** (shear locking) | 0.03 s |
| P1 cl=0.01 | ~610 | 20.70 | +23.8 % | 0.05 s |
| P1 cl=0.005 | ~2.5k | 17.54 | +5.0 % | 2.0 s |
| **P2 (quadratic) cl=0.02** | ~1.0k | 16.706 | **−0.024 %** | 0.18 s |
| **P2 cl=0.01** | ~2.0k | 16.706 | **−0.026 %** | 1.0 s |

Linear triangles **shear-lock** badly in bending (too stiff). **Quadratic (P2) elements cure it**:
mode 1 lands at **−0.026 %** vs EB (correctly just *below* EB). This is a genuine, benchmark-validated
TensorMesh modal solve.

**Differentiability for NUTS:** `∂f₁/∂E` via the factoring trick = 3.9776e-11, matches closed-form
(f₁/2E) to **relerr 8.95e-7** — but the gradient (eager torch, dense `eigvalsh` backward on the P2 mesh)
costs **~1.3 s**, and a finer P2 dense solve (4561 nodes) took **154 s** for a forward solve alone. Dense
eig scales poorly; production NUTS would need sparse `eigsh` (differentiable, present) and care near
clustered eigenvalues.

**TensorMesh vs JAX-beam — honest comparison for round 3:**
| | JAX EB beam | TensorMesh continuum |
|---|---|---|
| Benchmark match | <0.0011 % (40 elem) | −0.026 % (P2) |
| Element for slender beam | exact Hermite beam | none; needs P2 continuum (locks at P1) |
| Material-param autograd | native | needs E-factoring workaround (built-in detaches) |
| Geometry autograd | manual | **native** |
| Grad cost | **0.33 ms** | ~1.3 s (dense), needs sparse for scale |
| Stack match to NUTS (JAX/numpyro) | **yes** | no (PyTorch) |
| Install | none (uses .venv_nuts) | 5.5 min, py≥3.10 |

**Recommendation (unchanged headline):** use the **JAX beam** as the round-3 default — faster, exact,
no locking/element caveats, and it is the project's sampler stack. **Keep TensorMesh in reserve** for
when round 3 genuinely needs 2D/3D continuum geometry or native shape-gradient design; if used, use **P2
elements**, the **E/ρ-factoring** for material gradients, and **sparse eigsh** for scale.

---
### VERDICT (one line)
**GO** for a validated differentiable FEM. Default = **first-principles EB beam in JAX** (benchmark err
< 0.0011 %, interlacing 4/4, autograd 0.33 ms/grad, matches the NUTS stack). **TensorMesh also GO** now
that Python 3.13 is installed (P2 continuum cantilever −0.026 % vs EB, autograd recovered) but is slower
and has element/material-gradient caveats — reserve it for true continuum geometry.
