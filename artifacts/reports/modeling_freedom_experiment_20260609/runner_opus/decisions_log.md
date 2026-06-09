# Runner (Opus) Decisions Log — modeling-freedom / anti-overfitting

Append-only. Records non-obvious decisions so they survive compaction.

## 2026-06-09 — Start-of-run guards
- CWD asserted = `.../modeling_freedom_experiment_20260609`. Writing ONLY under `runner_opus/`.
- `shasum -c manifest.sha256` → all OK (contract.md, splits.json, my inputs match pins).
- Read ONLY: contract.md, splits.json, runner_opus/inputs/**. Did NOT open ../notes, parked
  shocksat packets, ../vault/**, scripts/gen_synthetic_tray.py, scripts/score_vault.py, or any
  other run. (shasum -c only HASHES vault files; it does not reveal their contents.)

## Synthetic forward-model assumptions (my modeling freedom; truth generator NOT read)
Public config gives: N=12 DOF, 4 stiffness groups, k0_nominal=3.0e6, m_modes=6,
sensor_dofs=[0,2,3,5,6,8,9,11], zeta=0.02, band 10-600 Hz, qoi_ref out11<-in0,
qoi_heldout out5<-in8, sigma_f_rel=0.005, sigma_phi=0.02. Masses NOT given.
- A1 Topology: fixed-free grounded chain. 12 springs: spring0 = ground->mass0; spring i =
  mass_{i-1}->mass_i (i=1..11). Tridiagonal K. RATIONALE: "grounded 12-DOF chain" = one end
  fixed; gives 12 modes, observe lowest 6. Mode-shape 8-sensor sub-norm ~0.85 matches data
  (mass-normalized 12-vector sliced to 8 DOFs) — corroborates topology.
- A2 Mass: uniform m=1.0 (M=I). RATIONALE: config gives no masses; unit mass is the natural
  nondimensional choice consistent with k0 and the 43-343 Hz band. CONSEQUENCE: pred_theta is
  defined relative to k_group=theta_g*k0 with m=1; if the truth used different masses, absolute
  theta is biased by a global stiffness/mass scale (flagged in packet).
- A3 Spring grouping: 4 groups of 3 consecutive springs (0-2,3-5,6-8,9-11), each scaled theta_g.
- A4 Model-form error: candidate model has NO cross-link joint (per config note). Best 4-theta
  LS fit to mean modes leaves ~5-10% freq residual + MAC 0.90-0.96 >> noise (0.5%/0.02). This
  structured residual IS the model-form error the discrepancy term must contend with.

## QOI definition (committed; vault's score_vault.py definition NOT read)
- QOI = peak receptance magnitude over band [10,600] Hz for the path: |H_{out,in}(w)| max,
  H_{jk}(w)=sum_n phi_jn phi_kn /(w_n^2 - w^2 + 2 i zeta w_n w), mass-normalized modes, zeta=0.02.
  Units m/N. Reported as linear m/N in finalists.json (also log10 in packet).
- RISK: if vault uses a different scalar (e.g. value at a fixed freq, or log), my ABSOLUTE qoi
  error vs truth is not comparable; the CROSS-FINALIST overfit ranking (which config drifts more)
  still holds. Flagged prominently in packet. This is honest-labeling, not a success claim.

## Selection / dev pipeline (frozen metrics from contract S2 — NOT changed)
- Registered dev score = posterior-predictive log predictive density (LPD) summed over the 4 DEV
  realizations' modal observations (freqs rel-err + aligned shape components). Higher better.
- Secondary: PSIS-LOO / WAIC from pointwise log-lik on train (no refit). Finalists also get true
  leave-one-realization-out refits.
- Reusable-holdout: round/jitter dev LPD to a noise threshold before registering an improvement
  (threshold documented in results_table + packet).

## Sampler
- NUTS (numpyro 0.19.0, jax x64 forced), >=4 chains, non-centered for hierarchical discrepancy.
  arviz unavailable (scipy incompat); R-hat/ESS via numpyro.diagnostics (split-R-hat, ESS).
  Convergence gate S3 enforced: maxRhat<=1.05, minESS>=200, div<2% over ALL sampled vars.

## ShockSat
- .pch/.mat at sibling paths are my READ-ONLY data inputs (granted by inputs_manifest + contract
  S9). I will parse raw modal data ONLY; I will NOT open any report/packet/notes/findings of the
  parked runs. Held-out pyro (vault/shocksat) is forbidden — committed OOD prediction made first.
