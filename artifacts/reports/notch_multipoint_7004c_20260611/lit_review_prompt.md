# Agent prompt — literature review for multi-point / empirical force- & response-limiting

Copy everything between the rules below into a fresh agent session (a model with web/
library access). It is self-contained. Follow this project's AGENTS.md rules:
plain English, define ML/stats terms, **no fabricated citations**, every claim
traceable to a real source, green/yellow/red honesty, and DISCLOSE-before-publish
on anything IP-relevant.

---

## ROLE
You are a research assistant doing a rigorous, source-traceable literature review
for the Agentic BayesX project. The goal is to map what is already known (and
patented) about doing force-limited and response-limited vibration testing for
**multi-point, 6-DOF (rocking-capable) interfaces using sparse interface
measurements instead of a full coupled forced FEM**, so the team can (a) avoid
re-deriving known results, (b) position any novelty honestly, and (c) feed a
freedom-to-operate (FTO) check.

## CONTEXT (what we already found in-house — verify, don't assume)
We ran a deterministic analytical study (`notch_multipoint_7004c_20260611`,
EX-A…EX-E) anchored to NASA-HDBK-7004C. Key in-house findings to test against the
literature:
1. 7004C's semi-empirical / simple-&-complex-TDOF / single-node impedance methods
   are scalar, single-interface, in-axis.
2. With spaced feet + 6-DOF, apparent mass is a 6×6 matrix; rocking loads cancel in
   the net in-axis force (the "resultant trap"); a single notch becomes a
   frequency-shifted cluster across mean/differential interface channels.
3. Notch spatial reach is governed by the backing's modal overlap factor, not a
   fixed radius (global when overlap < 1; ≈ λ/4 local when overlap ≳ 1).
4. The impedance method with MEASURED interface quantities reconstructs the coupled
   loads exactly; sparsity is the cost (1 foot → bounce only; ≥3 spaced feet →
   rocking/moment); response-limit transmissibility must be calibrated in the
   integrated configuration.

## QUESTIONS TO ANSWER FROM THE LITERATURE
A. **Force limiting beyond scalar 7004C.** Has multi-axis / multi-point / matrix
   (MIMO) force limiting been formalized? Moment limiting? Per-foot vs net-force
   limiting? Who, when, what was concluded?
B. **The resultant-force / rocking blind spot.** Is the cancellation of rocking
   loads in the summed interface force documented? Any standard practice for
   detecting/limiting it (moment gauges, multi-component dynamometers)?
C. **Apparent-mass / impedance measurement in practice.** Methods to measure
   interface apparent mass (drive-point and cross), to combine per-foot apparent
   masses into an interface model (cf. 7004C p.29, Piersol 1989), and the
   low- vs high-frequency / closely- vs widely-spaced validity limits.
D. **Empirical coupled-response prediction without a coupled FEM.** Frequency-Based
   Substructuring (FBS) / impedance coupling / Norton-Thevenin for test prediction;
   how sparse the interface measurement can be; experimental-dynamic-substructuring
   accuracy and pitfalls (rotational DOFs, expansion).
E. **Response limiting and transmissibility-based notching.** Theory and practice of
   response limiting (the industry norm); transmissibility/notch-control criteria
   (Sweitzer and successors); how control points are chosen; configuration/boundary
   dependence of transmissibility.
F. **Spatial reach / modal overlap / coherence.** Statistical-energy-analysis and
   modal-overlap treatments of when an interface moves coherently vs locally;
   bending-wavelength criteria; how this maps to "how far from a foot."
G. **Bayesian / statistical / data-driven approaches.** Bayesian or statistical FEM
   updating, in-situ/operational apparent-mass identification (OMA), uncertainty
   quantification applied to force/response limits or to interface environments.
H. **Standards & flight practice.** NASA-HDBK-7004C revisions, ECSS/ESA handbooks,
   MIL-STD-810, JPL/GSFC practice, and any multi-point/CLA (coupled loads analysis)
   guidance relevant to interface limiting.

## SEED AUTHORS / TERMS (find their key papers + who cites them)
Scharton (force limiting, apparent mass, JPL); Soucy/Sarafin (C² statistics);
Smallwood; Salter (1964, attachment uniformity); Sweitzer (1987 notching);
O'Hara & Remmers / Wada (effective mass); Neubert (impedance, skeleton); Piersol
(combining attachment apparent masses); for substructuring: de Klerk/Rixen/Voormeeren
(FBS classification), Allen/Mayes (experimental dynamic substructuring), transmissibility
substructuring. Terms: "force limited vibration", "apparent mass", "dynamic mass",
"mechanical impedance", "moment limiting", "multi-axis vibration test", "MIMO
random vibration control", "frequency based substructuring", "Lagrange multiplier
FBS", "response limiting notching", "modal overlap factor", "drive point impedance",
"rotational degrees of freedom substructuring".

## ALSO (IP / FTO — flag, do not opine legally)
Search patents around Bayesian/adaptive/multi-point force or response limiting and
notch control. Specifically locate and summarize **US8731868B2** (our flagged
design-around target) and find adjacent patents. Output a candidate-novelty vs
prior-art table; mark what looks crowded vs open. State clearly this is NOT a legal
FTO opinion and that disclosure to the IP officer must precede any public sharing.

## DELIVERABLES (write to `artifacts/reports/notch_lit_review_<date>/`)
1. `lit_review.md` — organized by questions A–H; every claim has a citation
   (author, year, venue, DOI/URL). Mark each in-house finding (1–4 above) as
   CONFIRMED / PARTIALLY-KNOWN / NOVEL-AS-FAR-AS-FOUND / CONTRADICTED, with the
   supporting reference.
2. `bibliography.bib` (or .md) — full references, deduplicated.
3. `novelty_and_fto_notes.md` — candidate-novelty vs prior-art table + the patent
   summaries (incl. US8731868B2) + crowded/open assessment + the not-legal-advice +
   disclose-first caveats.
4. `gaps_and_next_experiments.md` — what the literature leaves open that our
   coupled-model thread (ShockSat × tray) could answer.
5. A short `decisions_log.md` recording search scope, databases used, dates, and any
   source you could NOT access (so the next agent knows the coverage boundary).

## RULES
- No fabricated or guessed citations — if you cannot verify a source, say so and
  mark it UNVERIFIED. A plausible-looking but unconfirmed reference is a RED finding.
- Distinguish peer-reviewed, standards/handbooks, conference, thesis, vendor, and
  web sources by tier.
- Prefer primary sources over reviews; record what you could not access.
- Keep the in-house claims falsifiable: actively look for work that CONTRADICTS them.
- End with a one-paragraph honest summary: what is genuinely known, what is our
  likely-novel contribution, and what still must be tested on real hardware.
