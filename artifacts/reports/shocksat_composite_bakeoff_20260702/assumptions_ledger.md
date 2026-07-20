# assumptions_ledger — values, units, rationale, source, sensitivity priority
(Distinguishes: parameter uncertainty | observation noise | model discrepancy | forcing | aleatory | BC | QOI.)

| id | assumption | value / units | rationale + source | sens. priority |
|---|---|---|---|---|
| A1 | modal damping ζ (all modes) | 0.01 (–) | proven netcg choice; survey-typical | MED (bands scale ~1/ζ at peaks; ratios less) |
| A2 | measured-mode tier σ (freq, log-amp) | SD_F_M=0.01, SD_A_M=0.35 | netcg tier model; DD3 says cross-drive amp σ ≈0.86 (carried caveat: 1-oct-smoothed level is what's validated) | HIGH (drives band width) |
| A3 | unmeasured-mode tier σ | SD_F_U=0.06, SD_A_U=0.80 | netcg tier model; normal band ∝ SD_A_U (0.4→2.6x, 0.8→5.7x, 1.6→34x sweep in netcg) | HIGH (normal QOI) |
| A4 | statFEM F(k) form | marginal log-σ ramps 0.25→SD_A_U with unmeasured energy fraction; 1-oct correlated field | proven netcg formulation; DD2 learned σ_d=0.94, ℓ=0.10 oct (point-wise) — F(k) validated at 1-oct level only | HIGH |
| A5 | θ prior | log-normal, log-θ ~ N(0, 0.25), 9 groups (M0); same width for M1 params unless stated | NSIG_THETA=0.25 proven; prior-strength critique answered in plate-rehearsal thread (identifiability, not prior) | MED (evidence σ_prior swept 0.15/0.25/0.40) |
| A6 | modal-freq likelihood σ_w2 | HalfNormal(0.15) rel. ω², inferred | L5 proven (Kiran Eq 25) | LOW (inferred) |
| A7 | MAC likelihood term (S1) | (1−MAC_r)²/σ_mac², σ_mac ~ HalfNormal(0.3), inferred; MAC differentiable via jnp eigh — near-degenerate 246-258 Hz cluster gradient risk; mitigation = dense_mass NUTS + documented retune, freeze-basis fallback | modal_ash_mac.py precedent (converged before) | HIGH (the S1 axis itself) |
| A8 | Beck shape prior τ (S2) | φ = φ_FEM + τ·raw, τ=0.3, raw~N(0,1) per (74,nm) | modal_beck_ash.py proven converged | MED |
| A9 | data count | 5 drive caches (hit-averaged multi-impact H1, 111-115 channels) + 33-mode .ash EMA survey (76 nodes×3 ax); NO flight/build/test-to-test variability data → build/test variability NOT modeled (absent), stated | source_manifest, netcg | — (documented gap) |
| A10 | inferred vs fixed | inferred: θ (9 or candidate params), σ_w2, σ_mac (S1), raw shapes (S2), global gain per fold; fixed: ζ (A1), tier σ's (A2/A3), F(k) form (A4), tray region z≥55 in; NOT inferred latents: per-mode true amplitudes (marginalized by tier MC), unmeasured drumhead shapes | design | — |
| A11 | tier-1 screen proxy | Rayleigh-Ritz in the candidate-perturbed NOMINAL 80-mode basis (V_keep); ΔK,ΔM projected; scored freq+MAC vs .ash | IMPERFECT PROXY (documented; cannot see new local modes outside the nominal basis span) — hedged by carrying top ~30 to full eigensolves | HIGH for M1 funnel honesty |
| A12 | full eigensolve | eigsh k=80, sigma=-1e3 shift-invert, on T-reduced 399,510-DOF sparse K,M | remesh/mesh_screen proven path | LOW (validated) |
| A13 | drives / folds | 5 drives; leave-one-DRIVE-out; +Y unique 230.6 Hz observability | netcg | — |
| A14 | band | 45-260 Hz (data band); delivery band 20-2000 Hz is PRIOR-ONLY outside data band (carried caveat) | netcg contract | — |
| A15 | NUTS gates | 4 chains, x64, R-hat≤1.05, ESS≥200, div<2%; uniform retune policy documented per arm | AGENTS.md | — |
| A16 | input PSD | flat, known, at drive point; level cancels in ratios | netcg contract | — |
| A17 | uncertainty taxonomy | parameter=θ posterior; obs noise=σ_w2/σ_mac; model discrepancy=F(k)+tier amp; forcing=none (known input); aleatory build/test=absent (A9); BC=free-free (fixed); QOI band=posterior+tier+F(k) MC | design | — |
