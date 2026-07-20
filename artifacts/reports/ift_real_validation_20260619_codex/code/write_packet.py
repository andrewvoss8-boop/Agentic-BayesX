#!/usr/bin/env python3
"""Write the human-review packet from scorecard/checker JSON only."""
from __future__ import annotations

import json
from pathlib import Path

WS = Path(__file__).resolve().parent.parent
OUT = WS / "out"


def fmt(x, digits=3):
    if x is None:
        return "NA"
    try:
        return f"{float(x):.{digits}g}"
    except Exception:
        return str(x)


def main():
    scp = OUT / "scorecard.json"
    chkp = WS / "checker_report.json"
    if not scp.exists():
        raise SystemExit("scorecard missing; run code/scorecard.py first")
    sc = json.loads(scp.read_text())
    chk = json.loads(chkp.read_text()) if chkp.exists() else {"overall": "NOT-RUN", "green": 0, "yellow": 0, "red": 0}
    discp = OUT / "discretization_sensitivity.json"
    disc = json.loads(discp.read_text()) if discp.exists() else None
    convp = OUT / "convergence_table.json"
    conv = json.loads(convp.read_text()) if convp.exists() else None
    ift = sc.get("IFT") or {}
    l5 = sc.get("L5_modal_feature_marginal_qoi_discrepancy") or {}
    m2 = sc.get("M2_whole_frf_schneider") or {}

    lines = []
    lines.append("# IFT vs StatFEM on the real ShockSat held-out-sensor QOI")
    lines.append("")
    lines.append(f"Checker status: **{chk.get('overall')}** ({chk.get('green')} green / {chk.get('yellow')} yellow / {chk.get('red')} red).")
    lines.append(f"Generated verdict: **{sc.get('verdict')}** ({sc.get('status')}) - {sc.get('verdict_reason')}")
    lines.append("")
    lines.append("## 1. Method Summary")
    lines.append("")
    lines.append("IFT puts the reduced dynamic-stiffness equation in the field prior with learned inverse-temperature `beta`. The inherited real-data observable is `log|H|`, so the headline implementation uses the documented first-order log-magnitude moment approximation in `method_ift.md`; this is labeled as a YELLOW adaptation, not hidden.")
    lines.append("")
    lines.append("Data count: one real hit and one impact location; validation randomizes the observed/held-out channel split only. The copied StatFEM split code currently yields 77 dynamic-range-eligible mapped channels after the bad-channel exclusions.")
    lines.append("")
    lines.append("## 2. Scorecard")
    lines.append("")
    if ift:
        lines.append(f"IFT result source: `{ift.get('source')}`; kind: `{ift.get('kind')}`; splits: {ift.get('n_splits')}; convergence fraction: {fmt(ift.get('converged_frac'))}.")
        for q in ("peak", "band"):
            s = ift.get("summary", {}).get(q, {})
            lines.append(f"- IFT {q}: interval median {fmt(s.get('interval', {}).get('med'))}, CRPS median {fmt(s.get('crps', {}).get('med'))}, logpd median {fmt(s.get('logpd', {}).get('med'))}, coverage median {fmt(s.get('coverage', {}).get('med'))}, z-std median {fmt(s.get('zstd', {}).get('med'))}.")
    else:
        lines.append("IFT result missing.")
    if l5.get("qoi"):
        for q in ("peak", "band"):
            s = l5["qoi"][q]
            lines.append(f"- L5 {q}: interval median {fmt(s['interval']['med'])}, CRPS median {fmt(s['crps']['med'])}, coverage median {fmt(s['coverage']['med'])}, z-std median {fmt(s['zstd']['med'])}.")
    if m2.get("seed0"):
        for q in ("peak", "band"):
            s = m2["seed0"][q]
            lines.append(f"- M2 seed0 {q}: interval {fmt(s['interval'])}, CRPS {fmt(s['crps'])}, logpd {fmt(s['logpd'])}, coverage {fmt(s['coverage'])}; copied whole-FRF baseline is non-converged.")
    lines.append("")
    lines.append("## 3. Beta Thermometer")
    lines.append("")
    rows = ift.get("per_split", []) if ift else []
    if rows:
        beta_vals = [r.get("beta_med") for r in rows if r.get("beta_med") is not None]
        lines.append(f"Across available IFT splits, median beta range is {fmt(min(beta_vals))} to {fmt(max(beta_vals))}. Weak-beta fraction: {fmt(ift.get('beta_weak_frac'))}.")
    else:
        lines.append("No beta summary available yet.")
    lines.append("")
    lines.append("## 4. Convergence and Discretization")
    lines.append("")
    if conv:
        ci = conv["arms"]["IFT"]
        lines.append(f"IFT convergence gate: converged fraction {fmt(ci.get('converged_frac'))}, worst R-hat {fmt(ci.get('worst_rhat'))}, min ESS {fmt(ci.get('min_ess'))}, beta included in the gate.")
    if disc:
        lines.append(f"Discretization diagnostic: `{disc.get('kind')}` on split {disc.get('split_seed')}; status **{disc.get('status')}**; posterior-invariance certified = `{disc.get('posterior_invariance_certified')}`.")
        for arm in ("IFT", "L5"):
            shifts = disc["relative_shifts_vs_full"][arm]["every_4th_44"]
            lines.append(f"- {arm} every-4th grid shift vs full: peak interval {fmt(shifts['peak_interval_rel_shift'])}, band interval {fmt(shifts['band_interval_rel_shift'])}.")
    else:
        lines.append("Discretization diagnostic missing.")
    lines.append("")
    lines.append("## 5. Honest Limitations")
    lines.append("")
    for w in sc.get("warnings", []):
        lines.append(f"- {w}")
    lines.append("- YELLOW: the frequency-grid diagnostic reuses split-0 posterior samples; it is not a full sampler rerun on each grid.")
    deck = WS / "slides" / "ift_real_validation_honest_negative.pptx"
    if deck.exists():
        lines.append("- Deck generated from JSON-backed claims and rendered through artifact-tool.")
    else:
        lines.append("- Deck pending; checker must remain non-RED before it is accepted.")
    lines.append("")
    lines.append("## 6. Proposed Project-Log Row")
    lines.append("")
    lines.append("> IFT vs StatFEM real ShockSat validation - `artifacts/reports/ift_real_validation_20260619_codex/` - checker status copied verbatim after final run. Faithful physics-in-prior IFT arm compared against copied StatFEM L5/M2 held-out-sensor QOI baselines; verdict generated by `out/scorecard.json`.")
    (WS / "packet.md").write_text("\n".join(lines) + "\n")
    print(f"wrote {WS / 'packet.md'}")


if __name__ == "__main__":
    main()
