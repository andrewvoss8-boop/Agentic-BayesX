# Root-Cause: Cursor's "interface PSD" GIF is the wrong quantity (2026-06-03)

## Symptom (human-observed, confirmed)
Cursor's interface-response-PSD GIF/figure is visibly DIFFERENT from Opus and Codex: higher in the
mid-band, and it has **no antiresonance notch**. Human hypothesis: Cursor is plotting the tray response,
not the coupled interface PSD.

## Evidence (from artifacts; Cursor source was deleted, so this is inference from curves + its own eqns)
Visual (fig 10 vs Opus gif_frames/frame_flight_10 vs Codex after_flight_03):
- Opus & Codex (two INDEPENDENT implementations, in agreement): two coupled peaks (~62, ~130 Hz), a
  DEEP antiresonance NOTCH between them (~1e-6 to 1e-7), and a FLAT high-frequency plateau (~1e-4).
- Cursor: two peaks, but only a SHALLOW dip (~1e-3.5, no deep notch), and a high-frequency ROLL-OFF
  (~1/f^2 down to ~1e-9) instead of a flat plateau. Peak point estimate 0.0265 g^2/Hz
  (results.json interface_psd_peak_g2_per_hz) vs Opus posterior-mean peaks ~0.005-0.018.

Two physics tells:
1. ANTIRESONANCE: a coupled drive-point/interface accelerance MUST show a deep antiresonance between
   adjacent modes (pole-zero interlacing for drive-point FRFs). Opus/Codex show it; Cursor does not.
   A transfer/transmissibility-type response need not.
2. HIGH-FREQUENCY SHAPE: for a FORCE-driven interface accelerance, A->1/m at high freq, so
   response_PSD ~ |A|^2 S_force is roughly FLAT (Opus/Codex plateau). A base-driven TRANSMISSIBILITY
   response (|T|^2 x input spec) ROLLS OFF ~1/f^2 above resonance (Cursor's shape).

Cursor's own equations corroborate the mix-up: packet L52 builds the vibe stage on "standalone tray
transmissibility T"; L60-61 define tray = |H21|^2 and interface = H11. A correct H11 (drive-point)
would notch. Cursor's curve behaves like a transmissibility/base-driven response, not a force-driven
drive-point accelerance.

## Most likely root cause (high confidence, not code-confirmed — source deleted)
Cursor computed the "interface response PSD" with a TRANSMISSIBILITY / base-driven formulation
(reusing its tray-transmissibility machinery, likely |T|^2 x input spec), instead of the FORCE-driven
coupled interface accelerance x flight-force PSD that Opus and Codex used. Consequences match exactly:
no antiresonance notch, high-frequency roll-off, elevated antiresonance-band levels. This is a
QUANTITY-CONTRACT vs IMPLEMENTATION MISMATCH: Cursor's stated contract says "excitation = flight force
at m1, interface (dof0) accelerance," but the produced curve is not that quantity.

This also means Cursor's narrow-band "exceedance" the human saw is an ARTIFACT of the wrong quantity
(elevated mid-band with no notch), distinct from the genuine, marginal flight-3 exceedance Opus/Codex
found at the coupled mode. Do not pool Cursor's envelope result with the other two.

## Why this matters / harness implication
- This is exactly what the Quantity-Contract gate (expected resonance/ANTIRESONANCE behavior) and a
  cross-runner curve-shape check exist to catch. Neither fired (self-graded checkers don't test curve
  shape; Cursor's source is gone so even replay can't).
- Add to the round-3 trusted checks: for any named coupled drive-point/interface FRF, assert the
  expected antiresonance (a deep local minimum between the two resonances, e.g. notch/peak ratio below
  a threshold) and cross-runner shape agreement on the same synthetic truth.

## Confirmation path (round 3)
Cursor re-runs in isolation with surviving source; require it to (a) state and plot the exact FRF used
(force-driven interface accelerance), (b) show the antiresonance notch, (c) match Opus/Codex on the
shared synthetic truth within tolerance. If the notch appears and the plateau returns, the round-2
curve was the transmissibility mix-up; if not, escalate.

## Honesty note
Source-of-truth for Cursor's exact code is gone (deleted in the earlier cleanup), so this is a
high-confidence inference from the curve shape, the cross-runner agreement of two independent correct
implementations, and Cursor's own equation hints — not a line-of-code confirmation.
