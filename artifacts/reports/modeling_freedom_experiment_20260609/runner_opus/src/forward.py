"""Forward model for the synthetic tray: fixed-free grounded 12-DOF chain.

Modeling assumptions (see ../decisions_log.md A1-A4):
  - N=12 DOF, uniform mass m=1 (M=I).
  - 12 springs: spring0 = ground->mass0; spring i = mass_{i-1}->mass_i (i=1..11).
  - 4 stiffness groups of 3 consecutive springs, scaled by theta_g * k0 (k0=3e6).
  - NO cross-link joint (the deliberate model-form error from the public config).
All ops are jax-differentiable so NUTS/HMC can use gradients.
"""
import jax
jax.config.update("jax_enable_x64", True)
import jax.numpy as jnp
import numpy as np

N = 12
K0 = 3.0e6
M_UNIFORM = 1.0
NMODES = 6
SENSORS = np.array([0, 2, 3, 5, 6, 8, 9, 11])
ZETA = 0.02


def _spring_vec(theta):
    # theta: (4,) -> 12 spring stiffnesses (group of 3 each), * k0
    return jnp.repeat(theta, 3) * K0


def assemble_K(theta):
    k = _spring_vec(theta)
    # tridiagonal fixed-free: ground spring on DOF0, then chain
    diag = jnp.zeros(N)
    diag = diag.at[0].add(k[0])
    main = jnp.zeros(N)
    off = jnp.zeros(N - 1)
    # interconnect springs k[1..11] between i-1 and i
    ki = k[1:]  # length 11
    main = main.at[0].add(k[0])
    main = main.at[1:].add(ki)        # contribution to mass i
    main = main.at[:-1].add(ki)       # contribution to mass i-1
    off = off - ki
    K = jnp.diag(main) + jnp.diag(off, 1) + jnp.diag(off, -1)
    return K


def modes(theta, nmodes=NMODES):
    """Return (freqs_hz[nmodes], shapes_full[N,nmodes]) mass-normalized (M=I -> unit norm)."""
    K = assemble_K(theta)
    w2, V = jnp.linalg.eigh(K)  # ascending; M=I so V already mass-normalized (unit cols)
    f = jnp.sqrt(jnp.abs(w2)) / (2 * jnp.pi)
    return f[:nmodes], V[:, :nmodes]


def modes_sens(theta, nmodes=NMODES):
    f, V = modes(theta, nmodes)
    return f, V[SENSORS, :]


def receptance_peak(theta, out_dof, in_dof, band=(10.0, 600.0), ngrid=4000, zeta=ZETA):
    """Peak |H_{out,in}(w)| over the band, units m/N. Uses ALL 12 modes for accuracy.
    H_jk(w) = sum_n phi_jn phi_kn / (wn^2 - w^2 + 2 i zeta wn w).
    """
    K = assemble_K(theta)
    w2, V = jnp.linalg.eigh(K)
    wn = jnp.sqrt(jnp.abs(w2))           # rad/s, all 12
    fgrid = jnp.linspace(band[0], band[1], ngrid)
    w = 2 * jnp.pi * fgrid
    phi_j = V[out_dof, :]
    phi_k = V[in_dof, :]
    num = phi_j * phi_k                   # (12,)
    # denom over grid: (ngrid,12)
    denom = (wn[None, :] ** 2 - w[:, None] ** 2) + 2j * zeta * wn[None, :] * w[:, None]
    H = jnp.sum(num[None, :] / denom, axis=1)
    return jnp.max(jnp.abs(H))


if __name__ == "__main__":
    th = jnp.array([1.79, 0.93, 1.10, 0.86])
    f, Vs = modes_sens(th)
    print("freqs", np.asarray(f))
    print("sens shape norms", np.linalg.norm(np.asarray(Vs), axis=0))
    print("QOI ref (11<-0)", float(receptance_peak(th, 11, 0)))
    print("QOI heldout (5<-8)", float(receptance_peak(th, 5, 8)))
