# Priority deliverables — Bilionis review packet (2026-06-26)

Each row restates one of Andrew's priority asks (from the consolidation prompt), the
interpretation used, and where it is delivered. A priority with no delivered artifact is a
failure; an "assumed" interpretation is a warning to confirm at the review.

| # | Priority ask (Andrew's words, paraphrased) | Interpretation used | Delivered in | Status |
|---|---|---|---|---|
| P1 | "Take stock... thorough PowerPoint packet for a review with Bilionis going over everything." | One self-contained consolidation deck, no new science, every number traced. | `slides/shocksat_bilionis_review.pptx` (31 slides) + `packet.md` | DONE |
| P2 | "Inherited a calibrated model (MAC/freq) but found large model-form error in the FRF regime." | Show the modes are correlated (MAC 0.63, freq ~3%) yet FRF corr only ~0.27. | Deck slide 6; `packet.md §2`; src `correlate_all.json` | DONE |
| P3 | "Mean functions only moved minorly from the original FEM — quantify by how much, and was it useful for industry." | Forest plot of θ posterior movement; freq/amp value vs a no-skill baseline. | Deck slides 9–10 (`fig_theta_movement`, value); `packet.md §3` | DONE |
| P4 | "Confidence intervals were perpetually too wide to be aerospace-usable — an important finding." | The central honest finding, with the dB / GRMS numbers. | Deck slides 11–12 (`fig_wide_ci`); `packet.md §4` | DONE |
| P5 | "It always came back to mode shapes — a major hurdle." | 54 Hz shape MAC 0.17; shape-oracle σ lever; shapes don't transfer. | Deck slide 13 (`fig_residual_map`); `packet.md §5` | DONE |
| P6 | "Was agentic remeshing + Bayesian updating ever done, and how successful?" | Yes; ~30 edits + Bayesian on the best model; the plateau + the auditable boundary. | Deck slides 14–15 (`fig_remesh_plateau`); `packet.md §6` | DONE |
| P7 | "Evaluate a NEW metric based off the mean function — correlation of our mean with the FRF in the data vs the original FEM." | Per-channel log\|H\| correlation, updated vs original (0.269→0.338, 70% better). | Deck slides 7–8 (`fig_new_metric`, `fig_frf_grid`); `packet.md §3`; src `frf_comparison.json` | DONE |
| P8 | "Bilionis/Alberts/Kairui concern: physics in the likelihood is inconsistent for ODE/PDE (the number of physics 'samples' is an arbitrary parameter). Map inconsistent → StatFEM → IFT." | A 3-construction map table + the consistency toy that locates the drift to the arbitrary σ_r knob. | Deck slides 17–19 (map table, `consistency_money`); `packet.md §7`; src `sweep_summary.json` | DONE |
| P9 | "Show side-by-sides of how our method performed against IFT with actual numerical benchmarks." | IFT vs StatFEM-in-likelihood (M2) vs modal twin (L5) on identical real data. | Deck slides 20–21 (`ift_scorecard`, `ift_beta`); `packet.md §8`; src `scorecard.json` | DONE |
| P10 | "Document the many StatFEM formulations with figures and numerical success evaluation." | ≥10 likelihood/observable formulations + the discrepancy-form arms. | Deck slide 16 (`likelihood_inventory`); `packet.md §9` | DONE |
| P11 | "We also investigated a few recent related papers." | Triage of the pulled papers + the reproduced virtual-sensing result. | Deck slide 23; `packet.md §10` | DONE |
| P12 | "We also tried evidence-based model selection." | Occam-penalized model-class ranking on modal frequencies. | Deck slide 22; `packet.md §11`; src `stage1_evidence.json` | DONE |
| P13 | "What is the most potent, publishable finding(s)?" | Three ranked findings + paper angles, honest about defensible-vs-novel. | Deck slides 5, 25; `publishable_findings.md` | DONE |
| P14 | "Finalize the next direction for the project." | Three scoped options (A/B/C) + an explicit not-recommended list + the decision to make. | Deck slide 26; `packet.md §13` | DONE (decision pending at review) |

## Assumptions flagged for confirmation at the review
- "Usable" FRF-band target taken as ≈ +3 dB and "usable" mean-correlation as ≈ 0.7 — illustrative
  reference lines, NOT a customer spec (confirm the real certification target with Andrew).
- The new-metric "updated" arm = measured modal frequency + damping calibration with deterministic
  modal participations and ONE global gain (apples-to-apples mean). This is NOT the full posterior twin;
  the wide-CI slides carry that.
- Most of the new-metric / remeshing / wide-CI work is EXPLORATORY (figures + numbers, no immutable
  checker). The IFT / consistency / model-class / Card-D / papers threads ARE checker-backed (YELLOW/GREEN).
