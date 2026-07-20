#!/usr/bin/env python3
"""DETERMINISTIC FE model updating (D42): tune FEM group scalars to improve
FEM-vs-test peak-FREQUENCY correlation on the box-FOOT tap-transfer FRFs
(tap @ engine beam -> accel @ box foot). ONLY tap-transfer data is used for
tuning. This is a best-fit POINT estimate, NOT a posterior / NUTS / UQ; see
tuning_changelog.md for goal + overfitting guard.

Method: coordinate descent over a few uncertain ("yellow") group scalars, each
on a log grid; accept a move only if it lowers the box-foot score AND does not
degrade the HELD-OUT stand transfer set by > 1.0 pp. Every accepted move is a
changelog row. Modal re-solve uses the cheap per-group reassembly + exact
massless condensation (subset to 110 Hz).

Outputs: tuning_result.json, appends rows to tuning_changelog.md.
"""
import json
import os
import time

import numpy as np
import scipy.linalg as sla
import scipy.sparse as sp
import scipy.sparse.linalg as spla

WS = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MODEL = os.path.join(WS, "out", "model")
meta = json.load(open(os.path.join(MODEL, "meta.json")))
arr = np.load(os.path.join(MODEL, "arrays.npz"))
spc_idx = arr["spc_master_idx"]
MD = arr["master_dofs"]
NM = meta["ndof_master"]
GP = {int(g): i for i, g in enumerate(arr["grid_ids"])}
NOM = dict(meta["nominal_scalars"])
ZETA = 0.03
FMAXHZ = 110.0
KG = {n: sp.load_npz(os.path.join(MODEL, "groups", f"K_{n}.npz"))
      for n in meta["K_groups"]}
MG = {n: sp.load_npz(os.path.join(MODEL, "groups", f"M_{n}.npz"))
      for n in meta["M_groups"]}
GRID = dict(interface=800071, shield_mid=800038, top_left=1510,
            engine_beam=952, box=900002)


def mrow(grid):
    return int(np.where(MD == 6 * GP[grid] + 0)[0][0])


MROW = {k: mrow(g) for k, g in GRID.items()}


def build(scal):
    K = M = None
    for n, A in KG.items():
        s = scal.get("K_" + n, 1.0)
        if s:
            K = s * A if K is None else K + s * A
    for n, A in MG.items():
        s = scal.get("M_" + n, 1.0)
        if s:
            M = s * A if M is None else M + s * A
    return K.tocsr(), M.tocsr()


def solve(scal):
    K, M = build(scal)
    free = np.setdiff1d(np.arange(NM), spc_idx)
    dead = free[K.diagonal()[free] == 0.0]
    free = np.setdiff1d(free, dead)
    Kf, Mf = K[np.ix_(free, free)].tocsc(), M[np.ix_(free, free)].tocsr()
    md = np.where(Mf.diagonal() > 0)[0]
    zd = np.where(Mf.diagonal() == 0)[0]
    lu = spla.splu(Kf[np.ix_(zd, zd)].tocsc())
    S = lu.solve(Kf[np.ix_(zd, md)].toarray())
    Kred = Kf[np.ix_(md, md)].toarray() - Kf[np.ix_(md, zd)].toarray() @ S
    Mred = Mf[np.ix_(md, md)].toarray()
    Kred = 0.5 * (Kred + Kred.T)
    w2, V = sla.eigh(Kred, Mred, subset_by_value=(-np.inf, (2 * np.pi * FMAXHZ) ** 2),
                     driver="gvx")
    fr = np.sign(w2) * np.sqrt(np.abs(w2)) / (2 * np.pi)
    Phi = np.zeros((NM, V.shape[1]))
    Phif = np.zeros((free.size, V.shape[1]))
    Phif[md] = V
    Phif[zd] = -S @ V
    Phi[free] = Phif
    return fr, Phi


def transfer_peaks(fr, Phi, out_key, in_key, band=(5, 90)):
    po, pi = Phi[MROW[out_key]], Phi[MROW[in_key]]
    f = np.linspace(2, FMAXHZ, 3000)
    w = 2 * np.pi * f
    wr = 2 * np.pi * np.maximum(fr, 1e-6)
    H = np.zeros(w.size, complex)
    for r in range(fr.size):
        if fr[r] < 1.0:
            continue
        H += po[r] * pi[r] / (wr[r] ** 2 - w ** 2 + 2j * ZETA * wr[r] * w)
    y = np.abs(-w ** 2 * H)
    from scipy.signal import find_peaks
    m = (f >= band[0]) & (f <= band[1])
    ff, yy = f[m], y[m]
    if yy.max() <= 0:
        return []
    pk, _ = find_peaks(yy, prominence=0.06 * yy.max(),
                       distance=max(1, int(1.5 / np.median(np.diff(ff)))))
    return sorted(ff[pk].tolist())


def match_score(targets, fem_peaks, cap=8.0):
    if not fem_peaks:
        return cap, cap, 0
    errs = []
    for t in targets:
        e = min(abs(t - p) / t * 100 for p in fem_peaks)
        errs.append(min(e, cap))
    errs = np.array(errs)
    return float(np.median(errs)), float(errs.max()), int((errs < cap).sum())


# ---- targets (box-foot repeatable tap-transfer peaks) + held-out set ----
pf = json.load(open(os.path.join(WS, "out", "pseudo_frf.json")))
L = pf["qoi"]["box_foot_left"]["tap_peaks_hz"]
R = pf["qoi"]["box_foot_right"]["tap_peaks_hz"]
TARGETS = sorted(set(round((a + min(R, key=lambda x: abs(x - a))) / 2, 1)
                     for a in L
                     if min(abs(a - r) / a for r in R) < 0.05))
HELDOUT = {}   # (resp,tap) -> measured peaks, stand transfer only
for key, T in pf["transfer"].items():
    if T["tap_peaks_hz"]:
        HELDOUT[(T["resp"], T["tap_loc"])] = T["tap_peaks_hz"]


def box_score(scal):
    fr, Phi = solve(scal)
    fem = transfer_peaks(fr, Phi, "box", "engine_beam")
    return match_score(TARGETS, fem), fr, Phi


def heldout_score(scal):
    fr, Phi = solve(scal)
    errs = []
    for (rk, tk), meas in HELDOUT.items():
        if rk not in MROW or tk not in MROW:
            continue
        fem = transfer_peaks(fr, Phi, rk, tk)
        s, _, _ = match_score(meas, fem)
        errs.append(s)
    return float(np.median(errs)) if errs else None


def log_row(label, bscore, hscore, accept):
    med, mx, nm = bscore
    line = (f"| {label} | {med:.2f} | {mx:.2f} | {nm} | "
            f"{hscore:.2f} | {'YES' if accept else 'no'} |\n")
    with open(os.path.join(WS, "tuning_changelog.md"), "a") as fh:
        fh.write(line)


if __name__ == "__main__":
    t0 = time.time()
    print("TARGETS (box-foot repeatable tap-transfer peaks, Hz):", TARGETS)
    # ---- baseline ----
    (b_med, b_mx, b_nm), _, _ = box_score(NOM)
    base_ho = heldout_score(NOM)
    print(f"BASELINE box-foot score: median {b_med:.2f}% max {b_mx:.2f}% "
          f"matched {b_nm}/{len(TARGETS)}; held-out median {base_ho:.2f}%")
    log_row("rev-7 baseline (no tuning)", (b_med, b_mx, b_nm), base_ho, True)

    # ---- coordinate descent over uncertain group scalars ----
    PARAMS = {                     # name -> (group keys, log grid multipliers)
        "M_ebox(mass)":  (["M_m_ebox"], [0.6, 0.8, 1.0, 1.3, 1.6, 2.0]),
        "K_att_ebox(box bolt)": (["K_att_ebox"], [0.1, 0.3, 1.0, 3.0, 10.0]),
        "K_shield_att(weld)": (["K_shield_att"], [0.1, 0.3, 1.0, 3.0, 10.0]),
        "K_frame(beam)": (["K_beam_wall", "K_beam_rest"],
                          [0.5, 0.7, 1.0, 1.4, 2.0]),
        "K_bush(joints)": (["K_bush_joints"], [0.3, 1.0, 3.0]),
        "K_shield(stiff)": (["K_shield_mem", "K_shield_bend"],
                            [0.7, 1.0, 1.4, 2.0]),
    }
    cur = dict(NOM)
    cur_score, _, _ = box_score(cur)
    cur_ho = base_ho
    history = [dict(label="baseline", score=cur_score, heldout=cur_ho,
                    scalars={k: v for k, v in cur.items() if v != 1.0})]
    for it in range(2):                          # 2 passes
        for pname, (keys, grid) in PARAMS.items():
            best = (cur_score, cur_ho, None)
            base_mult = cur.get(keys[0], 1.0)
            for mult in grid:
                trial = dict(cur)
                for k in keys:
                    trial[k] = NOM.get(k, 1.0) * mult
                (med, mx, nm), _, _ = box_score(trial)
                if med < best[0][0] - 0.05:       # improvement on primary
                    ho = heldout_score(trial)
                    if ho <= base_ho + 1.0:        # overfitting guard
                        best = ((med, mx, nm), ho, mult)
            if best[2] is not None:
                for k in keys:
                    cur[k] = NOM.get(k, 1.0) * best[2]
                cur_score, cur_ho = best[0], best[1]
                lbl = f"pass{it+1} {pname} x{best[2]}"
                print(f"  ACCEPT {lbl}: box {cur_score[0]:.2f}% "
                      f"max {cur_score[1]:.2f}% n{cur_score[2]} ho {cur_ho:.2f}%")
                log_row(lbl, cur_score, cur_ho, True)
                history.append(dict(label=lbl, score=cur_score, heldout=cur_ho,
                                    scalars={k: v for k, v in cur.items()
                                             if v != 1.0}))
        med0 = history[-1]["score"][0]
    goal_met = cur_score[0] <= 3.0 and cur_score[1] <= 6.0 and cur_score[2] >= 4
    out = dict(targets_hz=TARGETS, baseline=dict(
        box_median=b_med, box_max=b_mx, box_matched=b_nm, heldout_median=base_ho),
        final=dict(box_median=cur_score[0], box_max=cur_score[1],
                   box_matched=cur_score[2], heldout_median=cur_ho),
        goal_met_params_only=bool(goal_met),
        tuned_scalars={k: round(v, 4) for k, v in cur.items() if v != 1.0},
        history=history, elapsed_s=round(time.time() - t0, 1),
        note="DETERMINISTIC point estimate (NOT a posterior/NUTS). Box-foot "
             "tap-transfer ONLY for tuning; stand transfer held out.")
    json.dump(out, open(os.path.join(WS, "out", "tuning_result.json"), "w"),
              indent=1)
    print(f"\nFINAL box-foot median {cur_score[0]:.2f}% max {cur_score[1]:.2f}% "
          f"n{cur_score[2]}; held-out {cur_ho:.2f}%; goal(params)={goal_met}; "
          f"elapsed {time.time()-t0:.0f}s")
