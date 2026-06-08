# What to ask Mark Girolami

Andrew Voss. 2026-06-08. For a first substantive exchange (you are connected on LinkedIn).

Purpose: sanity-check where the real white space is, surface the blockers he sees, and gauge
interest in a dynamic/aerospace test-drive of StatFEM, WITHOUT handing over the inventive idea.

---

## IP guardrail — read before you contact him (this changes what you say)

Girolami is the StatFEM author and an external expert. Two risks if you describe the specific
novel method (the "error-by-part-type" discrepancy, or the complex-lossy-joint-impedance +
unknown-forcing + load-QOI bundle):
1. **Co-inventorship / ownership.** If he contributes to the inventive concept, he (and his
   institution) can become a co-inventor, which complicates your title. This is the same logic
   in the Dr. B briefing, and it is STRONGER for an unaffiliated third party.
2. **Public-disclosure / novelty risk.** A detailed technical disclosure to someone outside a
   confidentiality arrangement can count against patentability.

So: keep this exchange at the level of PUBLISHED gaps and his read of the field. Ask about what
is open; do not reveal your specific claim. Per the IP plan (project_vision §9), disclose to the
Purdue Senior IP Officer BEFORE any substantive technical exchange or collaboration, and get the
provisional conception record dated first. If a real collaboration looks likely, route it through
a confidentiality / IP agreement rather than an open chat.

Honesty note: the OMA / input-state / force-ID + complex-joint-impedance **lit scan has not been
run yet**, so these questions partly stand in for it. After the scan you can ask sharper, more
specific things. Also, the recent dynamic-StatFEM references below came from an agent web-fetch on
2026-06-08; confirm the exact titles/authors yourself before citing them to him.

---

## Posture
Short, specific, and informed. Show you have read StatFEM and the digital-twin paper (and the
recent dynamic-StatFEM work). Lead with a genuine technical question, not a pitch. You are a
practicing aerospace structural dynamicist test-driving his method on problems you know well; that
is a credible and interesting position for him.

## The questions (gap-mapping; no inventive disclosure)

1. **Dynamic / frequency-domain observation.** I have seen StatFEM move from static/quasi-static
   to time-dependent / elastodynamic settings [recent dynamic-StatFEM paper, ~2026 — verify ref].
   Has it been driven by **frequency-domain data specifically — FRFs, modal parameters, or PSDs** —
   rather than time-domain state estimation? That is the data aerospace modal/vibration testing
   actually produces.

2. **Unknown / operational forcing.** In the StatFEM work I have seen, the input/forcing is known.
   Has StatFEM been run **output-only, with the excitation unknown and stochastic** (the operational
   modal analysis / joint input-state-estimation regime, e.g. Lourens, Maes)? Where does the
   input/system identifiability sit when you do not measure the force?

3. **Assembled interfaces and an interface-LOAD QOI.** Has StatFEM been applied at a **component
   interface in a substructured / CMS-FBS model**, where the quantity of interest is the **interface
   force / load** (not a displacement field), and the uncertain element is the **joint** (a complex,
   frequency-dependent, lossy impedance)? This is the regime where aerospace loads and force-limiting
   live.

4. **Parameter ↔ discrepancy confounding.** In dynamic StatFEM, how do you keep the model-form
   discrepancy from **absorbing the physical parameters** you are trying to identify
   (Kennedy-O'Hagan / Brynjarsdottir-O'Hagan / Plumlee)? Is that identifiability the live blocker you
   see, and do you lean on orthogonal/modular/cut formulations to control it?

5. **Discrepancy vs missing modes.** In a blind synthetic study we ran, the dominant residual was a
   **missing-higher-mode (fidelity) error** that a smooth GP discrepancy could not represent. Do you
   see the model-form discrepancy as the right tool for missing-resonance error, or do you reach for
   **higher fidelity / model-class selection** in that case? (Genuine methodological question.)

6. **Collaboration & venue.** Would a **dynamic, aerospace test-drive of StatFEM** — real
   vibration data, an interface-load decision — be of interest to you or your group? And is
   *Data-Centric Engineering* the right home for that kind of physics+data result?

## Do NOT, in this first exchange
- Describe the error-by-part-type discrepancy or the specific novel bundle as "your idea/method."
- Propose he co-develop the inventive concept before IP is sorted.
- Ask the now-stale question "has StatFEM gone dynamic?" — it has; that would signal you have not
  read his recent work. Ask the finer questions above instead.

## If he engages
Move a real collaboration to a confidentiality / IP arrangement (via Sponsored Programs), and keep
a dated record of who contributed which idea, so inventorship stays clean.
