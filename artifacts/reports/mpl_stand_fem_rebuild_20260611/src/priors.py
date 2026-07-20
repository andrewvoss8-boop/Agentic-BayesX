#!/usr/bin/env python3
"""Prior registry for the MPL stand twin (FABLE, 2026-06-11, D34).

This is the single place future Bayesian-updating work (the NEXT card) reads
priors from. NOTHING here runs a sampler. Each prior is on a GROUP SCALAR that
the parametric assembly already exposes: theta_g multiplies a fixed K_g or M_g,
so K(theta)=sum s_g K_g, M(theta)=sum m_g M_g (see assemble.py / meta.json).

Plain-English note for the ML side: a LogNormal(median m, sigma_ln s) prior on
a positive quantity x means ln(x) ~ Normal(ln m, s). It is the natural prior
for a mass/stiffness because (a) x stays positive, (b) it is multiplicative
(a factor-of-2 up and a factor-of-2 down are equally likely), and (c) NUTS
samples its unconstrained log nicely. The 95% interval is
[m * exp(-1.96 s), m * exp(+1.96 s)].

Writes out/priors.json.
"""
import json
import math
import os

import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from estimates import ESTIMATES

WS = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def lognormal_from_interval(lo, hi, p=0.95):
    """Median + sigma_ln of a LogNormal whose central p-interval is [lo,hi]."""
    from statistics import NormalDist
    z = NormalDist().inv_cdf(0.5 + p / 2.0)
    median = math.sqrt(lo * hi)            # geometric mean
    sigma_ln = math.log(hi / lo) / (2 * z)
    return median, sigma_ln


# ---- electronics-box mass: Andrew 'between 2 and 4 pounds' (round 4) --------
ebox_nominal = ESTIMATES["electronics_box"]["value"]["mass_lbm"]  # 3.0
m_med, m_sig = lognormal_from_interval(2.0, 4.0, p=0.95)

PRIORS = {
    # prior is on the SCALAR multiplying M_m_ebox; nominal mass = 3.0 lbm so
    # scalar s = mass/3.0. Encode the prior in BOTH mass and scalar terms.
    "M_m_ebox": dict(
        quantity="electronics-box mass scalar (mass = 3.0 lbm * scalar)",
        dist="lognormal", median_scalar=m_med / ebox_nominal,
        sigma_ln=m_sig,
        median_mass_lbm=m_med, mass_95=[2.0, 4.0],
        source="Andrew 2026-06-11 round 4: 'between 2 and 4 pounds'",
        status="ELICITED PRIOR (to be updated to a posterior in the next "
                "card from the tap-test frequencies)"),
}

# ---- the other estimated knobs are ALSO priors (wide, pending elicitation) --
# Documented here so the next card has a complete starting prior; widths are
# placeholders the human can tighten. NOT yet elicited from Andrew = wide.
PLACEHOLDER = {
    "M_m_valvemass": dict(quantity="valve tank/manifold lumped-mass scalar "
                          "(nominal 16 lbm on the 80/20 frame)",
                          dist="lognormal", median_scalar=1.0, sigma_ln=0.25,
                          status="PLACEHOLDER (Andrew to confirm tank/valve "
                          "masses)"),
    "K_valveframe": dict(quantity="80/20 valve-frame stiffness scalar "
                         "(extrusion series; nominal 1515 aluminum)",
                         dist="lognormal", median_scalar=1.0, sigma_ln=0.69,
                         note="the extrusion SERIES is the dominant knob "
                         "(~10x between 1\"/1.5\"/40mm); confirm series",
                         status="PLACEHOLDER"),
    "M_m_wbox": dict(quantity="white/beige box mass scalar (nominal 8 lbm)",
                     dist="lognormal", median_scalar=1.0, sigma_ln=0.30,
                     status="PLACEHOLDER guess"),
    "K_shield_att": dict(quantity="shield weld-spot stiffness scalar",
                         dist="lognormal", median_scalar=1.0, sigma_ln=1.15,
                         note="wide: spans ~x0.1-x10 (1-sigma), the #1 BC knob",
                         status="PLACEHOLDER"),
    "K_bush_joints": dict(quantity="deck joint (CBUSH) stiffness scalar",
                          dist="lognormal", median_scalar=1.0, sigma_ln=0.69,
                          status="PLACEHOLDER (x0.5-x2 1-sigma)"),
    "K_shield_mem": dict(quantity="shield in-plane(+bend via t) stiffness scalar",
                         dist="lognormal", median_scalar=1.0, sigma_ln=0.15,
                         note="t CONFIRMED 1.7mm -> narrow; couples to bend^3",
                         status="PLACEHOLDER"),
    "K_att_ebox": dict(quantity="electronics-box bolt stiffness scalar",
                       dist="lognormal", median_scalar=1.0, sigma_ln=0.69,
                       status="PLACEHOLDER"),
}

out = dict(
    note="Prior registry for the FUTURE posterior-update card. No sampler runs "
         "in the rebuild task. Priors are on group scalars exposed by "
         "assemble.py (theta -> K(theta), M(theta)).",
    elicited=PRIORS, placeholder=PLACEHOLDER,
    box_mass_prior_plain_english=(
        f"electronics box: LogNormal, median {m_med:.3f} lbm, sigma_ln "
        f"{m_sig:.4f}; 95% interval exactly [2.00, 4.00] lbm per Andrew. "
        "Mode 1 of the stand (box-on-panel) is the observable that updates it."))
with open(os.path.join(WS, "out", "priors.json"), "w") as fh:
    json.dump(out, fh, indent=1)

if __name__ == "__main__":
    print(json.dumps(out["elicited"], indent=1))
    print("box-mass prior:", out["box_mass_prior_plain_english"])
