#!/usr/bin/env python3
"""Known-answer test for adf_probe.py on a synthetic file with planted structure:
a 2560-byte preamble with ASCII metadata, then 12 records of 1024-byte header
(int32 signature [k, 76, 250, 1, 3] plus a channel name) and 4096 float32 samples.
Writes qa/adf_probe_unit.json; exit 1 on any failure."""
import json
import os
import struct
import sys
import tempfile

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import adf_probe  # noqa: E402


def main():
    rng = np.random.default_rng(1)
    pre = bytearray(2560)
    meta = b"ShkSat_78_Burst_5105_8109_9206_higher  OPoly v7.5.0  jwinkel  04-Mar-21"
    pre[100:100 + len(meta)] = meta
    recs = []
    for k in range(1, 13):
        h = bytearray(1024)
        h[0:20] = struct.pack("<5i", k, 76, 250, 1, 3)
        name = f"Channel {1100 + k}Z+ accel g".encode()
        h[40:40 + len(name)] = name
        x = (np.sin(2 * np.pi * 54.19 * np.arange(4096) / 1024.0) + 0.01 * rng.standard_normal(4096)).astype("<f4")
        recs.append(bytes(h) + x.tobytes())
    blob = bytes(pre) + b"".join(recs)
    p = os.path.join(tempfile.mkdtemp(), "synthetic.ati")
    open(p, "wb").write(blob)
    r = adf_probe.probe(p)
    rec_len = 1024 + 4096 * 4
    checks = {
        "size_reported": r["bytes"] == len(blob),
        "metadata_string_found_at_offset_100": any(s["offset"] == 100 and s["text"].startswith("ShkSat_78") for s in r["strings_first"]),
        "channel_names_found": sum("Channel 11" in s["text"] for s in r["strings_first"]) == 12,
        "all_12_signatures_found_at_record_starts": r["ash_style_signatures"] == [2560 + i * rec_len for i in range(12)],
        "record_period_is_top_distance": r["periodic_int32_distances"][0]["period_bytes"] == rec_len,
        "little_endian_floats_favoured": r["float32_plausible_fraction"]["little_endian_mean"] > r["float32_plausible_fraction"]["big_endian_mean"] + 0.2,
    }
    out = {"checks": checks, "all_pass": all(checks.values()), "top_periods": r["periodic_int32_distances"][:3]}
    json.dump(out, open(os.path.join(HERE, "..", "qa", "adf_probe_unit.json"), "w"), indent=1)
    print(json.dumps(out, indent=1))
    return 0 if out["all_pass"] else 1


if __name__ == "__main__":
    sys.exit(main())
