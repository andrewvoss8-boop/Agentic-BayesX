# damping_indicators.md — is there complex/non-proportional damping at the hard locations?

Follow-up to Card D (Andrew's question). Source: the AUTHORITATIVE NASA free-free modal-test summary
`ShkSat Free Free Mode Shapes Summary VJS.xlsx` (impact ref 1101_Zm). Reproduces from
`code/damping_indicators.py` → `out/damping_indicators.json`.

> "Complex"/non-proportional damping = the damping cannot be diagonalized by the undamped mode shapes; its
> signature is **mode-shape-dependent damping** (not a smooth function of frequency) that **concentrates at
> dissipative interfaces** (bolted joints, bulkheads, contact), and **spatially-varying phase** in the mode
> shapes (complex modes).

## Answer: YES — strong INDIRECT indicators; the direct (complex-shape) evidence was discarded in the fit.

### 1. Measured damping is highly non-uniform and tracks the interfaces (the key indicator)
| freq (Hz) | ζ (% crit) | mode description (NASA analyst) |
|---|---|---|
| **122.3** | **1.756** | Aluminum, Steel **Bulkheads, and Cross in-phase drum modes** |
| **118.5** | **0.834** | Aluminum & Steel **Bulkhead out-of-phase drum modes**; Cross 2nd bending |
| **107.5** | **0.505** | **Cross drum mode** |
| 188.6 | 0.440 | Panels **below the Aluminum bulkhead**, out of phase |
| 70.0 | 0.386 | Bottom panels in phase (simple panel) |
| 75.0 | 0.358 | Bottom panels (simple panel) |

- Damping spans **0.124–1.76% critical = a 14× spread** across 18 in-band modes.
- **Joint/bulkhead/cross modes average ζ 0.56% vs 0.27% for simple panel/other modes — 2.1× more damped**, and
  the **single most-damped mode (1.76%, 122 Hz) is the bulkhead+cross drum mode**.
- Damping that jumps with mode TYPE (which interface flexes), not smoothly with frequency, is the textbook
  signature of **localized, non-proportional damping** — Rayleigh/proportional damping cannot produce a 14×,
  shape-correlated spread. The dissipation lives in the **bolted-joint / bulkhead interfaces** — exactly the
  hard channels (ch40/52/69 bulkheads & bolted joint; the cross near the strut ch92).
- The "**out-of-phase** bulkhead" modes (118.5 Hz) are where the Al and steel bulkheads shear across the bolted
  joint — out-of-phase motion across a damped interface is precisely where complex (phase-shifted) modes arise.

### 2. Honest limits / caveats
- **The direct complex-mode evidence was not retained.** The `.ash` survey stored **real** normal-mode shapes
  (OPoly polyreference curve-fit → real float32 components), i.e. the curve-fit *assumed proportional damping*
  and discarded any spatial phase. So we see interface-localized *damping magnitude* (strong indirect indicator),
  not directly-measured complex *mode shapes*. Confirming true complex modes needs the complex residues / FRF
  phase at the hard channels (the raw impact FRF or an `_EXP` export), not analyzed here.
- **Data-hygiene flag:** the modal-twin's parsed `.ash` `damp` array (0.25–1.05) disagrees with this
  authoritative column (0.0012–0.0176) by ~65× and is mislabeled "fraction of critical" — the real measured
  damping is **0.12–1.76% critical**. (Card A used a uniform ζ=1% placeholder, so this did not corrupt Card A,
  but ζ=1% **over-damps** the light panel modes (~0.3%) and **under-damps** the bulkhead drum modes (1.76%).)

### 3. Why this matters for Card D's verdict
This is the missing piece that explains the per-sensor amplitude residual the re-meshing campaign could not fix:
- A **uniform** ζ (Card A) is wrong in both directions (over-damps panels, under-damps bulkheads) → it cannot
  match the peak amplitudes at the bulkhead/joint channels.
- A **real-eigenvalue/MAC** stiffness or mesh update (Card D) carries **no damping at all** → structurally
  blind to this effect.
- The data-justified improvement is therefore a **non-proportional (complex) damping model** — per-mode or
  per-interface modal damping, or a localized joint-damping matrix — calibrated to exactly these measured
  per-mode ζ. That is the concrete "suggest an improvement" lever, and it is a **damping/data** lever, not a
  mesh/stiffness one — confirming the Card D boundary (re-meshing is not the fix).
