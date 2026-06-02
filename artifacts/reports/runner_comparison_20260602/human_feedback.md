# Human First-Pass Feedback — 2026-06-02

The human reviewed Codex and Opus (cursory), not Cursor. This drives the round-1 reviews and the
next iteration. Captured verbatim, then structured.

## Verbatim

> codex gave a total runtime of 18 min. Others did not track runtime for the runner. We should make
> sure we get that tracked for each runner in the next iteration.
>
> Codex and Opus did not make the key plots I wanted -> the mean, 95%, and 99% confidence interval
> interface accel PSD (in the coupled system) graphed vs the original test spec after each flight.
> Or I can't find that graph. A GIF here would be excellent, showing how that graph changes with
> each flight. They plotted the forcing function, which is fine, but not the main graph I was
> looking for and thought I asked for. I'd like to see all 10 samples compared with the original
> +6dB one as well.
>
> many graphs showed the 3rms tray scalar, but did not compare it with the rms value from the
> original vibe test like I requested.
>
> On the sequential_observations_truth_vs_observed graph from codex, I noted 2 issues. The sparse
> sampling along the freq band in the top left graph was such that the peak of the tray response was
> clipped and not fully revealed. This may have been an issue elsewhere. How did each runner decide
> which frequency spacing to use, and did any consider the effect this would have on the results?
> This is an area for us to give attention for its relevance in this class of problems, which are
> very sensitive to the choice of frequency spacing.
> On that graph as well, the bottom left has no legend. But it seemed like a very important graph!
> all graphs should have legends.
>
> Finally, I noticed some issues with NUTS. Agents took different approaches, it wasn't clear when
> NUTS was or wasn't the right choice. Handling of this decision making by each agent should be
> investigated and given close attention for our top level work on harnesses, skills, and hooks.

## Structured action items

### A. Runtime tracking (harness, next iteration)
- Every runner must record wall-clock runtime (total and per-stage) in a machine-readable field.
- Only Codex reported runtime (~18 min, human-reported). Opus recorded "~2m48s" for the sampler
  step in commands.md but not a tracked total. Cursor recorded no runtime.

### B. Missing KEY plot (this is the headline deliverable gap)
- Wanted: mean + 95% + 99% CI of the **coupled-system interface acceleration PSD**, plotted
  **against the original test spec**, **after each flight** — ideally an animated GIF across flights.
- Also wanted: all 10 flight forcing samples shown together vs the original +6 dB forcing.
- None of the three produced this. Codex/Opus/Cursor each produced a single "input spectra + QOI"
  static figure, not the per-flight evolving interface-PSD-vs-spec view.

### C. QOI comparison gap
- Many plots show the tray 3*RMS / 3*GRMS scalar but do NOT overlay the original vibe-test RMS
  (setup: first-build vibe 3*GRMS = 43.9 g, smoothline = 28.3 g) for direct comparison.

### D. Frequency-spacing sensitivity (flagged as important for this problem class)
- Investigate how EACH runner chose frequency spacing, and whether any considered its effect.
- Codex top-left tray peak appears under-resolved by coarse spacing (peak possibly clipped).
- This problem class is highly sensitive to frequency-grid choice; make it a first-class assumption
  + sensitivity item next iteration.

### E. Plot hygiene
- Every graph must have a legend. Codex bottom-left (first flight input/tray, dual y-axis) has none.
- Use log frequency axes (already a gate) and check for clipped resonance peaks.

### F. NUTS decision quality (top-level harness/skills/hooks focus)
- Runners diverged: Opus = real NUTS (4 chains, converged marginals); Cursor = real NUTS but 2
  chains, non-converged latents; Codex = custom PyTorch HMC, not NUTS, non-converged scales.
- It was not clear when NUTS was/wasn't the right choice, nor what "good enough" convergence is.
- Needs explicit guidance + a convergence gate (see harness_improvements_proposed.md).

## Human process notes
- The review is collaborative; the human will answer questions and steer the next iteration after
  the four subagent reviews finish.
- The human has not reviewed Cursor's outputs at all yet.
