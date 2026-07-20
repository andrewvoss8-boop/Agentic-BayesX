# Decisions log — virtual-sensing-target credibility toy

Workspace: `artifacts/reports/paper_virtual_sensing_uq_toy_20260613/`.
Paper under review: Yan et al., *Physics-Informed Digital Twin for Spacecraft Structures
under Sensor Faults: Virtual Sensing via a Frequency Attention U-Net and Closed-Loop
Model Updating*, Aerospace Science and Technology (2026), doi:10.1016/j.ast.2026.112794.
(`references/Physics-Informed Digital Twin ... Closed-Loop Model Updating.pdf`)

- **D0 (2026-06-13, Andrew):** "go on the toy. start small and iterate to more ambitious
  challenges. Run at least 4 experiments before stopping. Do not stop for my feedback."
  => Autonomy grant for this thread (analogous to buffet thread D13). Build small first,
  escalate ambition, run >=4 experiments, do not pause for feedback. Durable-rule /
  checker / sampler-standard / notes changes still stop for Andrew. NUTS/HMC is the
  Bayesian sampler (project default).

- **D1:** Scope = the closed-loop *updating* stage only. We do NOT reimplement the FAU
  deep network (no access to their data/weights). The FAU-reconstructed "virtual ground
  truth" is replaced by an explicit, LABELED surrogate: truth FRF + a controlled
  reconstruction error whose magnitude is calibrated to the paper's reported FAU-Up
  masked-channel residual (~8-10 dB) and pure-FAU peak-frequency shift (~10.8%). This is
  a stand-in, not a reproduction of their network. Stated prominently in every artifact.

- **D2:** Forward model = the paper's modal-ROM FRF with its exact updating
  parameterization (Eqs. 4, 11, 12): Mr=I (mass-normalized modes), Kr(alpha)=Sa Kr0 Sa,
  Cr(beta)=Sb Cr0 Sb, input-coupling gamma. Diagonal reduced matrices => modal
  superposition FRF. Channels coupled through a fixed mode-shape matrix Phi so observed
  channels physically inform masked channels via shared modal parameters.

- **D3:** Fault = mask Ch3/Ch4 (the paper's representative A3 case). Observed = Ch1/Ch2.
  Likelihood/objective on log-amplitude (dB-equivalent) FRF, matching the paper's Eq. 21.

- **D4:** Experiment ladder (small -> ambitious), each checker-gated:
  - E1 discriminating: deterministic constrained NLS (paper's FAU-Up, point estimate)
    vs discrepancy-aware NUTS (the paper's own Future-Work #3 UQ) on the SAME virtual
    target. Trust test = held-out TRUE masked-channel FRF + masked-channel peak QOI.
  - E2 baselines + reconstruction-error sweep: add Meas-Up (discard masked) and Interp-Up
    (spatial interpolation) deterministic baselines mirroring the paper's Table 7/8; sweep
    reconstruction-error level; report masked-channel QOI error and Bayesian coverage vs
    level.
  - E3 configuration trend + identifiability: A1->A2->A3 monotonic joint softening; recover
    the alpha softening trend; apply the Modal/Eigenproblem Identifiability Gate
    (per-mode strain energy is trivial in modal coords -> use the FIM eigen-view) to test
    whether the *aggregate* softening trend is identifiable while *per-mode* alpha is not.
  - E4 biased reconstruction (stress test): virtual target carries a COHERENT bias
    (peak shift / systematic amplitude bias), not just random error. Test whether iid
    credibility inflation still covers, vs a correlated (Schneider-style) discrepancy
    model. Expect an honest boundary: UQ helps only if the error MODEL matches the
    reconstruction's error STRUCTURE.

- **D5:** Sampler standard = NUTS, >=4 chains, convergence gate (max R-hat <= 1.05, min
  ESS >= 200, div frac < 2%). Non-converged runs reported YELLOW with worst-case
  diagnostics on the figure, never as "active"/green.

- **D6:** No durable edits (AGENTS.md / checkers outside this workspace / notes/runs.md /
  project_log.md) without Andrew sign-off. Proposed log/notes rows go in packet.md.
