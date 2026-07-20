# Priority Deliverables (Andrew's asks, restated + delivery map)

| # | Andrew's ask (his words) | Interpretation (confirmed) | Delivered at | Status |
|---|---|---|---|---|
| P1 | "FEM of a rocket of the terran R/falcon 9 class … high resolution (most focused) modeling of the secondary structures on the dome … trays and COPV's" | Representative public-data fine-region FEM: dome + ring + barrel-to-first-frame + avionics tray + COPV + avionics lumped mass, mesh/truncation-converged to 400 Hz (D2/D4/D5) | P1 step 2 | NOT STARTED |
| P2 | "buffet forcing functions (patches of applied random force with varied correlations based on length scale/frequency)" + "include buffet and acoustic" | Pressure-field CSD forcing: Corcos convective buffet + diffuse-acoustic-field sinc coherence; rigorously = joint-acceptance modal forcing; 2 load cases LC1/LC2 (D3/D8/D9) | P1 steps 1+3 | IN PROGRESS (step-1 math validation) |
| P3 | "Should be valid up to 400 Hz" | REFRAMED (Andrew accepted, D4): fine region converged to 400 Hz; far-field uncertainty-bounded; coupling certified by convergence study + monolithic toy + CI coverage — never a deterministic full-vehicle claim | P1 step 2 (mesh conv.), P2 (truncation conv. + toy) | NOT STARTED |
| P4 | "QOI's should be strut loads, netCG loads (punch load into the dome), a good representative for the secondary structure, and accel at specific location on the tray at a lumped mass (avionics)" | Four pinned QOIs, PSDs + RMS over 20–400 Hz, both load cases (D6; contracts in quantity_contracts.md) | P1 step 3 | NOT STARTED |
| P5 | "CI is key" | Interval-valued QOIs from documented priors (damping, forcing, mounts, boundary impedance, gauge); intervals must WIDEN with model ignorance, never falsely narrow (D7) | P3 | NOT STARTED |

Warnings / assumed interpretations:
- P3 reframe was explicitly discussed and accepted in chat 2026-06-12 ("sounds good").
- D8 (separate liftoff/max-q load cases) and D9 (external fields on barrel OML,
  internal reduced-level DAF on dome/secondaries) are LEAD DEFAULTS flagged for
  Andrew's veto — both are cheap to change.
- All vehicle numbers are training-knowledge "public data" pending web verification
  (assumptions_ledger VERIFY list). No number in this study is a verified Terran-R fact.
