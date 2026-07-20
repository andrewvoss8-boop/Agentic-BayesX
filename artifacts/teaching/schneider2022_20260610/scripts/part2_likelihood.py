"""
PART 2 -- The likelihood formulation (the heart of the paper).

Teaching arc:
  (1) MULTIPLICATIVE complex model error:  Y_obs = Y_model (x) eps  (Eq. 13).
  (2) log eps = w + i theta,  w=log|eps|~N(0,sw^2) (|eps| lognormal),
      theta~N(0,sth^2)  (Eq. 14-15).  -> "improper complex normal".
  (3) Joint PDF of real & imaginary error (Eq. A.9): circle -> arc -> kidney
      as (sw, sth) change (reproduces Fig. 1 structure, synthetic).
  (4) Likelihood = density of the residual in (w, theta) coords (Eq. 17-18):
      split the model-vs-data mismatch into a LOG-MAGNITUDE error and a
      PHASE error and score both with the Gaussian.
  (5) Correlation R over SPACE (Dz) and FREQUENCY (Df): additive split r
      (Eq. 19-25).  Why it matters: dense data is over-counted if you ignore
      it -> over-tight posterior + biased damping (paper Sec. 5.4.1).

All synthetic / conceptual.
"""
from __future__ import annotations
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation, PillowWriter
from matplotlib.colors import LogNorm

import common as C

rng = np.random.default_rng(11)


# ===========================================================================
# Joint PDF of (Re, Im) of a SCALAR multiplicative error  (Eq. A.9, n=1)
#   w = log|eps| = 0.5 log(u^2+v^2) ~ N(0, sw^2);  theta = atan2(v,u) ~ N(0,sth^2)
#   f(u,v) = N(w;0,sw) N(theta;0,sth) / (u^2+v^2)
# ===========================================================================
def joint_pdf_ReIm(U, V, sw, sth):
    r2 = U ** 2 + V ** 2
    r2 = np.where(r2 < 1e-12, 1e-12, r2)
    w = 0.5 * np.log(r2)
    th = np.arctan2(V, U)
    gw = np.exp(-0.5 * (w / sw) ** 2) / (np.sqrt(2 * np.pi) * sw)
    gt = np.exp(-0.5 * (th / sth) ** 2) / (np.sqrt(2 * np.pi) * sth)
    return gw * gt / r2


# ===========================================================================
# FIG 1 -- building the multiplicative error model
# ===========================================================================
def fig1_error_model_build():
    sw, sth = 0.30, 0.30
    n = 4000
    w = rng.normal(0, sw, n)
    th = rng.normal(0, sth, n)
    eps = np.exp(w) * np.exp(1j * th)

    fig, axes = plt.subplots(1, 4, figsize=(14.5, 3.8))
    ax = axes[0]
    ax.hist(np.exp(w), bins=60, color=C.C_MAG, alpha=0.85, density=True)
    ax.axvline(1, color="k", ls="--", lw=1)
    ax.set_title(r"(a) $|\epsilon|=e^{w}$  lognormal" + "\n(median 1)")
    ax.set_xlabel(r"$|\epsilon|$")

    ax = axes[1]
    ax.hist(th, bins=60, color=C.C_PHA, alpha=0.85, density=True)
    ax.axvline(0, color="k", ls="--", lw=1)
    ax.set_title(r"(b) phase $\theta$  normal")
    ax.set_xlabel(r"$\theta$ [rad]")

    ax = axes[2]
    ax.plot(eps.real, eps.imag, ".", color=C.ACCENT, ms=2, alpha=0.35)
    ax.plot(1, 0, "o", color=C.C_ERR, ms=8)
    ax.add_patch(plt.Circle((0, 0), 1, fill=False, ls=":", color="0.5"))
    ax.axhline(0, color="k", lw=0.5); ax.axvline(0, color="k", lw=0.5)
    ax.set_aspect("equal"); ax.set_xlim(-0.2, 2.2); ax.set_ylim(-1.2, 1.2)
    ax.set_title(r"(c) $\epsilon=|\epsilon|e^{i\theta}$ in complex plane")
    ax.set_xlabel(r"Re{$\epsilon$}"); ax.set_ylabel(r"Im{$\epsilon$}")

    ax = axes[3]
    Hm = 0.7 * np.exp(1j * 0.6)        # a model FRF value
    Yobs = Hm * eps                     # multiplicative effect (Eq. 13)
    ax.plot(Yobs.real, Yobs.imag, ".", color=C.C_SURR, ms=2, alpha=0.3)
    ax.plot(Hm.real, Hm.imag, "o", color=C.C_TRUTH, ms=9, label="model $Y_S$")
    ax.annotate("", xy=(Hm.real, Hm.imag), xytext=(0, 0),
                arrowprops=dict(arrowstyle="-|>", color=C.C_TRUTH, lw=1.5))
    ax.axhline(0, color="k", lw=0.5); ax.axvline(0, color="k", lw=0.5)
    ax.set_aspect("equal")
    ax.set_title(r"(d) $Y_{obs}=Y_S\,\epsilon$" + "\nerror scales+rotates model")
    ax.set_xlabel(r"Re{$Y$}"); ax.set_ylabel(r"Im{$Y$}")
    ax.legend(loc="upper left")
    fig.suptitle(r"Multiplicative complex error: $\log\epsilon = w + i\theta$, "
                 r"$w\sim N(0,\sigma_w^2)$, $\theta\sim N(0,\sigma_\theta^2)$",
                 fontweight="bold")
    C.save(fig, "p2_fig1_error_model_build.png", rect=(0, 0.025, 1, 0.9))


# ===========================================================================
# FIG 2 -- joint PDF grid (reproduces Fig. 1 of the paper, synthetic)
# ===========================================================================
def fig2_joint_pdf_grid():
    combos = [(0.10, 0.10), (0.10, 0.50), (0.50, 0.10), (0.50, 0.50)]
    titles = ["both small\n(tight blob)", r"small $\sigma_w$, large $\sigma_\theta$"
              + "\n(arc along circle)", r"large $\sigma_w$, small $\sigma_\theta$"
              + "\n(radial smear)", "both large\n(kidney)"]
    u = np.linspace(-0.4, 2.3, 360)
    v = np.linspace(-1.5, 1.5, 360)
    U, V = np.meshgrid(u, v)
    fig, axes = plt.subplots(1, 4, figsize=(14.5, 3.9))
    for ax, (sw, sth), t in zip(axes, combos, titles):
        Z = joint_pdf_ReIm(U, V, sw, sth)
        ax.contourf(U, V, Z, levels=24, cmap="magma")
        ax.contour(U, V, Z, levels=8, colors="w", linewidths=0.4, alpha=0.5)
        ax.plot(1, 0, "+", color="cyan", ms=10, mew=2)
        ax.axhline(0, color="w", lw=0.4); ax.axvline(0, color="w", lw=0.4)
        ax.set_aspect("equal")
        ax.set_title(rf"$\sigma_w$={sw}, $\sigma_\theta$={sth}" + "\n" + t,
                     fontsize=10)
        ax.set_xlabel(r"Re{$\epsilon$}")
    axes[0].set_ylabel(r"Im{$\epsilon$}")
    fig.suptitle("Joint PDF of real & imaginary model error (Eq. A.9) -- "
                 "improper (non-circular) complex normal", fontweight="bold")
    C.save(fig, "p2_fig2_joint_pdf_grid.png", rect=(0, 0.025, 1, 0.9))


# ===========================================================================
# FIG 3 -- the likelihood of ONE observation (Eq. 17-18)
# ===========================================================================
def fig3_one_likelihood():
    sw, sth = 0.30, 0.30
    Ys = 0.7 * np.exp(1j * 0.6)            # surrogate/model value
    Yobs = 1.0 * np.exp(1j * 0.95)         # measured value
    logeps = np.log(Yobs) - np.log(Ys)     # residual in log space (Eq. 16)
    w_res, th_res = logeps.real, logeps.imag

    fig, axes = plt.subplots(1, 2, figsize=(12.4, 4.8))
    # left: complex plane with the two values and the (w,theta) decomposition
    ax = axes[0]
    u = np.linspace(0.1, 1.7, 300); v = np.linspace(-0.2, 1.4, 300)
    U, V = np.meshgrid(u, v)
    # error PDF centered on the MODEL value (scaled/rotated kidney)
    eps_grid = (U + 1j * V) / Ys
    Z = joint_pdf_ReIm(eps_grid.real, eps_grid.imag, sw, sth)
    ax.contourf(U, V, Z, levels=20, cmap="magma", alpha=0.9)
    ax.plot(Ys.real, Ys.imag, "o", color="cyan", ms=10, label=r"model $Y_S(x)$")
    ax.plot(Yobs.real, Yobs.imag, "X", color="lime", ms=12, mew=1.5,
            label=r"measured $Y_{obs}$")
    ax.plot([Ys.real, Yobs.real], [Ys.imag, Yobs.imag], "w--", lw=1)
    ax.axhline(0, color="w", lw=0.4); ax.axvline(0, color="w", lw=0.4)
    ax.set_aspect("equal"); ax.set_xlabel("Re"); ax.set_ylabel("Im")
    ax.set_title("Likelihood = error-PDF height at the measured point\n"
                 "(PDF = kidney scaled+rotated by the model value)")
    ax.legend(loc="upper left")

    # right: the residual scored in (w, theta) coords
    ax = axes[1]
    wax = np.linspace(-1, 1, 300); tax = np.linspace(-1, 1, 300)
    Wg, Tg = np.meshgrid(wax, tax)
    G = (np.exp(-0.5 * (Wg / sw) ** 2) * np.exp(-0.5 * (Tg / sth) ** 2))
    ax.contourf(Wg, Tg, G, levels=20, cmap="viridis")
    ax.plot(0, 0, "+", color="w", ms=12, mew=2)
    ax.plot(w_res, th_res, "X", color="red", ms=13, mew=1.5)
    ax.plot([0, w_res], [0, 0], color="orange", lw=2.5)
    ax.plot([w_res, w_res], [0, th_res], color="deepskyblue", lw=2.5)
    ax.text(w_res / 2, -0.08, "log-magnitude\nerror  w", color="orange",
            ha="center", va="top", fontsize=9)
    ax.text(w_res + 0.03, th_res / 2, "phase\nerror  " + r"$\theta$",
            color="deepskyblue", va="center", fontsize=9)
    ax.set_xlabel(r"$w=\log|\epsilon|$ (magnitude mismatch)")
    ax.set_ylabel(r"$\theta$ (phase mismatch)")
    ax.set_title(r"Same thing in $(w,\theta)$: a plain Gaussian (Eq. 18)"
                 + f"\nresidual w={w_res:+.2f}, "
                 + rf"$\theta$={th_res:+.2f}")
    fig.suptitle("Eq. (17):  L(x) = f_{log eps}( log Y_obs - log Y_S(x) )",
                 fontweight="bold")
    C.save(fig, "p2_fig3_one_likelihood.png", rect=(0, 0.025, 1, 0.92))


# ===========================================================================
# Correlation model (Eq. 19-25)
# ===========================================================================
# 5 synthetic sensor coords on a 2.5 x 1.1 m plate (echoes paper's 5 points)
SENSORS = np.array([[0.30, 0.56], [1.68, 0.56], [2.60, 0.56],
                    [0.76, 1.02], [2.60, 1.02]])
NMP = len(SENSORS)


def Rzz(lz):
    d = np.linalg.norm(SENSORS[:, None, :] - SENSORS[None, :, :], axis=-1)
    return np.exp(-d / lz)


def Rff(freqs, lf):
    df = np.abs(freqs[:, None] - freqs[None, :])
    return np.exp(-df / lf)


def full_R(freqs, lz, lf, r):
    """Additive spatial+frequency correlation, Eq. (19), assembled for all
    (sensor, frequency) pairs ordered by l = i + (s-1)*nmp (Eq. 24).

    R[(i,s),(i',s')] = r*exp(-Df/lf) + (1-r)*exp(-Dz/lz).
    (The paper writes this via Kronecker products, Eq. 25, for fast inversion.)
    """
    nf = len(freqs)
    Rz = Rzz(lz)            # nmp x nmp
    Rf = Rff(freqs, lf)     # nf x nf
    J_mp = np.ones((NMP, NMP))
    J_f = np.ones((nf, nf))
    R = r * np.kron(Rf, J_mp) + (1 - r) * np.kron(J_f, Rz)
    return R


def fig4_correlation_matrices():
    freqs = np.arange(100, 120.0)        # 20 lines, 1 Hz spacing
    nf = len(freqs)
    lz, lf, r = 0.8, 5.0, 0.7
    Rz = Rzz(lz); Rf = Rff(freqs, lf); R = full_R(freqs, lz, lf, r)

    fig = plt.figure(figsize=(13.5, 4.4))
    gs = fig.add_gridspec(1, 3, width_ratios=[0.8, 1, 1.25])
    ax = fig.add_subplot(gs[0])
    im = ax.imshow(Rz, cmap="viridis", vmin=0, vmax=1)
    ax.set_title(f"(a) spatial $R_{{zz}}$ (5 sensors)\n$l_z$={lz} m")
    ax.set_xlabel("sensor"); ax.set_ylabel("sensor")
    fig.colorbar(im, ax=ax, fraction=0.046)

    ax = fig.add_subplot(gs[1])
    im = ax.imshow(Rf, cmap="viridis", vmin=0, vmax=1)
    ax.set_title(f"(b) frequency $R_{{ff}}$ (20 lines)\n$l_f$={lf} Hz")
    ax.set_xlabel("freq line"); ax.set_ylabel("freq line")
    fig.colorbar(im, ax=ax, fraction=0.046)

    ax = fig.add_subplot(gs[2])
    im = ax.imshow(R, cmap="viridis", vmin=0, vmax=1)
    for k in range(1, nf):
        ax.axhline(k * NMP - 0.5, color="w", lw=0.3, alpha=0.5)
        ax.axvline(k * NMP - 0.5, color="w", lw=0.3, alpha=0.5)
    ax.set_title(f"(c) full $R$ = $r(R_{{ff}}\\otimes J)+(1-r)(J\\otimes R_{{zz}})$\n"
                 f"r={r}, ordered by l=i+(s-1)$n_{{mp}}$  ({R.shape[0]}x{R.shape[0]})")
    ax.set_xlabel("observation index l"); ax.set_ylabel("observation index l")
    fig.colorbar(im, ax=ax, fraction=0.046)
    fig.suptitle("Model-error correlation over SPACE and FREQUENCY (Eq. 19-25)",
                 fontweight="bold")
    C.save(fig, "p2_fig4_correlation_matrices.png", rect=(0, 0.025, 1, 0.92))


def fig5_split_factor():
    df = np.linspace(0, 40, 300)
    dz = np.linspace(0, 3, 300)
    lf, lz = 8.0, 0.8
    fig, axes = plt.subplots(1, 2, figsize=(12.2, 4.4))
    ax = axes[0]
    for r in [0.0, 0.3, 0.6, 0.82, 1.0]:
        rho = r * np.exp(-df / lf) + (1 - r) * 1.0   # Dz=0 -> rho_z=1
        ax.plot(df, rho, lw=2, label=f"r={r}")
    ax.axhline(0, color="k", lw=0.5)
    ax.set_xlabel(r"$\Delta f$ [Hz]  (same sensor)")
    ax.set_ylabel(r"correlation $\rho$")
    ax.set_title(r"Across frequency: floor $\to (1-r)$ as $\Delta f\to\infty$"
                 + "\n(Eq. 22)")
    ax.legend(title=r"split $r$")

    ax = axes[1]
    for r in [0.0, 0.3, 0.6, 0.82, 1.0]:
        rho = r * 1.0 + (1 - r) * np.exp(-dz / lz)   # Df=0 -> rho_f=1
        ax.plot(dz, rho, lw=2, label=f"r={r}")
    ax.set_xlabel(r"$\Delta z$ [m]  (same frequency)")
    ax.set_ylabel(r"correlation $\rho$")
    ax.set_title(r"Across space: floor $\to r$ as $\Delta z\to\infty$"
                 + "\n(Eq. 23)")
    ax.legend(title=r"split $r$")
    fig.suptitle(r"Split factor $r$: how much correlation lives in frequency vs "
                 r"space. Paper learns $r\approx0.82$ (frequency-shared error)",
                 fontweight="bold")
    C.save(fig, "p2_fig5_split_factor.png", rect=(0, 0.025, 1, 0.92))


def fig6_effective_data():
    # AR(1)-style effective sample size for n correlated frequency lines
    n = 136                       # like the paper's 25-160 Hz at 1 Hz
    lf = np.linspace(0.2, 40, 300)
    rho = np.exp(-1.0 / lf)       # adjacent-line correlation at 1 Hz spacing
    neff = n * (1 - rho) / (1 + rho)   # AR(1) ESS approximation
    fig, ax = plt.subplots(figsize=(8.8, 4.8))
    ax.plot(lf, neff, color=C.C_ERR, lw=2.5)
    ax.axhline(n, color=C.PRIOR if False else "0.4", ls="--",
               label=f"naive count (R=I): {n}")
    for L in [1, 5, 10, 20]:
        rr = np.exp(-1.0 / L); ne = n * (1 - rr) / (1 + rr)
        ax.plot(L, ne, "o", color=C.C_TRUTH)
        ax.annotate(f"$l_f$={L} Hz\n$\\approx${ne:.0f} indep.", (L, ne),
                    textcoords="offset points", xytext=(8, 8), fontsize=9)
    ax.set_xlabel(r"frequency correlation length $l_f$ [Hz]")
    ax.set_ylabel("effective # of INDEPENDENT data points")
    ax.set_title("Why correlation matters: dense data is OVER-COUNTED if ignored\n"
                 "(illustrative AR(1) ESS; paper learns $l_f\\approx$10 Hz)")
    ax.legend()
    C.save(fig, "p2_fig6_effective_data.png")


def fig7_correlated_vs_uncorrelated_posterior():
    # toy: infer a mean theta from n correlated residuals; show posterior width
    # with correct R vs with R=I (over-confident).  Echoes paper's damping finding.
    n = 40
    freqs = np.arange(n, dtype=float)         # 1-unit spacing
    lf = 8.0
    Rf = np.exp(-np.abs(freqs[:, None] - freqs[None, :]) / lf)
    sig = 0.3
    Cov = sig ** 2 * Rf
    true_mu = 1.0
    L = np.linalg.cholesky(Cov)
    y = true_mu + L @ rng.standard_normal(n)
    ones = np.ones(n)

    def post(Covm):
        Ci = np.linalg.inv(Covm)
        prec = ones @ Ci @ ones
        mean = (ones @ Ci @ y) / prec
        var = 1.0 / prec
        return mean, np.sqrt(var)

    m_c, s_c = post(Cov)                       # correct (correlated)
    m_u, s_u = post(sig ** 2 * np.eye(n))      # wrong (independence)
    xs = np.linspace(true_mu - 0.5, true_mu + 0.5, 400)
    fig, ax = plt.subplots(figsize=(9.0, 4.8))
    ax.plot(xs, np.exp(-0.5 * ((xs - m_c) / s_c) ** 2),
            color=C.C_ACC, lw=2.5, label=f"correlated R  (sd={s_c:.3f})")
    ax.plot(xs, np.exp(-0.5 * ((xs - m_u) / s_u) ** 2),
            color=C.C_ERR, lw=2.5, ls="--",
            label=f"independence R=I  (sd={s_u:.3f})")
    ax.axvline(true_mu, color="k", ls=":", label="truth")
    ax.set_xlabel("inferred parameter")
    ax.set_ylabel("posterior (unnormalized)")
    ax.set_title("Ignoring correlation -> artificially TIGHT, over-confident posterior\n"
                 f"here {s_c / s_u:.1f}x narrower; in the paper this biases DAMPING low")
    ax.legend()
    C.save(fig, "p2_fig7_correlated_vs_uncorrelated_posterior.png")


# ===========================================================================
# GIF 1 -- kidney morph (sweep sw, sth)
# ===========================================================================
def gif1_kidney_morph():
    u = np.linspace(-0.4, 2.3, 240); v = np.linspace(-1.5, 1.5, 240)
    U, V = np.meshgrid(u, v)
    # path: grow sth, then grow sw, then shrink sth
    seg = 22
    sths = np.concatenate([np.linspace(0.08, 0.6, seg),
                           np.full(seg, 0.6),
                           np.linspace(0.6, 0.12, seg)])
    sws = np.concatenate([np.full(seg, 0.10),
                          np.linspace(0.10, 0.6, seg),
                          np.full(seg, 0.55)])
    fig, ax = plt.subplots(figsize=(5.6, 5.2))
    ax.set_aspect("equal"); ax.set_xlabel(r"Re{$\epsilon$}")
    ax.set_ylabel(r"Im{$\epsilon$}")
    C.stamp(fig)

    def update(j):
        ax.clear()
        sw, sth = sws[j], sths[j]
        Z = joint_pdf_ReIm(U, V, sw, sth)
        ax.contourf(U, V, Z, levels=22, cmap="magma")
        ax.plot(1, 0, "+", color="cyan", ms=10, mew=2)
        ax.axhline(0, color="w", lw=0.4); ax.axvline(0, color="w", lw=0.4)
        ax.set_aspect("equal")
        ax.set_title(rf"$\sigma_w$={sw:.2f}, $\sigma_\theta$={sth:.2f}"
                     + "\ncircle -> arc -> kidney")
        ax.set_xlabel(r"Re{$\epsilon$}"); ax.set_ylabel(r"Im{$\epsilon$}")

    anim = FuncAnimation(fig, update, frames=len(sws), blit=False)
    out = C.gif_path("p2_gif1_kidney_morph.gif")
    anim.save(out, writer=PillowWriter(fps=14)); plt.close(fig)
    print("  wrote", out.relative_to(C.BASE))


# ===========================================================================
# GIF 2 -- error scatter: radial spread (sw) then tangential spread (sth)
# ===========================================================================
def gif2_error_scatter():
    n = 1500
    z0 = rng.standard_normal(n)        # base normals (fixed) for w
    t0 = rng.standard_normal(n)        # base normals for theta
    seg = 25
    sws = np.concatenate([np.linspace(0.02, 0.5, seg), np.full(seg, 0.5)])
    sths = np.concatenate([np.full(seg, 0.02), np.linspace(0.02, 0.6, seg)])
    fig, ax = plt.subplots(figsize=(5.6, 5.2)); C.stamp(fig)

    def update(j):
        ax.clear()
        sw, sth = sws[j], sths[j]
        eps = np.exp(sw * z0) * np.exp(1j * sth * t0)
        ax.plot(eps.real, eps.imag, ".", color=C.ACCENT, ms=2.5, alpha=0.35)
        ax.add_patch(plt.Circle((0, 0), 1, fill=False, ls=":", color="0.5"))
        ax.plot(1, 0, "o", color=C.C_ERR, ms=7)
        ax.axhline(0, color="k", lw=0.5); ax.axvline(0, color="k", lw=0.5)
        ax.set_xlim(-0.4, 2.4); ax.set_ylim(-1.3, 1.3); ax.set_aspect("equal")
        phase = ("radial spread grows ($\\sigma_w$)" if j < seg
                 else "tangential spread grows ($\\sigma_\\theta$)")
        ax.set_title(rf"$\sigma_w$={sw:.2f}, $\sigma_\theta$={sth:.2f}" + "\n" + phase)
        ax.set_xlabel(r"Re{$\epsilon$}"); ax.set_ylabel(r"Im{$\epsilon$}")

    anim = FuncAnimation(fig, update, frames=len(sws), blit=False)
    out = C.gif_path("p2_gif2_error_scatter.gif")
    anim.save(out, writer=PillowWriter(fps=14)); plt.close(fig)
    print("  wrote", out.relative_to(C.BASE))


# ===========================================================================
# GIF 3 -- correlation matrix as the split factor r sweeps 0 -> 1
# ===========================================================================
def gif3_correlation_sweep():
    freqs = np.arange(100, 120.0)
    nf = len(freqs)
    lz, lf = 0.8, 5.0
    rs = np.linspace(0, 1, 41)
    fig, ax = plt.subplots(figsize=(6.0, 5.4))
    im = ax.imshow(full_R(freqs, lz, lf, 0.5), cmap="viridis", vmin=0, vmax=1)
    fig.colorbar(im, ax=ax, fraction=0.046)
    for k in range(1, nf):
        ax.axhline(k * NMP - 0.5, color="w", lw=0.25, alpha=0.4)
        ax.axvline(k * NMP - 0.5, color="w", lw=0.25, alpha=0.4)
    ax.set_xlabel("observation index l"); ax.set_ylabel("observation index l")
    C.stamp(fig)

    def update(j):
        r = rs[j]
        im.set_data(full_R(freqs, lz, lf, r))
        ax.set_title(f"r={r:.2f}: "
                     + ("space-shared (block diag)" if r < 0.4
                        else "frequency-shared (stripes)" if r > 0.6
                        else "mixed"))
        return [im]

    anim = FuncAnimation(fig, update, frames=len(rs), blit=False)
    out = C.gif_path("p2_gif3_correlation_sweep.gif")
    anim.save(out, writer=PillowWriter(fps=12)); plt.close(fig)
    print("  wrote", out.relative_to(C.BASE))


if __name__ == "__main__":
    print("[part2] figures")
    fig1_error_model_build()
    fig2_joint_pdf_grid()
    fig3_one_likelihood()
    fig4_correlation_matrices()
    fig5_split_factor()
    fig6_effective_data()
    fig7_correlated_vs_uncorrelated_posterior()
    print("[part2] gifs")
    gif1_kidney_morph()
    gif2_error_scatter()
    gif3_correlation_sweep()
    print("[part2] done")
