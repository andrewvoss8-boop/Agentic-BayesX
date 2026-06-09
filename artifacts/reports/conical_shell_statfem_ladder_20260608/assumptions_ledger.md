# Assumptions Ledger

| Assumption | Value | Units | Source | Rationale | Sensitivity | Where used |
|---|---:|---|---|---|---|---|
| Shell thickness | 0.1 | inch | Vibrationdata PDF Appendix A | Published preliminary FEM value. | high | FEM metadata, sensitivity |
| Young modulus | 16317180.0 | lbf/in^2 | Vibrationdata PDF Appendix A | Adjusted in the preliminary FEM so the fundamental matched test. | high | FEM metadata, digital-twin launch |
| Poisson ratio | 0.33 | dimensionless | Vibrationdata PDF Appendix A | Published preliminary FEM value. | low | FEM metadata |
| Mass density | 0.000126941 | lbf*s^2/in^4 | Vibrationdata PDF Appendix A | Published preliminary FEM value; report writes lbf sec^2/in but shell density units are interpreted in inch-lbf-second consistency. | high | FEM metadata, sensitivity |
| Overall length | 45.0 | inch | Vibrationdata PDF Appendix A | Published approximate radome length. | medium | geometry check |
| Base diameter | 14.0 | inch | Vibrationdata PDF Appendix A | Published approximate base diameter. | medium | geometry check |
| Boundary condition | approximately free-free | categorical | Vibrationdata PDF test configuration | Radome rested on compliant foam; preliminary FEM omitted foam. | high | comparison, digital-twin launch |
| Fundamental damping | 0.6 | percent critical | Vibrationdata PDF introduction/damping section | Measured first-mode damping; not enough to infer a damping curve. | medium | digital-twin launch |
| Measured modes | [97.6, 278.0, 429.0, 529.0] | Hz | Vibrationdata PDF Table 1 | Published modal-test frequencies used as observed data. | high | FEM-vs-test comparison |
| Published preliminary FEA modes | [97.6, 274.0, null, 523.0] | Hz | Vibrationdata PDF Table 1 | Published FEM values; missing third mode retained as missing, not filled. | high | FEM-vs-test comparison |
| Human Femap/Nastran flexible pair means | [97.637315, 274.01795, 524.29385, 728.9819, 764.57545, 847.8621, 939.88045] | Hz | Human-supplied Femap/Nastran screenshots | Local solve evidence: six near-zero rigid-body modes followed by nearly degenerate flexible shell pairs. | high | local solve comparison, StatFEM v1 |
| FRF peak digitization | coarse visual peak features only | categorical | Vibrationdata PDF Figures 2-4 | Raw FRF ordinates are not available; amplitudes are secondary visual estimates with large uncertainty. | high | FRF/QOI layer |
| Modal StatFEM v1 observation noise | 0.004 | fraction of modal frequency | engineering assumption | Small term for reading/reporting frequency uncertainty. | medium | modal likelihood |
| Modal StatFEM v1 discrepancy scale | 0.02 | fraction of modal frequency | engineering assumption | Represents model-form error after the preliminary FEM tuning. | high | modal likelihood, held-out validation |
| Modal StatFEM v1 prior log stiffness sigma | 0.16 | natural log units | engineering assumption | Allows roughly +/-17% one-sigma stiffness variation while keeping v1 identifiable. | medium | modal posterior |
| Source FEM tuning | E and density adjusted to match the fundamental | categorical | Vibrationdata PDF Appendix A | This prevents treating the first-mode agreement as independent validation. | high | limitations, digital-twin launch |
| StatFEM active | true | boolean | This phase | A one-parameter modal-only StatFEM-style grid update is active; no NUTS/HMC claim is made. | high | checker, report |
