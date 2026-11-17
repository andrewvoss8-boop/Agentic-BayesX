# Decisions log

D1 (2026-11-16) Human direction recorded in notes/memory.md CURRENT STATE before work began.
D2 NASA host refused by the environment's network policy; not routed around (no mirrors, no other hosts). All work since uses data in hand.
D3 Exact listings rebuilt from the June 4 MiB directory tails (private backup). Only the directory slices (300 KB) are committed; their 4 MiB parents match the SHA-256 values the June runner printed.
D4 NASA's 74 MB deck is not committed. Slide text, four tables and three figures are committed under data/nasa_deck/ with hashes, labelled as NASA source material.
D5 Digitiser thresholds set before the known-answer run. Curve-level median error came out 0.66 dB against a 0.5 dB limit; the limit is kept and the gate is YELLOW. The metric-level limits (the quantities actually reported) were met with margin.
D6 The pilot (two drive-point curves) is labelled exploratory: conceived after reading the deck, curves chosen by NASA, drive points usually agree best.
D7 Project-FEM predictions for NASA's 264 plots frozen before any of them was seen (prereg_frozen_inputs.json). freeze_predictions.py later gained a --verify branch only; the verify run reproduces the frozen array hash exactly.
D8 Before any tier-4 plot was seen, the dry run showed the first QA rule (a test peak near 54.19 Hz) would wrongly exclude responses on a node line of mode 1. Replaced by a content-free axis check; the peak distance is kept as a diagnostic.
D9 Rehearsal uses stand-in shaker locations (NASA's shaker grids are not FEM grids) and reports damping resolvability estimator-free, because 25 of 27 FEM modes in 45-200 Hz are clustered beyond what half-power can separate.
D10 Correction to the 2026-11-14 report: before July 22 the project did use NASA's burst-run frequency tables (six burst runs, noise floor in shocksat_fem_modal_twin_20260609) and extracted the fixed-base model and display files; the raw burst time histories (.ati) and the burst FRF file (.afu) were never used. The impact-survey shapes (.ash) also came from FEM_and_CAD.zip.
