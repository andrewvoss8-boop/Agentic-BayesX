# Priority Deliverables

## Human Ask
Do any datasets in the folder, specifically ShockSat, MPL test stand, and suspended panel, show signs of amplitude-dependent damping or hysteresis?

## Interpretation
- "Show signs" means a traceable triage screen, not a final nonlinear-system identification.
- Evidence for amplitude-dependent damping/hysteresis can include:
  - damping estimate changing with response amplitude;
  - modal peak frequency changing with amplitude;
  - repeat tests at different drive levels giving different FRF shapes or coherence;
  - paired force-response time histories showing loop/phase behavior or non-proportional decay.
- A dataset can be marked inconclusive if it lacks repeated amplitude levels, calibrated paired force-response data, or reliable event windows.

## Acceptance Criteria
- Inventory available files for the three named datasets.
- Run reproducible numerical checks where the data supports them.
- Separate GREEN/YELLOW/RED status for each dataset and an overall status.
- Write a short report with evidence, caveats, and next measurements needed.
- Do not claim nonlinear damping/hysteresis from plots alone.

## Delivered Artifacts
- `analysis_report.md`: main answer and evidence table.
- `results.json`: machine-readable scan outputs.
- `scripts/scan_amplitude_dependence.py`: replayable analysis script.
- `check_scan.py` and `checker_report.json`: artifact and evidence checks.
