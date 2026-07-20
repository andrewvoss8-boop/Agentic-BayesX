# Decisions Log — Resolution-Consistent FRF Scoring (20260713)

- **D0 (2026-07-13, session start).** Goal: run the resolution-consistent scoring card end-to-end (arms B0–B5,
  Gates W/K/R, S1/S2/S3). Last decision: Andrew dispatched ("run it"); lead Fable = autonomous runner
  in-session. Next action: gate files → SHA-locked checker → gates → arms → freeze → vault → packet. Open
  ambiguities: none blocking; D1–D3 below resolve the card's delegated choices. Re-grounded from AGENTS.md,
  the card, the damping run's packet (incl. 2026-07-11 addendum) + quantity_contracts + score/femdamp/femlib
  code, scratch_test07 scripts, and the FOUND distiller (modal_multiref.py → multiref_frf.py → realfrf.py).

- **D1 (window operator form).** The card's scratch prototype used a Hann-kernel convolution (an
  approximation). The ACTUAL recovered processing uses an EXPONENTIAL response window (end=0.05) on a
  122880-sample frame with the impact at pre_gap=200. I implement 𝒲 as the exact closed-form DFT of the
  sampled, exponentially-windowed, frame-truncated modal impulse response (finite geometric sums; math in
  quantity_contracts.md). Rationale: (i) it IS the measurement operator, not a smoothing approximation;
  (ii) it reduces analytically to the naive FRF when window/truncation are removed (one formula, no
  path-mismatch bias between B0/B1 and B2/B3/B4/B5); (iii) exact at the cache's DFT bins; (iv) cheap
  (n_modes×n_bins closed form, no 122k-sample synthesis). Gate K verifies against analytic broadening; Gate W
  verifies the full recovered processing against raw data.

- **D2 (survey ζ → model modes).** Survey gives 33 (f, ζ) pairs; model has ~80 in-band modes. Chosen map:
  linear interpolation in frequency, end-clamped (zero free parameters; treats the survey as sampling a smooth
  ζ(f) trend). Alternative considered: matched-mode assignment via the frozen pairing + band-median for
  unmatched modes — rejected as primary because 27/33-style matching leaves ~50 model modes needing a fallback
  anyway; interp is simpler and uses only measured data. A3 sensitivity check (interp vs nearest) is run on B2
  and reported.

- **D3 (Gate W target: Test01 cache vs Test07 raw).** The stored m_xpos_990x cache was built from SIX
  Test01_ModalHammer hits; our raw zip is Test07_ImpactHammer (same node-990 +X drive family, nearby impact
  point, different hammer/series). Per the card's note: primary comparison = Test07-recomputed H1 vs stored
  cache (threshold 0.05 dex / 80% channels). If that fails on series differences, Gate W may pass LABELED on
  (a) Test07-internal consistency (hit-vs-hit recompute) + (b) the window-physics check (apparent-ζ of clean
  recomputed peaks matches ζ_w(f)+ζ_phys within ±25%), with Test01↔Test07 repeatability quantified and
  reported as a bonus result. No silent target swap: gate_W.json records WHICH comparison passed.

- **D4 (runtime accounting).** Every script appends {step, active_s} to out/runtime_log.jsonl;
  finalize sums → runtime.json {active_runtime_s, elapsed_wallclock_s} with wallclock from
  out/wallclock_start.txt to finalize time. Wall clock includes any idle; active is the comparable number.

- **D5 (score-log discipline).** All arm scores append to out/score_log.jsonl (cid, label, arm, damping spec,
  windowed flag, per-fold P1′/P2′/P3/P4, means, SE). The checker asserts EXACTLY the six pre-registered arm
  labels appear as dev entries (no-search audit) and that VAULT_FREEZE.sha256 predates any vault entry.

- **D9 (Gate W final verdict = FAIL, accepted; NO third re-basing, 2026-07-13).** After D8's force-free
  revision, the pre-registered criteria still fail: hit-consistency 0.090 dex median / frac_ok 0.078 (need
  0.05 dex on ≥80%) — single-hit, force-free repeatability (hits 002-004 are even from the NEXT DAY), a DATA
  property; window-physics median apparent-ζ ratio 1.5–1.9 (need 0.75–1.25) — the ±3-bin SDOF grid-fit breaks
  on non-isolated peaks at 2 Hz bin spacing and ShockSat's modal density (several fits rail or absorb
  neighbors). CRITICAL nuance, all recorded in gate_W.json: (i) TRULY isolated peaks agree with the window
  prediction (163.0 Hz ratio 0.88–0.90, 188.5 Hz 0.84–0.87, 233.1 Hz 1.32 on the stored cache); (ii) no peak
  is systematically NARROWER than predicted (nothing refutes window-broadening); (iii) the operator's
  provenance is exact (distiller source FOUND + hashed; cache metadata matches; the upstream workspace itself
  documents the exp-window added damping in realfrf.measured_zeta_w); (iv) Gate K passed vs analytics;
  (v) Test01↔Test07 shape corr 0.834. Per question_framing's pre-registered interpretation rule this is a
  QUANTITATIVE criterion failure, not an "outright/qualitative" one — but the pre-registered thresholds were
  not met on ANY comparison actually run, so pass_mode = "fail" (checker RED), S3 auto-fails, and the run
  reports OVERALL RED honestly. Inventing a third basis until something passed would be threshold-shopping;
  refused. The differential window-vs-rect idea was tested and found PHYSICALLY UNINFORMATIVE (rect-frame
  truncation broadening ≈ ζ_w at these frequencies) — reported, not used. Consequence for the verdicts:
  S1/S2 numbers are computed and reported with the loud caveat that the mechanism certification rests on
  Gate K + provenance, NOT on the raw-data gate; Andrew decides any follow-up (the clean fix = re-distill
  from records with a LIVE force channel or acquire Test01-class raw data).

- **D8 (Gate W force-free revision — DATA-FORCED, evidence logged, 2026-07-13).** The Test07 force channel
  (Recorder116 'Ch D20', lb) is DEAD in all four hits: its argmax is noise (−1.3 lb at t=0.012 s, rms 0.27 lb)
  while the actual impacts (~218 g accel) occur at ~0.50 s; per-hit force argmax indices 2958/17954/87684 are
  random noise locations (a 218 g response needs hundreds of lbf). Consequences: (i) the card's DIRECT Gate W
  comparison (recompute the stored H1 from Test07) is PHYSICALLY IMPOSSIBLE — H1 needs force; this also
  retro-explains the 2026-06-09 statfem-runner's "Test07 low coherence" finding; the first Gate W run's
  2.15 dex / coh 0.40 garbage is fully explained (accel/noise ratio + frames keyed on noise argmax).
  (ii) The stored caches themselves are Test01/02/03/06/04 MODAL-hammer builds (live force) — unaffected.
  (iii) Gate W's labeled fallback is revised to a FORCE-FREE basis on the same raw records: frame the
  RESPONSE on the accel-detected impact (era_id convention), apply the exact recovered exp window, FFT →
  windowed response spectra; then (a) hit-consistency = per-channel offset-removed median |Δlog10| between
  hit-001 and the other hits' mean, same 0.05 dex / 80% thresholds, offset removal REQUIRED because without
  force normalization absolute level varies with hit strength (documented); channel set = the stored cache's
  coherent rows; (b) window-physics = apparent ζ of clean ERA peaks in the windowed response spectrum within
  ±25% of ζ_ERA + ζ_w(f) (same threshold; estimator moved from the impossible H1 to the response spectrum);
  BONUS = Test01↔Test07 shape-level comparison (corr + offset-removed dex, labeled arbitrary-normalization).
  Thresholds unchanged; only the estimator moved, forced by the data. Gate W can now be at BEST "labeled"
  (YELLOW) — the honest ceiling for this data. Direct-path evidence (dead force) is recorded in gate_W.json.
  A dated addendum noting this revision is appended to quantity_contracts.md (append-only, no rewrite).

- **D7 (disk-full fallback for Gate W, 2026-07-13).** Disk hit 100% (134 MB free) during hit extraction
  (unzip exit 50). Fallback (no human stop-point needed; card autonomy rule): STREAM the raw hits — extract
  one .mat (~245 MB), compute its band-limited spectra (~0.2 MB), DELETE the .mat, proceed to the next;
  per-hit spectra cached individually (data/t07_spec_*.npz) so the gate resumes without re-extraction. The
  partially-extracted hit-002 file was deleted. This also satisfies the card's "clean extracted .mat files at
  the end" by construction (nothing large persists). scratch_test07's hit-001 .mat left untouched (referenced
  by the frozen addendum). Disk pressure flagged for Andrew in the packet.

- **D6 (Gate K semantics under the ACTUAL window — material finding, decided BEFORE running gates).** The
  card's Gate K clause "an already-broad (ζ=5%) peak must be ~unchanged (kernel is narrow relative to it)"
  encoded the scratch prototype's HANN-kernel mental model. The recovered distiller uses an EXPONENTIAL
  response window, whose correct analytic effect is a pole shift ζ→ζ+ζ_w(f) at EVERY peak width — a ζ=5%
  peak at 100 Hz drops ~16% (ζ_app=5.97%), it is NOT unchanged. The pre-registered PURPOSE of Gate K
  (operator must reproduce the analytic apparent-broadening prediction to ≤5%) is unchanged and is applied at
  BOTH ζ=0.3% and ζ=5%: `light_peak_err_frac` and `broad_peak_change_frac` are each (windowed-operator peak
  − analytic ζ+ζ_w(f) peak)/analytic, threshold ≤5% (checker field names locked). The card's original
  "unchanged vs unwindowed" quantity is ALSO computed and REPORTED (expected ≈ −16%, explained), so the
  Hann-vs-exponential correction is loud, not silent. No threshold is relaxed; the analytic target is
  corrected to the actual recovered window. This is a reportable finding about the card's assumption.
