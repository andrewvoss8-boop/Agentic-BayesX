# Priority deliverables — FEM feasibility spike

Restating the master's PRIORITY asks in my own words, my interpretation, and where delivered.

| # | Priority ask | Interpretation | Delivered |
|---|---|---|---|
| 1 | Try TensorMesh first; fall back to scikit-fem if immature/won't install — state which & why | Attempt the PyTorch differentiable lib; pick honest fallback | Initially TensorMesh **wouldn't run** (py≥3.10 vs 3.9.6) → fell back to a first-principles EB FEM **in JAX** (not scikit-fem; NUTS stack is JAX, scikit-fem isn't autodiff). **After human installed Python 3.13 (uv), TensorMesh was retested and now runs & validates** (P2 continuum −0.026% vs EB). Both paths documented; JAX recommended. [commands.md](commands.md) §A/§C, [report/spike_report.md](report/spike_report.md) §1+§8 |
| 2 | Build ONE component; assemble K & M | Beam, Hermite-cubic, consistent M | [code/beam_fem_spike.py](code/beam_fem_spike.py) `assemble()` |
| 3 | Solve modal (first ~5) + single-DOF drive-point interface FRF (accelerance) w/ light damping | eig + modal-superposition FRF at tip, ζ=2% | results.json `mesh_convergence`,`frf`; figs modes/frf |
| 4 | Validate vs analytical benchmark; report error %; confirm FRF antiresonance interlacing | βL cantilever; interlacing test | err < 0.0011% (nele40); 4/4 antiresonances interlaced. §3–4 |
| 5 | Differentiability: gradient of a natural freq (or FRF) w.r.t. a material/geom param flows; report works + cost | jax.grad of f₁ wrt E,h | matches closed-form 1.2e-9; 0.33 ms/grad. §5 |
| 6 | Deliver code/, report/spike_report.md, figures, commands.md, one-line VERDICT (GO/NO-GO) + scaling honesty | — | all present; VERDICT = **GO** — default **JAX EB beam**; **TensorMesh also GO** on py3.13 (reserve for continuum geometry). report §VERDICT+§8 |

**Ambiguity flagged & resolved:** "differentiable-first tool" assumed PyTorch (TensorMesh) per the
recon doc, but the project's actual sampler is JAX/numpyro. Since TensorMesh would not run anyway, I
resolved this by building the differentiable FEM in **JAX**, which both satisfies #5 and matches the
real pipeline. This is an assumption stated prominently, not a silent swap.
