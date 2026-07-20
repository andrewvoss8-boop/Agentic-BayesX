# damping_modeling_review.md — modeling complex / non-proportional damping with Bayesian updating

Review (Andrew's ask, 2026-06-19) of three papers for HOW to model the non-proportional ("complex") damping
we found localized at the ShockSat joint/bulkhead interfaces (`damping_indicators.md`), and how to fit it with
Bayesian updating — possibly with Schneider's complex-FRF likelihood. Per AGENTS Reference Gate: each idea is
mapped to OUR data/infrastructure, with an honest feasibility + identifiability assessment. **No code built
yet — this is a design review.**

Papers:
- **[DD20]** Das & Debnath 2020, *A Bayesian model updating with incomplete complex modal data*, MSSP 136:106524.
- **[K25]** Kiran, Das, Bansal 2025, *State-of-the-art review of Bayesian FE model updating*, Prob. Eng. Mech. 80:103761.
- **[S22]** Schneider, Papaioannou, Straub, Winter, Müller 2022, *Bayesian parameter updating … frequency
  transformed data using rational surrogate models*, MSSP 166:108407.

---

## 0. Why this is the right next step (ties to our finding)
Our authoritative measured damping is **non-proportional and interface-localized**: ζ spans 0.12–1.76% (14×),
and the most-damped modes are the **Al/steel bulkhead + cross "drum modes"** (122 Hz 1.76%, 118 Hz 0.83%, 107 Hz
0.51%) vs ~0.3% for plain panel modes. A single global ζ is wrong in *both* directions. This is precisely the
case all three papers say is (a) common in real structures and (b) under-addressed.
- **[K25] §4.3.2 + §8(a) name this as the open research gap verbatim:** "most works utilize real-valued modal
  data and avoid non-classical damping… real-life structures show… complex modes rather than real modes… very
  few works utilize complex modal data… leaving a gap in practical implementation on real-life large
  structures." ShockSat (a real spacecraft with measured interface-localized damping) is exactly that testbed →
  strong Ilias "identify-gap + improve" framing.
- **[S22] hit our exact symptom:** with a single global hysteretic damping η=2ζ on a CLT plate, "eigenfrequencies
  are recovered well, whereas amplitudes are not well predicted around the eigenfrequencies… we would have to
  INCREASE the damping ratio to explain the amplitude for some eigenfrequencies, whereas the damping ratio would
  have to be DECREASED to obtain the measured amplitude at others. This cannot be achieved by a single damping
  ratio." Schneider's *workaround* was to ABSORB the misfit into a correlated model-error σ_w (≈0.31, ×2.7) —
  the same ×2.7 amplitude ceiling we hit. The opportunity: **model the damping physically instead of absorbing it.**

---

## 1. [DD20] — the damping-update machinery (the core method to adopt)
**What it gives us:** a Bayesian (MAP) FE updating that infers **mass, stiffness AND damping** from **incomplete
complex modal data**, with BOTH classical (Rayleigh) and non-classical (viscous) damping, WITHOUT mode-matching
and WITHOUT a full eigensolve per iteration.

Key constructs (map to us):
- **Parameterized damping matrix (Eq 3):** `C(θ3,α0,α1) = C0 + Σ_g θ3_g C_g + α0 M(θ1) + α1 K(θ2)`.
  - `α0 M + α1 K` = Rayleigh (proportional) part → gives the smooth frequency-trend of ζ.
  - `Σ_g θ3_g C_g` = **non-classical, LOCALIZED viscous dampers** → exactly where we put dampers at the
    bulkhead/bolted-joint/cross interfaces we already identified. The `C_g` blocks live on the joint CBUSH DOFs
    (PBUSH 801–807) and the bulkhead-to-wall rings — the same per-PID block structure our assembler already has.
- **Complex eigenvalue (Eq 18):** `λ_m = −ζ_m ω_m + i ω_m √(1−ζ_m²)`. **We already have this from `.ash`:**
  measured ω̂_m (33 modes) + measured ζ̂_m (0.12–1.76%). So the measured *complex eigenvalues* are in hand today.
- **Quadratic eigenvalue equation (Eq 19):** `(λ_m² M + λ_m C + K) Ψ_m = 0` — the damped eigenproblem. The
  modeling-error residual (Eq 20) inserts the MEASURED λ̂_m and the (inferred) system shape Ψ_m; real & imaginary
  parts separated and Gaussian (Eqs 24–27).
- **Mode-matching-FREE:** the system complex mode shapes `Φ = [Re(Ψ); Im(Ψ)]` are treated as **inferred
  parameters** (not FEM eigvecs). This is the SAME trick that fixed our Sim-B eigvec-gradient pathology (our D22
  Beck L8b: R̂ 1.004, 0 div, where the FEM-eigvec amplitude likelihood gave 174 divergences). So [DD20] is
  NUTS/MAP-friendly for the same reason L8b was.
- **Efficiency:** sequential closed-form MAP updates (Eqs 35/42/48/54/60/66), Hessian → posterior covariance
  (uncertainty). Cheaper than Gibbs (their Tables 1–2: COV much lower than Gibbs at equal accuracy).

**Adoption for ShockSat:** build `C(θ) = α0 M + α1 K + Σ_g θ3_g C_g` with `C_g` on the joint/bulkhead groups;
project to our reduced modal basis `V_keep` (~80 modes) so the quadratic eig is a cheap 160×160 state-space
problem, not 400k DOF. Infer (α0, α1, θ3_g, σ) from the measured complex eigenvalues (ω̂, ζ̂) — i.e., **fit the
measured per-mode damping spread with a localized C** and ask: does interface damping reproduce ζ 0.12→1.76%?

## 2. [K25] — the map of options + the identifiability warning
- **§4.3.2 catalog** places [DD20] among the few complex-data methods (Cheung&Bansal Gibbs; Bansal&Cheung Caughey;
  Henikish model-reduction). Confirms the **mode-matching-free / eigen-equation** family (Yuen Eq 29, Ching Eq
  31–32, Yan-Katafygiotis multi-setup Eq 33–36) is the established route — our Beck L8b is already in this family,
  so extending L8b to carry a damped eigen-equation is the minimal step.
- **Identifiability (§3.2, Fig 1):** global vs **local** vs un-identifiability. Our whole-FRF multimodality (Card A
  R̂ 104–129) IS their "local identifiability" picture. LESSON: a damping update with too many free C_g will go
  multimodal/under-identified on a single impact → must gate identifiability FIRST (see §4 below).
- **§8(a) research gap** = our headline framing (above).
- **§4.2** points to [S22] and Yan et al. as the complex-FRF-likelihood options (next).

## 3. [S22] — the complex-FRF likelihood (the "may also need" piece)
**What it gives us:** a likelihood on the **full complex FRF** (magnitude AND phase), not just |H|, with a
**multiplicative log-error** and **space×frequency correlation** — and it returns model **evidence** for
comparison.
- **Multiplicative complex error (Eqs 13–18):** `log ε = log|ε| + iθ`; `|ε|` lognormal, phase `θ` normal,
  improper complex normal. `[w;θ] ~ N(0, diag(σ_w² R, σ_θ² R))`. The log-magnitude handles our multi-decade |H|
  span (our D4 ×100 gain + 5-decade |H1|); the **phase term is new for us** (we used |H| only).
- **Additive space+freq correlation (Eqs 19–25):** `ρ(Δz,Δf) = r·ρ_f + (1−r)·ρ_z`, `R = r(R_ff⊗I) + (1−r)(I⊗R_zz)`.
  **This is identical to the "faithful additive Schneider" we already implemented in Card A** (`schneider_faithful.py`,
  D13). So we have the machinery; the only delta is adding the **phase channel** and feeding it the **damped** FRF.
- **Their damping verdict (their §5.4) = our ceiling:** single global η can't match peak amplitudes; correlated
  σ_w≈0.31 absorbs it → ~90% coverage but wide. **Our experiment:** replace their single η with [DD20]'s localized
  non-proportional `C(θ3)`, predict the complex FRF, and test whether **σ_w shrinks** (physics explains what was
  discrepancy) and whether held-out complex-FRF coverage sharpens at the 8 hard channels.

## 4. Synthesis — proposed method "L-damp" (Das-Debnath C × Schneider complex likelihood)
A two-layer design that reuses our existing converged pieces (L8b mode-matching-free + faithful-additive Schneider):

1. **Damping model:** `C(θ) = α0 M + α1 K + Σ_g θ3_g C_g`, with `C_g` localized to the SE/damping-active interface
   groups (bulkheads, bolted joint 801, cross/strut). Rayleigh part for the global trend; localized viscous part
   for the non-proportional spread.
2. **Calibration likelihood (modal, mode-matching-free):** the damped eigen-equation residual on the measured
   complex eigenvalues `λ̂_m = −ζ̂_m ω̂_m + i ω̂_m√(1−ζ̂_m²)` (ω̂, ζ̂ from `.ash`), with system complex shapes
   inferred (NUTS-safe, no eigvec gradient). Reduced 160×160 state-space solve in the `V_keep` basis.
3. **Held-out prediction + Schneider complex likelihood:** predict the **complex** FRF `H(ω;θ,C)` at held-out
   channels via damped modal superposition; score with [S22]'s multiplicative log-|ε| + phase, additive
   space/freq correlation (reuse `schneider_faithful.py`, add the phase channel).
4. **The test (sharpen-not-absorb):** does localized non-proportional `C(θ3)` (a) reproduce the measured ζ spread
   0.12→1.76%, and (b) **reduce σ_w** and tighten held-out complex-FRF coverage at the 8 hard channels vs the
   uniform-ζ baseline? Report evidence (logZ) uniform-ζ vs Rayleigh vs Rayleigh+localized (Bayesian model
   selection, [S22]/[K25] §5).

## 5. Identifiability gate FIRST (do not skip — [K25] §3.2 + our own AGENTS Modal Identifiability Gate)
Before claiming any C_g is identifiable, compute the **damping analog of the strain-energy decomposition** we
already have: each mode's modal damping `ζ_m = (φ_m^T C φ_m)/(2 ω_m φ_m^T M φ_m)`, decomposed over groups →
`ζ_m = Σ_g ζ_{m,g}`. This tells which modes' measured ζ are sensitive to which interface damper (the
damping-dissipation-fraction table). Expect — by analogy to our 4/9 stiffness-identifiable result — that only the
bulkhead/cross/joint groups (which the descriptions and high ζ implicate) will be identifiable from 33 modes; the
rest sit at prior width. A single impact / single reference caps complex-mode-shape identifiability (our D20/D22
data limit), so lead with the **complex-eigenVALUE** fit (ω̂+ζ̂, in hand) and treat inferred complex
eigenVECTORS as the wider, caveated part.

## 6. Honest limits / risks (so we don't over-promise)
- **Real `.ash` shapes:** the survey curve-fit assumed proportional damping → we do NOT have directly-measured
  complex (phase-shifted) mode shapes. We either infer them ([DD20] mode-matching-free) or fit the
  complex-eigenVALUE only. Either way the *shape* complexity is inferred, not observed — state prominently.
- **Single impact / single reference:** caps per-interface damping identifiability and complex-shape recovery
  (D20/D22). The honest pre-test lever remains multi-reference / roving-hammer data.
- **Card A Sim-B caveat:** a single global *per-mode* damping did NOT sharpen the magnitude band. L-damp is a
  genuinely different lever (per-INTERFACE non-proportional C + PHASE likelihood, not one number on |H|), but
  success is an empirical question — the score decides, not the design.
- **Cost:** quadratic eig in the reduced basis is cheap; the new build is the C_g block assembly + the phase
  channel in the likelihood. Differentiable (mode-matching-free) → NUTS; escalate to TMCMC if multimodal.

## 7. One-line recommendation
Adopt **[DD20]'s localized non-proportional C(θ) + mode-matching-free complex eigen-equation** for the damping
update, validated through **[S22]'s complex (magnitude+phase) FRF likelihood with additive space/freq
correlation** (which we already have from Card A), gated by a **damping-dissipation-fraction identifiability
table** first. This directly attacks the ShockSat amplitude ceiling at the joint/bulkhead channels and lands on
the exact [K25] §8(a) open gap — a credible Ilias "improve the StatFEM" deliverable. **Surface to Andrew before
building (new method + new likelihood channel).**
