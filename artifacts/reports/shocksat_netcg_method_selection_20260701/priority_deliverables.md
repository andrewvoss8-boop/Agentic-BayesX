# priority_deliverables — ShockSat net-CG force method selection

Each PRIORITY ask (from the runner prompt) -> interpretation -> where delivered. A priority with no artifact = failure.

| # | Priority ask (prompt) | Interpretation | Delivered in | Status |
|---|---|---|---|---|
| P1 | Pick, PER QOI, the ONE updating method that passes the two-part selection rule (coverage hard-gate, then sharpest) and hand back shear + normal net-CG force bands + trust label | Bake off formulations on the net-CG force held-out objective; select per QOI | Stage 2/3: `out/bakeoff_scorecard.json`, `findings.md`, `figures/` | see packet status |
| P2 | Robustness requirement: selected method must NOT falsely sharpen the unmeasured-mode-driven (normal) QOI; overconfidence = DISQUALIFIER | Leave-modes-out humility test + coverage hard-gate on normal | Stage 2 `out/leave_modes_out.json`; §5 mechanism | see packet status |
| P3 | Fold in +Y (Test03/990y) as the 5th drive; quantify whether it lifts NORMAL trust / observes 234-254 Hz | Distill +Y to canonical cache; re-run trust w/ +Y observability | `data/multiref_modal/m_ypos_990y.npz`, `out/stage0_observability.json`, `out/stage0_trust.json` | DONE |
| P4 | QOI sensitivity + validity gate + sensitivity on assumed unmeasured-mode sigma (Stage 0) | Per-QOI mode/sensor weights, trust, validity, SD_F_U/SD_A_U sweep | `out/stage0_qoi_weights.json`, `stage0_trust.json`, `stage0_validity.json`, `stage0_sensitivity.json`, `figures/fig_stage0_qoi_trust.png` | DONE |
| P5 | Mesh screen (Axis B step1): score ~50-edit pool on a cheap held-out proxy, keep top ~3; carry through updating | Bounded blind QOI-shear proxy screen -> inherited + top 3 mesh axis | `out/mesh_screen_summary.json`, `code/mesh_screen.py` | RUNNING (detached) |
| P6 | ONE held-out harness + immutable SHA-locked checker (coverage 1-oct, sharpness, point) | net-CG force functional + answer key + 3 scores + `check.py` locked | Stage 1: `code/netcg_qoi.py`, `check.py`, `CHECKER.sha256` | see packet status |
| P7 | Two-problem delivery: shear sharp validated band; normal covering band + trust label + "one test that fixes it" | Stage 3 delivery figures + findings | `figures/`, `findings.md` | see packet status |
| P8 | All AGENTS gates (assumptions, identifiability, references, plots, sensitivity, discretization, verification, runtime) | Gate docs + checker | this workspace root docs + `runtime.json` | see per-gate rows in packet |

Notes: normal-QOI NUMBER is data-starved (Stage-0 validity PARTIAL, shape-trust 45%); per the autonomy rule its
deliverable is a covering band + leave-modes-out mechanism validation + a >200 Hz plate-test recommendation, NOT
a sharp number. Winner's-curse: the bake-off reports N (configs compared) and reads the winner as "best of N".
