# Phase P1 interim summary — observable resolution + matched-path sanity (Card A)

One-screen reviewable summary. Status tier per gate in brackets. Full detail: `decisions_log.md` D1–D4.

## What P1 set out to do
Resolve the held-out observable for validating the orthogonal-Schneider StatFEM twin on the REAL ShockSat,
and verify the FEM matched-path FRF is sane before any calibration (task §2(d), GREEN-required).

## Findings (all artifact-backed; reproducible)
1. **The prior "hammer FRF not-likelihood-ready, coherence ≈0.06" was a PROCESSING ARTIFACT [GREEN finding].**
   The prior runner used scipy Welch (nperseg=32768) over a single ~1 s impact transient with one force spike →
   most segments have force≈0 → coherence collapses (Discretization-Gate pitfall). A proper single-impact FRF
   (force window on the pulse + exponential response window, single FFT) recovers real resonances aligned with
   the 33 `.ash` measured modes to **median ~1.5–2.4 Hz** (ch1 71/116/168 ↔ 70.0/117.6/168.0, etc.).
   Artifact: `code/probe_observable.py` → `out/observable_investigation.json`.
2. **Data-availability limits [documented YELLOW].** Only **1 of 4** hammer hits is present as raw `.mat`;
   **3 of 326** channels were precomputed (raw hit-001 has **128** recorders → ~127 channels reprocessable, all
   at ONE impact location). → the §7 Monte-Carlo randomizes the **observed/held-out split** only; impact-location
   and hit axes collapse to one each (labeled reduction).
3. **Observable DECISION (Andrew):** option (b) — **all real FRF, single impact location** (no modal fallback).
   Logged as D2.
4. **Matched-path sanity gate [GREEN = PASS].** FEM accelerance (drive at the impact node (9,8,1)→nearest kept
   FEM node, response at the tap-channel nodes, reduced rows via the verified V_keep→reduced transform T) in
   g/lbf vs the measured single-impact FRF:
   - FEM first mode 54.6 Hz ≈ measured 54.2 Hz; genuine FEM-vs-real peak misalignment elsewhere = the real
     model-form error to calibrate.
   - Absolute amplitude offset = a **global ×100 units-gain**, stable across all 3 channels and across
     ζ∈{0.003,0.01,0.02} → a mode-shape mass-normalization/`g` constant (frequencies exact, reduced-vs-full
     eigval err 1e-10). Resolved with ONE global units-gain nuisance. Residual scatter (smoothed log-ratio std
     ≈0.5–0.8) = the true amplitude discrepancy the orthogonal-Schneider arm must cover.
   Artifact: `code/probe_matched_path.py` → `out/matched_path_sanity.json`.

## Locked-in decisions carried into P2–P5
- Truth = single-impact measured |H1| [g/lbf] (force/exp window, N=131072, Δf≈1.9 Hz), band 45–260 Hz.
- Model = FEM matched-path accelerance g/lbf + 1 global units-gain nuisance; constant-η damping, ζ_nom=0.01,
  sweep {0.003,0.01,0.02}.
- Likelihood = whole log|H| over observed channels, single-hit SNR/quality-weighted + band-restricted (the
  1-hit "coherence" substitute; YELLOW caveat).
- θ recovery has no real-data ground truth → parameter-count study scored on held-out QOI + FIM identifiability.

## Open items / caveats (for the packet)
- Exact origin of the ×100 gain (mass-normalization unit) is documented but not fully traced; it does not affect
  frequency/model-form conclusions and is identified by observed channels.
- Tap response channels map to the nearest kept FEM node (≤0.42 in) = an observation-operator approximation.
- Single hit → no multi-average coherence; the SNR weight is a labeled substitute (YELLOW).

## Next (P2)
Write the immutable `check.py` FIRST; build the real-data forward + the 4 arms (M0 naive contrast, M3
orthogonal-Schneider = method under validation; M1/M2 secondary); run one converged sanity NUTS cell; then the
sharpness suite on one split.
