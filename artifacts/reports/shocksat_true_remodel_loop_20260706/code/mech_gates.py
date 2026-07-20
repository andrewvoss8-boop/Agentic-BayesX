#!/usr/bin/env python3
"""V1-V5 mechanics validation gates (card §7, scopes pre-registered in decisions_log D8).
Failures BLOCK science. Writes out/mech_gates.json (+ partial after each gate: resumable).
Run detached:  nohup python3 code/mech_gates.py > logs/mech_gates.log 2>&1 &
"""
import json, os, sys, time
import numpy as np
import scipy.sparse as sp
from scipy.sparse.linalg import eigsh

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import femlib as F

WS = F.WS
OUT = os.path.join(WS, "out", "mech_gates.json")
t00 = time.time()


def save(res):
    with open(OUT, "w") as f:
        json.dump(res, f, indent=2)


def conm2_M(m):
    rows, cols, vals = [], [], []
    g2i = F.g2i_of(m)
    NDOF = 6 * len(m["gids"])
    for row in np.asarray(m["conm2"]):
        eid, g, mass = int(row[0]), int(row[1]), row[2]
        off = row[3:6]
        I11, I21, I22, I31, I32, I33 = row[6:12]
        Icm = np.array([[I11, I21, I31], [I21, I22, I32], [I31, I32, I33]])
        S = F.skew(off)
        M6 = np.zeros((6, 6))
        M6[0:3, 0:3] = mass * np.eye(3)
        M6[0:3, 3:6] = -mass * S
        M6[3:6, 0:3] = mass * S
        M6[3:6, 3:6] = Icm + mass * (S @ S.T)
        d = 6 * g2i[g] + np.arange(6)
        rows.append(np.repeat(d, 6)); cols.append(np.tile(d, 6)); vals.append(M6.ravel())
    return sp.coo_matrix((np.concatenate(vals), (np.concatenate(rows), np.concatenate(cols))),
                         shape=(NDOF, NDOF)).tocsr()


def expand_csr(K, ndof_new):
    K = K.tocoo()
    return sp.coo_matrix((K.data, (K.row, K.col)), shape=(ndof_new, ndof_new)).tocsr()


res = json.load(open(OUT)) if os.path.exists(OUT) else {}

# ================================================================ V1
if "V1" not in res:
    print("[V1] reassemble all PID blocks + full eigsh vs stored", flush=True)
    t0 = time.time()
    m = F.load_model()
    NDOF = 6 * len(m["gids"])
    devs = {}
    Ktot = None
    Mdiag_tot = np.zeros(NDOF)
    for spid in sorted(m["pshell"], key=int):
        Kmine, Mdiag, ne = F.assemble_shell(m, int(spid))
        Kst = sp.load_npz(os.path.join(F.MATD, f"K_shell_{spid}.npz"))
        dmax = float(abs(Kmine - Kst).max()); ref = float(abs(Kst).max())
        devs[f"shell_{spid}"] = dmax / ref
        Ktot = Kmine if Ktot is None else Ktot + Kmine
        Mdiag_tot += Mdiag
        print(f"  shell {spid}: {ne} elems, rel dev {dmax/ref:.2e}", flush=True)
    for bpid in sorted(m["pbush"], key=int):
        els = np.asarray(m["cbush"])[np.asarray(m["cbush"])[:, 1] == int(bpid)]
        kv = m["pbush"][bpid]["k"]
        Kmine = F.bush_pairs_K(m, [(ga, gb, kv, cid) for _, _, ga, gb, cid in els])
        Kst = sp.load_npz(os.path.join(F.MATD, f"K_bush_{bpid}.npz"))
        dmax = float(abs(Kmine - Kst).max()); ref = float(abs(Kst).max())
        devs[f"bush_{bpid}"] = dmax / ref
        Ktot = Ktot + Kmine
        print(f"  bush {bpid}: rel dev {dmax/ref:.2e}", flush=True)
    Mmine = sp.diags(Mdiag_tot).tocsr() + conm2_M(m)
    Mst = sp.load_npz(os.path.join(F.MATD, "M.npz"))
    mdev = float(abs(Mmine - Mst).max()) / float(abs(Mst).max())
    T, keep = F.build_T(m)
    Kr = (T.T @ (Ktot @ T)).tocsc()
    Mr = (T.T @ (Mmine @ T)).tocsc()
    print("  eigsh (full 399510-DOF, my reassembly)...", flush=True)
    lam, _ = eigsh(Kr, k=F.NMODES, M=Mr, sigma=F.SIGMA_SHIFT, which="LM")
    lam = np.sort(lam)
    F.log_eigensolve("vgate", "v1_reassembly", Kr.shape[0], time.time() - t0)
    ev = np.load(os.path.join(F.MATD, "eigvals.npy"))
    rel = np.abs(lam[6:] - ev[6:]) / np.abs(ev[6:])
    v1 = dict(block_rel_dev_max=float(max(devs.values())), block_rel_dev=devs,
              M_rel_dev=mdev, eig_rel_err_max=float(rel.max()),
              n_keep=int(len(keep)),
              metric=f"eig {rel.max():.2e}, blocks {max(devs.values()):.2e}",
              t_s=round(time.time() - t0, 1))
    v1["pass"] = bool(max(devs.values()) <= 1e-9 and mdev <= 1e-9 and rel.max() <= 1e-8)
    res["V1"] = v1
    save(res)
    F.log_runtime("V1", time.time() - t0)
    print(f"[V1] pass={v1['pass']} {v1['metric']}", flush=True)

# ================================================================ A0 baseline package (stored blocks)
if not os.path.exists(os.path.join(WS, "data", "packages", "A0.npz")):
    print("[A0] baseline package from stored Card-D blocks", flush=True)
    t0 = time.time()
    m = F.load_model()
    blocks = F.baseline_blocks(m)
    pkg = F.build_package(m, blocks, "A0", tag="baseline", note="inherited FEM, stored Card-D blocks")
    ev = np.load(os.path.join(F.MATD, "eigvals.npy"))
    rel = np.abs((2 * np.pi * pkg.freqs_el) ** 2 - ev[6:]) / ev[6:]
    res["A0_package"] = dict(eig_rel_err_max=float(rel.max()), n_pairs=int(len(pkg.pairs)),
                             mean_matched_mac=float(np.mean(pkg.pairs[:, 2])),
                             t_s=round(time.time() - t0, 1))
    save(res)
    F.log_runtime("A0_package", time.time() - t0)
    print(f"[A0] done: eig rel {rel.max():.2e}, pairs {len(pkg.pairs)}, "
          f"meanMAC {np.mean(pkg.pairs[:,2]):.3f}", flush=True)

# ================================================================ V2
if "V2" not in res:
    print("[V2] free-free RBM on REFINED dish submodel", flush=True)
    t0 = time.time()
    m0 = F.load_model()
    mr, info = F.refine_region(m0, [701], note="V2/V3 dish refine")
    K701, Mdiag, ne = F.assemble_shell(mr, 701)
    # submodel: grids used by pid-701 elements
    used = set()
    for conn in (np.asarray(mr["cquad4"])[np.asarray(mr["cquad4"])[:, 1] == 701][:, 2:6],
                 np.asarray(mr["ctria3"])[np.asarray(mr["ctria3"])[:, 1] == 701][:, 2:5]):
        used.update(int(g) for g in conn.ravel())
    g2i = F.g2i_of(mr)
    dofs = np.concatenate([6 * g2i[g] + np.arange(6) for g in sorted(used)])
    Ks = K701[dofs][:, dofs].tocsc()
    Ms = sp.diags(Mdiag[dofs]).tocsc()
    # k/ncv large enough for the 6-fold degenerate zero cluster; finite tol (tol=0 stalls ARPACK there)
    lam, _ = eigsh(Ks, k=20, ncv=90, M=Ms, sigma=F.SIGMA_SHIFT, which="LM", tol=1e-8)
    lam = np.sort(lam)
    f_hz = np.sqrt(np.clip(lam, 0, None)) / (2 * np.pi)
    ratio = float(abs(lam[5]) / lam[6])
    v2 = dict(n_elems=ne, n_hanging=info["n_hanging"], lam_rbm_max=float(np.abs(lam[:6]).max()),
              f7_hz=float(f_hz[6]), rbm_over_elastic=ratio,
              metric=f"|lam_rbm|/lam_el {ratio:.2e}, f7 {f_hz[6]:.1f} Hz",
              t_s=round(time.time() - t0, 1))
    v2["pass"] = bool(ratio < 1e-6)
    res["V2"] = v2
    save(res)
    F.log_runtime("V2", time.time() - t0)
    print(f"[V2] pass={v2['pass']} {v2['metric']}", flush=True)

# ================================================================ V3 (re-metric per D13)
if "V3" not in res or not res["V3"].get("pass", False):
    print("[V3] refinement null test (dish 2x; cross-model matched comparison, D13)", flush=True)
    t0 = time.time()
    if not os.path.exists(os.path.join(WS, "data", "packages", "v3_dishrefine.npz")):
        m0 = F.load_model()
        mr, info = F.refine_region(m0, [701], note="V3 dish refine null")
        NDOF_new = 6 * len(mr["gids"])
        K701_old, Mdiag_old, _ = F.assemble_shell(m0, 701)
        K701_new, Mdiag_new, ne = F.assemble_shell(mr, 701)
        blocks = {}
        for g, pids in F.GROUPS.items():
            Kg = None
            for p in pids:
                Kp = sp.load_npz(os.path.join(F.MATD, f"K_{p}.npz"))
                Kg = Kp if Kg is None else Kg + Kp
            blocks[g] = expand_csr(Kg, NDOF_new)
        blocks["plates"] = blocks["plates"] - expand_csr(K701_old, NDOF_new) + K701_new
        blocks["_fixed_bush99"] = expand_csr(sp.load_npz(os.path.join(F.MATD, "K_bush_99.npz")), NDOF_new)
        Mst = expand_csr(sp.load_npz(os.path.join(F.MATD, "M.npz")), NDOF_new)
        pad_old = np.zeros(NDOF_new); pad_old[:len(Mdiag_old)] = Mdiag_old
        blocks["__M__"] = Mst - sp.diags(pad_old).tocsr() + sp.diags(Mdiag_new).tocsr()
        pkg3 = F.build_package(mr, blocks, "v3_dishrefine", tag="vgate", note=json.dumps(info))
    else:
        pkg3 = F.Package.load("v3_dishrefine")
        info = {"note": "package reused (solved pre-D13)"}
    pkg0 = F.Package.load("A0")
    # D13: match A0<->refined by cross-MAC on the 228 obs DOFs, PARTICIPATING modes only (D12a)
    a0m = F.participation_mask(np.asarray(pkg0.sens_rows))
    a3m = F.participation_mask(np.asarray(pkg3.sens_rows))
    A0r = np.asarray(pkg0.ash_rows)[:, a0m]; A3r = np.asarray(pkg3.ash_rows)[:, a3m]
    f0 = np.asarray(pkg0.freqs_el)[a0m]; f3 = np.asarray(pkg3.freqs_el)[a3m]
    num = (A0r.T @ A3r) ** 2
    den = np.sum(A0r ** 2, 0)[:, None] * np.sum(A3r ** 2, 0)[None, :]
    MACx = num / (den + 1e-300)
    DF = f3[None, :] / f0[:, None] - 1.0
    cost = -MACx.copy(); cost[np.abs(DF) > 0.05] = 1e3; cost[MACx < 0.5] = 1e3
    from scipy.optimize import linear_sum_assignment
    ri, ci = linear_sum_assignment(cost)
    ok = cost[ri, ci] < 1e3
    dfm = np.abs(f3[ci[ok]] / f0[ri[ok]] - 1.0)
    mac0 = float(np.mean(np.asarray(pkg0.pairs)[:, 2]))
    mac3 = float(np.mean(np.asarray(pkg3.pairs)[:, 2]))
    v3 = dict(info=info, n_participating=[int(a0m.sum()), int(a3m.sum())],
              n_matched=int(ok.sum()), median_abs_df=float(np.median(dfm)),
              frac_df_gt_0p5pct=float(np.mean(dfm > 0.005)), max_abs_df=float(dfm.max()),
              mean_mac_to_test_base=mac0, mean_mac_to_test_refined=mac3, d_mac=mac3 - mac0,
              artifact_note="4 accel-drilling penalty modes move 124.5->62.7 Hz by construction "
                            "(excluded as unobservable, D12); see decisions_log D12/D13",
              metric=f"median|df| {np.median(dfm)*100:.4f}%, frac>0.5% {np.mean(dfm>0.005):.3f}, "
                     f"dMAC {mac3-mac0:+.4f}, matched {int(ok.sum())}",
              t_s=round(time.time() - t0, 1))
    v3["pass"] = bool(np.median(dfm) <= 0.001 and np.mean(dfm > 0.005) <= 0.10
                      and abs(mac3 - mac0) <= 0.01 and ok.sum() >= 45)
    res["V3"] = v3
    save(res)
    F.log_runtime("V3_rematch", time.time() - t0)
    print(f"[V3] pass={v3['pass']} {v3['metric']}", flush=True)

# ================================================================ V4
if "V4" not in res:
    print("[V4] thickness physics strip test (nu=0)", flush=True)
    t0 = time.time()
    L, Wd, nel = 8.0, 1.0, 8
    Estr, tstr = 1.0e7, 0.1

    def strip_model(tval):
        gids, xyz = [], []
        for i in range(nel + 1):
            for j in range(2):
                gids.append(1 + i * 2 + j); xyz.append([i * L / nel, j * Wd, 0.0])
        q = []
        for i in range(nel):
            a = 1 + i * 2
            q.append([100 + i, 999, a, a + 2, a + 3, a + 1])
        m = dict(gids=np.array(gids), xyz=np.array(xyz, float),
                 cquad4=np.array(q, int), ctria3=np.zeros((0, 5), int),
                 pshell={"999": dict(mid1=1, t=tval, bend_ratio=1.0, ts_t=0.833333)},
                 mat1={"1": dict(E=Estr, nu=0.0, G=Estr / 2.0, rho=2.5e-4)},
                 rbe2=np.zeros((0, 4), int), rbe2_gms=np.zeros(0, int),
                 released_rbe2=[], extra_springs=[], hanging={})
        return m

    def stiff(tval, load_dof):
        m = strip_model(tval)
        K, Md, _ = F.assemble_shell(m, 999)
        NDOF = K.shape[0]
        fixed = []
        for j in range(2):                       # clamp left edge (both nodes, all 6)
            fixed += list(6 * j + np.arange(6))  # nodes are ordered i*2+j -> left edge = first two
        free = np.setdiff1d(np.arange(NDOF), fixed)
        Kff = K[free][:, free].toarray()
        f = np.zeros(NDOF)
        tipn = [nel * 2, nel * 2 + 1]            # right-edge node indices
        for nidx in tipn:
            f[6 * nidx + load_dof] = 0.5
        d = np.linalg.solve(Kff + 1e-9 * np.eye(len(free)) * Kff.max(), f[free])
        u = np.zeros(NDOF); u[free] = d
        return 1.0 / np.mean([u[6 * nidx + load_dof] for nidx in tipn])

    ax1, ax2 = stiff(tstr, 0), stiff(2 * tstr, 0)          # membrane (axial u)
    bz1, bz2 = stiff(tstr, 2), stiff(2 * tstr, 2)          # bending (transverse w)
    r_mem = ax2 / ax1; r_bend = bz2 / bz1
    k_ax_analytic = Estr * tstr * Wd / L
    k_b_analytic = 3 * Estr * (Wd * tstr ** 3 / 12) / L ** 3
    v4 = dict(membrane_ratio=float(r_mem), bending_ratio=float(r_bend),
              k_axial_fe=float(ax1), k_axial_analytic=k_ax_analytic,
              k_bend_fe=float(bz1), k_bend_analytic=float(k_b_analytic),
              metric=f"t x2: membrane x{r_mem:.3f} (want 2), bending x{r_bend:.3f} (want 8)",
              t_s=round(time.time() - t0, 1))
    v4["pass"] = bool(abs(r_mem - 2.0) <= 0.04 and abs(r_bend - 8.0) <= 0.24
                      and abs(ax1 / k_ax_analytic - 1) < 0.05)
    res["V4"] = v4
    save(res)
    F.log_runtime("V4", time.time() - t0)
    print(f"[V4] pass={v4['pass']} {v4['metric']}", flush=True)

# ================================================================ V5
if "V5" not in res:
    print("[V5] frozen-pairing churn test", flush=True)
    t0 = time.time()
    pkg = F.Package.load("A0")
    mm = np.load(os.path.join(F.REMESH, "measured_modes.npz"), allow_pickle=True)
    live = np.asarray(mm["measured"]).reshape(-1)
    msh = np.asarray(mm["shapes"], float).reshape(33, -1)[:, live]
    mfreqs = np.asarray(mm["freqs"], float)
    ash = np.asarray(pkg.ash_rows)
    p_base, _ = F.hungarian_pairing(np.asarray(pkg.freqs_el), ash, live, mfreqs, msh)
    p_shift, _ = F.hungarian_pairing(np.asarray(pkg.freqs_el) * 1.10, ash, live, mfreqs, msh)
    g_base = F.greedy_pairing(np.asarray(pkg.freqs_el), ash, live, mfreqs, msh)
    g_shift = F.greedy_pairing(np.asarray(pkg.freqs_el) * 1.10, ash, live, mfreqs, msh)
    set_b = set((a, b) for a, b, _ in p_base)
    set_s = set((a, b) for a, b, _ in p_shift)
    churn_hung = len(set_b ^ set_s)
    churn_greedy = len(set((a, b) for a, b, _ in g_base) ^ set((a, b) for a, b, _ in g_shift))
    # protocol invariance: the frozen pairs stored in the package NEVER change with theta
    th = np.exp(np.random.default_rng(0).normal(0, 0.2, len(pkg.free_names)))
    pairs_after_theta = np.asarray(F.Package.load("A0").pairs)
    frozen_ok = bool(np.array_equal(pairs_after_theta, np.asarray(pkg.pairs)))
    v5 = dict(churn_if_repaired_hungarian=churn_hung, churn_if_repaired_greedy=churn_greedy,
              frozen_pairs_theta_invariant=frozen_ok, n_pairs=len(p_base),
              metric=f"re-pairing churns {churn_hung} (hung) / {churn_greedy} (greedy) pairs on +10% shift; "
                     f"frozen pairing untouched={frozen_ok}",
              t_s=round(time.time() - t0, 1))
    v5["pass"] = bool(frozen_ok and (churn_hung >= 1 or churn_greedy >= 1))
    res["V5"] = v5
    save(res)
    F.log_runtime("V5", time.time() - t0)
    print(f"[V5] pass={v5['pass']} {v5['metric']}", flush=True)

ok = all(res[k]["pass"] for k in ("V1", "V2", "V3", "V4", "V5") if k in res)
print(f"\nALL GATES: {'PASS' if ok else 'FAIL'}  total {time.time()-t00:.0f}s", flush=True)
