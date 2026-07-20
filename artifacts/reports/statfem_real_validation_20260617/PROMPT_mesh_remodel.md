# Runner prompt — Card D: data-driven FEM remodeling of the high-error ShockSat regions

You are a **runner agent** in **Agentic BayesX** with a **structural-FEM / model-correlation** task. Lead = Claude
Code; human = **Andrew Voss**; advisor objective = **Ilias Bilionis**: *"evaluate the StatFEM approach… identify its
gaps, and suggest improvements."* This card asks a sharper question: **can an agent contribute to FEM correlation by
re-meshing the model based on where the data says it is wrong?** Build for correctness, reproducibility,
traceability. Plain English on ML/stats; structural-dynamics terms (FEM, mesh, modal, MAC, FRF, joints, bulkheads)
used directly. **Never claim a correlation improvement without before/after MAC + frequency + the checker/figures
that prove it.**

## 0. RE-GROUND FIRST
Read `AGENTS.md` (every gate binds), then the validation study spine:
`artifacts/reports/statfem_real_validation_20260617/decisions_log.md` (D0–D22, esp. **D21 instrumentation review**
and **D22 mode-shape findings**) and `packet.md` (§2 verdict, §8 limitations). Then read the ShockSat source
documentation in `artifacts/reports/shocksat_statfem_runner_20260609/extracted/` — the **FEM decks** (`extracted/FEM/`,
Nastran cards: CQUAD4/CTRIA3/CBUSH/CONM2/RBE2/PSHELL/PBUSH), the **correlation reports**
(`extracted/FEM/Correlation/…`, incl. `Instrumentation_locations.xlsx`, `ShockSat_measured_weights.xlsx`,
`Test_log_4-29-21.xlsx`, the free-free mode-shape summaries), and the **modal-survey data**
(`../shocksat_fem_modal_twin_20260609/measured_modes.npz` = 33 modes × 76 nodes × 3 axes, + damping;
`measured_modes_provenance.md`). Restate goal / last decision / next action / open ambiguities in one line.

## 1. WHERE THE MODEL IS WRONG (the target regions — artifact-backed, do NOT re-derive)
Across a 25-split held-out Monte-Carlo, a FIXED set of sensors miss the 95% predictive band almost every split,
with **clean raw data (no clipping/saturation; appropriate sensor ranges; pass/fail uncorrelated with SNR)** and
**not a node-mapping artifact (snap→interp <1%)**. Per the instrumentation log (`ShockSat1_Instrumentation_and_
TestLog_…xlsx`), every one sits on the **+X impact/source face at a structural interface or the dish:**

| sensor | location (in) | description | nature of the hard physics |
|---|---|---|---|
| ch4 | (9, −1.5, 2.3) | Source +X Face Center | near-field / impact-face local dynamics |
| ch27 | (9, 7.1, 1.9) | Source +X Face +Y Edge | impact-face edge |
| ch38 | (7, −9, 1.75) | Source −Y Face +X Edge | source-box corner |
| ch40 | (9, −0.4, 10.4) | Steel Box **Below Bulkhead** | **bulkhead interface** |
| ch52 | (9, −0.4, 19.1) | Al Box **Above Bolted Joint** | **bolted-joint stiffness/damping** |
| ch69 | (9, −0.4, 28.7) | Al Box **Below Bulkhead** | **bulkhead interface** |
| ch92 | (8.7, 0, 49.6) | **Strut Base (+X)** | **strut-to-deck interface** |
| ch98 | (1.9, 0, 57) | **Dish Center** | flexible dish / local modes |

**Diagnosis from the validation study:** the as-received NASA-correlated FEM gets the global mode FREQUENCIES well
and the mode SHAPES mostly well (MAC-matched ≈0.73 vs the `.ash` survey), but **per-sensor amplitude is wrong at
these interface/near-drive locations** — the classic StatFEM hard part: **joint/bulkhead stiffness+damping, the
strut and dish local dynamics, and impact-face near-field response that a coarse mesh under-resolves.**

## 2. YOUR TASK — make a COPY of the FEM and re-mesh those regions to improve correlation
1. **Diagnose the mismatch quantitatively, region by region.** For each target region, compare FEM vs `.ash` measured
   mode shapes (MAC per mode, restricted to the region's sensors) and the FEM-vs-measured FRF/peak amplitude at those
   channels. Identify WHICH modes and WHICH physics (joint stiffness, bulkhead connectivity, strut/dish local modes,
   mesh density) drive the error. Write `region_diagnosis.md` with the evidence.
2. **COPY the FEM** into a NEW workspace (`artifacts/reports/shocksat_fem_remesh_YYYYMMDD/`). **Never edit the
   inherited model in place.** Verify the copy reproduces the baseline modal results first (eigenfrequencies + MAC)
   — establish the BEFORE baseline.
3. **Make targeted MESH/MODEL edits** in the high-error regions only, each justified by the diagnosis and documented:
   e.g., refine the mesh at the bulkhead/bolted-joint interfaces; correct connectivity/RBE/CBUSH joint stiffness;
   refine the strut-base and dish local geometry; add/adjust interface stiffness+damping where the data demands it.
   Keep edits MINIMAL and TRACEABLE (one change → re-solve → measure the effect); do not globally re-tune.
4. **Re-solve and measure the AFTER correlation.** Eigen-solve the edited model (use the available FEM tooling —
   the modal-twin pipeline / CalculiX in `.conda_calculix`, or document the solver). Report **before vs after**:
   per-mode frequency error and MAC vs `.ash`, AND the held-out-FRF/peak agreement at the 8 hard channels.
5. **Honest verdict:** did data-driven re-meshing IMPROVE the correlation at the hard regions WITHOUT degrading the
   rest (global MAC/frequency must not get worse)? Quantify. If it does not help, say so and diagnose why (e.g., the
   error is damping not stiffness/mesh).

## 3. THE META-DELIVERABLE (the actual research question)
**Can an autonomous agent adequately contribute to FEM correlation by remodeling from data?** Deliver a
`correlation_contribution.md` that honestly assesses: what the agent could diagnose, what mesh edits it made and
why, the measured before/after improvement, where human FEM judgment was still required, and the residual risk.
This is the headline — a credible, auditable yes/no with evidence, not a polished but unverifiable model.

## 4. Constraints / honesty
Plain ShockSat only (no coupled tray). **COPY-never-edit** the inherited FEM. Validate the BEFORE baseline before
any edit. Every "improved correlation" claim needs the before/after MAC+frequency table AND a figure. Do not overfit
the mesh to the 8 sensors at the expense of global correlation (report global MAC both ways). Reduced-model fidelity
must be re-verified if you re-reduce (the validation study's reduction matched the full FEM eigenfreqs to 3e-10 —
hold that bar). SURFACE to the lead/Andrew (don't self-apply): any durable-rule/checker change, any claim that the
remodeled FEM should REPLACE the inherited one, and the `docs/report/project_log.md` row. Mesh edits + diagnoses are
study artifacts and need no stop. Compute: pin BLAS threads, float64, long solves detached + resumable.

## 5. WIN CONDITION
A copied, re-meshed ShockSat FEM whose **per-mode MAC and FRF/peak agreement at the 8 hard channels measurably
improve** vs the as-received model **without degrading global correlation**, with every edit justified by the
data-mismatch diagnosis and a before/after evidence table — plus the honest `correlation_contribution.md` verdict on
whether the agent genuinely advanced the correlation effort.
