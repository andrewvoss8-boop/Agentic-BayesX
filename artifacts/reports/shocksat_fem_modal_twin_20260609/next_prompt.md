# ShockSat FEM Modal Twin — COMPLETE (session 3 wrap-up + recommendations)

Status as of 2026-06-10: all 13 remaining steps from the session-3 handoff are
done. This file is now a completion summary + recommendations for the lead/human,
not a handoff. Full decision trail: `decisions_log.md` D1–D30. Read `packet.md`
first.

## What was delivered
- **packet.md** — method summary at top, run-specific graphical model, lead-as-
  runner label, two-session integrity story, all three designs' honest coverage
  + convergence tables, sensitivity, reduction, FEMAP pointer, runtime, checker note.
- **Inference (NUTS, 4 chains, pinned .venv_nuts):**
  - FULL 18-mode posterior: **converges, gate PASS** (R-hat 1.022, ESS 232, 0 div).
  - BAND (6→12): non-converged even at depth-10/2000+2000 (R-hat 1.076); coverage 10/12.
  - LOMO (17→1 ×18): non-converged (worst R-hat 2.50); coverage 18/18.
- **Headline finding:** the twin is calibratable from the full modal set, but
  identification is **partial (~4/9 groups)** and **fragile under mode removal**;
  the NASA-hand-tuned **joints are not identifiable** from modes ≤222 Hz.
  `sigma_f ≈ 4.6%` ≫ 0.3–0.9% noise floor ⇒ model/element discrepancy. Held-out
  *frequencies* predict well because the predictable QOI is in the identifiable
  subspace. **Cross-confirms** the 2026-06-09 FIM identifiability study (~3
  identifiable stiffness params from modal data).
- 7 figures (legibility-QA'd), FEMAP nominal + posterior decks, sensitivity
  (5 arms), posterior validation (reduced≈full to 0.068%), lock, runtime.json,
  files_changed.md, manifest.json (70 artifacts).
- **Checker: 15/17 PASS.** The 2 FAILs are `convergence_band` + `convergence_lomo`
  — the documented findings, surfaced with worst-case R-hat/ESS, **not faked**.

## Replay
`bash run_all.sh` (steps 1–18; NUTS uses `../../../.venv_nuts/bin/python`),
then `python3 check.py`. Expect the two convergence gates to fail by design.

## DECISIONS FOR THE HUMAN (need your call — I did NOT act on these)
1. **Checker exit code.** `check.py` counts the two documented convergence
   findings toward `all_pass` and `raise SystemExit(1)`, so `run_all.sh` ends
   non-zero. I deliberately did NOT re-tune the gates to fake a pass. Options:
   (a) leave as-is (honest non-zero exit; meaning documented in packet §10);
   (b) split gates into "blocking build/correctness" vs "reported convergence
   findings" so the exit code reflects only blocking gates while the convergence
   values still print as FAIL. Either is honest; (b) makes one-command replay
   exit 0. **Your call — this is a checker-expectation change.**
2. **Proposed AGENTS.md gate (needs your approval before I touch AGENTS.md):**
   "Any compute job expected to exceed the agent tool's command timeout MUST be
   launched detached (`nohup … & disown`) and monitored via until-loops; never
   rely on the foreground tool to keep a long job alive." This session and D20
   both lost jobs to tool-timeout kills; a one-line durable gate would prevent it.

## RECOMMENDED FOLLOW-UPS (science, not blocking)
- **Differentiable subspace-MAC pseudo-likelihood (degenerate-mode fix).** The
  MAC arm diverges (82 div, R-hat 2.97) because the `eigh` backward's
  `1/(λ_i−λ_j)` term blows up at near-degenerate pairs (modes 6 & 7,
  117.63/118.53 Hz). Replace per-eigenvector MAC with an INVARIANT-SUBSPACE
  quantity (subspace-MAC / principal angles / mass-weighted cross-orthogonality)
  that is smooth in θ through degeneracies → lets MAC enter the headline with
  0 divergences. Alts: repeated-eigenvalue sensitivity (Mills-Curran/Dailey/
  Friswell) or Lorentzian-broadened eigh backward. Edit `run_nuts.py`
  model/forward + add a new sensitivity arm. (Prior art is rich; not a patent
  candidate without a real FTO/lit scan.)
- **Identifiability-driven re-parameterization:** merge the 5 unidentified
  groups (welds/contact/joints) into 1–2 lumped scales, or fix them at 1, and
  re-run — the reduced parameterization should converge in ALL designs and give
  tighter held-out intervals. This is the clean way to "fix" band/LOMO
  non-convergence without more data.
- **Pre-test design for joints:** the joints need a higher-frequency or
  joint-localized excitation/sensor set to become identifiable (tie to the FIM
  experiment-design tooling in `artifacts/reports/fim_identifiability_opus_20260609/`).
- **Independent second-solver cross-check (OPTIONAL, deferred D32):** re-solve
  `femap_handoff/*.dat` and compare to `nominal_modes.json` / posterior
  predictions. BLOCKED on the available FEMAP/NX student license (node cap vs
  67,683 grids). Do it via Purdue full NX/FEMAP (no cap, gold standard) or
  MYSTRAN (free, no cap, our deck is self-contained). `compare_femap.py` is to
  be written when the first `femap_*_freqs.csv` arrives. Not required for the
  current honest conclusion (independence rests on NASA-published + element val).
- **Basis enrichment** (`enrich_basis.py`, abandoned on cost D18) if more compute
  is available, to tighten the reduced-model bound away from the posterior point.

## ENVIRONMENT NOTES (carry forward)
- NUTS env = `../../../.venv_nuts/bin/python` ONLY (jax 0.4.30, numpyro 0.15.3).
  Its base interpreter is the system CommandLineTools python3.9, so `ps` shows
  that path even for correct venv jobs — verify via process env (`__PYVENV_LAUNCHER__`,
  jax version), NOT the ps interpreter path (D24).
- Always `OMP_NUM_THREADS=1 VECLIB_MAXIMUM_THREADS=1` for NUTS/eigh (multi-thread
  BLAS on the 74×74 reduced eigh thrashes ~10× slower).
- Full 400k-DOF eigsh ≈ 4–6 min each.
</content>
