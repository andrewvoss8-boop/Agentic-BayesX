# Source Register

| Source | Path or URL | What It Supports | Limits |
|---|---|---|---|
| Human research plan | current user prompt, 2026-06-02 | PSD points, dB convention, staged test sequence, fixed 3 dB flight variability, learnable build/sensor variability, Matérn forcing request. | Not a validated hardware dataset. |
| Fresh 2DOF packet | `artifacts/reports/fresh_2dof_statfem_fbs_20260601/fresh_2dof_statfem_packet.md` | Prior parameter assumptions, existing 2DOF transfer conventions, `3*GRMS` QOI precedent. | Current inference is prototype/legacy random-walk/random-scan Metropolis, not NUTS/HMC. |
| Fresh quantity contracts | `artifacts/reports/fresh_2dof_statfem_fbs_20260601/quantity_contracts.md` | Existing reciprocal-inertance and tray transmissibility conventions. | Does not cover the new sequential build/flight hierarchy. |
| Project sampler rule | `AGENTS.md` and `CLAUDE.md` | NUTS/HMC must be the future default and cannot be claimed active without code/checks. | Does not implement the sampler. |
