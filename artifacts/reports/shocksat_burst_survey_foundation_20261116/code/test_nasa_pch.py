#!/usr/bin/env python3
"""Known-answer test for nasa_pch.py on a synthetic punch file. Writes qa/nasa_pch_unit.json."""
import json, os, sys, tempfile
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import nasa_pch  # noqa: E402
rng = np.random.default_rng(3)
f = np.arange(10.0, 400.0001, 0.125)
pts = [11101, 11110, 1101]
M = [10 ** rng.uniform(-3, 2, (len(f), 3)) for _ in pts]
P = [rng.uniform(-180, 180, (len(f), 3)) for _ in pts]
p = os.path.join(tempfile.mkdtemp(), "s.pch")
nasa_pch.write_synthetic(p, pts, f, M, P)
r = nasa_pch.parse(p)
ok = {"points": sorted(r) == sorted(pts), "n_freq": all(len(r[q][0]) == len(f) == 3121 for q in pts),
      "mag_rel_err_lt_1e-6": all(np.max(np.abs(r[q][1] / M[i] - 1)) < 1e-6 for i, q in enumerate(pts)),
      "phase_err_lt_1e-4": all(np.max(np.abs(r[q][2] - P[i])) < 1e-4 for i, q in enumerate(pts))}
json.dump({"checks": ok, "all_pass": all(ok.values()), "note": "synthetic layout inferred from the June parser; real files not yet in hand"},
          open(os.path.join(HERE, "..", "qa", "nasa_pch_unit.json"), "w"), indent=1)
print(ok); sys.exit(0 if all(ok.values()) else 1)
