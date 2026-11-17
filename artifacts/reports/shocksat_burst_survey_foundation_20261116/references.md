# References checked

- NASA ShockSat correlation summary, `FEM/Correlation/Final_Summary_Documentation_101521_rev1.pptx` in NASA's public FEM_and_CAD.zip (CRC-32 6a9a1c7f). Used for: test and FEM frequencies, cross-orthogonality, pretest sensor-set checks, configuration and shaker statements, two drive-point FRF figures. Our numbers are checked against its printed values (gate A4) and its listed frequencies (gate A6).
- NASA ShockSat workshop page, https://nescacademy.nasa.gov/workshops/ShockSat (data source; unreachable from this environment).
- ShockSat testbed paper, Journal of Spacecraft and Rockets, https://arc.aiaa.org/doi/10.2514/1.A36538 (states the data and FEM are provided for public research use; modal test and correlation credited to NASA Langley and Glenn).
- ATA Engineering IMAT `readadf` documentation, http://www.ataengineering.com/downloads/imat/all_doc/doc/Content/import_export/readadf.html: `.afu` function, `.ati` time history and `.ash` shape files are I-DEAS associated data files; byte layout not published, hence the probe.
- PKWARE APPNOTE (ZIP format) for the central-directory and ZIP64 parsing in `code/zipdir.py`.
- Project record: Card H (2026-07-23, recovered, private repo), `shocksat_fem_modal_twin_20260609` (impact-survey shapes, burst-run frequency scatter), `shocksat_statfem_runner_20260609` (June probes and directory tails), 2026-08-10 failure-attribution handoff.
- Standards: NASA-STD-5002B, NASA-STD-7009B and ECSS-E-ST-32-11C were reviewed in the project's 2026-08-03 memo; this workspace makes no compliance claim.
