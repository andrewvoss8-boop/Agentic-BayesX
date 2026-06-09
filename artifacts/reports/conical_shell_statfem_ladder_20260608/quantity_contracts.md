# Quantity Contracts

## Modal frequency
- Numerator/denominator: not a ratio; cyclic natural frequency.
- Coordinate: global conical-shell modes of the radome.
- Excitation: impulse hammer test for measured modes; normal modes for FEM.
- Boundary condition: approximately free-free test on foam; preliminary FEM completely free and omits foam.
- Units: Hz.
- Expected behavior: free-free model should include six rigid-body modes near 0 Hz before flexible modes; published table reports flexible modes only.
- Reference: Vibrationdata `conical_shell.pdf`, Table 1 and Appendix A.
- Checker: require measured and published-FEA mode tables; require missing third FEA mode to remain missing rather than fabricated.

## Accelerance FRF
- Numerator: acceleration response.
- Denominator: impulse hammer force.
- Coordinates: aft-end and midpoint accelerometer response; hit location 12 inches from aft end.
- Boundary condition: radome on compliant foam, approximately free-free.
- Units: G/LBF, linear magnitude.
- Frequency axis: published figures use 0-1100 Hz linear; project review plots should use log frequency when regenerated from data. This phase has no raw FRF ordinates, only published modal peaks.
- Expected behavior: peaks near measured modal frequencies; amplitudes depend on hit/response location and damping.
- Reference: Vibrationdata `conical_shell.pdf`, Figures 2-4.
- Checker: report must state that no raw FRF ordinates were extracted in this phase.

## FEM-vs-test percent frequency error
- Numerator: published preliminary FEA frequency minus measured modal-test frequency.
- Denominator: measured modal-test frequency.
- Coordinate: matched published modes in Table 1.
- Units: percent.
- Expected behavior: first-mode error is exactly 0 because the report says the preliminary FEM properties were adjusted to match the fundamental.
- Reference: Vibrationdata `conical_shell.pdf`, Table 1 and Appendix A.
- Checker: require percent error table and explicit warning that first-mode agreement is tuned.

## Human Femap/Nastran flexible-pair frequency
- Numerator/denominator: not a ratio; mean cyclic natural frequency of a near-degenerate shell-mode pair.
- Coordinate: local Femap/Nastran output modes after the first six free-free rigid-body numerical-zero modes.
- Excitation: normal modes, no forcing.
- Boundary condition: free-free source deck.
- Units: Hz.
- Expected behavior: six near-zero rigid-body modes followed by nearly degenerate shell pairs.
- Reference: human-supplied screenshots `IMG_9814.jpg`, `IMG_9815.jpg`, `IMG_9816.jpg`.
- Checker: require six near-zero modes, pair means, and pair split metrics.

## Digitized peak accelerance QOI
- Numerator: acceleration response peak magnitude.
- Denominator: impulse hammer force.
- Coordinate: aft accelerometer response, hit at 12 inches from aft end.
- Boundary condition: radome on compliant foam, approximately free-free.
- Units: G/LBF.
- Frequency axis: log frequency for project-generated feature plot.
- Expected behavior: largest digitized peak near the first measured flexible mode.
- Reference: Vibrationdata `conical_shell.pdf`, Figures 2-4.
- Checker: require the report to label this as coarse visual digitization, not raw FRF data.
