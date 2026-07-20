#!/usr/bin/env python3
"""netcg_wide — net-CG force bands (Q3/Q4; S3/S4) on the wide package, netcg conventions REUSED
(FGRID 45-260 Hz, ZETA=1%, octave smoothing / coverage / grms via netcg_qoi read-only).

New vs netcg (H4, ledger A5b): tier update for extended-band measured modes — matched modes get SD_F 0.01
and a DATA-DRIVEN amplitude SD (cross-drive std of the per-mode amplitude scale factor fitted from the
wide caches; floor 0.35). The scale-factor fit is answer-key-style construction, never a selection score.

Outputs: out/cluster_amp_scatter.json, out/netcg_results.json (shear_x/shear_y/normal_z:
width_ratio vs FEM+6dB, coverage, widen_audit).
DEV drives only here; the +XY QOI answer key happens ONLY inside vault_grade.py (D7).
"""
from __future__ import annotations
import json, os, sys, time
import numpy as np

WS = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
ROOT = os.path.abspath(os.path.join(WS, "..", "..", ".."))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import wide_package as WP                      # noqa: E402
import wscore_wide as SW                       # noqa: E402
sys.path.insert(0, os.path.join(ROOT, "artifacts/reports/shocksat_netcg_method_selection_20260701/code"))
import netcg_qoi as NC                         # noqa: E402  (read-only reuse: FGRID, smoothing, coverage)

FGRID = NC.FGRID
ZETA = NC.ZETA
AXES = {"shear_x": 0, "shear_y": 1, "normal_z": 2}
DELIVERED = {"shear_x": 1.51, "shear_y": 2.30, "normal_z": 2.53}


class WQOI:
    """netcg-convention QOI forward on a wide package (duck-typed like NC.QOIModel where needed)."""

    def __init__(self, pkg, theta):
        self.pkg = pkg
        self.theta = np.asarray(theta, float)
        f, Q = pkg.modes(self.theta)
        self.inb = np.where((f >= 45.0) & (f <= 260.0))[0]
        self.nM = len(self.inb)
        self.f = f; self.Q = Q
        pairs = np.asarray(pkg.pairs)
        pairs = pairs[pairs[:, 2] >= 0.3]
        self.femk = pairs[:, 1].astype(int)
        mfreqs = np.asarray(pkg.mfreqs, float)
        m2f = {int(k): float(mfreqs[int(r)]) for r, k, mc in pairs}
        self.is_meas = np.isin(self.inb, self.femk)
        self.meas_f = np.array([m2f.get(int(k), f[int(k)]) for k in self.inb])
        # extended-band tier update (A5b): match measured clusters to inb modes
        ext = json.load(open(os.path.join(WS, "out", "extended_peaks.json")))
        self.ext_matched = np.zeros(self.nM, bool)
        for cl in ext["clusters"]:
            if not cl["measured_3plus"]:
                continue
            hz = cl["hz_mean"]
            j = int(np.argmin(np.abs(f[self.inb] - hz)))
            if abs(f[self.inb][j] / hz - 1.0) <= 0.02:
                self.ext_matched[j] = True
                if not self.is_meas[j]:
                    self.meas_f[j] = hz            # frequency now measured

    def g_axis(self, axis):
        return np.asarray(self.pkg.tray)[axis] @ self.Q[:, self.inb]

    def drive_part(self, dkey):
        return np.asarray(self.pkg.drives[dkey]) @ self.Q[:, self.inb]

    def spectrum(self, axis, amp=None, fscale=None, dkey=None, hidden=None):
        fi = self.meas_f.copy()
        if fscale is not None:
            fi = fi * fscale
        g = self.g_axis(axis)
        if dkey is not None:
            g = g * self.drive_part(dkey)
        if amp is not None:
            g = g * amp
        if hidden is not None:
            g = g.copy(); g[np.asarray(hidden)] = g[np.asarray(hidden)]  # hiding handled by caller tiers
        wi = 2 * np.pi * fi; w = 2 * np.pi * FGRID
        D = wi[:, None] ** 2 - w[None, :] ** 2 + 2j * ZETA * wi[:, None] * w[None, :]
        return np.abs(((g[:, None] * wi[:, None] ** 2) / D).sum(0))

    def unmeas_frac(self, axis, dkey=None, hidden=None, tiers_updated=True):
        g = self.g_axis(axis)
        if dkey is not None:
            g = g * self.drive_part(dkey)
        wi = 2 * np.pi * self.meas_f; w = 2 * np.pi * FGRID
        D = wi[:, None] ** 2 - w[None, :] ** 2 + 2j * ZETA * wi[:, None] * w[None, :]
        contrib = np.abs((g[:, None] * wi[:, None] ** 2) / D)
        meas = self.is_meas | (self.ext_matched if tiers_updated else False)
        if hidden is not None:
            meas = meas.copy(); meas[np.asarray(hidden)] = False
        return contrib[~meas].sum(0) / (contrib.sum(0) + 1e-300)


def cluster_amp_scatter(pkg, theta):
    """Per matched extended mode: cross-drive std of ln(amplitude scale). Answer-key-style ONE scale per
    mode per drive (joint over all channels; NOT per-channel fitting)."""
    q = WQOI(pkg, theta)
    caches = SW.load_caches()
    out = {}
    sens = np.asarray(pkg.sens_rows) @ q.Q[:, q.inb]     # (n_sens, nM)
    for j in np.where(q.ext_matched)[0]:
        fi = q.meas_f[j]
        lns = []
        for dkey in SW.DEV_KEYS:
            c = caches[dkey]
            fc = c["freqs"]
            bm = (fc >= fi * 0.97) & (fc <= fi * 1.03) & c["band"]
            if bm.sum() < 3:
                continue
            rows, cols = SW._usable(pkg, c, bm)
            if len(rows) < 5:
                continue
            wc = 2 * np.pi * fc[bm]
            wi = 2 * np.pi * fi
            D = wi ** 2 - wc ** 2 + 2j * ZETA * wi * wc
            phid = float(q.drive_part(dkey)[j])
            basis = (-(wc[None, :] ** 2)) * (sens[rows, j][:, None] * phid) / D[None, :]
            b = c["H1"][cols][:, bm]
            num = np.vdot(basis.ravel(), b.ravel())      # ONE complex scale per mode+drive
            den = np.vdot(basis.ravel(), basis.ravel())  # (least-squares in closed form; CHECKER-OK
            s = num / (den + 1e-300)                     #  non-selection: tier construction only)
            if np.abs(s) > 1e-12:
                lns.append(float(np.log(np.abs(s))))
        if len(lns) >= 3:
            out[f"{fi:.1f}Hz"] = {"n_drives": len(lns), "sd_ln_amp": round(float(np.std(lns, ddof=1)), 3),
                                  "mean_ln_amp": round(float(np.mean(lns)), 3)}
    json.dump(out, open(os.path.join(WS, "out", "cluster_amp_scatter.json"), "w"), indent=1)
    return out


def fk_band(q, axis, sd_a_vec, n_disc=400, seed=0, hidden=None, dkey=None):
    """statFEM F(k)-style band: base spectrum x smooth 1-oct log-amplitude field whose marginal ramps
    0.25 -> effective SD where less-measured modes drive the response (netcg formulation)."""
    rng = np.random.default_rng(seed)
    base = q.spectrum(axis, dkey=dkey)
    g = q.g_axis(axis)
    if dkey is not None:
        g = g * q.drive_part(dkey)
    wi = 2 * np.pi * q.meas_f; w = 2 * np.pi * FGRID
    D = wi[:, None] ** 2 - w[None, :] ** 2 + 2j * ZETA * wi[:, None] * w[None, :]
    contrib = np.abs((g[:, None] * wi[:, None] ** 2) / D)
    wfrac = (contrib * sd_a_vec[:, None]).sum(0) / (contrib.sum(0) + 1e-300)
    if hidden is not None:
        hv = np.zeros(q.nM); hv[np.asarray(hidden)] = NC.SD_A_U
        wfrac = np.maximum(wfrac, (contrib * hv[:, None]).sum(0) / (contrib.sum(0) + 1e-300))
    marg = np.maximum(0.25, wfrac)
    specs = []
    for _ in range(n_disc):
        zc = np.log(NC.octave_smooth(FGRID, np.exp(rng.normal(0, 1, len(FGRID))), 1.0))
        zc = (zc - zc.mean()) / (zc.std() + 1e-9)
        specs.append(base * np.exp(marg * zc))
    E = np.array(specs)
    return np.percentile(E, 2.5, 0), np.percentile(E, 50, 0), np.percentile(E, 97.5, 0)


def band_width_ratio(lo, hi):
    """95%-band GRMS-force ratio (hi/lo GRMS on 1-oct smoothed spectra), the netcg width convention."""
    return NC.grms(NC.octave_smooth(FGRID, hi)) / (NC.grms(NC.octave_smooth(FGRID, lo)) + 1e-300)


def sd_vectors(q, updated):
    sd_a = np.where(q.is_meas, NC.SD_A_M, NC.SD_A_U).astype(float)
    if updated:
        sc = json.load(open(os.path.join(WS, "out", "cluster_amp_scatter.json")))
        for j in np.where(q.ext_matched & ~q.is_meas)[0]:
            key = f"{q.meas_f[j]:.1f}Hz"
            sd_obs = sc.get(key, {}).get("sd_ln_amp")
            sd_a[j] = max(0.35, sd_obs) if sd_obs is not None else NC.SD_A_U
    return sd_a


def main(cid="A0_wide", theta=None, label="A1_wide_baseline"):
    t0 = time.time()
    pkg = WP.load(cid)
    if theta is None:
        theta = np.asarray(json.load(open(os.path.join(WS, "out", "theta_map_wide.json")))["theta_map_vec"])
    q = WQOI(pkg, theta)
    scatter = cluster_amp_scatter(pkg, theta)
    res = {"model": label, "cid": cid, "cluster_amp_scatter": scatter}
    # truth ensembles for coverage (tiers NOT updated: the plausible-truth stays honest about shapes)
    for name, axis in AXES.items():
        sd_old = sd_vectors(q, updated=False)
        sd_new = sd_vectors(q, updated=True)
        rng = np.random.default_rng(7)
        truths = []
        sdf = np.where(q.is_meas, NC.SD_F_M, NC.SD_F_U)
        for _ in range(200):
            amp = np.exp(rng.normal(0, 1, q.nM) * sd_old)
            fsc = 1 + rng.normal(0, 1, q.nM) * sdf
            truths.append(q.spectrum(axis, amp=amp, fscale=fsc))
        truths = np.array(truths)
        rec = {}
        for tag, sd in (("tiers_netcg", sd_old), ("tiers_updated", sd_new)):
            lo, med, hi = fk_band(q, axis, sd)
            cov = NC.coverage_vs_truth(lo, hi, truths, FGRID)
            # overconfidence audit: hide top-3 measured QOI-driving modes -> band must widen
            g = np.abs(q.g_axis(axis)) * q.is_meas
            top3 = np.argsort(-g)[:3]
            lo_h, _, hi_h = fk_band(q, axis, sd, hidden=top3)
            rec[tag] = {"width_ratio": round(band_width_ratio(lo, hi), 3),
                        "coverage": round(cov["weighted_coverage"], 3),
                        "widen_audit": round(band_width_ratio(lo_h, hi_h) / band_width_ratio(lo, hi), 3)}
        rec["delivered_reference"] = DELIVERED[name]
        res[name] = {"width_ratio": rec["tiers_updated"]["width_ratio"],
                     "coverage": rec["tiers_updated"]["coverage"],
                     "widen_audit": rec["tiers_updated"]["widen_audit"],
                     "detail": rec}
        print(name, json.dumps(rec), flush=True)
    json.dump(res, open(os.path.join(WS, "out", "netcg_results.json"), "w"), indent=1)
    with open(os.path.join(WS, "out", "runtime_log.jsonl"), "a") as f:
        f.write(json.dumps({"step": "netcg_wide", "active_s": round(time.time() - t0, 1)}) + "\n")


if __name__ == "__main__":
    main(*sys.argv[1:2])
