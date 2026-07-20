# Question and decision framing

**Engineering decision being supported.** When a sensor channel fails and you reconstruct
its frequency response ("virtual sensing") to fill the gap, then update a reduced FEM
against that reconstruction, how much should you trust the *updated model's prediction on
the failed channel* — and the stiffness/damping change it implies (joint softening)?

**Objective / success metric.** The paper's own metric: log-amplitude main-peak error on
the masked channel (dB). Our added metric: held-out coverage — does the prediction's
uncertainty interval contain the TRUE (post-hoc) masked-channel response and the
masked-channel peak QOI? Calibrated coverage, not a smaller point error, is the success
criterion for the uncertainty-quantification (UQ) step.

**What the optimizer / sampler is allowed to choose.** The ROM update parameters: per-mode
modal stiffness scaling alpha, modal damping scaling beta, input-coupling gamma, and (Bayes
only) a model-discrepancy/credibility scale. Box-constrained as in the paper.

**What remains human judgment.** Whether a recovered alpha trend may be read as physical
joint softening vs an effective ROM-level indicator; how much reconstruction error is
acceptable for a maintenance decision; whether the discrepancy/credibility model matches
the real reconstruction's error structure.

**What would make this the wrong question.** (a) If the masked channel shared no modes with
the observed channels, the physics could not transfer information and the comparison would
reduce to "trust the reconstruction blindly" for both methods. (b) If the reconstruction
error were negligible, deterministic and Bayesian updates would coincide and UQ would add
nothing. (c) If the true mismatch were fully inside the alpha/beta/gamma span (no
model-form discrepancy), there would be no discrepancy to absorb and the honest-scope
caveat would not bite. The toy deliberately includes shared modes, non-negligible
reconstruction error, and out-of-span discrepancy so the question is live.
