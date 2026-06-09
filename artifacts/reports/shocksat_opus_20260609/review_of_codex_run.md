# Opus Review of the Codex ShockSat Run

Reviewer: Claude Code (Opus), lead agent
Date: 2026-06-09
Reviewed workspace: `artifacts/reports/shocksat_statfem_runner_20260609/` (Codex GPT-5.5)
Reviewed decisions log: `.../decisions_log.md` (read before this review, per harness rule)

## One-paragraph verdict

The Codex run is a **good, honest foundation**. It did exactly the right *type* of first
move for a real public dataset: source provenance, file/FEM/instrumentation inventory,
channel map, test-log summary, first measured-data plots, quantity contracts, and a
StatFEM *launch definition* — with **no** posterior, **no** NUTS claim, and explicit
"this is diagnostic, not a likelihood" labeling. That restraint matches the project
vision (real data is the trust bridge; synthetic FEM is not validated science) and the
anti-overclaim rules. I am keeping all of that provenance/inventory work and building on it.

**However**, the one *quantitative* claim it surfaced — that the Test07 impact-hammer FRF
has "median coherence ~0.07" and is therefore "not likelihood-ready / low-coherence
diagnostic" — rests on **two coupled errors** that make the coherence number an artifact,
not a property of the data. Until those are fixed, the "data may be too poor for a
likelihood" branch of the wrong-question trigger is **not** supported by evidence.

## What Codex got right (keep)

- **Provenance + inventory**: source manifest, SHA256, ZIP integrity, file/FEM/instrumentation
  inventories, channel map (`channel_map.csv`), test-log summary. Reusable as-is.
- **MAT loader**: `Recorder{ch}` selective load via `scipy.io.loadmat(variable_names=...)`,
  reading hits straight from the zip. Clean; I reuse this pattern.
- **Sample-rate honesty**: caught that plotted MATs report `dXstep = 4e-6 s` = 250,000 sps,
  not the README's 100,000 sps general value, and labeled the file-specific value authoritative.
- **Restraint**: no posterior, no NUTS/HMC claim, no fabricated FEM-vs-test overlay. The
  hammer FRF is explicitly labeled diagnostic. Priority deliverables table is real and
  artifact-backed. This is the behavior the harness wants.
- **Real blocker correctly flagged**: the ShockSat shock channels map to `9900xxx` FEM grids
  while NASA's SOL 111 correlation uses force grids `11101/11110` and response points
  `1101-7105`. That grid reconciliation is a genuine, necessary task.

## What is wrong or mis-framed (fix)

### 1. Impact-FRF processing bug (drives the "low coherence" verdict)
Each Test07 MAT is **one** ~1 s impact hit at 250 kHz (~250,001 samples). Codex computes
coherence/FRF with Welch segmenting **inside that single transient**
(`nperseg=32768`, `noverlap=16384`, `scipy.signal.coherence/csd/welch`). A single hit splits
into ~15 Welch segments, but the hammer pulse occupies only one short window (a few ms);
the remaining ~14 segments are free-decay/noise. Magnitude-squared coherence averaged over
mostly-no-input segments collapses toward ~0. **Coherence ~0.07 is the expected artifact of
this method, not a data-quality measurement.**

Correct impact processing:
- One analysis frame **per hit**; apply a **force window** (short taper around the pulse) to
  the force and an **exponential window** to the response (anchored at impact).
- One FFT per hit → `F(f)`, `Y(f)`.
- Ensemble across hits: `H1 = <F* Y> / <F* F>`, coherence `γ² = |<F* Y>|² / (<F* F><Y* Y>)`.
- With only 4 hits, ensemble coherence has weak statistical power (small-N bias), so the
  **honest** few-hit quality metric is **hit-to-hit FRF repeatability** (overlay the per-hit
  FRFs) plus resonance sharpness — not a single coherence number.

### 2. Wrong frequency band for a modal hammer test
Codex evaluates coherence over **100–10,000 Hz** — the **pyro shock** band. But Test07 is a
**modal hammer** test (`Test01-07 = ModalHammer/ImpactHammer 990X/990Y/990Z/990XY`). NASA's
own FEM correlation reference for these is **SOL 111 free-free FRF verification, 10–400 Hz**
(decks `SOL_111_Free_Free_Force_11101X/11110Y.bdf`, response 10–400 Hz in the `.pch`).
A light hammer tap has little usable energy at 1–10 kHz, so coherence up there is naturally
poor regardless of method. The modal FRF must be judged in **~10–400 Hz** (extendable to
~2 kHz), against the SOL 111 reference — which is exactly the "compare against the reference
standard before accepting outputs" rule.

### 3. Minor: NASA comparison-PNG index may over-state extracted assets
`nasa_correlation_frf_assets.md` reports `11101X_Impact_Comparison: 132 PNG` etc., but no PNGs
are present under the extracted `FEM/Correlation` tree (`find ... -iname '*.png'` = 0). The
counts appear to come from the full-archive file *listing*, not extracted files. Not
fabrication (it is labeled "indexed_from_fem_archive"), but the index reads as if the plots
are in hand. I treat the SOL 111 `.pch` (which *is* extracted) as the usable FEM reference.

## Reconciled framing (what the data actually supports)

The dataset is richer than the Codex packet foregrounds. The extracted
`FEM/Correlation/` tree contains a **complete modal-correlation package**:
- FEM SOL 111 **free-free FRFs** (`.pch`, force at +X grid `11101`, +Y grid `11110`, 10–400 Hz);
- **Test mode shapes** (`Test_Mode_Shapes/`, `FINAL_FF`, `FINAL_fixed_base`);
- **TAM** (Test Analysis Model) reduced matrices (`ShockSat_TAM_101521.dat`, `TAM.pch`);
- modal test logs, instrumentation locations, measured weights.

So the natural **first real-data StatFEM bridge** is the **free-free modal correlation,
10–400 Hz** (FEM SOL 111 FRF vs measured hammer FRF at matched points / MAC against test
modes) — *not* the 100–10,000 Hz pyro shock, which is the harder held-out QOI/validation
layer. The pyro shock = the unknown-forcing, force-limiting load-QOI surface the project
vision cares about, and it should sit **downstream** of a validated low-frequency modal twin.

## What this Opus run does next

1. Re-process the Test07 hammer hits with correct impact windowing in the **modal band**,
   show **per-hit FRF repeatability** and properly-estimated ensemble coherence, and test
   whether the "low coherence" verdict survives. (This run.)
2. Parse the SOL 111 `.pch` FEM FRF as the **reference standard** and scope the point/unit
   reconciliation needed for a real FEM-vs-test overlay. (This run: scoping + parse.)
3. Define the StatFEM v1 around the **10–400 Hz free-free modal correlation** with the pyro
   shock as held-out validation. (Update launch definition.)

I did **not** modify Codex's workspace, its checker, durable rules, or sampler standards.
