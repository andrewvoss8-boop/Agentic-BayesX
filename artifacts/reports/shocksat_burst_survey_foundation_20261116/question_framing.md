# Question framing

Engineering decision supported: whether NASA's own ShockSat modal survey (burst-random shaker runs 78 and 99 free-free, run 139 fixed base, impact runs, the bolt-torque sweep) can serve as the higher-quality data set that the 2026-08-10 failure-attribution handoff said the project needed before any more modeling. If yes, the next study re-runs held-out FRF prediction on that data; if no, the project needs a new test.

Objective of this workspace: establish, with artifacts, (1) whether the files exist and can be fetched exactly; (2) what NASA's own documents say about them; (3) whether data already in hand indicate that modal-survey data agree with the FEM much better than the shock-campaign data the project used (median 10.0 dB per curve); (4) what the burst data could resolve; and (5) a frozen, pre-registered test that decides (3) once the files can be downloaded.

What the search may choose: nothing. No model is fitted. The only free choices (bands, smoothing, thresholds, QA rules) are fixed in `prereg_gated_analysis.md` before the deciding data are seen.

Human judgment retained: whether a SUPPORTED verdict justifies a new held-out study on NASA data; whether shaker-block mass loading is acceptable to model.

What would make this the wrong question: if the binding limit is the sensor set (NASA states its correlation struggles above 150 Hz because of sensor placement), better data at the same sensors cannot fix held-out amplitude above 150 Hz; the pre-registered stratification by band tests this.
