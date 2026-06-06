# Round 3 Published Data Contract

This folder contains observable synthetic data for the blind round-3 inference agent.

## File

- `observations.npz`

## Coordinate frame and DOF order

- SI units.
- Interface reference frame: `x` and `y` are transverse axes in the tray plane; `z` is axial, positive from dome/source toward the tray/load; rotations follow the right-hand rule about those axes.
- DOF order is stored in `dof_order`: `["x", "y", "z", "rx", "ry", "rz"]`.

## Frequency grid

- Key: `frequency_hz`
- Shape: `(n_frequency,)`
- Range: 5 to 600 Hz
- Count: 4040
- The grid is dense in the interface modal band and continues through 600 Hz.

## Apparent mass observations

- Keys: `apparent_mass_real`, `apparent_mass_imag`
- Shape: `(n_build, n_dof, n_frequency)` = `(8, 6, 4040)`
- Build count: 8
- DOF count: 6
- Complex apparent mass is `apparent_mass_real + 1j*apparent_mass_imag`.
- Translational DOFs (`x`, `y`, `z`) use units kg.
- Rotational DOFs (`rx`, `ry`, `rz`) use units kg*m^2.
- These are diagonal interface apparent-mass observations with sensor noise already applied.

## Flight forcing observations/input

- Key: `design_force_psd_N2_per_Hz`
- Shape: `(n_frequency,)`
- Units: `N^2/Hz`
- Key: `flight_force_psd_N2_per_Hz`
- Shape: `(n_flight, n_frequency)` = `(11, 4040)`
- Flight count: 11
- Units: `N^2/Hz`
- The shared forcing convention is PSD-space dB: multiply PSD by `10**(dB/10)`.
- Shared forcing model: mean offset -6 dB relative to the design envelope; Matern-3/2 GP in log10 frequency; fixed 3 dB flight-to-flight scatter.
- Machine-readable forcing metadata is stored in `forcing_model_json`.

## Response observations

- Key: `response_psd_g2_per_Hz`
- Shape: `(n_build, n_flight, n_frequency)` = `(8, 11, 4040)`
- Units: `g^2/Hz`
- This is the netCG response PSD for each build under each flight forcing draw.
- Key: `netcg_3grms_g`
- Shape: `(n_build, n_flight)` = `(8, 11)`
- Units: `g`
- Definition: `3 * sqrt(integral response_psd_g2_per_Hz df)`.
- netCG follows the shared canonical contract in `docs/agents/competitive_full_experiment/round3/netcg_quantity_contract.md`: `netCG = F_iface(omega) / m_load`, where `F_iface` is the dynamic transmitted load-interface force from source/load FBS apparent-mass coupling and `m_load` is the published scalar `load_mass_kg`.
- The f -> 0 rigid mass-sharing limit is a sanity check only, not the QOI definition.
- The load mass used for the netCG normalization is stored as `load_mass_kg`.

## Observable-only boundary

This contract intentionally gives schema, units, coordinate conventions, counts, and the shared forcing model only. It does not describe the hidden as-built generator, hidden parameter values, hidden noise scales, or hidden model-form details.
