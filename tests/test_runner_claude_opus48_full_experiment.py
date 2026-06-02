#!/usr/bin/env python3
"""Checker for the Claude Opus 4.8 full sequential vibe/modal/flight runner.

Validates that NUTS/HMC inference artifacts exist and meet acceptance gates.
A pass here is NOT proof of physical correctness; see packet.md manual review.

This is a NEW (non-immutable) test. It does not touch the four immutable checker
files; it re-verifies their hashes as part of the gate.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "artifacts" / "reports" / "runner_claude_opus48_20260602"
FIG = OUT / "figures"

IMMUTABLE = [
    "harness/checkers/verify_artifacts.py",
    "harness/checkers/check_canary.py",
    "tests/test_posterior_recovery.py",
    "tests/test_mdof_transfer.py",
]

REQUIRED_FILES = [
    "results.json",
    "nuts_diagnostics.json",
    "posterior_samples.npz",
    "packet.md",
    "commands.md",
    "files_changed.md",
    "assumptions_ledger.md",
    "assumptions_ledger.json",
    "known_failures.md",
    "review_request.md",
    "manifest.json",
]

REQUIRED_FIGS = [
    "01_truth_vs_observed.png",
    "02_posterior_full_vs_peak.png",
    "03_input_spectra_95_99.png",
    "04_qoi_intervals.png",
    "05_build_effect_recovery.png",
    "06_feature_map.png",
]


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    h.update(path.read_bytes())
    return h.hexdigest()


def main() -> int:
    checks: dict = {"checks": [], "status": "pass"}

    def record(name: str, ok: bool, detail: str = "") -> None:
        checks["checks"].append({"name": name, "pass": bool(ok), "detail": detail})
        if not ok:
            checks["status"] = "fail"

    # 1. Immutable checker hashes unchanged.
    manifest = {}
    for line in (ROOT / "harness/checkers/manifest.sha256").read_text().splitlines():
        digest, rel = line.split()
        manifest[rel] = digest
    for rel in IMMUTABLE:
        actual = _sha256(ROOT / rel)
        record(f"immutable_unchanged:{rel}", actual == manifest.get(rel), actual)

    # 2. Required files + figures exist.
    for rel in REQUIRED_FILES:
        record(f"file_exists:{rel}", (OUT / rel).exists())
    for rel in REQUIRED_FIGS:
        p = FIG / rel
        record(f"figure_exists:{rel}", p.exists() and p.stat().st_size > 5000)

    # 3. NUTS diagnostics present and sane for both models.
    if (OUT / "nuts_diagnostics.json").exists():
        diag = json.loads((OUT / "nuts_diagnostics.json").read_text())
        for label in ("full", "peak"):
            d = diag.get(label, {})
            record(f"{label}:is_nuts", "NUTS" in str(d.get("sampler", "")), str(d.get("sampler")))
            for field in ("divergences_total", "final_step_size", "max_observed_tree_depth",
                          "min_n_eff", "max_r_hat"):
                record(f"{label}:has_{field}", field in d)
            record(f"{label}:rhat_ok", d.get("max_r_hat", 9) < 1.05, str(d.get("max_r_hat")))
            record(f"{label}:ess_ok", d.get("min_n_eff", 0) > 200, str(d.get("min_n_eff")))
            record(f"{label}:divergence_fraction_ok",
                   d.get("divergence_fraction", 1) < 0.02, str(d.get("divergence_fraction")))

    # 4. Results contract present.
    if (OUT / "results.json").exists():
        r = json.loads((OUT / "results.json").read_text())
        for key in ("posterior_full", "posterior_peak", "qoi_full", "qoi_peak",
                    "qoi_interval_width_ratio_peak_over_full",
                    "fixed_flight_to_flight_qoi_log_sigma"):
            record(f"results_has:{key}", key in r)
        # Full likelihood should recover dome/tray fn within its own 95% interval.
        pf = r.get("posterior_full", {})
        for p in ("dome_hz", "tray_hz"):
            v = pf.get(p, {})
            ok = v and v["q025"] <= v["truth"] <= v["q975"]
            record(f"full_recovers_{p}", bool(ok),
                   f"truth={v.get('truth')} ci=[{v.get('q025')},{v.get('q975')}]")
        # Peak structural QOI interval should be wider than full (lossy likelihood).
        wr = r.get("qoi_interval_width_ratio_peak_over_full", {})
        record("peak_qoi_wider_than_full",
               wr.get("tray_structural_95_peak_over_full", 0) > 1.0,
               str(wr.get("tray_structural_95_peak_over_full")))

    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "checks.json").write_text(json.dumps(checks, indent=2))
    n_fail = sum(1 for c in checks["checks"] if not c["pass"])
    print(json.dumps({"status": checks["status"], "n_checks": len(checks["checks"]),
                      "n_fail": n_fail}, indent=2))
    return 0 if checks["status"] == "pass" else 2


if __name__ == "__main__":
    raise SystemExit(main())
