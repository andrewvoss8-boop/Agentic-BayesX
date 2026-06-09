# ShockSat Quantity Contracts

These contracts are written before accepting plots or likelihoods. Units are stated from the fetched README and instrumentation workbook unless otherwise noted.

## 1. Acceleration Time History

- Quantity name: acceleration time history.
- Numerator: calibrated accelerometer response signal.
- Denominator: none.
- Coordinate(s): sensor structural axis from the instrumentation sheet (`Accel Dir for SS X/Y/Z`) at a listed FEM grid.
- Excitation: hammer impact or pyro event, specified by test log.
- Boundary condition: as-tested ShockSat hardware; support/suspension condition must be taken from the relevant test log or overview before FEM comparison.
- Units: `g` for accelerometer channels, with sensor calibration in `mV/g`.
- Time axis: seconds from MAT sample zero. README states `100000 samples/s` generally; when a MAT file provides `dXstep`, the file-specific sample interval is authoritative for that plotted/test subset.
- Expected behavior: transient shock/impact response with baseline near zero after detrending; higher magnitude near source channels and wave-propagation decay/scatter away from source.
- Reference/source: ShockSat README and instrumentation workbook.
- Checker: require channel map, units, sample rate, and test ID before plotting.

## 2. Power Spectral Density Diagnostic

- Quantity name: one-sided Welch PSD diagnostic.
- Numerator: squared calibrated channel amplitude.
- Denominator: frequency bandwidth.
- Coordinate(s): same sensor coordinate as the time history.
- Excitation: same event as the time history.
- Boundary condition: as-tested hardware.
- Units: `g^2/Hz` for acceleration channels and `lbf^2/Hz` for hammer force if force is plotted.
- Frequency axis: Hz, log-scaled for review, focused on `100-10000 Hz`.
- Expected behavior: broad shock/impact energy; narrow modal content may appear, but PSD peaks are not natural frequencies without a feature contract.
- Reference/source: README target band and standard Welch PSD convention.
- Checker: label PSD as a diagnostic, not as an FRF or SRS.

## 3. Shock Response Spectrum

- Quantity name: Shock Response Spectrum (SRS).
- Numerator: peak absolute response of a bank of single-degree-of-freedom oscillators to the acceleration time history.
- Denominator: none.
- Coordinate(s): sensor structural axis.
- Excitation: pyro or impact acceleration input as measured at the channel.
- Boundary condition: as-tested hardware.
- Units: `g`.
- Frequency axis: oscillator natural frequency in Hz, preferably log-spaced.
- Expected behavior: positive envelope-like curve; not directly a transfer function and not phase-bearing.
- Reference/source: standard shock-test SRS convention; damping or Q must be stated when computed.
- Checker: SRS is not accepted unless damping/Q and algorithm are documented. This run uses PSD if SRS is not computed.

## 4. Hammer-Test FRF

- Quantity name: accelerance FRF from hammer force to acceleration.
- Numerator: response acceleration at selected channel.
- Denominator: measured hammer force at channel 116 or equivalent force channel.
- Coordinate(s): response sensor structural axis and hammer input point/direction from test log.
- Excitation: hammer force, units `lbf`.
- Boundary condition: as-tested hammer/modal configuration.
- Units: `g/lbf` if acceleration is in `g` and force is in `lbf`.
- Frequency axis: Hz, log-scaled unless a narrow linear modal zoom is justified.
- Expected behavior: resonant peaks, antiresonances depending on drive/response pair, phase roll if complex FRF is estimated.
- Reference/source: instrumentation workbook hammer row and modal-test FRF convention.
- Checker: do not call a response-only spectrum an FRF; require force channel and estimator details.

## 5. Cross-Channel Transfer Estimate

- Quantity name: response-response transfer or normalized cross-channel estimate.
- Numerator: response channel spectrum.
- Denominator: reference response channel spectrum.
- Coordinate(s): two listed sensor structural axes.
- Excitation: same event; forcing may be unknown for pyro.
- Boundary condition: as-tested hardware.
- Units: dimensionless if same units, otherwise stated ratio.
- Frequency axis: Hz, log-scaled.
- Expected behavior: useful for relative propagation diagnostics; not a physical FRF unless input conditions justify it.
- Reference/source: signal-processing convention, not a FEM property by itself.
- Checker: label as cross-channel diagnostic, not force-to-response FRF.

## 6. FEM Modal Frequency

- Quantity name: FEM modal frequency.
- Numerator: modal circular frequency converted to cycles per second.
- Denominator: `2*pi`.
- Coordinate(s): global FEM coordinates from source deck.
- Excitation: none; eigenvalue property.
- Boundary condition: FEM boundary/suspension assumptions from deck/correlation documentation.
- Units: Hz.
- Frequency axis: mode index or Hz.
- Expected behavior: positive flexible modes; rigid-body modes depend on boundary assumptions.
- Reference/source: fetched FEM deck/correlation files when parseable.
- Checker: require solver/source file and boundary-condition cards before comparing to test.

## 7. FEM Mode Shape / MAC

- Quantity name: mode shape and Modal Assurance Criterion (MAC).
- Numerator: squared magnitude of the modal-vector inner product.
- Denominator: product of modal-vector self inner products.
- Coordinate(s): paired test/FEM response coordinates at accelerometer grids or mapped nodes.
- Excitation: none for FEM mode; modal-test excitation for test mode extraction.
- Boundary condition: matched test/FEM boundary condition.
- Units: mode shapes are scale-normalized; MAC is dimensionless.
- Expected behavior: MAC near 1 for matching shapes, near 0 for orthogonal/unrelated shapes; repeated/close modes require subspace comparison.
- Reference/source: standard modal correlation convention.
- Checker: do not report MAC without test mode vectors and a coordinate map.

## 8. Candidate StatFEM Observation

- Quantity name: selected observation vector for v1 StatFEM.
- Numerator: measured modal frequencies, FRF log magnitudes/phases, or selected response features.
- Denominator: depends on chosen observation; explicitly stated in the launch definition.
- Coordinate(s): selected sensor/test coordinates with FEM grid map.
- Excitation: hammer/modal first if force is available; pyro response reserved for validation/QOI if appropriate.
- Boundary condition: matched test/FEM configuration.
- Units: observation-specific.
- Expected behavior: enough sensitivity to selected stiffness/damping parameters without allowing discrepancy to impersonate physics.
- Reference/source: ShockSat data and project StatFEM harness gates.
- Checker: require data count, likelihood data usage, inferred/fixed/not-inferred variables, and held-out validation.

## 9. Candidate QOI

- Quantity name: payload/interface/far-field shock response metric.
- Numerator: selected acceleration/SRS/PSD/FRF feature at a payload-like, interface, or far-field channel.
- Denominator: none for response metrics; force for FRF-derived quantities.
- Coordinate(s): selected channel structural axis and FEM grid.
- Excitation: pyro NSD or hammer/modal depending on model layer.
- Boundary condition: as-tested hardware and event.
- Units: `g`, `g^2/Hz`, `g/lbf`, or SRS `g`, explicitly chosen before inference.
- Expected behavior: response should reflect source-to-far-field propagation and joint/interface effects; not all QOI shifts are stiffness changes.
- Reference/source: ShockSat stated purpose as shock-propagation methodology test bed.
- Checker: QOI validation must hold out at least one channel, test, band, or mode family.
