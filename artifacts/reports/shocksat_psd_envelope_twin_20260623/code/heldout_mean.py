#!/usr/bin/env python3
"""HELD-OUT MEAN check (Andrew): does a CORRELATED FEM cover a held-out location at a SMALLER *validated* margin
than the un-updated FEM? Non-circular: the margin is set on OBSERVED sensors, then applied to HELD-OUT.

Per split (leave-sensors-out): calibrate theta on OBSERVED modal frequencies (reduced model); each model gets its
own global gain fit on observed. Build the structure-level max-envelope over OBSERVED, set the margin each model
needs to envelope the OBSERVED measured max-env (the 'validated margin'), APPLY it to the model's HELD-OUT max-env,
and check (a) does it cover the held-out measured max-env (generalization), (b) GRMS at that margin.
  correlated = calibrated freq (theta_med) + measured-effective damping
  un-updated = theta=1 + nominal 1% damping
Reference +X. Sweeps a few seeds/fractions. Output: out/heldout_mean.json + console.
"""
from __future__ import annotations
import json, sys
from pathlib import Path
import numpy as np
sys.path.insert(0, str(Path(__file__).resolve().parent))
import probe as P
import psd_forward as pf
import psd_envelope as pe

WS = Path(__file__).resolve().parent.parent
REF = "m_xpos_990x"


def split_eval(ctx):
    f = ctx.freqs; drow = ctx.drows[REF]; c = ctx.caches[REF]
    common = ctx.daq_master; cidx = {d: c["daq"].index(d) for d in common}
    rows = np.array([ctx.ch.rows[ctx.pos[d]] for d in common])         # (Nc,74)
    Hmeas = np.array([np.abs(c["H1"][cidx[d]]) for d in common])       # (Nc,Nf)
    obs = [common.index(d) for d in ctx.obs_daqs if d in common]
    ho = [common.index(d) for d in ctx.ho_daqs if d in common]
    tau = -(122880 - 1) / (250000.0 * np.log(0.05))
    eta_nom = 2.0 * (0.01 + 1.0 / (2 * np.pi * f * tau))
    th_med = np.median(ctx.theta_post, axis=0)[None, :]
    out = {}
    for name, theta, eta in [("correlated", th_med, ctx.eta), ("un_updated", np.ones((1, 9)), eta_nom)]:
        Hm = np.abs(pf.forward_H_batch(ctx.R, f, theta, drow, rows, eta)[0])        # (Nf,Nc)
        gain = np.median(np.log(Hmeas[obs].T + 1e-30) - np.log(Hm[:, obs] + 1e-30)) # gain fit on OBSERVED
        psd = (Hm * np.exp(gain)) ** 2                                              # (Nf,Nc)
        env_obs = pe.smoothline_envelope(f, psd[:, obs].max(1))
        env_ho = pe.smoothline_envelope(f, psd[:, ho].max(1))
        meas_obs = pe.smoothline_envelope(f, (Hmeas[obs].T ** 2).max(1))
        meas_ho = pe.smoothline_envelope(f, (Hmeas[ho].T ** 2).max(1))
        margin = max(0.0, float(np.max(10 * np.log10(np.maximum(meas_obs, 1e-300) / np.maximum(env_obs, 1e-300)))))
        spec_ho = pe.add_db_psd(env_ho, margin)                                     # validated margin applied to held-out
        exc = pe.exceedance(f, meas_ho, spec_ho)["exceeding_energy_fraction"]
        out[name] = {"validated_margin_dB": round(margin, 2), "GRMS_heldout_spec": round(pe.grms(f, spec_ho), 3),
                     "heldout_exceed_energy": round(exc, 4), "covers_heldout": bool(exc < 0.02)}
    return out


def run():
    rows = []
    for seed in (0, 1):
        for of in (0.7, 0.9):
            ctx = P.fit_context(seed=seed, obs_frac=of, warmup=500, samples=500)
            r = split_eval(ctx); r["seed"] = seed; r["obs_frac"] = of; r["calib_conv"] = bool(ctx.diag["converged"])
            rows.append(r)
            cc, un = r["correlated"], r["un_updated"]
            print(f"seed{seed} f{of}: CORR margin {cc['validated_margin_dB']:.1f}dB GRMS {cc['GRMS_heldout_spec']:.1f} "
                  f"cover {cc['covers_heldout']} | UN-UPD margin {un['validated_margin_dB']:.1f}dB GRMS "
                  f"{un['GRMS_heldout_spec']:.1f} cover {un['covers_heldout']}")
    cg = np.mean([r["correlated"]["GRMS_heldout_spec"] for r in rows])
    ug = np.mean([r["un_updated"]["GRMS_heldout_spec"] for r in rows])
    cc = np.mean([r["correlated"]["covers_heldout"] for r in rows])
    uc = np.mean([r["un_updated"]["covers_heldout"] for r in rows])
    summ = {"mean_GRMS_correlated": round(float(cg), 2), "mean_GRMS_un_updated": round(float(ug), 2),
            "GRMS_ratio_corr_over_unupd": round(float(cg / ug), 3),
            "cover_rate_correlated": round(float(cc), 2), "cover_rate_un_updated": round(float(uc), 2),
            "verdict": ("correlated covers held-out at LOWER GRMS" if cg < ug and cc >= uc
                        else "no twin advantage on held-out mean spec"),
            "splits": rows}
    (WS / "out" / "heldout_mean.json").write_text(json.dumps(summ, indent=2))
    print(f"\nMEAN held-out spec GRMS: correlated {cg:.1f} vs un-updated {ug:.1f} (ratio {cg/ug:.2f}); "
          f"cover-rate corr {cc:.2f} / un-upd {uc:.2f}")
    print(f"VERDICT: {summ['verdict']}")
    return summ


if __name__ == "__main__":
    run()
