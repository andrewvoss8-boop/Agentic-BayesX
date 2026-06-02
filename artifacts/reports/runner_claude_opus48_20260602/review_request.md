# Review Request — what to scrutinize

Please check these before trusting the packet.

1. **Flight likelihood scope.** I used only the scalar 3*GRMS flight observations (that is all the
   dataset stores). Is folding the fixed 3 dB forcing + sensor scatter into a single fixed
   `sigma_qoi` (tray 0.197 / iface 0.150 ln-units) acceptable, or should the realized forcing GP
   be reconstructed/inferred per flight? See `known_failures.md` items 1–2.

2. **Fixed-vs-learned boundary.** Confirm I kept the right things fixed: flight-to-flight = 3 dB
   (fixed), build-to-build and sensor noise (learned). See `assumptions_ledger.md`.

3. **Modal log-magnitude likelihood.** The generator scales complex FRF magnitude only (no phase
   noise), so I used a log-magnitude likelihood. Is that the intended reading of the setup, or was
   complex real/imag intended?

4. **Soft-argmax peak features.** `beta=45` soft argmax for differentiability vs hard observed
   features. Is the soft/hard mismatch small enough for a fair full-vs-peak comparison? Would you
   prefer a fixed-frequency-band amplitude feature instead?

5. **Peak model cannot learn sensor noise** (posterior≈prior). I reported this as a finding rather
   than tuning it away. Agree this is the correct interpretation?

6. **QOI definitions.** "tray 3*RMS" and "tray 3*GRMS" are numerically identical here (RMS in g =
   sqrt of PSD integral). I report structural-posterior QOI and future-build-flight predictive QOI
   separately. Confirm the predictive (new build) is the decision-relevant one, and that the
   wider-than-prior predictive is understood (item 8 in known_failures).

7. **Overfit-to-synthetic caveat.** Inference uses the same parametric model that generated the
   data (no model-form error), so recovery is unrealistically clean. Is a model-discrepancy
   stress test wanted as a follow-up?

8. **Checker strength.** `tests/test_runner_claude_opus48_full_experiment.py` checks file
   existence, NUTS diagnostic presence + thresholds, truth-in-CI for the full model, and
   peak-wider-than-full QOI. It does NOT encode the physics (limiting behavior, resonance
   locations). Suggest additional automatable physics checks.
