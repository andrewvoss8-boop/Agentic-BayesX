# paper_draft_dce_20260702 — journal paper draft (v0.1, internal review)

`paper_draft.md` (v0.2; v0.1 archived) — full draft targeting *Data-Centric Engineering* (Cambridge) or similar: the validation
harness (coverage-first + leave-modes-out audit) + three pre-registered studies on the real ShockSat
(method selection GREEN 22/0/0; plate-test rehearsal falsification 28G/3Y/1R; composite bake-off YELLOW
57G/6Y/0R). Every number traces to a workspace checker; figure plan maps to existing artifacts.

OPEN ITEMS FOR ANDREW (flagged, not decided by the agent):
1. Venue: DCE's editor-in-chief is Mark Girolami (statFEM originator) — strong topical fit since the winning
   formulation is statFEM-style and companion experiments engage statFEM/PIFT directly; consider whether
   that's a plus (fit) or needs framing care. Alternatives: MSSP, JSV, ASME J. Verif. Valid. UQ, AIAA.
2. Authorship, affiliations, advisor list; AI-assistance disclosure wording (current draft has one line).
3. NASA ShockSat data provenance/permissions for publication.
4. References need completion (placeholders marked).
5. The paper states negatives prominently by design — confirm you're comfortable with that framing.

v0.2 changes (2026-07-02): (a) references completed from knowledge with full bibliographic detail — items
marked [VERIFY] could not be web-checked in this environment (no browser tool) and MUST be confirmed before
submission (esp. the internal shorthand "Kiran" reference, the NASA-HDBK-7004C revision year, the Febrianto
DCE article number, and the Schneider 2022 details); (b) 13 figures embedded with full captions (copies in
figures/, provenance in each caption); (c) jargon pass — every acronym defined at first use (FEM, FRF, MAC,
DOF, QOI, NUTS, CRPS, ESS, statFEM, dB, CG, SHA-256), internal shorthands ("arms", "money figure", "L5",
"drumhead", "climatology", "MAP") replaced with plain descriptions.

v0.3 changes (2026-07-02, post browser-verification): "Kiran" identified = Kiran, Das & Bansal (2025),
Prob. Eng. Mech. 80, 103761 — cited in body (S0 eigenvalue likelihood Eq. 25; model-class selection Eqs.
43-44) and reference list. NASA-HDBK-7004C corrected to 2012. Girolami 2021 statFEM title corrected to
"...observation data and model predictions." Schneider et al. (2022) now cited in body at the F(k)
introduction + discussion. All 25 references carry DOIs/identifiers; only Vanik et al. (2000) still flagged
[VERIFY] for a final spot-check. v0.1/v0.2 archived (paper_draft_v0.1.md; git history for v0.2).
