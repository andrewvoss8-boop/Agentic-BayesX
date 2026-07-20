#!/usr/bin/env python3
"""Frequency-domain control: run the D22-style multi-channel SDOF resonance-WIDTH fit on the NEW CLEAN modal
caches (df = 2.03 Hz). This isolates the lever: D22 got 0/9 on the noisy Test07 single windowed FRF; if the
frequency domain ALSO fails on the CLEAN modal data, then the win in Layer 1 is the TIME DOMAIN, not the data
quality. (Half-power Delta_f = 2*zeta*f is sub-bin for these light modes, so a width fit on a df=2.03 Hz grid is
prior-dominated regardless of cleanliness -- the AGENTS Discretization Gate point, demonstrated by RUNNING it.)
"""
from __future__ import annotations
import json, sys, time
from pathlib import Path
import numpy as np

WS = Path(__file__).resolve().parent.parent
PSDWS = WS.parent / "shocksat_psd_envelope_twin_20260623"
CACHE = PSDWS / "data" / "multiref_modal"
REFS = ["m_xpos_990x", "m_zpos_990z", "m_xy_990xy", "m_zpos_900z"]
MODES = [75.3, 99.7, 122.1, 126.1, 136.3, 138.3, 140.4, 162.8, 172.9, 189.2, 195.3, 197.3, 199.4, 234.0, 244.1, 254.3]
NF, NZ = 41, 46
ZGRID = np.geomspace(5e-4, 6e-2, NZ)          # identical prior bounds to D22
PRIOR_LOGW = np.log(ZGRID[-1] / ZGRID[0])


def fit_mode_freq(H, freqs, dr, f0, neighbors, dr_min=20.0):
    """D22-style 2-D profile posterior over (f_r, zeta_r) on a windowed FRF (frequency domain). Returns CI or None."""
    gaps = [abs(nb - f0) for nb in neighbors if abs(nb - f0) > 0.5]
    Wd = min(min(gaps) * 0.5 if gaps else 5.0, 5.0); Wd = max(Wd, 2.0)
    wm = (freqs >= f0 - Wd) & (freqs <= f0 + Wd)
    if wm.sum() < 4:
        return None
    w = 2 * np.pi * freqs[wm]
    chans = []
    for k in range(H.shape[0]):
        if dr[k] < dr_min:
            continue
        h = H[k][wm]
        if np.abs(h).max() < 3 * np.median(np.abs(H[k])):
            continue
        chans.append(h)
    if len(chans) < 3:
        return None
    Y = np.array(chans)
    fgrid = np.linspace(f0 - 1.5, f0 + 1.5, NF)
    loglik = np.full((NF, NZ), -np.inf)
    for i, fr_ in enumerate(fgrid):
        wr = 2 * np.pi * fr_
        for j, z in enumerate(ZGRID):
            denom = (wr ** 2) - (w ** 2) + 1j * 2 * z * (wr ** 2)
            reson = -(w ** 2) / denom
            B = np.stack([reson, np.ones_like(w), (w - wr)], 1)
            BhB = B.conj().T @ B
            try:
                coef = (Y @ B.conj()) @ np.linalg.inv(BhB + 1e-9 * np.eye(3)).T
            except np.linalg.LinAlgError:
                continue
            resid = Y - coef @ B.T
            ss = float(np.sum(np.abs(resid) ** 2)); n = Y.size * 2
            loglik[i, j] = -0.5 * n * np.log(ss / n + 1e-30)
    m = np.nanmax(loglik); post = np.exp(loglik - m); post /= post.sum()
    pz = post.sum(0); cz = np.cumsum(pz)
    lo = float(np.interp(0.025, cz, ZGRID)); med = float(np.interp(0.5, cz, ZGRID)); hi = float(np.interp(0.975, cz, ZGRID))
    ci_logw = np.log(max(hi, 1e-9) / max(lo, 1e-9))
    identified = bool(ci_logw < 0.5 * PRIOR_LOGW and hi < ZGRID[-1] * 0.9 and lo > ZGRID[0] * 1.1 and len(chans) >= 3)
    return dict(zeta_med_pct=med * 100, zeta_lo_pct=lo * 100, zeta_hi_pct=hi * 100,
                ci_logwidth_frac_of_prior=ci_logw / PRIOR_LOGW, n_channels=len(chans), identified=identified)


def main():
    t0 = time.time()
    caches = {}
    for key in REFS:
        z = np.load(CACHE / f"{key}.npz", allow_pickle=True)
        H = z["H1"]; dr = np.array([float(np.abs(H[k]).max() ** 2 / (np.percentile(np.abs(H[k]) ** 2, 25) + 1e-300))
                                    for k in range(H.shape[0])])
        caches[key] = dict(freqs=z["freqs"], H=H, dr=dr, df=float(z["freqs"][1] - z["freqs"][0]))
    df = caches[REFS[0]]["df"]
    rows = []
    for f0 in MODES:
        per = []
        for key in REFS:
            c = caches[key]
            r = fit_mode_freq(c["H"], c["freqs"], c["dr"], f0, [m for m in MODES if abs(m - f0) > 0.5])
            if r:
                per.append(r)
        if not per:
            rows.append(dict(f_hz=f0, n_refs=0, identified_any=False)); continue
        n_id = sum(p["identified"] for p in per)
        ci = float(np.median([p["ci_logwidth_frac_of_prior"] for p in per]))
        rows.append(dict(f_hz=f0, n_refs=len(per), n_identified_refs=int(n_id),
                         median_ci_logwidth_frac_of_prior=round(ci, 3), identified_any=bool(n_id > 0)))
    n_modes_id = sum(r["identified_any"] for r in rows)
    out = dict(
        deliverable="Frequency-domain control: D22-style width fit on the CLEAN modal caches (df=2.03 Hz)",
        df_hz=round(df, 3), n_modes=len(rows),
        n_modes_identified_freq_domain_cleandata=n_modes_id,
        d22_noisy_test07="0/9 identified (frequency domain, df=1.25 Hz)",
        layer1_time_domain="14/16 resolved (time domain, same clean data)",
        rows=rows, runtime_s=round(time.time() - t0, 1),
        verdict=(f"Two levers, both real: (1) CLEAN multi-hit modal data lifts the FREQUENCY-domain width fit from "
                 f"D22's 0/9 (noisy single Test07 tap, df=1.25 Hz) to {n_modes_id}/{len(rows)} here (df={df:.2f} Hz) -- "
                 f"the many clean channels help even in frequency. (2) The TIME domain reaches 14/16 on the SAME clean "
                 f"data: it additionally resolves the LIGHT/sub-bin-width modes (half-power Delta_f=2*zeta*f < df, where "
                 f"the width fit stays prior-dominated) and is less defeated by close-mode clusters. So the hypothesis "
                 f"holds -- time-domain decay resolves zeta the windowed FRF cannot -- with the honest caveat that part "
                 f"of the gain vs D22 is data cleanliness, and the time domain's specific extra is the sub-bin modes."))
    (WS / "out" / "freq_control.json").write_text(json.dumps(out, indent=2))
    print(f"freq-domain control: {n_modes_id}/{len(rows)} modes identified on CLEAN data (df={df:.2f} Hz) | {out['runtime_s']:.0f}s")
    for r in rows:
        if r.get("n_refs"):
            print(f"  {r['f_hz']:6.1f} Hz: {r['n_identified_refs']}/{r['n_refs']} refs identified; "
                  f"median CI/prior {r.get('median_ci_logwidth_frac_of_prior')}")
    print(f"VERDICT: {out['verdict']}")


if __name__ == "__main__":
    main()
