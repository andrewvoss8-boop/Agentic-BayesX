#!/usr/bin/env python3
"""Reduced sequential statFEM pilot for ShockSat clean modal-hammer data.

This is a bounded analogue of Kavrakov et al.'s sequential statFEM, not a full-FE
SPDE material-field implementation. It uses the existing ShockSat reduced modal
model as the state model:

    x_n = [q_n, qdot_n]

Observed training sensors are assimilated by a linear-Gaussian modal-state filter.
Held-out sensors are predicted from the updated state, converted to FRFs with the
measured hammer force, then scored with the inherited PSD-envelope GRMS and
energy-weighted exceedance metrics.
"""
from __future__ import annotations

import json
import sys
import time
from dataclasses import dataclass
from pathlib import Path

import numpy as np
from scipy.linalg import expm
from scipy.signal import resample_poly

WS = Path(__file__).resolve().parent.parent
REPO = WS.parents[2]
PSD_WS = WS.parent / "shocksat_psd_envelope_twin_20260623"
EXPLORE_WS = WS.parent / "shocksat_multiref_explore_20260623"
RAW = EXPLORE_WS / "data" / "extracted"
OUT = WS / "out"
OUT.mkdir(exist_ok=True)

sys.path.insert(0, str((PSD_WS / "code").resolve()))
import realfrf as rf  # noqa: E402
import modal_feature as mf  # noqa: E402
import psd_forward as pf  # noqa: E402
import psd_envelope as pe  # noqa: E402
from modal_multiref import MODAL_REFS, N_MODAL  # noqa: E402

S_F0 = 1.0
ZETA = 0.01
FS_RAW = rf.FS
DOWN = 125
FS_DS = FS_RAW / DOWN
OBS_FRAC = 0.90
SEED = 0
PROCESS_SCALE = 0.08
OBS_NOISE_FRAC = 0.08
OBS_NOISE_FLOOR_G = 1.0e-4
EXC_ENERGY_OK = 0.02
MAX_STIFFNESS_GROUPS = 2

REF_FOLDERS = {
    "m_xpos_990x": "Test01_ModalHammer_990x",
    "m_zpos_990z": "Test02_ModalHammer_990z",
    "m_xy_990xy": "Test04_ModalHammer_990xy",
    "m_zpos_900z": "Test06_ModalHammer_900z",
}


def json_default(obj):
    if isinstance(obj, np.integer):
        return int(obj)
    if isinstance(obj, np.floating):
        return float(obj)
    if isinstance(obj, np.ndarray):
        return obj.tolist()
    raise TypeError(f"Object of type {type(obj).__name__} is not JSON serializable")


@dataclass
class Hit:
    force: np.ndarray
    accel: np.ndarray
    impact_idx: int
    file: str


def exp_window(n: int, end: float = 0.05) -> np.ndarray:
    return np.exp(np.log(end) * np.arange(n) / max(1, n - 1))


def force_window(n: int, impact_idx: int, fs: float, force_ms: float = 2.0) -> np.ndarray:
    win = np.zeros(n)
    half = max(1, int(force_ms * 1e-3 * fs))
    lo = max(0, impact_idx - half)
    hi = min(n, impact_idx + half)
    win[lo:hi] = 1.0
    return win


def segment_hit(force: np.ndarray, accel: np.ndarray) -> tuple[np.ndarray, np.ndarray, int] | None:
    ip = int(np.argmax(np.abs(force)))
    start = max(0, ip - rf.PROC["pre_gap"])
    if start + N_MODAL > force.size:
        return None
    sl = slice(start, start + N_MODAL)
    fseg = force[sl].astype(float).copy()
    yseg = accel[:, sl].astype(float).copy()
    # Remove tiny digitizer offsets using the short pre-hit segment available in the inherited window.
    n0 = min(rf.PROC["pre_gap"], fseg.size)
    fseg -= np.median(fseg[:n0])
    yseg -= np.median(yseg[:, :n0], axis=1)[:, None]
    fds = resample_poly(fseg, up=1, down=DOWN)
    yds = resample_poly(yseg, up=1, down=DOWN, axis=1)
    return fds, yds, int(round((ip - start) / DOWN))


def load_reference_hits(key: str, daqs: list[int]) -> list[Hit]:
    import scipy.io as sio

    folder = RAW / REF_FOLDERS[key]
    files = sorted(folder.glob("*.mat"))
    hits: list[Hit] = []
    want = [f"Recorder{rf.FORCE_RECORDER}"] + [f"Recorder{d}" for d in daqs]
    for fp in files:
        mat = sio.loadmat(str(fp), variable_names=want, struct_as_record=False, squeeze_me=True)
        force = np.asarray(mat[f"Recorder{rf.FORCE_RECORDER}"].Channels.Segments.Data.Samples, float)
        accel = np.array([
            np.asarray(mat[f"Recorder{d}"].Channels.Segments.Data.Samples, float)
            for d in daqs
        ])
        seg = segment_hit(force, accel)
        if seg is None:
            continue
        fds, yds, ip_ds = seg
        hits.append(Hit(force=fds, accel=yds, impact_idx=ip_ds, file=fp.name))
    if not hits:
        raise RuntimeError(f"No usable hits for {key} in {folder}")
    return hits


def ensemble_h1_from_hits(hits: list[Hit], accel_by_hit: list[np.ndarray]) -> tuple[np.ndarray, np.ndarray]:
    n = min(h.force.size for h in hits)
    freqs = np.fft.rfftfreq(n, 1.0 / FS_DS)
    band = (freqs >= rf.BAND[0]) & (freqs <= rf.BAND[1])
    n_chan = accel_by_hit[0].shape[0]
    sxx = np.zeros(freqs.size)
    sxy = np.zeros((n_chan, freqs.size), dtype=complex)
    for hit, y in zip(hits, accel_by_hit):
        f = hit.force[:n]
        yy = y[:, :n]
        fw = force_window(n, hit.impact_idx, FS_DS, rf.PROC["force_ms"])
        ew = exp_window(n, rf.PROC["exp_end"])
        ff = np.fft.rfft(f * fw)
        yf = np.fft.rfft(yy * ew[None, :], axis=1)
        sxx += np.abs(ff) ** 2
        sxy += yf * np.conj(ff)[None, :]
    h1 = sxy / (sxx[None, :] + 1e-300)
    return freqs[band], h1[:, band]


def split_sensors(daq_master: list[int], obs_frac: float = OBS_FRAC, seed: int = SEED) -> tuple[list[int], list[int]]:
    rng = np.random.default_rng(seed)
    perm = rng.permutation(len(daq_master))
    n_obs = int(round(obs_frac * len(daq_master)))
    obs = sorted(daq_master[i] for i in perm[:n_obs])
    held = sorted(daq_master[i] for i in perm[n_obs:])
    return obs, held


def measured_modes_from_observed(obs_daqs: list[int]) -> tuple[np.ndarray, np.ndarray, list[tuple[int, float]]]:
    R = rf.load_reduced()
    pooled: dict[int, list[float]] = {}
    for key in MODAL_REFS:
        z = np.load(PSD_WS / "data" / "multiref_modal" / f"{key}.npz", allow_pickle=True)
        meas = {
            "freqs": z["freqs"],
            "H": z["H1"],
            "daq": [int(d) for d in z["daq"]],
            "dyn_range": np.array([
                float(np.max(np.abs(row) ** 2) / (np.percentile(np.abs(row) ** 2, 25) + 1e-300))
                for row in z["H1"]
            ]),
        }
        common = [d for d in obs_daqs if d in meas["daq"]]
        if len(common) < 4:
            continue
        ch_simple = type("Ch", (), {"daq": common})
        freqs, _support = mf.extract_measured_modes(meas, ch_simple)
        pairs, _ = mf.match(R, freqs)
        for idx, hz in pairs:
            pooled.setdefault(int(idx), []).append(float(hz))
    pairs = [(idx, float(np.median(vals))) for idx, vals in sorted(pooled.items())]
    mode_idx = np.array([p[0] for p in pairs], dtype=int)
    mode_hz = np.array([p[1] for p in pairs], dtype=float)
    return mode_idx, mode_hz, pairs


def select_stiffness_groups(R: rf.Reduced, mode_idx: np.ndarray, mode_hz: np.ndarray) -> dict:
    theta0 = np.ones(9)
    f0 = mf.fem_modes_np(R, theta0)[mode_idx]
    h = 0.03
    J = np.zeros((len(mode_idx), 9))
    for g in range(9):
        tp = theta0.copy()
        tm = theta0.copy()
        tp[g] = np.exp(h)
        tm[g] = np.exp(-h)
        fp = mf.fem_modes_np(R, tp)[mode_idx]
        fm = mf.fem_modes_np(R, tm)[mode_idx]
        J[:, g] = (np.log(fp) - np.log(fm)) / (2 * h)
    rel_resid = np.log(np.maximum(mode_hz, 1e-9) / np.maximum(f0, 1e-9))
    sigma_floor = float(max(0.015, np.sqrt(np.mean(rel_resid**2))))
    fim = (J.T @ J) / (sigma_floor**2)
    diag = np.diag(fim)
    selected = [int(i) for i in np.argsort(diag)[::-1][:MAX_STIFFNESS_GROUPS]]
    eigval, eigvec = np.linalg.eigh(fim)
    order = np.argsort(eigval)[::-1]
    eigval = eigval[order]
    eigvec = eigvec[:, order]
    return {
        "sigma_floor_rel_freq": sigma_floor,
        "selected_groups": selected,
        "selected_group_names": [rf.GNAMES[i] for i in selected],
        "fim_diag": {rf.GNAMES[i]: float(diag[i]) for i in range(9)},
        "fim_eigenvalues": [float(x) for x in eigval[:5]],
        "strongest_combo": {
            rf.GNAMES[i]: float(eigvec[i, 0])
            for i in np.argsort(np.abs(eigvec[:, 0]))[::-1][:4]
        }
    }


def calibrate_stiffness_subset(R: rf.Reduced, mode_idx: np.ndarray, mode_hz: np.ndarray, groups: list[int]) -> dict:
    t0 = time.time()
    theta_post, sigma_w2, diag = mf.calibrate_modal(
        R,
        mode_idx,
        mode_hz,
        fg=groups,
        seed=20260623,
        warmup=500,
        samples=500,
        chains=4,
    )
    theta_med = np.median(theta_post, axis=0)
    return {
        "available": True,
        "runtime_s": round(time.time() - t0, 3),
        "groups": groups,
        "group_names": [rf.GNAMES[i] for i in groups],
        "diag": diag,
        "sigma_w2_rel_median": float(np.median(sigma_w2)),
        "theta_median": [float(x) for x in theta_med],
    }


def build_modal_mats(R: rf.Reduced, theta: np.ndarray, drive_row: np.ndarray, resp_rows: np.ndarray,
                     mode_idx: np.ndarray, dt: float) -> dict:
    K = R.A_fix + np.einsum("g,gij->ij", theta, R.A)
    lam, Qfull = np.linalg.eigh(K)
    lam = np.clip(lam, 1e-9, None)
    omega_all = np.sqrt(lam)
    Q = Qfull[:, mode_idx]
    omega = omega_all[mode_idx]
    m = len(mode_idx)
    z = np.full(m, ZETA)
    Ac = np.zeros((2 * m, 2 * m))
    Ac[:m, m:] = np.eye(m)
    Ac[m:, :m] = -np.diag(omega**2)
    Ac[m:, m:] = -np.diag(2.0 * z * omega)
    drive_modal = drive_row @ Q
    Bc = np.zeros((2 * m, 1))
    Bc[m:, 0] = drive_modal
    aug = np.zeros((2 * m + 1, 2 * m + 1))
    aug[:2 * m, :2 * m] = Ac
    aug[:2 * m, 2 * m:] = Bc
    eaug = expm(aug * dt)
    Ad = eaug[:2 * m, :2 * m]
    Bd = eaug[:2 * m, 2 * m]
    S = resp_rows @ Q
    C = np.concatenate([-S * (omega**2)[None, :] / rf.G_IN_S2,
                        -S * (2.0 * z * omega)[None, :] / rf.G_IN_S2], axis=1)
    D = (S @ drive_modal) / rf.G_IN_S2
    return {"Ad": Ad, "Bd": Bd, "C": C, "D": D, "omega": omega, "drive_modal": drive_modal}


def state_prior_sigma(mats: dict, force_peak: float) -> np.ndarray:
    """Fixed Gaussian prior scale for the bounded sequential MAP update.

    A full Kalman covariance recursion was too slow for a small replayable
    validity probe. This keeps the Bayesian prediction/update structure but uses
    one fixed prior covariance centered on the dynamic prediction at every time
    step.
    """
    omega = mats["omega"]
    drive = np.abs(mats["drive_modal"])
    floor = np.percentile(drive, 25) if drive.size else 1.0
    acc_sigma = PROCESS_SCALE * force_peak * np.maximum(drive, floor) + 1e-12
    q_sigma = acc_sigma / np.maximum(omega**2, 1e-12)
    v_sigma = acc_sigma / np.maximum(omega, 1e-12)
    return np.concatenate([q_sigma, v_sigma])


def filter_hit(force: np.ndarray, y_train: np.ndarray, mats_train: dict, mats_ho: dict,
               obs_sigma: np.ndarray, prior_sigma: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    Ad = mats_train["Ad"]
    Bd = mats_train["Bd"]
    Ctr = mats_train["C"]
    Dtr = mats_train["D"]
    Cho = mats_ho["C"]
    Dho = mats_ho["D"]
    n_state = Ad.shape[0]
    n_time = min(force.size, y_train.shape[1])
    x = np.zeros(n_state)
    rinv = 1.0 / (obs_sigma**2)
    yhat_train = np.zeros((Ctr.shape[0], n_time))
    yhat_ho = np.zeros((Cho.shape[0], n_time))
    CtR = Ctr.T * rinv[None, :]
    CtRC = CtR @ Ctr
    prior_prec = np.diag(1.0 / np.maximum(prior_sigma, 1e-12) ** 2)
    info = prior_prec + CtRC + np.eye(n_state) * 1e-12
    gain = np.linalg.solve(info, CtR)
    for k in range(n_time):
        f = force[k]
        x_pred = Ad @ x + Bd * f
        target = y_train[:, k] - Dtr * f
        residual = target - Ctr @ x_pred
        x = x_pred + gain @ residual
        yhat_train[:, k] = Ctr @ x + Dtr * f
        yhat_ho[:, k] = Cho @ x + Dho * f
    return yhat_train, yhat_ho


def zeta_eff_for_forward(freqs: np.ndarray) -> np.ndarray:
    tau = -(N_MODAL - 1) / (FS_RAW * np.log(rf.PROC["exp_end"]))
    return ZETA + 1.0 / (2 * np.pi * np.asarray(freqs, float) * tau)


def score_rows(freqs: np.ndarray, data_h: np.ndarray, pred_h: np.ndarray,
               fem_h: np.ndarray, daqs: list[int], variant: str, ref_key: str) -> tuple[list[dict], dict, np.ndarray]:
    data_psd = np.abs(data_h) ** 2 * S_F0
    pred_psd = np.abs(pred_h) ** 2 * S_F0
    fem_psd = np.abs(fem_h) ** 2 * S_F0
    env_factor = 1.0
    rows: list[dict] = []
    example = None
    for i, daq in enumerate(daqs):
        seq975 = pred_psd[i] * env_factor
        env_seq = pe.smoothline_envelope(freqs, seq975)
        env_fem6 = pe.smoothline_envelope(freqs, pe.add_db_psd(fem_psd[i], 6.0))
        g_seq = pe.grms(freqs, env_seq)
        g_fem = pe.grms(freqs, env_fem6)
        exc_seq = pe.exceedance(freqs, data_psd[i], env_seq)
        exc_fem = pe.exceedance(freqs, data_psd[i], env_fem6)
        row = {
            "ref": ref_key,
            "variant": variant,
            "daq": int(daq),
            "grms_seq_env": g_seq,
            "grms_fem6_env": g_fem,
            "grms_ratio": g_seq / (g_fem + 1e-300),
            "seq_below_fem6": bool(g_seq < g_fem),
            "seq_max_exc_db": exc_seq["max_exceedance_db_positive"],
            "seq_exc_energy_frac": exc_seq["exceeding_energy_fraction"],
            "fem6_max_exc_db": exc_fem["max_exceedance_db_positive"],
            "fem6_exc_energy_frac": exc_fem["exceeding_energy_fraction"],
            "clean_win": bool(g_seq < g_fem and exc_seq["exceeding_energy_fraction"] < EXC_ENERGY_OK),
        }
        rows.append(row)
        if example is None or row["grms_ratio"] < example[0]["grms_ratio"]:
            example = (row, data_psd[i], env_seq, env_fem6, pred_psd[i])
    assert example is not None
    ex_row, ex_data, ex_seq, ex_fem, ex_pred = example
    example_arr = np.vstack([freqs, ex_data, ex_pred, ex_seq, ex_fem])
    return rows, ex_row, example_arr


def aggregate(rows: list[dict]) -> dict:
    ratios = np.array([r["grms_ratio"] for r in rows], float)
    return {
        "n": len(rows),
        "median_grms_ratio": float(np.median(ratios)),
        "min_grms_ratio": float(np.min(ratios)),
        "max_grms_ratio": float(np.max(ratios)),
        "win_rate_grms": float(np.mean([r["seq_below_fem6"] for r in rows])),
        "clean_win_rate": float(np.mean([r["clean_win"] for r in rows])),
        "median_seq_exc_energy_frac": float(np.median([r["seq_exc_energy_frac"] for r in rows])),
        "median_seq_max_exc_db": float(np.median([r["seq_max_exc_db"] for r in rows])),
        "median_fem6_exc_energy_frac": float(np.median([r["fem6_exc_energy_frac"] for r in rows])),
    }


def run() -> dict:
    start_wall = time.time()
    R = rf.load_reduced()
    ch = rf.build_channels(R, list(range(1, rf.N_ACCEL_RECORDERS + 1)))
    daq_master = list(ch.daq)
    obs_daqs, held_daqs = split_sensors(daq_master)
    pos = {d: i for i, d in enumerate(daq_master)}
    obs_idx = [pos[d] for d in obs_daqs]
    held_idx = [pos[d] for d in held_daqs]

    mode_idx, mode_hz, matched_pairs = measured_modes_from_observed(obs_daqs)
    if mode_idx.size < 6:
        K0 = R.A_fix + np.einsum("g,gij->ij", np.ones(9), R.A)
        f0 = np.sqrt(np.clip(np.linalg.eigvalsh(K0), 1e-9, None)) / (2 * np.pi)
        mode_idx = np.where((f0 >= 45.0) & (f0 <= 260.0))[0]
        mode_hz = f0[mode_idx]
        matched_pairs = [(int(i), float(f)) for i, f in zip(mode_idx, mode_hz)]
    mode_idx = np.array(sorted(set(int(i) for i in mode_idx)), dtype=int)

    fim = select_stiffness_groups(R, mode_idx, mode_hz)
    try:
        stiffness = calibrate_stiffness_subset(R, mode_idx, mode_hz, fim["selected_groups"])
        theta_stiff = np.array(stiffness["theta_median"])
    except Exception as exc:  # keep the runner useful; checker will surface yellow/red as appropriate.
        stiffness = {"available": False, "error": repr(exc), "groups": fim["selected_groups"],
                     "group_names": fim["selected_group_names"]}
        theta_stiff = np.ones(9)

    variants = {
        "nominal_residual": np.ones(9),
        "stiffness_residual": theta_stiff,
    }

    detail: dict[str, dict[str, list[dict]]] = {v: {} for v in variants}
    summaries: dict[str, dict[str, dict]] = {v: {} for v in variants}
    residuals: dict[str, dict[str, dict]] = {v: {} for v in variants}
    examples: dict[str, np.ndarray] = {}

    for ref_key, ref in MODAL_REFS.items():
        hits = load_reference_hits(ref_key, daq_master)
        n = min(h.force.size for h in hits)
        hits = [Hit(h.force[:n], h.accel[:, :n], h.impact_idx, h.file) for h in hits]
        freqs, H_meas_all = ensemble_h1_from_hits(hits, [h.accel for h in hits])
        drive_row = pf.drive_row_for(R, ref["xyz"], ref["axis"])
        force_peak = float(np.median([np.max(np.abs(h.force)) for h in hits]))
        for variant, theta in variants.items():
            mats_all = build_modal_mats(R, theta, drive_row, ch.rows, mode_idx, 1.0 / FS_DS)
            mats_train = {
                "Ad": mats_all["Ad"],
                "Bd": mats_all["Bd"],
                "C": mats_all["C"][obs_idx],
                "D": mats_all["D"][obs_idx],
                "omega": mats_all["omega"],
                "drive_modal": mats_all["drive_modal"],
            }
            mats_ho = {
                "C": mats_all["C"][held_idx],
                "D": mats_all["D"][held_idx],
            }
            train_stack = np.concatenate([h.accel[obs_idx] for h in hits], axis=1)
            rms = np.sqrt(np.mean(train_stack**2, axis=1))
            obs_sigma = np.maximum(OBS_NOISE_FRAC * rms, OBS_NOISE_FLOOR_G)
            prior_sigma = state_prior_sigma(mats_all, force_peak)

            pred_train_hits = []
            pred_ho_hits = []
            for hit in hits:
                ytr, yho = filter_hit(hit.force, hit.accel[obs_idx], mats_train, mats_ho, obs_sigma, prior_sigma)
                pred_train_hits.append(ytr)
                pred_ho_hits.append(yho)
            _, H_pred_train = ensemble_h1_from_hits(hits, pred_train_hits)
            _, H_pred_ho = ensemble_h1_from_hits(hits, pred_ho_hits)
            H_meas_train = H_meas_all[obs_idx]
            H_meas_ho = H_meas_all[held_idx]

            log_ratio = np.log(np.abs(H_meas_train) + 1e-300) - np.log(np.abs(H_pred_train) + 1e-300)
            gain = float(np.median(log_ratio))
            sigma = float(np.std(log_ratio - gain))
            band_factor = float(np.exp(2.0 * 1.96 * sigma))
            H_pred_ho_scaled = H_pred_ho * np.exp(gain)
            H_pred_train_scaled = H_pred_train * np.exp(gain)

            fem_eta = zeta_eff_for_forward(freqs)
            H_fem_all = pf.forward_H_single(R, freqs, np.ones(9), drive_row, ch.rows, fem_eta).T
            fem_log_ratio = (
                np.log(np.abs(H_meas_train) + 1e-300)
                - np.log(np.abs(H_fem_all[obs_idx]) + 1e-300)
            )
            fem_gain = float(np.median(fem_log_ratio))
            H_fem_ho = H_fem_all[held_idx] * np.exp(fem_gain)

            rows, example_row, example_arr = score_rows(
                freqs,
                H_meas_ho,
                H_pred_ho_scaled * np.sqrt(band_factor),
                H_fem_ho,
                held_daqs,
                variant,
                ref_key,
            )
            detail[variant][ref_key] = rows
            summaries[variant][ref_key] = aggregate(rows)
            residuals[variant][ref_key] = {
                "training_gain_log": gain,
                "training_residual_sigma_logH": sigma,
                "psd_975_multiplier_from_residual": band_factor,
                "psd_975_multiplier_db": float(10.0 * np.log10(band_factor)),
                "fem_training_gain_log": fem_gain,
                "n_hits": len(hits),
                "force_peak_lbf_median": force_peak,
                "obs_noise_sigma_g_median": float(np.median(obs_sigma)),
                "example": example_row,
            }
            if variant == "stiffness_residual" and ref_key == "m_xpos_990x":
                examples["stiffness_residual_m_xpos_990x"] = example_arr
            if variant == "nominal_residual" and ref_key == "m_xpos_990x":
                examples["nominal_residual_m_xpos_990x"] = example_arr

    all_rows = {
        variant: [row for ref_rows in detail[variant].values() for row in ref_rows]
        for variant in variants
    }
    overall = {variant: aggregate(rows) for variant, rows in all_rows.items()}
    l5_probe = PSD_WS / "out" / "probe_seed00.json"
    l5_reused = json.loads(l5_probe.read_text()) if l5_probe.exists() else None
    rec = {
        "task": "ShockSat reduced sequential statFEM PSD-envelope validity probe",
        "workspace": str(WS),
        "status_interpretation": "YELLOW unless PSD envelope improves and caveats are resolved",
        "split": {
            "seed": SEED,
            "obs_frac": OBS_FRAC,
            "n_sensors": len(daq_master),
            "n_observed": len(obs_daqs),
            "n_heldout": len(held_daqs),
            "observed_daqs": obs_daqs,
            "heldout_daqs": held_daqs,
        },
        "data": {
            "raw_root": str(RAW),
            "references": {k: {kk: vv for kk, vv in v.items() if kk in ("label", "xyz", "axis", "note")}
                           for k, v in MODAL_REFS.items()},
            "fs_raw_hz": FS_RAW,
            "fs_filter_hz": FS_DS,
            "window_raw_samples": N_MODAL,
            "units": {"acceleration": "g", "force": "lbf", "frf": "g/lbf", "psd": "g^2/Hz"},
        },
        "method": {
            "state": "modal displacement and velocity",
            "mode_indices": [int(i) for i in mode_idx.tolist()],
            "n_modes": int(len(mode_idx)),
            "matched_mode_pairs_modeidx_hz": [[int(i), float(hz)] for i, hz in matched_pairs],
            "filter_label": "fixed-prior linear-Gaussian sequential MAP state filter; not NUTS/HMC",
            "hyperparameters": {
                "zeta": ZETA,
                "process_scale": PROCESS_SCALE,
                "obs_noise_frac": OBS_NOISE_FRAC,
                "obs_noise_floor_g": OBS_NOISE_FLOOR_G,
                "note": "fixed validity-probe hyperparameters, not inferred; fixed-prior covariance for bounded replay",
            },
        },
        "identifiability": fim,
        "stiffness_update": stiffness,
        "residual_calibration": residuals,
        "summaries": summaries,
        "overall_by_variant": overall,
        "detail": detail,
        "l5_probe_reused": {
            "path": str(l5_probe),
            "available": l5_reused is not None,
            "overall": l5_reused.get("combined_correlated") if l5_reused else None,
            "note": "Existing L5/modal-frequency PSD-envelope probe reused because the runner prompt allowed reuse if cheap.",
        },
        "thresholds": {
            "green_grms_ratio_lt": 1.0,
            "clean_exceeding_energy_fraction_lt": EXC_ENERGY_OK,
        },
        "runtime_s": round(time.time() - start_wall, 3),
    }
    (OUT / "results.json").write_text(json.dumps(rec, indent=2, default=json_default))
    if examples:
        np.savez_compressed(OUT / "example_envelopes.npz", **examples)
    runtime = {
        "active_runtime_s": rec["runtime_s"],
        "elapsed_wallclock_s": rec["runtime_s"],
        "machine": "local CPU",
        "notes": "Filter, stiffness-subset NUTS, scoring. Plot/check time excluded by design; active <= elapsed.",
    }
    (WS / "runtime.json").write_text(json.dumps(runtime, indent=2, default=json_default))
    print("Sequential statFEM pilot complete")
    print(f"  split: {len(obs_daqs)} observed / {len(held_daqs)} held-out sensors")
    print(f"  modes: {len(mode_idx)}; stiffness groups: {fim['selected_group_names']}")
    for variant, agg in overall.items():
        print(f"  {variant}: median GRMS ratio {agg['median_grms_ratio']:.3f}, "
              f"clean-win rate {100*agg['clean_win_rate']:.1f}%")
    print(f"  wrote {OUT / 'results.json'}")
    return rec


if __name__ == "__main__":
    run()
