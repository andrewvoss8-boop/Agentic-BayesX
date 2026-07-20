"""Forward models + Schneider correlated-complex-error machinery for Study A.

Physics: coupled source/load chain.
  DOF0 = source/interface (mass m1, grounded by k1,c1)
  DOF1 = load            (mass m2, coupled to source by k12,c12)
  DOF2 = HIDDEN dof      (mass m3, coupled to load by k23,c23)  -- TRUTH ONLY

The inference FEM is the 2-DOF model (DOF0,DOF1). The truth is 3-DOF; the missing
third DOF is the structural model-form error the discrepancy must absorb.

Observable: accelerance H_i0 = a_i / F0 (force at DOF0), for response DOF i in {0,1}.
Drive-point apparent mass = 1 / H_00 = F0 / a0 (the load read-out / 7004C observable).

All functions are JAX so the same code is differentiable for NUTS and usable for
numpy-style data generation.
"""
from __future__ import annotations
import jax
import jax.numpy as jnp

jax.config.update("jax_enable_x64", True)
TWO_PI = 2.0 * jnp.pi


def zeta_to_c(zeta, k, m):
    """Critical-damping conversion c = 2 zeta sqrt(k m)."""
    return 2.0 * zeta * jnp.sqrt(k * m)


def accelerance_2dof(freqs_hz, k1, k2, k12, c1, c2, c12, m1, m2):
    """Return complex accelerance channels [Nf,2]: H_00 and H_10 (a_i/F0)."""
    w = TWO_PI * freqs_hz                      # [Nf]
    M = jnp.array([[m1, 0.0], [0.0, m2]])
    K = jnp.array([[k1 + k12, -k12], [-k12, k2 + k12]])
    C = jnp.array([[c1 + c12, -c12], [-c12, c2 + c12]])

    def one(wi):
        Z = K + 1j * wi * C - (wi**2) * M
        H = jnp.linalg.inv(Z)
        a = -(wi**2) * H[:, 0]                 # accelerance column for force at DOF0
        return a                                # [2]
    A = jax.vmap(one)(w)                        # [Nf,2]
    return A


def accelerance_3dof(freqs_hz, k1, k2, k12, k23, c1, c2, c12, c23, m1, m2, m3):
    """Truth accelerance, same two observed channels (DOF0,DOF1), 3-DOF physics."""
    w = TWO_PI * freqs_hz
    M = jnp.array([[m1, 0.0, 0.0], [0.0, m2, 0.0], [0.0, 0.0, m3]])
    K = jnp.array([[k1 + k12, -k12, 0.0],
                   [-k12, k2 + k12 + k23, -k23],
                   [0.0, -k23, k23]])
    C = jnp.array([[c1 + c12, -c12, 0.0],
                   [-c12, c2 + c12 + c23, -c23],
                   [0.0, -c23, c23]])

    def one(wi):
        Z = K + 1j * wi * C - (wi**2) * M
        H = jnp.linalg.inv(Z)
        a = -(wi**2) * H[:, 0]
        return a[0:2]
    A = jax.vmap(one)(w)
    return A


def drivepoint_apparent_mass(accel_channel0):
    """Apparent mass M = F/a = 1 / accelerance at the drive point (channel 0)."""
    return 1.0 / accel_channel0


# ---------- Schneider correlation machinery (T-S2) ----------

def exp_corr(distances, length):
    """Stationary exponential correlation rho = exp(-|d|/length)."""
    return jnp.exp(-jnp.abs(distances) / length)


def schneider_R(freqs_hz, point_coords, length_f, length_z, r):
    """Additive space x frequency correlation matrix R (Eq. 25), ordered l=i+(s-1)nmp.

    R = r (R_ff kron I_nmp) + (1-r) (I_nf kron R_zz)
    freqs_hz: [nf], point_coords: [nmp] (1-D positions), returns [n,n], n=nf*nmp.
    """
    nf = freqs_hz.shape[0]
    nmp = point_coords.shape[0]
    df = jnp.abs(freqs_hz[:, None] - freqs_hz[None, :])      # [nf,nf]
    Rff = exp_corr(df, length_f)
    dz = jnp.abs(point_coords[:, None] - point_coords[None, :])
    Rzz = exp_corr(dz, length_z)
    Inmp = jnp.eye(nmp)
    Inf = jnp.eye(nf)
    R = r * jnp.kron(Rff, Inmp) + (1.0 - r) * jnp.kron(Inf, Rzz)
    return R


def stack_w_theta(data_complex, model_complex):
    """log-error split: r = log(data) - log(model) = w + i theta. Returns (w, theta) flat.

    Ordering matches schneider_R: l = i + (s-1)*nmp with i over points, s over freqs.
    Inputs are [nf, nmp] complex. Flatten row-major (freq outer, point inner).
    """
    logerr = jnp.log(data_complex) - jnp.log(model_complex)   # [nf,nmp] complex
    w = jnp.real(logerr).reshape(-1)
    theta = jnp.imag(logerr).reshape(-1)
    return w, theta
