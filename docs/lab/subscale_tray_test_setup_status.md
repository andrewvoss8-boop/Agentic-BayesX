# Subscale Avionics Tray Modal Test — Setup Status

- **Date:** 2026-06-08 (rev 2 — M3/M5 pin question resolved; original 2026-06-06)
- **Authors:** Andrew Voss (lead experimenter) + Claude Code (lead agent, advisory)
- **Status of rig:** DESIGN + PROCUREMENT in progress. Not yet assembled. Not yet instrumented.
- **Scope:** Physical subscale rig. This is a **lab note**, not a Round-3 BayesX deliverable.
- **Confidentiality:** A Relativity (RTY) spec sheet referenced in planning is marked
  PROPRIETARY & CONFIDENTIAL / CUI. Its numbers are **not reproduced here**; only used
  qualitatively to set our (deliberately different) configuration. Handle per obligations.

> All frequencies/forces below are **closed-form hand-calc estimates** unless tagged
> MEASURED. Confirm with FEM and/or bench measurement before relying on them.

---

## 1. Objective and configuration (DECIDED)

Build a subscale, coupled source–load rig to study **frequency-based substructuring (FBS)**
and **NASA-HDBK-7004 force-limiting** behavior, with the **strut-end joints as the
uncertain stiffness + damping element** to be characterized.

- **Configuration: NON-ISOLATED** (rigid metal rod-end / Heim joints; **no elastomeric
  isolators**). This **deliberately differs from the flight design** (flight avionics tray
  is isolated at a low mounted frequency via 6 elastomeric bushing strut isolators).
  - Rationale: the non-isolated, rigid-bolted-joint case is the *uncertain, hard-to-predict*
    regime (joint stiffness + micro-slip damping), which is the high-value target for model
    updating. It also re-aligns the physical rig with the Round-3 non-isolated framing.
  - **Honest label:** results represent a non-isolated configuration; they do NOT replicate
    the isolated flight tray. Flight-is-isolated is a documented known difference.
- **Physical coupled test** (not software-only FBS): tray on a 6-strut hexapod mounted to a
  **compliant** backing plate, so the 7004 force-limiting notch appears physically. A rigid
  shaker plate would over-test and suppress the notch.

### Earlier-guidance correction (logged for honesty)
Advice given mid-design — "rigid joints, no elastomer" — was briefly premised on the wrong
belief that flight was non-isolated. Once the flight spec showed isolation, that guidance was
flagged as wrong-for-flight. Final decision: **stay non-isolated by choice**, so the
"rigid joints / no elastomer" guidance is correct again *for this configuration*.

---

## 2. Component status

| # | Component | Spec / value | Status | Notes |
|---|-----------|--------------|--------|-------|
| 1 | **Tray (load)** | Thorlabs MB3030/M, 300×300×12.7 mm (½") solid Al, M6 tapped @ 25 mm grid. Bare mass ~3.0 kg as-built (tapped grid removes a few %); 3.09 kg idealized solid plate (geometry × density) | **PURCHASED** ($109, used) | 1st elastic mode well above the suspension band → acts rigid (estimate; confirm by FEM/test). **Phase-1 FEM uses the BARE tray, no ballast.** Mass remains tunable via bolt-on ballast for later phases. |
| 2 | **Struts (×6 links)** | Delta push rods L196-D8-M3: 196 mm eye-to-eye, 8 mm OD Al tube, **M3 rod-end bore** | **PURCHASED** | k_axial ≈ 5.5 MN/m (stiff; joints are the soft element). Strut 1st bending ~370 Hz (above band). Bond rod-ends into tubes (item 7). |
| 3 | **Backing plate (source)** | Steel, free-free on bungees; candidate 4 ft × 3/8" (≈245 lb) | **NOT PURCHASED** | Modes (4ft×3/8"): ~21/31/38/55/55/96 Hz. **Size TBD** — must match the *actual* non-isolated tray fundamental (item: Open Risk #3). Heavy → rigging needed. |
| 4 | **Clevis brackets (×6)** | Double-shear fork, **ear ≥6 mm**, jaw ~10 mm, **M3 pin**, **2× M6** base to grid | **NOT PURCHASED** | Sourcing via LLM-browser run. Opposed ¼"+ Al angle (drill-press) or COTS U-bracket. Thin ears (<6 mm) rejected — they steal joint compliance. |
| 5 | **Spacers** | M5 rigid Al spacers (5.2 mm ID; 1.5 & 3 mm) + M5 shim washers, both sides each joint | **PURCHASED** | Center the ball + set standoff; rigid metal, NOT elastomer. Per-joint — all 12 joints. |
| 6 | **Pin + nut** | M5×30 SHCS + M5 nylon locknut | **PURCHASED** | Pin = **M5**: the rod-end *ball bore* takes M5 (the "M3" in the part code = rod-end's own *stud thread*). Confirm bore with calipers on arrival. |
| 7 | **Adhesive** | J-B Weld 8276 KwikWeld | **PURCHASED** | Bond rod-ends into tubes (replaces friction set screws). Degrease/abrade; makes joint permanent. |

### Fasteners already purchased
| Item | Qty | Status | Note |
|------|-----|--------|------|
| M6×12 SHCS, 304 SS | 50 | PURCHASED | **Short** for thick bracket bases — get M6×16/20 if brackets are thick. |
| M6 flat washers | 100 | PURCHASED | OK for base. |
| M5 Al spacers (5.2 ID×8 OD, 1.5 & 3 mm) | ~15 | **PURCHASED ✓** | Clevis-pin spacers; center the ball both sides. |
| M5×30 SHCS | 30 | **PURCHASED ✓** | Clevis **pin** — rod-end ball bore takes M5. |
| M5 nylon locknuts | 50 | **PURCHASED ✓** | Pin locknut. |
| M5 flat washers (5 ID×12 OD) | 120 | **PURCHASED ✓** | Pin centering / shims. |

---

## 3. Geometry (DECIDED, pending hole-map)

- Hexapod: **3 bipods @ 120°**, struts **~30° off horizontal** (matches shallow flight strut
  angle; target <45°).
- **Standoff** (tray above plate): **~98 mm** for 30°.
- **Base feet ~170 mm** radially outboard of tray attach points.
- Tray attach radius ~120 mm (on the 300 mm tray); base circle ~290 mm radius (fits the plate).
- Stiffness split at 30°: ~25% of strut axial stiffness → vertical, ~75% → lateral
  ⇒ **soft bounce mode** (lands the fundamental low) + **stiff lateral** (separates modes).
- **Drill-ready 6-point hole map: NOT YET PRODUCED.**

---

## 4. Instrumentation plan (GAP — highest practical risk)

**Have:** 1 single-axis accelerometer. **No force measurement.**

An FRF / apparent mass / force-limiting result needs **measured input AND measured output**.
With 1 accel + no force, only natural frequencies + damping are obtainable (via any broadband
excitation). To close the loop:

- **Excitation (input):** borrow/rent an **instrumented modal impact hammer** (sized for a
  steel structure). Do a **roving-hammer** test with the single fixed accel to build mode shapes.
- **Interface force (QOI):** **PCB 740B02 ICP strain sensor(s)** bonded to struts.
  F = E·A·ε ⇒ ~150–350 N peak/strut at 100 µε (8 mm Al tube, wall-dependent). 0.5 g mass =
  negligible loading. Use **pairs (opposite faces)** to cancel bending. Calibrate the
  instrumented strut as a load cell (known weights) for traceable force.
- **Conditioning:** all ICP sensors need **IEPE power** (~4 mA) — DAQ must have IEPE inputs
  (070A02 / 070A05 are PCB conditioning options).
- **Controlled excitation via Teensy:** good for *generating* chirp/sine sweeps; gives
  frequencies + damping with the accel even uncalibrated. Limits: underpowered for large steel
  structures (hammer better), and the onboard ADC is marginal for clean data (prefer a borrowed
  DAQ, or a 24-bit I²S codec front end).

### Partners / sourcing (in pursuit)
- **LASIR (Vanderbilt)** — pursuing; **borrow preferred over rent** (gear + expert review).
- **UTC College of Engineering** — likely local loaner of hammer/accel/DAQ.
- **The Modal Shop rental** — quote-based; educational + LASIR angle should lower it; ~1-month
  window planned. **No rate quoted here** (not fabricating a number — request a quote).

---

## 5. Acceptance criteria / QOI (UNDERSPECIFIED — to define)

Currently qualitative. To be made falsifiable before testing:
- Force-limiting **notch** demonstrated at the coupled resonance (depth + frequency).
- Net interface force (strut-force sum) and a netCG-style metric.
- First N natural frequencies + damping, with stated tolerances.
- Build-to-build / reassembly scatter (a first-class output, not noise).

---

## 6. Open issues / risks (priority order)

1. **Clevis brackets not sourced** — the main missing structural item.
2. **Backing plate not sourced, and size depends on the (uncertain) non-isolated tray
   fundamental** — estimated joint-governed ~120–340 Hz rigid. **Estimate/measure the tray
   fundamental first, THEN size the plate so its modes bracket that resonance.** Do not lock
   the plate to ~85 Hz prematurely.
3. **Instrumentation** — no force channel yet. Candidate path: Dewesoft miniature triaxial
   (e.g., Dytran 3263A) + Dewesoft DAQ (IEPE + FRF software) + modal hammer + 740B02 strut
   strain. Pursue LASIR borrow first; confirm model #/cal cert/sensitivity/mass; avoid the
   unlabeled/"BROKEN" rental units.
4. **Plate handling** — 245+ lb on bungees needs a frame/gantry + lift points + 2–3 people.
   Consider 3 ft (138 lb) if rigging is limited (recompute modes first).
5. **Joint damping** — low, amplitude-dependent, least-repeatable element ⇒ expect nonlinearity.
   Mitigate: controlled/logged preload, low- vs high-level sweeps (amplitude-dependence check),
   assemble/reassemble repeats.
6. **Acceptance criteria not yet quantified** (Section 5).
7. **Confirm rod-end bore = 5 mm on arrival** — RESOLVED understanding: the "M3" in the strut
   part code is the rod-end's own *stud thread*, not the ball bore; the bore takes the **M5 pin**
   (M5 hardware already in hand and correct). One caliper check closes it definitively.
8. **M6×12 base screws** short for thick brackets — may need M6×16/20.

---

## 7. Alignment with Round-3 / BayesX (no durable changes made)

- Non-isolated, **joint-governed stiffness + damping** = exactly the parameters Round 3 infers;
  the **force-limiting notch** is the Round-3 headline; **interface force** = the netCG numerator.
- **Flight-is-isolated** (~low mounted frequency, elastomeric bushings) is a **documented known
  difference**, not a contradiction to fix.
- **No Round-3 task card or notes/ files were modified.** Re-anchoring Round 3 to an isolated
  case (if ever desired) is a durable-rule change requiring human approval.

---

## 8. Immediate next actions

- [ ] **Confirm rod-end ball bore = 5 mm** on strut arrival (M5 pin hardware already in hand).
- [ ] Source **6 clevis brackets** (ear ≥6 mm, double-shear).
- [ ] Get a **first estimate of the non-isolated tray fundamental**, then size the steel plate.
- [ ] Plan **plate rigging** (frame + bungees + lift points).
- [ ] Lock the **instrumentation borrow** (LASIR / UTC): hammer + IEPE DAQ + strain sensors.
- [ ] Produce the **drill-ready hexapod hole map** for the MB3030/M.
- [ ] Define **quantitative acceptance criteria** (Section 5).
