#!/usr/bin/env python3
"""MDOF reduced transfer-function sanity checks."""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np

from src.mdof.reduced_transfer import chain_system, frf_drivepoint, reduced_drivepoint_frf


def main() -> int:
    freqs = np.linspace(5.0, 220.0, 200)
    sys = chain_system(n=7, m0=1.2, k0=7.5e5, zeta=0.01)

    h_full = frf_drivepoint(sys.m, sys.c, sys.k, freqs, dof=0)
    h_red = reduced_drivepoint_frf(sys, freqs, dof=0, n_modes=4)

    rel = np.linalg.norm(h_full - h_red) / np.linalg.norm(h_full)
    report = {
        "relative_l2_error": float(rel),
        "pass": bool(rel < 0.45),
    }

    root = Path(__file__).resolve().parents[1]
    out = root / "artifacts" / "tests" / "mdof_transfer_report.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, indent=2))
    print(json.dumps(report, indent=2))
    return 0 if report["pass"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
