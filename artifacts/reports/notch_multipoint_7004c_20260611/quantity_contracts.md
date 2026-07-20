# Quantity Contracts — notch_multipoint_7004c_20260611

Per AGENTS.md Quantity Contract Gate: numerator / denominator / coordinate / excitation /
boundary condition / units / limiting behavior / resonance behavior / reference, BEFORE
plotting or checking. Conventions follow `references/nasa-7004c-notes.md` (source vs load
apparent mass postmortem).

## Q1 — Source apparent mass Ms(f)  [EX-A]
F at interface / a at interface, load DISCONNECTED, source internal excitation off, source
base FIXED (drive at the interface). Units: kg (nondim. in EX-A). Limits: -> infinity as
f->0 (stiffness line k/omega^2); MINIMUM ~ m/Q at the source fixed-base resonance.
Ref: 7004C §5.6 + Fig 9b; SDOF form m*|1 - r^2 + i r/Q| / r^2, r=omega/omega0.

## Q2 — Load apparent mass Ml(f)  [EX-A, EX-B, EX-C]
F at interface / a at interface, load driven at its base (fixed-base condition), source
disconnected. Units: kg. Limits: -> total load mass as f->0; PEAK ~ m*Q at the load
fixed-base resonance. Ref: 7004C §5.6 + Fig 9c; SDOF form m*|1 + i r/Q| / |1 - r^2 + i r/Q|.

## Q3 — Interface acceleration A(f) and force F(f), coupled  [EX-A]
Norton/Thevenin: A = As * Ms/(Ms+Ml); F = As * Ms*Ml/(Ms+Ml). As = free acceleration of
the source at the interface, load disconnected (7004C Eq 3/4, p.33-34). Units: nondim.
Resonances at minima of |Ms+Ml| (coupled-system frequencies, Eq B1); NOTCH in A at the
load fixed-base resonance where Ms collapses and Ml peaks.

## Q4 — 6x6 interface apparent-mass matrix M(omega)  [EX-B]
F_int (3 forces + 3 moments about the interface reference point O = foot-plan centroid at
the foot plane) / a_base (3 translational + 3 rotational accelerations of the RIGID base),
all feet moving uniformly with the base; payload free above. Units: kg, kg*m, kg*m^2
blocks. Limit f->0: EXACTLY the rigid-body mass matrix of the payload about O (parallel
axis terms m*h in coupling blocks). Resonances: peaks at payload fixed-base modes; each
DOF pair has its own structure; symmetric matrix. Sign convention: +F on payload from
base; right-hand rule moments about O. Ref: 7004C Appendix A generalization; p.56
"total mass or moment of inertia for that direction".

## Q5 — Effective mass (translational and rotary)  [EX-B]
Per mode n and direction p: contribution to the F_p/a_q ratio divided by the SDOF
frequency-response factor (7004C Appendix A, Eq A10). Units kg (translations), kg*m^2
(rotations). Check: sum over modes = rigid-body mass/inertia about O per direction.

## Q6 — Notch depth field D(x,y; f*)  [EX-C]
20*log10( |a_bare(x,y,f*)| / |a_loaded(x,y,f*)| ), where a_bare = plate acceleration
WITHOUT payload, a_loaded = WITH payload, same unit point force (C5), f* = a coupled-mode
frequency of the loaded system (where the loaded interface response notches). Units: dB.
Positive = payload absorber action suppressed the response there ("you can see the
notch"). Near-zero or negative = notch invisible there. NOT a transmissibility: same
excitation, two configurations. The map is a diagnostic OF THE CHANGE, denominator
effects called out in captions. Distance axis: euclidean distance to NEAREST foot, m.

## Q7 — Per-foot force, net force, interface moment  [EX-B, EX-C, EX-D]
F_i(f) = complex vertical force in foot i spring (payload side; Newton's 3rd law check
against plate side). Net Fz = sum_i F_i. Moment My about O: sum_i (x_i - x_O) * (-F_i)
... assembled from the same foot forces (+ lateral foot forces * h in EX-B). Units: N,
N*m (PSDs: N^2/Hz, (N m)^2/Hz). KEY BEHAVIOR under rocking: per-foot |F_i| large while
|sum F_i| -> ~0 (cancellation); |My| large. Ref: 7004C p.10 (net in-axis force is the
default measured/limited quantity), p.18 (voltage-summing box can give moments).

## Q8 — Semi-empirical force limit  [EX-D]
S_FF_limit(f) = C^2 * Mo^2 * S_AA(f) for f < fb; * (fb/f)^(2n) above (7004C Eq 2a/2b).
Mo = TOTAL payload mass 6 kg (stated: total vs asymptotic distinction ignored per p.30
simplification). S_AA = the TEST input acceleration PSD spec ((m/s^2)^2/Hz). Units
N^2/Hz. Applied to NET Fz (p.10 practice). C^2 from Eq B1/B2 (Q=25, mass ratio 0.556).

## Q10 — Interface apparent-mass matrices for reconstruction  [EX-E]
- Ml(ω) (LOAD, 4×4): payload(3-DOF z,θx,θy)+foot springs seen at the 4 plate-side foot
  vertical DOFs. Ml = -kc[I - Lp G kc Lpᵀ]/ω², G=(-ω²Mp+kc LpᵀLp)⁻¹, kc=kz(1+iη). Units kg.
  Low-f limit: finite (payload mass/inertia) in the 3 rigid foot combinations, → ∞ in the
  4th (warping) combination (pure spring, no mass behind it). Computable with NO plate.
- Ms(ω) (SOURCE, 4×4): bare plate at the 4 feet, Ms = [a/f]⁻¹ = [-ω² Φf diag(1/Dm) Φfᵀ]⁻¹.
  Units kg. Computable with NO payload.
- A_free(ω) (4-vector): bare-plate acceleration at the feet under the external point force
  (the source free acceleration, 7004C Eq 3). Units (m/s²)/N.
- Coupled reconstruction: a = (Ms+Ml)⁻¹ Ms A_free (foot accel); F = Ml a (force on payload
  per foot, = truth Ffoot). EXACT vs the coupled solve when matrices are full (verification).

## Q11 — Sparse reconstruction variants  [EX-E]
Each produces an estimate of the 4-foot interface motion + force channels from a SUBSET of
Q10 (no coupled FEM). FULL (4×4) = exact. SCALAR = single-point condensation o=[1,1,1,1]:
Ms_s=oᵀMs o, Ml_s=oᵀMl o, A_s=(oᵀA_free)/4 → uniform foot accel, net force only, moment≡0.
RIGID3 = project onto B=[1; y_foot; -x_foot] (4×3): Ms3=BᵀMs B etc → net Fz, Mx, My; per-foot
via minimum-norm B(BᵀB)⁻¹·gen. DIAG = per-foot independent (diagonal of Ms,Ml only).

## Q12 — Reconstruction error + remote proxy  [EX-E]
- Reconstruction error: complex relative error |X_recon - X_truth|/|X_truth| for channels
  X ∈ {net Fz, moment My, worst per-foot |F|, foot-accel vector}, vs frequency and as a
  band-peak (±10%) at each payload mode. Truth from the coupled solve.
- Remote response proxy: transmissibility T = a_remote/a_meanfeet. Proxy error =
  |T_coupled - T_bareplate|/|T_coupled| (boundary dependence of a remote control accel),
  vs frequency and vs distance (1/2/3 foot-spacings, foot spacing ≈ 0.16 m). Ties to EX-C
  visibility radius. Units dimensionless.

## Q9 — Overtest ratio  [EX-D]
R_i(f) = S_Fi_test(f) / S_Fi_flight(f) per foot i (and for CG accel, net Fz, My). Units:
dimensionless PSD ratio (report also in dB). R>1 = overtest at that frequency/channel.
Summary number per payload mode: ratio of PEAK PSD in a +/-10% band around the coupled-
mode frequency. "Flight" = hypothetical coupled plate simulation (assumptions D2/C5).
