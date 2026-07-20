#!/usr/bin/env python3
"""Resumable driver for the remaining subset cells (run sequentially to avoid the memory contention that killed
the parallel detached jobs). Each cell is cached + skipped if present, so a killed/relaunched run never restarts
finished work. Order: finish IFT-TMCMC subset, then the M2 divergence contrast."""
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import ift_tmcmc
import run_sweep

t0 = time.time()
for s in (2, 3, 4):
    print(f"[resume {time.strftime('%H:%M')}] IFT-TMCMC seed {s} ...", flush=True)
    ift_tmcmc.run_split_tmcmc(seed=s, n=1500, n_runs=4)
for s in (0, 1, 2):
    print(f"[resume {time.strftime('%H:%M')}] M2 seed {s} ...", flush=True)
    run_sweep.m2_split(s, 800, 800, 4, 250, False)
print(f"RESUME DONE in {time.time()-t0:.0f}s", flush=True)
