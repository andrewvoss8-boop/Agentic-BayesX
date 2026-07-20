#!/usr/bin/env python3
"""Build + cache the per-reference multi-hit ensemble FRFs once, on the SAME mapped channel set as the forward.

Common analysis resolution N=65536 (df 3.81 Hz): fits 4 hits each for +Z/+Y/900z and resolves the modes (≥10 Hz
spacing) — chosen over the +X-matched N=200000 because that window excludes the clean modal +Y (late impacts) and
leaves only 1-2 hits for the impact refs. Trade-off (documented): coarser df and more exponential-window damping
ζ_w (≈1.8% at 100 Hz vs 0.6% at N=200000), but CONSISTENT across references and across the BEFORE/AFTER comparison,
and includes every reference. Also keeps the N=200000 matched +X/+Z caches for the apples-to-apples cross-check.

Saves data/multiref/<key>_N65536.npz (and _N200000 where it fits). Resumable: skips a cache that already exists.
"""
from __future__ import annotations
import sys, json, time
from pathlib import Path
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import realfrf as rf
import multiref_frf as mrf

WS = Path(__file__).resolve().parent.parent
MULTIREF = WS / "data" / "multiref"; MULTIREF.mkdir(parents=True, exist_ok=True)


def main(force=False):
    t0 = time.time()
    R = rf.load_reduced()
    meas = rf.reprocess_measured(list(range(1, rf.N_ACCEL_RECORDERS + 1)))
    ch = rf.build_channels(R, meas["daq"])
    daqs = list(ch.daq)
    summary = {}
    for key in mrf.REFS:
        for N in (65536, 200000):
            outp = MULTIREF / f"{key}_N{N}.npz"
            if outp.exists() and not force:
                z = np.load(outp, allow_pickle=True)
                summary.setdefault(key, {})[f"N{N}"] = {"n_hits_used": int(z["n_hits_used"]), "cached": True}
                continue
            b = mrf.build_reference(key, daqs=daqs, N=N)
            if b is None or b.get("n_hits_used", 0) == 0:
                summary.setdefault(key, {})[f"N{N}"] = {"n_hits_used": 0}
                continue
            mrf.save_cache(b, outp)
            summary.setdefault(key, {})[f"N{N}"] = {"n_hits_used": b["n_hits_used"],
                                                    "df_hz": round(b["df_hz"], 3),
                                                    "coh_at_res_p90": None}
            print(f"cached {key} N{N}: {b['n_hits_used']} hits, df {b['df_hz']:.2f} Hz -> {outp.name}")
    (WS / "out" / "multiref_cache_summary.json").write_text(json.dumps(summary, indent=2))
    print(f"\ncache summary: {json.dumps(summary)}")
    print(f"runtime {time.time()-t0:.0f}s")


if __name__ == "__main__":
    main(force="--force" in sys.argv)
