# Files Changed / Authorship Map — ShockSat Modal Twin

Authorship is interleaved across three sessions (two ran in parallel by
accident; reconciled in `decisions_log.md` D16/D19/D20/D21). "S1/S2/S3" =
session 1 / 2 / 3. The canonical division is D19; this is the artifact-level map.

## Pipeline scripts (`scripts/`)
| file | wrote | role |
|---|---|---|
| parse_nastran.py, parse_ash.py | S1 | parse deck + measured .ash |
| fe_core.py, fe_validate.py | S1 | element library + validation |
| assemble_fem.py | S1 (+S2 drilling fix D12) | per-PID K/M assembly, RBE2 T |
| solve_nominal.py | S2 | nominal eigensolve + obs operator + MAC |
| pairing.py | S2 | Hungarian 1:1 mode pairing |
| reduce_model.py | S2 | 74-mode reduced basis + probes |
| enrich_basis.py | S2 | basis enrichment (ABANDONED on cost, D18; kept replayable) |
| noise_floor.py | S2 | replicate frequency noise floor |
| run_nuts.py | S2 canonical (D19; +S3 env-var/depth knobs D21/D22) | NUTS model, convergence, predict |
| lomo_parallel.py | S3 (D21) | parallel leave-one-mode-out driver |
| run_full.py | S3 | full 18-mode calibration |
| validate_posterior.py | S2/S3 (repointed to theta_full, D29) | reduced-vs-full at posterior theta |
| sensitivity.py | S2 | prior/MAC/band-edge arms |
| make_lock.py | S2 | lock-before-reveal hashes |
| make_figures.py | S2 (+S3 theta_posterior_full) | core figures |
| make_figures2.py | S3 | graphical model, LOMO, convergence figures |
| make_femap_deck.py | S2 | FEMAP normal-modes decks |
| hash_inputs.py | S2 (+S3 format fix D30) | input integrity hashing |
| joint_strain_energy.py | S3 (D36) | modal strain-energy decomposition (Modal Identifiability Gate) → joint_strain_energy.json |

## Reports / docs (root)
| file | wrote |
|---|---|
| measured_modes_provenance.md, measured_modes_summary.json | S1 (Task 0) |
| fem_parse_report.json, fe_validate_report.json, assembly_meta.json | S1 |
| fem_assembly_report.md | S2 (lead) |
| question_framing.md, quantity_contracts.md, assumptions_ledger.md | S2 (lead) |
| priority_deliverables.md | S1 |
| lead_code_review.md | S2 (lead review of pairing/run_nuts) |
| nominal_modes.json, nominal_mac_table.json | S2 |
| groups.json, reduction_report.json, noise_floor.json, pairing.json | S2 |
| run_all.sh, check.py | S2 (+S3 D23/usage) |
| **packet.md** | **S3** (this packet) |
| decisions_log.md | S1→S3 (D1–D30) |
| **files_changed.md, manifest.json, runtime.json (final)** | **S3** |

## Compute outputs (S3 unless noted)
- convergence_full.json, theta_full.json, nuts_full_samples.npz (full, gate PASS)
- convergence_band.json, heldout_band.json, nuts_band_samples.npz (band remedy, FAIL)
- heldout_lomo.json + logs/lomo_partial_*.json (LOMO, FAIL, coverage 18/18)
- sensitivity.json (5 arms)
- posterior_validation.json (reduced≈full, 0.068% max)
- heldout_lock.json (prediction hashes)
- inputs_sha256_end.json (0/50 changed — D30 format fix)
- checker_report.json (green/yellow/red: overall YELLOW = 15 green / 2 yellow / 0 red; the 2 yellows = documented convergence findings)
- figures/*.png (7), femap_handoff/* (decks + instructions + theta_posterior_mean.json)
- logs/failrun1_* (the FIRST band run, depth-8, PRESERVED as the multimodality evidence)

## Inputs (read-only, gitignored raw data; proven unchanged)
- `inputs_sha256_start.json` vs `inputs_sha256_end.json`: 0/50 content changes (D30).
- Measured: `Final_FF_Test_Shapes_100121.ash` (sibling extracted tree).
- Deck: `FEM_20211021/*.blk`, `*.dat` (sibling extracted tree).
</content>
</invoke>
