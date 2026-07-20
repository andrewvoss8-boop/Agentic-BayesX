#!/usr/bin/env python3
"""VALIDITY PROBE (D4): does the twin's 97.5%-band PSD envelope beat FEM+6 dB on GRMS at held-out sensors,
while enveloping the measured data? One split (default 90% training) on the CLEAN modal multi-reference set.

Twin = converged L5 modal-feature θ (calibrated from pooled observed modal frequencies) -> modal-superposition
accelerance at the held-out sensor for each reference drive, scaled by ONE training-global units-gain c, with a
broadband multiplicative amplitude discrepancy exp(N(0,σ)) (σ = MISALIGNMENT-FREE peak-height scatter on OBSERVED
channels — the band that makes it cover). FEM = θ=1 nominal, same gain, +6 dB. Damping = structural 1% + the
exp-window ζ_w(f) baked into the measured FRF (peak HEIGHTS comparable). PSD = |H|²·S_F0 (flat & common -> cancels).

fit_context() returns the shared fitted state (reused by fig_examples.py / MC). NO success claim (exploratory).
Output: out/probe_seed<seed>.json + console.
"""
from __future__ import annotations
import json, sys, time
from types import SimpleNamespace
from pathlib import Path
import numpy as np
from scipy.signal import find_peaks

sys.path.insert(0, str(Path(__file__).resolve().parent))
import realfrf as rf
import modal_feature as mf
import psd_forward as pf
import psd_envelope as pe
import multiref_frf as mr
from modal_multiref import MODAL_REFS, CACHE, N_MODAL

WS = Path(__file__).resolve().parent.parent
OUT = WS / "out"; OUT.mkdir(exist_ok=True)
S_F0 = 1.0
ZSTRUCT = 0.01
COMBINED_REFS = ["m_xpos_990x", "m_zpos_990z", "m_zpos_900z"]   # independent drive DOFs (avoid +XY/+X double count)
EXC_ENERGY_OK = 0.02                                          # clean cover = <2% of data band-energy exceeds


def zeta_eff(freqs):
    tau = -(N_MODAL - 1) / (rf.FS * np.log(mr.PROC["exp_end"]))
    return ZSTRUCT + 1.0 / (2 * np.pi * np.asarray(freqs, float) * tau)


def load_caches():
    out = {}
    for key in MODAL_REFS:
        z = np.load(CACHE / f"{key}.npz", allow_pickle=True)
        out[key] = {"freqs": z["freqs"], "H1": z["H1"], "daq": [int(d) for d in z["daq"]],
                    "xyz": tuple(float(x) for x in z["xyz"]), "axis": str(z["axis"])}
    return out


def meas_dict(c):
    H = c["H1"]
    dr = [float(np.abs(H[k]).max() ** 2 / (np.percentile(np.abs(H[k]) ** 2, 25) + 1e-300)) for k in range(H.shape[0])]
    return {"freqs": c["freqs"], "H": H, "daq": c["daq"], "dyn_range": np.array(dr)}


def model_H(ctx, theta_batch, drive_keys, resp_row):
    """Coherent (complex) sum over drive_keys of the modal-superposition accelerance for resp_row. (M,Nf)."""
    Hs = [pf.forward_H_batch(ctx.R, ctx.freqs, theta_batch, ctx.drows[k], resp_row[None, :], ctx.eta)[:, :, 0]
          for k in drive_keys]
    return pf.combined_H(Hs)


def meas_H(ctx, drive_keys, daq):
    Hs = []
    for k in drive_keys:
        c = ctx.caches[k]; Hs.append(c["H1"][c["daq"].index(daq)])
    return pf.combined_H(Hs)


def twin_psd_draws(ctx, drive_keys, daq):
    """Twin predictive PSD draws (M,Nf): |model(θ)·exp(gain)·exp(ε)|²·S_F0, ε~N(0,σ) broadband amplitude disc."""
    resp_row = ctx.ch.rows[ctx.pos[daq]]
    eps = np.random.default_rng(ctx.seed + 1000 + daq).normal(0, ctx.sig, len(ctx.thsub))
    H = np.abs(model_H(ctx, ctx.thsub, drive_keys, resp_row)) * np.exp(ctx.gain) * np.exp(eps)[:, None]
    return (H ** 2) * S_F0


def fem_psd(ctx, drive_keys, daq):
    return (np.abs(model_H(ctx, np.ones((1, 9)), drive_keys, ctx.ch.rows[ctx.pos[daq]])[0]) * np.exp(ctx.gain)) ** 2 * S_F0


def data_psd(ctx, drive_keys, daq):
    return (np.abs(meas_H(ctx, drive_keys, daq)) ** 2) * S_F0


def fit_context(seed=0, obs_frac=0.9, n_draws=300, warmup=800, samples=800, chains=4):
    R = rf.load_reduced()
    caches = load_caches()
    freqs = caches[COMBINED_REFS[0]]["freqs"]
    eta = zeta_eff(freqs)
    ch = rf.build_channels(R, [d for d in range(1, rf.N_ACCEL_RECORDERS + 1) if d not in rf.BAD_DAQ])
    common = set(ch.daq)
    for c in caches.values():
        common &= set(c["daq"])
    daq_master = [d for d in ch.daq if d in common]
    pos = {d: i for i, d in enumerate(ch.daq)}
    rng = np.random.default_rng(seed); perm = rng.permutation(len(daq_master))
    n_obs = int(round(obs_frac * len(daq_master)))
    obs_daqs = sorted(daq_master[i] for i in perm[:n_obs])
    ho_daqs = sorted(daq_master[i] for i in perm[n_obs:])
    drows = {key: pf.drive_row_for(R, c["xyz"], c["axis"]) for key, c in caches.items()}

    pooled = {}
    for key, c in caches.items():
        fq, _ = mf.extract_measured_modes(meas_dict(c), SimpleNamespace(daq=obs_daqs))
        for j, hz in mf.match(R, fq)[0]:
            pooled.setdefault(int(j), []).append(float(hz))
    obs_mode_idx = sorted(pooled)
    obs_w = np.array([np.median(pooled[j]) for j in obs_mode_idx])
    theta_post, _, diag = mf.calibrate_modal(R, np.array(obs_mode_idx), obs_w,
                                             seed=seed + 7, warmup=warmup, samples=samples, chains=chains)
    sub = np.linspace(0, theta_post.shape[0] - 1, min(theta_post.shape[0], n_draws)).astype(int)
    ctx = SimpleNamespace(R=R, caches=caches, freqs=freqs, eta=eta, ch=ch, pos=pos, drows=drows,
                          daq_master=daq_master, obs_daqs=obs_daqs, ho_daqs=ho_daqs, seed=seed,
                          theta_post=theta_post, thsub=theta_post[sub], diag=diag, obs_mode_idx=obs_mode_idx)

    # gain + amplitude discrepancy from MISALIGNMENT-FREE peak heights (calibrated model local-max within ±5 Hz)
    thmed = np.median(theta_post, axis=0)[None, :]
    df = float(freqs[1] - freqs[0]); tol = max(1, int(round(5.0 / df)))
    pr = []
    for key in caches:
        for d in obs_daqs:
            lm = np.log(np.abs(meas_H(ctx, [key], d)) + 1e-300)
            lf = np.log(np.abs(model_H(ctx, thmed, [key], ch.rows[pos[d]])[0]) + 1e-300)
            pk, _ = find_peaks(lm, prominence=0.3, distance=tol)
            for i in pk:
                lo, hi = max(0, i - tol), min(len(freqs), i + tol + 1)
                pr.append(float(lm[i] - np.max(lf[lo:hi])))
    pr = np.array(pr)
    ctx.gain = float(np.median(pr)); ctx.sig = float(np.std(pr - ctx.gain))
    return ctx


def score_case(ctx, drive_keys, daq):
    twin975 = np.percentile(twin_psd_draws(ctx, drive_keys, daq), 97.5, axis=0)
    env_twin = pe.smoothline_envelope(ctx.freqs, twin975)
    env_fem6 = pe.smoothline_envelope(ctx.freqs, pe.add_db_psd(fem_psd(ctx, drive_keys, daq), 6.0))
    dp = data_psd(ctx, drive_keys, daq)
    g_twin, g_fem6 = pe.grms(ctx.freqs, env_twin), pe.grms(ctx.freqs, env_fem6)
    et, ef = pe.exceedance(ctx.freqs, dp, env_twin), pe.exceedance(ctx.freqs, dp, env_fem6)
    return {"daq": int(daq), "grms_twin_env": g_twin, "grms_fem6_env": g_fem6, "grms_ratio": g_twin / g_fem6,
            "twin_below_fem6": bool(g_twin < g_fem6), "twin_max_exc_db": et["max_exceedance_db_positive"],
            "twin_exc_energy_frac": et["exceeding_energy_fraction"], "fem6_max_exc_db": ef["max_exceedance_db_positive"],
            "fem6_exc_energy_frac": ef["exceeding_energy_fraction"],
            "clean_win": bool(g_twin < g_fem6 and et["exceeding_energy_fraction"] < EXC_ENERGY_OK)}


def run(seed=0, obs_frac=0.9, write=True):
    t0 = time.time()
    ctx = fit_context(seed=seed, obs_frac=obs_frac)
    cases = {key: [score_case(ctx, [key], d) for d in ctx.ho_daqs] for key in ctx.caches}
    cases["combined_correlated"] = [score_case(ctx, COMBINED_REFS, d) for d in ctx.ho_daqs]

    def agg(rows):
        return {"n": len(rows), "median_grms_ratio": float(np.median([x["grms_ratio"] for x in rows])),
                "win_rate_grms": float(np.mean([x["twin_below_fem6"] for x in rows])),
                "clean_win_rate": float(np.mean([x["clean_win"] for x in rows])),
                "median_twin_exc_energy_frac": float(np.median([x["twin_exc_energy_frac"] for x in rows])),
                "median_twin_max_exc_db": float(np.median([x["twin_max_exc_db"] for x in rows])),
                "median_fem6_exc_energy_frac": float(np.median([x["fem6_exc_energy_frac"] for x in rows]))}

    rec = {"deliverable": "VALIDITY PROBE: twin 97.5% PSD-envelope GRMS vs FEM+6dB, clean modal multi-ref",
           "seed": seed, "obs_frac": obs_frac, "n_sensors": len(ctx.daq_master),
           "n_obs": len(ctx.obs_daqs), "n_heldout": len(ctx.ho_daqs),
           "calib": {"n_pooled_modes": len(ctx.obs_mode_idx), **ctx.diag},
           "units_gain_log": ctx.gain, "amplitude_discrepancy_sigma_log": ctx.sig,
           "sigma_implies_975_band_PSD_dB": float(10 * np.log10(np.exp(2 * 1.96 * ctx.sig))),
           "per_reference": {key: agg(cases[key]) for key in ctx.caches},
           "combined_correlated": agg(cases["combined_correlated"]),
           "detail": cases, "runtime_s": round(time.time() - t0, 1),
           "note": "exploratory; YELLOW by default; no success claim. eta=struct1%+window."}
    if write:
        (OUT / f"probe_seed{seed:02d}.json").write_text(json.dumps(rec, indent=2))
    print(f"PROBE seed{seed} obs_frac{obs_frac}: {len(ctx.obs_daqs)} obs / {len(ctx.ho_daqs)} held-out sensors")
    print(f"  calib: {len(ctx.obs_mode_idx)} pooled modes, converged={ctx.diag['converged']} "
          f"(R-hat {ctx.diag['max_rhat']:.3f}, ESS {ctx.diag['min_ess']:.0f}, div {ctx.diag['divergences']})")
    print(f"  units-gain(log) {ctx.gain:+.2f}; amplitude discrepancy sigma {ctx.sig:.2f} "
          f"=> twin 97.5 band ~+{rec['sigma_implies_975_band_PSD_dB']:.1f} dB in PSD (FEM+6dB bar = +6 dB)")
    for key in list(ctx.caches) + ["combined_correlated"]:
        a = rec["per_reference"][key] if key in ctx.caches else rec["combined_correlated"]
        print(f"  {key:20s}: median GRMS ratio {a['median_grms_ratio']:.2f}  win {a['win_rate_grms']*100:.0f}%  "
              f"clean-win {a['clean_win_rate']*100:.0f}%  (twin exceed-energy {a['median_twin_exc_energy_frac']:.3f})")
    print(f"  runtime {rec['runtime_s']}s")
    return rec


if __name__ == "__main__":
    seed = int(sys.argv[1]) if len(sys.argv) > 1 else 0
    of = float(sys.argv[2]) if len(sys.argv) > 2 else 0.9
    run(seed=seed, obs_frac=of)
