#!/usr/bin/env python3
"""
Shared-solver / faked-independence detector for the multi-agent FEM cross-build.

WHAT IT IS (plain English)
--------------------------
The Phase-1 exercise asked three agents to each build the SAME structure in
several different solvers ("engines"), independently. The whole point of running
many engines is that they are INDEPENDENT: if two "different" engines secretly
call the SAME piece of solver code, their agreement is meaningless (it is one
program reporting twice, not two confirmations).

A human-invisible but machine-obvious tell-tale of this kind of fake is that two
supposedly-independent engines return eigenfrequencies that match to far more
significant digits than two genuinely-different numerical methods ever would.
Real cross-software agreement is ~0.1-3% (different meshes, element theories,
eigensolvers). A SHARED solver agrees to ~1e-4 Hz or better (bit-for-bit-ish).

This script scans every results.json in runs/fem_phase1/, and for each AGENT
compares its engines pairwise. Any within-agent pair whose lowest modes match
to within a tiny absolute tolerance is FLAGGED as a suspected shared solver.

This is a NECESSARY, not sufficient, integrity check: it catches the specific
"relabel one solver as two" fake that occurred (codex JAX vs TensorMesh). It does
NOT prove independence by itself (see README limitations). It is advisory.

USAGE
-----
    python3 detect_shared_solver.py [runs/fem_phase1]
Exit code 1 if any pair is flagged, else 0.
"""
import json
import sys
from itertools import combinations
from pathlib import Path

# A genuinely-independent engine pair should differ by MORE than this on mode 1.
# Different mesh/element/eigensolver realistically differ by >> 1e-2 Hz. We flag
# anything closer than ABS_TOL_HZ (a near-bit-identical match = same solver).
ABS_TOL_HZ = 1.0e-2          # absolute Hz tolerance on the lowest mode
REL_TOL = 1.0e-4             # OR relative match across the whole spectrum


def load_freqs(p: Path):
    """Return a sorted list of frequencies (Hz) from a results.json of either schema."""
    d = json.loads(p.read_text())
    freqs = []
    if "frequencies_hz" in d and isinstance(d["frequencies_hz"], list):
        freqs = [float(x) for x in d["frequencies_hz"]]
    else:
        # schemas that use a list of dicts under "frequencies" or "modes"
        for key in ("frequencies", "modes"):
            if isinstance(d.get(key), list):
                for f in d[key]:
                    if isinstance(f, dict) and f.get("frequency_hz") is not None:
                        freqs.append(float(f["frequency_hz"]))
                    elif isinstance(f, (int, float)):
                        freqs.append(float(f))
                if freqs:
                    break
    agent = d.get("agent") or p.parent.parent.name
    tool = d.get("tool") or p.parent.name
    status = d.get("status", "")
    return agent, tool, status, sorted(freqs)


def spectra_match(a, b):
    """True if two spectra are suspiciously identical (shared solver signature)."""
    if not a or not b:
        return False, None
    # Mode-1 absolute match
    d1 = abs(a[0] - b[0])
    if d1 <= ABS_TOL_HZ:
        return True, f"mode-1 differ by {d1:.2e} Hz (<= {ABS_TOL_HZ:g})"
    # Whole-spectrum relative match over the common length
    n = min(len(a), len(b))
    if n >= 3:
        rel = max(abs(a[i] - b[i]) / max(abs(a[i]), 1e-12) for i in range(n))
        if rel <= REL_TOL:
            return True, f"all {n} modes match to rel {rel:.2e} (<= {REL_TOL:g})"
    return False, None


def main():
    root = Path(sys.argv[1] if len(sys.argv) > 1 else "runs/fem_phase1")
    by_agent = {}
    for p in sorted(root.glob("*/*/results.json")):
        agent, tool, status, freqs = load_freqs(p)
        if freqs:
            by_agent.setdefault(agent, []).append((tool, status, freqs, p))

    flagged = []
    print(f"# Shared-solver detector — scanned {root}")
    print(f"# ABS_TOL_HZ={ABS_TOL_HZ:g}, REL_TOL={REL_TOL:g}\n")
    for agent, builds in sorted(by_agent.items()):
        print(f"AGENT: {agent}  ({len(builds)} engines with frequencies)")
        for tool, status, freqs, _ in builds:
            head = ", ".join(f"{x:.4f}" for x in freqs[:4])
            print(f"   - {tool:12s} [{status:14s}] modes: {head} ...")
        for (ta, sa, fa, pa), (tb, sb, fb, pb) in combinations(builds, 2):
            hit, why = spectra_match(fa, fb)
            if hit:
                flagged.append((agent, ta, tb, why))
                print(f"   !! FLAG  {ta} vs {tb}: {why}  -> SUSPECTED SHARED SOLVER")
        print()

    if flagged:
        print("RESULT: FAIL — suspected faked cross-engine independence:")
        for agent, ta, tb, why in flagged:
            print(f"  - {agent}: {ta} == {tb} ({why})")
        print("\nNOTE: a flag means the two engines are almost certainly the same")
        print("solver under two labels. Their agreement must NOT be counted as")
        print("independent cross-software verification. Investigate / require a")
        print("genuinely independent re-derivation.")
        return 1
    print("RESULT: PASS — no within-agent engine pair is suspiciously identical.")
    print("(Necessary check only; does NOT by itself prove independence.)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
