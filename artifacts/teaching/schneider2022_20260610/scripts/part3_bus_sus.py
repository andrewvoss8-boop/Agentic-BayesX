"""
PART 3 -- BUS with Subset Simulation (the paper's posterior sampler).

Teaching arc:
  (1) BUS = "Bayesian Updating with Structural reliability methods" (Eq. 26):
      augment the parameters x with a uniform p~U(0,1); define the limit state
      h(x,p) = p - c L(x).  The ACCEPTED region {h<=0} i.e. {p <= c L(x)},
      projected onto x, IS the posterior.  (c = 1/max L so that cL<=1.)
  (2) Naive Monte Carlo accepts a tiny fraction when the likelihood is peaky.
  (3) Subset Simulation (Eq. 27): reach the rare accepted region through a
      chain of nested levels, each of conditional probability p0=0.2, using
      MCMC inside each level.  Final-level samples = posterior.

NOTE ON METHOD LABELLING (per project rules): this is a *teaching prototype*
SuS with modified-Metropolis MCMC.  It is NOT NUTS/HMC and NOT the paper's
adaptive aBUS-SuS (Betz et al. 2018); it is here only to make the BUS-SuS
mechanics visible.  Validated against the analytic Gaussian posterior below.
"""
from __future__ import annotations
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation, PillowWriter
from scipy.stats import norm

import common as C

rng = np.random.default_rng(3)

# ---- toy Bayesian problem with a KNOWN analytic posterior ------------------
# prior: x = (x1, x2) ~ N(0, I)   (standard normal, as in BUS practice)
# observation: g(x) = x1, measured d with noise sd SIGMA  -> peaky, tail-seeking
D_OBS = 3.0
SIGMA = 0.30
C_BUS = 1.0          # = 1/max L  (unnormalized L peaks at 1)

# analytic posterior on x1: N(mu_post, sd_post); x2 stays N(0,1)
MU_POST = D_OBS / (SIGMA ** 2 + 1)
SD_POST = 1.0 / np.sqrt(1 + 1 / SIGMA ** 2)


def like(x1):
    """Unnormalized likelihood, peak = 1 at x1 = D_OBS."""
    return np.exp(-0.5 * ((x1 - D_OBS) / SIGMA) ** 2)


def hfun(U):
    """Limit state h = p - c L(x), with p = Phi(u_p).  U is (...,3)=[x1,x2,up]."""
    x1 = U[..., 0]
    up = U[..., 2]
    p = norm.cdf(up)
    return p - C_BUS * like(x1)


# ===========================================================================
# A genuine (small) Subset Simulation in standard-normal space
# ===========================================================================
def subset_simulation(N=2000, p0=0.2, sig_prop=0.8, max_levels=8, seed=3):
    r = np.random.default_rng(seed)
    U = r.standard_normal((N, 3))
    Nc = int(N * p0)
    Ls = N // Nc
    levels = []        # list of (samples, threshold_b)
    for _ in range(max_levels):
        h = hfun(U)
        order = np.argsort(h)
        b = h[order[Nc - 1]]           # p0-quantile of h
        reached = b <= 0.0
        b_eff = 0.0 if reached else b
        levels.append((U.copy(), b_eff))
        if reached:
            break
        seeds = U[order[:Nc]]          # the p0 fraction with smallest h
        # grow each seed into a chain of length Ls inside {h <= b}
        chains = np.empty((Nc, Ls, 3))
        chains[:, 0] = seeds
        cur = seeds.copy()
        for t in range(1, Ls):
            cand = cur + sig_prop * r.standard_normal(cur.shape)
            # modified Metropolis: per-component accept w.r.t. standard normal
            ratio = np.exp(-0.5 * (cand ** 2 - cur ** 2))
            comp_acc = r.random(cur.shape) < np.minimum(1.0, ratio)
            cand = np.where(comp_acc, cand, cur)
            in_dom = hfun(cand) <= b
            cur = np.where(in_dom[:, None], cand, cur)
            chains[:, t] = cur
        U = chains.reshape(-1, 3)[:N]
    # posterior samples = final level with h <= 0
    Uf, bf = levels[-1]
    post = Uf[hfun(Uf) <= 0.0]
    pf = p0 ** (len(levels) - 1) * (np.mean(hfun(Uf) <= 0.0) / p0)
    return levels, post, pf


# ===========================================================================
# FIG 1 -- the BUS concept (augmented space + accepted region = posterior)
# ===========================================================================
def fig1_bus_concept():
    n = 60000
    x1 = rng.standard_normal(n)        # prior samples (1-D view; x2 marginal)
    p = rng.random(n)
    acc = p <= C_BUS * like(x1)
    grid = np.linspace(-2, 5, 500)

    fig = plt.figure(figsize=(8.6, 6.6))
    gs = fig.add_gridspec(2, 1, height_ratios=[2.1, 1.0], hspace=0.32)
    ax = fig.add_subplot(gs[0])
    ax.plot(x1[~acc][:8000], p[~acc][:8000], ".", color="0.78", ms=2,
            label="rejected")
    ax.plot(x1[acc], p[acc], ".", color=C.C_ACC, ms=3, label="accepted")
    ax.plot(grid, C_BUS * like(grid), color=C.C_ERR, lw=2.5,
            label=r"$c\,L(x)$")
    ax.set_ylim(0, 1.02); ax.set_xlim(-2, 5)
    ax.set_xlabel(r"parameter $x_1$  (prior samples)")
    ax.set_ylabel(r"auxiliary $p\sim U(0,1)$")
    ax.set_title("BUS augmented space: accept if  p <= c L(x)  (Eq. 26)\n"
                 f"only {100*acc.mean():.2f}% accepted -> naive MC is wasteful")
    ax.legend(loc="upper left")

    ax2 = fig.add_subplot(gs[1])
    ax2.hist(x1[acc], bins=40, density=True, color=C.C_ACC, alpha=0.8,
             label="accepted x (= posterior)")
    ax2.plot(grid, norm.pdf(grid, MU_POST, SD_POST), color=C.C_TRUTH, lw=2.5,
             label="analytic posterior")
    ax2.plot(grid, norm.pdf(grid, 0, 1), color=C.C_PRIOR, lw=1.8, ls="--",
             label="prior")
    ax2.set_xlim(-2, 5); ax2.set_xlabel(r"$x_1$"); ax2.set_ylabel("density")
    ax2.set_title("Projection onto x of the accepted samples = the posterior")
    ax2.legend(loc="upper left", fontsize=8)
    fig.suptitle("Bayesian updating recast as a reliability problem (BUS)",
                 fontweight="bold")
    C.save(fig, "p3_fig1_bus_concept.png", rect=(0, 0.02, 1, 0.95))


# ===========================================================================
# FIG 2 -- subset simulation levels
# ===========================================================================
def fig2_sus_levels():
    levels, post, pf = subset_simulation(N=2000, seed=5)
    nlev = len(levels)
    fig, axes = plt.subplots(1, nlev, figsize=(3.1 * nlev, 3.4), sharex=True,
                             sharey=True)
    if nlev == 1:
        axes = [axes]
    for k, (ax, (U, b)) in enumerate(zip(axes, levels)):
        h = hfun(U)
        ax.plot(U[:, 0], U[:, 1], ".", color="0.8", ms=2)
        sel = h <= b
        ax.plot(U[sel, 0], U[sel, 1], ".", color=C.C_ACC, ms=3)
        ax.axvline(D_OBS, color=C.C_ERR, ls=":", lw=1)
        ax.set_title(f"level {k}: "
                     + ("seeds (top 20%)" if b > 0 else "ACCEPTED (h<=0)")
                     + f"\nthreshold b={b:+.2f}")
        ax.set_xlabel(r"$x_1$")
        if k == 0:
            ax.set_ylabel(r"$x_2$")
    fig.suptitle("Subset Simulation: nested levels march the prior cloud into "
                 f"the posterior (p0=0.2, {nlev} levels, $\\hat P_{{acc}}$={pf:.1e})",
                 fontweight="bold")
    C.save(fig, "p3_fig2_sus_levels.png", rect=(0, 0.02, 1, 0.9))


# ===========================================================================
# FIG 3 -- recovered posterior validated against analytic
# ===========================================================================
def fig3_posterior_validation():
    levels, post, pf = subset_simulation(N=4000, seed=8)
    fig, axes = plt.subplots(1, 2, figsize=(11.6, 4.6))
    ax = axes[0]
    ax.plot(post[:, 0], post[:, 1], ".", color=C.C_ACC, ms=3, alpha=0.5,
            label="SuS posterior samples")
    th = np.linspace(0, 2 * np.pi, 200)
    for kσ in (1, 2):
        ax.plot(MU_POST + kσ * SD_POST * np.cos(th), 0 + kσ * 1.0 * np.sin(th),
                color=C.C_TRUTH, lw=2, ls="--")
    ax.plot(MU_POST, 0, "X", color=C.C_TRUTH, ms=12, label="analytic mean")
    ax.set_xlabel(r"$x_1$"); ax.set_ylabel(r"$x_2$")
    ax.set_title("Posterior cloud vs analytic 1$\\sigma$,2$\\sigma$ ellipses")
    ax.legend(loc="upper left")

    ax = axes[1]
    grid = np.linspace(1.5, 4, 400)
    ax.hist(post[:, 0], bins=45, density=True, color=C.C_ACC, alpha=0.8,
            label="SuS samples")
    ax.plot(grid, norm.pdf(grid, MU_POST, SD_POST), color=C.C_TRUTH, lw=2.5,
            label="analytic $N$")
    ax.axvline(D_OBS, color=C.C_ERR, ls=":", label="observation d")
    ax.set_xlabel(r"$x_1$"); ax.set_ylabel("density")
    ax.set_title(f"Marginal: SuS mean={post[:,0].mean():.3f} "
                 f"(analytic {MU_POST:.3f}),\n"
                 f"sd={post[:,0].std():.3f} (analytic {SD_POST:.3f})")
    ax.legend()
    fig.suptitle("BUS-SuS recovers the posterior (teaching prototype, "
                 "validated vs analytic)", fontweight="bold")
    C.save(fig, "p3_fig3_posterior_validation.png", rect=(0, 0.02, 1, 0.92))


# ===========================================================================
# GIF 1 -- BUS rejection "rain" builds the posterior
# ===========================================================================
def gif1_bus_rain():
    batches = 45
    per = 1500
    grid = np.linspace(-2, 5, 400)
    acc_x = []
    fig = plt.figure(figsize=(8.4, 6.2))
    gs = fig.add_gridspec(2, 1, height_ratios=[2.1, 1.0], hspace=0.33)
    axT = fig.add_subplot(gs[0]); axB = fig.add_subplot(gs[1])
    C.stamp(fig)

    def update(j):
        axT.clear(); axB.clear()
        x1 = rng.standard_normal(per); p = rng.random(per)
        a = p <= C_BUS * like(x1)
        acc_x.extend(list(x1[a]))
        axT.plot(x1[~a], p[~a], ".", color="0.82", ms=3)
        axT.plot(x1[a], p[a], ".", color=C.C_ACC, ms=5)
        axT.plot(grid, C_BUS * like(grid), color=C.C_ERR, lw=2.5)
        axT.set_xlim(-2, 5); axT.set_ylim(0, 1.02)
        axT.set_ylabel(r"$p\sim U(0,1)$")
        axT.set_title(f"BUS: raining (x,p); keep p<=cL(x)   "
                      f"[{len(acc_x)} kept of {(j+1)*per}]")
        if len(acc_x) > 5:
            axB.hist(acc_x, bins=40, density=True, color=C.C_ACC, alpha=0.8)
        axB.plot(grid, norm.pdf(grid, MU_POST, SD_POST), color=C.C_TRUTH, lw=2.5)
        axB.set_xlim(-2, 5); axB.set_xlabel(r"$x_1$"); axB.set_ylabel("density")
        axB.set_title("accepted-x histogram -> posterior (navy=analytic)")

    anim = FuncAnimation(fig, update, frames=batches, blit=False)
    out = C.gif_path("p3_gif1_bus_rain.gif")
    anim.save(out, writer=PillowWriter(fps=10)); plt.close(fig)
    print("  wrote", out.relative_to(C.BASE))


# ===========================================================================
# GIF 2 -- subset simulation levels contracting prior -> posterior
# ===========================================================================
def gif2_sus_levels():
    levels, post, pf = subset_simulation(N=2500, seed=5)
    # build a frame list: for each level show full cloud then highlight seeds
    frames = []
    for k, (U, b) in enumerate(levels):
        frames.append((k, U, b, False))
        frames.append((k, U, b, True))
    fig, ax = plt.subplots(figsize=(6.4, 5.6)); C.stamp(fig)

    def update(j):
        ax.clear()
        k, U, b, hi = frames[j]
        h = hfun(U)
        ax.plot(U[:, 0], U[:, 1], ".", color="0.82", ms=3)
        if hi:
            sel = h <= b
            ax.plot(U[sel, 0], U[sel, 1], ".", color=C.C_ACC, ms=4)
        ax.axvline(D_OBS, color=C.C_ERR, ls=":", lw=1.2)
        ax.plot(MU_POST, 0, "X", color=C.C_TRUTH, ms=12)
        ax.set_xlim(-3.5, 4.5); ax.set_ylim(-3.8, 3.8)
        ax.set_xlabel(r"$x_1$"); ax.set_ylabel(r"$x_2$")
        tag = ("highlight top-20% seeds (b={:.2f})".format(b) if hi
               else "level {} population".format(k))
        if b <= 0 and hi:
            tag = "FINAL: accepted = posterior"
        ax.set_title(f"Subset Simulation - level {k}\n{tag}")

    anim = FuncAnimation(fig, update, frames=len(frames), blit=False)
    out = C.gif_path("p3_gif2_sus_levels.gif")
    anim.save(out, writer=PillowWriter(fps=2.5)); plt.close(fig)
    print("  wrote", out.relative_to(C.BASE))


if __name__ == "__main__":
    print("[part3] figures")
    fig1_bus_concept()
    fig2_sus_levels()
    fig3_posterior_validation()
    print("[part3] gifs")
    gif1_bus_rain()
    gif2_sus_levels()
    print("[part3] done")
