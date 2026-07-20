#!/usr/bin/env python3
"""full_eig — full-order eigensolution of the INHERITED FEM (theta=1) up to F_TOP_HZ (card §5).

Reuses femlib (true-remodel workspace) READ-ONLY for model/blocks/T; the eigensolve loop, logging, and
outputs live in THIS workspace (out/eig_slices/, out/full_eig_summary.json). femlib.build_package is NOT
called (it writes into the other workspace). Spectrum-slice walk: repeated shift-invert eigsh at rising
shifts; slices deduped by eigenvalue proximity + M-orthogonality. Resumable: finished slices are skipped.

F_TOP_HZ = 1600 gives basis margin above the 1250 Hz reporting target (1.25 x an expected ~1000 Hz
certified ceiling); the REPORTED mode count is to 1250 Hz. All float64. Detached launch expected.
"""
from __future__ import annotations
import json, os, sys, time
import numpy as np
import scipy.sparse as sp
from scipy.sparse.linalg import eigsh

WS = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
TRM_CODE = os.path.abspath(os.path.join(WS, "..", "shocksat_true_remodel_loop_20260706", "code"))
sys.path.insert(0, TRM_CODE)
import femlib as F                                   # noqa: E402  (read-only reuse)

OUTD = os.path.join(WS, "out", "eig_slices")
os.makedirs(OUTD, exist_ok=True)
F_TOP_HZ = 1600.0
LAM_TOP = (2 * np.pi * F_TOP_HZ) ** 2
K_SLICE = 150
RTOL_DEDUP = 1e-7


def lam2f(lam):
    return np.sqrt(np.clip(lam, 0, None)) / (2 * np.pi)


def main():
    t0 = time.time()
    print("assembling inherited model (theta=1) ...", flush=True)
    m = F.load_model()
    blocks = F.baseline_blocks(m)
    M = blocks.pop("__M__")
    Ktot = None
    for name, Kb in blocks.items():
        Ktot = Kb if Ktot is None else Ktot + Kb
    T, keep = F.build_T(m)
    Kr = (T.T @ (Ktot @ T)).tocsc()
    Mr = (T.T @ (M @ T)).tocsc()
    n = Kr.shape[0]
    print(f"reduced system {n} DOF; assembly {time.time()-t0:.0f}s", flush=True)

    lams, vecs = [], []
    slices_meta = []
    si = 0
    sigma = F.SIGMA_SHIFT                        # -1e3: first slice = lowest modes incl. RBMs
    lam_hi = 0.0
    while True:
        sl_path = os.path.join(OUTD, f"slice_{si:02d}.npz")
        if os.path.exists(sl_path):
            z = np.load(sl_path)
            lam_s, V_s, sigma = z["lam"], z["V"], float(z["sigma"])
            print(f"slice {si}: loaded (resume) sigma={sigma:.3e} "
                  f"[{lam2f(lam_s.min()):.1f}-{lam2f(lam_s.max()):.1f} Hz]", flush=True)
        else:
            ts = time.time()
            print(f"slice {si}: eigsh k={K_SLICE} sigma={sigma:.4e} "
                  f"(~{lam2f(max(sigma,0)):.0f} Hz) ...", flush=True)
            lam_s, V_s = eigsh(Kr, k=K_SLICE, M=Mr, sigma=sigma, which="LM")
            np.savez_compressed(sl_path, lam=lam_s, V=V_s.astype(np.float64), sigma=sigma)
            print(f"  slice {si}: {time.time()-ts:.0f}s, "
                  f"[{lam2f(lam_s.min()):.1f}-{lam2f(lam_s.max()):.1f} Hz]", flush=True)
        order = np.argsort(lam_s)
        lam_s, V_s = lam_s[order], V_s[:, order]
        # dedupe against already-kept eigenvalues
        new_idx = []
        kept = np.concatenate(lams) if lams else np.array([])
        for j, lv in enumerate(lam_s):
            if kept.size and np.any(np.abs(kept - lv) <= RTOL_DEDUP * max(abs(lv), 1.0) + 1e-3):
                continue
            new_idx.append(j)
        if new_idx:
            lams.append(lam_s[new_idx]); vecs.append(V_s[:, new_idx])
        slices_meta.append({"slice": si, "sigma": sigma, "n_new": len(new_idx),
                            "f_lo": float(lam2f(lam_s.min())), "f_hi": float(lam2f(lam_s.max()))})
        lam_all = np.sort(np.concatenate(lams))
        # coverage check: contiguous from 0 up to the max of THIS slice
        lam_hi = max(lam_hi, lam_s.max())
        if lam_hi >= LAM_TOP:
            break
        sigma = 0.95 * float(lam_s.max())        # next shift just below current top (slice overlap)
        si += 1
        if si > 40:
            raise RuntimeError("too many slices; aborting")

    lam_all = np.concatenate(lams)
    V_all = np.hstack(vecs)
    order = np.argsort(lam_all)
    lam_all, V_all = lam_all[order], V_all[:, order]
    inb = lam_all <= LAM_TOP
    lam_all, V_all = lam_all[inb], V_all[:, inb]
    # M-orthonormality audit on the merged set (dedupe integrity; sample to keep it cheap)
    G = V_all.T @ (Mr @ V_all)
    off = np.abs(G - np.diag(np.diag(G)))
    print(f"merged {lam_all.size} modes to {F_TOP_HZ} Hz; max |M-cross| {off.max():.2e}", flush=True)
    if off.max() > 1e-6:
        # renormalize / drop duplicates via Gram
        good = [0]
        for j in range(1, lam_all.size):
            if np.all(np.abs(G[j, good]) < 1e-6):
                good.append(j)
        print(f"dropped {lam_all.size - len(good)} duplicate vectors by M-orthogonality", flush=True)
        lam_all, V_all = lam_all[good], V_all[:, good]
        G = V_all.T @ (Mr @ V_all)
    V_all = V_all / np.sqrt(np.diag(G))[None, :]
    freqs = lam2f(lam_all)
    n_rbm = int((freqs < 10.0).sum())
    np.savez_compressed(os.path.join(WS, "out", "full_eig_theta1.npz"),
                        lam=lam_all, freqs=freqs, n_rbm=n_rbm, keep=keep)
    np.save(os.path.join(WS, "out", "full_eig_V.npy"), V_all)   # (n_keepdof, n_modes) float64
    summ = {"n_dof": int(Kr.shape[0]), "f_top_hz": F_TOP_HZ, "n_modes_total": int(freqs.size),
            "n_rbm": n_rbm,
            "n_elastic_to_1250": int(((freqs >= 10) & (freqs <= 1250)).sum()),
            "n_elastic_to_1000": int(((freqs >= 10) & (freqs <= 1000)).sum()),
            "n_elastic_to_500": int(((freqs >= 10) & (freqs <= 500)).sum()),
            "n_elastic_to_260": int(((freqs >= 10) & (freqs <= 260)).sum()),
            "slices": slices_meta, "active_s": round(time.time() - t0, 1)}
    json.dump(summ, open(os.path.join(WS, "out", "full_eig_summary.json"), "w"), indent=1)
    with open(os.path.join(WS, "out", "runtime_log.jsonl"), "a") as f:
        f.write(json.dumps({"step": "full_eig", "active_s": round(time.time() - t0, 1)}) + "\n")
    print(json.dumps(summ, indent=1), flush=True)


if __name__ == "__main__":
    main()
