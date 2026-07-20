#!/usr/bin/env python3
"""Q + H legs for finalists (card §4.3): net-CG statFEM F(k) 95% bands (netcg conventions, reusing
netcg_qoi's octave smoothing / coverage / grms READ-ONLY) + the leave-modes-out honesty audit.

Q: per-drive net-CG shear/normal band vs the measured-FRF answer key on each dev drive (rmodel answer_key
   pattern — LSQ participation lives ONLY inside the answer-key truth reconstruction, never in selection).
H: hide the top-3 QOI-driving MEASURED modes -> statFEM F(k) band must WIDEN (ratio > 1.0 = honest;
   1.00 = structurally overconfident = disqualified). Writes out/qoi_<cid>.json + out/honesty_<cid>.json.
"""
from __future__ import annotations
import json, os, sys
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import femlib as F

import score as SC              # OUR scorer (import BEFORE foreign paths shadow 'score.py')

NETCG_CODE = os.path.join(F.ROOT, "artifacts/reports/shocksat_netcg_method_selection_20260701/code")
PSD_CODE = os.path.join(F.ROOT, "artifacts/reports/shocksat_psd_envelope_twin_20260623/code")
sys.path.insert(0, PSD_CODE)
sys.path.insert(0, NETCG_CODE)
import netcg_qoi as NC          # octave_smooth, coverage_vs_truth, grms, FGRID, tier sigmas (read-only)

WS = F.WS
FGRID = NC.FGRID
SD_F_M, SD_A_M, SD_F_U, SD_A_U = NC.SD_F_M, NC.SD_A_M, NC.SD_F_U, NC.SD_A_U
AXES = {0: "shear_X", 1: "shear_Y", 2: "normal_Z"}


class QPack:
    """netcg-convention QOI forward on a candidate Package (own basis)."""

    def __init__(self, cid):
        self.pkg = F.Package.load(cid)
        f1, _ = self.pkg.modes(np.ones(len(self.pkg.free_names)))
        self.inb = np.where((f1 >= F.BAND[0]) & (f1 <= F.BAND[1]))[0]
        self.nM = len(self.inb)
        pairs = np.asarray(self.pkg.pairs)
        femk = pairs[:, 1].astype(int)
        self.is_meas = np.isin(self.inb, femk)
        m2f = {int(k): float(np.asarray(self.pkg.mfreqs)[int(r)]) for r, k, _ in pairs}
        self.meas_f = np.array([m2f.get(int(k), f1[k]) for k in self.inb])

    def coef(self, theta, axis, dkey):
        f, Q = self.pkg.modes(theta)
        fi = f[self.inb]
        g = np.asarray(self.pkg.tray)[axis] @ Q[:, self.inb]
        phid = np.asarray(self.pkg.drives[dkey]) @ Q[:, self.inb] if dkey else np.ones(self.nM)
        return g * phid, fi

    def spectrum(self, theta, axis, dkey=None, amp=None, fscale=None):
        coef, fi = self.coef(theta, axis, dkey)
        if fscale is not None:
            fi = fi * fscale
        if amp is not None:
            coef = coef * amp
        wi = 2 * np.pi * fi; w = 2 * np.pi * FGRID
        D = wi[:, None] ** 2 - w[None, :] ** 2 + 2j * F.ZETA * wi[:, None] * w[None, :]
        return np.abs(((coef[:, None] * wi[:, None] ** 2) / D).sum(0))

    def unmeas_frac(self, theta, axis, dkey, hidden=None):
        coef, fi = self.coef(theta, axis, dkey)
        wi = 2 * np.pi * fi; w = 2 * np.pi * FGRID
        D = wi[:, None] ** 2 - w[None, :] ** 2 + 2j * F.ZETA * wi[:, None] * w[None, :]
        contrib = np.abs((coef[:, None] * wi[:, None] ** 2) / D)
        meas = self.is_meas.copy()
        if hidden is not None:
            meas[np.asarray(hidden)] = False
        return contrib[~meas].sum(0) / (contrib.sum(0) + 1e-300)


def statfem_fk_band(qp, theta_post, axis, dkey, hidden=None, n_theta=48, n_disc=30, seed=0):
    rng = np.random.default_rng(seed)
    idx = np.linspace(0, len(theta_post) - 1, min(n_theta, len(theta_post))).astype(int)
    specs = []
    for s in idx:
        th = theta_post[s]
        base = qp.spectrum(th, axis, dkey)
        marg = 0.25 + (SD_A_U - 0.25) * qp.unmeas_frac(th, axis, dkey, hidden=hidden)
        for _ in range(n_disc):
            zc = np.log(NC.octave_smooth(FGRID, np.exp(rng.normal(0, 1, len(FGRID))), 1.0))
            zc = (zc - zc.mean()) / (zc.std() + 1e-9)
            specs.append(base * np.exp(marg * zc))
    E = np.array(specs)
    return np.percentile(E, 2.5, 0), np.percentile(E, 50, 0), np.percentile(E, 97.5, 0)


def answer_key(qp, theta_map, axis, dkey, ridge=1e-3):
    """Truth reconstruction from the drive's OWN measured FRFs (rmodel pattern; the ONLY place LSQ lives)."""
    c = SC.load_caches()[dkey]
    f, Q = qp.pkg.modes(theta_map)
    rows_of = {d: i for i, d in enumerate(qp.pkg.sens_daq)}
    common = [d for d in c["daq"] if d in rows_of]
    srows = np.asarray(qp.pkg.sens_rows)[[rows_of[d] for d in common]] @ Q[:, qp.inb]
    H1 = np.array([c["H1"][c["daq"].index(d)] for d in common])
    fc = c["freqs"]; wc = 2 * np.pi * fc
    mi = np.where(qp.is_meas)[0]
    fi = qp.meas_f[mi]; wi = 2 * np.pi * fi
    D = wi[:, None] ** 2 - wc[None, :] ** 2 + 2j * F.ZETA * wi[:, None] * wc[None, :]
    phid = np.asarray(qp.pkg.drives[dkey]) @ Q[:, qp.inb]
    basis = (-(wc[None, :, None] ** 2)) * (srows[:, None, mi] * phid[mi][None, None, :]) / D.T[None, :, :]
    Amat = basis.reshape(-1, len(mi)); b = H1.reshape(-1)
    AhA = Amat.conj().T @ Amat + ridge * np.eye(len(mi)) * \
        (np.real(np.trace(Amat.conj().T @ Amat)) / len(mi))
    a = np.linalg.solve(AhA, Amat.conj().T @ b)
    g = np.asarray(qp.pkg.tray)[axis] @ Q[:, qp.inb]
    coefk = a * g[mi] * phid[mi]
    w = 2 * np.pi * FGRID
    Dq = wi[:, None] ** 2 - w[None, :] ** 2 + 2j * F.ZETA * wi[:, None] * w[None, :]
    return np.abs(((coefk[:, None] * wi[:, None] ** 2) / Dq).sum(0)), len(common)


def run_q_h(cid):
    qp = QPack(cid)
    z = np.load(os.path.join(WS, "data", f"theta_post_{cid}.npz"), allow_pickle=True)
    post = np.asarray(z["theta_post"])
    theta_map = np.median(post, 0)
    qout = {"cid": cid, "axes": {}, "convention": "netcg statFEM F(k); coverage hard gate >=0.95 wtd, "
                                                  "<=0.5 dB energy-wtd exceedance; per-drive answer keys"}
    for axis, name in AXES.items():
        per_drive = []
        for dkey in F.DRIVE_KEYS:
            ans, ncmn = answer_key(qp, theta_map, axis, dkey)
            lo, med, hi = statfem_fk_band(qp, post, axis, dkey)
            gain = NC.grms(NC.octave_smooth(FGRID, ans)) / (NC.grms(NC.octave_smooth(FGRID, med)) + 1e-300)
            cov = NC.coverage_vs_truth(lo * gain, hi * gain, ans[None, :], FGRID)
            per_drive.append({"drive": dkey, "coverage": cov["weighted_coverage"],
                              "exceed_dB": cov["energy_wtd_pos_dB_exceed"], "n_ch": ncmn})
        # sharpness vs FEM+6dB (flat modal drive, netcg sharpness ref)
        lo0, med0, hi0 = statfem_fk_band(qp, post, axis, None)
        tr_ens = truth_bandwidth_ref(qp, theta_map, axis)
        sharp = NC.grms(hi0 - lo0) / (tr_ens + 1e-300)
        qout["axes"][name] = {"per_drive": per_drive,
                              "min_coverage": min(d["coverage"] for d in per_drive),
                              "max_exceed_dB": max(d["exceed_dB"] for d in per_drive),
                              "band_over_fem6db": round(float(sharp), 3)}
    json.dump(qout, open(os.path.join(WS, "out", f"qoi_{cid}.json"), "w"), indent=1)
    # H: leave-modes-out (hide top-3 measured QOI drivers on the normal axis + shear)
    hout = {"cid": cid}
    ratios = []
    for axis, name in AXES.items():
        contrib = qp.spectrum(theta_map, axis)                     # reference
        mi = np.where(qp.is_meas)[0]
        scores = []
        for j in mi:
            amp = np.ones(qp.nM); amp[j] = 0.0
            scores.append((float(np.abs(qp.spectrum(theta_map, axis, amp=amp) - contrib).sum()), int(j)))
        top3 = [j for _, j in sorted(scores, reverse=True)[:3]]
        lo0, _, hi0 = statfem_fk_band(qp, post, axis, None)
        loH, _, hiH = statfem_fk_band(qp, post, axis, None, hidden=top3)
        r = float(NC.grms(np.log(hiH / loH)) / (NC.grms(np.log(hi0 / lo0)) + 1e-300))
        hout[name] = {"hidden_modes_inb_idx": top3, "widen_ratio": round(r, 4)}
        ratios.append(r)
    hout["lmo_widen_ratio"] = round(float(min(ratios)), 4)         # worst axis governs (checker reads this)
    json.dump(hout, open(os.path.join(WS, "out", f"honesty_{cid}.json"), "w"), indent=1)
    print(json.dumps({"qoi": {k: {kk: vv for kk, vv in v.items() if kk != "per_drive"}
                              for k, v in qout["axes"].items()},
                      "honesty": hout}, indent=1))


def truth_bandwidth_ref(qp, theta_map, axis):
    """FEM+6dB reference bandwidth (netcg sharpness denominator): log-band of x2 around the median."""
    med = qp.spectrum(theta_map, axis)
    return NC.grms(med * (10 ** 0.3) - med / (10 ** 0.3))


if __name__ == "__main__":
    run_q_h(sys.argv[1])
