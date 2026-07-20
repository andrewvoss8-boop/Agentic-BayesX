# Assumptions Ledger

| ID | Assumption | Value / Units | Rationale | Sensitivity Priority |
| --- | --- | --- | --- | --- |
| A1 | Damping sign from response-only ringdown can be screened with logarithmic decrement or Hilbert-envelope slope. | Dimensionless damping ratio `zeta` | Valid only for lightly damped, locally single-mode decay segments. | High |
| A2 | Frequency-shift sign can be screened by comparing dominant peak or zero-crossing frequency at different amplitudes. | Hz | Hardening/softening plus damping changes can move peaks; forcing/windowing can also move estimates. | High |
| A3 | ShockSat hammer FRF evidence is not likelihood-grade unless coherence/source mapping is acceptable. | Coherence dimensionless | Prior repo decision logs flag low coherence and unresolved source/response mapping. | High |
| A4 | Suspended panel LDV H1/H2/coherence products are modal-test summaries, not necessarily separate drive-amplitude sweeps. | Mixed units from source files | Without amplitude-level metadata, they can show quality/nonlinearity hints but not prove amplitude dependence. | High |
| A5 | MPL CSV acceleration uses the prior scan's channel interpretation unless headers say otherwise. | m/s^2 or g, checked per file | Existing scan notes KS78C +/-100g and 10 kHz; raw headers must still be inspected. | Medium |
