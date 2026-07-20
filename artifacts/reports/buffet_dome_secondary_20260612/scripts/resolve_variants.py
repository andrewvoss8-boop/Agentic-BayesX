#!/usr/bin/env python3
"""Overnight structural-variant re-solves (Sensitivity gate: vary what changes
the decision, not what is easy). Each variant: rebuild -> marching eigensolve
-> full QOI sweep. BC-A only (the BC bracket itself is already a reported
uncertainty axis from the nominal pair). Resumable: finished variants skipped.

Variants (vs nominal):
  kmlo  k_mount=1e6  (COPV mounts soft decade)   — COPV QOI driver
  kmhi  k_mount=1e8  (COPV mounts stiff decade)
  kjlo  k_joint=1e6  (tray strut joints soft)    — tray/strut QOI driver
  tdlo  t_dome=0.003 (thin dome: -40% gauge)     — host-model-form lever
  meshf Nth=300,Nz=20,Nu=30 (refined mesh)       — Discretization gate check

Run detached: nohup python3 scripts/resolve_variants.py > logs/variants.log 2>&1 &
"""
import json
import os
import subprocess
import sys
import time
from pathlib import Path

WS = Path(__file__).resolve().parent.parent
PY = sys.executable

VARIANTS = {
    "kmlo": {"k_mount": 1e6},
    "kmhi": {"k_mount": 1e8},
    "kjlo": {"k_joint": 1e6},
    "tdlo": {"t_dome": 0.003},
    "krlo": {"k_mount_rot": 1e3},   # D14 finding: COPV rotational-mount driver
    "krhi": {"k_mount_rot": 1e5},
    "meshf": {"Nth": 300, "Nz": 20, "Nu": 30},
}

for tag, ov in VARIANTS.items():
    t0 = time.time()
    qoi_done = WS / "out" / f"qoi_bcA_{tag}_summary.json"
    if qoi_done.exists():
        print(f"[{tag}] already complete, skip", flush=True)
        continue
    env = dict(os.environ, BUFFET_TAG=tag, BUFFET_PAR_OVERRIDES=json.dumps(ov),
               OMP_NUM_THREADS="1", VECLIB_MAXIMUM_THREADS="1")
    model = WS / "out" / f"model_bcA_{tag}.npz"
    if not model.exists():
        print(f"[{tag}] build...", flush=True)
        subprocess.run([PY, "scripts/build_model.py"], cwd=WS, env=env, check=True)
    meta_done = WS / "out" / f"modes_bcA_{tag}_meta.json"
    if not meta_done.exists():
        print(f"[{tag}] solve modes...", flush=True)
        subprocess.run([PY, "scripts/solve_modes.py", f"bcA_{tag}"], cwd=WS,
                       env=env, check=True)
    print(f"[{tag}] qoi sweep...", flush=True)
    subprocess.run([PY, "scripts/forcing_qoi.py", f"bcA_{tag}"], cwd=WS,
                   env=env, check=True)
    print(f"[{tag}] done in {time.time()-t0:.0f}s", flush=True)

print("all variants complete", flush=True)
