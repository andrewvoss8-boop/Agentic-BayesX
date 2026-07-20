# Priority Deliverables — ShockSat FRF-Domain Damping Updating (20260710)

Each priority ask (from the runner card §0/§4/§10), its interpretation, and where it is delivered. A priority
with no delivered artifact is a failure; an "assumed" interpretation without confirmation is a warning.

| # | Priority ask (card) | Interpretation | Delivered in |
|---|---|---|---|
| P1 | Answer the ONE falsifiable question (S1 improvement, S2 intelligence, S3 honesty, S4 attribution) with checker output | Grade honestly on dev + vault; a falsification is a valid outcome, loudly labeled | `out/verdicts.json`, `packet.md`, `findings.md`, `checker_report.json` |
| P2 | FRF-domain, FDAC-aware metrics (P1′ FDAC-aligned FRAC, P2′ FRSF, P3 raw corr) | Define + validate before use; quantify the P1′−P3 alignment gain | `quantity_contracts.md`, `code/metrics.py`, `code/gate_F.py`, `out/gate_F.json` |
| P3 | DAMPING action space genuinely implemented + physics-validated (band ζ / Rayleigh / per-joint η) | The new capability; void if not real + gated | `code/femdamp.py`, `code/gate_D1.py`, `out/gate_D1.json` |
| P4 | S4 attribution: is any S1 gain from the DAMPING family, not shape/θ? (damping-only ≥ 2/3 of margin) | Ablation: shape-only vs damping-only vs both vs A0 | `out/ablation.json`, `packet.md` §S4, ablation figure |
| P5 | Gate O sensor observability bound (reachable headroom = data- vs model-limited) | self-MAC + Fisher/EfI at the delivered sensor set; partition A0 residual into observable vs unobservable | `code/gate_O.py`, `out/gate_O.json`, observability figure |
| P6 | Physical-damping honesty gate (ζ∈[0.2%,5%], joint η≤0.2; else DISQUALIFIED as amplitude-fit-in-disguise) | Hard gate on finalists + A0/A0d | `code/verdicts.py`, `out/honesty_*.json` |
| P7 | Three-tier data protocol; dev budget ≤60/track; vault touched once after freeze | LODO dev, query_log budget count, VAULT_FREEZE precedes vault read | `out/query_log.jsonl`, `VAULT_FREEZE.sha256`, `out/vault_scores.json` |
| P8 | Reuse guards: exact-basis decision scores + multi-start MAP | Carried from completed run as non-negotiable | `code/spot_check.py`/`enrich_*` (reused), `out/spot_check_*.json` |
| P9 | NUTS/HMC posteriors for finalists + A0 + A0d (θ + low-dim damping), all-variable diagnostics | numpyro x64, 4 chains, R-hat≤1.05/ESS≥200/div<2% | `code/nuts_finalist.py`, `out/nuts_*.json` |
| P10 | statFEM Q leg (net-CG shear+normal F(k) coverage) for finalists | netcg conventions; coverage ≥0.95 hard gate | `code/qoi.py` (reused), `out/qoi_*.json` |
| P11 | Mechanics + metric gates BEFORE science (V1–V5 reused; D1/D2/F/O new) | Checker-encoded; failures block science | `out/mech_gates.json`, `out/gate_{D1,D2,F,O}.json` |
| P12 | Human-review packet + Tufte figures + continuity rows | Method summary up front; figures lint-clean; one runs.md + one project_log row at END | `packet.md`, `figures/`, `notes/runs.md`, `docs/report/project_log.md` |

**Pre-registered honest expectation (stated up front, per card §0):** the SHAPE family is expected to stay
~null; the DAMPING family MAY move amplitude (FRSF/P2′) but FDAC-aligned FRAC (P1′) gains are UNCERTAIN because
ShockSat's modal domain is already NASA-correlated and the hard-region shapes may be sensor-set-unobservable
(bounded by Gate O). All four outcomes (damping wins / damping sharpens amplitude only / data-limited per Gate O
/ clean null) are publishable. Delivering a replacement twin is NOT this run's job — replace/keep is a human
decision surfaced in the packet.
