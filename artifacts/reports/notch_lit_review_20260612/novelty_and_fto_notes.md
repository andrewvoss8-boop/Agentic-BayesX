# Novelty and FTO Notes — NOT a legal opinion

Status: YELLOW. This is engineering prior-art triage only. It is not a legal
freedom-to-operate (FTO) opinion, not a patentability opinion, and not claim
construction. Disclose any potentially patentable BayesX force/response-limiting
work to the Purdue/PRF IP officer before public sharing, including talks, papers,
Substack posts, slide decks, GitHub releases, or sponsor packets.

## Patent Search Scope

Surfaces searched on 2026-06-12: Google Patents, open web search, Google Patents
cited-by/citing-family pages for US8731868B2, and keyword searches for force
limiting, response limiting, notching, transfer path analysis, blocked force, MIMO
system identification, and vibration digital twin. This was not an attorney-grade
classification search.

## Flagged Patent: US8731868B2

US8731868B2, "Transfer path analysis," has priority date 2008-05-01, filing date
2009-04-29, publication/grant date 2014-05-20, and Google Patents lists it as
active with adjusted expiration 2030-03-13. Inventors are Janssens, Mas,
Gajdatsy, Van der Auweraer, and Gielen; the original assignee is LMS
International NV and Google lists Siemens Industry Software NV as current
assignee. Tier: patent. Source: https://patents.google.com/patent/US8731868B2/en

Engineering summary: the patent covers transfer path analysis using input and/or
response data plus system response functions, with a parametric model for load
estimation and path contributions. The Google Patents text says the data may be
measured or simulated, lab or in-situ, and the parametric load model can be a
physical model such as a mount model, constant mobility model, or band estimator.

Why it matters: BayesX's empirical interface-load workflow sits near TPA/source-
transfer-receiver methods when it estimates loads from measured responses and
response functions. Any product claim that uses parametric load models plus
measured transfer functions for path/load estimation should be reviewed against
this family.

Possible design-around direction to discuss with counsel: emphasize aerospace
qualification force/response limit generation, 6-DOF sparse interface apparent
mass, explicit moment/per-foot observability, standards-backed 7004C/ISO 23670
gates, and uncertainty/status reporting rather than generic acoustic/vibration TPA
path contribution analysis. Do not rely on this as legal advice.

## Adjacent Patents Found

| Patent | What it covers | Relevance to BayesX | Crowded/open read |
|---|---|---|---|
| US8731868B2, Transfer path analysis | Parametric-load TPA from response/input data and system response functions. | Directly adjacent to empirical load/path identification. | Crowded for generic TPA/load-estimation claims. |
| US11187619B2, Method and apparatus for detecting vibrational and/or acoustic transfers in a mechanical system | Neural-network detection/estimation of transfer behavior from input/response data. | Adjacent to data-driven transfer prediction. | Crowded for generic ML transfer-function detection. |
| US12050125B2, Controlled blocked force exciter for system identification in assembled structure | Controlled blocked-force exciter for fast in-situ MIMO system identification and blocked-force transfer functions. | Very adjacent to sparse in-situ MIMO interface/system response identification. | Crowded for controlled source/blocked-force system-ID hardware workflows. |
| US7542887B2, Dynamic analysis of complex systems | LMS dynamic analysis / complex system modeling prior art cited by US8731868B2. | Background TPA/dynamic-analysis family. | Crowded for broad dynamic-analysis software claims. |
| US6860152B2, High-frequency multiple-degree-of-freedom vibration test machine | MDOF vibration machine hardware. | Adjacent to multi-axis test hardware, not to Bayesian limiting logic. | Crowded for shaker hardware; less relevant to software/data method. |
| US8392000B2, Adaptive notch filter | Adaptive notch filter for control of flexible modes. | Uses "adaptive notching" language but not vibration qualification force/response limiting. | Crowded for generic adaptive notch filters; weakly relevant to test notching. |

## Candidate Novelty vs Prior Art

| Candidate BayesX idea | Closest prior art | Crowded or open? | Notes before disclosure/publication |
|---|---|---|---|
| Generic impedance/FBS coupling from measured interface matrices | de Klerk/Rixen/Voormeeren FBS, LM-FBS, Mayes transmission simulator, Neubert/7004C impedance. | Crowded. | Do not claim as novel. |
| Generic response limiting or force limiting with notches | NASA-HDBK-7004C, ISO 23670, Sweitzer, NIRSpec, TESS, CoNNeCT. | Crowded. | Do not claim as novel. |
| Multi-component force/moment channels in spacecraft tests | RP-1403, NASA-HDBK-7004C, Qiu et al. eight-transducer summing, NIRSpec mount strain gages. | Crowded in measurement practice. | Novelty, if any, is not "measure moments." |
| Resultant-trap diagnostic: net in-axis force can hide rocking/per-foot overtest | Implied by force/moment practice; not found as a named force-limit failure mode. | Possibly open, but basic statics reduces patent strength. | Useful as teaching/verification rule; legal novelty likely depends on integration with a method. |
| Modal-overlap/coherence rule for notch spatial reach | SEA/modal-overlap literature plus 7004C attachment-coherence warning. | Partly open in force-limiting context. | Could be valuable as an engineering rule, but verify with real data before public novelty claims. |
| Bayesian 7004C / robust apparent-mass twin: sparse 6-DOF interface data plus prior model, uncertainty-gated force/response limits, green/yellow/red status | Bayesian FEM updating, statFEM, FBS, TPA, ISO/NASA force limiting. | More open as a specific combination, but adjacent patent space is active. | Disclose before public sharing; attorney should claim-chart against US8731868B2, US12050125B2, and Siemens TPA/ML families. |
| Integrated-configuration transmissibility requirement for response-limit proxy | ISO response-limited testing, NIRSpec low-level runs, standard FRF practice. | Likely known practice, not patentable alone. | Treat as a safety/harness rule. |

## FTO Red Flags

- Generic "estimate loads from responses and transfer functions using a parametric
  model" is close to US8731868B2.
- Generic "use neural networks or ML to detect vibrational/acoustic transfers" is
  close to US11187619B2.
- Generic "controlled blocked-force source for MIMO system identification in an
  assembled structure" is close to US12050125B2.
- Generic force-limited and response-limited vibration testing is heavily covered
  by standards and public practice; novelty must be narrower than notching or
  force limiting itself.

## Safer Engineering Framing

For internal work, frame the contribution as a checked engineering workflow:
1. state force/response QOI and quantity contract;
2. measure enough sparse interface DOFs to distinguish bounce from rocking;
3. use FBS/impedance algebra as known coupling machinery;
4. propagate sparse-data/model uncertainty through a Bayesian or statistical
   update;
5. report green/yellow/red status and worst-case observability gaps.

This framing is still IP-relevant and should be disclosed before public sharing.
