# Assumptions Ledger — ShockSat FRF-Domain Damping Updating (20260710)

Value, units, rationale, source, sensitivity priority (H/M/L = how likely to change the S1–S4 decision). Priors
distinguish parameter uncertainty vs observation noise vs model discrepancy (AGENTS Assumptions Gate).

## Damping (the new action space)
| assumption | value / units | rationale & source | sens |
|---|---|---|---|
| measured modal damping interpretation | `damp` array = PERCENT critical damping → ζ = damp/100 | ratio reading gives ζ=32%/>100% (impossible for sharp measured resonances); percent gives ζ 0.06–1.05%, physical (D7) | H |
| band ζ prior center | 0.30 % (ratio 0.0030) | survey in-band median ζ (D7) | H |
| band ζ prior sd | lognormal, sd 0.5 (factor ~1.6) | weakly informative around survey median | M |
| band ζ hard gate | ζ ∈ [0.2 %, 5 %] | physical-damping honesty gate; a "win" outside = DISQUALIFIED (amplitude-fit in disguise) | H |
| ζ bands | 4 geom bands [45, 69.8, 108.2, 167.7, 260] Hz | equal-log width; mode counts 1/4/8/20 (D8) | M |
| Rayleigh α prior | LogNormal, center giving ζ≈0.3% at 150 Hz | classical minimal model; low-freq ζ∝1/ω | M |
| Rayleigh β prior | LogNormal, center giving ζ≈0.3% at 150 Hz | high-freq ζ∝ω | M |
| joint η_g prior | LogNormal center 0.02, ≤0.2 gate | typical bolted-joint loss factor; localized to CBUSH `joints`,`contact` (litreview §8) | H |
| inherited/baseline ζ (A0) | 1.0 % fixed | carried from completed run for continuity; ~3× survey median (documented mismatch A0d corrects) | H |

## FRF likelihood / metrics
| assumption | value | rationale | sens |
|---|---|---|---|
| band | 45–260 Hz | drive-cache support; first elastic 54.2 Hz, 33 modes in band | M |
| FRF residual on | log10|H| (magnitude) | literature §2: compare on log-magnitude, weight against antiresonance domination | M |
| global gain | ONE real dB offset per fold, from TRAIN drives only | absorbs input-level/units; NOT a per-channel/per-mode fit (anti-LSQ) | H |
| usable-channel gate | median in-band coherence ≥ 0.6 | same rule all candidates; drive caches carry coherence | M |
| FDAC form | improved cosine, real inner product ∈[−1,1] | phase-sensitive; avoids pairing 180°-out modes (litreview §2) | M |
| alignment warp | per-channel FDAC ridge ω_e*(ω_a), TRAIN-side, monotone-smoothed | frequency-shift accounting the completed run lacked | H |
| FRF observation noise σ | from (1−coherence)/coherence per line, floored | H1 estimator variance; separates noise from model discrepancy | M |

## Discretization / resolution (Gate D2 + Discretization gate)
| assumption | value | rationale | sens |
|---|---|---|---|
| frequency line spacing | ~2.0 Hz (105 lines, 45–260 Hz) | distilled caches; raw time histories deleted (no re-distillation without NASA re-download) | H |
| damping identifiability limit | HP-bandwidth 2ζf = 0.20–2.49 Hz (median 1.05) = 0.10–1.25 lines; ALL modes <3 Hz, 28/33 <2 Hz | per-mode ζ under-resolved at 2 Hz; only band-average ζ weakly constrained (D7); Gate D2 quantifies | H |
| damping ID method | FRF-BAND model-fit (fit magnitude shape over a band with ζ a parameter), NOT half-power/circle-fit per peak | 2 Hz too coarse for per-peak half-power (card §3) | H |
| not-inferred marking | any mode/band failing Gate D2 → damping NOT-inferred, reported | honest labeling of the resolution wall | H |

## Structure / model (carried from completed run, read-only reuse)
| assumption | value | rationale | sens |
|---|---|---|---|
| FEM | 406,098-DOF NASTRAN ShockSat, 80-mode reduced blocks | reused femlib; V1 reproduces blocks bit-exact | L |
| θ groups | 9 stiffness groups + fixed bush_99 | reduce_model convention (GROUPS) | M |
| θ prior | lognormal, sd 0.25 (per group) | S0-form modal posterior (D6, carried) | M |
| modal likelihood (θ_MAP) | Gaussian on paired eigenvalues, sd 5% of target | S0 convention (carried); MAC≥0.3 pairs only | M |
| pairing | frozen 1:1 Hungarian at θ=1, |df|/f>0.18 forbidden, unobservable modes excluded | carried guards (D12/D13 of completed run) | M |
| BC | free-free, 6 RBMs dropped (<10 Hz) | suspension test; first elastic 54.2 Hz | L |

## Data counts / variability
- 5 drives total: 4 dev (LODO) + 1 vault (+XY/Test04). 33-mode .ash survey. ~111 channels/drive.
- Build-to-build / test-to-test variability: NOT modeled (single article, single test campaign) — a documented
  limitation; the dev-vs-vault gap is a location effect, not a variability estimate.
- Sensitivity priority focus (H rows): damping interpretation & identifiability, ζ prior/gate, joint η prior,
  the alignment warp, and the 2 Hz resolution limit — these most plausibly flip S1/S4.
