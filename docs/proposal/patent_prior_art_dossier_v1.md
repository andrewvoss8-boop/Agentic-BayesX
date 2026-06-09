# Prior-Art & FTO Dossier (v1)

Provenance: produced by browser Claude (web search ON) from the prompt in this project, pasted back by
Andrew 2026-06-08. SCREENING PASS, NOT a clearance opinion. Saved verbatim for traceability. Synthesis +
caveats are folded into docs/proposal/patent_ideas_ranked.md ("Prior-art dossier v1 fold-in").

---

Scope of THIS session: patent-database verification + targeted white-space scan. Sources below were
fetched this session only. PATENT records are the priority; prior reviews surfaced only PAPERS.

Term key (first use): StatFEM = statistical finite element method (FEM that fuses physics model + sensor
data with full uncertainty). QOI = quantity of interest (the number you actually care about, here an
interface load). GP = Gaussian process (a flexible probabilistic curve/function model). FTO = freedom to
operate (can you practice without infringing an active patent). 101/Alice = US rule that bars patenting
an "abstract idea" unless tied to a concrete technical improvement.

## 1. What was actually found this session

PATENTS verified (claims read):
- US10585420B2 family, "geometry-compliant lattice structures" (ABEMIS/Doehring). Independent claims
  cover generating an FE mesh, building a lattice cell per mesh element, and deforming the lattice to
  conform to part geometry for additive manufacturing. [PATENT] Claims are GEOMETRY-GENERATION only. No
  dynamic/vibration-attenuation objective, no model-discrepancy posterior.
  (patents.google.com / USPTO print 11073819, 10642253, 11989003 are the same lattice-geometry family.)
- Doehring/ABEMIS markets "anti-vibration" meta/hyper-structures (LinkedIn company description), and the
  mesh-to-lattice generation IP is dated 2021. Marketing claims attenuation; the issued CLAIMS do not.
- CN114444366A [PATENT] bridge digital-twin FE model updating from traffic load + sensor vibration. Civil,
  input-load-driven, not output-only, not a force-limited interface-load QOI.
- US11010504 (Siemens) [PATENT] lattice design via parametrized unit cells for topology optimization.
  Deterministic material modeling; no Bayesian discrepancy posterior.
- Other lattice/AM patents (US11351732 digital-thread AM lattice; US10796039 lattice FE mesh; CN105900145A)
  are geometry/AM-process, not dynamic-uncertainty design.

PAPERS confirmed (anchors, all already known to you):
- Girolami 2021; Duffin 2021/2022 StatFEM/digital-twin foundations.
- Febrianto et al. arXiv:2103.13729 StatFEM railway bridge digital twin (strain QOI, input-load assisted).
- Beck & Katafygiotis 1998 Bayesian model updating; Behmanesh/Papadimitriou hierarchical updating;
  Kiran/Das review trend (output-only flagged un-researched).

NOT located this session (genuinely unsearched, see SEARCH NEXT): the 2026 elastodynamic StatFEM arXiv
(your 2604.12688 anchor), Lens.org/Espacenet assignee:ABEMIS hit list, automotive-NVH and defense filings,
any "AI provisional" ABEMIS pending apps.

## 2. Per-idea read (condensed; full claim drafting deferred)

A. THE BUNDLE — assembled-structure dynamic StatFEM, unknown forcing, discrepancy where it lives, output
to a force-limited interface-load QOI, held-out validation.
- Closest: Febrianto 2103.13729 [PAPER] (StatFEM digital twin, but strain QOI, not force-limited load);
  CN114444366A [PATENT] (input-load-driven, civil); force-limited-load literature [PAPERS] all
  handbook/2-DOF, no Bayesian StatFEM load QOI patent found.
- Verdict: novelty High, non-obviousness Medium-High. The combination (output-only + load QOI +
  force-limiting) is unclaimed in patents found.
- 101 anchor: claim as a method of CONDUCTING/SPECIFYING a force-limited vibration TEST (measured forces,
  notching) driven by the posterior — a physical test process, not pure math.
- FTO: none blocking found this session.
- Differentiators: (i) output-only forcing carried to interface LOAD; (ii) force-limit notch derived from
  the StatFEM posterior; (iii) held-out load-QOI calibration acceptance criterion.

B. SPEARHEAD — part-type/stiffness-indexed GP discrepancy, orthogonal to calibrated physics on the OUTPUT.
- Closest: Plumlee 2017 orthogonal-GP discrepancy [PAPER]; Schneider space-frequency model error [PAPER].
  No patent found indexing discrepancy by structural part type.
- Verdict: novelty High (as a patent), non-obviousness Medium-High.
- 101 anchor: tie the indexed discrepancy to a sensor-instrumented updating apparatus producing a
  validated load prediction.
- FTO: none found.
- Differentiators: (i) discrepancy indexed by part type/element stiffness; (ii) output-orthogonal
  construction guaranteeing physics/error separability; (iii) joint-type-specific GP kernels.

C. Complex lossy joint impedance as the uncertain StatFEM element in substructuring/CMS.
- Closest: jointed-structure dynamics [PAPERS, Brake/Iwan]; no StatFEM-joint-impedance patent found.
- Verdict: novelty Medium-High; non-obviousness Medium. Watch automotive-NVH filings (likely hidden).
- 101 anchor: frequency-based substructuring apparatus/process.
- FTO: UNRESOLVED — NVH is the likely blocking-art reservoir.

D. Output-only/operational dynamic StatFEM to a LOAD QOI. Overlaps A; treat as A's method core.
- Verdict High novelty in patents found; non-obviousness Medium-High.

E. Agentic/technician-data model updating on installed parts.
- Closest: digital-twin updating patents (CN114444366A) [PATENT]. Agentic-autonomy angle not found.
- Verdict Medium; broad SHM-automation art likely exists (unsearched). 101 risk higher (looks like
  software workflow) — anchor to instrumented field hardware.

F. QOI-weighted likelihood (weight fit near load-driving resonance).
- Verdict Medium novelty, LOW-Medium non-obviousness (looks like an obvious weighting tweak). Best as a
  DEPENDENT claim under A/B, not standalone.

G. QOI-targeted optimal sensor placement + drive-point "echolocation."
- Closest: Kammer EI, Papadimitriou QOI-OSP [PAPERS]; OSP patents likely exist (unsearched).
- Verdict Medium; the load-QOI + drive-point-excitation-design pairing may be clean. Needs OSP patent scan.

H. Discrepancy-aware / uncertainty-aware TOPOLOGY OPTIMIZATION (optimize against a StatFEM posterior that
   INCLUDES calibrated discrepancy).
- Closest: US11010504 Siemens [PATENT] (deterministic lattice TO); ABEMIS US10585420B2 family [PATENT]
  (geometry only). Neither optimizes against a discrepancy-inclusive posterior.
- Verdict: novelty High, non-obviousness Medium-High. This is a clear gap vs the verified lattice patents.
- 101 anchor: claim the manufactured ARTICLE / AM process whose geometry is the optimizer output —
  article + process survives Alice better than the algorithm alone.
- FTO: sits CLEAR of ABEMIS geometry claims (they claim mesh->lattice conforming geometry; you claim a
  design OBJECTIVE/posterior). Confirm against pending ABEMIS apps before filing.
- Differentiators: (i) objective evaluated on posterior-with-discrepancy; (ii) attenuation/bandgap target;
  (iii) discrepancy-driven robustness margin baked into the printed geometry.

I. Vibration-attenuating microstructure/metamaterial via Bayesian optimal experiment design (BOED).
- Closest: ABEMIS anti-vibration meta-structure marketing (no matching issued claim found) [PATENT/marketing
  gap]; metamaterial-bandgap-Bayesian-optimization [PAPERS, unsearched in patents].
- Verdict: novelty High if BOED design loop is the claimed step; non-obviousness Medium-High.
- 101 anchor: manufactured metamaterial article + the experiment-design-driven fabrication process.
- FTO: metamaterial/acoustic (G10K11/172) patent scan still required.

## 3. Synthesis

Cleanest white space (ranked, based on patents found vs not found this session):
1. A/D — force-limited interface-load QOI from output-only dynamic StatFEM. No blocking patent surfaced;
   strong 101 anchor via the physical test process. FILE FIRST (provisional).
2. H — discrepancy-aware topology optimization. Verified clear of ABEMIS/Siemens geometry claims; natural
   ABEMIS/Doehring collaboration vehicle. Strong second provisional.
3. B — part-type-indexed orthogonal GP discrepancy. Clean in patents found; pairs as method backbone.
4. I — BOED metamaterial. Promising but needs the metamaterial patent scan before confidence.
5. C/G — promising but FTO-exposed (NVH for C; OSP patents for G) until searched.
F and E are dependent-claim / weaker-standalone material.

Patents found-vs-not map:
- Found & cleared: lattice-geometry family (ABEMIS US10585420B2 etc.), Siemens US11010504, civil
  digital-twin CN114444366A. None block A/B/D/H as scoped.
- NOT searched yet (unknown): automotive NVH joint-impedance (C), OSP (G), acoustic-metamaterial (I),
  aerospace/defense force-limiting filings (A), ABEMIS pending "AI provisionals" (H/I).

## 4. SEARCH NEXT (prioritized, for next session)

1. Lens.org + Espacenet assignee:ABEMIS and inventor:Doehring — pull the full family incl. any pending
   apps; read claims of US11327465B2 and US12111630B2 directly (not yet individually fetched).
2. Fetch the 2026 elastodynamic StatFEM paper (arXiv 2604.12688) to sharpen A/D differentiation in writing.
3. Google Patents CPC G01M7/02 + "force limit*" + Bayesian/probabilistic — confirm no force-limited-load
   prediction patent exists (A/D clearance).
4. CPC F16F + automotive "NVH" + joint + "model updating"/impedance — the hidden-art reservoir for C.
5. CPC G10K11/16-172 + "bandgap" + "Bayesian optimization"/"optimal experiment design" — for I.
6. OSP patents: CPC G01H/G06F30 + "optimal sensor placement" + "information gain" — for G.
7. CPC G06F30/23 + G06N7/01 + "topology optimization" + "model uncertainty"/"discrepancy" — confirm H gap.
8. USPTO assignment search on ABEMIS to catch unpublished continuations.

Still needs a PROFESSIONAL patent/FTO search before any filing decision: full-text claim charting against
issued claims in CPC F16F, G01M7/02, G10K11, G06F30/23; defense/ITAR-adjacent filings; and any
non-English (DE/JP automotive, CN) family members. This v1 is a screening pass, not a clearance opinion.
[OPINION] throughout; novelty/FTO verdicts are not legal advice.
