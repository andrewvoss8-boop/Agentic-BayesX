#!/usr/bin/env python3
"""Card D — L-damp PROTOTYPE (b). Non-proportional (interface-localized) damping
in the held-out FRF, vs the uniform-zeta baseline, at the 8 hard channels.

Reuses (COPY) the validation study's 74x74 reduced model (A_fix + per-group A_g,
mass=I), measured complex FRF cache, and channel mapping. Damping:
    C = alpha0*I + sum_{g in IDENT} beta_g * A_g           (gated: identifiable groups only)
Light-damping per-mode modal damping (no quadratic eig needed for |H|, zeta<2%):
    zeta_k = alpha0/(2 w_k) + sum_g beta_g w_k f_{k,g}/2,  f_{k,g}=(Q_k^T A_g Q_k)/lam_k
The FRF denominator uses PER-MODE eta_k=2 zeta_k (non-proportional) instead of a
single eta. beta,alpha0 are fit (NNLS) to the measured per-mode zeta_hat (.ash).

Test: with ONE global log-gain (cannot absorb per-mode/per-channel variation), does
per-mode non-proportional damping reduce the held-out PEAK |H| error at the 8 hard
channels vs uniform zeta=1%?  Honest: the score decides.
"""
import json, os, sys
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import realfrf

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(HERE)
G_IN_S2 = 386.0886
BAND = (45.0, 260.0)
HARD = [4, 27, 38, 40, 52, 69, 92, 98]
# let NNLS pick from ALL groups (gate found top_box/plates/cross/al_welds/angle_brackets carry it;
# joints/contact/bottom_box -> 0). Use full set so localized damping gets its fair (best) shot.
IDENT = ["bottom_box", "steel_welds", "top_box", "al_welds", "angle_brackets",
         "cross_beam", "plates", "joints", "contact"]

R = realfrf.load_reduced()
GNAMES = realfrf.GNAMES
ch = realfrf.build_channels(R, HARD)

# nominal reduced model + modal strain-energy fractions
K0 = R.A_fix + R.A.sum(0)                       # theta = 1
lam, Q = np.linalg.eigh(K0); lam = np.clip(lam, 1e-9, None)
w = np.sqrt(lam)                                # rad/s
fmg = np.zeros((len(lam), len(GNAMES)))
for j, g in enumerate(GNAMES):
    AQ = R.A[j] @ Q
    fmg[:, j] = np.einsum("ik,ik->k", Q, AQ) / lam   # (modes, groups)

# measured per-mode damping (.ash), matched to FEM modes by frequency
mm = np.load("measured_modes.npz", allow_pickle=True)
f_meas = mm["freqs"]; zeta_meas = mm["damp"] / 100.0     # interpret .ash 'damp' as percent (D8 caveat)
fem_hz = w / (2*np.pi)
rows = []
for m in range(len(f_meas)):
    k = int(np.argmin(np.abs(fem_hz - f_meas[m])))
    if abs(fem_hz[k] - f_meas[m]) / f_meas[m] < 0.08:
        rows.append((m, k))
midx = [r[0] for r in rows]; kidx = [r[1] for r in rows]
zhat = zeta_meas[midx]; wk = w[kidx]; Fk = fmg[kidx]     # design at matched modes

# NNLS fit of zeta_k = alpha0/(2w) + alpha1 w/2 + sum_{g in IDENT} beta_g w f_kg /2
ig = [GNAMES.index(g) for g in IDENT]
A = np.column_stack([1.0/(2*wk), wk/2.0, (wk/2.0)[:, None]*Fk[:, ig]])
from scipy.optimize import nnls
coef, rnorm = nnls(A, zhat)
alpha0 = coef[0]; alpha1 = coef[1]; beta = np.zeros(len(GNAMES))
for b, j in zip(coef[2:], ig): beta[j] = b

# per-mode zeta for ALL fem modes (the non-proportional damping field)
zeta_k = alpha0/(2*w) + alpha1*(w/2.0) + (w/2.0) * (fmg @ beta)
zeta_k = np.clip(zeta_k, 1e-4, 0.1)

def fem_H(zeta):
    """complex accelerance (Nf,Nc) in g/lbf; zeta scalar OR per-mode array."""
    eta = 2.0 * np.asarray(zeta)
    Us = ch.rows @ Q                            # (Nc, r)
    Ud = ch.drive_row @ Q                       # (r,)
    om = 2*np.pi*FRQ
    if eta.ndim == 0:
        g = (1 + 1j*eta) * lam[None, :] - (om**2)[:, None]
    else:
        g = (1 + 1j*eta[None, :]) * lam[None, :] - (om**2)[:, None]
    H = -(om**2)[:, None] * np.einsum("sk,k,fk->fs", Us.astype(complex),
                                      Ud.astype(complex), 1.0/g)
    return H / G_IN_S2

# band frequency grid (native measured df)
cache = np.load("data/measured_frf_cache.npz", allow_pickle=True)
mf = cache["freqs"]; mH = cache["H"]; mdaq = list(cache["daq"])
bandm = (mf >= BAND[0]) & (mf <= BAND[1])
FRQ = mf[bandm]

H_before = fem_H(0.01)            # uniform zeta = 1%
H_after = fem_H(zeta_k)           # non-proportional per-mode zeta

# measured |H| at the 8 channels (band)
meas_logpeak = []; idx_ch = []
for d in ch.daq:
    i = mdaq.index(d)
    meas_logpeak.append(np.log(np.abs(mH[i, bandm]).max()))
meas_logpeak = np.array(meas_logpeak)

# ONE global log-gain c: align median over the whole band at the 8 channels (same for before/after)
def band_logmag(H): return np.log(np.abs(H) + 1e-30)
all_meas = np.concatenate([np.log(np.abs(mH[mdaq.index(d), bandm])+1e-30) for d in ch.daq])
c_before = np.median(all_meas - band_logmag(H_before).T.ravel())
c_after = np.median(all_meas - band_logmag(H_after).T.ravel())

# per-channel peak log|H| error (after global gain)
fem_before_peak = np.log(np.abs(H_before).max(0)) + c_before
fem_after_peak = np.log(np.abs(H_after).max(0)) + c_after
err_before = np.abs(fem_before_peak - meas_logpeak)
err_after = np.abs(fem_after_peak - meas_logpeak)

out = dict(
    note="L-damp prototype: non-proportional per-mode damping vs uniform zeta=1% at the 8 hard channels.",
    ident_groups=IDENT, alpha0=float(alpha0),
    beta={GNAMES[j]: float(beta[j]) for j in range(len(GNAMES)) if beta[j] > 0},
    nnls_zeta_residual=float(rnorm),
    zeta_k_range_pct=[float(zeta_k.min()*100), float(zeta_k.max()*100)],
    n_modes_matched=len(rows),
    channels=ch.daq, axes=ch.axes,
    meas_logpeak=meas_logpeak.tolist(),
    err_before_logpeak=err_before.tolist(), err_after_logpeak=err_after.tolist(),
    mean_abs_err_before=float(err_before.mean()), mean_abs_err_after=float(err_after.mean()),
    improved_channels=int(np.sum(err_after < err_before - 1e-3)),
    worsened_channels=int(np.sum(err_after > err_before + 1e-3)),
)
os.makedirs("out", exist_ok=True)
json.dump(out, open("out/ldamp_prototype.json", "w"), indent=1)

print(f"matched {len(rows)} modes; NNLS zeta residual {rnorm:.3e}")
print(f"non-proportional zeta_k range: {zeta_k.min()*100:.3f}% - {zeta_k.max()*100:.3f}% (uniform baseline 1.0%)")
print("damping by group:", {GNAMES[j]: round(beta[j],2) for j in range(len(GNAMES)) if beta[j]>0})
print(f"\nHELD-OUT PEAK |H| error at the 8 hard channels (log units, after one global gain):")
print(f"{'ch':>4} {'axis':>4} {'|err|before':>11} {'|err|after':>10}   {'better?':>7}")
for i, d in enumerate(ch.daq):
    tag = "BETTER" if err_after[i] < err_before[i]-1e-3 else ("worse" if err_after[i]>err_before[i]+1e-3 else "~same")
    print(f"{d:>4} {ch.axes[i]:>4} {err_before[i]:>11.3f} {err_after[i]:>10.3f}   {tag:>7}")
print(f"\nMEAN |err|: before {err_before.mean():.3f}  ->  after {err_after.mean():.3f}  "
      f"({out['improved_channels']}/8 channels better, {out['worsened_channels']}/8 worse)")
print("-> out/ldamp_prototype.json")
