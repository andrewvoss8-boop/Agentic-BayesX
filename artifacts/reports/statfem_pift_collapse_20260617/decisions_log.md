# decisions_log.md — Card B: Does our StatFEM exhibit the PIFT posterior collapse, and does orthogonal-Schneider cure it?

Runner: Claude Code (lead-as-runner for Card B). Human: Andrew Voss. Advisor objective: Ilias Bilionis.
Workspace: `artifacts/reports/statfem_pift_collapse_20260617/`.

## Re-grounding (session start 2026-06-17) — one line
- **goal:** test whether our StatFEM/FRF posterior COLLAPSES as observation density N grows (iid/naive: σ_d→0,
  θ tightens, held-out score DEGRADES = confidently-wrong-by-adding-data, the PIFT effect) and whether the
  ORTHOGONAL-SCHNEIDER correlated discrepancy CURES it (finite effective sample size → σ_d & score PLATEAU).
- **last decision:** (session 1) grounded in AGENTS.md (all gates), this card, `notes/memory.md`, the synthetic
  companion `statfem_shocksat_eval_20260616` (arms M0/M1/M2/M3 incl. orthogonal-Schneider already implemented),
  the FEM modal twin `shocksat_fem_modal_twin_20260609`, the statfem runner `shocksat_statfem_runner_20260609`.
- **next action:** SURFACE two human-decision items (analogy mapping + observable resolution) + two blockers
  (missing PIFT/IFT PDFs; missing transfer-path README) to Andrew BEFORE launching the multi-hour N-ladder.
  Then write immutable `check.py` FIRST, then P1 (one low-N + one high-N converged cell: does anything move?).
- **open ambiguities:** (1) PIFT/IFT analogy mapping — DRAFTED in `analogy_mapping_DRAFT.md`, awaiting Andrew
  sign-off (§11 SURFACE item, not self-decided). (2) Observable resolution — proposed synthetic-first then real
  matched-path, awaiting sign-off (§11 SURFACE item). (3) PIFT 2301.07609 + IFT 2306.02150 PDFs absent from
  `references/` — cannot "quote the passage" per §0 until provided/fetched. (4) The card's "transfer-path
  reconciliation README" in `shocksat_statfem_runner_20260609` does not exist as a README file.

## D0 — Plain-ShockSat constraint (Andrew, non-negotiable, card §3)
Use ONLY the plain standalone 9-group ShockSat FEM (reduced 74-mode basis) reused-by-COPY from
`shocksat_fem_modal_twin_20260609` / the companion `statfem_shocksat_eval_20260616/data/`. NO coupled tray, NO
payload coupling. Checker-enforced (no tray-model artifacts referenced).

## D1 — Reuse-by-COPY (anti-cheating, card §0/§9)
COPY (never edit) the companion's `code/core.py` (eigh-resolvent / dynamic-stiffness hysteretic FRF, D10
degeneracy-safe), `code/nuts_arms.py` (M3 orthogonal-Schneider / M2 plain-Schneider / M1 iid / M0 naive),
`code/predict.py`, `code/viz.py`, and the reduced FEM assets in `data/`. The N-ladder driver + the new
immutable `check.py` are written FRESH here. No immutable checker of another study is touched.

## D2 — Collapse mechanism is already LATENT in the reused arm code (key observation, to be PROVEN not assumed)
In `nuts_arms.py`: M0/M1 use a SCALAR residual variance (σ_meas²+σ_d² on all N residuals) → Fisher information
on σ_d (and on identified θ directions) scales ∝ N → posterior collapses as N→∞. M2/M3 whiten against the
eigenvalues Lam of the freq×space correlation matrix C = C_f ⊗ C_z (M3 additionally projects off the θ→FRF
span): the effective number of independent observations ≈ trace-based DOF of the whitened design, capped by the
correlation lengths → saturates under densification. THIS is the candidate cure mechanism. The N-ladder + the
effective-sample-size accounting must DEMONSTRATE this with numbers; do NOT pre-decide the verdict (card §9).

## OPEN — items SURFACED to Andrew 2026-06-17 (NOT self-decided; see surface message + analogy_mapping_DRAFT.md)
- S1 (card §11): PIFT→StatFEM analogy mapping — where it holds / breaks. DRAFT written; awaiting sign-off.
- S2 (card §11): observable resolution — proposed synthetic-first (controlled, isolates the mechanism) then real
  matched-path FRF (drive OWN FEM at the tap node + coherence-weight; NO SOL111 / mismatched path). Awaiting OK.
- B1 (blocker for §0 "quote the passage"): PIFT 2301.07609 & IFT 2306.02150 PDFs absent from references/.
- B2 (minor blocker for the real-data leg only): transfer-path "README" missing; propose using
  `shocksat_statfem_runner_20260609/{quantity_contracts.md,statfem_launch_definition.md,hammer_frf_*.csv,
  channel_map.csv}` as the matched-path source of record instead.
- N1 (inherited): companion's reduced-vs-full FRF discretization gate is a documented YELLOW (~5-8% > 3%, modal
  truncation of the 74-mode basis, fmax 321 Hz ≈ 1.2× band). Internally exact for the synthetic collapse demo;
  will carry the SAME documented YELLOW, will NOT silently relax a checker.

## D3 — Andrew "go" 2026-06-17 (resolves the SURFACE items + blockers)
Andrew: "papers are in references/pdfs. runs/statfem_realdata_20260617/README.md. go."
- S1 (analogy mapping): "go" = sign-off to proceed with the DRAFT mapping → promoted to `analogy_mapping.md`.
- S2 (observable): "go" = synthetic-first then real matched-path FRF (drive OWN FEM at the impact/tap node;
  coherence-weight; SOL111 discarded). Confirmed by the README.
- B1 RESOLVED: `references/pdfs/2301.07609v5.pdf` (PIFT) + `references/pdfs/2306.02150v2.pdf` (IFT) now present;
  verbatim collapse passages extracted + recorded in `references_and_quotes.md` (PIFT p17, p25).
- B2 RESOLVED: matched-path reconciliation README = `runs/statfem_realdata_20260617/README.md` (drive our FEM at
  the actual tap-impact node → matched-path accelerance vs measured H1 [g/lbf]; coherence-weight; hits as
  realizations; SOL111 discarded). The sibling Card A runner owns `statfem_real_validation_20260617/` — HANDS OFF.

## D4 — Integrity model: copied modules BYTE-IDENTICAL; ALL new logic in NEW files (anti-cheat, card §0/§9)
COPIED unedited (SHA-verified MATCH to companion): `code/{core.py,nuts_arms.py,predict.py,viz.py,
identifiability.py,image_qa.py}`; `data/{reduced_blocks,sensor_coords,measured_modes,group_geometry}.npz`,
`groups.json`, `joint_strain_energy_modaltwin.json`. Provenance chain reduced_blocks.npz SHA be9af90e… ==
modal twin `matrices/reduced_blocks.npz` == companion. NEW files only: `check.py` (immutable, written FIRST),
`scoring.py` (sharpness-aware interval-score/CRPS/PIT, re-uses `predict.PredCtx.krige`), `run_ladder.py`
(N-ladder driver, resumable), `ess_accounting.py`, `aggregate_sweep.py`, figure scripts, `run_all.sh`.
The checker SHA-asserts the copied modules are unedited (editing a copied scaffold in place = RED, card §6).

## D5 — Checker design choices for the NEW immutable check.py (transparent; new-study checker needs no human stop)
- Collapse sweep GREEN-required: `out/sweep_synth.json` + `out/sweep_real.json` must contain, per arm per N,
  σ_d 95% width, identified-θ 95% width, and a sharpness-aware held-out score (interval score / CRPS, in dB) +
  coverage + width + PIT. A claim without these numbers = RED (card §6).
- ESS accounting GREEN-required: `out/ess_accounting.json` with N and N_eff per arm (iid: N_eff=N; M3: trace
  participation-ratio of the whitened discrepancy design + N/(points-per-correlation-length)). 
- Verdict GREEN-required: `out/verdict.json` + packet section state collapse-vs-plateau WITH the verified PIFT
  quote + analogy mapping. DIRECTION is the finding (reported either way; a separate finding-gate is GREEN
  regardless of direction, like the companion's finding gate). NOT pre-decided (card §9).
- Synthetic controlled cross-check GREEN-required: `out/sweep_synth.json` present with the known-model-form-error
  truth documented.
- Discretization reduced-vs-full FRF: GREEN ≤3%; YELLOW if >3% with a diagnosis field present AND ≤12% ceiling
  (the inherited 74-mode-truncation YELLOW, internally exact for the synthetic demo); RED if missing or >12%.
- Real-data anti-cheat: `out/config_real.json` must carry `frf_path="matched_impact_node"` and
  `uses_sol111=false`; a SOL111/mismatched-path likelihood = RED (card §6).
- Inherited RED conditions wired: undocumented non-convergence (cell says converged but fails gate); coupled
  tray; edited copied scaffold (SHA); missing/fabricated figure; tufte/image-QA/overlap failure.
- `out/sweep_real.json` is a REQUIRED artifact → checker stays RED ("not done") until P3 lands; honest by design.

## D6 — Synthetic collapse-sweep design (P2; the controlled cross-check)
ONE fixed synthetic truth with a KNOWN model-form error: combo "mixed" (top_box×1.15, joints×1.20, plates×0.88)
+ ONE injected Schneider correlated-complex field (the genuine model-form error NOT representable by any θ).
Sweep N by densifying the frequency grid: N_freq ∈ {20,40,80,160,320} (geometric; 320 = 2× the 160 default =
"beyond the full grid by denser sampling"), observed sensors fixed at 6 (drive fixed). Secondary axis: sensors
∈ {3,6,12,18} at N_freq=160. Arms = M0 naive, M1 iid, M3 orthogonal-Schneider (M2 plain-Schneider optional/
affordable). Per cell: NUTS 4 chains, dense mass, depth-6 (D12), all-var convergence gate, reported per N.
