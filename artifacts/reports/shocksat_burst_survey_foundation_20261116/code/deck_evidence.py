#!/usr/bin/env python3
"""Extract checkable evidence from NASA's ShockSat correlation summary deck.

Source: FEM/Correlation/Final_Summary_Documentation_101521_rev1.pptx inside NASA's
public FEM_and_CAD.zip (74,518,670 bytes, CRC-32 6a9a1c7f in the archive directory).
The deck itself is NOT committed (74 MB, NASA's file). This script copies out only
(1) the slide text, (2) the text records of four vector tables, and (3) three FRF
figures used as measurement inputs for the digitisation pilot. Those small
extractions are committed under data/nasa_deck/ with hashes, so every later step
replays without the deck.

Usage:
  deck_evidence.py --deck PATH   re-extract from the deck, then build outputs
  deck_evidence.py               verify the committed extraction, then build outputs

Outputs:
  out/nasa_final_correlation.csv      NASA's test-vs-FEM table (frequency, cross-orthogonality)
  out/nasa_pretest_sensor_set.csv     NASA's own check of how well the 132 sensors separate FEM modes
  out/deck_evidence.json              quoted statements with slide numbers and derived statistics

Terms: "cross-orthogonality" is the mass-weighted overlap between a test mode shape
and a FEM mode shape, in percent; 100 means identical shapes at the sensors, 0 means
unrelated. "Pseudo-orthogonality" is the same check between FEM modes after they are
reduced to the sensor locations; a diagonal well below 100 means the sensor set
cannot tell that mode apart cleanly.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import struct
import sys
import zlib

HERE = os.path.dirname(os.path.abspath(__file__))
WS = os.path.dirname(HERE)
DD = os.path.join(WS, "data", "nasa_deck")

DECK_NAME = "FEM/Correlation/Final_Summary_Documentation_101521_rev1.pptx"
DECK_BYTES = 74518670
DECK_CRC32 = "6a9a1c7f"          # from the archive's central directory (out/zip_listings)
TABLE_SLIDES = {2: "test_self_orthogonality", 10: "final_cross_orthogonality",
                13: "fem_pseudo_orthogonality", 14: "pretest_tam_cross_orthogonality"}
FIG_SLIDES = {16: "fig_slide16_drive_point_11101X.png", 17: "fig_slide17_drive_point_11110Y.png",
              19: "fig_slide19_operator_variability.png"}
QUOTES = [  # (slide, key, exact substring that must be present in the slide text)
    (1, "configuration_used",
     "Only utilized the vertical free-free single bungee supported test configuration for modal correlation."),
    (1, "shaker_data_excluded",
     "Only utilized impact hammer test data because the blocks used for shaker testing had a significant mass "
     "loading impact on the modes and didn’t want to include them in the FEM."),
    (12, "sensor_set_limit",
     "Correlation will struggle above 150 Hz and is unlikely to meet requirements above 200 Hz due to "
     "instrumentation placement."),
    (16, "modal_bandwidth",
     "Comparison stopped at 400 Hz due to sample rate of data acquisition system setting for the modal tests"),
    (18, "impact_location_sensitivity",
     "the exact location of the impact in the frequency range above 150 Hz is critical"),
    (19, "impact_averaging", "The modal test always averages ~10 impacts together"),
    (46, "modes_from_two_runs",
     "Every test mode that was included in the correlation was able to be extracted from two different test runs"),
    (9, "bottom_box_unresolved",
     "The stainless-steel bottom box has been a very difficult part to correlate throughout this process and it is "
     "unknown why."),
]


def sha256_file(p):
    h = hashlib.sha256()
    with open(p, "rb") as fh:
        for b in iter(lambda: fh.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def emf_text_records(blob: bytes):
    """Text draw records of an Enhanced Metafile: list of [y, x, string] in device units.
    Record type 84 is EMR_EXTTEXTOUTW (UTF-16 text), 14 is end-of-file."""
    out, p = [], 0
    while p + 8 <= len(blob):
        typ, size = struct.unpack_from("<II", blob, p)
        if size < 8:
            break
        if typ == 84:
            x, y, n, off, _opt = struct.unpack_from("<iiIII", blob, p + 36)
            out.append([y, x, blob[p + off:p + off + 2 * n].decode("utf-16-le", "replace")])
        if typ == 14:
            break
        p += size
    return out


def extract(deck_path: str):
    from pptx import Presentation
    raw = open(deck_path, "rb").read()
    crc = f"{zlib.crc32(raw) & 0xFFFFFFFF:08x}"
    if len(raw) != DECK_BYTES or crc != DECK_CRC32:
        raise SystemExit(f"deck does not match NASA archive member: {len(raw)} bytes crc {crc}")
    os.makedirs(DD, exist_ok=True)
    prs = Presentation(deck_path)
    slides, tables = [], {}
    for i, s in enumerate(prs.slides, 1):
        texts, pics = [], []

        def walk(shapes):
            for sh in shapes:
                if sh.shape_type == 6:
                    walk(sh.shapes)
                    continue
                if sh.shape_type == 13:
                    pics.append(sh.image)
                if sh.has_text_frame and sh.text_frame.text.strip():
                    texts.append(sh.text_frame.text.strip())
        walk(s.shapes)
        slides.append({"slide": i, "texts": texts, "n_pictures": len(pics)})
        if i in TABLE_SLIDES:
            tables[TABLE_SLIDES[i]] = {"slide": i, "records": emf_text_records(pics[0].blob)}
        if i in FIG_SLIDES:
            open(os.path.join(DD, FIG_SLIDES[i]), "wb").write(pics[0].blob)
    json.dump(slides, open(os.path.join(DD, "slides_text.json"), "w"), indent=1, ensure_ascii=False)
    json.dump(tables, open(os.path.join(DD, "tables_raw.json"), "w"), indent=0)
    prov = {"deck_member": DECK_NAME, "deck_bytes": len(raw), "deck_crc32": crc,
            "deck_sha256": hashlib.sha256(raw).hexdigest(),
            "note": "NASA source material (reference inputs), not outputs generated by this project.",
            "files": {f: sha256_file(os.path.join(DD, f))
                      for f in ["slides_text.json", "tables_raw.json"] + list(FIG_SLIDES.values())}}
    json.dump(prov, open(os.path.join(DD, "PROVENANCE.json"), "w"), indent=1)


def verify():
    prov = json.load(open(os.path.join(DD, "PROVENANCE.json")))
    bad = [f for f, h in prov["files"].items() if sha256_file(os.path.join(DD, f)) != h]
    if bad:
        raise SystemExit(f"committed deck extraction changed: {bad}")
    return prov


def table_rows(records, x_min=40):
    """Group text records into rows by y and return each row's cells left to right,
    dropping the colour-scale legend that sits left of x_min."""
    rows = {}
    for y, x, s in records:
        rows.setdefault(y, []).append((x, s.strip()))
    return [[s for x, s in sorted(v) if x >= x_min] for _, v in sorted(rows.items())]


def parse_square(records, n_cols, has_diff):
    """Rows that start with an integer mode number and a frequency, followed by n_cols
    integer percentages (and an optional trailing signed percent difference)."""
    out = []
    for cells in table_rows(records):
        want = 2 + n_cols + (1 if has_diff else 0)
        if len(cells) != want or not cells[0].isdigit():
            continue
        try:
            f = float(cells[1])
            vals = [int(c) for c in cells[2:2 + n_cols]]
            diff = float(cells[-1]) if has_diff else None
        except ValueError:
            continue
        out.append({"mode": int(cells[0]), "freq_hz": f, "values": vals, "pct_diff": diff})
    return out


def header_freqs(records, label):
    for cells in table_rows(records, x_min=0):
        if label in cells:
            vals = []
            for c in cells:
                try:
                    vals.append(float(c))
                except ValueError:
                    pass
            return vals
    raise SystemExit(f"header row {label!r} not found")


def median(v):
    v = sorted(v)
    n = len(v)
    return v[n // 2] if n % 2 else 0.5 * (v[n // 2 - 1] + v[n // 2])


def build(prov):
    slides = json.load(open(os.path.join(DD, "slides_text.json")))
    tables = json.load(open(os.path.join(DD, "tables_raw.json")))
    by_slide = {s["slide"]: " \n".join(s["texts"]) for s in slides}
    quotes = []
    for slide, key, text in QUOTES:
        quotes.append({"slide": slide, "key": key, "text": text, "found_verbatim": text in by_slide[slide]})

    # --- final test-vs-FEM table (slide 10)
    rec = tables["final_cross_orthogonality"]["records"]
    fem_f = header_freqs(rec, "Test Shapes")           # 24 FEM frequencies
    rows = parse_square(rec, 24, True)
    final = []
    for r in rows:
        j = max(range(24), key=lambda k: r["values"][k])
        final.append({"test_mode": r["mode"], "f_test_hz": r["freq_hz"], "best_fem_col": j + 1,
                      "f_fem_best_hz": fem_f[j], "xo_best_pct": r["values"][j],
                      "pct_diff_nasa": r["pct_diff"],
                      "pct_diff_recomputed": round(100 * (fem_f[j] - r["freq_hz"]) / r["freq_hz"], 2)})
    with open(os.path.join(WS, "out", "nasa_final_correlation.csv"), "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(final[0].keys()))
        w.writeheader(); w.writerows(final)

    # --- pretest sensor-set checks (slides 13 and 14)
    pog = parse_square(tables["fem_pseudo_orthogonality"]["records"], 24, False)
    tam = parse_square(tables["pretest_tam_cross_orthogonality"]["records"], 24, True)
    fem24 = header_freqs(tables["fem_pseudo_orthogonality"]["records"], "FEM Shapes")
    sensor = []
    for i, r in enumerate(pog):
        t = tam[i] if i < len(tam) else None
        sensor.append({"fem_mode": r["mode"], "f_fem_hz": r["freq_hz"], "pseudo_orthogonality_diag_pct": r["values"][i],
                       "tam_freq_hz": t["freq_hz"] if t else None,
                       "tam_freq_error_pct": t["pct_diff"] if t else None})
    with open(os.path.join(WS, "out", "nasa_pretest_sensor_set.csv"), "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(sensor[0].keys()))
        w.writeheader(); w.writerows(sensor)

    self_o = parse_square(tables["test_self_orthogonality"]["records"], 33, False)
    offdiag = [abs(r["values"][k]) for i, r in enumerate(self_o) for k in range(33) if k != i]

    def band(rows, key, lo, hi):
        return [r for r in rows if lo <= r[key] < hi]

    ev = {
        "source": {k: prov[k] for k in ("deck_member", "deck_bytes", "deck_crc32", "deck_sha256")},
        "quotes": quotes,
        "final_correlation": {
            "n_test_modes": len(final),
            "f_test_range_hz": [final[0]["f_test_hz"], final[-1]["f_test_hz"]],
            "abs_pct_diff_median": median([abs(r["pct_diff_nasa"]) for r in final]),
            "abs_pct_diff_max": max(abs(r["pct_diff_nasa"]) for r in final),
            "n_within_5pct": sum(abs(r["pct_diff_nasa"]) <= 5.0 for r in final),
            "xo_best_median_pct": median([r["xo_best_pct"] for r in final]),
            "n_xo_ge_90": sum(r["xo_best_pct"] >= 90 for r in final),
            "n_xo_ge_80": sum(r["xo_best_pct"] >= 80 for r in final),
            "below_150hz": {"n": len(band(final, "f_test_hz", 0, 150)),
                            "abs_pct_diff_median": median([abs(r["pct_diff_nasa"]) for r in band(final, "f_test_hz", 0, 150)]),
                            "xo_best_median_pct": median([r["xo_best_pct"] for r in band(final, "f_test_hz", 0, 150)])},
            "from_150hz": {"n": len(band(final, "f_test_hz", 150, 1e9)),
                           "abs_pct_diff_median": median([abs(r["pct_diff_nasa"]) for r in band(final, "f_test_hz", 150, 1e9)]),
                           "xo_best_median_pct": median([r["xo_best_pct"] for r in band(final, "f_test_hz", 150, 1e9)])},
            "max_abs_gap_nasa_vs_recomputed_pct_diff": max(abs(r["pct_diff_nasa"] - r["pct_diff_recomputed"]) for r in final),
        },
        "pretest_sensor_set": {
            "n_fem_modes": len(sensor),
            "pseudo_orthogonality_diag_median_below_150hz": median([r["pseudo_orthogonality_diag_pct"] for r in band(sensor, "f_fem_hz", 0, 150)]),
            "pseudo_orthogonality_diag_median_from_150hz": median([r["pseudo_orthogonality_diag_pct"] for r in band(sensor, "f_fem_hz", 150, 1e9)]),
            "pseudo_orthogonality_diag_min": min(r["pseudo_orthogonality_diag_pct"] for r in sensor),
            "tam_freq_error_median_below_150hz": median([r["tam_freq_error_pct"] for r in band(sensor, "f_fem_hz", 0, 150)]),
            "tam_freq_error_median_from_150hz": median([r["tam_freq_error_pct"] for r in band(sensor, "f_fem_hz", 150, 1e9)]),
            "tam_freq_error_max": max(r["tam_freq_error_pct"] for r in sensor),
            "fem_freqs_hz_header_check": fem24[:3],
        },
        "test_self_orthogonality": {"n_modes": len(self_o), "offdiag_median_pct": median(offdiag),
                                    "offdiag_max_pct": max(offdiag),
                                    "n_offdiag_gt_10pct_pairs": sum(v > 10 for v in offdiag) // 2},
    }
    json.dump(ev, open(os.path.join(WS, "out", "deck_evidence.json"), "w"), indent=1, ensure_ascii=False)
    return ev


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--deck")
    a = ap.parse_args()
    if a.deck:
        extract(a.deck)
    prov = verify()
    ev = build(prov)
    print(json.dumps({k: v for k, v in ev.items() if k != "quotes"}, indent=1)[:2600])
    print("quotes found verbatim:", [(q["slide"], q["key"], q["found_verbatim"]) for q in ev["quotes"]])


if __name__ == "__main__":
    main()
