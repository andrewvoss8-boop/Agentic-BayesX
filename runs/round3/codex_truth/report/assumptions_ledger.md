# Public Assumptions Ledger

This public ledger records shared/observable assumptions only. Hidden truth details are in `sealed_truth/`.

```json
{
  "observable_counts": {
    "n_builds": 8,
    "n_flights": 11,
    "n_frequency": 4040
  },
  "shared_nominal_design_starting_point": {
    "dome_first_interface_mode_hz": 93.5,
    "tray_first_axial_mount_mode_hz": 86.25,
    "avionics_mass_kg": 136.0,
    "strut_count": 6,
    "coordinate_frame": "x/y transverse, z axial from dome/source toward tray/load"
  },
  "netcg_normalization_observable": {
    "load_mass_kg": 170.0,
    "g0_m_per_s2": 9.80665
  },
  "hidden_boundary": "As-built parameter values, hidden imperfection classes/sizes, and noise scales are sealed, not listed in this public assumptions file."
}
```
