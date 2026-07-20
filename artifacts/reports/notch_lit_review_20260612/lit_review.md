# Literature Review: Multi-point / empirical force- and response-limiting

Date: 2026-06-12. Overall review status: YELLOW. The core sources were verified
from open PDFs, standards previews, NASA NTRS, publisher/repository pages, and
Google Patents. Caveat: several older conference papers are only visible through
handbook references or publisher metadata, so their detailed claims are marked
limited-access rather than treated as fully read.

Plain-English statistical note: no Bayesian inference was run here. "Bayesian"
means a probability-based updating method that combines prior engineering
assumptions with measured data to produce an updated uncertainty distribution.

Source tier key: Tier: standard / handbook; Tier: peer-reviewed; Tier:
conference; Tier: thesis; Tier: vendor or web; Tier: patent.

## A. Force Limiting Beyond Scalar 7004C

NASA-HDBK-7004C and Scharton's NASA RP-1403 formalize the main force-limited
vibration testing methods around the total reaction force divided by prescribed
acceleration, i.e. apparent mass at an interface. The handbook methods include
semi-empirical C^2 limits, simple and complex two-degree-of-freedom-system
(TDFS) methods, and an impedance method using source and load apparent masses
[NASA-HDBK-7004C, 2012; Scharton, 1997]. Tier: standard / handbook.

The formal 7004C derivations are mainly scalar and single-interface in their
equations, but the handbook and RP-1403 explicitly acknowledge multi-component
practice: triaxial force transducers, voltage summing, and measurement of
moments and forces at individual mounting points are discussed; RP-1403 says
cross-axis force and moments may need limits for large eccentric spacecraft
[NASA-HDBK-7004C, 2012; Scharton, 1997]. Tier: standard / handbook.

Spacecraft practice has gone beyond one force channel. Qiu et al. describe an
eight-force-transducer spacecraft setup that computes key summed forces and
moments for a force-limited test, with reported summing errors mostly within
about 10 percent in their low/high-level checks [Qiu et al., 2017,
doi:10.21595/vp.2017.19163]. Tier: conference.

The JWST NIRSpec experience used strain gages on three kinematic mounts to
recover axial and lateral force at each interface and then reconstruct a global
interface force from phase-coherent time signals; the paper states that PSD-only
summation was not sufficient because phase matters [Salvignol/Salvignola et al.,
2009]. Tier: conference.

Conclusion for A: multi-axis and moment measurement/limiting are known in
practice, but the reviewed standards do not provide a general sparse 6-DOF
matrix force-limit theory for per-foot versus net-force limiting. Status:
PARTIALLY-KNOWN.

## B. Resultant-force / Rocking Blind Spot

The literature documents the mechanism that makes the blind spot plausible.
NASA-HDBK-7004C states that uniform motion of test attachments can overtest
hardware relative to flight attachments that move with uncorrelated or
differential motion, especially for wide attachments on lightweight flight
structure excited by acoustic noise [NASA-HDBK-7004C, 2012]. Tier: standard /
handbook.

RP-1403 is explicit that multi-point connections are common in the real world
and difficult for impedance methods; it says the issue of overtesting due to
uncorrelated inputs at multiple attachment points had not been addressed in that
monograph [Scharton, 1997]. Tier: handbook.

The measurement practice also points to the blind spot. RP-1403 recommends
triaxial force transducers and says the six resultant forces and moments for a
single node can be measured with commonly four triaxial transducers and a voltage
summer when moments and cross-axis forces matter [Scharton, 1997]. NIRSpec's
phase-coherent force reconstruction is another example where individual mount
signals cannot be reduced safely to independent PSDs [Salvignol/Salvignola et
al., 2009]. Tier: handbook / conference.

I did not find a source using the exact phrase "resultant trap" or a worked
example where equal-and-opposite rocking foot loads sum to zero net in-axis
force while per-foot loads remain large. The cancellation follows directly from
force/moment statics and from the above practice, but direct documentation of the
trap as a force-limit failure mode remains limited in the searched sources.
Status: PARTIALLY-KNOWN.

## C. Apparent-mass / Impedance Measurement in Practice

NASA-HDBK-7004C defines apparent mass as the complex frequency-response function
(FRF) equal to force divided by acceleration. RP-1403 uses apparent mass as the
preferred impedance-like quantity for force limiting, while noting that apparent
mass is complex and frequency-dependent [NASA-HDBK-7004C, 2012; Scharton, 1997].
Tier: standard / handbook.

7004C describes measuring load apparent mass during low-level sine sweep or
random runs and measuring source apparent mass with modal-hammer taps on the
mounting structure. It cites Neubert for the impedance method and Piersol et al.
for combining apparent masses measured at multiple attachment points into a
single-node model [NASA-HDBK-7004C, 2012]. Tier: standard / handbook. Piersol et
al. itself was not accessed in full here, so only the handbook's description is
used.

The important validity limit is already in 7004C: at low frequencies with
closely spaced attachment points, tapping at any attachment may yield the total
mounting-structure interface apparent mass; at high frequencies with widely
spaced attachments, different taps can represent only fractions of the total
interface apparent mass [NASA-HDBK-7004C, 2012]. Tier: standard / handbook.

NIRSpec shows a practical measured-interface workflow: low-level sine data
support an apparent-mass approach for an initial random level, while later levels
prefer direct time-domain force reconstruction because damping can change with
test level [Salvignol/Salvignola et al., 2009]. Tier: conference.

Conclusion for C: apparent-mass measurement and low/high frequency sparsity
limits are known. A full 6x6 sparse interface apparent-mass contract is not
spelled out in the reviewed force-limiting standards. Status: CONFIRMED for the
low/high sparse-measurement warning, PARTIALLY-KNOWN for 6-DOF matrix use in
force-limit criteria.

## D. Empirical Coupled-response Prediction Without a Coupled FEM

Frequency-Based Substructuring (FBS) is the main external prior art for empirical
coupling without a full coupled forced FEM. de Klerk, Rixen, and Voormeeren
classify dynamic substructuring methods and identify frequency-domain
impedance/admittance coupling and Lagrange Multiplier FBS as standard families
[de Klerk et al., 2008, AIAA Journal, doi:10.2514/1.33274]. Tier:
peer-reviewed.

LM-FBS introduces interface forces explicitly as Lagrange multipliers; the
publisher abstract states that substructures characterized by dynamic admittance
can be assembled and that the Boolean constraint formulation is computationally
straightforward [de Klerk, Rixen, and de Jong, 2006]. Tier: peer-reviewed
conference.

Experimental dynamic substructuring literature flags the same cost as the
in-house EX-E result: interface completeness. Mayes's Sandia tutorial says
experimental substructures historically worked mostly for special cases or
single-point attachments; for multiple attachments, rotations and moments were
often neglected, and the transmission-simulator method was developed to retain
joint stiffness/damping and infer rotations without measuring them directly
[Mayes, 2011]. Tier: conference/tutorial.

Haeussler and Rixen state that rotational DOFs at the interface are crucial for
accurate experimental substructuring, but no common procedure had been
established; they discuss virtual-point/interface-deformation-mode transforms
that map measured FRFs to generalized interface displacement and force
coordinates [Haeussler and Rixen, 2016]. Tier: conference.

Transfer Path Analysis (TPA) and blocked-force methods are adjacent empirical
load-identification prior art. US8731868B2 covers parametric-load TPA from
input/response data and system response functions, and US12050125B2 covers a
controlled blocked-force exciter for in-situ MIMO system identification in an
assembled structure [US8731868B2; US12050125B2]. Tier: patent.

Conclusion for D: exact empirical coupling from measured matrices is not novel
by itself; it is central to FBS/impedance coupling. The narrower BayesX framing
would need to be the aerospace force/response-limit application with sparse
interface measurements, explicit 6-DOF rocking/moment observability, and
uncertainty-gated notching. Status: PARTIALLY-KNOWN.

## E. Response Limiting and Transmissibility-based Notching

Response limiting is standard practice. ISO 23670 defines response-limited
vibration testing as reducing input acceleration to keep specified response
points at or below specified values, and it defines notching as reducing input
level or spectrum to avoid overtesting at resonances [ISO 23670:2021]. Tier:
standard.

ISO 23670 requires response-limited tests to define response limits at specific
points on the specimen, put monitoring accelerometers at those points, and modify
control inputs as needed to keep those responses below limits [ISO 23670:2021].
Tier: standard.

7004C discusses Sweitzer's 1987 mechanical-impedance correction as a heuristic
response/notching criterion: for random vibration, notching the input by the
response transmissibility magnitude reduces a resonance amplification from Q^2
to Q in PSD terms; 7004C also says Sweitzer did not directly relate the rule to
the flight mounting impedance [NASA-HDBK-7004C, 2012; Sweitzer, 1987, cited
there]. Tier: standard / limited-access conference.

Small-satellite guidance from Instar says manual notching and response limiting
are usually trusted mainly for the fundamental mode, because both depend on
pretest FEM accuracy; it recommends low-level runs and adjustment of notch
frequency/depth from measured data [Instar, 2017]. Tier: vendor/practice.

The searched sources support the in-house warning that transmissibility is
configuration-dependent: response limits are tied to monitoring points and
configuration-specific low-level runs [ISO 23670:2021; NASA-HDBK-7004C, 2012;
Salvignol/Salvignola et al., 2009]. I did not find a force-limiting standard
that explicitly says "bare-configuration transmissibility is invalid after
integration"; that is a direct structural-dynamics consequence and is consistent
with practice, not a located quote. Status: PARTIALLY-KNOWN.

## F. Spatial Reach / Modal Overlap / Coherence

NASA-HDBK-7004C identifies coherent shaker attachment motion versus uncorrelated
flight attachment motion as a high-frequency, wide-attachment overtest driver
[NASA-HDBK-7004C, 2012]. Tier: standard / handbook.

Statistical Energy Analysis (SEA) sources define modal overlap as damping
bandwidth divided by average modal spacing; high modal overlap means high damping
or high modal density and smoother responses, while modal overlap below about one
is a regime where deterministic/modal behavior remains important [Irvine, SEA
Parameters; Lund SEA lecture notes]. Tier: web/tutorial.

The reviewed SEA/material does not directly translate modal overlap into
"notch visible to a response sensor r foot-spacings away." The in-house rule
that low modal overlap gives global reach while high overlap trends toward
local wavelength-scale reach is physically consistent with modal/wave theory and
7004C's attachment-coherence warning, but I did not find a direct force-limiting
source stating that criterion. Status: NOVEL-AS-FAR-AS-FOUND, with the caveat
that this is a literature-search statement, not a novelty opinion.

## G. Bayesian / Statistical / Data-driven Approaches

I found Bayesian and statistical model-updating literature for structural
dynamics, but not a direct Bayesian force-limit or response-limit notching method
for sparse multi-point interfaces. Beck and Katafygiotis, Sohn and Law, and later
Bayesian model-updating work are recognized foundations for probabilistic FE
model updating; Ching and Chen review Bayesian methods for dynamic model
updating [Ching and Chen, 2011]. Tier: peer-reviewed.

StatFEM treats finite-element predictions, observation data, and model
uncertainty in one Bayesian/statistical framework; recent statFEM work is aimed
at coherent data-FEM fusion under model discrepancy rather than at force-limited
vibration tests specifically [Duffin et al., 2021; Girolami-related statFEM
review/PNAS sources]. Tier: peer-reviewed.

Bayesian Operational Modal Analysis (OMA) quantifies uncertainty in modal
parameters from output-only vibration data, which is relevant to in-situ
identification when forces are absent, but it does not by itself give interface
force limits [O'Connell et al., 2026 accepted manuscript; Au/Yuen BAYOMA
literature]. Tier: peer-reviewed.

Blocked-force and in-situ TPA methods provide a data-driven route to assembly
load/source characterization. Sturm et al. investigate in-situ blocked forces for
source characterization and virtual acoustic prototyping, and patents around
TPA/blocked-force identification show this space is active [Sturm et al., 2016;
US8731868B2; US12050125B2]. Tier: conference / patent.

Conclusion for G: Bayesian/statistical updating is mature in structural dynamics,
and data-driven in-situ force identification is active in NVH/TPA, but the
searched literature did not reveal a direct Bayesian 7004C-style sparse 6-DOF
force/response limiting workflow with green/yellow/red uncertainty gates. Status:
NOVEL-AS-FAR-AS-FOUND for that combination only.

## H. Standards and Flight Practice

NASA-HDBK-7004C is the core force-limited vibration standard/handbook for NASA
practice. It covers semi-empirical, simple/complex TDFS, impedance, force gage
installation, response/Sweitzer notching context, and flight/ground examples
[NASA-HDBK-7004C, 2012]. Tier: standard / handbook.

ISO 23670:2021 is a broader space-systems vibration testing standard that
includes force-limited vibration testing, response-limited vibration testing,
notching, force measurement devices, and control-point placement. It explicitly
allows simultaneous acceleration and force-limit strategies [ISO 23670:2021].
Tier: standard.

ECSS-E-HB-32-26A is an ECSS spacecraft mechanical loads analysis handbook; the
ECSS landing page says it recommends engineering practices for European programs
and can be cited in contracts/program documents [ECSS, 2013]. Tier: standard /
handbook.

MIL-STD-810H Method 514.8 is less space-specific, but its vibration method
requires documentation of the vibration exciter control strategy, including
single-point response, multipoint response, force limit, or waveform control when
used [MIL-STD-810H Method 514.8 sample]. Tier: standard.

Flight practice examples include Cassini/JPL force limiting in RP-1403, NASA
CoNNeCT semi-empirical force limiting, TESS camera mass-model force-limited
random vibration, and JWST NIRSpec interface-force notching [Scharton, 1997;
Staab et al., 2012; TESS ATS paper, 2015/2016; Salvignol/Salvignola et al.,
2009]. Tier: handbook / NASA TM / conference.

## Status of the Four In-house Findings

Status labels available: CONFIRMED, PARTIALLY-KNOWN, NOVEL-AS-FAR-AS-FOUND,
CONTRADICTED.

| In-house finding | Literature status | Support |
|---|---|---|
| 1. 7004C's semi-empirical / simple-and-complex TDOF / single-node impedance methods are scalar, single-interface, in-axis. | PARTIALLY-KNOWN | Confirmed for the formal derivations and equations in 7004C/RP-1403. Not absolute, because 7004C/RP-1403 also discuss triaxial transducers, moments, individual mounting points, and six-resultant measurement in practice. |
| 2. With spaced feet plus 6-DOF, apparent mass is a 6x6 matrix; rocking loads cancel in net in-axis force; one notch becomes a cluster across mean/differential channels. | PARTIALLY-KNOWN | Matrix/moment measurement and rotational-DOF importance are known in RP-1403 and FBS literature. I found no direct external worked example of net-force cancellation plus notch clustering in the force-limiting context. |
| 3. Notch spatial reach is governed by backing modal overlap, not a fixed radius. | NOVEL-AS-FAR-AS-FOUND | Modal overlap and attachment coherence are known; the direct notch-reach criterion was not found in force-limiting/response-limiting sources searched. |
| 4. Measured impedance reconstructs coupled loads exactly; sparsity is the cost; response-limit transmissibility must be calibrated in the integrated configuration. | PARTIALLY-KNOWN | Exact coupling by measured admittance/impedance is core FBS/LM-FBS prior art; sparse-interface and rotational-DOF pitfalls are known. The specific 7004C empirical recipe and the 1-foot versus >=3-foot rocking threshold were not found as a packaged method. |

## Honest Summary

What is genuinely known: force limiting, response limiting, apparent mass, C^2
limits, Sweitzer-style notching, multi-component force/moment measurement, and
FBS/TPA empirical coupling are all real prior art. What looks likely-novel, as
far as this open search found, is not "using impedance" or "using data instead of
a coupled FEM"; it is the specific aerospace workflow that treats the interface
as a sparse 6-DOF/multi-foot measurement problem, exposes the net-resultant
rocking blind spot, links notch spatial reach to modal-overlap/coherence, and
wraps empirical force/response limits in Bayesian uncertainty with explicit
green/yellow/red honesty gates. What still must be tested on real hardware is
whether sparse >=3-foot measurements and integrated-configuration
transmissibility actually protect the per-foot/moment and critical-response
channels on ShockSat x tray or an equivalent article.
