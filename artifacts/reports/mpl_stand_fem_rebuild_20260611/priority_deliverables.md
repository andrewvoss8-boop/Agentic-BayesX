# Priority Deliverables — MPL Stand Parametric FEM Rebuild (FABLE, 2026-06-11)

Restated in my own words from `docs/lab/mpl_stand_fem_rebuild_runner_prompt.md`.
This model is a deliberately COARSE PRIOR for a Bayesian robust-twin demo; the win
condition is correctness + parametrization + honesty, NOT fidelity.

| # | Priority ask (my restatement) | Acceptance | Delivered at |
|---|---|---|---|
| 1 | Parse the Femap/Simcenter SESTATIC deck with a real fixed-width parser (CRLF/CR, shorthand floats, continuations) and assemble global K, M in Python: Timoshenko CBEAM, flat-shell CQUAD4 (membrane+bending+drilling), CBUSH, RBE2 via MPC elimination, SPC1 elimination. Validate the element library vs textbook closed forms BEFORE the full model. | Parser counts match deck (1415 GRID, 1288 CBEAM, 72 CQUAD4, 70 CBUSH, 39 RBE2, 4 SPC1); element validation gates green in check.py | `src/parse_deck.py`, `src/elements.py`, `src/validate_elements.py`, `out/parse_summary.json`, `out/element_validation.json` |
| 2 | θ → (K(θ), M(θ)) with cheap reassembly: per-group constant matrices K(θ)=Σ s_g K_g (ShockSat pattern). Groups: shield PSHELL, CBUSH joints, 2 beam sections, foot springs (optional variant), mounted-mass attachments + masses. Numpy/scipy OK; document the JAX path. | Reassembly cost ≪ assembly; group list in packet; reassembly-vs-direct check green | `src/assemble.py`, `out/groups.json`, packet §parametrization |
| 3 | Add backside mounted masses estimated FROM PHOTOS (Andrew's live instruction): valve panel, electronics box, upper white box as CONM2+CBUSH (local mode each); PSU as bare CONM2. Every estimate: ledger entry w/ value/units/rationale/sensitivity priority, ANDREW-CONFIRM-REQUIRED, and a parameter. Packet lists exact questions for Andrew. | Ledger + question list exist; estimated-mass gates at best YELLOW | `assumptions_ledger.md`, `src/mounted_masses.py`, packet §questions-for-Andrew |
| 4 | Modal solve 0–500 Hz (≥30 modes) + sanity gates: mass closure, 6 rigid-body modes free-free, no negative eigenvalues, DUAL mode tables (t=0.5 deck-nominal vs 16 ga) for the #1 sensitivity knob, dominant-region (kinetic/strain-energy fraction) per mode. | check.py gates; both tables in packet | `src/modal.py`, `out/modes_nominal.json`, `out/modes_16ga.json`, packet mode tables |
| 5 | Interface points: nearest grid(s) to (a) SHIELD MOUNT = top-center of shield top edge; (b) BEAM MOUNT = top-left (viewed from logo side) on the BACK wall of the top beam. Grid IDs + coords, marked on figures, panel-vs-frame motion across modes; flag interpretation if ambiguous. | Grid IDs + coords reported + marked in figures | `src/interface_points.py`, `out/interface_points.json`, figures |
| 6 | Mode-shape GIFs for ≥10–15 flexible modes (3-D wireframe, freq+mode+stamp on figure, feet marked, undeformed overlay, per-mode normalized scale PRINTED, "shapes not amplitudes" stated) + one small-multiples PNG. Tufte skill + tufte_lint on saved .py; image-legibility QA. | GIFs + PNG exist; lint + QA artifacts | `src/make_gifs.py`, `src/make_figures.py`, `gifs/`, `figures/`, `out/image_qa.json` |
| 7 | packet.md (method summary up front, dual mode tables, GIF index, ledger, Andrew questions, honest limitations) + check.py green/yellow/red + run_all.sh one-command replay + runtime.json + manifest.json. | `bash run_all.sh` replays; check.py exits 0 unless RED | `packet.md`, `check.py`, `run_all.sh`, `runtime.json`, `manifest.json` |

Ambiguities flagged at start (per Clarification Gate):
- **A-priority-1:** Real shield gauge unknown — Andrew has NOT supplied it; 0.5 in kept
  as deck-nominal prior mean per card, 16 ga variant reported, question listed.
  STATUS: assumed-with-both-interpretations (dual tables) = the card's own remedy.
- **A-priority-2:** Mounted-mass masses/locations not provided — Andrew said (chat,
  2026-06-11) to estimate from photos. Estimates = priors, YELLOW at best.
- **A-priority-3:** "Top-left on the back wall of the top beam" — interpreted in deck
  coordinates after parsing; interpretation stated with a figure; flagged
  ANDREW-CONFIRM-REQUIRED if the geometry leaves doubt.

Sampler decision: NO sampler this task (future NUTS task will consume K(θ),M(θ)).
