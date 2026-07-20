# Decisions log — time-domain latent-force damping/residual diagnostic

Workspace: `artifacts/reports/shocksat_latent_force_damping_20260623/`. Runner = lead-as-runner (Andrew dispatched
`docs/lab/shocksat_latent_force_damping_runner_prompt.md`). Re-grounded from AGENTS.md (all gates), notes/memory.md
CURRENT STATE, the D22 damping_inference (0/9), the live PSD-envelope twin contracts/D7, and realfrf machinery.

## D0 — Re-grounding statement (one line)
GOAL: do clean modal-hammer ring-downs (time domain) resolve per-mode ζ that D22 (single windowed FRF, freq, 0/9)
could not; decompose a latent MFE force into damping-vs-residual; does measured ζ move the held-out PSD-envelope GRMS.
Inherited: reuse the PSD-envelope QOI byte-identical; D7 already found the envelope-GRMS win is a per-node-shape-error
honest negative. Open ambiguity flagged up front (D2 below).

## D1 — Integrity baseline FIRST
Reproduced D22 by running the inherited `damping_inference.py` on the cached Test07 windowed FRF → **0/9 identified**
(`out/d22_reproduction.json`, n_identified=0). This is the bar to beat before any improvement claim.

## D2 — KEY PRE-FLIGHT FINDING (surfaced): the FEM is OVER-damped, so the prompt's bridge is SIGN-FLIPPED
The runner prompt's bridge assumes the FEM is UNDER-damped (ζ too light → FEM+6 dB over-conservative → measured ζ
lowers the twin). But realfrf.ZETA_NOM = **1.0%** structural is HEAVIER than the .ash modal ζ (0.25–0.44%) and than
the measured ring-down ζ (~0.4%). So the FEM is OVER-damped: correcting ζ toward the measured value RAISES the twin's
peaks and RAISES its envelope GRMS (MORE conservative). Decision: do NOT assume the lever direction — quantify it with
the finite-perturbation check, and report the sign honestly. (Confirmed: see D6.)

## D3 — Data: build TIME-DOMAIN ring-down caches (the inherited caches are frequency-domain FRFs)
Built decimated (250 kHz → 2.5 kHz, zero-phase FIR) time-domain caches from the clean modal `.mat` (already extracted
in the psd_envelope workspace; 5.6 GB). 4 refs × 6 hits × 111 channels; 1 s records, impact ≈500 ms, ring-down ≈500 ms.
Caches `data/ringdown/*.npz` ≈ 6 MB each (24 MB total) — self-contained for replay. fs/pre-trigger/units verified by
`probe_mat.py`. Force peak 416–805 lbf; post/pre SNR median 4–25.

## D4 — Layer 1 method: band-pass + analytic-signal log-decrement (transparent) + hierarchical NUTS posterior
- Deterministic: per (mode, ref, channel, hit) band-pass + Hilbert envelope + weighted log-linear fit → ζ; bootstrap
  CI over accepted traces. **14/16 union modes RESOLVED** (CI < ½ prior, interior, ≥8 clean traces).
- Bayesian: hierarchical NON-CENTERED NUTS (zeta_pop + per-trace zeta_i = zeta_pop·exp(s_between·z_i); ζ enters
  nonlinearly through exp(−ζ·2πf·t); prior LogUniform[0.05%,6%] = D22 bounds). **14/16 converged** (R-hat ≤ 1.020,
  ESS ≥ 250, 0 divergences); ζ ≈ 0.33–0.76% (median ~0.45%), consistent with .ash. The shared-ζ pooling was upgraded
  to hierarchical because it gave an implausibly tight CI (ignored between-channel heterogeneity = a Layer-2 signal).
- Sampler labeling: the NUTS posterior is over ζ (nonlinear); the Layer-2 Kalman smoother is a FILTER, not NUTS.

## D5 — Frequency-domain CONTROL on the clean data (isolate domain vs data quality) — honest nuance
Ran the D22-style width fit on the CLEAN modal caches (df=2.03 Hz): **7/16 identified**. So clean multi-hit data
helps even in frequency (0→7); the TIME domain adds the light/sub-bin-width and clustered modes (7→14). Decision:
do NOT claim "the domain is magic" — report both levers; the time domain's specific gain is the sub-bin modes.

## D6 — Finite-perturbation (Layer-1 gate) result: ζ is an ABSOLUTE lever but CANCELS in the win ratio
`finite_perturbation.py`: envelope GRMS scales ~1/ζ (a strong absolute lever → ζ passes the "is it a lever" gate),
BUT the twin/FEM+6 dB win RATIO is INVARIANT to ζ (spread = 1.0000) because the inherited contract uses the SAME
damping for FEM and twin (common-mode → cancels; mirrors D8's "channel-common → gain-absorbed"). And measured ζ (0.4%)
< FEM nominal (1%) → measured-ζ twin is MORE conservative. So damping is NOT a lever on the inherited win metric.

## D7 — Layer 2: latent force is dominantly a damping correction; little nonlinear residual (caveated)
RTS Kalman smoother (FILTER) per-mode latent modal force; velocity-projection recovers ζ_true cross-checking the
log-decrement (corr ~0.82) and Layer-1 NUTS. The MFE is dominantly a viscous DAMPING correction (FEM over-damped);
the non-viscous residual shows no amplitude dependence (residual-vs-q² corr ~0.03) or non-exponential decay
(early/late-ζ ratio ~1.08). CAVEAT: the raw latent-force variance split (damping vs residual fraction) is process-noise
(q_g) and close-mode-beating contaminated, so the q_g-robust velocity-projection ζ + the cross-check are the headline,
not the variance fraction. (Free-decay GPLFM is weakly identified for the split — documented.)

## D8 — Layer 3: HONEST NEGATIVE confirmed with the real pipeline
`layer3_value.py` (reuses probe.fit_context byte-identical, 90% split, NUTS calib converged): combined-correlated
median GRMS ratio A(nominal)=12.4, B(measured-ζ, identical η)=11.0 ≈ A (ζ cancels), C(measured-ζ twin vs nominal
FEM+6 dB)=14.3 ≥ A (FEM over-damped → worse). All framings 0% win. Binding limit = per-node FEM shape error (twin
97.5 band ~+27 dB), exactly D7. Damping does NOT buy a less-conservative envelope on this structure.

## D9 — Disk discipline (deviation from the prompt's blanket "delete raw .mat and zips", surfaced)
My time-domain caches (24 MB) are self-contained for replay. The raw modal `.mat` (in the psd_envelope workspace,
5.6 GB) and the root-level zips (3.9 GB, Andrew's downloads) are SHARED/owned resources; I did NOT delete them
unilaterally (disk at 14 GB free, not critical; deletion is destructive and the data is re-downloadable from the public
NASA delivery). Flagged for Andrew: safe to delete if disk pressure arises. `cache_builder.py` documents the one-time
data-prep step (requires the raw `.mat`); `run_all.sh` replays the ANALYSIS from the saved caches.

## Guardrails honored
No durable-rule / checker-standard / sampler-standard / project_log / project_vision edits; only this workspace + the
lead CURRENT STATE block in notes/memory.md. The result tiers, the sign-flip finding, and any QOI/standard implications
are surfaced for Andrew, not self-applied.
