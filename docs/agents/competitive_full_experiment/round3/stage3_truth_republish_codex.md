# Stage-3 Truth Re-publish — Codex GPT-5.5 (bounded; conserve credits)

Paste into Codex GPT-5.5 at the master repo root. SAME sealed truth as before — only the netCG QOI is
recomputed to the canonical definition, then re-published + re-sealed. NO new model-form error, NO
inference, NO NUTS.

```text
You are the TRUTH-AUTHOR for Agentic BayesX round 3, Stage-3 prep (Codex GPT-5.5). You previously
authored the independent ground truth in runs/round3/codex_truth/. A definitional inconsistency was
found in the netCG QOI; fix ONLY that, keep everything else identical, re-publish, re-seal.

INDEPENDENCE RULE (unchanged): your entire workspace is runs/round3/codex_truth/. Do NOT read the
inference agent's code/model under runs/round3/opus48/. Read ONLY:
docs/agents/competitive_full_experiment/round3/netcg_quantity_contract.md (the new canonical netCG),
your own runs/round3/codex_truth/ files, and the shared protocol/task card.

WHAT TO CHANGE (only this):
- Recompute the truth's netCG QOI per netcg_quantity_contract.md: netCG = F_iface(omega)/m_load with
  F_iface the DYNAMIC transmitted interface force from FBS/impedance coupling of your source and load
  interface apparent masses (it must RESONATE at the coupled modes), m_load = your published
  load_mass_kg. You previously used the rigid mass-ratio constant transmission (~0.28); that is FORBIDDEN
  for the QOI now (keep it only as the f->0 sanity check). Verify the f->0 rigid limit and the resonant
  amplification.
- Keep the SAME as-built truth structures, the SAME per-build/per-flight draws, the SAME model-form
  imperfections (spatial symmetry-breaking + higher modes + per-DOF stiffness + sensor noise) and the
  SAME apparent-mass observations. Do NOT add or change model-form error — Stage 3 must test the SAME
  truth that the frequency-only discrepancy failed on.

RE-PUBLISH (runs/round3/codex_truth/dataset/):
- Recompute and overwrite ONLY the netCG-derived published quantities (e.g. netcg_3grms_g and any
  per-flight netCG PSD) using the canonical definition. The interface apparent-mass observations and the
  interface acceleration response PSD are UNCHANGED. Update data_contract.md to (a) state netCG now
  follows netcg_quantity_contract.md and (b) reference that contract; keep it OBSERVABLES-ONLY.

RE-SEAL (runs/round3/codex_truth/sealed_truth/):
- Recompute the netCG SCORING KEY (clean, noise-free truth netCG per the canonical definition; per-build
  x per-flight) and overwrite scoring_key.json/.npz accordingly. Leave the rest of the sealed truth
  (true_parameters, model_form_imperfections, generator) unchanged except the netCG computation.

LOG: append to decisions_log.md exactly what changed (netCG recompute to canonical dynamic FBS;
forbidden rigid mass-ratio removed) and confirm the f->0 limit + resonant structure. Update runtime.json.
DO NOT: change the model-form error, run inference, produce GIFs/PPT, read runs/round3/opus48/, or write
outside runs/round3/codex_truth/. Then stop.
```
