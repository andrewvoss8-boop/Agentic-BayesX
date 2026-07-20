#!/usr/bin/env python3
"""spot_freeze — G04 exact-basis spot checks on the freeze-set candidates (card §5/§9.4).
For each freeze-set candidate: a full own-space eigensolve at its multi-start theta_MAP, compare in-band
(<=1000 Hz) frequencies to the scored package's frequencies (<=0.3% = trusted). Own-space candidates are
exact by construction (basis IS the solve); projected split/scale candidates are the real test. Writes
out/spot_checks.json {"freeze_set":[{cid,max_freq_err_pct}], "pairing_frozen": True}. These solves also
count toward the loop's full-eigensolve total."""
import json, os, sys
import numpy as np

WS = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import wscore_wide as SW                      # noqa: E402
import loop_wide as L                         # noqa: E402


def freeze_cids():
    """A0_wide (baseline/B/C/F basis) + best agent-D + best random-R candidate."""
    recs = SW.existing("dev")
    cids = {"A0_wide"}
    for track in ("agent", "random"):
        best, bv = None, -9
        for line in open(os.path.join(WS, "out", "query_log.jsonl")):
            r = json.loads(line)
            if r.get("track") == track and (r.get("sub200_P1p") or -9) > bv:
                best, bv = r["cid"], r["sub200_P1p"]
        if best:
            cids.add(best)
    return sorted(cids)


def main():
    fs = []
    for cid in freeze_cids():
        rec = L.spot_check(cid)                # full solve at theta_MAP; writes spot_checks_raw.jsonl
        fs.append({"cid": cid, "max_freq_err_pct": rec["max_freq_err_pct"],
                   "median_freq_err_pct": rec["median_freq_err_pct"],
                   "n_modes_checked": rec["n_modes_checked"], "pass": rec["pass_0p3pct"]})
        print(cid, rec["max_freq_err_pct"], "%", flush=True)
    out = {"freeze_set": fs, "pairing_frozen": True,
           "note": "full own-space eigensolve at each candidate's multi-start theta_MAP vs its scored "
                   "package frequencies; own-space candidates exact by construction, projected split/scale "
                   "candidates are the real <=0.3% test (D22 rule)."}
    json.dump(out, open(os.path.join(WS, "out", "spot_checks.json"), "w"), indent=1)
    print("freeze-set spot checks:", [(f["cid"], f["max_freq_err_pct"]) for f in fs])


if __name__ == "__main__":
    main()
