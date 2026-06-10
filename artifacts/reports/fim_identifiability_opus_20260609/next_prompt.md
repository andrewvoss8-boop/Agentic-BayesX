# Next prompt / recommendations (for the lead + human, after review)

This was a pre-test design calculation (Fisher information + profile likelihood), not a
posterior run. Recommended follow-ups, in priority order:

1. **Make the joints observable on purpose (experiment redesign).** The two joint stiffnesses
   are unidentifiable because the joints are near-rigid + moment-free. If joint behaviour
   matters for any downstream QOI, the test must be redesigned: a deliberately joint-compliant
   build (lower k), a moment-carrying joint, or a static/proof load that loads the joint
   laterally. Re-run this FIM on that variant to confirm it lights the joints up. (Cheap.)

2. **Promote 3-of-5 to a real NUTS/HMC Bayesian update** on the hexapod tray, inferring exactly
   the identifiable set (`strut_EA`, `tray_E`, `strut_EI`) and fixing the joints at prior, with
   synthetic-then-real modal data. This is where the sampler rule + convergence gate apply.
   The FIM marginals (sd ≈ 0.01–0.03) are the expected posterior widths to sanity-check NUTS against.

3. **Band-aware test plan.** The 3rd parameter (`strut_EI`) needs the 540–570 Hz tray-flex modes.
   Decide whether the rig/excitation/DAQ can resolve that band; if not, the honest plan is a
   **2-parameter** twin (`strut_EA`, `tray_E`). Fold the where-to-measure (near-center z) and
   where-to-hit (corner tap) results into the instrumentation plan.

4. **Repeat with discrepancy present.** Add a modal-frequency discrepancy term and re-check
   practical identifiability; held-out coverage remains the referee (cf. the StatFEM v1 lesson:
   a converged twin can be confidently wrong out of regime).

## Durable-rule note (LEAD decides after human review — not changed here)
- This run is evidence for a small reusable harness item: a **pre-test FIM/identifiability gate**
  ("how many parameters can this test support, which combos are sloppy, where to measure/hit")
  before committing to a Bayesian-updating campaign. Surface to Andrew before encoding in AGENTS.md.
