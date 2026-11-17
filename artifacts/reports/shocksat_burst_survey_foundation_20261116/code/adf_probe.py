#!/usr/bin/env python3
"""First-look structure probe for undocumented binary files (I-DEAS associated data
files: .ati time histories, .afu functions, .ash shapes).

It does not decode anything; it reports evidence a person needs to write a decoder:
 - file size and whether it is a whole number of 512-byte blocks;
 - printable ASCII strings (>= 6 characters) with byte offsets (channel names, units,
   dates, software names);
 - candidate record headers: int32 words repeated at a fixed byte period;
 - where the bytes look like float32 samples (finite, magnitudes between 1e-12 and 1e7),
   for little- and big-endian readings, in 64 KiB windows.
Known layout from this project's June work (shocksat_fem_modal_twin_20260609/scripts/
parse_ash.py): .ash records start with the int32 signature [index, n_channels, 250, 1, 3]
and use a 640-word preamble; the probe searches for the same signature.

Usage: adf_probe.py FILE [--json OUT]
"""
import argparse
import collections
import json
import os
import re
import sys

import numpy as np

WIN = 1 << 16


WORD = re.compile(rb"[A-Za-z]{4,}")
RARE = set(b'?{}[]|\\^`~!"#$%&\'()*;<=>@')


def strings(b, minlen=6, limit=200):
    """Printable runs that contain a run of at least 4 letters and at most 10 % rare
    punctuation. Chance printable runs inside float32 sample data are dominated by '?'
    and similar bytes (the exponent byte of values near 1 is 0x3F), so they are dropped."""
    out = []
    for m in re.finditer(rb"[\x20-\x7e]{%d,}" % minlen, b):
        g = m.group()
        if not WORD.search(g) or sum(c in RARE for c in g) > 0.1 * len(g):
            continue
        out.append({"offset": m.start(), "text": m.group().decode("ascii")[:120]})
        if len(out) >= limit:
            break
    return out


def float_windows(b, order):
    a = np.frombuffer(b[: len(b) // 4 * 4], dtype=order + "f4")
    res = []
    for k in range(0, len(a), WIN // 4):
        w = a[k:k + WIN // 4]
        with np.errstate(all="ignore"):
            ok = np.isfinite(w) & (np.abs(w) > 1e-12) & (np.abs(w) < 1e7)
        res.append(float(ok.mean()))
    return res


def signatures(b):
    i32 = np.frombuffer(b[: len(b) // 4 * 4], dtype="<i4")
    hits = []
    for k in np.where(i32[2:] == 250)[0] + 2:
        if k + 2 < len(i32) and i32[k + 1] == 1 and i32[k + 2] == 3 and 1 <= i32[k - 1] <= 4096 and i32[k - 2] >= 1:
            hits.append(int(k * 4 - 8))
    return hits


def periodic_words(b, max_words=2_000_000, top=8):
    """Most common byte distances between repeats of the same small positive int32
    value at 4-byte alignment; a fixed-size record layout shows up as one dominant
    distance."""
    i32 = np.frombuffer(b[: min(len(b), max_words * 4) // 4 * 4], dtype="<i4")
    small = np.where((i32 > 0) & (i32 < 100000))[0]
    pos = collections.defaultdict(list)
    for k in small[:400000]:
        pos[int(i32[k])].append(int(k))
    d = collections.Counter()
    for v, ks in pos.items():
        if 3 <= len(ks) <= 5000:
            dd = np.diff(ks) * 4
            for x in dd[dd >= 256]:
                d[int(x)] += 1
    return [{"period_bytes": p, "count": c} for p, c in d.most_common(top)]


def probe(path):
    b = open(path, "rb").read()
    le, be = float_windows(b, "<"), float_windows(b, ">")
    return {"file": os.path.basename(path), "bytes": len(b), "blocks_512": len(b) / 512.0,
            "whole_512_blocks": len(b) % 512 == 0, "first_64_bytes_hex": b[:64].hex(),
            "strings_first": strings(b), "n_strings_total": sum(1 for _ in re.finditer(rb"[\x20-\x7e]{6,}", b)),
            "ash_style_signatures": signatures(b)[:50], "periodic_int32_distances": periodic_words(b),
            "float32_plausible_fraction": {"little_endian_mean": float(np.mean(le)), "big_endian_mean": float(np.mean(be)),
                                           "little_endian_windows": le[:400], "big_endian_windows": be[:400]}}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("file")
    ap.add_argument("--json")
    a = ap.parse_args()
    r = probe(a.file)
    if a.json:
        json.dump(r, open(a.json, "w"), indent=1)
    print(json.dumps({k: v for k, v in r.items() if k not in ("strings_first", "float32_plausible_fraction")}, indent=1)[:2000])
    print("float32 plausible (LE/BE):", round(r["float32_plausible_fraction"]["little_endian_mean"], 3),
          round(r["float32_plausible_fraction"]["big_endian_mean"], 3))
    for s in r["strings_first"][:25]:
        print(f"  {s['offset']:>10}  {s['text']}")


if __name__ == "__main__":
    sys.exit(main())
