#!/usr/bin/env python3
"""full_eig2 — SINGLE definite-shift full-order eigensolve of the inherited FEM (theta=1), k=K_ALL lowest
modes (card §5). Replaces the interior-shift slice walk of full_eig.py after measuring that interior
shifts cost 35-90+ min per 150 modes vs ~5 min at the definite shift sigma=-1e3 (decisions D8).
The k lowest modes come out of ONE factorization — no slicing, no dedupe. Slices 0-1 from full_eig.py are
kept as independent cross-checks (out/full_eig_crosscheck.json). Outputs identical to full_eig.py
(out/full_eig_theta1.npz + out/full_eig_V.npy + out/full_eig_summary.json). Detached launch expected."""
from __future__ import annotations
import json, os, sys, time
import numpy as np
from scipy.sparse.linalg import eigsh

WS = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
TRM_CODE = os.path.abspath(os.path.join(WS, "..", "shocksat_true_remodel_loop_20260706", "code"))
sys.path.insert(0, TRM_CODE)
import femlib as F                                   # noqa: E402  (read-only reuse)

K_ALL = 560          # D9: k=650/ncv=1301 thrashed a 16 GB machine (9.4 GB RSS, 40% duty); 560/840 fits.
NCV = 840            # 840 x 399510 x 8 B = 2.7 GB Lanczos basis; expected top ~1300 Hz >= 1250 target.


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
    print(f"reduced system {Kr.shape[0]} DOF; eigsh k={K_ALL} sigma={F.SIGMA_SHIFT} ...", flush=True)
    ts = time.time()
    lam, V = eigsh(Kr, k=K_ALL, M=Mr, sigma=F.SIGMA_SHIFT, which="LM", ncv=NCV)
    idx = np.argsort(lam); lam, V = lam[idx], V[:, idx]
    dt = time.time() - ts
    freqs = np.sqrt(np.clip(lam, 0, None)) / (2 * np.pi)
    n_rbm = int((freqs < 10.0).sum())
    print(f"solve {dt:.0f}s: {K_ALL} modes, top {freqs[-1]:.1f} Hz, n_rbm={n_rbm}", flush=True)
    # M-orthonormality audit
    G = V.T @ (Mr @ V)
    off = np.abs(G - np.diag(np.diag(G))).max()
    V = V / np.sqrt(np.diag(G))[None, :]
    np.savez_compressed(os.path.join(WS, "out", "full_eig_theta1.npz"),
                        lam=lam, freqs=freqs, n_rbm=n_rbm, keep=keep)
    np.save(os.path.join(WS, "out", "full_eig_V.npy"), V)
    # cross-check vs the interior-shift slices (independent factorizations)
    xc = {}
    for si in (0, 1):
        p = os.path.join(WS, "out", "eig_slices", f"slice_{si:02d}.npz")
        if os.path.exists(p):
            z = np.load(p)
            lam_s = np.sort(np.asarray(z["lam"]))
            errs = []
            for lv in lam_s:
                j = int(np.argmin(np.abs(lam - lv)))
                errs.append(abs(lam[j] - lv) / max(abs(lv), 1.0))
            xc[f"slice_{si}"] = {"n": int(lam_s.size), "max_rel_lam_err": float(np.max(errs)),
                                 "median_rel_lam_err": float(np.median(errs))}
    summ = {"n_dof": int(Kr.shape[0]), "k": K_ALL, "top_hz": float(freqs[-1]), "n_rbm": n_rbm,
            "n_elastic_to_1250": int(((freqs >= 10) & (freqs <= 1250)).sum()),
            "n_elastic_to_1000": int(((freqs >= 10) & (freqs <= 1000)).sum()),
            "n_elastic_to_500": int(((freqs >= 10) & (freqs <= 500)).sum()),
            "n_elastic_to_260": int(((freqs >= 10) & (freqs <= 260)).sum()),
            "m_orth_offdiag_max": float(off), "crosscheck_vs_slices": xc,
            "solve_s": round(dt, 1), "active_s": round(time.time() - t0, 1)}
    json.dump(summ, open(os.path.join(WS, "out", "full_eig_summary.json"), "w"), indent=1)
    json.dump(xc, open(os.path.join(WS, "out", "full_eig_crosscheck.json"), "w"), indent=1)
    with open(os.path.join(WS, "out", "runtime_log.jsonl"), "a") as f:
        f.write(json.dumps({"step": "full_eig2", "active_s": round(time.time() - t0, 1)}) + "\n")
    with open(os.path.join(WS, "out", "eigensolve_log.jsonl"), "a") as f:
        f.write(json.dumps({"tag": "full_eig2_k650", "cid": "A0_wide_basis", "n_dof": int(Kr.shape[0]),
                            "t_s": round(dt, 1), "ts": time.strftime("%Y-%m-%dT%H:%M:%S")}) + "\n")
    print(json.dumps(summ, indent=1), flush=True)


if __name__ == "__main__":
    main()
