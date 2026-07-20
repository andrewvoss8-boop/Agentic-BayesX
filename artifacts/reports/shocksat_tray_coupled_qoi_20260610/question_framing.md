# Question framing — shocksat_tray_coupled_qoi_20260610

**Engineering decision being supported.** When a payload organization predicts
the interface load its payload (here: a hypothetical hexapod tray) will
transmit into its host structure (here: the validated ShockSat modal twin),
it must choose (a) an analysis METHOD — full coupled time-history, modal-SRS
hand method, or PSD/Miles envelope — and (b) a COUPLING assumption — treat the
interface motion as an unchangeable base input (uncoupled, the standard
test-spec practice) or account for the payload loading the source
(coupled = force-limiting, NASA-HDBK-7004C). The decision: which method/
coupling combination is adequate, how conservative is each shortcut, and is
the answer even knowable given the mount stiffness is an unidentified joint?

**Objective function / success metric.** Per-axis peak interface force
|F_d|max (N) and its uncertainty. Method error = ratio of a method's estimate
to the time-history reference on the SAME environment. Coupling gap = ratio of
uncoupled to coupled peak force (the 7004C over-test factor). Mount dominance
= share of QOI variance attributable to mount-stiffness uncertainty.

**What the analysis is allowed to choose.** Implementation details (frequency
grid, mode counts, integration scheme), the sensitivity-arm grid, and the MC
sample sizes — all documented. It is NOT allowed to choose the scope (locked
by D38), the QOI definition (quantity contract), or to relabel the
hypothetical coupled QOI as validated.

**What remains human judgment.** Whether the invented mount/placement/input
assumptions are the interesting ones (sign-off flags D2–D4); whether the
conservatism levels found here justify changing any real test practice;
any durable harness rule changes.

**What would make this the wrong question.** (1) If the real concern were
per-mount loads or interface moments, the single-point net-CG-force
condensation would hide the answer (D38 explicitly dropped that arm for THIS
QOI). (2) If the real environment were pyro near-field shock, the linear FEM
cannot predict it — that case is deliberately skipped (D38). (3) If the tray
were ever really mounted, its placement/mount values would replace the
invented ones and the QOI would need re-deriving — nothing here is a hardware
prediction. (4) If the source were flight-mounted (not free-free), the source
apparent mass below ~50 Hz would change character; conclusions about the
low-frequency rigid-mass line are configuration-specific.
