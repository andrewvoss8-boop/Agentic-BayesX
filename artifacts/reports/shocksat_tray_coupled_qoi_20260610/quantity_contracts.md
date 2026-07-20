# Quantity contracts — shocksat_tray_coupled_qoi_20260610

Written BEFORE any number or plot (Quantity Contract Gate). Conventions pinned
against `docs/lab/apparent-mass-convention-postmortem.md`,
`references/nasa-7004c-notes.md`, and NASA-HDBK-7004C §5.6 / Figure 9.
Coordinate frame: ShockSat global axes (x, y lateral; z up along the stack),
tray axes aligned to them (D3). All contracted quantities in SI (N, m, s, kg);
ShockSat modal data is converted snail-inch → SI before use (C8).

---

## C1. QOI — net CG interface load on the secondary, F = (Fx, Fy, Fz)

| field | value |
|---|---|
| name | net CG interface load resultant on the secondary (the tray) |
| definition | the 3 TRANSLATIONAL components of the 6-component interface force transmitted through the single-point mount INTO the tray (action on the secondary). Because the mount chain (condensation node + CBUSH) is massless, this force is identical on both ends of the mount and equals the net external force on the tray = (total tray mass) × (tray CG acceleration) by Newton's second law — hence "net CG load". |
| numerator | interface force [N], components in global x, y, z |
| denominator | none (it is a force, not a ratio); the per-axis SUMMARY metric is QOI_d = max_t |F_d(t)| over the 20 s record, reported as median and range over 8 input seeds, with parameter-uncertainty bands over MC draws |
| cut location | the source-side end of the mount CBUSH at ShockSat node P (top circular plate center). Massless chain ⇒ same force at the tray-side condensation node |
| sign convention | + = force ON the tray in +x/+y/+z. The reaction on ShockSat is −F |
| excitation | C7 base input a_free(t): the acceleration ShockSat's node P would have WITH NO TRAY ATTACHED (free/unloaded interface motion). Rotational components of a_free = 0 (assumption A6) |
| boundary condition | UNCOUPLED arm: the chain base is driven rigidly by a_free (infinite source impedance — standard spec practice). COUPLED arm: ShockSat's finite source mobility feeds back (C5) |
| units | N; time histories at fs = 2048 Hz |
| expected limiting behavior | quasi-static (input ≪ first chain mode): |F| → M_chain(0)·a = (3.16 kg)·a_free,d for translations (tray rigid mass) |
| expected resonance behavior | uncoupled: peaks driven by chain fixed-base modes (bounce/rock ~95–130 Hz at nominal mount). Coupled: force-limited (notched) near those same modes, per 7004C |
| reference | NASA-HDBK-7004C §5.6, Fig 9; force = mass × acceleration bookkeeping per Craig-Bampton enforced-motion formulation |
| checker | M_chain(0) ≈ tray rigid mass to <0.5 %; uncoupled peak ≥ coupled peak at chain-resonance bands; units carried in JSON |

## C2. Load apparent mass of the mount+tray chain, M_chain(ω) (6×6)

| field | value |
|---|---|
| name | 7004C-style LOAD apparent mass of the chain (CBUSH + condensation node + tray) |
| numerator | interface force 6-vector F_b at the chain base (source-side CBUSH end) [N, N·m] |
| denominator | enforced base acceleration 6-vector a_b at that same point [m/s², rad/s²] |
| coordinate | the interface point P, NOT a moving response coordinate (postmortem trap: this is the base-reaction convention, not drive-point F/a at a mass) |
| excitation | enforced motion of the chain base; tray otherwise free |
| boundary condition | LOAD convention: structure mounted on a driven, otherwise rigid base ("fixed-base driven") |
| units | kg (trans-trans block), kg·m, kg·m² for coupling/rotary blocks |
| expected limiting behavior | ω→0: M_chain → rigid-body mass matrix of the tray about P (zz = total tray mass 3.16 kg; off-diagonal terms from CG offset z_CG ≈ 0.19 m above P... computed value recorded in out/) |
| expected resonance behavior | INTERIOR PEAKS at the chain's fixed-base natural frequencies (load apparent mass peaks at resonance — Fig 9 load curve) |
| modal form | M_chain(ω) = M_rb + Σ_k Γ_k Γ_kᵀ ω² / (ω_k² − ω² + 2 i ζ_k ω_k ω), with Γ_k = φ_kᵀ M Ψ (participation), Ψ = static constraint modes −K_ff⁻¹K_fb, M_rb = Ψᵀ M Ψ; completeness Σ_k Γ_k Γ_kᵀ = M_rb (all mass-carrying modes computed) |
| reference | NASA-HDBK-7004C Fig 9 (load curve); Craig & Bampton 1968 enforced-motion |
| checker | low-freq limit matches rigid mass; interior peak exists; completeness sum rule to <0.5 % |

## C3. Source accelerance Y_S(ω) (6×6) and source apparent mass M_S(ω)

| field | value |
|---|---|
| name | ShockSat drive-point accelerance at mount node P (used in FBS); its inverse shown only for the Fig-9-style apparent-mass comparison |
| numerator / denominator | Y_S = a_P / F_P (acceleration response at P per force at P), free-free ShockSat, no tray. M_S = Y_S⁻¹ (matrix inverse, source apparent mass looking INTO ShockSat at P) |
| coordinate | drive point P, 6 DOF |
| excitation | point force/moment at P |
| boundary condition | FREE-FREE ShockSat (the validated test configuration). **Stated deviation from the 7004C Fig 9 cartoon:** the handbook's example source is GROUNDED, so its apparent mass grows → ∞ as ω → 0; a FREE-FREE source instead tends to the finite rigid-body mass "seen" at P (mass line). Resonance behavior is analogous (source apparent-mass NOTCHES near source resonances) |
| units | Y_S: (m/s²)/N; M_S: kg |
| modal form | Y_S(ω) = Σ_m φ_m(P) φ_m(P)ᵀ (−ω²)/(λ_m − ω² + 2 i ζ_m √λ_m ω), sum over 6 rigid-body + 74 elastic ROM modes; θ_S-dependent via the reduced eigenproblem |
| expected limiting behavior | ω → 0 (below 1st elastic, above suspension RBMs): Y_S → −ω² × rigid flexibility = a/F = R_P M_rb,S⁻¹ R_Pᵀ (rigid-body mass line ≈ 58 kg seen in translation at low f, less at high f as P sits atop a tall flexible stack) |
| expected resonance behavior | accelerance peaks at elastic modes (54.6 Hz first); M_S notches there |
| reference | NASA-HDBK-7004C §5.6 Fig 9 (with the free-free deviation stated); predecessor packet §2 (ROM provenance) |
| checker | RBM mass-line check: Σ_RBM φφᵀ at P vs rigid-body mass matrix from geometry (few-% tolerance, suspension-mode contamination documented if seen) |

## C4. Validity band of every frequency-domain quantity

Input band 20–250 Hz (C7). ShockSat ROM validated to <280 Hz (predecessor
reduction report; 74-mode basis to 321 Hz). Chain modes computed exactly (full
eigh of the small tray model), but coupled results are only TRUSTED where the
source ROM is valid: **the trusted band is 20–250 Hz**; figures shade
anything above 250 Hz as out-of-band. Frequency grid: rfft grid of the 20 s
record, df = 0.05 Hz (≈50 lines across a half-power bandwidth of a ζ=1 %,
125 Hz mode — Discretization Resolution Gate; resolution sensitivity arm
halves T to check df-dependence of peaks).

## C5. Coupled interface force (LM-FBS single-point coupling)

| field | value |
|---|---|
| name | coupled interface force F_cpl(ω) |
| formula | F_cpl = (I + M_chain Y_S)⁻¹ M_chain a_free — derived from interface equilibrium/compatibility: a_S = a_free − Y_S F (source unloading), F = M_chain a_S (chain driven by actual interface motion) |
| convention note | equivalent to the classic single-line result F = [M_S M_T/(M_S+M_T)] a_free... in 1-DOF scalar form (7004C impedance method); matrix form used throughout |
| force-limiting ratio | R_d(ω) = |F_cpl,d| / |F_unc,d| with F_unc = M_chain a_free. Expected: R ≈ 1 off-resonance, R ≪ 1 (notch) near chain fixed-base modes, R may MODESTLY exceed 1 near shifted coupled-system resonances (energy moves, it doesn't vanish) — both behaviors are the 7004C story |
| reference | NASA-HDBK-7004C §5.6; de Klerk, Rixen & Voormeeren, AIAA J 46(5) 2008 (general FBS framework) |
| checker | independent verification: direct Newmark integration of the assembled coupled (ROM ⊕ mount ⊕ tray) model under an equivalent force at P reproduces F_cpl(t) to <2 % peak error |

## C6. SRS and the modal-SRS force method

| field | value |
|---|---|
| SRS definition | maximax ABSOLUTE-ACCELERATION shock response spectrum of a_free,d(t): peak |absolute acceleration| of an SDOF (fn, Q) base-driven by the record, over a 1/24-octave fn grid 10–1000 Hz; Smallwood ramp-invariant recursive filter; units g vs Hz; Q ∈ {10, 25, 50} (sweep — Q is an ASSUMPTION, the chain's actual ζ_k is not Q's inverse) |
| force method | F_d ≈ sqrt( Σ_k [ m_eff,k,d · SRS_d(f_k, Q) ]² + [ m_resid,d · max|a_d(t)| ]² ), SRSS over chain fixed-base modes in-band; m_eff,k,d = Γ_k,d² (modal effective mass, kg); m_resid,d = M_rb,dd − Σ_in-band m_eff,k,d (residual rigid mass carried at the peak input acceleration) |
| what it ignores | cross-axis coupling (per-axis independent), modal phase (SRSS), source compliance (inherently UNCOUPLED) — these ARE the method errors being quantified |
| participation = MMF | per D38: modal participation factor / modal effective mass scaling, not mode-shape-at-CG scaling |
| reference | Smallwood, "An improved recursive formula..." (1981); NASA-STD-7003 SRS practice; SRSS combination per standard modal combination rules (named alternatives: ABSSUM conservative bound, NRL — SRSS used, stated) |
| checker | SRS filter validated against the analytic SDOF sine response (±1 % at resonance); m_eff sum rule |

## C7. Base input a_free(t) (the specified environment)

| field | value |
|---|---|
| definition | 3 independent Gaussian stationary records (x, y, z), band-limited flat acceleration PSD W0 = 0.01 g²/Hz over 20–250 Hz (zero outside), grms = sqrt(0.01 × 230) = 1.517 g per axis, T = 20 s, fs = 2048 Hz, N_seeds = 8, g = 9.80665 m/s² |
| role | the free/unloaded interface acceleration at P (what a spec would call the interface random environment). It is an INVENTED, linear-valid, moderate environment (D2) — NOT a measured ShockSat environment |
| rotational input | 0 (A6) — net CG translational force is translation-input dominated; a rotational-input probe is a logged gap |
| peak factor note | expected peak of a 20 s Gaussian band-limited record ≈ σ·sqrt(2 ln(f0·T)) ≈ 3.9–4.2 σ (f0 ≈ 100–250 Hz) ⇒ the Miles "3σ" convention is EXPECTED to sit ~25 % below true record peaks even for a rigid mass — documented so the envelope arm's miss is not misread |
| reference | Miles 1954 / NASA random-vibe practice (3σ design convention); Rice/Cartwright–Longuet-Higgins peak factor |
| checker | realized grms within 2 % of spec; PSD flatness within band |

## C8. Unit and frame reconciliation (ShockSat snail-inch → SI)

ShockSat deck: inch / lbf / s, mass in snails (lbf·s²/in), g = 386.088 in/s²,
total mass 0.331 snail = 57.96 kg. Mass-normalized mode shapes convert as:
translations φ_SI = φ_si / sqrt(175.126835 kg/snail); rotations
φ_SI = φ_si / (sqrt(175.126835) × 0.0254 m/in). Eigenvalues [rad²/s²] are
unit-invariant. Geometry: 1 in = 0.0254 m. Checker: the converted RBM block at
P must reproduce the SI rigid-body mass matrix (C3 checker); tray model is
native SI (predecessor FIM inputs).

## C9. PSD/Miles envelope arm

| field | value |
|---|---|
| per-mode Miles force | sigma_F,k,d = m_eff,k,d · sqrt( (π/2) · f_k · Q · W_d(f_k) ) (the Miles SDOF result: response of a (f_k, Q) oscillator to flat-near-f_k PSD), W_d = analytic input PSD (C7) in (m/s²)²/Hz |
| rigid term | sigma_rigid,d = m_resid,d · grms_d |
| combination | RSS over modes + rigid term; report 3 × sigma_F as the "3σ peak" envelope |
| assumptions that must hold (and their status here) | flat PSD near each mode (true by construction in-band — modes near the 250 Hz edge violate it, flagged per-mode), lightly damped SDOF (true), stationary Gaussian (true by construction), peak ≈ 3σ (KNOWN low for T=20 s — C7 note) |
| label | ENVELOPE arm — never presented as a prediction of the reference peak |
| reference | Miles 1954; NASA-HDBK-7005 random vibration practice |

## C10. Overnight addendum (D10) — synthetic mounted-config modal survey + value of information

| field | value |
|---|---|
| survey observable | natural frequencies of the COUPLED (tray-mounted-on-ShockSat) configuration, f_i ≤ 240 Hz, plus mode-shape samples at ~30 physical accel channels (used for PAIRING only, never in the likelihood) |
| truth generator | FULL (unreduced) coupled model at truth parameters drawn once from the honest priors, with a 6×6 mount stiffness including translation–rotation off-diagonal coupling the inference model cannot represent (structured model-form discrepancy) |
| noise | frequency: 0.3 % relative, one realization (predecessor replicate floor); shapes: 2 % (pairing only) |
| likelihood (inference) | log f_pred,i ~ Normal(log f_data,i, σ_f) over calib-filtered paired modes — whole paired set, frequency-only (no peak/feature selection; MAC used for pairing only, same rationale as the predecessor: eigenvector gradients are ill-conditioned near degeneracies) |
| inferred | 6 mount stiffness multipliers (LogNormal(0,1.15)), 5 tray θ (LogNormal(0,0.25)), σ_f (HalfNormal(0.05)) = 12 latents |
| fixed (not inferred) | θ_S at the predecessor posterior MEDIAN (the truth uses a DIFFERENT posterior draw — honest unmodeled variation at the posterior scale, absorbed by σ_f); geometry, damping, condensation topology |
| value-of-information metric | per axis d, for the coupled time-history peak QOI: width ratio W_after/W_before of the 68 % and 95 % intervals, where BEFORE = prior-mount propagation (§2 of the packet) and AFTER = posterior-mount propagation, both × the full predecessor θ_S posterior and 8 seeds; plus truth-QOI coverage before/after, and the force-limiting-factor interval tightening |
| expected behavior | the identifiability gate predicts dlnf/dlnk up to 0.449 ≫ σ_f-floor → mount multipliers should be recovered (effective values, given the off-diagonal truth) and QOI width should collapse substantially; if it does NOT, that is a publishable honest negative on the pre-test-lever claim |
| convergence gate | full AGENTS.md gate (R-hat ≤ 1.05, ESS ≥ 200 over ALL latents, div < 2 %); non-converged ⇒ YELLOW, intervals labeled not-trustworthy, never "NUTS active" |
| reference | predecessor run_nuts.py methodology (frequency likelihood + stop-gradient tracking); Cramér–Rao logic of the FIM workspace; NASA-HDBK-7004C §5.6 for the force-limit consequence |
| checker | reduction gate ≤ 0.5 % (modes ≤ 300 Hz, anchors + truth point); truth-lock SHA unchanged; pairing report (n_calib ≥ 8); convergence JSON over all variables; VOI artifacts present |

## Convention collision table (two-nearby-conventions rule)

| name | trap | used here |
|---|---|---|
| apparent mass | drive-point F/a at a moving mass (reciprocal inertance, NOTCHES at resonance) vs base-reaction/interface convention (load curve PEAKS at fixed-base resonance) | 7004C source/load interface convention ONLY (C2, C3); no drive-point F/a is ever labeled apparent mass |
| source apparent mass | grounded-source Fig 9 cartoon (→∞ at DC) vs free-free source (→ rigid mass line) | free-free, deviation stated (C3) |
| SRS | relative-displacement SRS vs absolute-acceleration SRS | maximax ABSOLUTE acceleration (C6) |
| participation scaling | mode shape at CG vs participation factor/effective mass (MMF) | effective mass (D38: "MMF=participation") |
| peak convention | 3σ design convention vs true Gaussian record peak (~4σ for T=20 s) | both reported, never conflated (C7, C9) |
| "fixed-base tray modes" | tray-on-rigid-feet (FIM model) vs tray-on-mount-base-clamped (chain) | CHAIN modes everywhere in methods; rigid-feet modes only as the model-verification target |
