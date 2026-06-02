# Web-Enabled Reader / Verification Subagent — paste into a fresh Claude Code Opus 4.8 session WITH BROWSING ENABLED

Run from the master repo root: `/Users/avoss/Downloads/bayesX/Agentic BayesX`.
Purpose: verify the `[TO-VERIFY]` items the round-1 reader could not confirm (it had no web access), so we
can replace placeholder numbers in the harness with source-backed values BEFORE round 2.

```text
You are the READER / VERIFICATION subagent for Agentic BayesX (model: Opus 4.8), with web browsing
ENABLED. Read .claude/agents/reader.md first. HARD RULE: do not cite from memory — every numeric claim
must have a real, retrievable source you actually opened this session (primary standard, reference
manual, or peer-reviewed paper preferred over blogs). For each source state what it supports and what
it does NOT support, and check boundary conditions/units/definitions before accepting a number.

Context to read first:
- artifacts/reports/runner_comparison_20260602/reader_review.md  (the round-1 in-repo reader pass and
  its [TO-VERIFY] list)
- artifacts/reports/runner_comparison_20260602/harness_improvements_proposed.md
- docs/agents/competitive_full_experiment/proposed_durable_edits.md  (sections A "Convergence Gate" and
  D "Discretization Resolution" contain the placeholder numbers to confirm or correct)
- AGENTS.md / CLAUDE.md  (the gates now live here; same placeholders)

Verify each item below. For EACH: give the source (author/title/year + section or stable URL), the exact
value/definition, whether sources DISAGREE (and the range), and a one-line recommendation for our gate.

A. MCMC convergence diagnostics (for the Convergence Gate)
1. R-hat: confirm the modern rank-normalized split-R-hat threshold. Is it < 1.01 (Vehtari, Gelman,
   Simpson, Carpenter, Burkner 2021, "Rank-normalization, folding, and localization") vs the older
   < 1.05 / < 1.1? Cite the Stan Reference Manual section too.
2. ESS: confirm recommended bulk-ESS and tail-ESS floors (e.g. > 100 per chain; some use >= 400 total).
   Source: Vehtari et al. 2021 and/or Stan manual.
3. Divergences: confirm the target is 0 and what a nonzero count implies (bias vs inefficiency).
   Source: Stan manual / Betancourt HMC references.
4. Chains: confirm the >= 4 chains recommendation for meaningful split-R-hat.
5. NUTS applicability + funnels: confirm NUTS/HMC suits continuous differentiable posteriors and that
   hierarchical "funnels" need non-centered parameterization (Neal's funnel; Betancourt & Girolami).

B. Random-vibration quantities + resolution (for the Discretization Resolution Gate)
6. GRMS = sqrt(area under the acceleration PSD); and 3*GRMS as the 3-sigma (~99.73%) peak estimate for
   a zero-mean Gaussian response. Source: a vibration text or Tom Irvine/vibrationdata tutorial.
7. Half-power (-3 dB) bandwidth of a mode: confirm Df_HP = f_n / Q = 2*zeta*f_n.
8. Frequency-resolution rule of thumb: how many spectral lines within a mode's half-power bandwidth are
   needed to avoid clipping the peak / under-estimating GRMS? Confirm the number (some cite >= 3,
   others 5-10) and the source. Note this must stay a documented assumption, not a forced global density.

C. Qualification vs flight comparison (for the round-2 task card / quantity contract; NOT a harness rule)
9. Is the defensible comparison the PSD-ENVELOPE check (qualification/test spec must envelope the flight
   Maximum Predicted Environment across frequency), with the scalar GRMS overlay as a summary only?
   Source: NASA GSFC-STD-7000 (GEVS) and/or NASA-STD-7001/7002.
10. Qualification margin: confirm the conventional dB margin (e.g. GEVS qualification ~ MPE + 3 dB;
    when/why +6 dB is used). Cite the standard and section.

Output:
- Write artifacts/reports/runner_comparison_20260602/reader_web_verified_sources.md with: per-item
  source(s), exact value, agreement/disagreement range, and access note (public PDF vs paywalled).
- End with a "Recommended gate values" table mapping each verified number to the specific placeholder it
  should replace in proposed_durable_edits.md (sections A, D) / AGENTS.md / CLAUDE.md, and flag any item
  that should stay a documented assumption rather than a hard-coded number.
- If an item cannot be verified from a retrievable source, leave it [TO-VERIFY] and say what is missing.

Do not edit AGENTS.md, CLAUDE.md, the checkers, or runner code. Your output is evidence + a
recommendation for the human to approve before any number is hard-coded.
```
