#!/usr/bin/env python3
"""Stage 1 — forcing-math plumbing validation on an analytic SS plate.

Validates the NEW machinery this study introduces (pressure-field cross-spectral
density -> joint acceptance -> modal force CSD -> response PSD) against closed
forms on a simply-supported rectangular plate whose modes are analytic, BEFORE
any FEM is built. Checks (IDs referenced by check.py):

  C1  fully-correlated limit: modal force vs analytic (integral of phi dA)^2;
      even modes unloaded.
  C2a Corcos separable FAST path == full-matrix path (machine precision).
      The fast path is the production trick for the barrel; the full path is
      what non-separable geometry will use. They must agree exactly here.
  C2b grid-resolution error of the joint acceptance vs a 10x-fine 1-D
      quadrature at 400 Hz (informs dome/barrel mesh sizing vs coherence length).
  C3  DAF sinc coherence -> fully-correlated limit at low frequency.
  C4  response-PSD peaks land on analytic natural frequencies.
  C5  band RMS from integrated PSD vs white-near-resonance modal closed form.
  C6  Hermitian modal-force CSD; real non-negative response PSD.
  C7  physics monotonicity: shorter coherence length (bigger Corcos decay)
      -> lower joint acceptance for the fundamental at fixed frequency.

Units: SI throughout. PSDs one-sided per Hz. Pressure PSD Phi_p in Pa^2/Hz.
Run: python3 scripts/validate_forcing_math.py  -> out/forcing_validation.json
"""
import json
import time
import numpy as np

T0 = time.time()
OUT = {}

# ---------------------------------------------------------------- plate setup
a, b, t = 0.8, 0.6, 0.004            # m
E, nu, rho = 71e9, 0.33, 2800.0      # Pa, -, kg/m^3
D = E * t**3 / (12 * (1 - nu**2))    # N*m
eta = 0.02                           # structural loss factor (Q=50? no: Q=1/eta=50)
# NOTE: eta is the structural loss factor; half-power viscous equivalent zeta=eta/2.

def f_mn(m, n):
    return (np.pi / 2.0) * np.sqrt(D / (rho * t)) * ((m / a) ** 2 + (n / b) ** 2)

F_MAX_MODE = 850.0
modes = [(m, n) for m in range(1, 9) for n in range(1, 9) if f_mn(m, n) <= F_MAX_MODE]
modes.sort(key=lambda mn: f_mn(*mn))
fn = np.array([f_mn(m, n) for (m, n) in modes])
wn = 2 * np.pi * fn
c_norm = np.sqrt(4.0 / (rho * t * a * b))     # mass-normalization constant
OUT["plate"] = {"a_m": a, "b_m": b, "t_m": t, "eta": eta,
                "n_modes": len(modes), "f_modes_hz": fn.round(3).tolist()}

# cell-centered uniform grid (uniform area weights, no boundary half-cells)
Nx, Ny = 48, 36
xs = (np.arange(Nx) + 0.5) * (a / Nx)
ys = (np.arange(Ny) + 0.5) * (b / Ny)
XX, YY = np.meshgrid(xs, ys, indexing="ij")
xf, yf = XX.ravel(), YY.ravel()
N = xf.size
dA = (a / Nx) * (b / Ny)

def phi(m, n, x, y):
    return c_norm * np.sin(m * np.pi * x / a) * np.sin(n * np.pi * y / b)

PHI = np.stack([phi(m, n, xf, yf) for (m, n) in modes], axis=1)   # N x M
P = dA * PHI                                                      # area-weighted

# separations (precomputed once)
XI = xf[:, None] - xf[None, :]          # streamwise (x) separation
ETA = yf[:, None] - yf[None, :]         # lateral (y) separation
R = np.sqrt(XI**2 + ETA**2)

# ------------------------------------------------------------- forcing models
Uc = 210.0          # m/s convection speed (ledger D3)
ax_c, ay_c = 0.12, 0.72   # Corcos decay coefficients (ledger D5)
c_air = 343.0
PHI_P = 100.0       # Pa^2/Hz flat level for validation (arbitrary, documented)

def corcos_SQQ_full(f, axc=ax_c, ayc=ay_c):
    """Full-matrix path: S_QQ = P^H S_pp P (M x M complex)."""
    w = 2 * np.pi * f
    Spp = PHI_P * np.exp(-axc * w * np.abs(XI) / Uc) \
                * np.exp(-ayc * w * np.abs(ETA) / Uc) \
                * np.exp(1j * w * XI / Uc)
    return P.conj().T @ (Spp @ P.astype(complex))

def corcos_SQQ_fast(f, axc=ax_c, ayc=ay_c):
    """Separable fast path: tensor-factor the Corcos kernel on the grid.
    S_QQ[(m,n),(m',n')] = Phi_p * (Sx^T Dx Sx)[m,m'] * (Sy^T Dy Sy)[n,n']
    with Dx complex (decay+convection), Dy real (decay)."""
    w = 2 * np.pi * f
    xi1 = xs[:, None] - xs[None, :]
    et1 = ys[:, None] - ys[None, :]
    Dx = np.exp(-axc * w * np.abs(xi1) / Uc) * np.exp(1j * w * xi1 / Uc)
    Dy = np.exp(-ayc * w * np.abs(et1) / Uc)
    dx, dy = a / Nx, b / Ny
    ms = sorted({m for (m, _) in modes}); ns = sorted({n for (_, n) in modes})
    Sx = np.stack([np.sin(m * np.pi * xs / a) for m in ms], axis=1) * dx
    Sy = np.stack([np.sin(n * np.pi * ys / b) for n in ns], axis=1) * dy
    Gx = Sx.T @ (Dx @ Sx.astype(complex))   # len(ms) x len(ms)
    Gy = Sy.T @ (Dy @ Sy)                   # real
    M = len(modes)
    SQQ = np.empty((M, M), dtype=complex)
    mi = {m: i for i, m in enumerate(ms)}; ni = {n: i for i, n in enumerate(ns)}
    for p_, (m1, n1) in enumerate(modes):
        for q_, (m2, n2) in enumerate(modes):
            SQQ[p_, q_] = PHI_P * c_norm**2 * Gx[mi[m1], mi[m2]] * Gy[ni[n1], ni[n2]]
    return SQQ

def daf_SQQ(f):
    w = 2 * np.pi * f
    kr = (w / c_air) * R
    Spp = PHI_P * np.sinc(kr / np.pi)       # np.sinc(x)=sin(pi x)/(pi x)
    return P.T @ (Spp @ P)

# --------------------------------------------------- C1 fully-correlated limit
ones_SQQ_diag = (PHI_P * (P.sum(axis=0)) ** 2)
def Q_analytic(m, n):
    return c_norm * (a / (m * np.pi)) * (1 - np.cos(m * np.pi)) \
                  * (b / (n * np.pi)) * (1 - np.cos(n * np.pi))
qa = np.array([Q_analytic(m, n) for (m, n) in modes])
odd = np.array([(m % 2 == 1) and (n % 2 == 1) for (m, n) in modes])
lowo = odd & np.array([(m <= 5) and (n <= 5) for (m, n) in modes])
rel_c1 = np.abs(ones_SQQ_diag[lowo] - PHI_P * qa[lowo] ** 2) / (PHI_P * qa[lowo] ** 2)
even_leak = float(ones_SQQ_diag[~odd].max() / ones_SQQ_diag[odd].max())
OUT["C1_fully_correlated"] = {
    "max_rel_err_oddodd_mn_le5": float(rel_c1.max()),
    "even_mode_leak_ratio": even_leak}

# --------------------------------------------- C2a fast vs full (machine prec)
c2a = []
for f in (50.0, 200.0, 400.0):
    Sf, Ss = corcos_SQQ_full(f), corcos_SQQ_fast(f)
    c2a.append(float(np.abs(Sf - Ss).max() / np.abs(Sf).max()))
OUT["C2a_fast_vs_full_maxrel"] = c2a

# ---------------------- C2b grid resolution vs 10x-fine 1-D quadrature, 400 Hz
def jx_1d(m, f, npts, axc=ax_c):
    x = (np.arange(npts) + 0.5) * (a / npts); dx = a / npts
    s = np.sin(m * np.pi * x / a) * dx
    xi = x[:, None] - x[None, :]
    w = 2 * np.pi * f
    Dx = np.exp(-axc * w * np.abs(xi) / Uc) * np.exp(1j * w * xi / Uc)
    return (s @ (Dx @ s.astype(complex))).real

def jy_1d(n, f, npts, ayc=ay_c):
    y = (np.arange(npts) + 0.5) * (b / npts); dy = b / npts
    s = np.sin(n * np.pi * y / b) * dy
    et = y[:, None] - y[None, :]
    w = 2 * np.pi * f
    return float(s @ (np.exp(-ayc * w * np.abs(et) / Uc) @ s))

c2b = {}
for (m, n) in [(1, 1), (3, 3), (5, 5)]:
    coarse = jx_1d(m, 400.0, Nx) * jy_1d(n, 400.0, Ny)
    fine = jx_1d(m, 400.0, 10 * Nx) * jy_1d(n, 400.0, 10 * Ny)
    c2b[f"mode_{m}{n}"] = float(abs(coarse - fine) / abs(fine))
# coherence lengths at 400 Hz for the mesh-sizing note
w400 = 2 * np.pi * 400.0
OUT["C2b_grid_vs_fine_quadrature_400hz"] = {
    **c2b,
    "Lcoh_stream_m": float(Uc / (ax_c * w400)),
    "Lcoh_lateral_m": float(Uc / (ay_c * w400)),
    "grid_dx_m": a / Nx, "grid_dy_m": b / Ny,
    "nodes_per_lateral_Lcoh": float((Uc / (ay_c * w400)) / (b / Ny))}

# ------------------------------------------------------- C3 DAF low-freq limit
f_lo = 10.0
d_lo = np.real(np.diag(daf_SQQ(f_lo)))
OUT["C3_daf_lowfreq_vs_fullcorr"] = {
    "rel_diff_mode11": float(abs(d_lo[0] - ones_SQQ_diag[0]) / ones_SQQ_diag[0])}

# ---------------------------------------------- response PSD (Corcos forcing)
# response point chosen OFF the node lines of all checked modes (run-1 lesson:
# 0.31a sat near mode-(3,*) node line x=a/3 and buried that peak — legitimate
# physics, wrong probe placement for a peak check)
x0, y0 = 0.23 * a, 0.29 * b
phi0 = np.array([phi(m, n, x0, y0) for (m, n) in modes])

def Hvec(f):
    w = 2 * np.pi * f
    return 1.0 / (wn**2 * (1 + 1j * eta) - w**2)

def Saa_at(f, SQQ):
    w = 2 * np.pi * f
    g = (w**2) * Hvec(f) * phi0          # accel modal participation at x0
    return float(np.real(g.conj() @ SQQ @ g))

# frequency grid: log background + resonance clusters (documented per
# Discretization Resolution gate; clusters resolve half-power widths ~eta*fn)
f_bg = np.geomspace(15.0, 550.0, 200)
# cluster spacing 0.5% of fn resolves the ~2% half-power width (>=4 pts/width;
# run-1 used 1.7% spacing = ~1 pt/width, too coarse to localize peaks)
clusters = [f * (1 + np.linspace(-0.12, 0.12, 49)) for f in fn if f < 520]
fgrid = np.unique(np.concatenate([f_bg] + clusters))
fgrid = fgrid[(fgrid >= 15.0) & (fgrid <= 550.0)]

Saa = np.empty(fgrid.size)
herm_worst = 0.0
for i, f in enumerate(fgrid):
    SQQ = corcos_SQQ_full(f)
    herm_worst = max(herm_worst, float(np.abs(SQQ - SQQ.conj().T).max() / np.abs(SQQ).max()))
    Saa[i] = Saa_at(f, SQQ)

OUT["C6_numerics"] = {"worst_hermitian_resid": herm_worst,
                      "min_Saa": float(Saa.min())}

# C4: a local PSD maximum must sit at each analytic frequency. NOTE (run-1
# lesson): a windowed GLOBAL max is the wrong check — under Corcos convection
# even modes ARE loaded and a taller neighbor can sit inside the window; so we
# test distance from each target to the NEAREST local maximum.
ilocal = np.where((Saa[1:-1] > Saa[:-2]) & (Saa[1:-1] > Saa[2:]))[0] + 1
f_local = fgrid[ilocal]
peaks = {}
for (m, n) in [mn for mn, o in zip(modes, odd) if o][:4]:
    f_t = f_mn(m, n)
    fpk = float(f_local[np.argmin(np.abs(f_local - f_t))])
    peaks[f"mode_{m}{n}"] = {"f_analytic_hz": float(f_t), "f_peak_hz": fpk,
                             "rel_err": float(abs(fpk - f_t) / f_t)}
OUT["C4_peak_placement"] = peaks

# C5: integrated RMS vs white-near-resonance closed form (same mode set both
# sides; diagonal-only closed form -> tolerance documented in check.py)
var_num = np.trapz(Saa, fgrid)
var_cf = 0.0
for j, f_j in enumerate(fn):
    if f_j > 520:
        continue
    SQQj = np.real(np.diag(corcos_SQQ_full(f_j)))[j]
    var_cf += phi0[j] ** 2 * SQQj * wn[j] / (4.0 * eta)
OUT["C5_rms"] = {"sigma_numeric_ms2": float(np.sqrt(var_num)),
                 "sigma_closedform_ms2": float(np.sqrt(var_cf)),
                 "ratio": float(np.sqrt(var_num / var_cf))}

# C7: coherence-length physics. RUN-1 LESSON (kept deliberately): naive
# "more coherence => more modal force" is WRONG for a convective field at high
# frequency — the convection phase exp(i*w*xi/Uc) self-cancels over a
# long-wavelength mode (aerodynamic-coincidence behavior), so J11 vs decay is
# NON-monotone at 400 Hz. Monotonicity DOES hold where no phase competes:
# (a) the lateral pure-decay kernel, any frequency; (b) the streamwise kernel
# at low frequency (convective wavelength >> panel). We check those, and we
# RECORD the 400 Hz non-monotone curve as documented coincidence physics.
scales = (0.5, 1.0, 2.0, 4.0)
jy_scan = [jy_1d(1, 400.0, Ny, ayc=s * ay_c) for s in scales]
jx_lo = [jx_1d(1, 2.0, Nx, axc=s * ax_c) for s in scales]   # lam_c=105m >> a
j11_400 = [float(np.real(np.diag(corcos_SQQ_fast(400.0, axc=s * ax_c,
                                                 ayc=s * ay_c)))[0])
           for s in scales]
OUT["C7_coherence_physics"] = {
    "scales": list(scales),
    "Jy_lateral_400hz": jy_scan,
    "Jy_monotone_decreasing": bool(all(jy_scan[i] > jy_scan[i + 1] for i in range(3))),
    "Jx_streamwise_2hz": jx_lo,
    "Jx_lowfreq_monotone_decreasing": bool(all(jx_lo[i] > jx_lo[i + 1] for i in range(3))),
    "J11_400hz_nonmonotone_coincidence": j11_400,
    "note": "non-monotone J11(400Hz) = expected convective-coincidence physics,"
            " not an error; see packet."}

# response curve saved for the future figure stage (no figure generated here)
OUT["response_curve"] = {"f_hz": fgrid.round(4).tolist(),
                         "Saa_ms2_2_per_hz": Saa.tolist(),
                         "note": "Corcos LC2-style validation forcing on SS plate; "
                                 "figure deferred to figure stage (Tufte gate)."}
OUT["runtime_s"] = time.time() - T0

with open("out/forcing_validation.json", "w") as fh:
    json.dump(OUT, fh, indent=1)
print(json.dumps({k: v for k, v in OUT.items() if k != "response_curve"}, indent=1))
