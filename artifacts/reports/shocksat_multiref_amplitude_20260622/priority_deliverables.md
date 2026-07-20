# Priority deliverables — Card G (multi-reference amplitude)

Each priority restated in my own words, with its interpretation and where it is delivered. A priority with no
delivered artifact is a failure; an "assumed" interpretation without confirmation is a warning.

| # | Priority (my words) | Interpretation | Delivered in | Status |
|---|---|---|---|---|
| P1 | **Part A — DUPLICATE the Card F value program on +X-only** as an integrity/repro baseline | Run the byte-identical copied code; reproduce freq skill ≈+0.93, amplitude skill ≈−1.0, Beck −0.68→−0.25 within tolerance | `out/partA_freq_value_seed00.json`, `out/partA_value_eval_seed0*.json`, `out/partA_modal_beck_ash.json`; check.py `partA.*` gates | PENDING |
| P2 | **Coherence diagnostic FIRST** (cheap, do not stop on it) | Build per-reference FRFs (force=Rec116, identical realfrf windowing/H1); report multi-hit coherence at drive point + 8 hard accels for +Z/+Y/900z; contextualises every amplitude verdict | `out/coherence_by_reference.json`, `figures/fig_coherence.png` | PENDING |
| P3 | **Held-out AMPLITUDE skill — BEFORE(+X)/AFTER(multi-ref) headline** | Calibrate using ≥2 references; predict held-out sensor peak-|H|/band-GRMS; CRPS-skill/interval/coverage/z-std vs climatology, same seeds/splits; does it rise from ≈−1.0 toward/above 0? | `out/multiref_value.json`, `figures/fig_value_multiref.png`; check.py `partB.amplitude` | PENDING |
| P4 | **Frequency skill preserved under multi-ref** | Confirm the +0.93 freq skill is not hurt (and report whether multi-drive adds matched modes) | `out/multiref_freq.json`; check.py `partB.frequency` | PENDING |
| P5 | **MECHANISM figure (the proof)** | Per-mode (φ_{s,k}, ζ_k) posterior collapse single-ref RIDGE → multi-ref POINT, and/or drive-shape ratio |H(d1)|/|H(d2)| recovering φ_d ratios; tie every claim to this, not a bare score move | `out/drive_shape_ratio.json`, `figures/fig_mechanism.png`; check.py `partB.mechanism` | PENDING |
| P6 | **Identifiability gate re-run WITH multi-ref** | FIM/strain-energy: how many parameter directions clear the realized discrepancy floor single-ref vs multi-ref (earns the "multi-ref is the fix" pre-test claim) | `out/multiref_identifiability.json`, `figures/fig_identifiability.png`; check.py `partB.identifiability` | PENDING |
| P7 | **Damping + Beck shape-field re-run with multi-ref** | Re-run the ≤0 levers (damping_inference, modal_beck_ash) with references that now separate participation from ζ — do they become positive? | `out/multiref_damping.json`, `out/multiref_beck.json` | PENDING |
| P8 | **Gates + honesty** | NUTS all-variable convergence (R̂≤1.05/ESS≥200/div<2%) or YELLOW; re-pairing-robust; three-tier; units-gain caveat on every amplitude number | `decisions_log.md`, `packet.md`, all `out/*.json` diag blocks | ONGOING |
| P9 | **Reproducibility + traceability** | one-command replay `run_all.sh`; `runtime.json` (active vs elapsed + disk footprint); figures via saved `.py` + tufte-lint + `out/image_qa.json`; locked check.py | `run_all.sh`, `runtime.json`, `code/fig_*.py`, `out/image_qa.json`, `check.py` | PENDING |

## Win condition (card §7) — the scoped, honest answer
One of three, each backed by mechanism + held-out score + figure:
- (i) YES — multi-reference breaks the confound and amplitude becomes skillful (score + φ/ζ posterior collapse);
- (ii) NO, data-quality — impact-hammer coherence too low (evidence; pyro is next);
- (iii) NO, even with the confound provably broken — the Card F amplitude limit is genuinely model-form/QOI-intrinsic,
  now EARNED (FIM + still-negative skill).

## Surface-to-Andrew (autonomy does NOT cover these — NOT self-applied)
- any durable-rule / checker-standard / sampler-standard change;
- any claim the twin should REPLACE the inherited FEM;
- the `docs/report/project_log.md` row.

## FINAL STATUS (2026-06-22, check.py GREEN 18/0/0)
- **P1 Part A reproduce — DONE/GREEN.** freq +0.931, amp −1.00, Beck −0.680→−0.252 = Card F exactly (`out/partA_*`).
- **P2 coherence — DONE/GREEN.** `coherence_by_reference.json` + `fig_coherence.png`: impact ~0.28–0.39 at resonances,
  modal +Y 0.92 (instrument split). +X broadband "~0.07" shown to be a 100–10 kHz artifact.
- **P3 held-out amplitude before/after — DONE (headline = NEGATIVE).** `multiref_value.json`+`fig_value_multiref.png`:
  −1.00 → −0.11 (measured residue), none of +Z/+Y/900z beat +X, oracle +0.58. Does NOT cross 0. All converged.
- **P4 frequency preserved — DONE/GREEN.** `multiref_freq.json`: +0.931 before=after (reference-invariant), coverage 17→23.
- **P5 mechanism — DONE.** `drive_shape_ratio.json`+`fig_mechanism.png`: best corr 0.32, large sensor-spread = confound
  not cleanly broken from this data.
- **P6 identifiability — DONE.** `multiref_identifiability.json`+`fig_identifiability.png`: stiffness floor-limited
  (3→3), amplitude confound broken on drive side (3 separable ratios).
- **P7 damping/Beck levers — DONE (subsumed).** measured-residue R_{d,k} = data-driven φ_d/ζ separation; by-drive ≤0;
  literal damping_inference/modal_beck_ash re-run scoped out (coherence-limited / .ash-driven) — see packet §5.
- **P8 gates/honesty — DONE.** NUTS converged (R̂≤1.003); units-honest gain; three-tier; packet YELLOW scientific verdict.
- **P9 repro/traceability — DONE.** `run_all.sh`, `runtime.json` (active 516 s, footprint 2.8 MB), saved fig .py +
  tufte-lint + `image_qa.json`, locked `check.py`.

WIN CONDITION met: credible auditable BEFORE/AFTER answering the card — outcome (iii) earned + (ii) data-quality.
