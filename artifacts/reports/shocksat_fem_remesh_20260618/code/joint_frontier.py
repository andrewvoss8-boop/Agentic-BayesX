#!/usr/bin/env python3
"""Card D — JOINT-update frontier (answers Andrew: don't hold the other params fixed).

The group campaign + local-interface sweep are 1-D slices (vary one param, freeze
the rest at nominal). This scans the FULL 9-parameter space in the fast 74x74
reduced model (eigh ~24 ms) to find whether a JOINT update has a point that
improves the hard-region SHAPE without a frequency penalty -- a 'both-improve'
point a one-at-a-time sweep structurally cannot find.

Re-pairing-robust metric: TRACK each nominal FEM mode to its shape-continuation
in each sampled model, so every test mode keeps the SAME PHYSICAL partner (no
greedy re-pairing churn). Report Pareto frontier (mean|df%| vs hard-region MAC)
and any point with mean|df%| <= nominal AND hard MAC > nominal AND global MAC >= nominal.
"""
import json, os, time
import numpy as np

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(HERE)
t0 = time.time()
rb = np.load("data/reduced_blocks.npz", allow_pickle=True)
A_fix, A = rb["A_fix"], rb["A"]; obs_V = rb["obs_V"]            # (228,74)
GN = [str(g) for g in rb["gnames"]]
mm = np.load("measured_modes.npz", allow_pickle=True)
nodes, f_meas, mshapes, mmask = mm["nodes"], mm["freqs"], mm["shapes"], mm["measured"]
live = mmask.reshape(-1)
phi_tst = mshapes.reshape(33, -1)                               # (33,228)
rd = json.load(open("out/region_diagnosis.json"))
hard_idx = sorted({i for reg in rd["regions"].values() for i in reg})
hard_live = np.array([j*3+ax for j in hard_idx for ax in range(3) if mmask[j, ax]])

def modes(theta):
    K = A_fix + np.einsum("g,gij->ij", theta, A)
    lam, Q = np.linalg.eigh(K)
    f = np.sqrt(np.clip(lam, 0, None))/(2*np.pi)
    S = obs_V @ Q                                              # (228,74) shapes at accel nodes
    return f, S

def macvec(av, bv):
    na = (av*av).sum(0); nb = (bv*bv).sum(0)
    return (av*bv).sum(0)**2/(na*nb + 1e-30)

# nominal reference
f0, S0 = modes(np.ones(9))
el = np.arange(74)                       # use all; pair test->nominal FEM (greedy, live DOFs)
def pair_test(S):
    P = []
    for t in range(33):
        b = phi_tst[t]
        sc = [macvec(S[live, j], b[live]) for j in range(74)]
        P.append(int(np.argmax(sc)))
    return P
pair0 = pair_test(S0)
calib = [t for t in range(33) if macvec(S0[live, pair0[t]], phi_tst[t][live]) > 0.5]

def metrics(f, S):
    # track each nominal FEM mode -> continuation in S (max MAC over full 228 DOFs)
    track = np.array([int(np.argmax(macvec(S0[:, j][:, None], S))) for j in range(74)])
    dfp, gmac, hmac = [], [], []
    for t in calib:
        j0 = pair0[t]; k = track[j0]
        dfp.append(abs(f[k]/f_meas[t]-1)*100)
        gmac.append(macvec(S[live, k], phi_tst[t][live]))
        if hard_live.size >= 2:
            hmac.append(macvec(S[hard_live, k], phi_tst[t][hard_live]))
    return float(np.mean(dfp)), float(np.mean(gmac)), float(np.mean(hmac)) if hmac else np.nan

m0 = metrics(f0, S0)
print(f"NOMINAL: mean|df%| {m0[0]:.3f}  global MAC {m0[1]:.3f}  hard-region MAC {m0[2]:.3f}  "
      f"(over {len(calib)} calib modes)")

# Latin-hypercube-ish scan of theta in [0.6,1.4]^9
rng = np.random.default_rng(0)
N = 6000
TH = 0.6 + 0.8*rng.random((N, 9))
rec = np.zeros((N, 3))
for i in range(N):
    f, S = modes(TH[i]); rec[i] = metrics(f, S)
dfp, gmac, hmac = rec[:, 0], rec[:, 1], rec[:, 2]

# both-improve: freq not worse AND hard MAC better AND global not worse
both = (dfp <= m0[0]) & (hmac > m0[2] + 0.005) & (gmac >= m0[1] - 0.003)
# Pareto front (minimize df, maximize hmac)
order = np.argsort(dfp)
pareto = []
best_h = -1
for i in order:
    if hmac[i] > best_h:
        best_h = hmac[i]; pareto.append(int(i))

out = dict(note="joint 9-parameter frontier, tracked (re-pairing-robust) metric, reduced model",
    n_samples=N, n_calib_modes=len(calib), groups=GN,
    nominal=dict(mean_abs_df_pct=m0[0], global_mac=m0[1], hard_region_mac=m0[2]),
    n_both_improve=int(both.sum()),
    best_both_improve=None, runtime_s=round(time.time()-t0, 1))
if both.sum():
    # among both-improve, the one with max hard MAC
    cand = np.where(both)[0]; bi = cand[np.argmax(hmac[cand])]
    out["best_both_improve"] = dict(
        theta={GN[g]: round(float(TH[bi, g]), 3) for g in range(9)},
        mean_abs_df_pct=round(float(dfp[bi]), 3), global_mac=round(float(gmac[bi]), 3),
        hard_region_mac=round(float(hmac[bi]), 3),
        d_df_pct=round(float(dfp[bi]-m0[0]), 3), d_global_mac=round(float(gmac[bi]-m0[1]), 3),
        d_hard_mac=round(float(hmac[bi]-m0[2]), 3))
out["pareto_front"] = [dict(mean_abs_df_pct=round(float(dfp[i]), 3),
                            hard_region_mac=round(float(hmac[i]), 3),
                            global_mac=round(float(gmac[i]), 3)) for i in pareto]
json.dump(out, open("out/joint_frontier.json", "w"), indent=1)

print(f"\nJOINT scan ({N} samples, {len(calib)} calib modes, tracked pairing):")
print(f"  points improving hard-region SHAPE without a frequency penalty (and global not worse): "
      f"{int(both.sum())} of {N}")
if out["best_both_improve"]:
    b = out["best_both_improve"]
    print(f"  BEST both-improve: hard MAC {m0[2]:.3f}->{b['hard_region_mac']:.3f} ({b['d_hard_mac']:+.3f}), "
          f"|df%| {m0[0]:.3f}->{b['mean_abs_df_pct']:.3f} ({b['d_df_pct']:+.3f}), "
          f"global MAC {m0[1]:.3f}->{b['global_mac']:.3f} ({b['d_global_mac']:+.3f})")
    print(f"  theta: {b['theta']}")
else:
    print("  NONE -> the shape-vs-frequency tradeoff holds even in the full joint space.")
print("-> out/joint_frontier.json")
