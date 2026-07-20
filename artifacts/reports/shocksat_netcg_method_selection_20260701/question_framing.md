# question_framing — Question & Decision Gate

**Engineering decision.** An aerospace partner hands us an inherited (vendor-correlated) ShockSat FEM + a
modal-hammer test set and wants the **net-CG FORCE on the top tray/plate**, in BOTH directions, with trustworthy
uncertainty bands, under a known flat input PSD. We must pick — PER QOI — the ONE Bayesian-updating method that
delivers a band we can stand behind, and hand back shear + normal net-CG force predictions with a trust label.

**Objective / success metric (two-part selection rule, per QOI).**
1. COVERAGE is a HARD GATE: the twin's 95% band, 1-octave-smoothed, must envelope the held-out-reconstructed QOI
   (narrow exceedances tolerated as energy-weighted positive dB-exceedance). A method that fails coverage OR that
   is overconfident on the leave-modes-out test is DISQUALIFIED for that QOI, no matter how sharp.
2. Among covering methods, prefer the SHARPEST (then lowest point error).

**What the search MAY choose:** the updating formulation, the remesh candidate (from the screened top ~3), the
parameter/pooling set.

**What stays HUMAN judgment:** the input-PSD assumption (flat, level); the acceptable band width for
certification; and whether the normal-QOI band is delivered as a usable screening bound or flagged "needs new data".

**What would make this the WRONG question:** if the partner actually needs a LOCAL mount/component response (not
the NET tray force) — that is the ~14.6x wall (reproduced here as `mount_response` 13% trust / 14.6x band) with no
statistical rescue. We would say so and stop chasing sharpness there.

**Binding design requirement (Andrew).** The selected method must be robust to QOIs driven by modes outside its
optimal range: it must NOT get "sucked into" falsely sharpening the unmeasured-mode-driven (normal) QOI by
overfitting the data-rich measured band, and it MUST communicate the true (wide) uncertainty there. This is why
coverage + leave-modes-out is the hard gate and sharpness is only rewarded where earned.

**Held-out is the only trust arbiter.** In-sample metrics (e.g. the `correlate_all` FRF-corr) are known artifacts
(§1.1) and are NEVER used to rank. One unified candidate pool, one harness. Convergence != trust (NUTS all-variable
gate is necessary but the held-out + leave-modes-out gates decide).
