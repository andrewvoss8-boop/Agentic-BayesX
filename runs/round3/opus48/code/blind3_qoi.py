#!/usr/bin/env python3
"""STAGE-3 full-uncertainty netCG + interface-PSD QOI (canonical FBS contract; closes D13).

netCG = F_iface/m_load, F_iface from DYNAMIC FBS coupling of source+load apparent mass (z DOF):
  H(w) = M_L_z/((M_S_z+M_L_z) m_load g0);  netCG(w)=H F;  PSD_netCG=|H|^2 PSD_F;  3GRMS=3 sqrt(int PSD df).
  f->0 rigid limit netCG->F/(m_source+m_load); resonates at coupled modes. FORBIDDEN: rigid const ratio,
  drive-point F/M_zz. (See netcg_quantity_contract.md.)

Full uncertainty propagated (D13): parameter (k_pop,d0,f_dome epistemic) + build (exp(sigma_build z),
aleatory) + flight (11 published flight forcings, aleatory) + structure-based discrepancy d (its posterior
uncertainty). sigma_e is sensor noise -> excluded from the physical QOI.

Reads report/blind3_posterior.npz. Writes report/blind3_qoi_results.json + figures.
"""
from __future__ import annotations
import json, os, sys
from pathlib import Path
import numpy as np
import jax, jax.numpy as jnp
jax.config.update("jax_enable_x64", True)
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import blind3_model as bm

HERE = Path(__file__).resolve().parents[1]
REP = HERE / "report"; FIG = REP / "figures"; FIG.mkdir(parents=True, exist_ok=True)
NSUB = 400


def main(post_name="blind3_posterior.npz", tag="withd", results_name="blind3_qoi_results.json"):
    obs = bm.load_observations()
    P = np.load(REP / post_name)
    # M_src6/m_dome are deterministic read-offs (not parameters) -> recompute from obs (robust to npz contents)
    M_src6, m_dome, lf = bm.source_rigid_from_asymptote(obs)
    m_load = obs["load_mass"]; g0 = obs["g0"]
    m_source_z = float(M_src6[2] + m_dome)

    # QOI integration grid: dense log grid over the energy band (5-300 Hz captures mount+bounce cluster)
    fq = np.geomspace(5.0, 300.0, 500)
    fqj = jnp.asarray(fq)
    # forcing on the QOI grid
    flight = np.stack([np.interp(fq, obs["f"], obs["flight_force"][k]) for k in range(obs["flight_force"].shape[0])])
    design = np.interp(fq, obs["f"], obs["design_force"])     # qualification envelope (spec)

    # subsample posterior (d0 absent in the without-discrepancy posterior -> zeros)
    k_pop = np.exp(P["log_k_pop"]); f_dome = P["f_dome"]; sb = P["sigma_build"]
    d0 = P["d0"] if "d0" in P.files else np.zeros((len(k_pop), 6))
    nd = len(k_pop); idx = np.linspace(0, nd - 1, min(NSUB, nd)).astype(int)
    rng = np.random.default_rng(11)

    def H_of(k_struts, fd):
        MLz, MSz = bm.netcg_transfer_z(jnp.asarray(k_struts), float(fd), M_src6, m_dome, fqj)
        return np.asarray(MLz), np.asarray(MSz)

    # ---- full-uncertainty netCG 3GRMS samples (draw x flight) ----
    grms = []; psd_draws = []
    Hmag_nom = None
    for ii, i in enumerate(idx):
        zb = rng.standard_normal()                       # aleatory NEW build
        k = k_pop[i] * np.exp(sb[i] * zb) * np.exp(d0[i])
        MLz, MSz = H_of(k, f_dome[i])
        H = MLz / ((MSz + MLz) * m_load * g0)
        Hmag2 = np.abs(H) ** 2
        if ii == 0:
            Hmag_nom = (MLz, MSz, H)
        for kf in range(flight.shape[0]):
            psd = Hmag2 * flight[kf]
            grms.append(3.0 * np.sqrt(np.trapz(psd, fq)))
            if ii < 60:
                psd_draws.append(psd)
    grms = np.array(grms); psd_draws = np.array(psd_draws)

    truth_obs = obs["netcg"].ravel()                     # published observed netCG (the comparison)
    qp = np.percentile(grms, [0.5, 2.5, 50, 97.5, 99.5])
    cov95 = float(np.mean((truth_obs >= qp[1]) & (truth_obs <= qp[3])))
    cov99 = float(np.mean((truth_obs >= qp[0]) & (truth_obs <= qp[4])))
    bias = float(np.median(grms) / np.mean(truth_obs))

    # ---- spec / narrow-band exceedance: 99%-hi predicted flight netCG PSD vs spec (design envelope) ----
    spec_psd = np.abs(Hmag_nom[2]) ** 2 * design
    hi99 = np.percentile(psd_draws, 99, axis=0)
    exceed_frac = float(np.mean(hi99 > spec_psd))
    spec_grms = 3.0 * np.sqrt(np.trapz(spec_psd, fq))
    overall_margin = float(spec_grms / np.median(grms))

    results = dict(
        definition="netCG=F_iface/m_load; F_iface from FBS coupling M_L/(M_S+M_L)*F (canonical contract)",
        m_source_z_kg=m_source_z, m_load_kg=m_load,
        netcg_fzero_rigid_limit=float(m_load / (m_source_z + m_load)),
        netcg_3grms_g=dict(p0p5=float(qp[0]), p2p5=float(qp[1]), p50=float(qp[2]),
                           p97p5=float(qp[3]), p99p5=float(qp[4])),
        published_observed_netcg_g=dict(min=float(truth_obs.min()), mean=float(truth_obs.mean()),
                                        max=float(truth_obs.max())),
        coverage_of_published_95=cov95, coverage_of_published_99=cov99, bias_ratio_median=bias,
        spec_3grms_g=float(spec_grms), overall_scalar_margin=overall_margin,
        narrowband_exceedance_frac_99hi_vs_spec=exceed_frac,
        n_posterior_used=len(idx), n_flights=int(flight.shape[0]),
        posterior=post_name, tag=tag,
        note="full uncertainty: parameter(epistemic)+build(aleatory)+flight(aleatory)+discrepancy d. "
             "sigma_e (sensor noise) excluded from physical QOI. Compare vs PUBLISHED observed netCG.")
    (REP / results_name).write_text(json.dumps(results, indent=2))

    # ---- FIG 1: netCG transfer |H|*m_load*g0 = M_L/(M_S+M_L): f->0 limit + resonance ----
    MLz, MSz, H = Hmag_nom
    ratio = np.abs(MLz / (MSz + MLz))
    fig, ax = plt.subplots(figsize=(8.4, 5.0))
    ax.semilogx(fq, ratio, color="#1f77b4", lw=2, label="|M_L/(M_S+M_L)| (FBS transmission)")
    ax.axhline(m_load / (m_source_z + m_load), color="gray", ls="--",
               label=f"f→0 rigid limit = m_load/(m_src+m_load) = {m_load/(m_source_z+m_load):.3f}")
    ax.set_xlabel("frequency [Hz] (log)"); ax.set_ylabel("FBS transmission ratio")
    ax.set_title("netCG transfer (canonical FBS): rigid f→0 limit + resonant amplification\n"
                 "NOT drive-point F/M_zz, NOT a constant mass ratio", fontsize=10)
    ax.grid(True, which="both", alpha=0.3); ax.legend(fontsize=8.5)
    fig.tight_layout(); fig.savefig(FIG / f"blind3_netcg_transfer_{tag}.png", dpi=140); plt.close(fig)
    if tag == "withd":
        import shutil; shutil.copy(FIG / f"blind3_netcg_transfer_{tag}.png", FIG / "blind3_netcg_transfer.png")

    # ---- FIG 2: full-uncertainty netCG 3GRMS vs published truth ----
    fig, ax = plt.subplots(figsize=(8.4, 5.0))
    ax.hist(grms, bins=50, density=True, color="#9ecae1", alpha=0.8, label="predicted netCG 3·GRMS (full unc.)")
    for i, t in enumerate(truth_obs):
        ax.axvline(t, color="#d62728", alpha=0.25, lw=1, label="published observed" if i == 0 else None)
    ax.axvline(qp[2], color="#1f77b4", lw=2, label=f"pred median {qp[2]:.2f} g")
    ax.axvspan(qp[1], qp[3], color="#1f77b4", alpha=0.12, label="pred 95%")
    ax.set_xlabel("netCG 3·GRMS [g]"); ax.set_ylabel("density")
    ax.set_title(f"Full-uncertainty netCG vs published truth — bias {bias:.2f}×, "
                 f"95% cov {cov95:.2f}, 99% cov {cov99:.2f}", fontsize=10)
    ax.legend(fontsize=8.5); fig.tight_layout()
    fig.savefig(FIG / f"blind3_netcg_grms_vs_truth_{tag}.png", dpi=140)
    if tag == "withd":
        import shutil; shutil.copy(FIG / f"blind3_netcg_grms_vs_truth_{tag}.png", FIG / "blind3_netcg_grms_vs_truth.png")
    plt.close(fig)

    # ---- FIG 3: interface netCG PSD bands vs spec (narrow-band exceedance) ----
    lo = np.percentile(psd_draws, 2.5, axis=0); md = np.percentile(psd_draws, 50, axis=0)
    fig, ax = plt.subplots(figsize=(8.6, 5.0))
    ax.loglog(fq, spec_psd, color="k", lw=2, label="spec (design envelope) netCG PSD")
    ax.loglog(fq, md, color="#1f77b4", lw=1.6, label="predicted median")
    ax.fill_between(fq, lo, hi99, color="#1f77b4", alpha=0.18, label="predicted 2.5–99%")
    exc = hi99 > spec_psd
    ax.loglog(fq[exc], hi99[exc], "r.", ms=3, label="99%-hi exceeds spec")
    ax.set_xlabel("frequency [Hz] (log)"); ax.set_ylabel("netCG PSD [g²/Hz] (log)")
    ax.set_title(f"Interface netCG PSD vs spec — overall margin {overall_margin:.2f}×, "
                 f"narrow-band 99%-hi exceedance {exceed_frac*100:.1f}%", fontsize=10)
    ax.grid(True, which="both", alpha=0.3); ax.legend(fontsize=8)
    fig.tight_layout(); fig.savefig(FIG / f"blind3_netcg_psd_vs_spec_{tag}.png", dpi=140)
    if tag == "withd":
        import shutil; shutil.copy(FIG / f"blind3_netcg_psd_vs_spec_{tag}.png", FIG / "blind3_netcg_psd_vs_spec.png")
    plt.close(fig)

    print("[%s] netCG 3GRMS p50 %.3f g [95%% %.3f-%.3f] | truth mean %.3f (%.3f-%.3f)" %
          (tag, qp[2], qp[1], qp[3], truth_obs.mean(), truth_obs.min(), truth_obs.max()))
    print("[%s] bias %.2fx | 95%% cov %.2f | 99%% cov %.2f | f->0 limit %.3f" %
          (tag, bias, cov95, cov99, m_load / (m_source_z + m_load)))
    print("[%s] spec margin %.2fx | narrow-band 99hi exceedance %.1f%%" % (tag, overall_margin, exceed_frac * 100))


if __name__ == "__main__":
    # primary = WITH-d (non-converged; caveated); also the CONVERGED without-d (trustworthy QOI)
    main("blind3_posterior.npz", "withd", "blind3_qoi_results.json")
    main("blind3_posterior_nodisc.npz", "nodisc", "blind3_qoi_results_nodisc.json")
