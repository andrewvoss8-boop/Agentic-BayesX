# Recommended next steps

## Cheap corrections

1. Promote the isolated repair, not the original collector output.
   - Cost: under 1 hour.
   - Use `shocksat_full_spectrum_frf_repair_20260716/out/` for finite S1/S2 statistics and F=C.
   - Withdraw the original F=R row, null error bars, and "all S1-S5 falsified" sentence.
   - Correct conclusion: S1, S2, and S5 are not met; S3 and S4 are unresolved.
   - Closes: C8 and the result-status error in C5.

2. Regenerate the arms figure from repaired values and stamp limitations on it.
   - Cost: 1 to 2 hours.
   - Show actual fold SE, remove the false F=R duplicate, label C exact as invalid pending per-fold refits, and print arm-B/C worst R-hat 360.6 and ESS 2.0 beside any MAP-based result.
   - Closes: C2, C6, C8 presentation gaps.

## Cheap new compute

3. Refit arm C on each exact fold.
   - Cost: 0.5 to 2 CPU-hours based on the logged MAP runtime; no NUTS rerun.
   - For each leave-one-drive-out fold, fit the shape MAP on its three training drives using the enriched basis, then score only the excluded drive.
   - Acceptance: no held-out drive enters its shape fit; four exact fold scores and paired SE exist.
   - Closes: C6 and the unsupported "C collapses" part of H1.

4. Full exact re-rank of all 28 remodel candidates.
   - Cost: about 3 CPU-hours of eigensolves from the observed 6 to 9 minutes per enrichment, plus scoring; budget 4 to 6 wall-clock hours detached and resumable.
   - Enrich every candidate at its own theta_MAP, then re-score all 14 agent and 14 random candidates with identical folds, warp, gain, and bands.
   - Report track maxima, paired fold SE, rank changes, and candidate-specific screening bias.
   - Closes: C1 and the winner's-curse gap in C7.

5. Reproduce the delivered net-CG reference before changing tiers.
   - Cost: 1 to 3 engineer-days, under 1 CPU-hour after implementation.
   - Port the validated QOI model and statFEM F(k) path byte-for-byte until A1 reproduces 1.51/2.30/2.53 within a pre-registered tolerance. Only then apply wide-band tier updates and compare arms.
   - Acceptance: reference reproduction first, held-out coverage at least 0.95, hide-top-3 audit responds where the hidden modes carry participation.
   - Closes: C5; resolves S3/S4.

## Genuine model-form experiment

6. Run a stratified model-form pilot rather than asking the agent for unconstrained free-text edits.
   - Cost: 3 to 5 engineer-days to build the action executor, then about 8 to 16 CPU-hours for 30 agent and 30 matched-random candidates.
   - Outer loop is discrete model search. Inner loop recalibrates continuous theta for each candidate. NUTS/HMC is not the discrete model selector.
   - Give both tracks equal quotas in five families:
     1. Geometry: attachment location, bracket footprint, midsurface offset, and joint footprint within drawing or survey tolerances.
     2. Element formulation: RBE2 versus RBE3 plus CBUSH, beam versus shell bracket idealization, and quad-dominant versus mixed shell formulation.
     3. Connectivity: tie radius, weld segmentation, distributed versus point attachment, and compliant rotational connection.
     4. Mesh topology and density: conforming h-refinement, alternate transition patterns, local coarsening controls, and plate/joint region remeshing.
     5. Property-only control: thickness, stiffness scale, and region split.
   - Do not let residual diagnosis choose only the easiest family. Require six candidates per family before adaptive allocation.
   - Match the random control by family, changed DOF count, and estimated solve cost.
   - Mechanical gates before scoring: six rigid-body modes, no disconnected components, positive stiffness, mass change within the declared geometry contract, element-quality limits, and a finite perturbation that moves the targeted modes/QOI.
   - Evaluation: train-side diagnosis only; deterministic multi-start theta_MAP per candidate; exact full-order basis at theta_MAP for every candidate; four-drive LODO score; net-CG coverage hard gate after C5 is fixed.
   - Stop condition: if rankings are unstable across drive folds or model-form effects remain below discrepancy, report data/BC limitation rather than escalating search.
   - Closes: C7 and directly tests Andrew's geometry, element type, mesh form/density question.

7. Prefer the MPL stand for the first full model-form demonstration, then transfer the harness to ShockSat.
   - Cost: 1 to 2 weeks including one controlled validation campaign.
   - Reason: MPL geometry and mesh are editable and new measurements can adjudicate model-form changes. ShockSat is archive-only, so a larger discrete search has a higher risk of fitting one campaign without a new physical answer key.
   - ShockSat remains useful as the fixed-data stress test after the action grammar passes on MPL.

## Expensive compute, after the method gaps close

8. Extend the FEM basis with a high-RAM CPU eigensolver.
   - Cost: 1 to 3 engineer-days plus roughly 6 to 24 compute-hours on a 64 to 128 GB CPU node.
   - Use partitioned shift-invert/SLEPc or equivalent, overlap-check adjacent slices, and certify modes to at least 1.25 times the scoring ceiling.
   - Do not describe the 1250 Hz problem as generally infeasible until this solver class is tested.
   - Closes: C4 and enables a real 500 to 1000 Hz arm table.

9. Use TMCMC only if posterior uncertainty remains decision-relevant after model-form and QOI repairs.
   - Cost: 2 to 4 engineer-days plus 2 to 8 compute-hours for a checkpointed pilot.
   - First verify the likelihood and forward model on held-out data. Then use a float64 CPU/high-RAM or A100 population run and report global mode weights.
   - A second sampler cannot rescue an invalid arm-C fold, a mismatched net-CG port, or a narrow action space.
   - Closes: C2 if a trustworthy global posterior is still needed.
