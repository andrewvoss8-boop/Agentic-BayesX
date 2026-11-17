#!/usr/bin/env python3
"""Dump every sheet of an .xlsx file (cell values only) to JSON, for test logs and test
reports fetched from NASA. Usage: xlsx_dump.py FILE --out OUT.json [--max-rows N]"""
import argparse
import json

import openpyxl


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("file")
    ap.add_argument("--out", required=True)
    ap.add_argument("--max-rows", type=int, default=2000)
    a = ap.parse_args()
    wb = openpyxl.load_workbook(a.file, read_only=True, data_only=True)
    out = {"file": a.file, "sheets": {}}
    for ws in wb.worksheets:
        rows = []
        for r in ws.iter_rows(values_only=True):
            if any(c is not None for c in r):
                rows.append([None if c is None else (c if isinstance(c, (int, float)) else str(c)) for c in r])
            if len(rows) >= a.max_rows:
                break
        out["sheets"][ws.title] = rows
    json.dump(out, open(a.out, "w"), indent=0, default=str)
    print(a.out, {k: len(v) for k, v in out["sheets"].items()})


if __name__ == "__main__":
    main()
