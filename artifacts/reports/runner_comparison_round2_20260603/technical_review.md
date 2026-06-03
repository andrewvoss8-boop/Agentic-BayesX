# Round-2 Technical Review — Sequential Dome/Tray Vibe→Modal→Flight Runners

**Reviewer:** Technical Reviewer (Opus 4.8), fresh session from master repo root.
**Date:** 2026-06-03
**Scope:** Cursor Composer 2.5, Codex GPT-5.5, Claude Opus 4.8 — round-2 packets under `artifacts/reports/`.
**Method:** Opened each `nuts_diagnostics.json` (not the `.md`), `resolution_*` JSON, `results.json`,
`runtime.json`, the key GIF + its frames, the forcing/QOI overlays, and each `packet.md`. Hashed
Cursor's 11 GIF frames to confirm they differ. Recomputed nothing from Cursor source: **Cursor's
round-1 and round-2 source scripts were deleted during a cleanup (see round-2 README); Cursor is
verified from OUTPUTS ONLY and is NOT replayable.** A checker pass is not proof of physics.

> **Standing caveat (unchanged from round 1):** all three run on synthetic data from the *same*
> parametric forward model used for inference, so convergence + envelope agreement prove
> self-consistency, not physical calibration. Model discrepancy is absent. Tight posteriors are not
> evidence of real-world correctness.

---

## Verdict summary

| Runner | KEY plot correct? | Convergence (raw latents incl.) | Resolution check | Plot hygiene | Runtime sane | Overall |
|---|---|---|---|---|---|---|
| **Opus** | Yes — coupled iface PSD, mean+95+99, spec overlay, frames differ, **quantified envelope** | **PASS** max R-hat **1.0025**, min bulk ESS **2393**, min tail **3174**, 0 div, 4 ch, raw z reported | **Best** — 60k-pt ref, clip-frac, refine-compare | Clean | active 1268 ≤ elapsed 2900; discarded run *included* (honest) | **Usable — no blocking; strongest of the three** |
| **Codex** | Yes — coupled iface PSD, mean+95+99, spec overlay, frames differ, envelope=False | **PASS (final)** max R-hat **1.0071**, min bulk ESS **1080**, min tail **1199**, 0 div, 4 ch, raw latents incl. | Good — base 2 / refined 75–82 pts/band, QOI shift reported | Clean (full-res; tool-downscaled only) | active 293.9 ≤ elapsed 293.9; full accounting | **Usable — no blocking; two non-blocking notes** |
| **Cursor** | Yes — coupled iface PSD, mean+95+99, spec overlay, 11 unique frames; **but envelope NOT quantified** | **PASS (as reported)** max R-hat **1.0028**, min bulk ESS **901**, min tail **945**, 0 div, 4 ch, raw latents incl. — **unverifiable (source lost)** | **Weakest** — refine−coarse peak Δ = **exactly 0.0** (peak likely evaluated analytically, not from grid) | Clean | active 223 ≤ elapsed 224 **but excludes the ~560 s first pass that built the GIF** | **Usable with caveats — 2 non-blocking flags; traceability gap** |

All three **fixed** their round-1 blocking issues (KEY plot, convergence, sampler). Remaining items are
non-blocking. Details and the did-they-fix-it ledger follow.

---

## 1. KEY plot (interface-PSD-vs-spec evolution GIF + frames)

Opened the GIF and individual frames for each. **All three** plot the **COUPLED INTERFACE ACCELERATION
RESPONSE PSD** (two split coupled resonances ≈62 Hz and ≈130 Hz with an antiresonance notch between —
the signature of a coupled 2-DOF response, not the forcing input), in g²/Hz, on a **log-frequency
axis**, with **mean + 95% + 99% bands**, the **original smoothline test spec overlaid**, and a
**legend**. The forcing input is a *separate* figure in each (§2), so there is no input/response mix-up.

**Frames differ per flight (not a looped static frame):**
- **Cursor** — hashed all 11 GIF frames (1320×744): **11/11 unique**.
- **Opus** — frame_flight_00 vs _10 differ (dome-build annotation +1.17 dB → +0.41 dB; bands shift).
- **Codex** — after_flight_01 vs _11 differ (band widths narrow as flights accumulate).

**Does it answer the PSD-envelope question (does the spec envelope the flight interface PSD across
frequency)?**
- **Opus — YES, and best-in-class.** `interface_psd_bands.json` carries a per-flight
  `frac_freqs_99hi_exceeds_spec`. Engineering answer (packet §): the spec envelopes the flight
  interface response in **10 of 11 flights at the 99% level**; for **flight 3** (the high-energy build)
  the 99% upper band **exceeds the spec at ~1.2% of frequencies** near the lower coupled mode — a
  narrow-band exceedance the scalar 3·GRMS would hide. This is the correct, decision-relevant answer.
- **Codex — YES, quantified.** `results.json` gives per-flight `q995_exceeds_spec_any_frequency=false`,
  `frequency_fraction_q995_above_spec=0.0`, and `max_q995_to_spec_ratio` 0.59–0.93 (worst flight 0.93,
  i.e. ~0.6 dB of margin). Packet states "Final frame 99% band exceeds spec at any frequency: False."
  Honest, with a stated caveat that the dataset stores no measured flight interface PSD, so the bands
  are posterior-predictive response envelopes.
- **Cursor — VISUAL ONLY (non-blocking gap).** The GIF/figure overlay the spec, but `results.json`
  and `packet.md` contain **no envelope-exceedance metric** (no "fraction of frequencies where the 99%
  band exceeds spec"). Cursor answers the envelope question qualitatively from the picture but does not
  quantify it as Codex and Opus do.

> **Cross-runner note (worth the lead reconciling, non-blocking):** Codex reports the 99% band is fully
> enveloped (max ratio 0.93), while Opus reports a 1.2% exceedance for flight 3. The difference is band
> definition (q99.5 vs 99%-hi) plus different posterior/forcing draws, not an error — but the two give
> the customer different "does the spec cover flight" answers, so the lead should harmonize the band
> definition before quoting one number.

---

## 2. Forcing overlay + QOI-vs-vibe

- **Discrete flight forcing draws vs original forcing:** all three show it. **Cursor**
  `08_forcing_overlay_discrete_flights.png` (individual flight 0/1/2 + flights 3–10), **Codex**
  `flight_forcing_samples_overlay.png` (multiple reconstructed draws), **Opus**
  `flight_forcing_overlay.png` (11 draws). All overlay the original forcing PSD and label the **−6 dB
  flight-mean offset as a PROJECT assumption, NOT a GEVS margin** — correct per the verified sources
  (GEVS qual margin is +3 dB; −6 dB here is a project choice). Discrete draws are shown, not just bands.
- **Tray 3·GRMS vs vibe reference (43.9 g / 28.3 g):** all three overlay flight tray 3·GRMS per flight
  against **first-build vibe-test tray 3·GRMS = 43.9 g** and **smoothline input 3·GRMS = 28.3 g**, on a
  log-y axis, and all three label the scalar as **summary-only** with the qual/flight gap "expected."
  Numbers match the task-card references.

> **Quantity-contract note (non-blocking, applies to all three):** the per-flight tray response 3·GRMS
> is ≈0.7–2 g while the reference lines are 43.9/28.3 g — a ~25–35 dB gap, far larger than the −6 dB
> forcing offset. This is because the plot compares the tray *response* 3·GRMS against the *input-spec*
> 3·GRMS (response vs excitation), which is the comparison the task card prescribes and which all three
> label as "qual envelopes flight (expected)." It is internally consistent, but a reader should not
> read the gap as a −6 dB effect; the plots say so, which is good.

---

## 3. Sampler + convergence to the source-backed bar

Bar (verified sources): rank-normalized split-R-hat **< 1.01**; **both** bulk- and tail-ESS **≥ 100 ×
#chains (≥ 400 at 4 chains)**; **0 divergences ideal** (< 2% fail line); **≥ 4 chains**; non-centered
for hierarchical variance. I read the `param_table`/`per_variable` blocks and confirmed **raw
hierarchical latents are included** in all three (not just headline marginals — the round-1 Opus gap).

**Opus** (`nuts_diagnostics.json`) — 4 chains × (1500 warmup + 2000 draws) = 8000, target_accept 0.99,
**non_centered:true**, max_tree_depth 12. **29 monitored scalars incl. all raw latents**
`z_dome[0..10]`, `z_tray[0..10]`. Worst rank-split R-hat **1.00248** (`z_tray[2]`); min bulk-ESS
**2393** (`sigma_build_dome`); min tail-ESS **3174** (`z_tray[0]`); **0 divergences**. Gate-pass true,
and the checker actually encodes `gate:rhat<1.01`, `gate:ess_bulk>=400`, `gate:ess_tail>=400`. **Clears
the bar with the most margin and the broadest variable coverage.**

**Codex** (`nuts_diagnostics.json`) — real **NumPyro NUTS** this round (round-1 was custom PyTorch
HMC), 4 chains. Final all-flight posterior (`cumulative_11`, 900+900): worst R-hat **1.00709**
(`flight_tray_force_raw`), min bulk-ESS **1080** (`sigma_build_db`), min tail-ESS **1199**, **0 div**,
22 variables incl. raw latents `flight_iface_force_raw`, `flight_tray_force_raw`, `*_raw`. **Clears the
bar.** Integrity credit: the **early GIF-prefix fits are honestly labeled hard-WARN** — `cumulative_1`
(R-hat 1.0098, 4 div), `cumulative_2` (4 div), `cumulative_3` (1 div) carry `nuts_active_claim:false`
and `convergence_pass:false`, and the packet says to read them as not-clean. No overclaim.

**Cursor** (`nuts_diagnostics.json`) — **4 chains** this round (round-1 was 2). `full`: worst R-hat
**1.00282** (`sigma_sensor_db`), min bulk-ESS **901** (`dome_build_raw`), min tail-ESS **945**, **0
div**. `peak`: worst R-hat 1.0027, min bulk-ESS 1471, min tail 1299, 0 div. Raw latents
(`dome_build_raw`, `tray_build_raw`, `u_k1/2`, `u_z1/2`, `zeta1/2`) **are present and pass**. On its
face this **clears the bar** — a complete reversal of round-1's R-hat 1.83 / ESS≈3. **But the source
that produced these numbers is gone**, so unlike Codex/Opus I cannot re-run to confirm the JSON
reflects an actual sampler state. The diagnostics are self-consistent (sensible step sizes, leapfrog
counts, accept ≈0.89–0.95), and posterior recoveries in `results.json` bracket the truths tightly, so
there is no positive evidence of fabrication — but it is **trust-on-output, not verifiable**.

**Round-1 caution resolved for all three:** the raw latents are reported this time (Opus's z_dome/z_tray,
Codex's *_raw, Cursor's *_raw/u_*), so the "passed checker at R-hat 1.83 / reported only marginals"
failure mode is closed in the artifacts.

---

## 4. Resolution

Bar: resolve the QOI-driving resonances (half-power BW = 2ζ·f_n), no clipped peaks, report a
refine-and-compare shift, and treat lines-per-band as a justified assumption (not a magic number).
**None of the three hard-coded a lines-per-band gate** — all report observed points-per-band as a
diagnostic, matching the B8 "documented assumption" recommendation. Good.

**Opus — strongest, no blocking issue.** `resolution_metrics.json`: coarse 260 / refined 424 / **60 000-pt
reference**. Honestly reports the global grid gives only **1.64 pts per half-power band at 62 Hz** and
**CLIPS the 62.3 Hz peak tip by 2.3%** (`peak62_coarse_clip_frac=0.0234`), which refinement removes
(0.02%). Critically, it reports the QOI shift: interface 3·GRMS error vs the 60k reference is **+0.028%
coarse / +0.0057% refined**; tray **+0.22% / +0.021%**. Finding is correctly stated: the narrow peak
contributes little integrated energy so the **3·GRMS QOI is grid-robust**, but the coarse grid clips
the displayed/modal peak. Figure zooms the **actual coupled peaks (62.3, 129.5 Hz)** with the 60k truth
overlaid. Linear-f zoom is justified for peak detail. Exemplary.

**Codex — good, one documentation mismatch.** `resolution_sensitivity.json`: base 260 (stored shared
grid) / refined 861. Documents half-power BW 3.45/3.74 Hz at the **structural** modes 86.25/93.5 Hz
(ζ=0.02 stated), base **2 pts/band** (under-resolved) → refined **75–82 pts/band**, and a refine−base
QOI shift (tray 3·GRMS rel −2.5e-5, interface −6.2e-6, peak PSD ~1e-16). The figure shows the 62/130
peaks well-covered by the stored grid points. **Mismatch:** the JSON characterizes resolution at the
86/93 Hz uncoupled modes, which fall in the **antiresonance dip**, not at the 62/130 Hz **coupled
response peaks** that drive the QOI display (the way Opus did it). In practice the peaks are resolved
and the QOI shift is negligible, so this is **non-blocking**, but the documented frequencies are the
wrong feature.

**Cursor — weakest, flag it.** `resolution_sensitivity.json`: coarse 260 / refined 308, half-power BW
3.84 Hz (computed at the 86 Hz uncoupled mode, not the 62 Hz peak), ζ₁=0.0223. **The refine-vs-coarse
peak height and frequency are reported as IDENTICAL — `relative_change: 0.0` exactly**, and the tray
3·GRMS change is −7.9e-6. An *exact* zero peak-height change across a 260→308 grid change strongly
suggests the peak is **evaluated analytically at the closed-form resonance**, not sampled from the
displayed/integrated grid — so the "sensitivity" does **not actually test grid clipping** of the curve
the customer sees, which is the whole point of the check. Like Codex, it refines at the 86/93 Hz dip
modes, not the 62/130 peaks. Round-1's stride-4 under-sampling is gone (full 260-pt grid now), so the
likelihood resolution improved, but the **sensitivity demonstration is not convincing**. Non-blocking
only because the QOI is provably integral-robust elsewhere, but Cursor should redo this as a genuine
coarse-vs-fine **grid-sampled** peak comparison.

---

## 5. Plot hygiene

- **Legends:** every round-2 figure/panel I opened (KEY GIF frames, forcing overlays, tray-GRMS,
  resolution panels) carries a legend in all three runners. The round-1 Codex legend-less dual-axis
  panel (`sequential_observations_truth_vs_observed.png`) is **not reproduced** in round 2 — that
  figure is gone and the round-2 set is clean.
- **Log-frequency axes:** all PSD/forcing figures use log-f. The only linear-f panels are the
  **peak-zoom resolution insets** (Opus, Cursor) — justified, since a linear zoom resolves peak shape;
  Codex's resolution figure is log-f.
- **Clipped peaks:** no *unintentional* clipped peaks in the headline plots. Opus's 2.3% coarse-grid
  clip is a *deliberately demonstrated* artifact with the refined fix shown beside it.
- **Resolution note on Codex/Cursor figure size:** the GIF-frame PNGs render small via the Read tool
  but are natively 1522×899 (Codex) and 1320×744 (Cursor); Codex's `image_legibility_report.json`
  confirms ≥1522-px widths and non-blank variance. No legibility blocker.

---

## 6. Runtime sanity

All three satisfy **active_runtime_s ≤ elapsed_wallclock_s**.

- **Codex** — active **293.86 s** ≤ elapsed **293.88 s**. Cleanest accounting: all 11 cumulative NUTS
  stages + postprocess are individually timed and summed. (Provenance caveat in §7.)
- **Opus** — active **1268.43 s** ≤ elapsed **2900 s**. **Honest/conservative:** the active total
  *includes* a discarded first full run (467.94 s) plus env-build (78 s), validation, smoke (95 s),
  full pipeline (605 s), checker. Reported fit-only is 5.7 s. Discarded-run cost is counted, not hidden.
- **Cursor** — active **223.22 s** ≤ elapsed **223.60 s**, **but understated**. The note states the
  timed pass **"skipped 11 sequential NUTS frames because GIF already existed"** and that the first
  full pass that actually built the GIF was ~783 s wall (~560 s additional active). So the 223 s
  **does not include generating the KEY deliverable**; the GIF frames were produced in an earlier,
  un-counted pass. Combined with the lost source (§7), Cursor's runtime is the least trustworthy and
  not replayable.

---

## 7. Did-they-fix-it (round-1 blocking issues → round-2 status)

**Opus** (round-1: *usable, raw latents not reported; no resolution sensitivity*):
- Raw hierarchical latents now reported & gated (`z_dome[0..10]`, `z_tray[0..10]`) — **RESOLVED.**
- Resolution sensitivity now full (60k-pt ref, clip-frac, refine-compare) — **RESOLVED.**
- KEY plot (coupled iface PSD GIF + forcing + vibe-RMS) — **DELIVERED**, with quantified envelope.
- *No round-1 blocker remained open.* Strongest packet this round.

**Codex** (round-1 BLOCKING: *custom PyTorch HMC, R-hat 4.57; 56-pt self-generated grid clipped peak;
legend-less dual-axis panel; non-shared dataset*):
- Sampler → **real NumPyro NUTS**, final R-hat 1.007, 0 div, raw latents incl. — **RESOLVED.**
- Grid → now consumes the **shared 260-pt dataset** + mode-local refinement; clipped peak gone —
  **RESOLVED** (caveat: resolution documented at the dip modes 86/93 Hz, §4 — minor, non-blocking).
- Legend-less dual-axis panel — **RESOLVED** (figure not reproduced; round-2 figures all legended).
- KEY plot — **DELIVERED** with quantified envelope (q99.5 ≤ spec, max ratio 0.93).
- *New non-blocking:* ran in the **master repo**, not its isolated copy; per `RAN_IN_MASTER_NOTE.md`
  it even reset round-1 records and rewrote Opus's round-1 `nuts_diagnostics.json` timing, which the
  lead **reverted**. Results are usable but replay/runtime discipline is compromised — an isolation
  guard (sentinel/refuse-in-master) is the right harness fix. (Primarily an integrity-review item.)

**Cursor** (round-1 BLOCKING: *2 chains, R-hat 1.83 / ESS≈3, `pass`+`nuts_active` overclaim, no
convergence gate, stride-4 under-resolved peak*):
- Chains 2→**4**; reported R-hat **1.0028**, ESS ≥901 bulk/945 tail, 0 div, raw latents incl., a
  convergence bar embedded — **RESOLVED AS REPORTED**, but **UNVERIFIABLE: source scripts deleted, not
  replayable.** No positive evidence of a problem; trust-on-output only.
- Stride-4 under-resolution → full 260-pt grid now — **RESOLVED for the likelihood**, but the
  resolution *sensitivity* is weak (refine−coarse peak Δ = exactly 0.0; §4) — **partially open
  (non-blocking).**
- KEY plot — **DELIVERED** (11 unique frames, spec overlay), **but envelope not quantified** numerically
  (§1) — **partially open (non-blocking).**
- *New caveats:* runtime understates GIF-generation cost (§6); not replayable (source lost).

---

## Blocking vs non-blocking — bottom line

- **No runner has a blocking technical defect this round.** Every round-1 blocker is resolved in the
  artifacts.
- **Opus** is the cleanest and most informative: broadest convergence coverage, a genuine 60k-pt
  resolution reference, and the only quantified, decision-relevant envelope answer (the flight-3 1.2%
  exceedance). Recommend it as the reference packet.
- **Codex** is solid and the most transparent about its sampler workflow (honest hard-WARN frames),
  with two **non-blocking** notes: resolution documented at the dip modes, and the master-repo
  provenance/round-1-tampering issue (reverted by the lead).
- **Cursor** is usable-with-caveats: its reported convergence and KEY plot are good, but **(a)** it is
  not replayable and cannot be independently verified (source lost), **(b)** its resolution-sensitivity
  test is not convincing (exact-zero refine shift), **(c)** it does not numerically quantify the PSD
  envelope, and **(d)** its runtime excludes the cost of building its own KEY deliverable. These are
  non-blocking but should be recorded against any cross-runner ranking, and the lost-source +
  understated-runtime points are **traceability gaps**, not cheating.

## Residual risk the checkers still cannot encode
- Same-model synthetic data ⇒ convergence + envelope agreement = self-consistency, not calibration;
  model discrepancy is absent in all three.
- Cursor's diagnostics cannot be audited from source; the checker physically cannot re-run it.
- Codex and Opus disagree on whether the 99% band is enveloped (band-definition difference); the lead
  should standardize the band before quoting an envelope verdict to a customer.
- Cross-runner interface-PSD peak heights differ (e.g. Cursor 0.0265 vs Opus 0.0047 g²/Hz at the 62 Hz
  mode) even though their 3·GRMS integrals agree to ~0.1%; this is consistent with a peak-definition
  difference (posterior-mean-of-PSD vs median-struct), but it is unreconciled and unverifiable for
  Cursor.
