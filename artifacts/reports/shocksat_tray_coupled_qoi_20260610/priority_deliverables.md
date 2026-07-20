# Priority deliverables — shocksat_tray_coupled_qoi_20260610

Restated in my own words from the task card
(`docs/lab/shocksat_tray_coupled_qoi_runner_prompt.md`, scope locked by
predecessor decision D38). Status updated as delivered.

| # | Priority ask (my restatement) | Interpretation / where ambiguous | Delivered artifact |
|---|---|---|---|
| P1 | Quantity contract FIRST for the net-CG-load QOI and the apparent-mass quantities, with the source/load convention traps pinned (postmortem + 7004C Fig 9) | Unambiguous after postmortem re-read; free-free-source deviation from the Fig 9 grounded-source cartoon stated explicitly | `quantity_contracts.md` |
| P2 | Method comparison: how much modal-SRS and PSD/Miles over/under-predict the net CG load vs the time-history reference, conservatism quantified, under model + mount uncertainty | Same environment for all three methods (one input spec, methods differ only in how they consume it) | `out/qoi_results.json`, packet §5, `figures/fig_method_comparison.png` |
| P3 | Uncoupled→coupled gap = apparent-mass / force-limiting quantification, tied to NASA-HDBK-7004C (notch / over-test shown) | Coupled = LM-FBS with validated ShockSat ROM as source; uncoupled = same chain driven rigidly by the free-interface motion | packet §6, `figures/fig_force_limiting.png`, `figures/fig_apparent_mass.png` |
| P4 | Mount-stiffness sensitivity: is the QOI mount-dominated? Apply the Modal/Eigenproblem Identifiability Gate to the coupled interface modes | Mount-dominance = variance share of the QOI from mount-stiffness uncertainty vs ShockSat-theta vs tray-theta vs seed; gate = strain-energy decomposition + finite perturbation, no sampler claim | `out/variance_decomposition.json`, `out/mount_identifiability.json`, packet §7, `figures/fig_mount_sensitivity.png`, `figures/fig_identifiability.png` |
| P5 | Honesty/labeling: coupled tray QOI is HYPOTHETICAL (methods demo, no hardware-validation claim); invented assumptions ledgered; figures carry run/invalidity labels | Every data figure carries run label + "HYPOTHETICAL" flag | all figures, `assumptions_ledger.md`, packet banner |
| P6 | Workspace mechanics: priority_deliverables, question_framing, quantity_contracts, assumptions_ledger, check.py (green/yellow/red), run_all.sh, runtime.json, manifest.json, files_changed.md, decisions_log.md, packet.md with method summary + graphical model AT TOP | — | this workspace |

Ambiguity flags raised at start (per the Clarification Gate):
- A-flag-1: base input definition — interpreted as a SPECIFIED synthetic
  moderate random (D2); both the card and D38 explicitly allow this; the
  measured-strut-base alternative was rejected for vault-integrity reasons.
  Surfaced for sign-off, not blocking.
- A-flag-2: tray placement node and mount nominal stiffness are INVENTED by
  design (the card says so); values chosen with stated rationale (D3, D4) and
  swept in sensitivity arms. Surfaced for sign-off, not blocking.
- No other priority ask was ambiguous.
