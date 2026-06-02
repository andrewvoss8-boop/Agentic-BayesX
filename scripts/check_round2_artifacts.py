#!/usr/bin/env python3
"""Runner-local (NON-immutable) acceptance checker for the round-2 deliverables.
Artifact-backed: verifies required files, GIF frame count, diagnostic gate fields,
internal consistency (nuts_active only if converged), and the PSD-band/resolution
records. Writes checks.json. Does NOT modify any immutable checker file."""
from __future__ import annotations
import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "artifacts/reports/runner_claude_opus48_round2_20260602"
FIG = OUT / "figures"
checks = []


def add(name, ok, detail=""):
    checks.append({"check": name, "pass": bool(ok), "detail": str(detail)})


def exists(rel, minbytes=200):
    p = OUT / rel
    ok = p.exists() and p.stat().st_size >= minbytes
    add(f"exists:{rel}", ok, f"{p.stat().st_size if p.exists() else 0} bytes")
    return ok


def main():
    # required contract files
    for f in ["priority_deliverables.md", "runtime.json", "nuts_diagnostics.json",
              "nuts_diagnostics.md", "assumptions_ledger.md", "quantity_contracts_round2.md",
              "resolution_analysis.md", "resolution_metrics.json", "commands.md",
              "files_changed.md", "known_failures.md", "review_request.md", "manifest.json",
              "packet.md", "interface_psd_bands.json"]:
        exists(f)

    # figures
    for f in ["figures/interface_response_psd_vs_spec.gif", "figures/flight_forcing_overlay.png",
              "figures/flight_qoi_vs_vibe_reference.png", "figures/resolution_sensitivity.png",
              "figures/posterior_recovery.png", "figures/sequential_assimilation_qoi.png"]:
        exists(f, minbytes=1000)

    # GIF frames count == 11
    frames = sorted((FIG / "gif_frames").glob("frame_flight_*.png"))
    add("gif_frames==11", len(frames) == 11, f"{len(frames)} frames")

    # interface psd bands has 11 records w/ required keys
    try:
        bands = json.loads((OUT / "interface_psd_bands.json").read_text())
        ok = len(bands) == 11 and all({"flight_id", "peak_mean_psd_g2_per_hz",
                                       "frac_freqs_99hi_exceeds_spec"} <= set(b) for b in bands)
        add("interface_psd_bands:11_records_keys", ok, f"{len(bands)} records")
    except Exception as e:
        add("interface_psd_bands:11_records_keys", False, repr(e))

    # diagnostics gate fields + consistency
    try:
        diag = json.loads((OUT / "nuts_diagnostics.json").read_text())
        req = {"sampler", "n_chains", "divergences", "divergence_fraction",
               "worst_rank_split_rhat", "min_ess_bulk", "min_ess_tail",
               "gate_rhat_pass", "gate_ess_pass", "gate_divergence_pass", "converged",
               "nuts_active", "per_variable", "raw_latents_included"}
        add("diagnostics:required_fields", req <= set(diag), f"missing={req-set(diag)}")
        add("diagnostics:n_chains>=4", diag["n_chains"] >= 4, diag["n_chains"])
        add("diagnostics:raw_latents_included", diag.get("raw_latents_included") is True)
        add("diagnostics:not_smoke", diag.get("smoke_mode") is False, f"smoke={diag.get('smoke_mode')}")
        # consistency: nuts_active <=> converged
        add("consistency:nuts_active==converged",
            diag["nuts_active"] == diag["converged"],
            f"nuts_active={diag['nuts_active']} converged={diag['converged']}")
        # gate thresholds honored if converged claimed
        if diag["converged"]:
            add("gate:rhat<1.01", diag["worst_rank_split_rhat"]["value"] < 1.01,
                diag["worst_rank_split_rhat"])
            add("gate:ess_bulk>=400", diag["min_ess_bulk"]["value"] >= 400, diag["min_ess_bulk"])
            add("gate:ess_tail>=400", diag["min_ess_tail"]["value"] >= 400, diag["min_ess_tail"])
            add("gate:div_frac<0.02", diag["divergence_fraction"] < 0.02, diag["divergence_fraction"])
        else:
            add("gate:honest_not_converged_reported", True,
                "converged=False reported; no clean 'NUTS active' claim")
        # all monitored latents have rhat/ess entries
        n_latents = diag.get("n_monitored_scalar_quantities", 0)
        add("diagnostics:>=29_monitored_quantities", n_latents >= 29, n_latents)
    except Exception as e:
        add("diagnostics:parse", False, repr(e))

    # resolution metrics has reference comparison + clip metric
    try:
        res = json.loads((OUT / "resolution_metrics.json").read_text())
        req = {"interface_3grms_refined_err_vs_ref", "peak62_coarse_clip_frac",
               "reference_points", "grid_refined_points"}
        add("resolution:reference_and_clip_fields", req <= set(res), f"missing={req-set(res)}")
    except Exception as e:
        add("resolution:parse", False, repr(e))

    # runtime.json fields
    try:
        rt = json.loads((OUT / "runtime.json").read_text())
        ok = {"active_runtime_s", "elapsed_wallclock_s"} <= set(rt) and rt["active_runtime_s"] <= rt["elapsed_wallclock_s"]
        add("runtime:fields_and_active<=elapsed", ok, rt)
    except Exception as e:
        add("runtime:parse", False, repr(e))

    # immutable checkers untouched
    try:
        r = subprocess.run(["shasum", "-a", "256", "-c", "harness/checkers/manifest.sha256"],
                           cwd=ROOT, capture_output=True, text=True)
        add("immutable_checkers:unchanged", r.returncode == 0 and "FAILED" not in r.stdout, r.stdout.strip()[-200:])
    except Exception as e:
        add("immutable_checkers:unchanged", False, repr(e))

    n_pass = sum(c["pass"] for c in checks)
    result = {"n_checks": len(checks), "n_pass": n_pass, "n_fail": len(checks) - n_pass,
              "all_pass": n_pass == len(checks), "checks": checks}
    (OUT / "checks.json").write_text(json.dumps(result, indent=2))
    print(f"checks: {n_pass}/{len(checks)} pass; all_pass={result['all_pass']}")
    for c in checks:
        if not c["pass"]:
            print("  FAIL:", c["check"], "-", c["detail"])
    return 0 if result["all_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
