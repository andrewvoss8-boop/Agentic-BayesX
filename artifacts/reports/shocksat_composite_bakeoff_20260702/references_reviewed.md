# references_reviewed — Reference and Standards Gate

| reference | how used / checked | where |
|---|---|---|
| NASA-HDBK-7004C (force limiting) | net-CG interface FORCE convention (apparent-mass/base-reaction), named vs the acceleration alternative; inherited verbatim from the proven netcg contracts | quantity_contracts.md |
| Kiran et al. (Bayesian FE updating), Eq 25 | S0/S1 frequency likelihood form (relative ω² Gaussian, inferred σ_w2); Eq 43-44 evidence = fit − complexity | rmodel.run_nuts, tier3_evidence.py |
| statFEM (Girolami et al.) Eq 38 | analytic marginal-likelihood screen Σ = D R D + J C J^T at θ_MAP, type-II ML hyperparameters | tier3_evidence.py (stage1_evidence pattern) |
| Beck & Katafygiotis / Yuen (mode-matching-free Bayesian modal updating) | S2 arm: system mode shapes as free parameters, Rayleigh-quotient frequency consistency + measured-shape pull; avoids eigenvector-derivative pathology | rmodel.run_nuts m_S2 (modal_beck_ash precedent) |
| Allemang (MAC) | MAC definition + its use as a shape-match statistic in likelihood and pairing; pairing by one-to-one assignment (cross-orthogonality style), not greedy | quantity_contracts.md, tier1/tier2 |
| Fox & Kapoor (eigenvalue derivatives) | exact dλ/dθ rows of the evidence Jacobian | tier3_evidence.jacobians |
| Schneider et al. (statFEM structural dynamics) | frequency-correlated output discrepancy concept behind F(k); the proven netcg formulation is reused unchanged | rmodel.statfem_fk_band |
| Prior internal studies (pinned bars) | netcg_method_selection_20260701 (statFEM F(k) bars, coverage machinery), modelclass_L5_20260619 (Beck + MAC-null precedents, evidence machinery), fem_remesh_20260618 (diagnosis, Card D boundary, metric traps) | question_framing.md provenance |

Ruled out / not applicable: MIL-STD-810 (environment tailoring — not a modal-updating reference);
vibrationdata.com SDOF examples (contracts already pinned by 7004C + prior studies). Units, axes, limiting
behavior (ω→0 net force → input × tray mass) checked against the inherited contracts in quantity_contracts.md.
