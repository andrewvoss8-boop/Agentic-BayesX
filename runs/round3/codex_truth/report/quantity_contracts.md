# Quantity Contracts

## Complex diagonal apparent mass `M_ii(omega)`

- Numerator: complex interface generalized force in DOF `i`.
- Denominator: complex interface acceleration in the same DOF.
- Coordinates: `x`, `y`, `z`, `rx`, `ry`, `rz` in the published right-handed interface frame.
- Units: kg for translational DOFs; kg*m^2 for rotational DOFs.
- Excitation/BC: diagonal drive-point interface measurement of the assembled source/load truth unit.
- Expected behavior: modal resonances appear as apparent-mass valleys/rapid phase changes; drive-point antiresonances appear as apparent-mass peaks; translational low-frequency magnitudes are mass-scale quantities.

## Flight force PSD

- Quantity: one-sided interface force PSD.
- Units: N^2/Hz.
- dB convention: PSD-space dB, factor `10**(dB/10)`.
- Excitation: source-side stochastic flight forcing.

## netCG response PSD

- Numerator: dynamic interface force transmitted into the load from source/load FBS apparent-mass coupling, divided by load mass.
- Denominator: one standard gravity for conversion to g.
- Units: g^2/Hz.
- BC/modeling convention: single axial `z` interface coupling through source/load apparent-mass FBS. `F_iface(omega) = M_load(omega) * F(omega) / (M_source(omega) + M_load(omega))`.
- Shared contract: `docs/agents/competitive_full_experiment/round3/netcg_quantity_contract.md`.
- Limiting behavior: at low frequency the acceleration tends toward a rigid mass-sharing response; the rigid mass ratio is a sanity check only. Narrow-band coupled resonant features can dominate scalar GRMS.

## netCG `3*GRMS`

- Definition: `3 * sqrt(integral response_psd_g2_per_Hz df)`.
- Units: g.
- Integration coordinate: frequency in Hz over the published grid.
