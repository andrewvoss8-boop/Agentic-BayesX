#!/usr/bin/env python3
"""dryrun_pipeline — smoke-test the downstream pipeline on a PROVISIONAL basis (slices 0+1, ~450 modes to
639 Hz) while the real k=560 solve runs. NOTHING here writes real artifacts: score log is redirected to
out/dryrun_score_log.jsonl, package saved as A0_dryrun, no theta_map_wide.json. Purpose: surface bugs in
wide_package/_train_warp/_grade_bands/theta_map/surrogate NOW. Deleted-safe (all dryrun files are
disposable and ignored by the checker)."""
import json, os, sys, time
import numpy as np

WS = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

t0 = time.time()
# ---- provisional merged basis from slices 0+1
sl = []
for si in (0, 1):
    z = np.load(os.path.join(WS, "out", "eig_slices", f"slice_{si:02d}.npz"))
    sl.append((np.asarray(z["lam"]), np.asarray(z["V"])))
lam = sl[0][0]; V = sl[0][1]
for lam_s, V_s in sl[1:]:
    keep = []
    for j, lv in enumerate(lam_s):
        if not np.any(np.abs(lam - lv) <= 1e-7 * max(abs(lv), 1.0) + 1e-3):
            keep.append(j)
    lam = np.concatenate([lam, lam_s[keep]]); V = np.hstack([V, V_s[:, keep]])
order = np.argsort(lam); lam, V = lam[order], V[:, order]
freqs = np.sqrt(np.clip(lam, 0, None)) / (2 * np.pi)
n_rbm = int((freqs < 10).sum())
print(f"provisional basis: {len(lam)} modes, top {freqs[-1]:.0f} Hz, n_rbm={n_rbm}", flush=True)

# save as if it were the real thing but under dryrun names
np.savez_compressed(os.path.join(WS, "out", "dryrun_eig.npz"), lam=lam, freqs=freqs, n_rbm=n_rbm)
np.save(os.path.join(WS, "out", "dryrun_V.npy"), V)

# ---- monkey-patch wide_package to read dryrun basis and write A0_dryrun
import wide_package as WP
_np_load = np.load
def load_patch(path, *a, **k):
    if path == os.path.join(WS, "out", "full_eig_theta1.npz"):
        return _np_load(os.path.join(WS, "out", "dryrun_eig.npz"), *a, **k)
    if path == os.path.join(WS, "out", "full_eig_V.npy"):
        return _np_load(os.path.join(WS, "out", "dryrun_V.npy"), *a, **k)
    return _np_load(path, *a, **k)
np.load = load_patch
if not os.path.exists(os.path.join(WP.PKGD, "A0_dryrun.npz")):
    WP.build("A0_dryrun")
np.load = _np_load
pkg = WP.load("A0_dryrun")
print(f"package ok: r={np.asarray(pkg.A).shape[1]}, pairs={len(np.asarray(pkg.pairs))}", flush=True)

# ---- theta_map (multi-start)
theta, nlp, ok = pkg.theta_map()
print("theta_MAP:", np.round(theta, 3).tolist(), "ok:", ok, flush=True)

# ---- scoring smoke test (redirect log)
import wscore_wide as SW
SW.SLOG = os.path.join(WS, "out", "dryrun_score_log.jsonl")
rec = SW.score_dev_wide("DRYRUN_A1", pkg, theta, note="dryrun; provisional basis to 639 Hz", log=True)
print("A1-dryrun bands:", json.dumps(rec["bands_agg"], indent=1), flush=True)

# ---- surrogate check machinery (arm B path) on the dryrun package
import arm_b_nuts as AB
sur = AB.Surrogate(pkg)
import wide_forward as WFW
caches = SW.load_caches()
fc = caches["m_xpos_990x"]["freqs"][caches["m_xpos_990x"]["band"]]
th = np.exp(np.random.default_rng(0).normal(0, 0.25, 9))
lamS, R = sur.modes_np(th)
exact = WFW.predict_logH(pkg, th, "m_xpos_990x", fc, windowed=True)
f2 = np.sqrt(np.clip(lamS, 1e-6, None)) / (2 * np.pi)
m_in = (f2 >= AB.F_SUPPORT[0]) & (f2 <= AB.F_SUPPORT[1])
zi = WFW.zeta_table(f2)
Us = np.asarray(pkg.sens_rows) @ R
Ud = (np.asarray(pkg.drives["m_xpos_990x"]) @ R) * m_in
res = Us * Ud[None, :]
import jax.numpy as jnp
surr = np.asarray(AB.jax_windowed_logH(jnp.asarray(res), jnp.asarray(np.where(m_in, f2, 1e6)),
                                       jnp.asarray(zi), jnp.asarray(np.round(fc * AB.NFRAME / AB.FS).astype(int))))
bm = fc < 200
d = np.abs(surr[:, bm] - exact[:, bm])
print(f"surrogate-vs-exact sub200 med dex: {np.median(d):.4f} (1-sigma prior draw)", flush=True)
print(f"DRYRUN COMPLETE in {time.time()-t0:.0f}s", flush=True)
