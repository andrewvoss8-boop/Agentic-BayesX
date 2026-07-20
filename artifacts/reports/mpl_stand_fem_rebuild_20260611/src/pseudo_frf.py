#!/usr/bin/env python3
"""Pseudo-FRF comparison, rev-7 FEM vs scrappy test (FABLE, D39/D40).

NO force was measured -> PSEUDO-FRFs: peak FREQUENCIES comparable, amplitudes
NOT. Two consistent comparison types:

 (A) TAP TRANSFER FRFs (apples-to-apples: a wrench tap IS a point force).
     For response location B and tap (excitation) location A, the FEM comparand
     is the TRANSFER ACCELERANCE H_BA(w) = -w^2 sum_r phi_rB phi_rA /
     (w_r^2 - w^2 + 2 i zeta w_r w) (mass-normalized modes, X = shield-normal,
     test answer A5). A 3x3 matrix over {interface, shield-mid, top-left};
     diagonal = drive points. Test = averaged |FFT| of the response over the
     good taps at A. WINDOWING FIX (D40): each tap window is capped BEFORE the
     next event and any window containing a near-rail peak (>90 g = 883 m/s^2)
     is rejected -> the saturated drive hit no longer contaminates its
     neighbor (the top-center bug Andrew caught).

 (B) ACOUSTIC FRFs (apples-to-apples via a MODELED forcing function): the
     speaker pink noise is a DISTRIBUTED acoustic pressure, NOT a point force,
     so the FEM uses an ACOUSTIC FORCING MODEL = uniform in-phase pressure over
     the shield (normal-incidence plane wave; valid where acoustic wavelength
     >> panel, i.e. low freq -- FLAGGED). Modal acoustic force f_r ~ sum over
     shield X-dofs of phi_r (uniform tributary area approx). FEM acoustic
     response at B = -w^2 sum_r f_r phi_rB /(...) times the pink input shape
     S^(1/2) ~ 1/sqrt(f). Test = sqrt(Welch PSD) of the steady segment.

Normalization: each curve to its own 5-150 Hz peak. Uncalibrated coarse prior,
photo-estimate masses. NO sampler. Output: out/pseudo_frf.json.
"""
import json
import os

import numpy as np
import pandas as pd
from scipy.signal import welch, find_peaks

WS = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(WS, "..", "..", "..", "MPL test stand", "FEM", "test_data")
FS = 10000.0
ZETA = 0.03
WIN_S = 2.5                  # tap window length (df ~ 0.4 Hz; fits tight gaps)
SAT = 883.0                  # 90 g near-rail reject threshold (rail = 981)
FNORM = (5.0, 150.0)
FPICK = (5.0, 90.0)
FSHOW = 250.0               # store to 250 so the valve frame modes (~156/190) show

# FEM nodes (X dof): 3 key stand locations + the QOI points (D41)
GRID = dict(interface=800071, shield_mid=800038, top_left=1510,
            valve=910009,        # top frame node near the manifold/valves
            box=900002,          # electronics-box CONM2 (rigid box / its feet)
            engine_beam=952,     # frame node by the thrust plate (tap location)
            foot=692)            # front-left foot (SPC'd in nominal -> see note)
SPC_GRIDS = {1, 164, 692, 1212}

# Per setup: response location + tap groups {tap-location: onsets} + all event
# onsets in the file (to cap windows) + acoustic file/window.
SETUPS = {
    "interface": dict(
        resp="interface", tap_file="unloaded top.csv",
        taps=dict(interface=[11.4, 20.4],          # 24.6 saturated -> excluded
                  engine_beam=[42.2, 46.4, 50.9],
                  shield_mid=[61.9, 66.4, 70.5],
                  top_left=[82.9, 86.6, 91.7],
                  foot=[102.9, 106.0, 109.2]),      # front-left foot
        all_events=[11.4, 20.4, 24.6, 42.2, 46.4, 50.9, 61.9, 66.4, 70.5,
                    82.9, 86.6, 91.7, 102.9, 106.0, 109.2],
        acoustic_file="acoustic unloaded top.csv", acoustic_win=(14, 76)),
    "shield_mid": dict(
        resp="shield_mid", tap_file="shield tap.csv",
        taps=dict(interface=[9.1, 12.8, 16.4],
                  shield_mid=[24.2, 27.6, 31.0],
                  engine_beam=[54.7, 57.5, 62.0],
                  top_left=[74.3, 77.6, 81.4]),
        all_events=[9.1, 12.8, 16.4, 24.2, 27.6, 31.0, 39.4, 41.7, 45.8,
                    54.7, 57.5, 62.0, 74.3, 77.6, 81.4],
        acoustic_file="shield acoustic.csv", acoustic_win=(11, 71)),
    "top_left": dict(
        resp="top_left", tap_file="top left beam tap.csv",
        taps=dict(interface=[9.5, 12.9, 16.7],
                  shield_mid=[23.3, 25.6, 28.8],
                  engine_beam=[34.3, 37.2, 40.6],
                  top_left=[74.4, 80.8, 87.4]),       # 47.1,61.4 dropped (A2)
        all_events=[9.5, 12.9, 16.7, 23.3, 25.6, 28.8, 34.3, 37.2, 40.6,
                    47.1, 61.4, 74.4, 80.8, 87.4],
        acoustic_file="top left beam acoustic.csv", acoustic_win=(12, 47)),
}

# QOI points (Setup 4, HELD-OUT records): accel @ QOI point, tap @ engine beam.
# These directly test the mounted-mass models (80/20 valve frame; box-on-shield).
# CAVEATS: valve acoustic is weak (RMS 0.019 = low SNR); the box BODY/top was
# NOT measured (DAQ cable broke) -- we have the box FEET (mount interface), both
# mapped to the rigid-box CONM2 node; valve's OWN frame modes are ~156/190 Hz,
# above the clean 5-90 Hz band, so this tests the stand->QOI PATH more than the
# QOI's own resonance.
QOI = {
    "valve": dict(resp="valve", tap_loc="engine_beam",
                  tap_file="valve tap (engine mount) and acoustic.csv",
                  taps=[8.8, 12.4, 16.6], all_events=[8.8, 12.4, 16.6],
                  acoustic_file="valve tap (engine mount) and acoustic.csv",
                  acoustic_win=(29, 80), weak_acoustic=True),
    "box_foot_left": dict(resp="box", tap_loc="engine_beam",
                  tap_file="top left avi foot tap and acoustic.csv",
                  taps=[4.8, 8.3, 13.4], all_events=[4.8, 8.3, 13.4],
                  acoustic_file="top left avi foot tap and acoustic.csv",
                  acoustic_win=(19, 72)),
    "box_foot_right": dict(resp="box", tap_loc="engine_beam",
                  tap_file="top right avi foot tap and acoustic.csv",
                  taps=[4.8, 8.7, 13.0], all_events=[4.8, 8.7, 13.0],
                  acoustic_file="top right avi foot tap and acoustic.csv",
                  acoustic_win=(19, 64)),
}


def load(fn):
    return pd.read_csv(os.path.join(DATA, fn), usecols=[0, 1]).to_numpy()[:, 1]


def tap_spectrum(a, onsets, all_events):
    """Averaged |FFT| over the good taps; window capped before the next event;
    saturated windows rejected (D40 fix). Returns (freqs, mag, n_used, log)."""
    n = int(WIN_S * FS)
    freqs = np.fft.rfftfreq(n, 1.0 / FS)
    han = np.hanning(n)
    acc = np.zeros(freqs.size)
    used, log = 0, []
    ev = np.array(sorted(all_events))
    for t0 in onsets:
        nxt = ev[ev > t0 + 0.05]
        cap = (nxt.min() - 0.3) if nxt.size else (t0 + WIN_S)
        if cap - t0 < WIN_S:                       # not enough clean room
            log.append(dict(onset=t0, status="rejected: next event too close"))
            continue
        i0 = int((t0 - 0.05) * FS)
        seg = a[i0:i0 + n]
        if seg.size < n:
            log.append(dict(onset=t0, status="rejected: short")); continue
        if np.abs(seg).max() > SAT:                # saturated -> reject
            log.append(dict(onset=t0, status=f"rejected: peak "
                            f"{np.abs(seg).max():.0f} m/s2 > {SAT} (near rail)"))
            continue
        acc += np.abs(np.fft.rfft((seg - seg.mean()) * han))
        used += 1
        log.append(dict(onset=t0, status="used",
                        peak_ms2=round(float(np.abs(seg).max()), 0)))
    acc /= max(used, 1)
    return freqs, acc, used, log


# ---- FEM modal data ----
sh = np.load(os.path.join(WS, "out", "modes_nominal_shapes.npz"))
FR, PHI, MD = sh["freqs"], sh["Phi"], sh["master_dofs"]
arr = np.load(os.path.join(WS, "out", "model", "arrays.npz"))
GP = {int(g): i for i, g in enumerate(arr["grid_ids"])}
REGION = arr["region"].astype(str)


def mrow(grid):
    return int(np.where(MD == 6 * GP[grid] + 0)[0][0])    # X dof master row


SHIELD_ROWS = [int(np.where(MD == 6 * GP[int(g)] + 0)[0][0])
               for g, r in zip(arr["grid_ids"], REGION) if r == "shield"]
WR = 2 * np.pi * np.maximum(FR, 1e-6)
KEEP = FR >= 1.0


def fem_transfer(grid_out, grid_in, freqs):
    # SPC'd nodes (feet) are grounded in the nominal model -> a force there does
    # nothing (degenerate). Flag rather than fake it (model-form gap; D42).
    if grid_out in SPC_GRIDS or grid_in in SPC_GRIDS:
        return np.zeros(freqs.size)
    po, pi = PHI[mrow(grid_out)], PHI[mrow(grid_in)]
    w = 2 * np.pi * freqs
    H = np.zeros(w.size, complex)
    for r in np.where(KEEP)[0]:
        H += po[r] * pi[r] / (WR[r] ** 2 - w ** 2 + 2j * ZETA * WR[r] * w)
    return np.abs(-w ** 2 * H)


def fem_acoustic(grid_out, freqs):
    """Response at out node to a uniform pressure over the shield (modal force
    f_r ~ sum of phi_r over shield X-dofs), times pink input shape 1/sqrt(f)."""
    po = PHI[mrow(grid_out)]
    fr_force = PHI[np.ix_(SHIELD_ROWS, np.arange(FR.size))].sum(axis=0)
    w = 2 * np.pi * freqs
    H = np.zeros(w.size, complex)
    for r in np.where(KEEP)[0]:
        H += fr_force[r] * po[r] / (WR[r] ** 2 - w ** 2 + 2j * ZETA * WR[r] * w)
    return np.abs(-w ** 2 * H) / np.sqrt(np.maximum(freqs, 1.0))   # pink tilt


def acoustic_test(fn, win):
    a = load(fn)
    n = int(len(a))
    t = np.arange(n) / FS
    seg = a[(t >= win[0]) & (t <= win[1])]
    nper = int(8 * FS)
    f, p = welch(seg, FS, nperseg=nper, noverlap=nper // 2, detrend="constant")
    return f, np.sqrt(p)


def norm_band(f, y, band=FNORM):
    m = (f >= band[0]) & (f <= band[1])
    pk = y[m].max() if m.any() and y[m].max() > 0 else 1.0
    return y / pk


def pick(f, y, band=FPICK, n=8):
    m = (f >= band[0]) & (f <= band[1])
    ff, yy = f[m], y[m]
    if yy.size == 0 or yy.max() <= 0:
        return []
    df = np.median(np.diff(ff))
    pi, _ = find_peaks(yy, prominence=0.08 * yy.max(), distance=max(1, int(1.5 / df)))
    order = pi[np.argsort(yy[pi])[::-1]][:n]
    return sorted([round(float(ff[i]), 2) for i in order])


def nearest_fem(peaks):
    out = []
    for p in peaks:
        k = int(np.argmin(np.abs(FR - p)))
        out.append(dict(test_hz=p, fem_hz=round(float(FR[k]), 2),
                        err_pct=round(100 * (p - FR[k]) / FR[k], 1)))
    return out


def thin(f, y, npts=1300):
    m = f <= FSHOW
    f, y = f[m], y[m]
    idx = np.unique(np.linspace(0, f.size - 1, npts).astype(int))
    return [f[idx].tolist(), np.array(y)[idx].round(5).tolist()]


LABEL = {"interface": "Top-center interface", "shield_mid": "Shield middle",
         "top_left": "Top-left steel beam", "valve": "Valve (QOI)",
         "box": "Electronics-box foot (QOI)", "engine_beam": "Engine beam",
         "foot": "Front-left foot"}
ffem = np.linspace(2, FSHOW, 4000)

out = dict(contract=__doc__[:1500], fs_hz=FS, assumed_damping=ZETA,
           window_s=WIN_S, sat_reject_ms2=SAT, norm_band_hz=FNORM,
           locations_label=LABEL, transfer={}, acoustic={}, qoi={})

# ---- (A) tap transfer matrix ----
for skey, S in SETUPS.items():
    a = load(S["tap_file"])
    for tloc, onsets in S["taps"].items():
        ftap, ytap, nused, log = tap_spectrum(a, onsets, S["all_events"])
        yt = norm_band(ftap, ytap)
        yf = norm_band(ffem, fem_transfer(GRID[S["resp"]], GRID[tloc], ffem))
        tpk = pick(ftap, yt)
        key = f"resp_{skey}__tap_{tloc}"
        out["transfer"][key] = dict(
            resp=skey, tap_loc=tloc, n_taps_used=nused, tap_log=log,
            is_drive_point=(skey == tloc),
            tap_peaks_hz=tpk, tap_vs_fem=nearest_fem(tpk),
            curves=dict(test=thin(ftap, yt), fem=thin(ffem, yf)))
        print(f"[transfer {skey} <- tap {tloc}] taps used {nused}/{len(onsets)}"
              f"  peaks {tpk}")
        for L in log:
            if "rejected" in L["status"]:
                print(f"    onset {L['onset']}: {L['status']}")

# ---- (B) acoustic with FEM acoustic forcing ----
for skey, S in SETUPS.items():
    fac, yac = acoustic_test(S["acoustic_file"], S["acoustic_win"])
    yt = norm_band(fac, yac)
    yf = norm_band(ffem, fem_acoustic(GRID[S["resp"]], ffem))
    apk = pick(fac, yt)
    out["acoustic"][skey] = dict(
        resp=skey, acoustic_peaks_hz=apk, acoustic_vs_fem=nearest_fem(apk),
        forcing="FEM = uniform pressure over shield (normal-incidence plane "
                "wave); valid where wavelength>>panel (low freq), FLAGGED",
        curves=dict(test=thin(fac, yt), fem=thin(ffem, yf)))
    print(f"[acoustic {skey}] peaks {apk}")

# ---- (C) QOI points: valve + box feet (tap @ engine beam + acoustic) ----
for qkey, Q in QOI.items():
    a = load(Q["tap_file"])
    ftap, ytap, nused, log = tap_spectrum(a, Q["taps"], Q["all_events"])
    yt = norm_band(ftap, ytap)
    yf_tap = norm_band(ffem, fem_transfer(GRID[Q["resp"]], GRID[Q["tap_loc"]],
                                          ffem))
    fac, yac = acoustic_test(Q["acoustic_file"], Q["acoustic_win"])
    ya = norm_band(fac, yac)
    yf_ac = norm_band(ffem, fem_acoustic(GRID[Q["resp"]], ffem))
    tpk, apk = pick(ftap, yt), pick(fac, ya)
    out["qoi"][qkey] = dict(
        resp=Q["resp"], tap_loc=Q["tap_loc"], n_taps_used=nused, tap_log=log,
        weak_acoustic=Q.get("weak_acoustic", False),
        tap_peaks_hz=tpk, tap_vs_fem=nearest_fem(tpk),
        acoustic_peaks_hz=apk, acoustic_vs_fem=nearest_fem(apk),
        curves=dict(tap_test=thin(ftap, yt), tap_fem=thin(ffem, yf_tap),
                    ac_test=thin(fac, ya), ac_fem=thin(ffem, yf_ac)))
    print(f"[QOI {qkey}] resp={Q['resp']} taps {nused}/{len(Q['taps'])} "
          f"tap peaks {tpk}; acoustic peaks {apk}")

with open(os.path.join(WS, "out", "pseudo_frf.json"), "w") as fh:
    json.dump(out, fh)
print("wrote out/pseudo_frf.json")
