# region_diagnosis.md — Card D Phase 1 (READ-ONLY, before any edit)

Where and why the as-received NASA-correlated ShockSat FEM disagrees with the measured data, region by
region. All numbers reproduce from `code/diagnose_regions.py` → `out/region_diagnosis.json` (region MAC) and
are cross-referenced to the validation study (`statfem_real_validation_20260617/out/mc_pattern_summary.json`,
packet §2). **No model edits have been made.** This document decides which edits are worth attempting.

> MAC ("modal assurance criterion") = squared cosine between two mode-shape vectors, in [0,1]; 1 = identical
> shape, 0 = orthogonal. "Region-restricted MAC" = the same, computed using only the measured DOFs at a
> region's sensors. "FRF" = frequency-response function (here accelerance |H|, g/lbf). "PBUSH/CBUSH" = a
> Nastran scalar spring element/property representing a joint with 6 stiffness terms (3 translation, 3 rotation).

---

## 0. The BEFORE baseline (global, as-received FEM vs `.ash` survey)
- Global matched MAC = **0.633** over the 26 well-paired modes (MAC>0.3). Consistent with the validation
  study's "MAC-matched ≈0.70–0.73" headline (the small difference is which modes pass the >0.3 filter; the
  clean low modes are 0.88–0.97). **The FEM mode shapes are globally decent.**
- Low modes: test 1 (54.2 Hz) MAC 0.97 / Δf +0.75%; the FEM gets the global frequencies and shapes well.
- The disagreement the data flags is **per-sensor amplitude at 8 interface / impact-face channels**, not a
  global shape failure. This is the StatFEM-hard part (joints, interfaces, near-field), confirmed below.

## 1. The 8 target channels — checker-confirmed, SNR-uncorrelated
From the validation 25-split Monte-Carlo (`mc_pattern_summary.json`):
- **7 channels consistently FAIL the 95% predictive band: ch4, 27, 38, 40, 52, 69, 98** (pass-rate ≤0.34,
  overall 0.855). Pass-rate correlation vs dynamic range = +0.04 and vs height = −0.05 (≈0) ⇒ the misses are
  **genuine model-form error, not low SNR / data quality** (ch29–31, ch101 already excluded as bad-DAQ).
- **HONEST DISCREPANCY:** the card's region table lists **8** channels including **ch92 (strut base)**, but
  ch92 is **NOT** in the checker's consistently-fail-7. ch92 was added from the D21 instrumentation review as a
  strut-to-deck interface of interest; treat it as a *suspected* interface region, not a checker-confirmed
  failure. I diagnose all 8 but will label ch92 accordingly in any before/after claim.

## 2. Region-restricted MAC (the shape leg) — and its honest limitation
The `.ash` survey measures only **1–3 axes** at the nodes nearest these channels, so region-restricted MAC is
**thin** (few DOFs) and noisy. The channel→nearest-`.ash`-node map distances are also large for some
(ch69 d=6.0 in, ch40 d=4.0 in), so the MAC-at-nearest-node is a *proxy* for the hard channel, not its exact
shape. Read these as directional, with the FRF/amplitude leg (§3–4) as the robuster evidence.

| region | channels | measured axes | region MAC (mean / median over 26 modes) | vs global 0.63 |
|---|---|---|---|---|
| source_face | ch4(X), ch27(X), ch38(Y) | 1 axis each → 3 DOF | 0.51 / 0.53 | **worse** |
| box_column | ch40(X), ch52(Z), ch69(X) | 3 DOF | 0.71 / 0.76 | better/at-par |
| strut_base | ch92(X,Y,Z) | 3 DOF | 0.48 / 0.39 | **worse** |
| dish | ch98(Z) | 1 DOF | not computable (1 DOF) | — |

- **High-frequency local modes are where shapes diverge most.** The worst region-MAC modes are the dense
  high modes: source_face → test modes 12/16/21/26/27 (158–233 Hz) ≈ 0.00; strut_base → modes 18/25/13
  (166–223 Hz) ≈ 0.0–0.01; box_column → modes 26/22/21 (199–231 Hz) ≈ 0.01–0.10. The clean low modes are fine;
  the FEM loses the **local high-frequency mode shapes** at these regions. This matches "a coarse mesh
  under-resolves local/near-field dynamics."
- **box_column shapes are actually OK (0.71)** → for the bulkhead/bolted-joint channels the *shape* is not the
  main problem; the amplitude miss there is more likely frequency-misalignment near sharp resonances + joint
  damping (see §3).

## 3. The joint model is ALREADY finite and ALREADY tried — a pivotal negative for the obvious lever
Inspecting `fem_model.npz` connectivity at the regions:
- The instrumentation nodes (10101, 7101, 6101, 1101, 11101 …) are themselves **CBUSH PID 99** = accelerometer
  attachment bushes (K ≈ [1e6,1e6,1e6,1e7,1e7,1e7]), `fixed` (not calibrated). They are not structure.
- The **real structural joints are PBUSH 801–807** (Joint_Connections) with **finite, anisotropic, already-
  NASA-correlated** stiffnesses, e.g. near the bolted joint (ch52) eid 8000014 **PID 801** K=[1e6,1e6,5e6,
  12240,1e7,1e7]; near the strut base (ch92) **PID 807** K=[5e6,324000,324000,1e7,1e7,869000] and **PID 902**
  (contact) K=[6800,0,0,0,0,0]. The joints are the calibration group **`joints` = bush_801…807**.
- **CRITICAL:** the validation study (D13) found only **4 of 9 groups identifiable** (bottom_box, cross_beam,
  plates, top_box) — the **`joints` group was NOT identifiable**, and scaling θ_joints did not fix the amplitude
  misses. So **"soften / re-stiffen the rigid joints" is NOT a fresh lever** — the joints are not rigid, they
  are finite CBUSH that the data already cannot pin and that θ-scaling already failed to fix.
- The fresh lever Card D actually offers (vs Card A's θ-scaling) is changing the **mesh / connectivity** so the
  mode **shapes themselves** move (θ-scaling provably cannot move shapes; D22). That points to **local mesh
  refinement** at the under-resolved local-mode regions (dish, impact face, strut base), not to re-tuning the
  already-finite, already-non-identifiable joint springs.

## 4. FRF / amplitude leg (cited from the validation study; to be reproduced at the 8 channels in Phase 2)
- The validation twin under-predicts peak |H| at these channels (Schneider Fig-6-type amplitude/damping floor),
  with the held-out misses concentrated at the interface/near-field locations (§1). The amplitude ceiling is a
  **combination**: residual shape error (MAC 0.5–0.7 on dense modes) + frequency misalignment near sharp
  resonances + dense-mode superposition + damping (packet §2.3). Per-mode damping does NOT sharpen it
  (validation Sim-B). 
- For Card D I will reproduce the FEM-vs-measured peak |H| at the 8 channel nodes as the BEFORE amplitude
  baseline (Phase 2), so any AFTER claim is a true before/after at the hard channels.

## 5. Diagnosis verdict → what to edit (feeds the scoping decision)
1. **Dish (ch98) — local mesh refinement, highest-confidence true-remesh lever.** A flexible dish whose local
   modes are under-resolved; refining its mesh genuinely changes its local mode shapes/frequencies. Single
   1-DOF MAC can't quantify it, but the physics + the high-mode shape divergence support it.
2. **Impact/source face (ch4/27/38) — local mesh refinement.** Worst region MAC (0.51) and near-zero MAC on
   high modes ⇒ under-resolved near-field/face-panel local modes. Refining the +X face panel mesh is a true
   remesh lever.
3. **Strut base (ch92) — local mesh + connectivity.** Worst region MAC (0.48); strut-to-deck modeled by
   PID 807 + 902 contact. Refining the strut-base attachment region. (Caveat: ch92 not in the confirmed fail-7.)
4. **Box column / bulkheads + bolted joint (ch40/52/69) — LOW expected payoff from re-mesh.** Shapes are OK
   (0.71); the joints are finite & non-identifiable; the miss here is more freq-alignment + damping than
   under-resolved shape. Re-meshing is unlikely to help; honest to say so and not over-edit here.

**Net:** the data-justified re-mesh targets are the **local-mode regions (dish, impact face, strut base)**, NOT
the joints (already finite, already non-identifiable). The expected outcome is modest and not guaranteed — the
validation evidence says shape error is only part of the amplitude ceiling. This is the honest setup for the
"can an agent contribute by remodeling from data?" verdict.
