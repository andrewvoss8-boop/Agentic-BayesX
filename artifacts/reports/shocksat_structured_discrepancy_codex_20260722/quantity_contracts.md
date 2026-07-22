# Quantity contracts

For drive `d`, response channel `i`, frequency `f_s`, and `H_ref = 1 g/lbf`:

```text
q_meas(d,i,s)  = ln(|H1_meas(d,i,f_s)| / H_ref)       [dimensionless]
q_fem(d,i,s;θ) = ln(|H1_fem(d,i,f_s;θ,ζ)| / H_ref)    [dimensionless]
r(d,i,s;θ)     = q_meas - q_fem - c_d                 [dimensionless]
r              = m(f_s,x_i,a_i) + u(f_s,x_i,a_i) + e
e              ~ Normal(0, sigma_e^2)
```

`H1` is force-referenced accelerance: response acceleration along the channel's frozen structural-axis label divided by impact force along the drive axis, with free-free ShockSat boundary conditions. Sensor coordinates `x_i=(x,y,z)` are inches in the frozen ShockSat frame used by `channel_map.csv`: `z` is axial height; `x,y` are transverse. The categorical response axis `a_i` is not treated as a fourth coordinate. Drive gain `c_d` is a scalar natural-log amplitude offset. For a held-out drive it is not estimated from that drive.

The source cache labeled `+XY (990)` is contracted as an equal-amplitude normalized X+Y drive at its frozen impact coordinate because the reduced forward exposes Cartesian rows. This forcing-direction approximation is a high-priority sensitivity and limits drive-transfer claims.

The structured mean is `m=H beta`. The zero-prior-mean residual Gaussian process is `u`. Reports separate `E[H_* beta|training]`, `E[u_*|training]`, their posterior covariance/cross-covariance, and their sum. Decibels are `20/log(10) * q`; the report never takes the logarithm of a dimensional accelerance.

## Expected behavior and reference

Accelerance tends toward an inverse-mass-like finite high-frequency response in a sufficiently local rigid regime; within this reduced flexible-structure band it has resonant peaks and antiresonant notches. A coarse 2.5 Hz grid cannot certify individual sharp peak amplitudes. It is used for broad discrepancy transfer relative to the 10 Hz kernel; a 1.25 Hz refinement near held-out cores bounds grid sensitivity. The covariance form follows Schneider et al. (2022), Eqs. (19)–(25), but only for log magnitude.

## Spectral-estimation contract

The five multireference caches contain H1 estimates on a common native grid. Each cache records the number of retained impacts (`n_hits_used`) and the impact identities. The inherited processing uses force-referenced spectra and coherence; the selected analysis interpolates log magnitude to the frozen grid and does not re-average impacts. Frequency range, native spacing, retained-hit count, drive axis, and coherence inventory are recorded in `data_inventory.json`. Window, frame length, overlap, detrending, and averaging details are inherited source metadata where present; missing fields are explicit YELLOW limitations, not guessed.
