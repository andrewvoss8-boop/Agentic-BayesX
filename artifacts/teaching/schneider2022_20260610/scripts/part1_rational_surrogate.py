"""
PART 1 -- Building a PCE-rational surrogate of an FRF.

Teaching arc:
  (1) An FRF is COMPLEX-valued: real+imaginary  <->  magnitude+phase.
  (2) An FRF is naturally a RATIONAL function (ratio of polynomials) -- of
      frequency, AND of the model parameters.  Polynomials struggle at
      resonance; rationals do not.
  (3) The paper's surrogate (Eq. 3-9): R(X)=P(X)/Q(X) with Hermite-PCE
      numerator/denominator, fit by the linearized regression of Eq. (6)-(9).
  (4) How well it approximates -- in the complex (Nyquist) plane and in
      magnitude/phase.

All synthetic.  Mode frequencies borrow the paper's public shell-model
eigenfrequencies (Fig. C.10) only so the toy FRF looks structurally familiar.
"""
from __future__ import annotations
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation, PillowWriter

import common as C

rng = np.random.default_rng(7)

# ---- a toy 5-mode FRF (synthetic; frequencies from paper Fig. C.10) --------
FR = [30.8, 64.7, 87.0, 105.0, 155.0]            # Hz
ZE = [0.025, 0.022, 0.028, 0.030, 0.035]         # damping ratios
AMP = [1.0, -0.8, 0.9, -0.7, 1.1]                # modal constants (sign -> antiresonances)
FGRID = np.linspace(25, 160, 271)                # 0.5 Hz spacing


def H_true(f):
    return C.modal_frf(f, FR, ZE, AMP)


# ===========================================================================
# FIG 1 -- the complex nature of an FRF: Nyquist + magnitude + phase
# ===========================================================================
def fig1_complex_nature():
    f = FGRID
    H = H_true(f)
    fig = plt.figure(figsize=(12.4, 4.2))
    gs = fig.add_gridspec(1, 3, width_ratios=[1.15, 1, 1])

    ax0 = fig.add_subplot(gs[0])
    sc = ax0.scatter(H.real, H.imag, c=f, cmap="viridis", s=14)
    ax0.axhline(0, color="k", lw=0.6); ax0.axvline(0, color="k", lw=0.6)
    ax0.set_xlabel("Re{H}"); ax0.set_ylabel("Im{H}")
    ax0.set_title("(a) Complex plane (Nyquist)\neach resonance = a loop")
    ax0.set_aspect("equal", adjustable="datalim")
    cb = fig.colorbar(sc, ax=ax0, fraction=0.046, pad=0.04); cb.set_label("f [Hz]")

    ax1 = fig.add_subplot(gs[1])
    ax1.semilogy(f, np.abs(H), color=C.C_MAG, lw=2)
    for fr in FR:
        ax1.axvline(fr, color="k", ls=":", lw=0.7, alpha=0.5)
    ax1.set_xlabel("f [Hz]"); ax1.set_ylabel("|H|")
    ax1.set_title("(b) Magnitude (peaks = modes)")

    ax2 = fig.add_subplot(gs[2])
    ax2.plot(f, np.unwrap(np.angle(H)), color=C.C_PHA, lw=2)
    for fr in FR:
        ax2.axvline(fr, color="k", ls=":", lw=0.7, alpha=0.5)
    ax2.set_xlabel("f [Hz]"); ax2.set_ylabel("phase [rad]")
    ax2.set_title("(c) Phase (drops ~pi per mode)")

    fig.suptitle("FRF is COMPLEX-valued:  H = Re + i Im  =  |H| e^{i phase}",
                 fontweight="bold")
    C.save(fig, "p1_fig1_complex_nature.png", rect=(0, 0.025, 1, 0.93))


# ===========================================================================
# FIG 2 -- one frequency point: a+bi <-> magnitude/phase
# ===========================================================================
def fig2_one_point():
    f0 = 95.0
    H0 = H_true(np.array([f0]))[0]
    fig, ax = plt.subplots(figsize=(6.2, 5.4))
    ax.axhline(0, color="k", lw=0.6); ax.axvline(0, color="k", lw=0.6)
    ax.annotate("", xy=(H0.real, H0.imag), xytext=(0, 0),
                arrowprops=dict(arrowstyle="-|>", color=C.ACCENT, lw=2.5))
    ax.plot([H0.real, H0.real], [0, H0.imag], color=C.C_ERR, ls="--", lw=1.5)
    ax.plot([0, H0.real], [H0.imag, H0.imag], color=C.C_ERR, ls="--", lw=1.5)
    ax.plot(H0.real, H0.imag, "o", color=C.C_TRUTH, ms=9)
    th = np.linspace(0, np.angle(H0), 60)
    rr = 0.25 * abs(H0)
    ax.plot(rr * np.cos(th), rr * np.sin(th), color=C.C_PHA, lw=2)
    ax.text(H0.real / 2, -0.12 * abs(H0), "a = Re{H}", color=C.C_ERR, ha="center")
    ax.text(H0.real + 0.02 * abs(H0), H0.imag / 2, "b = Im{H}",
            color=C.C_ERR, va="center")
    ax.text(0.55 * H0.real, 0.55 * H0.imag, "|H|", color=C.ACCENT,
            fontsize=12, fontweight="bold")
    ax.text(rr * 1.2 * np.cos(np.angle(H0) / 2), rr * 1.2 * np.sin(np.angle(H0) / 2),
            "phase", color=C.C_PHA)
    ax.set_aspect("equal", adjustable="datalim")
    ax.set_xlabel("Re{H}"); ax.set_ylabel("Im{H}")
    ax.set_title(f"One FRF value at f = {f0:.0f} Hz\n"
                 f"|H|={abs(H0):.3g},  phase={np.angle(H0):+.2f} rad")
    C.save(fig, "p1_fig2_one_point.png")


# ===========================================================================
# FIG 3 -- polynomial vs rational fit OF FREQUENCY (why rational wins)
#   Uses the paper's OWN linearized rational regression (Eq. 6-9) but with a
#   monomial basis in normalized frequency instead of Hermite-in-X.
# ===========================================================================
def _design_freq(f, deg):
    x = (f - FGRID.mean()) / (0.5 * (FGRID[-1] - FGRID[0]))   # -> ~[-1,1]
    return np.vander(x, deg + 1, increasing=True)


def fig3_poly_vs_rational_freq():
    f = FGRID
    H = H_true(f)
    # plain polynomial PCE (numerator only), high degree
    deg_poly = 14
    Psi = _design_freq(f, deg_poly)
    p_poly = C.fit_poly_pce(Psi, H)
    H_poly = Psi @ p_poly
    # rational fit  P/Q  (np=10, nq=12) via Eq. (6)-(9)
    dp, dq = 10, 12
    PsiP = _design_freq(f, dp)
    PsiQ = _design_freq(f, dq)
    p, q = C.fit_rational_pce(PsiP, PsiQ, H)
    H_rat = C.eval_rational(PsiP, PsiQ, p, q)

    fig, axes = plt.subplots(1, 2, figsize=(12.2, 4.6))
    ax = axes[0]
    ax.semilogy(f, np.abs(H), color=C.C_TRUTH, lw=2.4, label="true FRF")
    ax.semilogy(f, np.abs(H_poly), color=C.C_POLY, lw=1.8, ls="--",
                label=f"polynomial deg {deg_poly}")
    ax.semilogy(f, np.abs(H_rat), color=C.C_SURR, lw=1.8, ls=":",
                label=f"rational P/Q ({dp},{dq})")
    ax.set_xlabel("f [Hz]"); ax.set_ylabel("|H|")
    ax.set_title("Fit OF FREQUENCY: rational tracks every resonance")
    ax.legend(loc="lower right")

    ax = axes[1]
    ax.semilogy(f, np.abs(H_poly - H) + 1e-16, color=C.C_POLY, lw=1.8,
                label="polynomial error")
    ax.semilogy(f, np.abs(H_rat - H) + 1e-16, color=C.C_SURR, lw=1.8,
                label="rational error")
    ax.set_xlabel("f [Hz]"); ax.set_ylabel("|H_approx - H_true|")
    ax.set_title("Absolute error (log): rational ~ machine-level")
    ax.legend(loc="upper right")
    fig.suptitle("Why a RATIONAL surrogate: an FRF is a ratio of polynomials; "
                 "a single polynomial cannot place poles", fontweight="bold")
    C.save(fig, "p1_fig3_poly_vs_rational_freq.png", rect=(0, 0.025, 1, 0.92))


# ===========================================================================
# FIG 4 -- the paper's actual surrogate: rational IN THE PARAMETER (Hermite-PCE)
#   FRF value at a fixed frequency as a function of a stiffness scale k(xi),
#   k lognormal (like the paper's prior).  Plain Hermite-PCE vs rational
#   Hermite-PCE.  The parameter sweep crosses a resonance -> a pole in k.
# ===========================================================================
FR0 = [88.0, 150.0]      # nominal mode freqs for the parameter demo
ETA = [0.05, 0.06]       # hysteretic loss factors
AMP2 = [1.0, 0.6]
F0_DEMO = 95.0           # fixed observation frequency (just above mode 1)
K0, SIG = 1.0, 0.10      # lognormal stiffness scale: k = K0*exp(SIG*xi)


def k_of_xi(xi):
    return K0 * np.exp(SIG * xi)


def H_of_xi(xi):
    k = k_of_xi(xi)
    return C.hysteretic_frf_vs_param(F0_DEMO, k, FR0, ETA, AMP2)


def fig4_rational_in_parameter():
    # experimental design (LHS-like): standard-normal samples
    N = 60
    xi_ed = np.sort(rng.standard_normal(N) * 1.1)
    M = H_of_xi(xi_ed)
    xi_test = np.linspace(-3, 3, 400)
    H_test = H_of_xi(xi_test)

    # plain Hermite-PCE (numerator only), degree d
    d_poly = 8
    p_poly = C.fit_poly_pce(C.hermite_norm(xi_ed, d_poly), M)
    H_poly = C.hermite_norm(xi_test, d_poly) @ p_poly
    # rational Hermite-PCE: mp=3, mq=4 (exactly the paper's CLT choice!)
    mp, mq = 3, 4
    PsiP = C.hermite_norm(xi_ed, mp)
    PsiQ = C.hermite_norm(xi_ed, mq)
    p, q = C.fit_rational_pce(PsiP, PsiQ, M)
    H_rat = C.eval_rational(C.hermite_norm(xi_test, mp),
                            C.hermite_norm(xi_test, mq), p, q)

    fig, axes = plt.subplots(1, 2, figsize=(12.2, 4.7))
    ax = axes[0]
    ax.semilogy(xi_test, np.abs(H_test), color=C.C_TRUTH, lw=2.4, label="true |H(k)|")
    ax.semilogy(xi_test, np.abs(H_poly), color=C.C_POLY, lw=1.8, ls="--",
                label=f"Hermite-PCE deg {d_poly}")
    ax.semilogy(xi_test, np.abs(H_rat), color=C.C_SURR, lw=1.8, ls=":",
                label=f"rational PCE ($m_p$={mp},$m_q$={mq})")
    ax.semilogy(xi_ed, np.abs(M), ".", color="k", ms=5, alpha=0.5,
                label="experimental design")
    ax.set_xlabel(r"standard-normal input $\xi$  (k = $k_0 e^{\sigma\xi}$, lognormal)")
    ax.set_ylabel(r"|H| at fixed f = 95 Hz")
    ax.set_title("Surrogate IN THE PARAMETER: resonance crossing = a pole in k")
    ax.legend(loc="lower center", ncol=1)

    ax = axes[1]
    ax.semilogy(xi_test, np.abs(H_poly - H_test) + 1e-16, color=C.C_POLY,
                lw=1.8, label="polynomial-PCE error")
    ax.semilogy(xi_test, np.abs(H_rat - H_test) + 1e-16, color=C.C_SURR,
                lw=1.8, label="rational-PCE error")
    ax.set_xlabel(r"$\xi$"); ax.set_ylabel("abs error")
    ax.set_title(r"Rational PCE ($m_p$=3,$m_q$=4) >> high-degree polynomial")
    ax.legend(loc="upper center")
    fig.suptitle("The paper's surrogate R(X)=P(X)/Q(X): Hermite-PCE numerator / "
                 "denominator, fit by Eqs. (6)-(9)", fontweight="bold")
    C.save(fig, "p1_fig4_rational_in_parameter.png", rect=(0, 0.025, 1, 0.92))


# ===========================================================================
# FIG 5 -- approximation quality in BOTH representations (complex + mag/phase)
# ===========================================================================
def fig5_quality_both_reps():
    xi_test = np.linspace(-3, 3, 400)
    H_test = H_of_xi(xi_test)
    N = 60
    xi_ed = np.sort(rng.standard_normal(N) * 1.1)
    M = H_of_xi(xi_ed)
    mp, mq = 3, 4
    p, q = C.fit_rational_pce(C.hermite_norm(xi_ed, mp),
                              C.hermite_norm(xi_ed, mq), M)
    H_rat = C.eval_rational(C.hermite_norm(xi_test, mp),
                            C.hermite_norm(xi_test, mq), p, q)

    fig, axes = plt.subplots(1, 3, figsize=(13.2, 4.3))
    ax = axes[0]
    ax.plot(H_test.real, H_test.imag, color=C.C_TRUTH, lw=2.4, label="true")
    ax.plot(H_rat.real, H_rat.imag, color=C.C_SURR, lw=1.6, ls=":", label="surrogate")
    ax.scatter(M.real, M.imag, c="k", s=10, alpha=0.4, label="design pts")
    ax.axhline(0, color="k", lw=0.5); ax.axvline(0, color="k", lw=0.5)
    ax.set_aspect("equal", adjustable="datalim")
    ax.set_xlabel("Re{H}"); ax.set_ylabel("Im{H}")
    ax.set_title("(a) complex plane (a+bi)")
    ax.legend(loc="best")

    ax = axes[1]
    ax.plot(xi_test, np.abs(H_test), color=C.C_TRUTH, lw=2.4)
    ax.plot(xi_test, np.abs(H_rat), color=C.C_SURR, lw=1.6, ls=":")
    ax.set_yscale("log"); ax.set_xlabel(r"$\xi$"); ax.set_ylabel("|H|")
    ax.set_title("(b) magnitude")

    ax = axes[2]
    ax.plot(xi_test, np.unwrap(np.angle(H_test)), color=C.C_TRUTH, lw=2.4)
    ax.plot(xi_test, np.unwrap(np.angle(H_rat)), color=C.C_SURR, lw=1.6, ls=":")
    ax.set_xlabel(r"$\xi$"); ax.set_ylabel("phase [rad]")
    ax.set_title("(c) phase")
    fig.suptitle("Same surrogate, two equivalent views: real/imag  and  magnitude/phase",
                 fontweight="bold")
    C.save(fig, "p1_fig5_quality_both_reps.png", rect=(0, 0.025, 1, 0.92))


# ===========================================================================
# GIF 1 -- frequency sweep: dot traces Nyquist while markers track Bode
# ===========================================================================
def gif1_nyquist_sweep():
    f = FGRID
    H = H_true(f)
    fig = plt.figure(figsize=(11.5, 4.3))
    gs = fig.add_gridspec(2, 2, width_ratios=[1.1, 1])
    axN = fig.add_subplot(gs[:, 0])
    axM = fig.add_subplot(gs[0, 1])
    axP = fig.add_subplot(gs[1, 1])

    axN.plot(H.real, H.imag, color="0.8", lw=1)
    axN.axhline(0, color="k", lw=0.5); axN.axvline(0, color="k", lw=0.5)
    axN.set_aspect("equal", adjustable="datalim")
    axN.set_xlabel("Re{H}"); axN.set_ylabel("Im{H}"); axN.set_title("Nyquist")
    (trailN,) = axN.plot([], [], color=C.ACCENT, lw=2)
    (dotN,) = axN.plot([], [], "o", color=C.C_ERR, ms=9)

    axM.semilogy(f, np.abs(H), color="0.8", lw=1)
    axM.set_ylabel("|H|"); axM.set_title("magnitude")
    (dotM,) = axM.plot([], [], "o", color=C.C_ERR, ms=7)
    axP.plot(f, np.unwrap(np.angle(H)), color="0.8", lw=1)
    axP.set_xlabel("f [Hz]"); axP.set_ylabel("phase")
    (dotP,) = axP.plot([], [], "o", color=C.C_ERR, ms=7)
    phase_un = np.unwrap(np.angle(H))
    fig.suptitle("Frequency sweep: one complex number per frequency",
                 fontweight="bold")
    fig.tight_layout(rect=(0, 0.03, 1, 0.94))
    C.stamp(fig)

    idx = np.linspace(0, len(f) - 1, 90).astype(int)

    def update(j):
        i = idx[j]
        trailN.set_data(H.real[:i + 1], H.imag[:i + 1])
        dotN.set_data([H.real[i]], [H.imag[i]])
        dotM.set_data([f[i]], [np.abs(H)[i]])
        dotP.set_data([f[i]], [phase_un[i]])
        return trailN, dotN, dotM, dotP

    anim = FuncAnimation(fig, update, frames=len(idx), blit=True)
    out = C.gif_path("p1_gif1_nyquist_sweep.gif")
    anim.save(out, writer=PillowWriter(fps=18))
    plt.close(fig)
    print("  wrote", out.relative_to(C.BASE))


# ===========================================================================
# GIF 2 -- rational order convergence vs polynomial (fit of frequency)
# ===========================================================================
def gif2_order_convergence():
    f = FGRID
    H = H_true(f)
    orders = list(range(2, 19))
    fig, ax = plt.subplots(figsize=(9.5, 4.6))
    ax.semilogy(f, np.abs(H), color=C.C_TRUTH, lw=2.4, label="true FRF")
    (lp,) = ax.semilogy(f, np.abs(H), color=C.C_POLY, lw=1.7, ls="--",
                        label="polynomial deg d")
    (lr,) = ax.semilogy(f, np.abs(H), color=C.C_SURR, lw=1.7, ls=":",
                        label="rational (d, d+2)")
    ax.set_ylim(np.abs(H).min() * 0.3, np.abs(H).max() * 3)
    ax.set_xlabel("f [Hz]"); ax.set_ylabel("|H|")
    ax.legend(loc="lower right")
    ttl = ax.set_title("")
    fig.tight_layout(rect=(0, 0.03, 1, 1)); C.stamp(fig)

    def update(j):
        d = orders[j]
        Psi = _design_freq(f, d)
        Hp = Psi @ C.fit_poly_pce(Psi, H)
        PsiP = _design_freq(f, d); PsiQ = _design_freq(f, d + 2)
        p, q = C.fit_rational_pce(PsiP, PsiQ, H)
        Hr = C.eval_rational(PsiP, PsiQ, p, q)
        lp.set_ydata(np.abs(Hp)); lr.set_ydata(np.abs(Hr))
        ttl.set_text(f"Increasing order  d = {d}: rational locks on, "
                     f"polynomial still ringing")
        return lp, lr, ttl

    anim = FuncAnimation(fig, update, frames=len(orders), blit=False)
    out = C.gif_path("p1_gif2_order_convergence.gif")
    anim.save(out, writer=PillowWriter(fps=3))
    plt.close(fig)
    print("  wrote", out.relative_to(C.BASE))


# ===========================================================================
# GIF 3 -- parameter sweep: resonance peak moves, surrogate tracks complex value
# ===========================================================================
def gif3_param_sweep():
    # build surrogate over xi once
    N = 60
    xi_ed = np.sort(rng.standard_normal(N) * 1.1)
    M = H_of_xi(xi_ed)
    mp, mq = 3, 4
    p, q = C.fit_rational_pce(C.hermite_norm(xi_ed, mp),
                              C.hermite_norm(xi_ed, mq), M)

    def surr(xi):
        return C.eval_rational(C.hermite_norm(np.atleast_1d(xi), mp),
                               C.hermite_norm(np.atleast_1d(xi), mq), p, q)[0]

    f = np.linspace(60, 130, 300)
    xis = np.linspace(-2.6, 2.6, 70)

    fig = plt.figure(figsize=(11.5, 4.4))
    gs = fig.add_gridspec(1, 2, width_ratios=[1.25, 1])
    axF = fig.add_subplot(gs[0]); axC = fig.add_subplot(gs[1])
    axF.axvline(F0_DEMO, color="0.6", ls="--", lw=1)
    (lF,) = axF.semilogy([], [], color=C.C_TRUTH, lw=2)
    (dF,) = axF.semilogy([], [], "o", color=C.C_ERR, ms=8)
    axF.set_xlim(f.min(), f.max()); axF.set_ylim(2e-7, 5e-4)
    axF.set_xlabel("f [Hz]"); axF.set_ylabel("|H(f; k)|")
    axF.set_title("FRF with the resonance sweeping through f0=95 Hz")
    # full true locus at f0 across xi
    Hloc = H_of_xi(xis)
    axC.plot(Hloc.real, Hloc.imag, color="0.8", lw=1)
    axC.axhline(0, color="k", lw=0.5); axC.axvline(0, color="k", lw=0.5)
    (dCt,) = axC.plot([], [], "o", color=C.C_TRUTH, ms=9, label="true H(f0;k)")
    (dCs,) = axC.plot([], [], "x", color=C.C_SURR, ms=11, mew=2.5,
                      label="rational surrogate")
    axC.set_aspect("equal", adjustable="datalim")
    axC.set_xlabel("Re{H}"); axC.set_ylabel("Im{H}")
    axC.set_title("Value at f0 in complex plane")
    axC.legend(loc="upper left")
    fig.suptitle("Surrogate tracks the complex FRF value as the parameter k changes",
                 fontweight="bold")
    fig.tight_layout(rect=(0, 0.03, 1, 0.93)); C.stamp(fig)

    def update(j):
        xi = xis[j]
        Hf = C.hysteretic_frf_vs_param  # not used; use modal in freq with shifted k
        k = k_of_xi(xi)
        # FRF vs frequency at this k (hysteretic)
        w = 2 * np.pi * f
        wr0 = 2 * np.pi * np.asarray(FR0)
        den = (k * wr0[None, :] ** 2 * (1 + 1j * np.asarray(ETA)[None, :])
               - w[:, None] ** 2)
        Hk = (np.asarray(AMP2)[None, :] / den).sum(1)
        lF.set_data(f, np.abs(Hk))
        H0 = H_of_xi(xi)[0]
        dF.set_data([F0_DEMO], [np.abs(H0)])
        dCt.set_data([H0.real], [H0.imag])
        Hs = surr(xi)
        dCs.set_data([Hs.real], [Hs.imag])
        return lF, dF, dCt, dCs

    anim = FuncAnimation(fig, update, frames=len(xis), blit=True)
    out = C.gif_path("p1_gif3_param_sweep.gif")
    anim.save(out, writer=PillowWriter(fps=16))
    plt.close(fig)
    print("  wrote", out.relative_to(C.BASE))


if __name__ == "__main__":
    print("[part1] figures")
    fig1_complex_nature()
    fig2_one_point()
    fig3_poly_vs_rational_freq()
    fig4_rational_in_parameter()
    fig5_quality_both_reps()
    print("[part1] gifs")
    gif1_nyquist_sweep()
    gif2_order_convergence()
    gif3_param_sweep()
    print("[part1] done")
