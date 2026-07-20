# Question Framing — Multi-point / 6-DOF behavior vs the NASA-HDBK-7004C toolbox

Task date: 2026-06-11. Lead-as-runner (Claude, lead agent). Workspace:
`artifacts/reports/notch_multipoint_7004c_20260611/`.

## Engineering decision being supported
When planning a force-limited vibration test (or interpreting flight/coupled-analysis
predictions) for a component mounted at MULTIPLE geometrically spaced feet, when can the
engineer trust the scalar NASA-HDBK-7004C tools (semi-empirical limit, simple/complex TDOF
force limit, single-node impedance method, net in-axis force limiting), and when do
multi-point/6-DOF effects (rocking, per-foot force cancellation, moment loads, notch
locality) change the answer enough to require moment/per-foot limits or a coupled model?

## Andrew's three explicit curiosities (from chat, 2026-06-10/11)
1. How do the 7004C 2-DOF intuitions change with multiple mounting points and
   6-dimensional motion, especially with geometrically spaced feet where rocking
   becomes possible?
2. How far away from a mounting foot can you get and still see the effect of the notch?
3. Can this be answered from first principles, or does it need a model of a compliant
   backing structure plus the payload — built, visualized, probed? (Andrew delegated the
   modeling choices: "I will leave it to your judgement.")

## Success metric
Artifact-backed numerical examples in which every claimed behavior is visible in a
figure/GIF AND traceable to checker-verified numbers, with the 7004C scalar-tool
prediction overlaid on the multi-point truth so the gap IS the result. No sampler, no
Bayes here: deterministic frequency-domain structural dynamics, exact small matrices.

## What the agent was allowed to choose (delegated judgment)
- Model forms (lumped TDOF replication; rigid box on 4 feet; simply supported plate as
  compliant backing), all parameter values, frequency grids, figures, GIF designs,
  PowerPoint structure.

## What remains human judgment
- Whether these teaching examples justify a follow-on study on the real ShockSat × tray
  hardware models; any durable harness/rule changes; publication/IP use of the material.

## What would make this the wrong question
- If the real decision is about a SPECIFIC flight article, a generic plate example only
  teaches intuition — the hardware-specific coupled study (already on the roadmap) is the
  decision tool. These examples deliberately trade realism for verifiable transparency.
- If test practice questions (control-system implementation, gage placement) dominate
  rather than dynamics, a hardware/test-ops reference would matter more than models.
