#!/usr/bin/env python3
"""Write manifest.json: every artifact in the workspace with size + sha256."""
import hashlib
import json
import os

WS = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SKIP_DIRS = {"logs"}
items = []
for root, dirs, files in os.walk(WS):
    dirs[:] = [x for x in dirs if x not in SKIP_DIRS]
    for f in sorted(files):
        if f == "manifest.json" or f.endswith(".pyc"):
            continue
        p = os.path.join(root, f)
        rel = os.path.relpath(p, WS)
        h = hashlib.sha256(open(p, "rb").read()).hexdigest()[:16]
        items.append(dict(path=rel, bytes=os.path.getsize(p), sha256_16=h))
manifest = dict(
    workspace="artifacts/reports/mpl_stand_fem_rebuild_20260611",
    runner="FABLE", date="2026-06-11",
    task="MPL stand parametric FEM rebuild (coarse prior model; no sampler)",
    inputs=dict(
        deck="MPL test stand/FEM/Test Stand FEA.dat",
        photos="MPL test stand/FEM/test stand photos jun 11 26/IMG_9842-9846",
        human_confirmations="clamp 415.3 g; shield vertical perpendicular to "
                            "thrust; shield t=1.7 mm; runner=FABLE override"),
    n_artifacts=len(items), artifacts=items)
with open(os.path.join(WS, "manifest.json"), "w") as fh:
    json.dump(manifest, fh, indent=1)
print("manifest:", len(items), "artifacts")
