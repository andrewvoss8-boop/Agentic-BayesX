#!/usr/bin/env python3
"""(b) headline QOI = per-location modal FREQUENCY content (identifiable). Extracts measured peak frequencies per
accel location from features.json (tap spectra), gates FEM modes by OOP amplitude at the node ("alive" modes),
matches measured peaks to the nearest alive FEM mode, calibrates theta on TRAINING locations via a differentiable
matched-eigenfrequency likelihood (lam(theta) eigen-sensitivity; converges per project Study K/L5), and scores
the held-out location's peak frequencies with CRPS-skill vs CLIMATOLOGY (predict held-out peaks from the pooled
observed-location peaks) + interval/coverage. Transmissibility shape stays a diagnostic (D7).
"""
from __future__ import annotations
import json, os, sys, time
from pathlib import Path
import numpy as np

os.environ.setdefault("OMP_NUM_THREADS", "1"); os.environ.setdefault("VECLIB_MAXIMUM_THREADS", "1")
os.environ.setdefault("XLA_FLAGS", "--xla_force_host_platform_device_count=4")
sys.path.insert(0, str(Path(__file__).resolve().parent))
import mpl_fem as FF
import score as SC

WS = Path(__file__).resolve().parents[1]; OUT = WS / "out"
FEAT = WS.parents[2] / "MPL test stand" / "FEM" / "test_data_scan_20260611" / "features.json"
FBAND = (40.0, 300.0)
FMAX_KEEP = 420.0
GROUPS = ["K_shield_bend", "K_shield_mem", "K_beam_wall", "K_beam_rest", "K_plate_bend", "K_bush_joints"]
# accel CSV (sensor position) -> held-out location key
FILE2LOC = {
    "unloaded top.csv": "interface",
    "shield tap.csv": "shield",
    "top left beam tap.csv": "beam",
    "valve tap (engine mount) and acoustic.csv": "valve",
    "top left avi foot tap and acoustic.csv": "avi-L",
    "top right avi foot tap and acoustic.csv": "avi-R",
}
HELD = ["interface", "beam", "valve", "avi-L", "avi-R"]
ALIVE_FRAC = 0.10     # mode "alive" at a node if |phi_x| >= ALIVE_FRAC * max_i|phi_x| there
MATCH_WIN = 0.08      # match a measured peak to nearest alive FEM mode within +/-8%


def measured_peaks():
    """Per-location robust measured peak set (Hz) in FBAND, from features.json tap spectra."""
    feat = json.load(open(FEAT))["tap_spectra"]
    loc_peaks = {l: [] for l in (HELD + ["shield"])}
    for fn, blk in feat.items():
        if fn not in FILE2LOC:
            continue
        loc = FILE2LOC[fn]
        lists = [v["peak_hz"] for v in blk["locations"].values()]
        allpk = sorted(p for L in lists for p in L if FBAND[0] <= p <= FBAND[1])
        if len(lists) >= 3:
            # cluster within 2.5 Hz; keep clusters seen in >=2 tap lists (robust = a real global mode)
            clusters = []
            for p in allpk:
                if clusters and p - clusters[-1][-1] <= 2.5:
                    clusters[-1].append(p)
                else:
                    clusters.append([p])
            peaks = sorted(float(np.mean(c)) for c in clusters if len(c) >= 2)
        else:
            peaks = sorted(set(round(p, 2) for p in allpk))
        loc_peaks[loc] = peaks
    return loc_peaks


def precompute():
    fem = FF.FEM_model()
    freqs, Phi = fem.solve_modes()
    keep = freqs <= FMAX_KEEP
    freqs = freqs[keep]; Phi = Phi[:, keep]
    lam0 = (2 * np.pi * freqs) ** 2
    phix, gamma = fem.oop_shapes(Phi)
    se = {}
    for g in GROUPS:
        Kg = fem.KG[g[2:]]
        se[g] = np.einsum("ij,ij->j", Phi, (Kg @ Phi)) / np.maximum(lam0, 1e-30)
    return dict(fem=fem, freqs=freqs, lam0=lam0, phix=phix, se=se, groups=list(GROUPS),
                mpk=measured_peaks())


def alive_modes(P, loc):
    """indices of FEM modes alive at loc (|phi_x| >= ALIVE_FRAC*max) and in/near FBAND."""
    a = np.abs(P["phix"][loc]); thr = ALIVE_FRAC * a.max()
    return np.where((a >= thr) & (P["freqs"] >= FBAND[0] * 0.8) & (P["freqs"] <= FBAND[1] * 1.1))[0]


def match_pairs(P, loc, freqs_theta=None):
    """match each measured peak at loc to the nearest ALIVE FEM mode within MATCH_WIN. Returns list of
    (measured_hz, mode_index, fem_hz)."""
    f = P["freqs"] if freqs_theta is None else freqs_theta
    alive = alive_modes(P, loc)
    pairs = []
    for fm in P["mpk"][loc]:
        if alive.size == 0:
            continue
        k = alive[np.argmin(np.abs(f[alive] - fm))]
        if abs(f[k] - fm) / fm <= MATCH_WIN:
            pairs.append((float(fm), int(k), float(f[k])))
    return pairs


def calibrate_freq(P, train, seed=20260620, warmup=800, samples=800, chains=4, prior_sd=0.12):
    """Matched-eigenfrequency NUTS calibration on TRAINING locations (assignments fixed at nominal)."""
    import jax, jax.numpy as jnp, numpyro, numpyro.distributions as dist
    from numpyro.infer import MCMC, NUTS
    import numpyro.diagnostics as diag
    numpyro.set_host_device_count(chains)
    pairs = [(fm, k) for loc in train for (fm, k, _) in match_pairs(P, loc)]
    fm = jnp.asarray([p[0] for p in pairs]); kidx = np.array([p[1] for p in pairs])
    lam0p = jnp.asarray(P["lam0"][kidx])
    SEp = jnp.asarray(np.stack([P["se"][g][kidx] for g in P["groups"]], 0))   # (G, npairs)
    G = len(P["groups"])

    def model():
        tau = numpyro.sample("tau", dist.Normal(jnp.zeros(G), prior_sd))
        theta = numpyro.deterministic("theta", jnp.exp(tau))
        sigf = numpyro.sample("sigma_f", dist.HalfNormal(0.1))
        lam = lam0p * (1.0 + jnp.sum(SEp * (theta[:, None] - 1.0), axis=0))
        fk = jnp.sqrt(jnp.maximum(lam, 1e-6)) / (2 * jnp.pi)
        numpyro.sample("obs", dist.Normal(jnp.log(fk), sigf), obs=jnp.log(fm))

    mcmc = MCMC(NUTS(model, target_accept_prob=0.9), num_warmup=warmup, num_samples=samples,
                num_chains=chains, chain_method="sequential", progress_bar=False)
    mcmc.run(jax.random.PRNGKey(seed))
    grp = mcmc.get_samples(group_by_chain=True); rh, es = [], []
    for k, v in grp.items():
        va = np.asarray(v)
        cols = [va] if va.ndim == 2 else [va[:, :, j] for j in range(va.shape[-1])]
        for c in cols:
            rh.append(float(diag.gelman_rubin(c))); es.append(float(diag.effective_sample_size(c)))
    ndiv = int(np.asarray(mcmc.get_extra_fields().get("diverging", np.zeros(1))).sum())
    conv = dict(max_rhat=float(np.nanmax(rh)), min_ess=float(np.nanmin(es)),
                div_frac=float(ndiv / (samples * chains)), n_pairs=len(pairs))
    conv["converged"] = bool(conv["max_rhat"] <= 1.05 and conv["min_ess"] >= 200 and conv["div_frac"] < 0.02)
    return mcmc.get_samples(group_by_chain=False), conv


def fk_samples(P, k, theta_draws):
    SEk = np.stack([P["se"][g][k] for g in P["groups"]], 0)            # (G,)
    lam = P["lam0"][k] * (1.0 + theta_draws @ (SEk) - SEk.sum())       # theta-1 dot SEk
    return np.sqrt(np.maximum(lam, 1e-6)) / (2 * np.pi)


def score_freq(P, h, post, n_draws=400, seed=1):
    pairs = match_pairs(P, h)
    if not pairs:
        return None
    th = np.asarray(post["theta"]); sf = np.asarray(post["sigma_f"])
    idx = np.linspace(0, th.shape[0] - 1, min(th.shape[0], n_draws)).astype(int)
    rng = np.random.default_rng(seed)
    pooled = np.array([fm for loc in [l for l in HELD if l != h] for fm in P["mpk"][loc]])  # climatology ensemble
    crps_t, crps_c, iv, cov, z, dfp, dfn, df_clim = [], [], [], [], [], [], [], []
    for (f_m, k, f_nom) in pairs:
        fk = fk_samples(P, k, th[idx])                                  # (S,)
        pred = fk * np.exp(rng.normal(0, sf[idx]))
        st = SC.score_qoi(pred, f_m)
        crps_t.append(st["crps"]); iv.append(st["interval_score"]); cov.append(st["covered"]); z.append(st["z"])
        crps_c.append(SC.crps_sample(pooled, f_m))
        dfp.append(abs(np.median(pred) - f_m) / f_m * 100)              # calibrated twin |df|%
        dfn.append(abs(f_nom - f_m) / f_m * 100)                        # nominal FEM |df|%
        df_clim.append(abs(pooled[np.argmin(np.abs(pooled - f_m))] - f_m) / f_m * 100)  # nearest pooled peak |df|%
    ct, cc = float(np.mean(crps_t)), float(np.mean(crps_c))
    return {"n_peaks": len(pairs), "twin_crps": ct, "clim_crps_pooled": cc,
            "crps_skill_vs_clim_pooled": float(1 - ct / max(cc, 1e-9)),
            "twin_interval": float(np.mean(iv)), "twin_coverage": float(np.mean(cov)), "z_mean": float(np.mean(z)),
            "twin_median_df_pct": float(np.median(dfp)), "nominal_fem_median_df_pct": float(np.median(dfn)),
            "nearest_pooled_peak_median_df_pct": float(np.median(df_clim))}


if __name__ == "__main__":
    P = precompute()
    print(f"kept {len(P['freqs'])} FEM modes <= {FMAX_KEEP} Hz")
    for loc in (HELD + ["shield"]):
        pk = P["mpk"][loc]; al = alive_modes(P, loc); pr = match_pairs(P, loc)
        errs = [abs(a - b) / a * 100 for a, _, b in pr]
        print(f"{loc:10s} meas peaks({len(pk)})={[round(x,1) for x in pk]}")
        print(f"           alive FEM modes={al.size}; matched {len(pr)}/{len(pk)} "
              f"median |df|={np.median(errs):.1f}% " if pr else f"           alive={al.size}; matched 0")
