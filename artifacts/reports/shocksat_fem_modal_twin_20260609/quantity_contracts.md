# Quantity Contracts — ShockSat FEM Modal Twin

Contract = what exactly each named quantity is, before it is plotted, fitted,
or checked.

## Modal frequency f_i [Hz]
- Definition: sqrt(lambda_i)/(2*pi) where (K q = lambda M q) is the undamped
  generalized eigenproblem of the FREE-FREE structure (no constraints; the six
  rigid-body modes are excluded from all elastic-mode statements).
- Units: Hz. K in lbf/in, M in lbf*s^2/in (consistent in/lbf/s system),
  lambda in (rad/s)^2.
- Measured side: OPoly polyreference fit of impact-hammer FRFs (the .ash set);
  test article suspended soft (free-free approximation). Damped natural
  frequencies; at the measured damping (0.1-1.7% critical) the damped/undamped
  distinction is < 0.02% and is ignored (ledger A14).
- Expected behavior: 6 RBMs ~0 Hz; first elastic ~54 Hz; density of modes
  increases with frequency; model trustworthiness decreases above ~150 Hz
  (NASA's own correlation statement).

## MAC (Modal Assurance Criterion) [dimensionless 0..1]
- Definition: MAC(phi, psi) = |phi^T psi|^2 / ((phi^T phi)(psi^T psi)) over
  the 132 MEASURED translational DOFs (76 accelerometer nodes x the measured
  subset of X,Y,Z, basic coordinate frame). Real-valued shapes.
- No mass weighting (the test never measured a mass matrix; the TAM
  cross-orthogonality NASA used is a different, mass-weighted quantity —
  named here so the two are not confused).
- Scale-invariant: per-mode arbitrary scaling of the test shapes drops out.
- Expected behavior: ~1 for a correct 1:1 mode pair, degrading with spatial
  aliasing as mode order rises (76 sensors cannot distinguish high-order
  panel modes).

## theta_g (part-group stiffness scale) [dimensionless]
- Definition: multiplier on the assembled stiffness block of part group g:
  K(theta) = K_fixed + sum_g theta_g K_g. Because element stiffness is linear
  in Young's modulus E (shells) and spring rate k (bushes), theta_g = 1.15
  is EXACTLY a 15% increase of E (or k) of every element in the group.
- Mass is NOT scaled (as-weighed checks pin it: 127.89 lb, CG z 28.01 in).
- Prior: lognormal, median 1 (see assumptions ledger for width).

## Held-out QOI
- QOI = the measured frequency f_i [Hz] (and its MAC) of a mode EXCLUDED from
  calibration, predicted by the posterior: median + central 95% CI of
  f_i(theta) over posterior samples (frequency CI is parameter-uncertainty
  only; the +noise-widened predictive interval is reported alongside).
- Coverage = fraction of held-out modes whose measured f_i falls inside the
  95% interval. Honest target ~0.95; both directions of miss are reported.
- No receptance/FRF QOI is defined in this packet: the upstream finding stands
  (SOL111 vs Test07 are different transfer paths; an FRF-magnitude likelihood
  or QOI would be invalid here).
