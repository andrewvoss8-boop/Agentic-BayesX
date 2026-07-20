# Priority deliverables — ShockSat FULL-SPECTRUM FRF study (20260714)

Card: pasted runner card, dispatched by Andrew 2026-07-14 (lead-authored). Each priority ask, my
interpretation, and where it will be delivered. Written BEFORE any science (§3 order).

| # | Priority ask (card) | Interpretation (mine, plain English) | Delivered at |
|---|---|---|---|
| P1 | Wide-band re-distillation from raw (§4) | Rebuild all 5 drives' FRF caches 45 Hz → certified ceiling (target ≥1000 Hz), same 2.03 Hz spacing/window as the existing caches, validated against existing caches on the 46.8–258.4 Hz overlap (corr ≥0.999, med |Δlog10H| ≤0.01), one zip at a time, force-health-checked per hit | `data/multiref_wide/*.npz`, `data/source_register.md`, `data/force_health.json`, `out/overlap_validation.json` |
| P2 | The arms × bands table (§7, "the study's centerpiece") | For every arm A0,A1,B,C,D,E,F: fold-averaged held-out per-channel log\|H\| correlation ± fold SE, in sub-200 / 200–500 / 500–ceiling Hz bands | `packet.md` §results, `out/arms_bands_table.json`, per-band table figure |
| P3 | Amplitude-TRAINED updating (arm B, first ever) | NUTS posterior over 9 group-stiffness θ with likelihood on TRAIN-drive log\|H\| (whole band, one global gain per drive, statFEM-style correlated error term) + θ-only overconfidence control | `code/arm_b_*.py`, `out/arm_B*.json`, posterior figures |
| P4 | Amplitude-trained shape inference (arm C) | Beck-style shape perturbations trained on amplitudes + survey shapes; report per-point gains AND net-CG coverage split honestly | `out/arm_C*.json`, findings H1 verdict |
| P5 | Remodeling loop with amplitude compass (arm D) + equal-budget random control | ≥3 rounds, ≤80 agent dev queries, ≥40 full eigensolves, diagnosis→proposal links, seeded random control at same budget | `out/query_log.jsonl`, round summaries, trajectory figure |
| P6 | Selection-score re-test (arm E) | Amplitude-inclusive Bayesian model-class selection on ~10 D-candidates + A1 + rand10; Spearman vs held-out ranking + scatter figure | `out/arm_E*.json`, scatter figure |
| P7 | Net-CG QOI results (§7) | Shear X/Y band width vs 1.51×/2.30× with held-out-drive coverage (hard gate ≥0.95); normal band with extended-band cluster tiers vs 2.53× ; overconfidence audit (hide top-3 modes, band must widen) | `out/netcg_*.json`, bands before/after figure |
| P8 | QOI-weighted sensor score | Correlation weighted by net-CG shear participation per sensor; per-sensor deltas for 10 highest-weight sensors | `out/qoi_weighted_scores.json`, per-sensor figure |
| P9 | Per-H verdicts (H1–H5) + S1–S5 with statuses copied from the checker | Explicit, numbered, GREEN/YELLOW/RED per Result Status Standard; falsification is a valid outcome | `findings.md`, `out/verdicts.json` |
| P10 | Continuity + integrity | Pinned bars A0=0.1969±0.002 (HARD), A1=0.2371±0.005; SHA-locked checker before science; vault frozen, read once; query budgets; leakage grep; runtime.json; run_all.sh replay | `CHECKER.sha256`, `VAULT_FREEZE.sha256`, `checker_report.json`, `run_all.sh`, `runtime.json` |

Acceptance criteria: the pre-registered S1–S5 in `question_framing.md` (verbatim from the card §7).

Ambiguity flags (assumption stated, not blocking; card says do not stop for approval):
- **"P1-class metric" for the per-band table:** the card says "per-channel log|H| correlation". The A0/A1
  continuity bars are P1′ (FDAC-aligned FRAC) numbers from the resolution run, so the primary metric stays
  P1′ for continuity; the per-band splits are computed with the SAME P1′ machinery restricted to each band,
  and raw log|H| correlation (P3) is reported alongside. If the alignment ridge is unstable in a sparse band,
  that band falls back to P3 and is labeled.
- **"500 Hz–ceiling" band:** reported only where the drive's certified ceiling exceeds 500 Hz; otherwise the
  cell is marked `not certified` rather than filled with uncertified data.
- Free disk is ~24 GiB (card estimated ~2.9 GB); the one-zip-at-a-time protocol is kept anyway (D0).
