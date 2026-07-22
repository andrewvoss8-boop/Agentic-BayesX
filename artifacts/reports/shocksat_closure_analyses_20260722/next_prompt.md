# Next prompt — Task Card B (report rebuild)

Task Card A (this workspace) is complete; do NOT extend it. The next session should:

1. Re-ground per AGENTS.md: read `AGENTS.md`, `docs/agents/closure_analyses_20260722/task_card_B_report_rebuild.md`,
   `notes/memory.md` CURRENT STATE, this workspace's `packet.md` + `out/checker_report.json`, and the
   runner `decisions_log.md` here.
2. Execute Task Card B: rebuild the advisor report (≤9 pages) around the A1–A5 outputs of this
   workspace plus the recovered damping/phase/undercoverage findings, applying the 10
   adjudication-mapped required changes.
3. Human stop point: before finalizing if A3 flips the load narrative — it does NOT (A3 confirms the
   statFEM-beats-incumbent conclusion under CRPS on measured shear evidence, 8/10 drive-axis cells
   under all 3 envelope conventions), so the stored narrative stands, but confirm with Andrew.

Key handoff facts (all checker-backed here):
- A1: 4 identified combinations (0.019/0.029/0.259/0.355), nearly pure bottom_box/top_box/plates/cross_beam;
  5 prior-like. Known answer matched. Subspace claim only.
- A2: see out/a2_sigma_f_sweep.json (reference reproduction + 5-prior floor stability + predictive checks).
- A3: incumbent numbers reproduced exactly (max|dev| 0.000); CRPS columns added; normal-Z stays
  synthetic self-consistency; 2.526 vs 2.958 stated adjacently.
- A4: iid whole-FRF likelihood profiles are multimodal (~10 local maxima per slice) with separated
  chains in different local modes — diagnosis, not verdict.
- A5: phase diagnostic FOUND (statfem_real_validation_20260617, circ var 0.8536) — cite, do not recompute.
