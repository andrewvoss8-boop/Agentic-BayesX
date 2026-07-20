# quantity_contracts.md

## `log|H_1(omega)|`

- Numerator: measured response acceleration in `g`.
- Denominator: hammer force in `lbf`.
- Coordinate: sensor structural axis from copied `channel_map.csv`.
- Excitation: same +X point force at the ShockSat impact-node mapping used by the StatFEM run.
- Boundary condition: inherited free/free reduced ShockSat model.
- Units: natural log of `[g/lbf]`.
- Expected limiting behavior: low response away from resonances; sharp growth near modes; local minima/antiresonances possible.
- Resonance behavior: peak location sensitive to FEM frequency error and damping; magnitude sensitive to mode shape, damping, and global gain.
- Reference convention: copied `realfrf.py` matched-path accelerance.

## Peak Accelerance

- Numerator: maximum `|H_1(omega)|` over 45-260 Hz.
- Denominator: force in `lbf`.
- Units: `[g/lbf]`.
- Coordinate and excitation: held-out response channel under the same drive point.
- Expected limiting behavior: controlled by the largest in-band resonance at that channel.
- Resonance behavior: sharp and under-resolved if the resonance falls between frequency lines; cannot be interpreted without the frequency-grid caveat.
- Scoring: copied `score.py::score_qoi`, interval score / CRPS / log predictive density headline.

## Band-GRMS

- Numerator: square root of the frequency integral of `|H_1(omega)|^2`.
- Denominator: `lbf`.
- Units: `[g/lbf]` under a flat unit force PSD convention.
- Coordinate and excitation: held-out response channel under the same drive point.
- Expected limiting behavior: accumulates energy across the 45-260 Hz band; less single-peak sensitive than peak accelerance.
- Resonance behavior: dominated by dense clusters if several modes are near a channel's high-response axis.
- Scoring: copied `score.py::score_qoi`, same as peak.

## `beta`

- Definition: learned inverse-temperature multiplying the dynamic-stiffness residual in the IFT field prior.
- Numerator / denominator: precision on `||Z u - f||^2`; numeric units are inherited from the reduced residual norm.
- Expected limiting behavior: large `beta` makes the field close to the FEM equation; small `beta` makes the prior broad and indicates low trust in the coarse physics.
- Reference: IFT/PIFT physics-informed prior trust parameter in arXiv:2306.02150 and arXiv:2301.07609.
