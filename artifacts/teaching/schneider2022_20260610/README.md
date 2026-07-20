# Teaching deck — Schneider et al. (2022), rational-surrogate Bayesian FRF updating

A self-contained, visual teaching example of three core ideas from:

> F. Schneider, I. Papaioannou, D. Straub, C. Winter, G. Müller,
> "Bayesian parameter updating in linear structural dynamics with frequency
> transformed data using rational surrogate models," *Mechanical Systems and
> Signal Processing* **166**:108407 (2022).

**Deliverable:** [`schneider2022_teaching.pptx`](schneider2022_teaching.pptx) (26 slides)
built from the figures in [`figures/`](figures/) and animations in [`gifs/`](gifs/).

> ⚠️ **Honesty label.** Every figure/animation here is a small **synthetic /
> conceptual** teaching model produced by the scripts in [`scripts/`](scripts/).
> They are **NOT** a reproduction of the paper's cross-laminated-timber (CLT)
> numerical results. Where public values from the paper are reused (shell-model
> eigenfrequencies from Fig. C.10; the `mp=3, mq=4` surrogate orders; the learned
> split factor `r≈0.82`), that is stated on the figure.

## Reproduce

```bash
bash run_all.sh
```

Requires `python3` with `numpy`, `scipy`, `matplotlib`, `pillow`, `python-pptx`.
Re-runs all three generators and reassembles the deck (~1–2 min).

## What's covered

### Part 1 — A PCE-rational surrogate of an FRF  (`part1_rational_surrogate.py`)
- An FRF is **complex-valued**: real+imaginary ↔ magnitude+phase (Nyquist/Bode).
- An FRF is naturally a **ratio of polynomials** → it has poles; a single
  polynomial cannot fit resonances, a rational can (fit *of frequency*).
- The paper's surrogate `R(X)=P(X)/Q(X)`: Hermite-PCE numerator/denominator,
  fit by the **linearized regression of Eqs. (6)–(9)** (implemented faithfully in
  `common.fit_rational_pce`), demonstrated *over a parameter* with a pole crossing.
- Approximation quality shown in both the complex plane and magnitude/phase.

### Part 2 — The likelihood formulation  (`part2_likelihood.py`)
- **Multiplicative complex error** `Y_obs = Y_model ∘ ε`; `log ε = w + iθ` with
  `w=log|ε|` normal (|ε| lognormal) and phase `θ` normal (Eqs. 13–15).
- **Improper (non-circular) complex normal**: the joint PDF of real/imag error
  (Eq. A.9) morphs circle → arc → radial smear → **kidney** (reproduces Fig. 1's
  structure).
- The **likelihood of one observation** (Eqs. 17–18): the model-vs-data mismatch
  split into a log-magnitude error `w` and a phase error `θ`, each Gaussian-scored.
- **Space + frequency correlation** (Eqs. 19–25): additive exponential kernels,
  split factor `r`, Kronecker assembly — and **why it matters** (don't over-count
  dense data → honest posterior width; the paper's damping-bias finding).

### Part 3 — BUS + Subset Simulation  (`part3_bus_sus.py`)
- **BUS** (Eq. 26): augment `x` with `p~U(0,1)`, accept if `p ≤ c·L(x)`; the
  accepted region projected onto `x` is the posterior.
- **Subset Simulation** (Eq. 27): nested levels at conditional probability
  `p0=0.2` with MCMC inside each level reach the rare accepted region.
- A genuine (small) SuS is implemented and **validated against a known analytic
  Gaussian posterior** (mean/sd match to ~1–3 %).
- **Method label (per project rules):** this is a *teaching prototype* sampler
  using modified-Metropolis MCMC — **not NUTS/HMC** and **not** the paper's
  adaptive aBUS-SuS (Betz et al. 2018). For intuition only.

## Files

| Path | What |
|---|---|
| `scripts/common.py` | style, physics helpers, faithful Eqs. (6)–(9) rational fit, Hermite-PCE |
| `scripts/part1_rational_surrogate.py` | 5 figures + 3 GIFs |
| `scripts/part2_likelihood.py` | 7 figures + 3 GIFs |
| `scripts/part3_bus_sus.py` | 3 figures + 2 GIFs (incl. real SuS) |
| `scripts/build_pptx.py` | assembles the 26-slide deck |
| `figures/` | 15 PNGs | 
| `gifs/` | 8 animated GIFs (play in PowerPoint slideshow mode) |

## Notes
- Animated GIFs play in PowerPoint slideshow mode (2016+/365). Static viewers
  (e.g. some LibreOffice versions) show the first frame; the standalone GIFs in
  `gifs/` always animate in a browser/image viewer.
- The space+frequency correlation matrix is assembled directly from Eq. (19) for
  clarity (`r·R_ff⊗J + (1−r)·J⊗R_zz`, a valid PSD covariance matching the
  Eq. 22–23 limits); the paper writes it via Kronecker products (Eq. 25) for
  efficient inversion.
