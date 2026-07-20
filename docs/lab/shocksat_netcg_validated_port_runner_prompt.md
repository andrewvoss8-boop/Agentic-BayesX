# Runner card B — VALIDATED NET-CG QOI PORT (post-review item 4: make S3/S4 assessable)

**Paste-and-run: you are an autonomous runner agent. Execute end-to-end without stopping for approval,
EXCEPT the one hard gate in §2 which may end the run early as BLOCKED — that is a valid, reportable outcome.
Never fabricate; never claim beyond your checker's output.**

Date issued: 2026-07-16. Author: lead (Claude/Fable), dispatched by Andrew. Est. compute: ~2–4 h.
Workspace (create): `artifacts/reports/shocksat_netcg_validated_port_20260716/`
READ-ONLY: `shocksat_full_spectrum_frf_20260714/` (study), `shocksat_fullspec_review_gpt56_20260716/`
(review), `shocksat_full_spectrum_frf_repair_20260716/` (repair), `shocksat_netcg_method_selection_20260701/`
(the delivered-twin thread — the machinery you must REUSE, not reimplement), every locked checker, durable
rules.

## 0. Re-ground (mandatory)
Read `AGENTS.md`, `docs/compute_protocol.md`; the study's `findings.md` POST-REVIEW box + `decisions_log.md`
D15–D17; the review's `review.md` C5; the netcg thread's `packet.md`, `quantity_contracts.md`,
`code/netcg_qoi.py`, `code/heldout_drive.py`, `out/stage0_qoi_weights.json`. Write D0 in your
`decisions_log.md`. Verify your tool's compaction behavior; filesystem = source of truth.

## 1. Why this card exists
The full-spectrum study REIMPLEMENTED the net-CG statFEM F(k) band machinery on its wide package and could
not reproduce the delivered twin's calibrated band widths (got ~5.4–8.2× / 1.6–3.7× / 2.0–5.1× vs delivered
**1.51× (shear X) / 2.30× (shear Y) / 2.53× (normal Z)**). The review (C5, accepted) ruled S3/S4
**CANNOT-VERIFY** until the reference reproduces. Your job: make S3/S4 assessable by REUSING the validated
netcg machinery — or prove precisely why it cannot be done and close the question as BLOCKED-with-diagnosis.

## 2. HARD GATE FIRST — reference reproduction (do NOTHING arm-related before this)
Reproduce the delivered twin's band widths **1.51 / 2.30 / 2.53 (±0.05 each)** by driving the ORIGINAL
`netcg_qoi.py` + its reduced model + the L5 θ posterior exactly as the netcg run did (its `run_all.sh` shows
the invocation; reuse read-only, outputs to YOUR workspace). This is the pre-registered Gate N0.
- **PASS →** proceed to §3.
- **FAIL →** diagnose (grid, tier SDs, smoothing, θ posterior, drive convention — diff your invocation
  against the netcg run's logged outputs step by step), write `BLOCKED.md` with the exact divergence point
  and numbers, mark S3/S4 permanently CANNOT-VERIFY-pending-human, and finish with the checker. Do NOT
  "fix" constants until the reference matches — that is calibration-shopping.

## 3. Bridge, then assess (only after N0 passes)
1. **Bridge gate N1:** evaluate the netcg machinery's band for the INHERITED model at the full-spectrum
   study's θ_MAP (its `out/theta_map_wide.json`) instead of the L5 posterior median — quantify how much of
   any width change is the θ point vs the model. Report; no threshold (diagnostic).
2. **Tier update (H4/S4):** apply the pre-registered A5b tier rule from the study's `assumptions_ledger.md`
   (matched extended-band cluster modes: SD_F 0.06→0.01; SD_A = cross-drive amplitude scatter from the
   study's `out/cluster_amp_scatter.json`, floored at 0.35) INSIDE the netcg machinery. Report normal-Z
   width vs 2.53× and coverage vs the netcg plausible-truth ensemble. **S4 rule (pre-registered): ≤1.90×
   AND coverage ≥0.95.**
3. **S3 (shear):** evaluate the repair-corrected finalists (repair `verdicts.json`; enriched packages in the
   study's `data/packages_wide/*__enr.npz` — you will need a documented mapping from the wide package's
   tray/drive rows into the netcg reduced model, OR evaluate via per-mode frequency/amplitude perturbations
   of the netcg model matched to each finalist's paired modes; state your choice and validate it on the
   baseline first: baseline-through-your-mapping must reproduce N0 within ±0.05). Held-out-drive coverage
   via `heldout_drive.py` conventions, DEV DRIVES ONLY. **S3 rule: narrower than 1.51/2.30 while coverage
   ≥0.95.** Overconfidence audit: hide the top-3 measured QOI-driving modes → every band must widen (>1).
4. **VAULT RULE:** the +XY drive is NOT read. Its QOI answer key stays unbuilt. Dev drives only.

## 4. Pre-registration + checker (BEFORE any science)
`priority_deliverables.md`; `question_framing.md` with the pre-registered N0/N1/S3/S4 rules above verbatim;
`quantity_contracts.md` copying the netcg force contract + your finalist-mapping definition. Then `check.py`:
run on empty workspace (RED), SHA-lock, never edit. Checker gates: N0 reproduction (±0.05 each) or
BLOCKED.md present; every statistic finite; baseline-through-mapping validation; no per-mode amplitude LSQ
outside answer-key construction (grep; `CHECKER-OK(non-selection)` annotations); no +XY reads (grep data
paths); figures scripted/linted/QA'd (bands before/after, coverage bars); runtime.json; self-SHA.
`REUSED_code.sha256` for all netcg/study files you import.

## 5. Rules + deliverables
- NO SAMPLER unless you re-drive the existing L5 posterior (reused draws = fine, label as reused; any NEW
  posterior must be NUTS with the full AGENTS convergence gate — not expected in this card).
- Deliverables: `packet.md` (method summary first: exactly what was reused vs mapped vs new), `findings.md`
  (S3/S4 verdicts with numbers, or the BLOCKED diagnosis), `out/verdicts_S3S4.json`, ≥3 figures,
  `decisions_log.md`, `run_all.sh`, checker report. Continuity: `notes/runs.md` + `docs/report/project_log.md`
  row, status copied from YOUR checker.
- Honest failure modes: N0 may fail (BLOCKED is valid); the tier update may NOT narrow normal-Z (if the
  observed cluster amplitude scatter is large, S4 falsifies honestly — that is the pre-registered H4
  falsification path); finalists may widen shear (report; the delivered twin then simply stands).
