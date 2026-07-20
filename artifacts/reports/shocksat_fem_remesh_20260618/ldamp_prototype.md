# ldamp_prototype.md — L-damp prototype (b) result (PRELIMINARY)

Non-proportional (interface-localized) damping in the held-out FRF vs uniform ζ=1%, at the 8 hard channels.
Reproduces from `code/ldamp.py` → `out/ldamp_prototype.json`. Reuses (COPY) the validation study's 74×74
reduced model + measured complex FRF cache + channel mapping.

## What it does
- Damping `C = α₀M + α₁K + Σ_g β_g A_g`; light-damping per-mode `ζ_k = α₀/(2ω_k) + α₁ω_k/2 + Σ_g β_g ω_k f_{k,g}/2`;
  FRF denominator uses PER-MODE `η_k = 2ζ_k` (non-proportional) instead of one η.
- (α₀,α₁,β) fit (NNLS) to the measured per-mode ζ̂ (`.ash`, ÷100). ONE global log-gain (can't absorb
  per-channel variation). Metric: held-out peak |H| error at the 8 channels, before(uniform 1%)/after(non-prop).

## Result: preliminary NEGATIVE — and the run did NOT fairly test the key hypothesis
| | mean |peak-error| (log) | channels better |
|---|---|---|
| before (uniform ζ=1%) | 1.498 | — |
| after (non-proportional ζ_k) | 2.184 | **1 of 8** (only ch52, the bolted joint) |

- The fitted `ζ_k` range came out **0.075–0.77%, all BELOW the 1% baseline**, and the localized β collapsed to
  ~0 (NNLS preferred Rayleigh α₀/α₁ in the reduced basis). So this run effectively LOWERED damping everywhere
  rather than RAISING it on the bulkhead modes — i.e., it did **not** test the actual hypothesis from
  `damping_indicators.md` (that the 107–122 Hz bulkhead/cross drum modes are *more* damped, ζ up to 1.76%, which
  would *lower* their peaks). Two reasons, both honest caveats:
  1. **ζ-target units (D8 caveat):** used `.ash damp ÷100` (range 0.06–1.05%), not the authoritative free-free
     **xlsx** values (0.12–1.76%, where the bulkhead bump lives). The bulkhead over-damping is in the xlsx, not
     the `.ash` array used here.
  2. **Basis mismatch:** the identifiability gate found localized β *is* identifiable in the full-order V_keep
     basis (top_box 32% etc.), but in this 74×74 reduced basis NNLS degenerated to Rayleigh-only. The reduced
     A_g modal-strain projections differ enough that the localized lever vanished.

## CORRECTION (Andrew, 2026-06-19): do NOT read this as "it's shape not damping"
An earlier version of this file concluded the residual is "shape not damping" on an order-of-magnitude argument
("damping only moves a peak by ~factor 2"). **That argument is WRONG and is retracted.** The measured ζ spans
**0.06%–1.76% (factor ~30)**, so per-mode damping CAN produce factor 2–25 amplitude swings. Damping is therefore
**not** ruled out by this prototype — and the prototype's negative is confounded by its degenerate fit (β→0,
wrong ζ target), so it does not cleanly test damping either way.

**The real resolution — participation and damping are confounded at a single impact.** The resonant peak is
`|H_peak| ∝ φ_{s,k}·φ_{d,k} / ζ_k` (modal participation ÷ damping). A wrong peak amplitude is explained EQUALLY
by wrong participation or wrong damping, and **a single drive point cannot separate them.** This is why BOTH the
Card-D shape/re-mesh attempts AND this damping prototype are inconclusive — not because the answer is "shape" or
"damping," but because the single-impact data is **under-determined** on exactly this trade-off.
- ch52 (bolted joint) improved, 7/8 worsened — but with a degenerate fit this pattern carries no clean signal.
- The lever that breaks the confound is **multi-reference / roving-hammer data**: a second drive node varies
  `φ_{d,k}` while `ζ_k` is fixed, separating participation from damping. (Consistent with Card A's
  data-limited bands and the Card D "spend the next test dollar on data" conclusion.)

## Honest status + what a CLEAN L-damp needs next
This is a **preliminary** prototype, not a finished result. To make it a fair test of the over-damped-bulkhead
hypothesis it needs: (1) the **authoritative xlsx ζ** (with the 1.76% bulkhead bump) as the calibration target;
(2) the **V_keep-basis localized β** (gate-consistent, so the localized lever doesn't degenerate); (3) the
**complex-eigenvector** calibration (Das–Debnath quadratic eig) rather than the light-damping per-mode
approximation; (4) the **Schneider complex (magnitude+phase) held-out likelihood**. **Honest status: this
prototype does NOT establish that damping fails — its negative is confounded by a degenerate fit AND by the
single-impact participation/damping degeneracy.** Even a clean L-damp on one impact will hit that degeneracy: it
can fit the data either by adjusting participation or by adjusting ζ, with the same likelihood. The decisive
experiment is **multi-reference data** (which breaks the confound), not a better single-impact fit. **Surfaced to
Andrew: (i) run the clean single-impact L-damp anyway (will likely confirm the confound — an honest "can't
separate" finding), or (ii) recognize the single-impact ceiling now and close the thread on the
multi-reference-data conclusion?**
