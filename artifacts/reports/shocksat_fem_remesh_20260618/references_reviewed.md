# references_reviewed.md — Card D

| ref | what it is | used for | verdict |
|---|---|---|---|
| Das & Debnath 2020, MSSP 136:106524 | Bayesian (MAP) FE updating with INCOMPLETE COMPLEX modal data; updates mass+stiffness+DAMPING (Rayleigh α0,α1 + non-classical viscous C=C0+Σθ3_g C_g); mode-matching-free; complex eigenvalue λ=−ζω+iω√(1−ζ²); quadratic eig (λ²M+λC+K)Ψ=0 | THE damping-update machinery to adopt: localized non-proportional C at our joint/bulkhead groups; mode-matching-free = NUTS-safe (same fix as our L8b) | ADOPT (core method) |
| Kiran, Das, Bansal 2025, Prob. Eng. Mech. 80:103761 | State-of-the-art review of Bayesian FE updating; §4.3 modal likelihoods (mode-matching + mode-matching-free/eigen-equation), §4.2 FRF (Schneider, Yan), §3.2 identifiability (global/local/un-), §8(a) research gap | map of options; identifiability warning (our multimodality = their "local identifiability"); §8(a) "complex modal data + non-classical damping on real-life structures" = our headline gap framing | FRAME + GATE |
| Schneider et al. 2022, MSSP 166:108407 | Bayesian updating on COMPLEX FRF; multiplicative log-error (|ε| lognormal + phase normal), additive space×freq correlation R=r(R_ff⊗I)+(1−r)(I⊗R_zz), BUS-SuS, model evidence | the complex (magnitude+PHASE) held-out likelihood; = our Card A faithful-additive Schneider + a new phase channel + damped FRF. NOTE: his single-η damping hit our EXACT amplitude ceiling (absorbed into σ_w≈0.31) | ADOPT (validation likelihood) |

Synthesis + proposed "L-damp" method, identifiability gate, and honest limits in `damping_modeling_review.md`.
