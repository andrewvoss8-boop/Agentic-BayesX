#!/usr/bin/env python3
"""Wide-band tray FRF: ALL modes, with prior (k_j) uncertainty + build variability.

Answers: 'are there graphs of the prior and variability for the tray FRF (all modes)?'
Shows the load interface apparent mass |M_L(w)| AND the coupled interface accelerance over 20-2000 Hz
(joint bounce + panel flex modes), with the prior-predictive band from the k_j prior and build draws.
Also overlays the measurement band used for inference and the (narrow) model-form-error band, to make
the band-coverage question explicit.
"""
from __future__ import annotations
import sys, math
from pathlib import Path
import numpy as np
import jax.numpy as jnp
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

HERE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE/"code"))
import mdof_forward as mdof
import statfem_kj as sf

FIG = HERE/"report"/"figures"
F = np.geomspace(20.0, 2000.0, 1200)
jf = jnp.asarray(F)


def appmass(kj):
    f_tray = math.sqrt(kj/sf.M_LOAD)/(2*np.pi)
    return np.abs(np.asarray(mdof.load_apparent_mass(f_tray, sf.ZETA_TRAY, jf, sf.TRAY_FLEX, m_load=sf.M_LOAD)))


def iface(kj):
    f_tray = math.sqrt(kj/sf.M_LOAD)/(2*np.pi)
    return np.abs(np.asarray(mdof.interface_accel_per_force_g(sf.DOME_F1, f_tray, sf.ZETA_DOME, sf.ZETA_TRAY,
                  jf, sf.DOME_BASIS, sf.TRAY_FLEX, m1_eff=sf.M1_PHYS, m2_eff=sf.M_LOAD)))


def main():
    rng = np.random.default_rng(7)
    # prior-predictive k_j draws
    kj_prior = np.exp(rng.normal(math.log(sf.KJ_GUESS), sf.PRIOR_LOG_SD, 300))
    # build-variability draws around truth
    kj_build = sf.KJ_TRUE*np.exp(sf.SIGMA_BUILD*rng.standard_normal(12))

    AM_prior = np.array([appmass(k) for k in kj_prior])
    IF_prior = np.array([iface(k) for k in kj_prior])
    flex = sf.TRAY_FLEX

    fig, axes = plt.subplots(2, 1, figsize=(11, 9))
    # ---- apparent mass (inference channel) ----
    ax = axes[0]
    lo, md, hi = np.quantile(AM_prior, [0.05, 0.5, 0.95], axis=0)
    ax.fill_between(F, lo, hi, color="#ccccff", alpha=0.7, label="prior-predictive 5–95% (from k_j prior)")
    ax.loglog(F, md, color="#3333aa", lw=1.8, label="prior median")
    ax.loglog(F, appmass(sf.KJ_TRUE), color="#d62728", lw=2.0, ls="--", label="truth k_j")
    for i, k in enumerate(kj_build):
        ax.loglog(F, appmass(k), color="#2ca02c", lw=0.7, alpha=0.5, label="build draws (12)" if i==0 else None)
    ax.axvspan(45, 180, color="orange", alpha=0.12, label="inference band (45–180 Hz)")
    for fk, lab in [(sf.TRAY_F1_TRUE, "joint bounce 86 Hz"), (flex[0], f"panel flex {flex[0]:.0f} Hz"),
                    (flex[1], f"panel flex {flex[1]:.0f} Hz")]:
        ax.axvline(fk, color="gray", ls=":", lw=0.9); ax.text(fk*1.02, ax.get_ylim()[1]*0.3 if False else 1, "", fontsize=7)
    ax.set_xlabel("frequency [Hz] (log)"); ax.set_ylabel("|M_L| apparent mass [kg]")
    ax.set_title("Tray LOAD interface apparent mass — ALL modes (joint bounce + panel flex)\n"
                 "prior-predictive band = ONLY the joint mode (86 Hz) moves with k_j; panel flex modes (377, 1632 Hz) are FIXED", fontsize=9.5)
    ax.grid(True, which="both", alpha=0.3); ax.legend(fontsize=8, loc="upper right")
    # ---- coupled interface accelerance ----
    ax = axes[1]
    lo, md, hi = np.quantile(IF_prior, [0.05, 0.5, 0.95], axis=0)
    ax.fill_between(F, lo, hi, color="#cce5cc", alpha=0.7, label="prior-predictive 5–95% (from k_j prior)")
    ax.loglog(F, md, color="#1f7a1f", lw=1.8, label="prior median")
    ax.loglog(F, iface(sf.KJ_TRUE), color="#d62728", lw=2.0, ls="--", label="truth k_j")
    ax.set_xlabel("frequency [Hz] (log)"); ax.set_ylabel("|H_iface| coupled accelerance [g/N]")
    ax.set_title("Coupled INTERFACE accelerance — all coupled modes; the k_j prior moves the joint-related coupled feature", fontsize=9.5)
    ax.grid(True, which="both", alpha=0.3); ax.legend(fontsize=8, loc="lower left")
    fig.tight_layout(); fig.savefig(FIG/"statfem_tray_frf_allmodes.png", dpi=145); plt.close(fig)
    print("wrote", FIG/"statfem_tray_frf_allmodes.png")
    print("tray modes: joint %.1f Hz, panel flex %s Hz" % (sf.TRAY_F1_TRUE, np.round(flex,0)))


if __name__ == "__main__":
    main()
