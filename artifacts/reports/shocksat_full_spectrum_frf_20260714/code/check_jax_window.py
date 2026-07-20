#!/usr/bin/env python3
"""check_jax_window — gate for arm B's JAX port of the exact window operator (decisions D5).
Compares arm_b_nuts.jax_windowed_logH against the REUSED wforward._windowed_H on synthetic residues
(dense-mode + light/heavy damping cases). Must agree to < 1e-9 dex. Writes out/armB_jax_check.json."""
import json, os, sys
import numpy as np

WS = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import wide_forward as WFW                    # noqa: E402  (brings wforward as WFW.WF)
import arm_b_nuts as AB                       # noqa: E402
import jax.numpy as jnp                       # noqa: E402

rng = np.random.default_rng(7)
n_s, n_m = 5, 40
fi = np.sort(rng.uniform(50, 1500, n_m))
zi = rng.uniform(0.002, 0.05, n_m)
res = rng.normal(0, 1, (n_s, n_m))
fc = np.arange(45.0, 1000.0, 2.0345052083333335)
kb = np.round(fc * AB.NFRAME / AB.FS).astype(int)

ref = np.log10(np.abs(WFW.WF._windowed_H(res, fi, zi, fc)) + 1e-300)     # physical units
jx = np.asarray(AB.jax_windowed_logH(jnp.asarray(res), jnp.asarray(fi), jnp.asarray(zi),
                                     jnp.asarray(kb))) + np.log10(AB.G_IN_S2)  # undo /G for comparison
err = float(np.max(np.abs(jx - ref)))
out = {"max_abs_err_dex": err, "pass": bool(err < 1e-9), "n_modes": n_m, "n_sens": n_s,
       "band": [float(fc[0]), float(fc[-1])], "note": "jax port vs reused wforward._windowed_H"}
json.dump(out, open(os.path.join(WS, "out", "armB_jax_check.json"), "w"), indent=1)
print(json.dumps(out))
assert out["pass"], "JAX window port mismatch"
