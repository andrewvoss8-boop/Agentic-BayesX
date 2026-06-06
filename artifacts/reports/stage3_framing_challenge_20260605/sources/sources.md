# Sources — Stage-3 framing challenge (fetched THIS session, 2026-06-05)

Honesty rule: every external claim in `framing_challenge.md` is tagged and resolved here with the URL,
HTTP status, byte size, and a short SHA-256 prefix of the file fetched this session. Claims I could NOT
verify from a fetched source are marked `[SPECULATIVE]` or `[OPINION]` in the report and are NOT asserted
as fact.

## Web fetches (this session)
| tag | what | URL | HTTP | bytes | sha256[:16] |
|---|---|---|---|---|---|
| `[FLV]` | NASA Force Limited Vibration Testing Monograph (Scharton, JPL) — overtest problem, dynamic-absorber effect, apparent/effective/residual mass, notching | https://ntrs.nasa.gov/api/citations/19970023193/downloads/19970023193.pdf | 200 | 6,537,464 | 57918ac84bf95f2f |
| `[YUNIS]` | Yunis, *The Standard Deviation of Launch Vehicle Environments* (NTRS 20120001364) — 3 dB flight-to-flight, P95/50 MPE | https://ntrs.nasa.gov/api/citations/20120001364/downloads/20120001364.pdf | 200 | 1,586,133 | 7cf1613e729325c0 |
| `[STATFEM]` | Girolami et al., *The statistical finite element method (statFEM)* (arXiv:1905.06391) — abstract: data = FE + model misspecification + noise | https://arxiv.org/abs/1905.06391 | 200 | 50,470 | f9449eb1c20ae40c |
| `[BMA]` | Bayesian model averaging (Wikipedia) — definition: average predictions weighted by posterior model probability | https://en.wikipedia.org/wiki/Bayesian_model_averaging | 200 | 337,820 | 3fe175dfe9b37919 |
| `[DT]` | Digital twin (Wikipedia) — definition | https://en.wikipedia.org/wiki/Digital_twin | 200 | 210,957 | 7a5c55eb77b366f3 |

## Repo PDFs READ this session (cited as primary; present in repo root)
| tag | what | file | note |
|---|---|---|---|
| `[KOH]` | Kennedy & O'Hagan (2001), *Bayesian calibration of computer models* | `KennedyOHagan_2002 (1).pdf` | abstract decoded this session: calibration + discrepancy + error; "predictions allow for all sources of uncertainty." |
| `[TMCMC]` | Ching & Chen (2007), *Transitional MCMC for Bayesian model updating, model class selection and model averaging* | `2007-...transitional-markov-chain-monte-carlo...pdf` | abstract read this session: TMCMC samples "multimodal PDFs, very peaked PDFs, and PDFs with flat manifold" and estimates model-class evidence for selection/averaging. |
| `[DTSTATFEM]` | Febrianto, Butler, Girolami, Cirak (2022), *Digital twinning of self-sensing structures using statFEM* | `digital-twinning-...statistical-finite-element-method.pdf` | abstract read: railway-bridge linear case study (benign/static regime). |

## Fetch FAILURES this session (so I do NOT cite from memory)
- Brynjarsdottir & O'Hagan (2014), *Learning about physical parameters: the importance of model
  discrepancy* — attempted `tonyohagan.co.uk` (404) and a Wiley DOI (403) and Semantic Scholar API
  (202, 0 bytes). **NOT fetched.** Where the report leans on its central claim (a flexible discrepancy
  destroys parameter identifiability unless given real structure), it is marked `[SPECULATIVE — not
  fetched this session]` and attributed to the *project's own* `notes/project_vision.md` §4, which
  records that citation.
- Plumlee (2017), *orthogonal Gaussian-process discrepancy* — arXiv id I tried (1411.3043) was an
  unrelated physics paper; **NOT fetched.** The orthogonality argument is attributed to the project's
  own vision doc and marked `[SPECULATIVE — not fetched]`.
</parameter>
</invoke>
