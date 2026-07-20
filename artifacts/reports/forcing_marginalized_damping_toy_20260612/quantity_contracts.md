# Quantity contracts - forcing-marginalized damping toy

## Complex response ratio `T21(f, A)`

- Numerator: secondary acceleration `a2(f, A)`.
- Denominator: primary acceleration `a1(f, A)`.
- Coordinate: one translational DOF on each mass.
- Excitation: single hidden force applied at the primary mass.
- Boundary condition: primary attached to ground; secondary attached to primary; hidden truth also has an unmodelled rattler attached to secondary.
- Units: dimensionless.
- Expected limiting behavior: as `f -> 0`, secondary and primary move together, so `|T21| -> 1`.
- Resonance behavior: peaks/valleys near primary-secondary and hidden-rattler modes; high damping reduces peak height and broadens features.
- Reference convention: transfer ratio / transmissibility style; not an absolute FRF and not a force spectrum.

## Interface-force per primary acceleration `M12(f, A)`

- Numerator: complex primary-secondary joint force `F12 = (k12 + i omega c12) (x2 - x1)` in N.
- Denominator: primary acceleration `a1 = -omega^2 x1` in m/s^2.
- Coordinate: force in the single joint coordinate.
- Units: kg.
- Expected limiting behavior: finite inertial load proxy away from zeros of `a1`.
- Resonance behavior: peaks near joint-sensitive modes; damping and stiffness softening change both magnitude and bandwidth.
- Reference convention: apparent-mass-like ratio, but local joint force rather than net interface force.

## Equivalent joint damping `zeta_joint`

- Numerator/denominator: dimensionless damping ratio inferred by the twin for a 2-DOF equivalent joint.
- Units: none.
- Excitation dependence: inferred separately for low and high amplitude labels.
- Expected behavior: if high-amplitude slip dissipates more energy, `zeta_high > zeta_low`.
- Caveat: this is not Coulomb coefficient, preload, or a physical microslip law. It is an equivalent linear damping ratio near a tested condition.
