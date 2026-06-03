# Sources — Framing Challenge (2026-06-03)

Browsing ENABLED. Every external numeric/factual claim in `framing_challenge.md` is backed by a source
fetched and parsed THIS session (no citing from memory), or by the already-verified repo file
`runner_comparison_20260602/reader_web_verified_sources.md`. Raw files live in `/tmp` (not committed).

## Fetched this session
| tag | source | URL | HTTP | bytes | sha256[:16] |
|---|---|---|---|---|---|
| `[YUNIS]` | Isam Yunis, *The Standard Deviation of Launch Vehicle Environments*, NASA KSC, NTRS 20120001364 | https://ntrs.nasa.gov/api/citations/20120001364/downloads/20120001364.pdf | 200 | 1586133 | 7cf1613e729325c0 |
| `[HDBK7004]` | NASA-HDBK-7004B, *Force Limited Vibration Testing* (vibrationdata mirror) | http://vibrationdata.com/tutorials/NASA-HDBK-7004B.pdf | 200 | 900975 | a4d04f5a07a2bbbd |
| `[IRVINE]` | T. Irvine, *Random Vibration* tutorial (vibrationdata) | https://www.vibrationdata.com/tutorials2/random.pdf | 200 | 298493 | 658ff59eefceee9d |

`[IRVINE]` hash (658ff59eefceee9d) matches the IRVINE-RAND entry in the repo's prior
`reader_web_verified_sources.md` — same file, independent re-fetch, cross-checked.

## Key verbatim quotes captured this session
- `[YUNIS]` (abstract): *"The results suggest that 3dB is a conservative and reasonable standard
  deviation for the source environment and the payload environment."*
- `[YUNIS]` (MPE defs): *"A standard environmental specification is P95/50, which is the level we expect
  to be greater than 95% of the data with 50% confidence. This is referred to as the Maximum Expected
  Environment (MPE)... Another standard environment is P99/90... the Extreme Expected Environment."*
- `[YUNIS]` (sparse data): *"often very little data exists to define the standard deviation and it is
  better to use a typical standard deviation than one derived from a few measurements"*; sample size
  *"is small (typically <5)."* (Small-sample k-factor / normal tolerance limit, Eq. 5.)
- `[HDBK7004]` (overtest cause): *"the major cause of over testing in aerospace vibration tests is
  associated with the infinite mechanical impedance of the shaker and the standard practice of
  controlling the input acceleration to the frequency envelope of the flight data. This approach results
  in artificially high shaker forces and responses at the resonance frequencies of the test item."*
- `[HDBK7004]` (notching): controllers *"limit the measured forces and thereby notch the input
  acceleration in real time."*
- `[HDBK7004]` (overtest penalty): traditional acceleration-controlled tests *"may cause failures that
  would not occur in flight"*; goal is a *"realistic (flight-like) test with a specified positive
  margin."*

## Reused from repo (already web-verified on 2026-06-02, hashes in that file)
| tag | source | repo file |
|---|---|---|
| `[GEVS]` | GSFC-STD-7000 (GEVS): spec must envelope flight env; Limit Level = MPE; qual margin = **+3 dB** (the +6 dB in tables are spectral slopes, NOT a margin); scalar GRMS = summary | `artifacts/reports/runner_comparison_20260602/reader_web_verified_sources.md` §C9–C10 (GEVS sha256[:16] 6e56386c9dcd1443) |
| StatFEM | Girolami et al., statistical FEM = FE + GP **discrepancy** term | repo `statFEM.pdf`, `digital-twinning-...statistical-finite-element-method.pdf` |

## Fetch attempts that failed (for transparency)
- `en.wikipedia.org/wiki/Force_limited_vibration_testing` → 404 (page name differs).
- `royalsocietypublishing.org/doi/10.1098/rspa.2018.0826` (StatFEM paper) → 403 (paywall/bot block);
  used the repo PDF instead.
- Several NTRS force-limiting citation IDs → 404; used the HDBK-7004B vibrationdata mirror instead.

## Tools
`curl -sL -A "Mozilla/5.0"` for retrieval; `pdfminer.six` (`extract_text`) for PDF parsing;
`shasum -a 256` for content hashes.
