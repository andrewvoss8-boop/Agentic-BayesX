# Assumptions ledger — Study A (executed). Synthetic; one realization.

All values are synthetic and chosen to exercise the discrepancy lever; they are NOT a real structure.
Distinguish: parameter uncertainty (priors), observation noise (iid), model discrepancy (Schneider error),
model-form error (hidden 3rd DOF). Forcing-LEVEL cancels in apparent mass M=F/a (no forcing prior needed).

| Symbol | Meaning (unit) | Value | Role | Source / rationale | Sensitivity priority |
|---|---|---|---|---|---|
| m1,m2,m3 | source/load/hidden masses (kg) | 1.0, 0.6, 0.25 | TRUTH (3-DOF) | source/load split from `src/twodof` defaults; m3 = the hidden DOF the 2-DOF FEM omits | high (model-form) |
| f1,f2,f3 | uncoupled nat. freqs (Hz) | 110, 75, 220 | TRUTH | `src/twodof` defaults; f3 high → hidden mode just past band edge | high |
| ζ1,ζ2,ζ3 | damping ratios (–) | 0.015, 0.020, 0.03 | TRUTH | light structural damping | med |
| Nf | frequency lines (–) | 56 log-spaced 30–200 Hz | grid | dense FRF (Schneider use-case); resolves both coupled peaks | med (discretization gate) |
| nmp | spatial measurement points (–) | 2 (drive + cross) | grid | minimum to exercise R_zz space block | low |
| σ_w* | injected log-magnitude error sd (–) | 0.12 | INJECTED discrepancy | Schneider CLT posterior σ_w≈0.31; we use smaller | high |
| σ_θ* | injected phase error sd (rad) | 0.10 | INJECTED discrepancy | Schneider posterior σ_θ≈0.31; smaller here | high |
| ℓ_f* | injected freq correlation length (Hz) | 18 | INJECTED discrepancy | Schneider posterior ℓ_co,f≈10 Hz; OFF the V2 prior mean on purpose (anti-rig, D-A wrong-question) | high |
| r* | injected space/freq split (–) | 0.8 | INJECTED discrepancy | Schneider posterior r≈0.82 | med |
| σ_iid | iid complex obs noise sd (rel.) | 0.03 | observation noise | small sensor noise floor | med |
| extra | non-multiplicative additive term | 1.5% of median |M| | INJECTED | breaks the "exactly Schneider" assumption (anti-rig) | high |
| prior k1,k2,k12 | log-normal sd on stiffness (–) | 0.18 | PRIOR | matches `fresh_2dof` prior; ~±9% on freq | — |
| prior ζ | log-normal sd on damping (–) | 0.35 | PRIOR | matches `fresh_2dof` | — |
| V2 hyperpriors | σ_w,σ_θ ~ LogNormal; ℓ_f ~ LogNormal(mean≈10 Hz); r ~ Uniform(0,1) | — | INFERRED | Schneider Table 1 shapes; ℓ_f prior mean deliberately ≠ injected 18 Hz | high |
| held-out band | excluded freqs (Hz) | top 25% of band (≈157–200 Hz) | trust split | contiguous high-band holdout = honest extrapolation test (vision §7) | — |
| NUTS | chains / warmup / samples / target_accept | 4 / 1000 / 1000 / 0.9 | sampler | AGENTS convergence gate; non-centered hyperparameters | — |

Inferred: k1,k2,k12 (→ f1,f2,coupling), ζ1,ζ2, and (V2 only) σ_w,σ_θ,ℓ_f,r.
Fixed / not inferred: masses (known), nmp, Nf, the hidden 3rd DOF (that is the model-form error, unmodeled
on purpose), forcing level (cancels in M=F/a).
Limitation: ONE synthetic dataset, ONE realization; no flight/build/test-to-test variability modeled.

---
# Study G assumptions (unified modal statFEM, realistic synthetic panel twin)

| Symbol | Meaning (unit) | Value | Role | Rationale | Sens. priority |
|---|---|---|---|---|---|
| grid | panel nodes | 8×5 = 40, dx=0.1 m (0.7×0.4 m, 2.0 kg) | mesh | LDV-scan-like; ~real panel scale | low |
| truth d(x,y) | bending field | 1 + 0.18·sin·cos + 0.10·linear; ×0.62 patch (4 nodes) | TRUTH model-form error | smooth heterogeneity + local damage; UNREPRESENTABLE by the 4-quadrant FEM | high |
| suspension | cable springs | 1.15·ks, 0.90·ks at 2 top corners (truth); 1.0·ks (FEM) | TRUTH error | uneven cables | med |
| damping truth | Rayleigh + dashpot | a0=0.55, a1=4e-5, c_dash=1.3 at a patch node | TRUTH (NON-proportional) | in-band ζ 0.5–1.1% with mode-to-mode spread | high |
| mass loading | drive-side added mass (kg) | +0.008 at drive node (truth only) | TRUTH error | shaker/stinger loading | med |
| floor | additive noise floor | med|H|·2e-3 | measurement | matches REAL panel min/med ≈ 2.3e-3 | med |
| gains | per-point calibration (dB) | N(0, 0.5 dB), generation only | measurement | transducer scatter; absorbed by σ_w in inference | low |
| mult. noise | complex sensor noise | 2% | measurement | LDV-ish | low |
| bands | generation / inference (Hz) | 2–100 @0.125 / 10–60 @0.125 | grids | low-f junk excluded like the real panel's <8 Hz | med (documented) |
| points | scan / observed / held-out | 20 / 15 / 5 (corner, centre, edge×2, IN-PATCH) | split | held-out QOIs at never-measured nodes | — |
| NM, B | latent modes / Ritz basis | 13 / 17 | model | nominal modes ≤80 Hz; B=NM+4 margin | med |
| priors | s_g LN(0,0.2); s_susp LN(0,0.3); a0,a1 LN(nom,0.7); δ LN(nom gaps,0.25); ζ LN(0.01,0.7); c N(e_m,0.3)+iN(0,0.1) | — | priors | centered at nominal FEM | — |
| τ | eigen-residual looseness | 0.004 + LN(0.03, 0.8), inferred | statFEM lever | floor bounds the needle (documented) | high |
| σ_w,σ_θ,ℓ_f,ℓ_z,κ | discrepancy hypers | all inferred (LN priors) | Schneider layer | see method_ums.md | high |
| NUTS | headline / frames | 4×(800+800) ta=0.85 mtd=9 / 2×(300+300) | sampler | frames labeled reduced | — |
| QOI gate | held-out coverage | ≥8/10 of 95% CIs (A: peak |H|; B: band RMS at 5 nodes) | trust gate | nominal 95% w/ small-sample slack | — |

Inferred: 4 s_g, s_susp, a0, a1, 13 δ, 13 ζ, 13×17×2 c, τ, σ_w, σ_θ, ℓ_f, ℓ_z, κ (= 481 dims).
Fixed/not inferred: M (mass), basis Φ0, the truth's patch/dashpot/mass-loading (the model error), gains.
One dataset, one realization; no test-to-test variability (stated limitation).
