# Decisions Log — notch_lit_review_20260612

- D1 (scope, 2026-06-12): Review covers multi-point / 6-DOF / sparse-measurement
  force-limiting and response-limiting literature, plus patent/FTO triage. It tests
  the four in-house findings from `notch_multipoint_7004c_20260611` against
  external sources. No new structural simulation, no sampler, and no figures are
  required.
- D2 (source discipline): A claim is citable only when a source was verified by
  open web, publisher abstract/landing page, accessible PDF, Google Patents, NASA
  NTRS, standards landing page, or an equivalent primary/near-primary page in this
  session. Paywalled papers may be cited only for bibliographic facts visible on a
  landing page; their detailed conclusions must be marked limited-access if not
  available elsewhere.
- D3 (IP boundary): Novelty/FTO notes are engineering research triage only, not a
  legal opinion. Anything potentially patentable or design-around relevant must be
  disclosed to the Purdue/PRF IP officer before public sharing.
- D4 (status standard): The review is GREEN only if required artifacts exist and
  no citation is knowingly fabricated. It is YELLOW if coverage gaps remain but are
  documented. It is RED if an unverified citation is used as fact, a required
  artifact is missing, or IP caveats are omitted.

## Search Scope Log

- Date: 2026-06-12, timezone America/New_York.
- Databases / surfaces used: NASA NTRS, NASA/Experior/Vibrationdata open PDFs,
  ISO standards preview, ECSS landing page, MIL-STD-810H Method 514.8 public PDF
  excerpt, ESA/NIRSpec PDF, AIAA/Springer/ASME/TU Delft/TUM/OSTI/repository
  landing pages, ISMA open PDFs, Google Patents, and open web search.
- Search terms used: force limited vibration, apparent mass, dynamic mass,
  mechanical impedance, moment limiting, multi-axis vibration test, MIMO random
  vibration control, frequency based substructuring, Lagrange multiplier FBS,
  response limiting notching, modal overlap factor, drive point impedance,
  rotational degrees of freedom substructuring, transfer path analysis, blocked
  force, US8731868B2, Bayesian FEM updating, Bayesian operational modal analysis.
- Local extraction: Python `pypdf` was used for open PDFs because `pdftotext` was
  not installed. Extracted/checked PDFs included NASA-HDBK-7004C, NASA RP-1403,
  NASA/TM-2012-217627, TESS force-limited random vibration paper, and NIRSpec
  interface-force notching paper.

## Inaccessible / Limited Sources

- Piersol et al. 1989 Orbiter sidewall payload report: not accessed in full; used
  only through NASA-HDBK-7004C's description.
- Sweitzer 1987 mechanical impedance correction: not accessed in full; used only
  through NASA-HDBK-7004C / Springer references.
- O'Hara and Remmers 1969 plus Wada et al. 1972 effective-mass sources: not
  accessed in full; used only through NASA-HDBK-7004C's effective-mass discussion.
- Soucy/Dharanipathi/Sedaghati 2005 IMAC comparison paper: not accessed in full;
  metadata verified through NASA-HDBK/Springer references.
- Scharton 1995 and Soucy/Dharanipathi/Sedaghati 2006 AIAA papers: publisher
  metadata/DOI verified; detailed claims only used where also supported by NASA
  handbook, open NASA papers, or accessible abstracts.
- No professional patent database or attorney claim chart was run. Patent notes
  are therefore engineering triage only.
