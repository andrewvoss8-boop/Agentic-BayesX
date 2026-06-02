# Log-Frequency Plot and GP Coordinate Postmortem

Date: 2026-06-01

Audience: Dr. Bilionis, lab collaborators, future Agentic BayesX agents

## What Happened

Andrew had already asked for frequency-domain transfer-function review plots to use log-scaled frequency axes. The key FRF artifact did that correctly, but later packet additions for synthetic measurement/error plots were created with linear frequency axes. The agent treated the earlier requirement as local to one plot family rather than as a project-level convention for frequency-domain review artifacts.

This was not a numerical failure. It was a requirement-propagation failure.

## Why the Agent Missed It

The failure chain:

1. The explicit log-axis request was satisfied once in `key_2dof_transfer_functions_linear.png`.
2. New plots were added later for clean-vs-observed channels, absolute error, relative error, and GP samples.
3. Those new plotting functions used Matplotlib defaults, which means linear x axes unless `set_xscale("log")` is called.
4. The review-packet checker verified file existence, embedded image links, and text snippets, but did not encode the frequency-axis convention.
5. Human review caught the inconsistency.

This is a useful agentic-workflow lesson: requirements need to become durable constraints or checkable metadata, not just remembered instructions.

## Modeling Correction

The synthetic discrepancy GP previously used a squared-exponential covariance in linear frequency:

```text
k(f, f') = sigma_d^2 exp(-0.5 ((f - f') / ell_hz)^2)
```

The workflow now uses natural log frequency:

```text
eta = ln(f)
k(eta, eta') = sigma_d^2 exp(-0.5 ((eta - eta') / ell_d)^2)
```

This makes correlation depend on frequency ratio rather than absolute Hz spacing.

## Why Log Frequency Is Reasonable Here

For broad-band structural dynamics review, log frequency is often more natural than linear frequency:

- engineers commonly inspect FRFs, apparent masses, transmissibilities, and spectra on log-frequency axes;
- modal features are often interpreted by frequency ratio and damping bandwidth rather than by a fixed Hz distance everywhere;
- a fixed 8 Hz correlation length means something very different at 20 Hz than at 150 Hz;
- log-frequency stationarity is a transparent first assumption for a toy model meant to span multiple modes.

This is not a claim that log-frequency GP discrepancy is universally correct. Real data may require mode-local discrepancy models, per-channel scaling, rational-function structure, or nonstationary kernels. The point is that log-frequency is the more defensible default for this bootstrap than linear-Hz stationarity.

## Fix Applied

- Packet channel/error/GP plots now use log-scaled frequency axes.
- The synthetic data generator uses `discrepancy_coordinate = natural_log_frequency`.
- The MCMC likelihood uses the same log-frequency squared-exponential covariance.
- Review-packet manifest metadata records the intended frequency-axis scale for key packet figures.
- The review-packet checker now verifies that metadata for channel/error/GP figures says `log`.
- `design/statfem-assumptions.md` and `docs/CODEX.md` now document the log-frequency plotting and GP convention.

## Guardrail

Future frequency-domain plots should declare:

| Field | Required value or explanation |
|---|---|
| Frequency axis | `log` unless linear Hz is justified |
| Frequency coordinate for discrepancy | `ln(f)` or documented alternative |
| Kernel coordinate units | log-frequency, Hz, modal frequency ratio, etc. |
| Why the coordinate is reasonable | short engineering rationale |
| Checker or metadata | artifact should record axis scale and GP coordinate |

## Open Questions

- Should the synthetic frequency grid itself be log-spaced for review examples, or remain linear to mimic FFT-style measurement bins?
- Should the GP be stationary in `ln(f)`, or should it be mode-local and tied to damping bandwidths?
- Should discrepancy amplitude also be relative/per-channel rather than additive in raw complex units?
