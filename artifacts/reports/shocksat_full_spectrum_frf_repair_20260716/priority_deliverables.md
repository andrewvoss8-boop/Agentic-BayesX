# Priority deliverables

1. Correct exact arm means and fold standard errors from the saved per-fold scores.
2. Recompute finite S1/S2 paired statistics.
3. Restore the pre-registered arm-F identity, F=C, without treating random control as a deliverable arm.
4. Add a SHA-locked checker that rejects NaN/null statistics and arm-method mismatch.
5. Preserve and verify the reviewed study inputs byte-for-byte.

Acceptance: no reviewed file changes; no new science compute; repaired checker has no RED; all limitations remain explicit.
