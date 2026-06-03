# Reader / Literature Review — Round 2 (2026-06-03)

Role: READER (Opus 4.8). Scope: do the round-2 runners' METHOD CHOICES (qual-vs-flight comparison,
resolution justification) align with the round-1 web-verified sources, and can the still-open
`[TO-VERIFY]` items be closed?

**Browsing status: ENABLED this session via `curl` from Bash** (the WebSearch/WebFetch tools were not
in my toolset, but network egress works; HTTP 200 confirmed on mc-stan.org and standards.nasa.gov).
Every numeric/standards claim below is backed by a source I fetched and parsed THIS session — not from
memory. I did **not** edit any runner code, checker, AGENTS.md, or CLAUDE.md.

Inputs read:
- `artifacts/reports/runner_comparison_20260602/reader_web_verified_sources.md` (round-1 web pass)
- `runner_cursor_composer25_round2_20260602/` (packet, priority_deliverables, assumptions, resolution_sensitivity.json, known_failures)
- `runner_codex_gpt55_round2_20260602/` (packet, priority_deliverables, quantity_contracts, resolution_sensitivity.json, assumptions)
- `runner_claude_opus48_round2_20260602/` (packet, priority_deliverables, quantity_contracts_round2, resolution_analysis.md, assumptions)

---

## Bottom line

| Check | Cursor | Codex | Opus |
|---|---|---|---|
| Qual-vs-flight framed as PSD-envelope (Task 1) | ✅ aligned | ✅ aligned (quantified) | ✅ aligned (best articulated) |
| Scalar 3·GRMS used as summary only, not sole acceptance | ✅ | ✅ | ✅ |
| −6 dB labeled PROJECT assumption, NOT GEVS margin / NOT +6 dB/oct slope | ✅ | ✅ | ✅ (both traps named) |
| Resolution uses half-power BW Δf = 2ζf_n (Task 2) | ✅ | ✅ | ✅ |
| Honest sensitivity check, no invented standardized line-count | ✅ | ✅ (reports raw count, not as a standard) | ✅ (explicitly refuses to invent one) |
| Resolution refinement centered on the COUPLED interface peak that drives the headline figure | ⚠️ refines standalone modes (86/93.5 Hz), not coupled 62.3/129.5 Hz | ⚠️ same gap | ✅ identifies & refines 62.3/129.5 Hz |

No runner commits the failure modes the task card warned about (scalar-as-sole-acceptance, or −6 dB
presented as a GEVS qualification margin). The one shared method weakness is a resolution-targeting
nuance (last row), described below — a technical-review follow-up, not a source-alignment violation.

---

## Task 1 — qual-vs-flight = PSD-envelope check, scalar as summary

**Verified frame (round-1, re-confirmed against the CURRENT GEVS rev below):** the defensible
acceptance check is a PSD/ASD **envelope** comparison across frequency (the spec must envelope the
flight environment); the scalar overall GRMS is a *summary only* because a single number can hide a
narrow-band exceedance. The setup's −6 dB flight-forcing offset is a project assumption; the GEVS
qualification-vs-acceptance margin is **+3 dB**.

**Cursor — aligned.**
- [packet.md](../runner_cursor_composer25_round2_20260602/packet.md): quantity contract states the
  interface response PSD is "compared to smoothline vibe qualification spec as envelope reference."
- [priority_deliverables.md](../runner_cursor_composer25_round2_20260602/priority_deliverables.md):
  "PSD envelope check remains primary"; tray 3·GRMS is the scalar (P3), the GIF/final PSD-vs-spec is
  the KEY deliverable (P1).
- [known_failures.md](../runner_cursor_composer25_round2_20260602/known_failures.md): "6 dB flight
  forcing offset is a project assumption, not a GEVS qualification margin." ✔ no margin conflation.

**Codex — aligned, and quantified the envelope test.**
- [packet.md](../runner_codex_gpt55_round2_20260602/packet.md): "The primary metric is frequencywise
  PSD envelope comparison, especially the 99% band. The tray 3*GRMS overlay is only a scalar summary."
- Gives an actual envelope metric: final-frame 99% band exceeds spec = `False`; max 99%/spec ratio
  `0.5929` at 62.41 Hz; fraction of frequencies above spec `0.0000`. This is exactly the
  frequency-wise check the source requires, not a scalar pass/fail.
- [assumptions_ledger](../runner_codex_gpt55_round2_20260602/assumptions_ledger.md): "−6.0 dB … not a
  GEVS margin." ✔
- Honest caveat I endorse: the dataset has **no stored flight interface PSD**, so the bands are
  *posterior-predictive response envelopes*, not measured-flight PSD posteriors. Codex states this
  plainly; the engineering question is still answerable, but reviewers should not read the bands as
  data-conditioned flight PSD.

**Opus — aligned, best articulated.**
- [packet.md](../runner_claude_opus48_round2_20260602/packet.md): the envelope is the headline (P1);
  finds the spec envelopes the flight interface response in 10/11 flights at 99%, but for flight 3 the
  99% band **exceeds spec at ~1.2% of frequencies** near the lower coupled mode — "a narrow-band
  exceedance that the scalar 3·GRMS summary would hide." This is the textbook justification for *why*
  the envelope (not the scalar) is the acceptance check; Opus demonstrates the failure mode rather than
  just asserting it.
- [quantity_contracts_round2.md](../runner_claude_opus48_round2_20260602/quantity_contracts_round2.md):
  margin note names BOTH round-1 traps — the −6 dB offset is "NOT the GEVS qualification margin (+3 dB),
  and NOT a GEVS '+6 dB/oct' spectral slope." ✔

---

## Task 2 — resolution justified by half-power bandwidth + honest sensitivity

**Verified definition:** half-power (−3 dB) bandwidth Δf = f_n/Q = 2ζ·f_n. The "lines per half-power
band" number is NOT a standardized value; keep it a documented assumption + sensitivity check.

All three use Δf = 2ζ·f_n correctly and run a base-vs-refined sensitivity check; none hard-codes an
invented standardized line count.

- **Cursor** — [resolution_sensitivity.json](../runner_cursor_composer25_round2_20260602/resolution_sensitivity.json):
  `half_power_bandwidth_hz_assumed = 3.84`, rationale "half-power Df=2*zeta*f_n"; refined 260→308
  points; tray 3·GRMS relative change ≈ −8e-6. Sensitivity is honest. **No invented line-count.**
- **Codex** — [resolution_sensitivity.json](../runner_codex_gpt55_round2_20260602/resolution_sensitivity.json):
  `half_power_bandwidth_hz_assuming_zeta_0p02 = 3.45/3.74`, reports `base_points_in_half_power_band = 2`
  vs `refined = 75/82`. It *reports* the line count descriptively (not as a standard threshold) and
  ties the conclusion to a sub-percent QOI shift (−0.0006%). This is the right use of the number.
- **Opus** — [resolution_analysis.md](../runner_claude_opus48_round2_20260602/resolution_analysis.md):
  uses Δf = 2ζ·f_n (verified vs Irvine), explicitly states "No source-backed fixed 'lines per band'
  number is invented; density is a documented assumption and resolution is PROVEN by the sensitivity
  check"; reports ~1.7 points in the 62.3 Hz half-power band on the global grid (2.3% peak clip) →
  refined to ≈0; integrated 3·GRMS robust to sub-percent vs a 60k-point reference. Strongest treatment.

**⚠️ Shared method nuance (flag for the technical reviewer, not a source violation):** Opus identifies
that the **coupled** interface-response peaks sit at **62.3 / 129.5 Hz**, distinct from the standalone
tray (86.25 Hz) and dome (93.5 Hz) modes. Cursor's and Codex's resolution refinement is centered on the
standalone 86/93.5 Hz modes, yet both evaluate a headline interface peak near ~62 Hz (Cursor
`interface_psd_peak_freq_hz = 62.4`; Codex max-ratio at 62.41 Hz). For Cursor the refined-vs-coarse
peak `relative_change` is exactly `0.0`, which suggests its refinement may not have added density at the
62 Hz coupled peak that actually drives the headline envelope figure — so its "robust" result is weaker
evidence than Codex/Opus there. The integrated 3·GRMS is still grid-insensitive for all three (the
narrow 62 Hz peak carries little total energy), so the decision QOI conclusion holds; but the
*peak-resolution* claim for the interface PSD figure is best supported only by Opus. Recommend Cursor
and Codex confirm half-power resolution at the coupled 62.3/129.5 Hz peaks, not only at 86/93.5 Hz.

---

## Task 3 — newly verified citations (closing the open `[TO-VERIFY]` items)

### (c) GEVS revision currency — RESOLVED. Current revision = GSFC-STD-7000**B** (2021), and the
numbers the harness uses are unchanged from the 2005 base.

Source: **GSFC-STD-7000B**, General Environmental Verification Standard (GEVS),
`https://standards.nasa.gov/system/files/tmp/GSFC-STD-7000B_Approved_Admn%20Ext.pdf`
(landing page `https://standards.nasa.gov/standard/gsfc/gsfc-std-7000`).
HTTP 200; 10,953,002 bytes; sha256[:16] `3e4bf794cdba48b0`; 337 pages.
Cover: **Approved 04-28-2021, Revalidation 04-28-2027, Superseding GSFC-STD-7000A.** Document History
Log: Baseline **April 2005**, Rev A **4/22/2013**, Rev B **2021**.

Confirmed in rev B (page numbers from the fetched PDF):
- **PSD-envelope is the check (p43):** qualification by similarity requires "the previous qualification
  program has adequately enveloped the new mission environments." → C9 holds in rev B.
- **Limit Level def (p24):** "The maximum expected flight level (consistent with the minimum
  probability levels of Table 2.4-2)." (= MPE.)
- **+3 dB qual margin — two places (stronger than the 2005 base quote):**
  - p45 verification-level table (Random Vibration / Acoustics, Qualification & Protoflight):
    **"Limit Level + 3dB"**.
  - p317: "The qualification (prototype or protoflight) test level is **generally 3 dB greater** than
    the maximum expected (acceptance) test level. That is not always the case however. If the expected
    level is less than the workmanship level an envelope of the two is used…" → C10 (+3 dB, with
    workmanship-floor exception) holds verbatim in rev B.
- **+6 dB / −6 dB are SLOPES, not margins (p69–70):** the generalized random-vibration tables list
  "+6 dB/oct" and "−6 dB/oct" ASD ramp slopes; p70 also has a separate **6 dB ASD reduction for heavier
  components** (mass-attenuation knock-down), again not a margin uplift. The round-1 "+6 dB is a slope,
  not a margin" trap is confirmed in the current revision.

**Implication:** any harness/task-card number sourced from the 2005 base (envelope check, +3 dB qual
margin, Limit Level = MPE) is still current under GSFC-STD-7000B. No update needed; just cite rev B.

### (b) Does any controlled standard define a +6 dB margin? — RESOLVED (with scope caveat).

Yes — but **not** for random-vibration qualification. GEVS rev B p143 cites
**MIL-STD-464C, section 5.1 "Margins"**: "safety critical and mission critical system functions shall
have a margin of **at least 6 dB**," verified by test/analysis. **Scope = electromagnetic environmental
effects (E3) for safety/mission-critical functions**, not structural/random-vibration qualification.
So the round-1 conclusion stands and is now sharpened: a +6 dB margin is a real controlled requirement,
but in the EMI/E3 domain — it must not be imported as a vibration qualification or forcing-uncertainty
margin, and it is unrelated to the project's −6 dB forcing offset.

### (a) Spectral lines per half-power band — STILL `[TO-VERIFY]` for the exact number; mechanism source added.

I could not retrieve a primary standard/text stating an exact "N lines per half-power band" number.
What I did confirm this session, as the underlying *mechanism*:
- **B&K BR0458, "Structural Testing Part 1, Mechanical Mobility Measurements"**
  `https://www.bksv.com/media/doc/br0458.pdf` — HTTP 200; 1,248,051 bytes; sha256[:16]
  `8af229fd1daa3c59`; 49 pages. States that "a **bias error** can occur when the response has very
  narrow resonances, compared to the frequency resolution being used … Narrow resonances ring for a
  long time," and that leakage makes "measured peaks … too broad and too low … the result of working
  with too little frequency resolution." This is the documented basis for refining the grid at lightly
  damped resonances — but it gives no specific line count.
- **B&K BR0507, "Structural Testing Part 2, Modal Analysis and Simulation"**
  `https://www.bksv.com/media/doc/br0507.pdf` — HTTP 200; 1,322,910 bytes; 56 pages. Searched; **no**
  "lines per half-power band" rule found.

The widely-quoted "≥5–10 lines across the half-power band" rule lives in modal-testing texts
(e.g. Ewins, *Modal Testing: Theory, Practice and Application*) and vendor app notes I could not
retrieve as static primary text this session. **Recommendation unchanged from round 1:** keep it a
documented assumption + sensitivity check, never a hard-coded harness density. All three runners did
exactly this, so no runner is misaligned on this point.

---

## Source register (fetched this session)

| key | URL | HTTP | bytes | sha256[:16] |
|---|---|---|---:|---|
| GSFC-7000 landing | https://standards.nasa.gov/standard/gsfc/gsfc-std-7000 | 200 | 25,154 | d3f0e5bce64b03e4 |
| GSFC-STD-7000B (PDF) | https://standards.nasa.gov/system/files/tmp/GSFC-STD-7000B_Approved_Admn%20Ext.pdf | 200 | 10,953,002 | 3e4bf794cdba48b0 |
| B&K BR0458 (Mech. Mobility) | https://www.bksv.com/media/doc/br0458.pdf | 200 | 1,248,051 | 8af229fd1daa3c59 |
| B&K BR0507 (Modal Analysis) | https://www.bksv.com/media/doc/br0507.pdf | 200 | 1,322,910 | (not line-count source) |

(Round-1 sources — Stan manual, Vehtari 2021, Irvine PSD/random/half-power PDFs, GSFC-STD-7000 2005
base — remain as recorded in `runner_comparison_20260602/reader_web_verified_sources.md`; I did not
re-fetch them this session.)

---

## Remaining `[TO-VERIFY]` / open items

1. **Exact spectral-lines-per-half-power-band number** — still not pinned to a retrievable primary
   standard. Mechanism is sourced (B&K BR0458). Keep as documented assumption + sensitivity check.
   (No runner misaligned.)
2. **Coupled-peak resolution for Cursor & Codex** — their refinement centers on the standalone
   86/93.5 Hz modes; the headline interface-response peak is ~62 Hz. Technical reviewer should confirm
   the half-power band at the coupled 62.3/129.5 Hz peaks is actually resolved (Opus does this; Cursor's
   `relative_change = 0.0` hints its refinement missed the 62 Hz peak). Decision QOI (3·GRMS) is
   grid-robust for all three regardless.
3. **Replay/traceability (carry-over, not a reader item):** per the round-2 README, Cursor's source
   scripts were deleted, so Cursor is not replayable; Codex ran in the master repo, not an isolated
   copy. Flagged for the checker/integrity reviewers.

## What I did NOT do
- Did not edit any runner code, checker, AGENTS.md, CLAUDE.md, or the runners' reports. This file is the
  only artifact I wrote.
