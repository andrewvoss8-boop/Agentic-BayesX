# ShockSat Opus Continuation — Decisions Log

## 2026-06-09 — Fork into an Opus workspace, keep Codex foundation
Decision: Start `artifacts/reports/shocksat_opus_20260609/`; reuse Codex's
provenance/inventory/MAT-loader/channel-map as-is; do not modify Codex's workspace,
checker, durable rules, or sampler standards.
Rationale: Codex's foundation is honest and correct in kind. The issue is one
quantitative claim, not the scaffolding. Forking keeps Codex's run immutable/traceable.

## 2026-06-09 — Treat the "0.07 coherence" verdict as a method artifact to test
Decision: Re-process Test07 with standard impact-FRF processing (force window +
exponential response window, one FFT per hit, ensemble H1/coherence across hits) and
re-run Codex's per-transient Welch on the same data for an explicit A/B.
Rationale: Welch segmenting inside a single transient averages mostly-no-input
segments → coherence ~0. The honest test is to process correctly and report what
changes, rather than accept the artifact as a data-quality verdict.
Result: near-resonance coherence rose from ~0.05 to 0.83–0.89; median 0.24–0.39
(weak between modes due to only 4 hits at varying points). Verdict overturned:
data carry coherent modal information.

## 2026-06-09 — Evaluate in the modal band 10–400 Hz, not the 100–10,000 Hz shock band
Decision: Judge the modal hammer FRF in 10–400 Hz against NASA SOL 111 free-free FRF.
Rationale: Test07 is a modal hammer test; NASA's correlation reference is SOL 111
(force 11101/11110, 10–400 Hz). 100–10,000 Hz is the pyro SHOCK band — wrong context
for a light hammer tap and naturally low coherence there.

## 2026-06-09 — FEM vs test = resonance-frequency alignment only (no magnitude likelihood)
Decision: Compare FEM SOL111 vs measured FRF by peak frequencies; do not overlay
magnitudes as a likelihood.
Rationale: FEM response point 1101 ≠ test grid 9900001, and SOL111 force-amplitude
unit normalization is unread. Peak frequencies are global for a free-free structure,
so frequency alignment is valid before point/unit matching; magnitude is not.

## 2026-06-09 — Recommend StatFEM v1 on the 10–400 Hz modal correlation, pyro as held-out QOI
Decision (recommendation to human, not yet built): anchor the first real-data StatFEM
update on the free-free modal correlation; keep pyro shock (unknown forcing, force-
limiting load QOI) as the downstream held-out validation = the project novelty axis.
Rationale: matches project vision (real data = trust bridge; build a validated low-
frequency twin before the harder unknown-forcing shock layer). Needs human approval
before building a posterior.
