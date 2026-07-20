#!/usr/bin/env python3
"""P1.5 / D2 / D3 -- matched-path FEM-vs-real FRF sanity gate (task §2(d), GREEN-required).

Builds the FEM matched-path accelerance FRF in g/lbf:
    drive d = nearest kept FEM node to the impact point (9,8,1) in, X axis (hammer normal to +X face);
    response s = nearest kept FEM node to each measured tap channel coord, on its structural axis;
    reduced row of ANY full DOF f = V_keep[row(f), :80] @ T,  T solved 1e-14 from obs_V (verified P1.5);
    H_recept = sum_k U_s[k] U_d[k] / ((1+i*eta) lam_k - w^2);  accelerance = -w^2 H_recept;
    g/lbf = accelerance / 386.089 in/s^2 per g.
Compares to the measured single-impact FRF (hit-001, force/exp window) for DAQ ch 1, 50, 87:
    - peak-frequency alignment in 45-260 Hz;
    - median in-band amplitude RATIO |H_meas|/|H_fem| -> tells us if a constant units-gain is needed.

NO calibration / NO NUTS. Output: out/matched_path_sanity.json  (numbers cited in decisions_log D3).
Run:  ../../.venv_nuts/bin/python code/probe_matched_path.py
"""
from __future__ import annotations
import csv, json
from pathlib import Path
import numpy as np
import scipy.io as sio
from scipy.signal import find_peaks

WS = Path(__file__).resolve().parent.parent
SYN = WS.parent / "statfem_shocksat_eval_20260616" / "data"
TWIN = WS.parent / "shocksat_fem_modal_twin_20260609"
RUN = WS.parent / "shocksat_statfem_runner_20260609"
MAT = RUN / "extracted/Test07_ImpactHammer_990x/Test07_impacthammer_990x_001_5_20_2021_2_32_37 PM.mat"

G_IN_S2 = 386.0886            # in/s^2 per g
ZETA = 0.02                   # nominal modal damping for the sanity check
BAND = (45.0, 260.0)
AX = {"X": 0, "Y": 1, "Z": 2}
IMPACT_XYZ = (9.0, 8.0, 1.0)  # TestLog hit-001 impact point; +X face, hammer Normal -> X drive
IMPACT_AXIS = "X"


def load_reduced():
    rb = np.load(SYN / "reduced_blocks.npz", allow_pickle=True)
    obs_V, A_fix, A = rb["obs_V"], rb["A_fix"], rb["A"]
    obs_dofs = np.load(SYN / "obs_dofs.npy")
    keep = np.load(SYN / "keep_dofs.npy")
    vk = np.load(SYN / "V_keep.npy", mmap_mode="r")
    T, *_ = np.linalg.lstsq(np.asarray(vk[obs_dofs, :80]), obs_V, rcond=None)  # (80,74)
    fm = np.load(TWIN / "fem_model.npz", allow_pickle=True)
    xyz = fm["xyz"]
    keeprow = {int(d): i for i, d in enumerate(keep)}     # full dof id -> kept row index
    return dict(A_fix=A_fix, A=A, T=np.asarray(T), vk=vk, keeprow=keeprow, xyz=xyz)


def reduced_row(R, point_xyz, axis):
    """74-vector reduced shape at the kept FEM DOF nearest `point_xyz` on `axis`."""
    nn = int(np.argmin(np.linalg.norm(R["xyz"] - np.asarray(point_xyz, float), axis=1)))
    dof = 6 * nn + AX[axis]
    if dof not in R["keeprow"]:
        raise KeyError(f"DOF {dof} (node idx {nn}) not kept")
    return np.asarray(R["vk"][R["keeprow"][dof], :80]) @ R["T"], nn


def fem_frf_g_per_lbf(R, freqs, drive_row, resp_row, theta=None, zeta=ZETA):
    theta = np.ones(9) if theta is None else theta
    K = R["A_fix"] + np.einsum("g,gij->ij", theta, R["A"])
    lam, Q = np.linalg.eigh(K)
    lam = np.clip(lam, 1e-9, None)
    eta = 2.0 * zeta
    Us = resp_row @ Q
    Ud = drive_row @ Q
    w = 2 * np.pi * freqs
    g = (1 + 1j * eta) * lam[None, :] - (w ** 2)[:, None]
    H_recept = np.einsum("k,fk->f", (Us * Ud).astype(complex), 1.0 / g)   # in/lbf
    accel = -(w ** 2) * H_recept                                          # (in/s^2)/lbf
    return accel / G_IN_S2                                                # g/lbf


def measured_frf(recorders, N=131072, force_ms=2.0, decay_blocks=8.0):
    recs = ["Recorder116"] + [f"Recorder{r}" for r in recorders.values()]
    d = sio.loadmat(str(MAT), variable_names=recs, struct_as_record=False, squeeze_me=True)
    fs = 1.0 / 4e-6

    def samp(r):
        return np.asarray(d[f"Recorder{r}"].Channels.Segments.Data.Samples, float)
    F = samp(116)
    ip = int(np.argmax(np.abs(F)))
    start = max(0, ip - 200)
    sl = slice(start, start + N)
    pk = ip - start
    half = int(force_ms * 1e-3 * fs)
    fwin = np.zeros(N); fwin[max(0, pk - half):pk + half] = 1.0
    ewin = np.exp(-np.arange(N) / (N / decay_blocks))
    freqs = np.fft.rfftfreq(N, 1 / fs)
    Ff = np.fft.rfft(F[sl] * fwin)
    out = {}
    for lbl, r in recorders.items():
        out[lbl] = np.fft.rfft(samp(r)[sl] * ewin) / Ff
    return freqs, out


def band_peaks(freqs, mag, n=8):
    m = (freqs >= BAND[0]) & (freqs <= BAND[1])
    fb, mb = freqs[m], mag[m]
    pks, _ = find_peaks(mb, prominence=mb.max() * 0.05)
    top = sorted(pks[np.argsort(mb[pks])[::-1][:n]])
    return fb[top].tolist()


def logf_smooth(logmag, freqs, frac=0.06):
    """Moving average of log|H| over a log-frequency window (removes peak-misalignment spikes so the
    underlying SCALE offset between FEM and measured is exposed)."""
    lf = np.log(freqs)
    win = (lf.max() - lf.min()) * frac
    out = np.empty_like(logmag)
    for i in range(len(lf)):
        w = np.abs(lf - lf[i]) <= win
        out[i] = logmag[w].mean()
    return out


def main():
    R = load_reduced()
    # response channel coords from channel_map (tap_impact)
    rows = {r["daq_channel"]: r for r in csv.DictReader(open(RUN / "channel_map.csv"))
            if r["configuration"] == "tap_impact"}
    ch_daq = {"ch1": "1", "ch50": "50", "ch87": "87"}
    recorders = {"ch1": 1, "ch50": 50, "ch87": 87}
    drive_row, drive_node = reduced_row(R, IMPACT_XYZ, IMPACT_AXIS)

    freqs_m, Hmeas = measured_frf(recorders)
    bm = (freqs_m >= BAND[0]) & (freqs_m <= BAND[1])
    fgrid = np.geomspace(BAND[0], BAND[1], 400)   # fine FEM grid for peak finding

    fm = freqs_m[bm]
    res = {"impact_point_xyz": IMPACT_XYZ, "impact_axis": IMPACT_AXIS, "drive_node_idx": drive_node,
           "band_hz": list(BAND), "g_in_s2": G_IN_S2, "zeta_sweep": [0.003, 0.01, 0.02], "channels": {}}
    for lbl, daq in ch_daq.items():
        row = rows[daq]
        coord = (float(row["x_in"]), float(row["y_in"]), float(row["z_in"]))
        resp_row, resp_node = reduced_row(R, coord, row["structural_axis"])
        logmeas = np.log(np.abs(Hmeas[lbl][bm]))
        sm_meas = logf_smooth(logmeas, fm)
        ch = {"daq": daq, "coord": coord, "axis": row["structural_axis"], "resp_node_idx": resp_node,
              "meas_peaks_hz": [round(x, 1) for x in band_peaks(freqs_m, np.abs(Hmeas[lbl]))], "by_zeta": {}}
        for z in res["zeta_sweep"]:
            Hfem = fem_frf_g_per_lbf(R, fgrid, drive_row, resp_row, zeta=z)
            Hfem_m = fem_frf_g_per_lbf(R, fm, drive_row, resp_row, zeta=z)
            sm_fem = logf_smooth(np.log(np.abs(Hfem_m)), fm)
            # smoothed log-ratio = log(meas/FEM) with peak-misalignment spikes averaged out
            log_ratio = sm_meas - sm_fem
            ch["by_zeta"][str(z)] = {
                "fem_peaks_hz": [round(x, 1) for x in band_peaks(fgrid, np.abs(Hfem))],
                "smoothed_log10_ratio_mean": float(np.mean(log_ratio) / np.log(10)),
                "smoothed_log10_ratio_std": float(np.std(log_ratio) / np.log(10)),
                "implied_units_gain_meas_over_fem": float(np.exp(np.mean(log_ratio))),
            }
        res["channels"][lbl] = ch
    (WS / "out").mkdir(exist_ok=True)
    (WS / "out" / "matched_path_sanity.json").write_text(json.dumps(res, indent=2))
    print(f"impact drive node idx {drive_node}  (nearest kept node to {IMPACT_XYZ}, axis {IMPACT_AXIS})")
    for lbl, c in res["channels"].items():
        print(f"--- {lbl} (DAQ {c['daq']}, {c['axis']}) node {c['resp_node_idx']}  meas peaks {c['meas_peaks_hz']}")
        for z, b in c["by_zeta"].items():
            print(f"    zeta={z}: FEM peaks {b['fem_peaks_hz']}  | smoothed log10(meas/FEM) "
                  f"mean {b['smoothed_log10_ratio_mean']:+.2f} std {b['smoothed_log10_ratio_std']:.2f}"
                  f"  -> gain x{b['implied_units_gain_meas_over_fem']:.1f}")
    print("wrote out/matched_path_sanity.json")


if __name__ == "__main__":
    main()
