# Literature comparison — Ching & Chen (2007) TMCMC 2DOF identifiability vs our 2DOF/MDOF StatFEM findings

**Reviewer role:** literature-comparison reviewer (Agentic BayesX, Opus 4.8). I compared our blind round-3
StatFEM model-updating findings and our fresh-2DOF StatFEM/FBS results against Ching, J., and Chen, Y.-C.
(2007), "Transitional Markov Chain Monte Carlo Method for Bayesian Model Updating, Model Class Selection,
and Model Averaging," *J. Eng. Mech.* 133(7):816–832.

**Honesty rules applied.** Every paper claim below is cited to a section/figure/equation/page that I read
from the actual PDF in repo root (page numbers are the journal page printed on each page; PDF page = journal
page − 815). I **read the figures visually** (extracted Figs 3–5 as images) rather than relying on memory. I
separate what the paper SUPPORTS from what is OUR extension, and I mark `[SPECULATIVE]` / `[TO-VERIFY]`. I
wrote ONLY to this file.

> **One correction to the task framing up front (honesty).** The task brief refers to "Fig. 1 — (a)
> unidentifiable, (b) locally identifiable, (c) globally identifiable." That is **not** what Fig. 1 of this
> paper is. In the actual PDF, **Fig. 1 (p. 821) is the structural diagram** — captioned "2DOF and 4DOF
> planar shear building in Example 1 and Example 3." The identifiability *taxonomy* is conveyed through the
> three **Cases I/II/III** of Example 1, whose (k₁,k₂) sample clouds are **Figs. 3, 4, and 5 (pp. 822–824)**.
> Moreover, the exact words "globally identifiable" and "locally identifiable" **do not appear anywhere in
> this PDF** (text search: 0 occurrences each; "unidentif" appears 2×, "flat manifold" 1× in the abstract,
> "almost unidentifiable" 1× for Case I, "bimodal" 4×, "single sharp peak" 1× for Case III). The three-term
> taxonomy is from the **cited** Katafygiotis & Beck (1998), "Updating models and their uncertainties.
> Part II: Model identifiability," *J. Eng. Mech.* 124(4):463–467 — `[TO-VERIFY]`: that source is not in the
> repo, so I attribute the precise naming to it by citation only. I therefore use the paper's own words —
> *flat / almost-unidentifiable* (Case I), *bimodal / two peaks* (Case II), *single sharp peak* (Case III) —
> and map them to the familiar taxonomy where it helps, flagged as such.

> **Second correction — dimensionality (do not over-map our Stage 3 onto the paper's 2DOF).** The paper's
> Example 1 (and its (k₁,k₂) sample plots, Figs. 3–5) is a genuine **2-degree-of-freedom, 2-parameter**
> problem. **Our Stage 3 is NOT 2DOF.** It is an **MDOF** problem: a **6-DOF diagonal complex interface
> apparent mass** with **six per-strut stiffnesses k₁…k₆** on a hexapod, plus an axial-dome resonator, a
> per-strut discrepancy field, build-to-build hierarchy, and noise — a high-dimensional parameter space
> (`runs/round3/opus48/report/packet_stage3.md` §1). So when I map a Stage-3 ridge onto Ching & Chen's
> (k₁,k₂) plane, that plane is a **conceptual 2-parameter projection** (e.g. k_pop vs the per-strut
> discrepancy magnitude, or σ_d vs σ_e), **not** a literal redraw of their Fig. 3. The **only genuinely
> 2DOF↔2DOF, apples-to-apples** comparison we have lives in **`artifacts/reports/`** — the fresh 2DOF
> StatFEM/FBS run (`fresh_2dof_statfem_fbs_20260601`, also reused by `multi_agent_first_loop_20260602`), a
> true 2-mode (dome/tray) model. That is the one row in the table below that sits in the same dimensionality
> as the paper; the Stage-0/1 and Stage-3 rows are MDOF analogs of the *geometry*, not the *dimensionality*.

---

## (a) What the paper's 2DOF identifiability result actually says (cited)

**The model (Example 1, p. 821).** A 2DOF linear shear building (Fig. 1a). Actual masses m₁=m₂=1, actual
stiffnesses k₁=k₂=1,000, modal damping ζ₁=ζ₂=3%. Masses are assumed **known**; the goal is to sample
f(θ|M,D), the posterior of the **uncertain stiffnesses, dampings, and the noise variance**, given measured
**acceleration time histories** (sampling interval 0.02 s; roof/2nd-floor channels corrupted by white
Gaussian noise of true variance 0.2, itself treated as uncertain). Priors are uniform: k∈[0,3000],
ζ∈[0.01,0.05], noise variance∈[0,1] (p. 821).

**The likelihood uses the whole measured acceleration record** (a time-domain Gaussian-noise likelihood),
*not* extracted modal peaks/features. There is **no Kennedy–O'Hagan / StatFEM model-discrepancy term**, no
hierarchy, no FRF, no FBS QOI. This is a clean parameter-identifiability study.

**The three identifiability regimes (p. 821, results pp. 821–825):**

- **Case I — flat / "almost unidentifiable."** Only roof + base acceleration, short record (1 s),
  **narrow-band** base excitation so **only the first mode is excited**. "Since only the first mode is
  excited, the posterior PDF is relatively flat (i.e., almost unidentifiable)" (p. 821). I inspected
  **Fig. 3 (p. 822)**: at the final stage the TMCMC (k₁,k₂) samples trace a **curved, hyperbolic L-shaped
  ridge** sweeping from low-k₁/high-k₂ down to high-k₁/low-k₂ — a one-dimensional flat manifold of near-equal
  posterior density. The competing AMH sampler instead **collapses onto a few isolated dots** and fails to
  reveal the ridge.
- **Case II — bimodal / "two peaks."** Roof + base, 1 s, **wide-band** base so **both modes excited**.
  "the posterior PDF contains two peaks … as correctly indicated by the TMCMC samples" (p. 825). **Fig. 4
  (p. 823)**: at the final stage the TMCMC samples form **two isolated clusters** (near (k₁,k₂)≈(1000,1000)
  and ≈(1900,500)); AMH collapses to a single cluster and **misses the second mode**.
- **Case III — single sharp peak (globally identifiable, in the taxonomy sense).** Roof + base + 2nd-floor
  acceleration, longer record (10 s). "the posterior PDF contains one sharp peak located at [1,000 1,000]"
  (p. 825). **Fig. 5 (p. 824)**: TMCMC converges to a **single tight point** at the true (1000,1000). Note
  the paper's own caveat — **AMH "converge[s] to a location slightly different from [1,000 1,000]"** (p. 825),
  i.e. a sharp peak can still sit at a (slightly) wrong place if the sampler/model is imperfect.

A second, decisive visual detail I verified: **in the early tempering stages even Case III shows a curved
ridge** (Fig. 5, stage 4) that only **collapses to a point as the temper exponent rises toward the full
posterior**. Identifiability here is produced by *observability* — more measured DOFs (2nd floor), longer
record, and wider-band excitation move the same structure from flat (I) → bimodal (II) → sharp peak (III).

**Why TMCMC (the paper's thesis).** Abstract (p. 816): TMCMC can "draw samples from some difficult PDFs
(e.g., multimodal PDFs, very peaked PDFs, and PDFs with flat manifold)." It builds a **sequence of
intermediate PDFs that temper from prior to posterior** — Eq. (11), p. 818:
`f_j(θ) ∝ f(θ|M)·f(D|M,θ)^{p_j}`, with `0 = p_0 < p_1 < … < p_m = 1` (p_0 = prior, p_m = posterior) — using
plausibility-weight resampling between stages (Eqs. (12)–(16), pp. 818–819). The motivation (Introduction,
pp. 816–817): single-chain MH "may be not efficient when the uncertain variables are highly correlated
conditioning on the data and when the posterior PDF is very peaked," and "most MCMC techniques are not
applicable when the PDF is multimodal" — a multimodal target gives "a nonergodic Markov chain (i.e., the
Markov chain samples may be trapped in one of the peaks and never propagate to the others)" (p. 817).
Example 2 (mixture of two Gaussians, pp. 825) demonstrates this directly: plain MH "samples are trapped in
one peak" when the peaks are isolated, while TMCMC samples both.

**Evidence / model-class machinery.** TMCMC produces the **evidence f(D|M) as a by-product**: the product of
the per-stage normalizing constants S = ∏ Sⱼ is an asymptotically unbiased estimator of f(D|M) (p. 819,
algorithm step 3; Eq. (15)). Evidence is the engine of **Bayesian model class selection**, Eq. (2) (p. 817):
`P[M(i)|D] ∝ f[D|M(i)]·P[M(i)]`. Example 1 reports `log[f(D|M)]` per case (Table 1, p. 825); Example 3
(4DOF, Table 5, p. 831) uses per-model-class `log[f(D|M)]` to rank competing model classes.

---

## (b) Mapping our cases onto the paper's taxonomy (with evidence)

The paper's taxonomy is about **posterior geometry** (flat manifold / multiple discrete modes / single
peak). I classify each of our cases by its *geometry*, with our recomputed diagnostics as evidence. **Two
caveats.** (1) *Axis:* the paper's ridge lives in the **physical 2-parameter (k₁,k₂)** plane; our ridges
live in **parameter ↔ discrepancy / noise-scale** spaces. (2) *Dimensionality:* only the **fresh-2DOF** row
is a true 2DOF↔2DOF match; **Stage 0/1 and Stage 3 are MDOF** (6-DOF apparent mass, 6 per-strut k's +
discrepancy field + hierarchy), so their "(k₁,k₂)-plane" entry is a **2-parameter projection of a
high-dimensional posterior**, not a literal copy of Fig. 3. The *geometry* (a flat ridge a single chain
cannot traverse) transfers; the *axes*, the *cause*, and the *dimensionality* differ — see (e). The "DOF"
column below makes this explicit.

| Our case | DOF / param-dim (vs paper's 2DOF, 2-param) | Paper taxonomy (this PDF's words) | Geometry match to | Evidence (our artifacts) |
|---|---|---|---|---|
| **Frequency-only discrepancy, Stage 0/1** (blind_round3_review_20260604) | **MDOF** (6-DOF apparent mass; k_strut + per-DOF discrepancy + hierarchy + σ's) — *analog, not 2DOF* | **Flat manifold + bimodal** (hybrid of Case I & II) | Fig. 3 ridge **and** Fig. 4 two-peaks | rank-split R-hat **2.41** (z_b), bulk ESS ≈ **5**, 0 divergences = non-ergodic/multimodal (not under-warming). The **σ_d↔σ_e ridge** is real and only **masked by capping σ_d=0.3**; the *flexible* (learn σ_d) variant re-runs σ_d→~2.7. A minimal variant shows a **bimodal k_strut** ("stiff struts push modes out of band → discrepancy explains all"). So: a flat σ_d↔σ_e ridge co-existing with discrete modes. |
| **Structure/property per-strut discrepancy, Stage 3 (with-d)** (blind_round3_stage3_review_20260605) | **MDOF** (6-DOF; **k₁…k₆ per-strut** + 6-d discrepancy field + f_dome + per-build z_b + σ_d/σ_build/σ_e) — *high-dim, NOT the paper's 2DOF* | **Flat / almost-unidentifiable** (Case I analog) | Fig. 3 curved ridge, **projected** to (k_pop, σ_d) | worst R-hat **2.85**, min bulk ESS **4.7**, 0 div = flat manifold, no between-chain mixing. σ_d runs to **1.33** (≫0.20 prior); k_pop **de-identifies** to [6.4e6,16.8e6] (vs tight without-d). **n_eff(k_pop)=0.64 < 1** → posterior **wider than the prior** = a broad manifold, the quantitative signature of "flat/unidentifiable." Starve-data (1 build, 40–100 Hz) **still R-hat 2.85** → the ridge is **structural**, not data-deluge — exactly as Case I's flatness is a structural property of the data/model, not a sampler artifact. |
| **Per-strut ASYMMETRIC physics ALONE, Stage 3 (without-d)** | **MDOF** (6-DOF; k₁…k₆ + f_dome + hierarchy, no discrepancy) — *not 2DOF* | **Single sharp peak** (Case III / globally identifiable, *within its model class*) | Fig. 5 single point | worst R-hat **1.009**, min bulk ESS **487**, 0 div; k_pop tight [1.678e7,1.693e7]. **But, like Ching & Chen's Case-III caveat (AMH peak slightly off [1000,1000]), our sharp peak is biased:** netCG **3.10× high, 0% coverage**, f_dome ~20 Hz low. Globally identifiable ⇏ accurate; it is a *sharp peak inside an inadequate model class* (missing higher modes; σ_e ~150–190× true sensor noise). |
| **Fresh-2DOF: full-curve vs peak-feature likelihood** (`artifacts/reports/fresh_2dof_statfem_fbs_20260601`) | **TRUE 2DOF** (2-mode dome/tray) — *the one apples-to-apples dimensionality match to the paper* | full-curve → **sharp peak** (Case III-like); peak-only → **toward flat** (Case I-like) | Fig. 5 → Fig. 3 direction | Whole-FRF/PSD likelihood gives tight fn (dome 95% CI ≈ [93.20,93.68] Hz; tray ≈ [86.04,86.35] Hz). Switching to peaks/notches only **widens fn intervals 21.6× (dome), 27.3× (tray)**, and the dome truth falls **outside** the peak-only 95% CI. Discarding the whole curve for peaks reduces *observability* — the same lever (more vs less informative data) that moves Ching & Chen's structure from III → I. **Caveat:** this fresh-2DOF run used **random-walk Metropolis (legacy/prototype** per CLAUDE.md; acceptance ~0.49), **not NUTS** — widths reflect both the likelihood choice and a legacy sampler. |

**Does our ridge phenomenology match the paper's curved (k₁,k₂) manifold qualitatively? YES.** The Stage-3
with-d posterior is a flat ridge of near-equal density along which one quantity trades off against another
(k_pop ↔ per-strut discrepancy field; equivalently σ_d ↔ σ_e in Stage 0/1), with a single NUTS chain unable
to traverse it (R-hat 2.85, ESS 4.7, n_eff<1) — geometrically the same pathology as Fig. 3's L-shaped ridge
where a single AMH chain collapses to a few dots. The match is **qualitative (geometry + sampler failure
mode)**, not a structural equivalence (their ridge is k₁↔k₂; ours is parameter↔discrepancy — see (e)).

---

## (c) Sampler implication — does TMCMC help us, and where it cannot?

**The paper SUPPORTS trying TMCMC (or another tempering/SMC, and ABC by analogy) on our ridge/multimodal
cases.** Our NUTS failed *precisely* on the geometries TMCMC was built for: with-d R-hat 2.85, ESS 4.7,
n_eff(k_pop)<1, bimodal k_strut in Stage 0/1, and a tree-depth-capped, non-mixing single chain. Ching & Chen
show (Figs. 3–5; Example 2, p. 825) that single-chain samplers (MH, and even AMH) **collapse or get trapped**
on exactly flat-manifold and multimodal posteriors, whereas tempering from prior to posterior (Eq. 11)
**samples them correctly**. `[SPECULATIVE]` — the paper critiques **MH/IS**, predating routine HMC-in-SHM, so
its "single-chain Metropolis fails on multimodal/flat" argument extends to **single-chain HMC/NUTS** only by
analogy; HMC's gradient mixing does not cure non-ergodicity across isolated modes or geodesic-trapping on a
flat ridge. Our empirical NUTS failure (0 divergences, no mixing) is consistent with that extension, but the
paper does not state it.

**What TMCMC WOULD fix for us:**
1. **Mixing / honest credible intervals on the ridge.** Our NUTS cannot even *map* the with-d ridge (it
   hits the tree-depth cap every draw; grid-invariance was honestly labeled intractable). TMCMC would draw
   the full manifold the way Fig. 3-TMCMC does, instead of NUTS producing a non-converged, unreliable
   marginal. The reported marginals would become trustworthy *as a description of a (still wide) posterior*.
2. **A correctly marginalized QOI.** With an honestly sampled (wide) posterior, the propagated netCG
   uncertainty would be a faithful reflection of the non-identifiability, not an artifact of a stuck chain.
3. **Evidence f(D|M) for the with-d vs without-d comparison** (Eq. 15; Table 1/5) — see (d).

**What TMCMC would NOT fix — the central honest point:** *a better sampler reveals the ridge; it does not
remove it.* Our Stage-3 confounding is **structural non-identifiability**: the per-strut discrepancy
`k_j = k_pop·exp(d_j)` lives in the **same parameter space** as the per-strut stiffness, so k_pop and the
discrepancy field are confounded **by construction**. This is the analog of Ching & Chen's **Case I, which
stays a flat manifold no matter how well you sample it** — TMCMC samples the manifold honestly (Fig. 3) but
the structure is still unidentifiable; the data simply do not pin a unique point. Our **starve-data companion
(still R-hat 2.85)** and **n_eff(k_pop)=0.64** independently confirm the non-identifiability is structural,
not a mixing failure — so TMCMC would convert our *failed-to-sample* result into a *correctly-sampled,
honestly-wide, still-non-identified* result. It would **not** make k_pop identifiable, would **not** remove
the netCG bias of the converged without-d model (that bias is **model-class inadequacy / missing higher
modes**, orthogonal to sampling), and would **not** lower the σ_e missing-mode floor.

**Bottom line for a future "NUTS vs TMCMC/ABC" round:** the evidence base supports it. TMCMC/SMC is the right
tool to (i) sample our flat/multimodal posteriors that single-chain NUTS cannot mix, and (ii) compute
evidence for model-class comparison. But it must be framed honestly: TMCMC is a **diagnosis-and-honest-
sampling** tool for our ridge, **not a fix** for the structural confounding or the missing-mode bias. The
real fixes remain modeling-side (orthogonal/cut discrepancy; higher-fidelity FEM).

---

## (d) Consistency of prescriptions — paper vs us

**What the paper would prescribe** for ill-posed/flat updating problems is twofold:
1. **Increase observability** to move I → III: more measured DOFs, longer records, wider-band excitation
   (Case I→III is achieved exactly this way, pp. 821–825). This is a *data/experiment-design* lever.
2. **If you must live with a difficult posterior, sample it properly with TMCMC and use evidence f(D|M)**
   (Eqs. 1–2, 11, 15; Tables 1, 5) to do **model class selection / averaging** rather than committing to one
   model class.

**What we prescribed** (memory.md NEXT ACTION; both blind reviews §7/headline): (a) make the discrepancy
**orthogonal to the calibration parameters** (output-mode/participation space) or use **modular / "cut"
updating** so the discrepancy cannot trade against k_pop; (b) **raise FEM fidelity** (flexible isogrid panel
+ strut/shell bending) to add the missing in-band and >160 Hz modes.

**Are they consistent? Yes, and complementary — on different axes.**
- The paper's lever-1 (more observability) and our orthogonal/cut-discrepancy prescription **agree that the
  cure for a flat manifold is to break the trade-off** — the paper does it by adding informative data, we do
  it by removing the confounding in the parameterization. Both target the *identifiability* directly rather
  than blaming the sampler.
- Our "higher-fidelity FEM" prescription maps onto the paper's **model-class** thinking: our missing-mode σ_e
  floor is a **model-class inadequacy**, and the paper's framework would address it by **comparing model
  classes via evidence** (a richer FEM is a new M(i); pick the one with higher f[D|M(i)], or average — Eq. 2,
  Example 3/Table 5). This is a genuinely useful lens **we have not used**.

**Does the paper offer an alternative lens on our with-d-vs-without-d comparison? Yes — model-class
evidence.** We currently decide with-d vs without-d on the **convergence gate** (with-d fails, R-hat 2.85;
without-d passes, R-hat 1.009). Ching & Chen would instead/also compute **log[f(D|M)] for each** (Table 1 for
Example 1; Table 5 for Example 3) and let evidence rank them. Evidence carries a built-in **Ockham penalty**
on the extra discrepancy parameters, so it would likely **penalize the over-parameterized confounded with-d
class** on principled grounds rather than only on non-convergence — a sampler-robust complement to our gate.
**Caveat:** computing evidence requires a sampler that integrates over the posterior (TMCMC's S=∏Sⱼ), which
we do not currently run; so this is an *additional reason* to trial TMCMC, not something our present NUTS
pipeline can deliver.

---

## (e) Honest differences and caveats (where the analogy holds vs breaks)

**Where it holds (qualitative):**
- **Posterior geometry + sampler failure mode.** Our flat ridge ↔ Fig. 3; our bimodal Stage-0/1 k_strut ↔
  Fig. 4; our converged without-d ↔ Fig. 5; single-chain collapse/non-ergodicity is the shared pathology.
- **Observability drives identifiability.** Our full-curve→peak-only widening (21.6–27.3×) is the same
  III→I direction the paper produces by removing measured DOFs / shortening the record / narrowing excitation.
- **The taxonomy's logical content** (flat manifold ⇒ non-identifiable regardless of sampler; multimodal ⇒
  need a non-trapping sampler; sharp peak ⇒ classical asymptotics OK) applies to our cases.

**Where it breaks (do not overclaim equivalence):**
- **Dimensionality — our Stage 3 is MDOF, not the paper's 2DOF.** This is the most important caveat. The
  paper's Example 1 is a literal **2DOF, 2-parameter (k₁,k₂)** problem whose posterior can be *drawn* on a
  plane (Figs. 3–5). **Our Stage 3 is a 6-DOF apparent-mass model with k₁…k₆ + a per-strut discrepancy field
  + an axial-dome resonator + build hierarchy** — a high-dimensional posterior. So Stage 3 (and Stage 0/1) is
  an **MDOF analog of the paper's *geometry*** (a flat ridge / multimodality in a 2-parameter projection),
  **not** a same-dimensionality re-run of Fig. 3. The **only genuine 2DOF↔2DOF** comparison in our work is the
  fresh 2DOF StatFEM/FBS run in `artifacts/reports/fresh_2dof_statfem_fbs_20260601` (and its reuse in
  `multi_agent_first_loop_20260602`). Do not read the Stage-3 rows as "the paper's 2DOF problem."
- **Different ridge axes / different cause.** Ching & Chen's Case-I ridge is **pure parameter
  non-identifiability from limited observability** in the **physical (k₁,k₂)** plane. Our key Stage-3 ridge is
  **parameter ↔ model-discrepancy confounding** (k_pop ↔ per-strut d, or σ_d ↔ σ_e), a pathology of a
  **StatFEM discrepancy term living in the calibration parameter space**. The paper **has no discrepancy
  term**, so it does **not** directly study discrepancy-induced confounding; the analogy is to the *geometry*,
  not the *mechanism*. (Even Ching & Chen's Case I would not become identifiable by adding a discrepancy in
  the same space — that is our distinct contribution/failure.)
- **Likelihood and quantity contracts differ.** Theirs: **time-domain acceleration**, known masses, infer
  k/ζ/noise-variance. Ours: **complex MDOF apparent-mass FRF** (Stage 3) or **whole FRF/response-PSD**
  (fresh-2DOF), with a **StatFEM discrepancy**, **build-to-build hierarchy**, and an **FBS netCG QOI**
  (`netCG = [M_L/(M_S+M_L)]·F/m_load`). None of the StatFEM/hierarchy/FBS machinery is in Ching & Chen.
- **"Globally identifiable" ≠ "accurate."** Our converged without-d posterior is a *sharp peak in the wrong
  place* (netCG 3.1× high, 0% coverage; f_dome ~20 Hz low) because of **model-class inadequacy** (missing
  higher modes; σ_e ~150–190× true sensor noise). Ching & Chen's Example 1 uses a *correct* model class, so
  their Case III recovers the truth; our Case-III-like result is identifiable but biased. The paper's own
  AMH "slightly-off peak" (p. 825) is the closest in-paper acknowledgment that a sharp peak can be wrong;
  our missing-mode bias is a **stronger** version the paper does not encounter, and it is the residual that
  **no sampler** (NUTS or TMCMC) can fix — only a richer model class can.
- **Dimensionality.** The paper notes (Conclusion, p. 832) "the accuracy of the TMCMC estimators decreases
  with increasing θ dimension." Our with-d model is high-dimensional (per-strut field + hierarchy), so a
  future TMCMC trial inherits this caveat. `[SPECULATIVE]` it may need many stages / large N to behave on our
  full hierarchical StatFEM model.

---

## Overall conclusion (honest)

**They partly agree, and the disagreement is the most useful part.** Ching & Chen (2007) and our findings
**agree** that (1) our problematic posteriors are genuinely *flat-manifold / multimodal*, not artifacts —
our Stage-3 with-d ridge is qualitatively their Fig.-3 Case-I manifold, and our converged without-d is their
Fig.-5 Case-III sharp peak; (2) single-chain sampling fails on exactly these geometries, so a tempering/SMC
sampler like TMCMC is the indicated tool, supporting a future NUTS-vs-TMCMC/ABC round; and (3) identifiability
is governed by observability/structure, not by the sampler. They **diverge / go beyond us** in offering
**model-class evidence f(D|M)** as a principled, Ockham-penalized lens on our with-d vs without-d comparison —
a tool we have not used. The crucial honest boundary: **TMCMC would let us *sample* our ridge correctly and
compute evidence; it would not *remove* the structural parameter↔discrepancy confounding nor the
missing-higher-mode bias.** Those remain modeling problems (orthogonal/cut discrepancy + higher-fidelity FEM)
— and on that, paper and us are consistent.

---

## Sources (page / section / figure / equation citations — all read from the repo PDF)

Ching, J., and Chen, Y.-C. (2007). "Transitional Markov Chain Monte Carlo Method for Bayesian Model Updating,
Model Class Selection, and Model Averaging." *J. Eng. Mech.* 133(7):816–832. (File:
`2007-transitional-markov-chain-monte-carlo-method-for-bayesian-model-updating-model-class-selection-and-model-averaging.pdf`,
17 PDF pages; journal page = PDF page + 815.)

- **Abstract, p. 816** — TMCMC "able to draw samples from some difficult PDFs (e.g., multimodal PDFs, very
  peaked PDFs, and PDFs with flat manifold)"; estimates evidence f(D|M) for model class selection/averaging.
- **Introduction, pp. 816–817** — model updating "potentially ill-posed … more than one optimal solution
  (Katafygiotis and Beck 1998)"; MH inefficient for highly correlated/very-peaked posteriors; "most MCMC
  techniques are not applicable when the PDF is multimodal."
- **Problem definition, p. 817** — Eq. (1) posterior f(θ|M,D) + evidence f(D|M); Eq. (2) model-class
  posterior P[M(i)|D] ∝ f[D|M(i)]·P[M(i)]; multimodal target ⇒ "nonergodic Markov chain … trapped in one of
  the peaks."
- **TMCMC method, p. 818** — Eq. (10) f(θ|M,D) ∝ prior·likelihood; **Eq. (11) intermediate (tempered) PDFs
  f_j(θ) ∝ f(θ|M)·f(D|M,θ)^{p_j}, 0=p_0<…<p_m=1** (prior→posterior).
- **TMCMC algorithm, pp. 818–819** — Eqs. (12)–(16) plausibility weights / resampling; **evidence
  S=∏_{j} S_j asymptotically unbiased for f(D|M)** (step 3; Eq. 15).
- **Example 1 (2DOF), p. 821** — m₁=m₂=1, k₁=k₂=1000, ζ=3%, masses known, infer stiffness/damping/noise
  variance from acceleration; uniform priors k∈[0,3000], ζ∈[0.01,0.05], noise var∈[0,1]; Cases I (flat,
  narrow-band 1 s, "almost unidentifiable"), II (bimodal, wide-band 1 s), III (single sharp peak, roof+base+
  2F, 10 s). **Fig. 1 (p. 821) = "2DOF and 4DOF planar shear building"** (structural diagram, NOT the
  taxonomy). Fig. 2 (p. 821) = p-value evolution.
- **Figs. 3, 4, 5 (pp. 822–824)** — (k₁,k₂) sample evolution, AMH vs TMCMC, for Cases I/II/III. *I inspected
  these images:* Fig. 3 = curved L-shaped ridge (flat manifold); Fig. 4 = two isolated clusters (bimodal,
  ≈(1000,1000) & ≈(1900,500)); Fig. 5 = single tight point at (1000,1000); AMH collapses/traps in all three.
- **Results discussion, p. 825** — "For Case II, the posterior PDF contains two peaks … For Case III … one
  sharp peak located at [1,000 1,000] … the AMH samples converge to a location slightly different from
  [1,000 1,000]." **Table 1 (p. 825)** reports per-case log[f(D|M)] (evidence) and E[max drift].
- **Example 2 (mixture of two Gaussians), p. 825** — plain MH "samples are trapped in one peak" when peaks
  isolated; TMCMC samples both — direct multimodality demonstration.
- **Example 3 (4DOF) + Table 5 (p. 831)** — model class selection by per-model-class log[f(D|M)].
- **Conclusion, p. 832** — TMCMC applicable to multimodal and higher-dimensional posteriors, but "accuracy
  of the TMCMC estimators decreases with increasing θ dimension."
- **References, p. 832** — Katafygiotis & Beck (1998), "Part II: Model identifiability," *J. Eng. Mech.*
  124(4):463–467 (source of the globally/locally/unidentifiable taxonomy, `[TO-VERIFY]`, not in repo);
  Beck & Au (2002) (AMH); Beck & Yuen (2004) (model selection).

**Our findings cited:**
- `artifacts/reports/blind_round3_review_20260604/review.md` (Stage 0/1: R-hat 2.41, ESS≈5; σ_d↔σ_e ridge
  masked by σ_d cap; bimodal k_strut; netCG 4.86×; σ_e ~120× true noise).
- `artifacts/reports/blind_round3_stage3_review_20260605/review.md` (Stage 3: without-d R-hat 1.009/ESS 487;
  with-d R-hat 2.85/ESS 4.7, σ_d→1.33, n_eff(k_pop)=0.64; starve-data still 2.85; netCG 3.10× converged /
  1.71× wide; σ_e ~150–190× true noise; missing-mode floor).
- `runs/round3/opus48/report/packet_stage3.md`, `blind_known_failures.md` (per-strut confounding lesson;
  "discrepancy must be orthogonal to calibration params / modular cut updating"; Stage-4 higher-fidelity FEM).
- `artifacts/reports/fresh_2dof_statfem_fbs_20260601/peak_feature_likelihood_summary.json` (full-vs-peak:
  fn interval widening 21.57× dome / 27.32× tray; legacy random-walk MH, acceptance ~0.49).
- `CLAUDE.md` (NUTS/HMC default + convergence gate: R-hat ≤1.05/≤1.01, ESS≥200, divergence <2%, ≥4 chains,
  non-centered hierarchical).
