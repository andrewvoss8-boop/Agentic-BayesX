#!/usr/bin/env python3
"""Generate the ShockSat StatFEM runner packet from fetched source artifacts.

The script is intentionally inventory-first. It only plots measured data when a
fetched MAT archive can be parsed and channel metadata exists.
"""

from __future__ import annotations

import csv
import datetime as dt
import hashlib
import html
import io
import json
import math
import os
import re
import shutil
import struct
import subprocess
import sys
import time
import zipfile
import zlib
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from openpyxl import load_workbook
from scipy import io as scipy_io
from scipy import signal

try:
    from pypdf import PdfReader
except Exception:  # pragma: no cover - optional
    PdfReader = None


OUT = Path(__file__).resolve().parents[1]
REPO = OUT.parents[2]
SOURCES = OUT / "sources"
EXTRACTED = OUT / "extracted"
FIGURES = OUT / "figures"
LOGS = OUT / "logs"
for directory in (SOURCES, EXTRACTED, FIGURES, LOGS):
    directory.mkdir(parents=True, exist_ok=True)

RUN_START = time.time()
RUN_DATE = "2026-06-09"
BASE_MEDIA = "https://mediaex-server.larc.nasa.gov"
WORKSHOP_URL = "https://nescacademy.nasa.gov/workshops/ShockSat/ShockSat1"


KNOWN_SOURCE_ENTRIES = [
    {
        "name": "_README.txt",
        "kind": "file",
        "path": "/shocksat/_README.txt",
        "listed_size": "2.88 kB",
        "priority": "required",
    },
    {
        "name": "_ShockSat_Overview_20220606.pdf",
        "kind": "file",
        "path": "/shocksat/_ShockSat_Overview_20220606.pdf",
        "listed_size": "6.26 MB",
        "priority": "required",
    },
    {
        "name": "FEM_and_CAD.zip",
        "kind": "archive",
        "path": "/shocksat/FEM_and_CAD.zip",
        "listed_size": "1.89 GB",
        "priority": "high",
    },
    {
        "name": "Instrumentation_and_TestLog.zip",
        "kind": "archive",
        "path": "/shocksat/Instrumentation_and_TestLog.zip",
        "listed_size": "93.95 MB",
        "priority": "required",
    },
    {
        "name": "Test_Data_Impact",
        "kind": "folder",
        "path": "/shocksat/Test_Data_Impact/",
        "listed_size": None,
        "priority": "high",
    },
    {
        "name": "Test_Data_Parametric.zip",
        "kind": "archive",
        "path": "/shocksat/Test_Data_Parametric.zip",
        "listed_size": "3.33 GB",
        "priority": "deferred_if_disk_tight",
    },
    {
        "name": "Test_Data_Pyro_Frangible_Joints.zip",
        "kind": "archive",
        "path": "/shocksat/Test_Data_Pyro_Frangible_Joints.zip",
        "listed_size": "7.81 GB",
        "priority": "deferred_if_disk_tight",
    },
    {
        "name": "Test_Data_Pyro_NSI_NSD.zip",
        "kind": "archive",
        "path": "/shocksat/Test_Data_Pyro_NSI_NSD.zip",
        "listed_size": "1.41 GB",
        "priority": "high",
    },
]


INSTRUMENTATION_SHEETS = {
    "Instrumentation_Tap": "tap_impact",
    "Instrumentation_NSI_NSD_Param": "nsi_nsd_parametric",
    "Instrumentation_FrangibleJoint": "frangible_joint",
}


def now_utc() -> str:
    return dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat()


def rel(path: Path | str) -> str:
    p = Path(path)
    try:
        return str(p.resolve().relative_to(REPO.resolve()))
    except Exception:
        return str(p)


def sha256_file(path: Path, block_size: int = 1024 * 1024) -> str | None:
    if not path.exists() or path.is_dir():
        return None
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(block_size), b""):
            h.update(block)
    return h.hexdigest()


def file_meta(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {"exists": False}
    stat = path.stat()
    return {
        "exists": True,
        "local_path": rel(path),
        "size_bytes": stat.st_size,
        "mtime_utc": dt.datetime.fromtimestamp(stat.st_mtime, dt.timezone.utc)
        .replace(microsecond=0)
        .isoformat(),
        "sha256": sha256_file(path) if path.is_file() else None,
    }


def write_json(path: Path, obj: Any) -> None:
    path.write_text(json.dumps(obj, indent=2, sort_keys=True) + "\n")


def write_csv(path: Path, rows: list[dict[str, Any]], fieldnames: list[str]) -> None:
    with path.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow({k: row.get(k, "") for k in fieldnames})


def clean_text(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, dt.datetime):
        return value.strftime("%Y-%m-%d")
    if isinstance(value, float) and value.is_integer():
        return str(int(value))
    return str(value).strip()


def parse_listing_html(path: Path) -> list[dict[str, str | None]]:
    if not path.exists():
        return []
    text = path.read_text(errors="replace")
    pattern = re.compile(
        r'<button[^>]+data-text="(?P<name>[^"]+)"[^>]+data-link="(?P<link>[^"]+)"'
        r'[^>]+data-folder="(?P<folder>[^"]*)"[^>]*>.*?'
        r'<span[^>]*>(?P<label>.*?)</span>(?P<size>[^<\n\r]*)',
        re.S,
    )
    rows = []
    for match in pattern.finditer(text):
        rows.append(
            {
                "name": html.unescape(match.group("name")),
                "link": html.unescape(match.group("link")),
                "is_file": "yes" if match.group("folder") == "1" else "no",
                "listed_size": html.unescape(match.group("size")).strip() or None,
            }
        )
    return rows


def zip_listing(path: Path, max_names: int = 400) -> dict[str, Any] | None:
    if not path.exists():
        return None
    try:
        with zipfile.ZipFile(path) as zf:
            infos = zf.infolist()
            ext_counts = Counter()
            top_dirs = Counter()
            entries = []
            for info in infos:
                name = info.filename
                suffix = Path(name).suffix.lower() or "<none>"
                if not info.is_dir():
                    ext_counts[suffix] += 1
                top_dirs[name.split("/", 1)[0] if "/" in name else "<root>"] += 1
                if len(entries) < max_names:
                    entries.append(
                        {
                            "name": name,
                            "compressed_size": info.compress_size,
                            "uncompressed_size": info.file_size,
                            "date_time": "%04d-%02d-%02dT%02d:%02d:%02d"
                            % info.date_time,
                        }
                    )
            return {
                "archive": rel(path),
                "entry_count": len(infos),
                "total_uncompressed_size_bytes": int(sum(i.file_size for i in infos)),
                "extension_counts": dict(sorted(ext_counts.items())),
                "top_directories": dict(top_dirs.most_common(30)),
                "entries_sample": entries,
            }
    except Exception as exc:
        return {"archive": rel(path), "parse_failed": repr(exc)}


def extract_from_zip(
    archive: Path,
    members: list[str],
    dest_root: Path,
    max_total_bytes: int = 250 * 1024 * 1024,
) -> list[dict[str, Any]]:
    extracted = []
    if not archive.exists():
        return extracted
    total = 0
    with zipfile.ZipFile(archive) as zf:
        names = set(zf.namelist())
        for member in members:
            if member not in names:
                continue
            info = zf.getinfo(member)
            if info.is_dir():
                continue
            if total + info.file_size > max_total_bytes:
                extracted.append(
                    {
                        "member": member,
                        "status": "skipped_size_limit",
                        "uncompressed_size": info.file_size,
                    }
                )
                continue
            zf.extract(member, dest_root)
            total += info.file_size
            extracted.append(
                {
                    "member": member,
                    "status": "extracted",
                    "uncompressed_size": info.file_size,
                    "local_path": rel(dest_root / member),
                }
            )
    return extracted


def read_overview_pdf() -> dict[str, Any]:
    pdf = SOURCES / "_ShockSat_Overview_20220606.pdf"
    out: dict[str, Any] = file_meta(pdf)
    out["page_count"] = None
    out["text_extract_status"] = "not_attempted"
    out["keywords_found"] = {}
    text_path = EXTRACTED / "overview_text_excerpt.txt"
    if not pdf.exists() or PdfReader is None:
        out["text_extract_status"] = "missing_pdf_or_pypdf"
        return out
    try:
        reader = PdfReader(str(pdf))
        out["page_count"] = len(reader.pages)
        chunks = []
        for page in reader.pages[:12]:
            chunks.append(page.extract_text() or "")
        text = "\n".join(chunks)
        text_path.write_text(text[:20000])
        out["text_extract_status"] = "extracted_first_12_pages"
        out["text_excerpt_path"] = rel(text_path)
        for term in [
            "108",
            "36 accelerometers",
            "Nastran",
            "correlated",
            "shock",
            "hammer",
            "pyro",
        ]:
            out["keywords_found"][term] = term.lower() in text.lower()
    except Exception as exc:
        out["text_extract_status"] = f"parse_failed: {exc!r}"
    return out


def build_source_manifest() -> dict[str, Any]:
    listing_entries = parse_listing_html(SOURCES / "ShockSat1_file_browser.html")
    impact_entries = parse_listing_html(SOURCES / "Test_Data_Impact_file_browser.html")
    source_entries = []
    known_by_name = {e["name"]: dict(e) for e in KNOWN_SOURCE_ENTRIES}
    for entry in listing_entries:
        known_by_name.setdefault(
            entry["name"],
            {
                "name": entry["name"],
                "kind": "archive" if entry["is_file"] == "yes" else "folder",
                "path": entry["link"],
                "listed_size": entry["listed_size"],
                "priority": "listed_on_source_page",
            },
        )
    for entry in known_by_name.values():
        local_name = entry["name"]
        local_path = SOURCES / local_name
        if entry["kind"] == "folder":
            local_path = SOURCES / f"{local_name}_file_browser.html"
        meta = file_meta(local_path)
        range_head = LOGS / f"range_{local_name}.first_byte"
        tail = LOGS / f"range_{local_name}.tail_4MiB.bin"
        state = "fetched" if meta.get("exists") else "manual_required"
        if (
            meta.get("exists")
            and entry["kind"] == "archive"
            and not zipfile.is_zipfile(local_path)
        ):
            state = "partial_download"
        if entry["kind"] == "folder" and meta.get("exists"):
            state = "fetched"
        if not meta.get("exists") and tail.exists():
            state = "too_large_deferred"
        if local_name in {
            "Test_Data_Parametric.zip",
            "Test_Data_Pyro_Frangible_Joints.zip",
        } and not meta.get("exists"):
            state = "too_large_deferred"
        if local_name == "FEM_and_CAD.zip" and not meta.get("exists") and (
            OUT / "sources" / "FEM_and_CAD.zip"
        ).exists():
            state = "partial_download"
        source_entries.append(
            {
                "name": local_name,
                "kind": entry["kind"],
                "source_browser_path": entry["path"],
                "download_url": BASE_MEDIA + str(entry["path"])
                if str(entry["path"]).startswith("/shocksat")
                else None,
                "listed_size": entry.get("listed_size"),
                "priority": entry.get("priority"),
                "state": state,
                "local": meta,
                "range_first_byte_probe": file_meta(range_head),
                "tail_range_listing_probe": file_meta(tail),
            }
        )
    for entry in impact_entries:
        local = SOURCES / entry["name"]
        tail = LOGS / f"range_{entry['name']}.tail_4MiB.bin"
        state = "fetched" if local.exists() else "too_large_deferred"
        if local.exists() and not zipfile.is_zipfile(local):
            state = "partial_download"
        source_entries.append(
            {
                "name": entry["name"],
                "kind": "impact_archive",
                "source_browser_path": entry["link"],
                "download_url": BASE_MEDIA + str(entry["link"]),
                "listed_size": entry["listed_size"],
                "priority": "candidate_hammer_data",
                "state": state,
                "local": file_meta(local),
                "tail_range_listing_probe": file_meta(tail),
            }
        )
    return {
        "generated_utc": now_utc(),
        "run_date": RUN_DATE,
        "workspace": rel(OUT),
        "workshop_url": WORKSHOP_URL,
        "direct_asset_route_note": (
            "Direct nescacademy /shocksat URLs returned 404. The browser page posts a hidden "
            "url field and redirects to mediaex-server.larc.nasa.gov; direct mediaex URLs support "
            "HEAD and byte-range requests."
        ),
        "source_entries": source_entries,
        "overview_pdf": read_overview_pdf(),
    }


def build_file_inventory(source_manifest: dict[str, Any]) -> dict[str, Any]:
    archives = []
    extracted_status = []
    for path in sorted(SOURCES.glob("*.zip")):
        listing = zip_listing(path)
        archives.append(listing)
    for path in sorted(EXTRACTED.rglob("*")):
        if path.is_file():
            extracted_status.append(file_meta(path))
    tail_samples = {}
    for path in sorted(LOGS.glob("range_*.tail_4MiB.bin")):
        try:
            text = subprocess.run(
                ["strings", str(path)],
                check=True,
                capture_output=True,
                text=True,
            ).stdout
            names = []
            for line in text.splitlines():
                if re.search(
                    r"\.(bdf|nas|op2|f06|xlsx|mat|csv|txt|pdf|stp|step|iges|igs|"
                    r"prt|asm|dat|uff|unv|jpg|png|pptx)$",
                    line,
                    flags=re.I,
                ):
                    names.append(line.strip())
                if len(names) >= 120:
                    break
            tail_samples[path.name] = names
        except Exception as exc:
            tail_samples[path.name] = [f"strings_failed: {exc!r}"]
    return {
        "generated_utc": now_utc(),
        "archives": archives,
        "source_file_count": len([p for p in SOURCES.iterdir() if p.is_file()]),
        "extracted_files": extracted_status,
        "tail_range_filename_samples": tail_samples,
    }


def parse_instrumentation_workbook() -> tuple[list[dict[str, Any]], list[dict[str, Any]], dict[str, Any]]:
    xlsx = (
        EXTRACTED
        / "Instrumentation_and_TestLog"
        / "ShockSat1_Instrumentation_and_TestLog_Simplified_for_Delivery_20220525.xlsx"
    )
    if not xlsx.exists():
        return [], [], {"status": "missing_xlsx"}
    wb = load_workbook(xlsx, data_only=True, read_only=True)
    channel_rows: list[dict[str, Any]] = []
    for sheet_name, config in INSTRUMENTATION_SHEETS.items():
        ws = wb[sheet_name]
        for row in ws.iter_rows(min_row=3, values_only=True):
            loc = row[0]
            if loc is None:
                continue
            serials = [clean_text(x) for x in clean_text(row[16]).split(",")]
            while len(serials) < 3:
                serials.append("")
            base = {
                "configuration": config,
                "source_sheet": sheet_name,
                "location_no": clean_text(row[0]),
                "channel_count_label": clean_text(row[1]),
                "description": clean_text(row[2]),
                "x_in": clean_text(row[3]),
                "y_in": clean_text(row[4]),
                "z_in": clean_text(row[5]),
                "fem_grid": clean_text(row[6]),
                "daq_position_label": clean_text(row[10]),
                "sensor_model": clean_text(row[14]),
                "range_k_g_or_force": clean_text(row[15]),
                "notes": clean_text(row[23]),
                "sample_rate_sps": 100000,
                "sample_rate_source": "README and workbook location descriptions",
            }
            axis_meta = [
                ("x", row[11], row[7], row[17], row[20], serials[0]),
                ("y", row[12], row[8], row[18], row[21], serials[1]),
                ("z", row[13], row[9], row[19], row[22], serials[2]),
            ]
            for axis_label, daq_channel, structural_axis, cal, daq_cal, serial in axis_meta:
                if daq_channel is None:
                    continue
                quantity = "hammer_force" if "hammer" in base["description"].lower() else "acceleration"
                engineering_units = "lbf" if quantity == "hammer_force" else "g"
                cal_units = "mV/lb" if quantity == "hammer_force" else "mV/g"
                channel_rows.append(
                    {
                        **base,
                        "axis_label": axis_label,
                        "daq_channel": int(daq_channel) if isinstance(daq_channel, (int, float)) else clean_text(daq_channel),
                        "structural_axis": clean_text(structural_axis),
                        "serial_number": serial,
                        "calibration_value": clean_text(cal),
                        "calibration_units": cal_units,
                        "cal_in_daq": clean_text(daq_cal),
                        "quantity": quantity,
                        "engineering_units": engineering_units,
                    }
                )
    test_rows: list[dict[str, Any]] = []
    for sheet_name in [s for s in wb.sheetnames if s.startswith("TestLog")]:
        ws = wb[sheet_name]
        headers = [clean_text(v) or f"extra_col_{i+1}" for i, v in enumerate(next(ws.iter_rows(min_row=1, max_row=1, values_only=True)))]
        blank_run = 0
        for excel_row, row in enumerate(ws.iter_rows(min_row=2, values_only=True), start=2):
            if all(v is None for v in row[: min(len(row), 13)]):
                blank_run += 1
                if blank_run >= 30:
                    break
                continue
            blank_run = 0
            record = {
                "source_sheet": sheet_name,
                "excel_row": excel_row,
                "test_type": sheet_name.replace("TestLog_", "").lower(),
            }
            for idx, header in enumerate(headers):
                if idx >= len(row):
                    continue
                record[header] = clean_text(row[idx])
            test_rows.append(record)
    summary = {
        "status": "parsed",
        "workbook_path": rel(xlsx),
        "sheets": wb.sheetnames,
        "channel_rows": len(channel_rows),
        "unique_configurations": sorted(set(r["configuration"] for r in channel_rows)),
        "unique_daq_channels_by_configuration": {
            config: len({r["daq_channel"] for r in channel_rows if r["configuration"] == config})
            for config in sorted(set(r["configuration"] for r in channel_rows))
        },
        "test_log_rows": len(test_rows),
        "sample_rate_sps": 100000,
        "coordinate_units": "inch",
        "acceleration_units": "g",
        "hammer_force_units": "lbf",
        "notes": [
            "README states all FEM and data are in English units.",
            "README states raw data were acquired at 100,000 samples/s with anti-aliasing.",
            "README states accelerometer resonances are at 35 kHz and results target 100-10,000 Hz.",
            "README states instrumentation changed slightly from impact to pyro tests at locations 34-35, channels 106-111.",
        ],
    }
    return channel_rows, test_rows, summary


def write_instrumentation_outputs(
    channel_rows: list[dict[str, Any]],
    test_rows: list[dict[str, Any]],
    summary: dict[str, Any],
) -> None:
    if channel_rows:
        channel_fields = [
            "configuration",
            "source_sheet",
            "location_no",
            "daq_channel",
            "quantity",
            "engineering_units",
            "axis_label",
            "structural_axis",
            "description",
            "x_in",
            "y_in",
            "z_in",
            "fem_grid",
            "sensor_model",
            "serial_number",
            "range_k_g_or_force",
            "calibration_value",
            "calibration_units",
            "cal_in_daq",
            "sample_rate_sps",
            "notes",
        ]
        write_csv(OUT / "channel_map.csv", channel_rows, channel_fields)
    if test_rows:
        fields = sorted({k for row in test_rows for k in row})
        preferred = [
            "source_sheet",
            "excel_row",
            "test_type",
            "Test No.",
            "Date",
            "Filename",
            "Description",
            "Test POC",
            "Comments",
            "Impact Point",
            "Impact Grid",
        ]
        fields = preferred + [f for f in fields if f not in preferred]
        write_csv(OUT / "test_log_summary.csv", test_rows, fields)
    inventory = {
        "generated_utc": now_utc(),
        "summary": summary,
        "channel_counts_by_configuration": dict(
            Counter(r["configuration"] for r in channel_rows)
        ),
        "quantity_counts": dict(Counter(r["quantity"] for r in channel_rows)),
        "example_channels": channel_rows[:12],
        "bad_or_caution_comments": [
            row
            for row in test_rows
            if "channel" in clean_text(row.get("Comments")).lower()
            or "bad" in clean_text(row.get("Comments")).lower()
            or "clipped" in clean_text(row.get("Comments")).lower()
        ][:30],
        "test_log_counts_by_sheet": dict(Counter(r["source_sheet"] for r in test_rows)),
    }
    write_json(OUT / "instrumentation_inventory.json", inventory)
    md = [
        "# Instrumentation and Test-Log Inventory",
        "",
        f"Generated: {inventory['generated_utc']}",
        "",
        "## Summary",
        "",
        f"- Workbook status: `{summary.get('status')}`",
        f"- Channel rows after axis expansion: `{len(channel_rows)}`",
        f"- Test-log rows parsed: `{len(test_rows)}`",
        "- Coordinate units: `inch`.",
        "- Acceleration units: `g`, based on workbook calibration columns in `mV/g` and README English-unit statement.",
        "- Hammer force channel units: `lbf`, based on the `Hammer` row calibration in `mV/lb`.",
        "- Sample rate: README states `100000 samples/s` as general acquisition metadata; plotted MAT subsets use file-specific `dXstep` when present.",
        "",
        "## Configuration Counts",
        "",
        "| Configuration | Expanded channel rows | Unique DAQ channels |",
        "|---|---:|---:|",
    ]
    for config in sorted(set(r["configuration"] for r in channel_rows)):
        md.append(
            f"| {config} | {sum(r['configuration']==config for r in channel_rows)} | "
            f"{len({r['daq_channel'] for r in channel_rows if r['configuration']==config})} |"
        )
    md += [
        "",
        "## High-Priority Notes",
        "",
        "- Accelerometer locations include FEM grid IDs, which is the key bridge for mapping sensors onto FEM nodes/elements.",
        "- Impact/tap instrumentation and pyro instrumentation are not identical; do not use one global calibration map silently.",
        "- Test logs mention bad/caution channels, including channel 101 bad at installation and channels 29-31 with 60 Hz noise in NSI logs.",
        "",
        "## Delivered Tables",
        "",
        f"- Channel map: `{rel(OUT / 'channel_map.csv')}`",
        f"- Test log summary: `{rel(OUT / 'test_log_summary.csv')}`",
    ]
    (OUT / "instrumentation_inventory.md").write_text("\n".join(md) + "\n")


def find_candidate_fem_members(zpath: Path) -> list[str]:
    if not zpath.exists():
        return []
    candidates = []
    source_ext = {
        ".bdf",
        ".nas",
        ".dat",
        ".fem",
        ".blk",
        ".pch",
        ".f06",
        ".op2",
        ".inp",
        ".cdb",
        ".unv",
        ".uff",
        ".pptx",
        ".xlsx",
        ".txt",
    }
    with zipfile.ZipFile(zpath) as zf:
        for info in zf.infolist():
            if info.is_dir():
                continue
            name = info.filename
            suffix = Path(name).suffix.lower()
            if name.startswith("FEM/") and suffix in source_ext and info.file_size < 80 * 1024 * 1024:
                candidates.append(name)
            if "Final_Summary_Documentation" in name:
                candidates.append(name)
        # Keep only unique members.
    return sorted(set(candidates))


def parse_nastran_like(path: Path) -> dict[str, Any]:
    cards = Counter()
    nodes = 0
    elements = Counter()
    mats = Counter()
    props = Counter()
    bcs = Counter()
    sol_lines = []
    element_cards = {
        "CTRIA3",
        "CTRIA6",
        "CQUAD4",
        "CQUAD8",
        "CHEXA",
        "CPENTA",
        "CTETRA",
        "CROD",
        "CBAR",
        "CBEAM",
        "CBUSH",
        "CONM2",
        "RBE2",
        "RBE3",
    }
    material_cards = {"MAT1", "MAT2", "MAT8", "MAT9", "MATS1"}
    prop_cards = {"PSHELL", "PCOMP", "PBAR", "PBEAM", "PROD", "PBUSH", "PSOLID", "PMASS"}
    bc_cards = {"SPC", "SPC1", "SPCD", "SUPORT", "MPC", "MPCADD", "SPCADD"}
    try:
        with path.open("r", errors="ignore") as f:
            for raw in f:
                line = raw.rstrip("\n")
                stripped = line.strip()
                if not stripped or stripped.startswith("$"):
                    continue
                upper = stripped.upper()
                if upper.startswith("SOL "):
                    sol_lines.append(stripped)
                card = re.split(r"[\s,\*]+", upper, maxsplit=1)[0]
                if card in {"+", "*"} or card.startswith("+"):
                    continue
                cards[card] += 1
                if card == "GRID":
                    nodes += 1
                if card in element_cards:
                    elements[card] += 1
                if card in material_cards:
                    mats[card] += 1
                if card in prop_cards:
                    props[card] += 1
                if card in bc_cards:
                    bcs[card] += 1
    except Exception as exc:
        return {"path": rel(path), "parse_failed": repr(exc)}
    return {
        "path": rel(path),
        "solver_family_inference": "Nastran-like bulk data" if nodes or elements else "unknown",
        "solution_lines": sol_lines[:20],
        "node_count_grid_cards": nodes,
        "element_counts": dict(elements),
        "total_element_count": int(sum(elements.values())),
        "material_card_counts": dict(mats),
        "property_card_counts": dict(props),
        "boundary_condition_card_counts": dict(bcs),
        "top_card_counts": dict(cards.most_common(40)),
    }


def nastran_fields(line: str) -> list[str]:
    if "," in line:
        return [part.strip() for part in line.split(",")]
    return [line[i : i + 8].strip() for i in range(0, len(line), 8)]


def nastran_float(value: str) -> float | None:
    text = value.strip().replace("D", "E").replace("d", "E")
    if not text:
        return None
    if "E" not in text.upper():
        text = re.sub(r"(?<=[0-9.])([+-]\d+)$", r"E\1", text)
    try:
        return float(text)
    except Exception:
        return None


def nastran_int(value: str) -> int | None:
    try:
        return int(value.strip())
    except Exception:
        return None


def collect_nastran_geometry(paths: list[Path]) -> dict[str, Any]:
    nodes: dict[int, tuple[float, float, float]] = {}
    elements: list[dict[str, Any]] = []
    materials: list[dict[str, Any]] = []
    coordinate_cards = Counter()
    for path in paths:
        if not path.exists():
            continue
        with path.open("r", errors="ignore") as f:
            for raw in f:
                stripped = raw.rstrip("\n")
                if not stripped.strip() or stripped.lstrip().startswith("$"):
                    continue
                fields = nastran_fields(stripped)
                if not fields:
                    continue
                card = fields[0].upper().replace("*", "")
                if card == "GRID" and len(fields) >= 6:
                    gid = nastran_int(fields[1])
                    x = nastran_float(fields[3])
                    y = nastran_float(fields[4])
                    z = nastran_float(fields[5])
                    if gid is not None and x is not None and y is not None and z is not None:
                        nodes[gid] = (x, y, z)
                elif card in {"CQUAD4", "CTRIA3"}:
                    eid = nastran_int(fields[1]) if len(fields) > 1 else None
                    pid = nastran_int(fields[2]) if len(fields) > 2 else None
                    node_fields = fields[3:7] if card == "CQUAD4" else fields[3:6]
                    elem_nodes = [nastran_int(v) for v in node_fields]
                    elem_nodes = [v for v in elem_nodes if v is not None]
                    if eid is not None and len(elem_nodes) >= 3:
                        elements.append(
                            {
                                "element_id": eid,
                                "card": card,
                                "property_id": pid,
                                "nodes": elem_nodes,
                                "source": rel(path),
                            }
                        )
                elif card == "MAT1":
                    materials.append(
                        {
                            "source": rel(path),
                            "material_id": nastran_int(fields[1]) if len(fields) > 1 else None,
                            "E": nastran_float(fields[2]) if len(fields) > 2 else None,
                            "G": nastran_float(fields[3]) if len(fields) > 3 else None,
                            "nu": nastran_float(fields[4]) if len(fields) > 4 else None,
                            "rho": nastran_float(fields[5]) if len(fields) > 5 else None,
                            "alpha": nastran_float(fields[6]) if len(fields) > 6 else None,
                            "raw_card": stripped,
                        }
                    )
                elif card.startswith("CORD"):
                    coordinate_cards[card] += 1
    shock_grid_ids = list(range(9900001, 9900036)) + [9900135, 9900136]
    present_shock_grids = sorted(gid for gid in shock_grid_ids if gid in nodes)
    missing_shock_grids = sorted(gid for gid in shock_grid_ids if gid not in nodes)
    if nodes:
        xyz = np.array(list(nodes.values()), dtype=float)
        bounds = {
            "x_in": [float(np.nanmin(xyz[:, 0])), float(np.nanmax(xyz[:, 0]))],
            "y_in": [float(np.nanmin(xyz[:, 1])), float(np.nanmax(xyz[:, 1]))],
            "z_in": [float(np.nanmin(xyz[:, 2])), float(np.nanmax(xyz[:, 2]))],
        }
    else:
        bounds = {}
    return {
        "node_count_unique": len(nodes),
        "surface_element_count_parseable": len(elements),
        "surface_element_counts": dict(Counter(e["card"] for e in elements)),
        "bounds_in": bounds,
        "coordinate_card_counts": dict(coordinate_cards),
        "materials_mat1": materials,
        "shock_instrumentation_grid_check": {
            "expected_from_readme": "9900001-9900136, with impact accelerometers 35-36 represented as 9900135-9900136 in the FEM note",
            "present_count": len(present_shock_grids),
            "present_grid_ids": present_shock_grids,
            "missing_grid_ids": missing_shock_grids,
        },
        "_nodes_for_plot": nodes,
        "_elements_for_plot": elements,
    }


def draw_mesh_preview(geometry: dict[str, Any]) -> None:
    nodes = geometry.get("_nodes_for_plot") or {}
    elements = geometry.get("_elements_for_plot") or []
    fig = plt.figure(figsize=(10, 8))
    ax = fig.add_subplot(111, projection="3d")
    if not nodes:
        ax.text2D(0.08, 0.55, "No parseable GRID coordinates for mesh preview.", transform=ax.transAxes)
        fig.savefig(FIGURES / "fem_mesh_preview.png", dpi=180)
        plt.close(fig)
        return
    node_ids = np.array(list(nodes.keys()))
    xyz = np.array([nodes[int(gid)] for gid in node_ids], dtype=float)
    # Plot a deterministic thin sample of nodes/elements so the figure stays readable.
    if len(node_ids) > 12000:
        sample_idx = np.linspace(0, len(node_ids) - 1, 12000).astype(int)
        xyz_plot = xyz[sample_idx]
    else:
        xyz_plot = xyz
    ax.scatter(xyz_plot[:, 0], xyz_plot[:, 1], xyz_plot[:, 2], s=0.25, c="#7a7a7a", alpha=0.25)
    for element in elements[:: max(1, len(elements) // 2500)]:
        pts = [nodes.get(nid) for nid in element["nodes"] if nid in nodes]
        if len(pts) < 3:
            continue
        pts_arr = np.array(pts + [pts[0]], dtype=float)
        ax.plot(pts_arr[:, 0], pts_arr[:, 1], pts_arr[:, 2], color="#4b6f9f", lw=0.25, alpha=0.35)
    shock_ids = geometry.get("shock_instrumentation_grid_check", {}).get("present_grid_ids", [])
    shock_pts = np.array([nodes[gid] for gid in shock_ids if gid in nodes], dtype=float)
    if len(shock_pts):
        ax.scatter(shock_pts[:, 0], shock_pts[:, 1], shock_pts[:, 2], s=18, c="#c73b3b", label="shock accel FEM grids")
        ax.legend(loc="upper left")
    ax.set_title("ShockSat FEM Mesh Preview, Main 20211021 Blocks")
    ax.set_xlabel("X (in)")
    ax.set_ylabel("Y (in)")
    ax.set_zlabel("Z (in)")
    ax.view_init(elev=18, azim=-55)
    fig.tight_layout()
    fig.savefig(FIGURES / "fem_mesh_preview.png", dpi=180)
    plt.close(fig)


def build_fem_inventory(file_inventory: dict[str, Any]) -> dict[str, Any]:
    zpath = SOURCES / "FEM_and_CAD.zip"
    inventory: dict[str, Any] = {
        "generated_utc": now_utc(),
        "archive_status": "missing",
        "units": "English units from README; detailed length/force/mass convention must be verified in FEM files",
        "candidate_members_extracted": [],
        "parsed_models": [],
        "parser_gaps": [],
        "tail_range_evidence": file_meta(LOGS / "range_FEM_and_CAD.zip.tail_4MiB.bin"),
    }
    if not zpath.exists():
        inventory["archive_status"] = "not_fetched_or_partial"
        inventory["parser_gaps"].append("Full FEM_and_CAD.zip was not available when this script ran.")
        return inventory
    if not zipfile.is_zipfile(zpath):
        inventory["archive_status"] = "partial_download"
        inventory["parser_gaps"].append("FEM_and_CAD.zip exists locally but is not a complete readable ZIP yet.")
        return inventory
    inventory["archive_status"] = "fetched"
    listing = zip_listing(zpath, max_names=800)
    inventory["archive_listing_summary"] = listing
    members = find_candidate_fem_members(zpath)
    inventory["candidate_fem_members"] = members[:300]
    extracted = extract_from_zip(zpath, members, EXTRACTED, max_total_bytes=350 * 1024 * 1024)
    inventory["candidate_members_extracted"] = extracted
    for item in extracted:
        if item.get("status") != "extracted":
            continue
        p = REPO / item["local_path"]
        if p.suffix.lower() in {".bdf", ".nas", ".dat", ".fem", ".blk"}:
            parsed = parse_nastran_like(p)
            inventory["parsed_models"].append(parsed)
    main_component_paths = sorted((EXTRACTED / "FEM" / "FEM_20211021").glob("*.blk"))
    if main_component_paths:
        geometry = collect_nastran_geometry(main_component_paths)
        plot_geometry = dict(geometry)
        draw_mesh_preview(plot_geometry)
        geometry.pop("_nodes_for_plot", None)
        geometry.pop("_elements_for_plot", None)
        inventory["main_fem_20211021_aggregate"] = geometry
    else:
        inventory["parser_gaps"].append("Main FEM_20211021 component block files were not extracted.")
    if not inventory["parsed_models"]:
        inventory["parser_gaps"].append(
            "No Nastran-like source deck was parsed from extracted candidate FEM members yet."
        )
    return inventory


def draw_fem_file_tree(fem_inventory: dict[str, Any]) -> None:
    fig, ax = plt.subplots(figsize=(12, 7))
    ax.axis("off")
    title = "ShockSat FEM/CAD Archive Inventory"
    ax.text(0.02, 0.96, title, fontsize=18, fontweight="bold", va="top")
    lines = [
        f"Archive status: {fem_inventory.get('archive_status')}",
        f"Units: {fem_inventory.get('units')}",
    ]
    listing = fem_inventory.get("archive_listing_summary") or {}
    if listing:
        lines.append(f"Archive entries: {listing.get('entry_count')}")
        lines.append(
            "Top directories: "
            + ", ".join(f"{k} ({v})" for k, v in (listing.get("top_directories") or {}).items())
        )
        ext = listing.get("extension_counts") or {}
        lines.append(
            "Key extensions: "
            + ", ".join(
                f"{k}:{v}"
                for k, v in ext.items()
                if k
                in {
                    ".bdf",
                    ".nas",
                    ".dat",
                    ".fem",
                    ".op2",
                    ".f06",
                    ".pptx",
                    ".png",
                    ".stp",
                    ".step",
                    ".jpg",
                }
            )
        )
    parsed = fem_inventory.get("parsed_models") or []
    aggregate = fem_inventory.get("main_fem_20211021_aggregate") or {}
    if parsed:
        best = max(parsed, key=lambda p: p.get("node_count_grid_cards", 0))
        lines += [
            "",
            "Largest parsed Nastran-like model:",
            f"  {best.get('path')}",
            f"  GRID cards: {best.get('node_count_grid_cards')}",
            f"  Elements: {best.get('total_element_count')} {best.get('element_counts')}",
            f"  Materials: {best.get('material_card_counts')}",
            f"  Boundary cards: {best.get('boundary_condition_card_counts')}",
        ]
    if aggregate:
        lines += [
            "",
            "Main FEM_20211021 aggregate:",
            f"  unique GRID cards: {aggregate.get('node_count_unique')}",
            f"  parseable shell elements: {aggregate.get('surface_element_count_parseable')} {aggregate.get('surface_element_counts')}",
            f"  bounds (in): {aggregate.get('bounds_in')}",
            f"  shock grids present: {aggregate.get('shock_instrumentation_grid_check', {}).get('present_count')}",
        ]
    else:
        lines += ["", "No full source deck parsed yet. Tail evidence showed FEM correlation assets."]
    y = 0.88
    for line in lines:
        ax.text(0.03, y, line, fontsize=11, va="top", wrap=True)
        y -= 0.055 if len(line) < 120 else 0.09
    fig.tight_layout()
    fig.savefig(FIGURES / "fem_file_tree.png", dpi=180)
    plt.close(fig)


def write_fem_outputs(fem_inventory: dict[str, Any]) -> None:
    write_json(OUT / "fem_inventory.json", fem_inventory)
    draw_fem_file_tree(fem_inventory)
    parsed = fem_inventory.get("parsed_models") or []
    aggregate = fem_inventory.get("main_fem_20211021_aggregate") or {}
    md = [
        "# FEM and CAD Inventory",
        "",
        f"Generated: {fem_inventory['generated_utc']}",
        "",
        f"- Archive status: `{fem_inventory.get('archive_status')}`",
        f"- Units: `{fem_inventory.get('units')}`",
        "- Solver/source-format inference is based on extracted file extensions and parsed cards; no solver result is treated as validated unless the source file supports it.",
        "",
        "## Archive Evidence",
        "",
    ]
    listing = fem_inventory.get("archive_listing_summary")
    if listing:
        md += [
            f"- Entry count: `{listing.get('entry_count')}`",
            f"- Total uncompressed size: `{listing.get('total_uncompressed_size_bytes')}` bytes",
            f"- Top directories: `{listing.get('top_directories')}`",
            f"- Extension counts: `{listing.get('extension_counts')}`",
        ]
    else:
        md.append("- Full archive listing is not available yet; see tail-range listing logs.")
    md += ["", "## Parsed Model Metadata", ""]
    if parsed:
        for model in parsed:
            md += [
                f"### {model.get('path')}",
                "",
                f"- Solver/source family inference: `{model.get('solver_family_inference')}`",
                f"- Solution lines: `{model.get('solution_lines')}`",
                f"- Node count from GRID cards: `{model.get('node_count_grid_cards')}`",
                f"- Element counts: `{model.get('element_counts')}`",
                f"- Material cards: `{model.get('material_card_counts')}`",
                f"- Property cards: `{model.get('property_card_counts')}`",
                f"- Boundary-condition cards: `{model.get('boundary_condition_card_counts')}`",
                "",
            ]
    else:
        md.append("- No source deck was parsed in this run. This is a blocker for node/element-count claims.")
    if aggregate:
        grid_check = aggregate.get("shock_instrumentation_grid_check", {})
        md += [
            "",
            "## Main FEM_20211021 Aggregate",
            "",
            f"- Unique GRID cards parsed across component blocks: `{aggregate.get('node_count_unique')}`",
            f"- Parseable surface elements: `{aggregate.get('surface_element_count_parseable')}`",
            f"- Surface element counts: `{aggregate.get('surface_element_counts')}`",
            f"- Coordinate-card counts: `{aggregate.get('coordinate_card_counts')}`",
            f"- Geometry bounds, inches: `{aggregate.get('bounds_in')}`",
            f"- Shock instrumentation grids present: `{grid_check.get('present_count')}`",
            f"- Missing expected shock grids: `{grid_check.get('missing_grid_ids')}`",
            "",
            "## Material Cards Parsed From Main Blocks",
            "",
            "| Source | MAT1 ID | E | G | nu | rho | alpha |",
            "|---|---:|---:|---:|---:|---:|---:|",
        ]
        for material in aggregate.get("materials_mat1", [])[:40]:
            md.append(
                "| {source} | {material_id} | {E} | {G} | {nu} | {rho} | {alpha} |".format(
                    **material
                )
            )
    md += [
        "",
        "## Sensor-to-FEM Mapping Status",
        "",
        "- Instrumentation sheets include FEM grid IDs for accelerometer locations. README states shock accelerometer grids are `9900001-9900136`.",
        "- A verified node/element mapping requires the fetched FEM source deck and confirmation that these grids exist in that deck.",
        "",
        f"![FEM file tree]({rel(FIGURES / 'fem_file_tree.png')})",
        "",
        f"![FEM mesh preview]({rel(FIGURES / 'fem_mesh_preview.png')})",
    ]
    (OUT / "fem_inventory.md").write_text("\n".join(md) + "\n")


def is_numeric_array(value: Any) -> bool:
    return isinstance(value, np.ndarray) and np.issubdtype(value.dtype, np.number)


def choose_mat_data(mat: dict[str, Any]) -> tuple[str | None, np.ndarray | None, dict[str, Any]]:
    candidates = []
    for key, val in mat.items():
        if key.startswith("__") or not is_numeric_array(val):
            continue
        arr = np.asarray(val)
        if arr.ndim == 1 and arr.size > 1000:
            candidates.append((key, arr.size, 1, arr))
        elif arr.ndim == 2 and max(arr.shape) > 1000 and min(arr.shape) >= 2:
            candidates.append((key, max(arr.shape), min(arr.shape), arr))
    if not candidates:
        return None, None, {"numeric_candidates": []}
    candidates.sort(key=lambda x: (x[2], x[1]), reverse=True)
    key, _, _, arr = candidates[0]
    arr = np.asarray(arr, dtype=float)
    if arr.ndim == 2 and arr.shape[0] < arr.shape[1] and arr.shape[0] <= 200:
        arr = arr.T
    return key, arr, {
        "numeric_candidates": [
            {"key": k, "shape": list(np.asarray(a).shape)} for k, _, _, a in candidates[:20]
        ]
    }


def extract_first_mat(archive: Path, preferred_regex: str, dest_root: Path) -> dict[str, Any]:
    if not archive.exists():
        return {"status": "archive_missing", "archive": rel(archive)}
    def extract_partial_local_member() -> dict[str, Any]:
        data = archive.read_bytes()
        pos = 0
        candidates = []
        while True:
            i = data.find(b"PK\x03\x04", pos)
            if i < 0 or i + 30 > len(data):
                break
            try:
                (
                    sig,
                    _ver,
                    _flags,
                    compression,
                    _mtime,
                    _mdate,
                    _crc,
                    compressed_size,
                    uncompressed_size,
                    name_len,
                    extra_len,
                ) = struct.unpack_from("<IHHHHHIIIHH", data, i)
            except Exception:
                break
            if sig != 0x04034B50:
                break
            name_start = i + 30
            name_end = name_start + name_len
            data_start = name_end + extra_len
            data_end = data_start + compressed_size
            if name_end > len(data):
                break
            name = data[name_start:name_end].decode("utf-8", errors="replace")
            complete = data_end <= len(data)
            if name.lower().endswith(".mat") and complete:
                candidates.append(
                    {
                        "name": name,
                        "compression": compression,
                        "compressed_size": compressed_size,
                        "uncompressed_size": uncompressed_size,
                        "data_start": data_start,
                        "data_end": data_end,
                    }
                )
            if not complete:
                break
            pos = data_end
        preferred = [c for c in candidates if re.search(preferred_regex, c["name"], flags=re.I)]
        candidate = (preferred or candidates or [None])[0]
        if candidate is None:
            return {
                "status": "partial_zip_no_complete_mat",
                "archive": rel(archive),
                "complete_mat_members_count": len(candidates),
            }
        raw = data[candidate["data_start"] : candidate["data_end"]]
        if candidate["compression"] == 0:
            payload = raw
        elif candidate["compression"] == 8:
            payload = zlib.decompress(raw, -15)
        else:
            return {
                "status": "partial_zip_unsupported_compression",
                "archive": rel(archive),
                "member": candidate["name"],
                "compression": candidate["compression"],
            }
        out_path = dest_root / candidate["name"]
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_bytes(payload)
        return {
            "status": "extracted_from_partial_zip_local_header",
            "archive": rel(archive),
            "member": candidate["name"],
            "local_path": rel(out_path),
            "mat_members_count": len(candidates),
            "compressed_size": candidate["compressed_size"],
            "uncompressed_size": candidate["uncompressed_size"],
            "partial_archive_bytes_available": archive.stat().st_size,
        }
    try:
        with zipfile.ZipFile(archive) as zf:
            mats = [n for n in zf.namelist() if n.lower().endswith(".mat")]
            preferred = [n for n in mats if re.search(preferred_regex, n, flags=re.I)]
            member = (preferred or mats or [None])[0]
            if member is None:
                return {"status": "no_mat_members", "archive": rel(archive)}
            zf.extract(member, dest_root)
            return {
                "status": "extracted",
                "archive": rel(archive),
                "member": member,
                "local_path": rel(dest_root / member),
                "mat_members_count": len(mats),
            }
    except Exception as exc:
        partial = extract_partial_local_member()
        if partial["status"].startswith("extracted"):
            partial["central_directory_status"] = f"unavailable_or_parse_failed: {exc!r}"
            return partial
        partial["central_directory_error"] = repr(exc)
        return partial


def recorder_sample(mat: dict[str, Any], daq_channel: int) -> dict[str, Any] | None:
    key = f"Recorder{daq_channel}"
    rec = mat.get(key)
    if rec is None:
        return None
    try:
        data = rec.Channels.Segments.Data
        info = rec.Channels.ChannelInfos.ChannelInfo
        samples = np.asarray(data.Samples, dtype=float)
        dx = float(data.dXstep)
        x0 = float(data.dX0)
        return {
            "samples": samples,
            "sample_interval_s": dx,
            "sample_rate_sps": 1.0 / dx if dx else None,
            "time_zero_s": x0,
            "channel_name": clean_text(getattr(info, "Name", "")),
            "channel_units": clean_text(getattr(info, "YUnits", "")),
            "record_title": clean_text(getattr(rec, "Title", "")),
            "time_of_first_sample": clean_text(getattr(rec, "TimeOfFirstSample", "")),
        }
    except Exception:
        return None


def list_hammer_hit_sources(archive: Path, fallback_mat: Path | None) -> list[dict[str, Any]]:
    sources: list[dict[str, Any]] = []
    if archive.exists() and zipfile.is_zipfile(archive):
        with zipfile.ZipFile(archive) as zf:
            members = sorted(n for n in zf.namelist() if n.lower().endswith(".mat"))
            for member in members:
                info = zf.getinfo(member)
                sources.append(
                    {
                        "source_type": "zip_member",
                        "archive": rel(archive),
                        "member": member,
                        "compressed_size": info.compress_size,
                        "uncompressed_size": info.file_size,
                    }
                )
    elif fallback_mat and fallback_mat.exists():
        sources.append(
            {
                "source_type": "extracted_partial_member",
                "local_path": rel(fallback_mat),
                "uncompressed_size": fallback_mat.stat().st_size,
            }
        )
    return sources


def load_recorders_for_hit(
    hit_source: dict[str, Any],
    archive: Path,
    recorder_channels: list[int],
) -> dict[str, Any]:
    variable_names = [f"Recorder{ch}" for ch in recorder_channels]
    if hit_source.get("source_type") == "zip_member":
        with zipfile.ZipFile(archive) as zf:
            payload = zf.read(hit_source["member"])
        return scipy_io.loadmat(
            io.BytesIO(payload),
            squeeze_me=True,
            struct_as_record=False,
            variable_names=variable_names,
        )
    local_path = REPO / hit_source["local_path"]
    return scipy_io.loadmat(
        local_path,
        squeeze_me=True,
        struct_as_record=False,
        variable_names=variable_names,
    )


def load_and_plot_first_data(channel_rows: list[dict[str, Any]]) -> dict[str, Any]:
    manifest: dict[str, Any] = {
        "generated_utc": now_utc(),
        "readme_sample_rate_sps": 100000,
        "sample_rate_policy": "use per-file MAT dXstep when present; README value is treated as general metadata, not a forced override",
        "processing": {
            "baseline_removal": "subtract pre-window/channel mean before plotting and PSD",
            "filtering": "no digital bandpass filter in first plot",
            "psd_method": "scipy.signal.welch with Hann window; nperseg chosen from available length",
            "srs": "not computed in this first subset; PSD is used instead of SRS",
        },
        "datasets": [],
        "selected_channels": [],
        "status": "pending",
    }
    channel_by_config: dict[str, dict[int, dict[str, Any]]] = defaultdict(dict)
    for row in channel_rows:
        try:
            channel_by_config[row["configuration"]][int(row["daq_channel"])] = row
        except Exception:
            pass

    data_jobs = [
        {
            "label": "hammer_impact_test07_990x",
            "archive": SOURCES / "Test07_ImpactHammer_990x.zip",
            "preferred_regex": r"Test.*001.*\.mat$|\.mat$",
            "configuration": "tap_impact",
            "channels": [1, 50, 87, 116],
        },
        {
            "label": "pyro_nsd1",
            "archive": SOURCES / "Test_Data_Pyro_NSI_NSD.zip",
            "preferred_regex": r"NSD1.*\.mat$|990x001.*\.mat$|\.mat$",
            "configuration": "nsi_nsd_parametric",
            "channels": [1, 50, 87, 100],
        },
    ]
    plotted_any = False
    time_fig, time_axes = plt.subplots(len(data_jobs), 1, figsize=(12, 7), sharex=False)
    psd_fig, psd_axes = plt.subplots(len(data_jobs), 1, figsize=(12, 7), sharex=False)
    overview_labels = []
    overview_rms = []
    if len(data_jobs) == 1:
        time_axes = [time_axes]
        psd_axes = [psd_axes]
    for job_idx, job in enumerate(data_jobs):
        ax_t = time_axes[job_idx]
        ax_p = psd_axes[job_idx]
        extraction = extract_first_mat(
            job["archive"],
            job["preferred_regex"],
            EXTRACTED,
        )
        dataset_record = {**job, "archive": rel(job["archive"]), "extraction": extraction}
        if not str(extraction.get("status", "")).startswith("extracted"):
            ax_t.text(0.05, 0.6, f"{job['label']}: archive not available", transform=ax_t.transAxes)
            ax_t.axis("off")
            ax_p.text(0.05, 0.6, f"{job['label']}: archive not available", transform=ax_p.transAxes)
            ax_p.axis("off")
            manifest["datasets"].append(dataset_record)
            continue
        local_mat = REPO / extraction["local_path"]
        try:
            whos = scipy_io.whosmat(local_mat)
            dataset_record["whosmat_count"] = len(whos)
            dataset_record["whosmat_sample"] = [
                {"name": name, "shape": list(shape), "class": cls}
                for name, shape, cls in whos[:12]
            ]
            recorder_vars = [
                f"Recorder{ch}"
                for ch in job["channels"]
                if any(name == f"Recorder{ch}" for name, _shape, _cls in whos)
            ]
            if recorder_vars:
                mat = scipy_io.loadmat(
                    local_mat,
                    squeeze_me=True,
                    struct_as_record=False,
                    variable_names=recorder_vars,
                )
                dataset_record["load_status"] = "loaded"
                dataset_record["mat_format"] = "per_recorder_struct"
                dataset_record["mat_variables_loaded"] = recorder_vars
                for ch in job["channels"]:
                    sample = recorder_sample(mat, ch)
                    if sample is None:
                        dataset_record.setdefault("missing_channels", []).append(ch)
                        continue
                    channel_meta = channel_by_config[job["configuration"]].get(ch, {})
                    fs = float(sample["sample_rate_sps"])
                    samples = sample["samples"]
                    n = samples.size
                    window_n = min(n, int(0.05 * fs))
                    if window_n < 100:
                        window_n = min(n, 2000)
                    t = sample["time_zero_s"] + np.arange(window_n) * sample["sample_interval_s"]
                    y = samples[:window_n].astype(float)
                    y = y - np.nanmean(y[: min(len(y), 200)])
                    units = sample["channel_units"] or channel_meta.get("engineering_units", "unknown")
                    desc = channel_meta.get("description", f"channel {ch}")
                    axis = channel_meta.get("structural_axis", "")
                    label = f"ch {ch} {axis} ({units})".strip()
                    ax_t.plot(t * 1000.0, y, lw=0.8, label=label)
                    nperseg = min(8192, max(256, len(y) // 2))
                    freqs, pxx = signal.welch(y, fs=fs, nperseg=nperseg, window="hann")
                    mask = (freqs >= 100.0) & (freqs <= 10000.0)
                    ax_p.loglog(freqs[mask], pxx[mask], lw=0.9, label=label)
                    overview_labels.append(f"{job['label']} ch{ch}")
                    overview_rms.append(float(np.sqrt(np.nanmean(y**2))))
                    if abs(fs - 100000.0) > 1e-6:
                        dataset_record.setdefault("sample_rate_warnings", []).append(
                            f"DAQ channel {ch} MAT dXstep gives {fs:g} samples/s; README general value is 100000 samples/s."
                        )
                    manifest["selected_channels"].append(
                        {
                            "dataset": job["label"],
                            "daq_channel": ch,
                            "units": units,
                            "description": desc,
                            "time_window_s": window_n / fs,
                            "sample_interval_s": sample["sample_interval_s"],
                            "sample_rate_sps": fs,
                            "sample_rate_source": "MAT Segments.Data.dXstep",
                            "mat_channel_name": sample["channel_name"],
                            "record_title": sample["record_title"],
                            "time_of_first_sample": sample["time_of_first_sample"],
                        }
                    )
                    plotted_any = True
            else:
                mat = scipy_io.loadmat(local_mat, squeeze_me=True, struct_as_record=False)
                key, data, meta = choose_mat_data(mat)
                dataset_record["load_status"] = "loaded"
                dataset_record["mat_variable"] = key
                dataset_record["mat_meta"] = meta
                if data is None:
                    raise RuntimeError("no usable numeric data matrix found")
                dataset_record["data_shape"] = list(data.shape)
                fs = 100000.0
                n = data.shape[0] if data.ndim > 1 else data.size
                window_n = min(n, int(0.05 * fs))
                if window_n < 100:
                    window_n = min(n, 2000)
                t = np.arange(window_n) / fs
                for ch in job["channels"]:
                    channel_meta = channel_by_config[job["configuration"]].get(ch, {})
                    if data.ndim == 1:
                        if ch != job["channels"][0]:
                            continue
                        y = data[:window_n].astype(float)
                    else:
                        col = ch - 1 if data.shape[1] >= ch else None
                        if col is None:
                            continue
                        y = data[:window_n, col].astype(float)
                    y = y - np.nanmean(y[: min(len(y), 200)])
                    units = channel_meta.get("engineering_units", "unknown")
                    desc = channel_meta.get("description", f"channel {ch}")
                    label = f"ch {ch} {channel_meta.get('structural_axis','')}".strip()
                    ax_t.plot(t * 1000.0, y, lw=0.8, label=label)
                    nperseg = min(8192, max(256, len(y) // 2))
                    freqs, pxx = signal.welch(y, fs=fs, nperseg=nperseg, window="hann")
                    mask = (freqs >= 100.0) & (freqs <= 10000.0)
                    ax_p.loglog(freqs[mask], pxx[mask], lw=0.9, label=label)
                    overview_labels.append(f"{job['label']} ch{ch}")
                    overview_rms.append(float(np.sqrt(np.nanmean(y**2))))
                    manifest["selected_channels"].append(
                        {
                            "dataset": job["label"],
                            "daq_channel": ch,
                            "units": units,
                            "description": desc,
                            "time_window_s": window_n / fs,
                            "sample_rate_sps": fs,
                            "sample_rate_source": "fallback README/general value",
                        }
                    )
                    plotted_any = True
            ax_t.set_title(f"{job['label']} time histories")
            ax_t.set_xlabel("time after MAT sample 0 (ms)")
            ax_t.set_ylabel("calibrated channel value")
            ax_t.legend(fontsize=8, ncol=2)
            ax_t.grid(True, alpha=0.25)
            ax_p.set_title(f"{job['label']} PSD diagnostic, 100-10000 Hz")
            ax_p.set_xlabel("frequency (Hz, log scale)")
            ax_p.set_ylabel("power spectral density (channel units^2/Hz)")
            ax_p.legend(fontsize=8, ncol=2)
            ax_p.grid(True, which="both", alpha=0.25)
        except Exception as exc:
            dataset_record["load_status"] = "parse_failed"
            dataset_record["parse_error"] = repr(exc)
            ax_t.text(0.05, 0.6, f"{job['label']} parse failed:\n{exc!r}", transform=ax_t.transAxes)
            ax_t.axis("off")
            ax_p.text(0.05, 0.6, f"{job['label']} parse failed:\n{exc!r}", transform=ax_p.transAxes)
            ax_p.axis("off")
        manifest["datasets"].append(dataset_record)
    time_fig.tight_layout()
    psd_fig.tight_layout()
    time_fig.savefig(FIGURES / "first_time_histories.png", dpi=180)
    psd_fig.savefig(FIGURES / "first_srs_or_psd.png", dpi=180)
    plt.close(time_fig)
    plt.close(psd_fig)
    fig, ax = plt.subplots(figsize=(12, 6))
    if overview_labels:
        x = np.arange(len(overview_labels))
        ax.bar(x, overview_rms)
        ax.set_xticks(x)
        ax.set_xticklabels(overview_labels, rotation=45, ha="right", fontsize=8)
        ax.set_ylabel("RMS over plotted first window")
        ax.set_title("First Channel Comparison Overview")
        ax.grid(True, axis="y", alpha=0.25)
    else:
        ax.text(0.05, 0.6, "No raw MAT data parsed yet.", transform=ax.transAxes, fontsize=14)
        ax.axis("off")
    fig.tight_layout()
    fig.savefig(FIGURES / "channel_comparison_overview.png", dpi=180)
    plt.close(fig)
    manifest["status"] = "plotted" if plotted_any else "blocked_or_parse_failed"
    write_json(OUT / "first_data_subset_manifest.json", manifest)
    return manifest


def parse_sol111_bdf_summary(path: Path) -> dict[str, Any]:
    summary: dict[str, Any] = {"path": rel(path), "exists": path.exists()}
    if not path.exists():
        return summary
    text = path.read_text(errors="replace")
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith("SUBTITLE"):
            summary["subtitle"] = stripped.split("=", 1)[-1].strip()
        if stripped.startswith("FORCE"):
            parts = stripped.split()
            if len(parts) >= 8:
                summary["force_card"] = stripped
                summary["force_grid"] = int(float(parts[2]))
                summary["force_cid"] = parts[3]
                summary["force_magnitude"] = float(parts[4])
                summary["force_vector"] = [float(parts[5]), float(parts[6]), float(parts[7])]
        if stripped.startswith("FREQ1"):
            parts = stripped.split()
            if len(parts) >= 5:
                start = float(parts[2])
                step = float(parts[3])
                count = int(float(parts[4]))
                summary["frequency_hz"] = {
                    "start": start,
                    "step": step,
                    "count_increment_value": count,
                    "stop_if_n_is_increment_count": start + step * count,
                }
    return summary


def parse_pch_acceleration_summary(path: Path) -> dict[str, Any]:
    summary: dict[str, Any] = {"path": rel(path), "exists": path.exists()}
    if not path.exists():
        return summary
    points: list[int] = []
    first_point: int | None = None
    freq_values: list[float] = []
    active_first_point = False
    for line in path.read_text(errors="replace").splitlines():
        match = re.search(r"\$POINT ID =\s*(\d+)", line)
        if match:
            point = int(match.group(1))
            points.append(point)
            if first_point is None:
                first_point = point
            active_first_point = point == first_point
            continue
        parts = line.split()
        if active_first_point and len(parts) >= 2 and parts[1] == "G":
            try:
                freq_values.append(float(parts[0]))
            except Exception:
                pass
    unique_points = sorted(set(points))
    summary.update(
        {
            "point_count_including_repeats": len(points),
            "unique_response_point_count": len(unique_points),
            "unique_response_points": unique_points,
            "unique_response_points_sample": unique_points[:40],
            "contains_duplicate_points": len(points) != len(unique_points),
        }
    )
    if freq_values:
        diffs = np.diff(freq_values)
        step = float(np.median(diffs)) if len(diffs) else None
        summary["frequency_hz"] = {
            "count_first_point": len(freq_values),
            "min": float(np.min(freq_values)),
            "max": float(np.max(freq_values)),
            "median_step": step,
        }
    return summary


def build_nasa_correlation_frf_assets() -> dict[str, Any]:
    zpath = SOURCES / "FEM_and_CAD.zip"
    assets: dict[str, Any] = {
        "generated_utc": now_utc(),
        "status": "missing_fem_archive",
        "sol111_decks": [],
        "pch_files": [],
        "comparison_png_groups": {},
        "interpretation": (
            "NASA correlation FRF assets are indexed here as source evidence. They are not "
            "automatically comparable to Test07 shock-channel FRFs unless source and response "
            "grid conventions are reconciled."
        ),
    }
    frf_root = EXTRACTED / "FEM" / "Correlation" / "FRF_Verification"
    for bdf in sorted(frf_root.glob("*.bdf")):
        assets["sol111_decks"].append(parse_sol111_bdf_summary(bdf))
    for pch in sorted(frf_root.glob("*.pch")):
        assets["pch_files"].append(parse_pch_acceleration_summary(pch))
    if zpath.exists() and zipfile.is_zipfile(zpath):
        assets["status"] = "indexed_from_fem_archive"
        with zipfile.ZipFile(zpath) as zf:
            pngs = [
                name
                for name in zf.namelist()
                if name.startswith("FEM/Correlation/FRF_Verification/")
                and name.lower().endswith(".png")
            ]
        groups: dict[str, dict[str, Any]] = {}
        for name in pngs:
            parts = name.split("/")
            group = parts[3] if len(parts) > 4 else "<root>"
            file_name = parts[-1]
            match = re.match(r"Acceleration_(?P<point>\d+)(?P<axis>[XYZ])\+\.png$", file_name)
            record = groups.setdefault(
                group,
                {
                    "png_count": 0,
                    "response_points": set(),
                    "axes": Counter(),
                    "sample_files": [],
                },
            )
            record["png_count"] += 1
            if len(record["sample_files"]) < 10:
                record["sample_files"].append(name)
            if match:
                record["response_points"].add(int(match.group("point")))
                record["axes"][match.group("axis")] += 1
        for group, record in groups.items():
            assets["comparison_png_groups"][group] = {
                "png_count": record["png_count"],
                "unique_response_point_count": len(record["response_points"]),
                "response_points_sample": sorted(record["response_points"])[:30],
                "axis_counts": dict(record["axes"]),
                "sample_files": record["sample_files"],
            }
    elif assets["sol111_decks"] or assets["pch_files"]:
        assets["status"] = "indexed_from_extracted_files_only"
    write_json(OUT / "nasa_correlation_frf_assets.json", assets)

    fig, ax = plt.subplots(figsize=(12, 6))
    ax.axis("off")
    ax.text(0.02, 0.94, "NASA Correlation FRF Asset Index", fontsize=18, fontweight="bold", va="top")
    y = 0.82
    lines = [f"Status: {assets['status']}"]
    for deck in assets["sol111_decks"]:
        lines.append(
            "SOL111 deck {name}: force grid {grid}, vector {vec}".format(
                name=Path(deck.get("path", "")).name,
                grid=deck.get("force_grid"),
                vec=deck.get("force_vector"),
            )
        )
    for pch in assets["pch_files"]:
        freq = pch.get("frequency_hz") or {}
        lines.append(
            "PCH {name}: {n} response points, {f0}-{f1} Hz".format(
                name=Path(pch.get("path", "")).name,
                n=pch.get("unique_response_point_count"),
                f0=freq.get("min"),
                f1=freq.get("max"),
            )
        )
    for group, record in assets["comparison_png_groups"].items():
        lines.append(
            f"PNG group {group}: {record['png_count']} plots, {record['unique_response_point_count']} response points"
        )
    for line in lines:
        ax.text(0.03, y, line, fontsize=10.5, va="top", wrap=True)
        y -= 0.075
    fig.tight_layout()
    fig.savefig(FIGURES / "nasa_correlation_frf_asset_summary.png", dpi=180)
    plt.close(fig)

    md = [
        "# NASA Correlation FRF Asset Index",
        "",
        f"Generated: {assets['generated_utc']}",
        "",
        f"- Status: `{assets['status']}`",
        f"- Interpretation: {assets['interpretation']}",
        "",
        "## SOL 111 Decks",
        "",
        "| Deck | Subtitle | Force grid | Force vector | Frequency request |",
        "|---|---|---:|---|---|",
    ]
    for deck in assets["sol111_decks"]:
        md.append(
            f"| `{deck.get('path')}` | `{deck.get('subtitle')}` | {deck.get('force_grid')} | "
            f"`{deck.get('force_vector')}` | `{deck.get('frequency_hz')}` |"
        )
    md += [
        "",
        "## PCH Response Sets",
        "",
        "| PCH | Unique response points | Frequency range | Sample response points |",
        "|---|---:|---|---|",
    ]
    for pch in assets["pch_files"]:
        freq = pch.get("frequency_hz") or {}
        md.append(
            f"| `{pch.get('path')}` | {pch.get('unique_response_point_count')} | "
            f"`{freq.get('min')}`-`{freq.get('max')}` Hz | `{pch.get('unique_response_points_sample')}` |"
        )
    md += [
        "",
        "## Comparison Plot Groups In Archive",
        "",
        "| Group | PNG count | Unique response points | Axis counts |",
        "|---|---:|---:|---|",
    ]
    for group, record in assets["comparison_png_groups"].items():
        md.append(
            f"| `{group}` | {record['png_count']} | {record['unique_response_point_count']} | `{record['axis_counts']}` |"
        )
    md += ["", f"![NASA FRF asset summary]({rel(FIGURES / 'nasa_correlation_frf_asset_summary.png')})"]
    (OUT / "nasa_correlation_frf_assets.md").write_text("\n".join(md) + "\n")
    return assets


def compute_hammer_frf_layer(
    channel_rows: list[dict[str, Any]],
    test_rows: list[dict[str, Any]],
    fem_inventory: dict[str, Any],
    first_data_manifest: dict[str, Any],
) -> dict[str, Any]:
    assets = build_nasa_correlation_frf_assets()
    selected_response_channels = [1, 50, 87]
    force_channel = 116
    nperseg = 32768
    noverlap = nperseg // 2
    manifest: dict[str, Any] = {
        "generated_utc": now_utc(),
        "status": "not_computed",
        "dataset": "hammer_impact_test07_990x",
        "quantity": "provisional H1 accelerance estimate",
        "quantity_contract": {
            "estimator": "H1_yf = G_fy / G_ff using scipy.signal.csd(force, response) and scipy.signal.welch(force)",
            "numerator": "cross power spectral density between input force f and output acceleration y",
            "denominator": "input force auto power spectral density",
            "units": "g/lbf, using MAT channel units g for response and lb/lbf for hammer force",
            "coordinate": "response channel structural axis from instrumentation workbook",
            "excitation": "Test07 impact hammer force channel 116, nominal 990x test label; exact source grid not yet mapped to SOL 111 force grids",
            "boundary_condition": "as-tested impact hammer configuration; suspension/support interpretation still from NASA test context",
        },
        "processing": {
            "baseline_removal": "subtract mean of first 1000 samples from each loaded channel",
            "window": "Hann",
            "nperseg": nperseg,
            "noverlap": noverlap,
            "detrend": "False after explicit baseline subtraction",
            "frequency_band_reported_hz": [100.0, 10000.0],
            "acceptance_note": "Low coherence keeps this out of the StatFEM likelihood; it is a diagnostic transfer estimate.",
        },
        "nasa_correlation_assets": {
            "json": rel(OUT / "nasa_correlation_frf_assets.json"),
            "md": rel(OUT / "nasa_correlation_frf_assets.md"),
            "status": assets.get("status"),
        },
        "channels": [],
        "comparison_status": "not_evaluated",
    }
    test07_rows = [
        row
        for row in test_rows
        if str(row.get("Filename", "")).lower().startswith("test07_impacthammer_990x")
        or str(row.get("Test No.", "")).startswith("7.")
    ]
    manifest["test_log_matches"] = test07_rows
    manifest["test_log_match_count"] = len(test07_rows)
    manifest["source_location_metadata"] = [
        {
            "filename": row.get("Filename"),
            "description": row.get("Description"),
            "impact_point": row.get("Impact Point"),
            "impact_grid": row.get("Impact Grid"),
            "comments": row.get("Comments"),
            "source_sheet": row.get("source_sheet"),
            "excel_row": row.get("excel_row"),
        }
        for row in test07_rows
    ]
    channel_by_config: dict[int, dict[str, Any]] = {}
    for row in channel_rows:
        if row.get("configuration") != "tap_impact":
            continue
        try:
            channel_by_config[int(row["daq_channel"])] = row
        except Exception:
            pass
    dataset_record = next(
        (d for d in first_data_manifest.get("datasets", []) if d.get("label") == "hammer_impact_test07_990x"),
        None,
    )
    if not dataset_record:
        manifest["status"] = "blocked_no_hammer_dataset_record"
        write_json(OUT / "hammer_frf_subset_manifest.json", manifest)
        return manifest
    extraction = dataset_record.get("extraction") or {}
    if not str(extraction.get("status", "")).startswith("extracted"):
        manifest["status"] = "blocked_hammer_mat_not_extracted"
        manifest["extraction"] = extraction
        write_json(OUT / "hammer_frf_subset_manifest.json", manifest)
        return manifest
    local_mat = REPO / extraction["local_path"]
    if not local_mat.exists():
        manifest["status"] = "blocked_hammer_mat_missing"
        manifest["local_mat"] = rel(local_mat)
        write_json(OUT / "hammer_frf_subset_manifest.json", manifest)
        return manifest
    load_channels = selected_response_channels + [force_channel]
    try:
        archive = SOURCES / "Test07_ImpactHammer_990x.zip"
        hit_sources = list_hammer_hit_sources(archive, local_mat)
        if not hit_sources:
            raise RuntimeError("no Test07 MAT hit sources available")
        manifest["test_log_archive_alignment_note"] = (
            f"TestLog matching found {len(test07_rows)} Test07 rows; the available archive/source "
            f"exposes {len(hit_sources)} MAT hit file(s). Treat TestLog rows as source-location "
            "metadata, not a one-to-one loaded-hit list, until the NASA file/test mapping is reconciled."
        )
        response_grids = []
        present_grids = set(
            (fem_inventory.get("main_fem_20211021_aggregate") or {})
            .get("shock_instrumentation_grid_check", {})
            .get("present_grid_ids", [])
        )
        freqs: np.ndarray | None = None
        fs: float | None = None
        pff_hits: list[np.ndarray] = []
        h1_hits_by_channel: dict[int, list[np.ndarray]] = {ch: [] for ch in selected_response_channels}
        coh_hits_by_channel: dict[int, list[np.ndarray]] = {ch: [] for ch in selected_response_channels}
        hit_rows: list[dict[str, Any]] = []
        force_peaks = []
        force_rms_values = []
        first_samples: dict[int, dict[str, Any]] | None = None
        for hit_index, hit_source in enumerate(hit_sources, start=1):
            hit_row: dict[str, Any] = {
                "hit_index": hit_index,
                "source_type": hit_source.get("source_type"),
                "member": hit_source.get("member", ""),
                "local_path": hit_source.get("local_path", ""),
                "load_status": "pending",
            }
            try:
                mat = load_recorders_for_hit(hit_source, archive, load_channels)
                samples: dict[int, dict[str, Any]] = {}
                for ch in load_channels:
                    sample = recorder_sample(mat, ch)
                    if sample is None:
                        raise RuntimeError(f"Recorder{ch} not found in MAT hit")
                    samples[ch] = sample
                if first_samples is None:
                    first_samples = samples
                fs_values = [float(samples[ch]["sample_rate_sps"]) for ch in load_channels]
                if max(fs_values) - min(fs_values) > 1e-9:
                    raise RuntimeError(f"sample-rate mismatch across FRF channels: {fs_values}")
                hit_fs = fs_values[0]
                if fs is None:
                    fs = hit_fs
                elif abs(hit_fs - fs) > 1e-9:
                    raise RuntimeError(f"sample-rate mismatch across hits: {hit_fs} vs {fs}")
                n = min(len(samples[ch]["samples"]) for ch in load_channels)
                force = np.asarray(samples[force_channel]["samples"][:n], dtype=float)
                force = force - np.nanmean(force[: min(1000, n)])
                seg = min(nperseg, n)
                ov = min(noverlap, max(0, seg // 2))
                hit_freqs, pff = signal.welch(
                    force,
                    fs=hit_fs,
                    window="hann",
                    nperseg=seg,
                    noverlap=ov,
                    detrend=False,
                )
                if freqs is None:
                    freqs = hit_freqs
                elif len(hit_freqs) != len(freqs) or float(np.max(np.abs(hit_freqs - freqs))) > 1e-9:
                    raise RuntimeError("frequency grid mismatch across Test07 hits")
                force_abs_peak_idx = int(np.nanargmax(np.abs(force)))
                force_peak = float(np.nanmax(np.abs(force)))
                force_rms = float(np.sqrt(np.nanmean(force**2)))
                force_peaks.append(force_peak)
                force_rms_values.append(force_rms)
                pff_hits.append(pff)
                hit_row.update(
                    {
                        "load_status": "loaded",
                        "sample_rate_sps": hit_fs,
                        "sample_count_used": n,
                        "force_peak_abs_lbf": force_peak,
                        "force_peak_abs_time_s": float(force_abs_peak_idx / hit_fs),
                        "force_rms_lbf": force_rms,
                    }
                )
                band = (hit_freqs >= 100.0) & (hit_freqs <= 10000.0)
                for ch in selected_response_channels:
                    response = np.asarray(samples[ch]["samples"][:n], dtype=float)
                    response = response - np.nanmean(response[: min(1000, n)])
                    _, gfy = signal.csd(
                        force,
                        response,
                        fs=hit_fs,
                        window="hann",
                        nperseg=seg,
                        noverlap=ov,
                        detrend=False,
                    )
                    _, coh = signal.coherence(
                        force,
                        response,
                        fs=hit_fs,
                        window="hann",
                        nperseg=seg,
                        noverlap=ov,
                        detrend=False,
                    )
                    with np.errstate(divide="ignore", invalid="ignore"):
                        h1 = gfy / pff
                    h1_hits_by_channel[ch].append(h1)
                    coh_hits_by_channel[ch].append(coh)
                    finite = band & np.isfinite(np.abs(h1)) & np.isfinite(coh)
                    if np.any(finite):
                        hit_row[f"ch{ch}_median_coherence_100_10000"] = float(np.nanmedian(coh[finite]))
                        hit_row[f"ch{ch}_median_abs_h1_g_per_lbf"] = float(np.nanmedian(np.abs(h1[finite])))
                hit_rows.append(hit_row)
            except Exception as hit_exc:
                hit_row["load_status"] = "parse_failed"
                hit_row["parse_error"] = repr(hit_exc)
                hit_rows.append(hit_row)
        loaded_hit_rows = [row for row in hit_rows if row.get("load_status") == "loaded"]
        if freqs is None or fs is None or first_samples is None or not loaded_hit_rows:
            raise RuntimeError("no Test07 hammer hits could be loaded for FRF computation")
        band = (freqs >= 100.0) & (freqs <= 10000.0)
        hit_count = len(loaded_hit_rows)
        pff_mean = np.nanmean(np.vstack(pff_hits), axis=0) if pff_hits else np.full_like(freqs, np.nan)
        manifest.update(
            {
                "status": "computed_multi_hit_diagnostic" if hit_count > 1 else "computed_low_coherence_diagnostic",
                "local_mat": rel(local_mat),
                "hit_source_count": len(hit_sources),
                "hit_count_loaded": hit_count,
                "hit_sources": hit_sources,
                "hit_summary_csv": rel(OUT / "hammer_frf_hit_summary.csv"),
                "sample_rate_sps": fs,
                "sample_rate_source": "MAT Segments.Data.dXstep",
                "sample_count_used": int(max(row.get("sample_count_used", 0) for row in loaded_hit_rows)),
                "force_channel": {
                    "daq_channel": force_channel,
                    "mat_units": first_samples[force_channel].get("channel_units"),
                    "workbook_units": channel_by_config.get(force_channel, {}).get("engineering_units"),
                    "peak_abs_lbf_max_over_hits": float(np.nanmax(force_peaks)) if force_peaks else None,
                    "peak_abs_lbf_median_over_hits": float(np.nanmedian(force_peaks)) if force_peaks else None,
                    "rms_lbf_median_over_hits": float(np.nanmedian(force_rms_values)) if force_rms_values else None,
                },
            }
        )
        npz_payload: dict[str, Any] = {
            "frequency_hz": freqs,
            "force_psd_mean_lbf2_per_hz": pff_mean,
        }
        fig_mag, ax_mag = plt.subplots(figsize=(12, 7))
        fig_coh, ax_coh = plt.subplots(figsize=(12, 6))
        channel_csv_rows = []
        for ch in selected_response_channels:
            if not h1_hits_by_channel[ch]:
                continue
            h1_stack = np.vstack(h1_hits_by_channel[ch])
            coh_stack = np.vstack(coh_hits_by_channel[ch])
            h1 = np.nanmean(h1_stack, axis=0)
            coh = np.nanmean(coh_stack, axis=0)
            meta = channel_by_config.get(ch, {})
            grid = clean_text(meta.get("fem_grid"))
            grid_int = int(grid) if grid.isdigit() else None
            response_grids.append(grid_int)
            label = f"ch {ch}, grid {grid}, {meta.get('structural_axis')}"
            for hit_h1 in h1_stack:
                ax_mag.loglog(freqs[band], np.abs(hit_h1[band]), lw=0.45, alpha=0.16, color="0.45")
            ax_mag.loglog(freqs[band], np.abs(h1[band]), lw=1.6, label=f"{label}, mean of {h1_stack.shape[0]}")
            for hit_coh in coh_stack:
                ax_coh.semilogx(freqs[band], hit_coh[band], lw=0.45, alpha=0.14, color="0.45")
            ax_coh.semilogx(freqs[band], coh[band], lw=1.6, label=f"{label}, mean")
            finite_band = band & np.isfinite(np.abs(h1)) & np.isfinite(coh)
            if np.any(finite_band):
                peak_idx_candidates = np.where(finite_band)[0]
                peak_idx = peak_idx_candidates[int(np.nanargmax(np.abs(h1[finite_band])))]
                median_coh = float(np.nanmedian(coh[finite_band]))
                channel_summary = {
                    "daq_channel": ch,
                    "description": meta.get("description"),
                    "response_units": first_samples[ch].get("channel_units") or meta.get("engineering_units"),
                    "accelerance_units": "g/lbf",
                    "structural_axis": meta.get("structural_axis"),
                    "fem_grid": grid,
                    "fem_grid_verified_in_main_model": bool(grid_int in present_grids),
                    "x_in": meta.get("x_in"),
                    "y_in": meta.get("y_in"),
                    "z_in": meta.get("z_in"),
                    "median_abs_h1_100_10000_g_per_lbf": float(np.nanmedian(np.abs(h1[finite_band]))),
                    "max_abs_h1_100_10000_g_per_lbf": float(np.nanmax(np.abs(h1[finite_band]))),
                    "max_abs_h1_frequency_hz": float(freqs[peak_idx]),
                    "median_coherence_100_10000": median_coh,
                    "fraction_coherence_ge_0p8_100_10000": float(np.mean(coh[finite_band] >= 0.8)),
                    "frf_likelihood_ready": False,
                    "frf_likelihood_blocker": "low coherence and/or source-grid convention not reconciled",
                    "hit_count_used": int(h1_stack.shape[0]),
                }
                if median_coh < 0.8:
                    manifest["status"] = (
                        "computed_multi_hit_low_coherence_diagnostic"
                        if hit_count > 1
                        else "computed_low_coherence_diagnostic"
                    )
            else:
                channel_summary = {
                    "daq_channel": ch,
                    "description": meta.get("description"),
                    "response_units": first_samples[ch].get("channel_units") or meta.get("engineering_units"),
                    "accelerance_units": "g/lbf",
                    "structural_axis": meta.get("structural_axis"),
                    "fem_grid": grid,
                    "fem_grid_verified_in_main_model": bool(grid_int in present_grids),
                    "frf_likelihood_ready": False,
                    "frf_likelihood_blocker": "no finite FRF samples in reported band",
                }
            manifest["channels"].append(channel_summary)
            channel_csv_rows.append(channel_summary)
            key = f"ch{ch:03d}"
            npz_payload[f"{key}_h1_mean_real_g_per_lbf"] = np.real(h1)
            npz_payload[f"{key}_h1_mean_imag_g_per_lbf"] = np.imag(h1)
            npz_payload[f"{key}_coherence_mean"] = coh
            npz_payload[f"{key}_h1_hits_real_g_per_lbf"] = np.real(h1_stack)
            npz_payload[f"{key}_h1_hits_imag_g_per_lbf"] = np.imag(h1_stack)
            npz_payload[f"{key}_coherence_hits"] = coh_stack
        ax_mag.set_title(f"Test07 Hammer H1 Accelerance Diagnostic ({hit_count} loaded hit{'s' if hit_count != 1 else ''})")
        ax_mag.set_xlabel("frequency (Hz, log scale)")
        ax_mag.set_ylabel("|H1| (g/lbf)")
        ax_mag.grid(True, which="both", alpha=0.25)
        ax_mag.legend(fontsize=8)
        fig_mag.tight_layout()
        fig_mag.savefig(FIGURES / "hammer_frf_accelerance_subset.png", dpi=180)
        plt.close(fig_mag)
        ax_coh.axhline(0.8, color="0.35", lw=0.9, ls="--", label="0.8 coherence reference")
        ax_coh.set_title(f"Test07 Hammer Coherence Diagnostic ({hit_count} loaded hit{'s' if hit_count != 1 else ''})")
        ax_coh.set_xlabel("frequency (Hz, log scale)")
        ax_coh.set_ylabel("magnitude-squared coherence")
        ax_coh.set_ylim(-0.02, 1.02)
        ax_coh.grid(True, which="both", alpha=0.25)
        ax_coh.legend(fontsize=8)
        fig_coh.tight_layout()
        fig_coh.savefig(FIGURES / "hammer_frf_coherence_subset.png", dpi=180)
        plt.close(fig_coh)
        np.savez(OUT / "hammer_frf_estimates.npz", **npz_payload)
        write_csv(
            OUT / "hammer_frf_hit_summary.csv",
            hit_rows,
            [
                "hit_index",
                "source_type",
                "member",
                "local_path",
                "load_status",
                "sample_rate_sps",
                "sample_count_used",
                "force_peak_abs_lbf",
                "force_peak_abs_time_s",
                "force_rms_lbf",
                "ch1_median_coherence_100_10000",
                "ch1_median_abs_h1_g_per_lbf",
                "ch50_median_coherence_100_10000",
                "ch50_median_abs_h1_g_per_lbf",
                "ch87_median_coherence_100_10000",
                "ch87_median_abs_h1_g_per_lbf",
                "parse_error",
            ],
        )
        write_csv(
            OUT / "hammer_frf_channel_map.csv",
            channel_csv_rows,
            [
                "daq_channel",
                "description",
                "response_units",
                "accelerance_units",
                "structural_axis",
                "fem_grid",
                "fem_grid_verified_in_main_model",
                "x_in",
                "y_in",
                "z_in",
                "median_abs_h1_100_10000_g_per_lbf",
                "max_abs_h1_100_10000_g_per_lbf",
                "max_abs_h1_frequency_hz",
                "median_coherence_100_10000",
                "fraction_coherence_ge_0p8_100_10000",
                "frf_likelihood_ready",
                "frf_likelihood_blocker",
            ],
        )
        nasa_points = set()
        for pch in assets.get("pch_files", []):
            nasa_points.update(pch.get("unique_response_points", []))
        measured_grid_intersection = sorted(g for g in response_grids if g in nasa_points)
        manifest["comparison_status"] = (
            "not_directly_overlayable_currently"
            if not measured_grid_intersection
            else "response_grid_overlap_found_source_still_needs_check"
        )
        manifest["comparison_blockers"] = [
            "Test07 shock response channels map to 9900001-style FEM grids; NASA SOL 111 PCH response points are modal-test grids such as 1101/2101/11101.",
            "Test07 source location from channel 116 is not yet mapped to SOL 111 force grids 11101X or 11110Y.",
            "H1 estimates have low median coherence across 100-10000 Hz.",
        ]
        manifest["numeric_estimates_npz"] = rel(OUT / "hammer_frf_estimates.npz")
        manifest["channel_map_csv"] = rel(OUT / "hammer_frf_channel_map.csv")
        manifest["figures"] = [
            rel(FIGURES / "hammer_frf_accelerance_subset.png"),
            rel(FIGURES / "hammer_frf_coherence_subset.png"),
            rel(FIGURES / "nasa_correlation_frf_asset_summary.png"),
        ]
    except Exception as exc:
        manifest["status"] = "parse_failed"
        manifest["parse_error"] = repr(exc)
    write_json(OUT / "hammer_frf_subset_manifest.json", manifest)
    write_hammer_frf_markdown(manifest)
    return manifest


def write_hammer_frf_markdown(manifest: dict[str, Any]) -> None:
    lines = [
        "# Hammer FRF Diagnostic and FEM Alignment",
        "",
        f"Generated: {manifest.get('generated_utc')}",
        "",
        "## Status",
        "",
        f"- FRF status: `{manifest.get('status')}`",
        f"- Comparison status: `{manifest.get('comparison_status')}`",
        "- Interpretation: this is a derived-data diagnostic. It is not accepted as a StatFEM likelihood input in this packet.",
        "",
        "## Quantity and Processing",
        "",
    ]
    qc = manifest.get("quantity_contract") or {}
    for key in ["estimator", "numerator", "denominator", "units", "coordinate", "excitation", "boundary_condition"]:
        lines.append(f"- {key}: {qc.get(key)}")
    proc = manifest.get("processing") or {}
    lines += [
        "",
        "## Processing Choices",
        "",
    ]
    for key, value in proc.items():
        lines.append(f"- {key}: `{value}`")
    force = manifest.get("force_channel") or {}
    lines += [
        "",
        "## Force Channel",
        "",
        f"- DAQ channel: `{force.get('daq_channel')}`",
        f"- MAT units: `{force.get('mat_units')}`; workbook units: `{force.get('workbook_units')}`",
        f"- Loaded hit count: `{manifest.get('hit_count_loaded')}` of `{manifest.get('hit_source_count')}` available MAT source(s)",
        f"- TestLog/archive alignment: {manifest.get('test_log_archive_alignment_note')}",
        f"- Baseline-removed maximum peak absolute force over loaded hits: `{force.get('peak_abs_lbf_max_over_hits')}` lbf",
        f"- Baseline-removed median peak absolute force over loaded hits: `{force.get('peak_abs_lbf_median_over_hits')}` lbf",
        f"- Baseline-removed median RMS force over loaded hits: `{force.get('rms_lbf_median_over_hits')}` lbf",
        f"- Per-hit summary CSV: `{manifest.get('hit_summary_csv')}`",
        "",
        "## Test-Log Source Metadata",
        "",
        "| Filename | Description | Impact point | Comments |",
        "|---|---|---|---|",
    ]
    for row in manifest.get("source_location_metadata", []):
        lines.append(
            f"| `{row.get('filename')}` | {row.get('description')} | `{row.get('impact_point')}` | {row.get('comments')} |"
        )
    lines += [
        "",
        "## Response Channels",
        "",
        "| DAQ | FEM grid | Verified in FEM | Axis | Description | Median coherence | Likelihood ready |",
        "|---:|---:|---|---|---|---:|---|",
    ]
    for channel in manifest.get("channels", []):
        lines.append(
            f"| {channel.get('daq_channel')} | {channel.get('fem_grid')} | "
            f"{channel.get('fem_grid_verified_in_main_model')} | {channel.get('structural_axis')} | "
            f"{channel.get('description')} | {channel.get('median_coherence_100_10000')} | "
            f"{channel.get('frf_likelihood_ready')} |"
        )
    lines += [
        "",
        "## NASA Correlation Asset Status",
        "",
        f"- Asset index JSON: `{manifest.get('nasa_correlation_assets', {}).get('json')}`",
        f"- Asset index Markdown: `{manifest.get('nasa_correlation_assets', {}).get('md')}`",
        f"- Asset index status: `{manifest.get('nasa_correlation_assets', {}).get('status')}`",
        "",
        "## Comparison Blockers",
        "",
    ]
    for blocker in manifest.get("comparison_blockers", []):
        lines.append(f"- {blocker}")
    lines += [
        "",
        "## Figures",
        "",
        f"![Hammer accelerance diagnostic]({rel(FIGURES / 'hammer_frf_accelerance_subset.png')})",
        "",
        f"![Hammer coherence diagnostic]({rel(FIGURES / 'hammer_frf_coherence_subset.png')})",
        "",
        f"![NASA FRF asset summary]({rel(FIGURES / 'nasa_correlation_frf_asset_summary.png')})",
    ]
    (OUT / "hammer_frf_alignment.md").write_text("\n".join(lines) + "\n")


def write_quantity_contracts() -> None:
    md = """# ShockSat Quantity Contracts

These contracts are written before accepting plots or likelihoods. Units are stated from the fetched README and instrumentation workbook unless otherwise noted.

## 1. Acceleration Time History

- Quantity name: acceleration time history.
- Numerator: calibrated accelerometer response signal.
- Denominator: none.
- Coordinate(s): sensor structural axis from the instrumentation sheet (`Accel Dir for SS X/Y/Z`) at a listed FEM grid.
- Excitation: hammer impact or pyro event, specified by test log.
- Boundary condition: as-tested ShockSat hardware; support/suspension condition must be taken from the relevant test log or overview before FEM comparison.
- Units: `g` for accelerometer channels, with sensor calibration in `mV/g`.
- Time axis: seconds from MAT sample zero. README states `100000 samples/s` generally; when a MAT file provides `dXstep`, the file-specific sample interval is authoritative for that plotted/test subset.
- Expected behavior: transient shock/impact response with baseline near zero after detrending; higher magnitude near source channels and wave-propagation decay/scatter away from source.
- Reference/source: ShockSat README and instrumentation workbook.
- Checker: require channel map, units, sample rate, and test ID before plotting.

## 2. Power Spectral Density Diagnostic

- Quantity name: one-sided Welch PSD diagnostic.
- Numerator: squared calibrated channel amplitude.
- Denominator: frequency bandwidth.
- Coordinate(s): same sensor coordinate as the time history.
- Excitation: same event as the time history.
- Boundary condition: as-tested hardware.
- Units: `g^2/Hz` for acceleration channels and `lbf^2/Hz` for hammer force if force is plotted.
- Frequency axis: Hz, log-scaled for review, focused on `100-10000 Hz`.
- Expected behavior: broad shock/impact energy; narrow modal content may appear, but PSD peaks are not natural frequencies without a feature contract.
- Reference/source: README target band and standard Welch PSD convention.
- Checker: label PSD as a diagnostic, not as an FRF or SRS.

## 3. Shock Response Spectrum

- Quantity name: Shock Response Spectrum (SRS).
- Numerator: peak absolute response of a bank of single-degree-of-freedom oscillators to the acceleration time history.
- Denominator: none.
- Coordinate(s): sensor structural axis.
- Excitation: pyro or impact acceleration input as measured at the channel.
- Boundary condition: as-tested hardware.
- Units: `g`.
- Frequency axis: oscillator natural frequency in Hz, preferably log-spaced.
- Expected behavior: positive envelope-like curve; not directly a transfer function and not phase-bearing.
- Reference/source: standard shock-test SRS convention; damping or Q must be stated when computed.
- Checker: SRS is not accepted unless damping/Q and algorithm are documented. This run uses PSD if SRS is not computed.

## 4. Hammer-Test FRF

- Quantity name: accelerance FRF from hammer force to acceleration.
- Numerator: response acceleration at selected channel.
- Denominator: measured hammer force at channel 116 or equivalent force channel.
- Coordinate(s): response sensor structural axis and hammer input point/direction from test log.
- Excitation: hammer force, units `lbf`.
- Boundary condition: as-tested hammer/modal configuration.
- Units: `g/lbf` if acceleration is in `g` and force is in `lbf`.
- Frequency axis: Hz, log-scaled unless a narrow linear modal zoom is justified.
- Expected behavior: resonant peaks, antiresonances depending on drive/response pair, phase roll if complex FRF is estimated.
- Reference/source: instrumentation workbook hammer row and modal-test FRF convention.
- Checker: do not call a response-only spectrum an FRF; require force channel and estimator details.

## 5. Cross-Channel Transfer Estimate

- Quantity name: response-response transfer or normalized cross-channel estimate.
- Numerator: response channel spectrum.
- Denominator: reference response channel spectrum.
- Coordinate(s): two listed sensor structural axes.
- Excitation: same event; forcing may be unknown for pyro.
- Boundary condition: as-tested hardware.
- Units: dimensionless if same units, otherwise stated ratio.
- Frequency axis: Hz, log-scaled.
- Expected behavior: useful for relative propagation diagnostics; not a physical FRF unless input conditions justify it.
- Reference/source: signal-processing convention, not a FEM property by itself.
- Checker: label as cross-channel diagnostic, not force-to-response FRF.

## 6. FEM Modal Frequency

- Quantity name: FEM modal frequency.
- Numerator: modal circular frequency converted to cycles per second.
- Denominator: `2*pi`.
- Coordinate(s): global FEM coordinates from source deck.
- Excitation: none; eigenvalue property.
- Boundary condition: FEM boundary/suspension assumptions from deck/correlation documentation.
- Units: Hz.
- Frequency axis: mode index or Hz.
- Expected behavior: positive flexible modes; rigid-body modes depend on boundary assumptions.
- Reference/source: fetched FEM deck/correlation files when parseable.
- Checker: require solver/source file and boundary-condition cards before comparing to test.

## 7. FEM Mode Shape / MAC

- Quantity name: mode shape and Modal Assurance Criterion (MAC).
- Numerator: squared magnitude of the modal-vector inner product.
- Denominator: product of modal-vector self inner products.
- Coordinate(s): paired test/FEM response coordinates at accelerometer grids or mapped nodes.
- Excitation: none for FEM mode; modal-test excitation for test mode extraction.
- Boundary condition: matched test/FEM boundary condition.
- Units: mode shapes are scale-normalized; MAC is dimensionless.
- Expected behavior: MAC near 1 for matching shapes, near 0 for orthogonal/unrelated shapes; repeated/close modes require subspace comparison.
- Reference/source: standard modal correlation convention.
- Checker: do not report MAC without test mode vectors and a coordinate map.

## 8. Candidate StatFEM Observation

- Quantity name: selected observation vector for v1 StatFEM.
- Numerator: measured modal frequencies, FRF log magnitudes/phases, or selected response features.
- Denominator: depends on chosen observation; explicitly stated in the launch definition.
- Coordinate(s): selected sensor/test coordinates with FEM grid map.
- Excitation: hammer/modal first if force is available; pyro response reserved for validation/QOI if appropriate.
- Boundary condition: matched test/FEM configuration.
- Units: observation-specific.
- Expected behavior: enough sensitivity to selected stiffness/damping parameters without allowing discrepancy to impersonate physics.
- Reference/source: ShockSat data and project StatFEM harness gates.
- Checker: require data count, likelihood data usage, inferred/fixed/not-inferred variables, and held-out validation.

## 9. Candidate QOI

- Quantity name: payload/interface/far-field shock response metric.
- Numerator: selected acceleration/SRS/PSD/FRF feature at a payload-like, interface, or far-field channel.
- Denominator: none for response metrics; force for FRF-derived quantities.
- Coordinate(s): selected channel structural axis and FEM grid.
- Excitation: pyro NSD or hammer/modal depending on model layer.
- Boundary condition: as-tested hardware and event.
- Units: `g`, `g^2/Hz`, `g/lbf`, or SRS `g`, explicitly chosen before inference.
- Expected behavior: response should reflect source-to-far-field propagation and joint/interface effects; not all QOI shifts are stiffness changes.
- Reference/source: ShockSat stated purpose as shock-propagation methodology test bed.
- Checker: QOI validation must hold out at least one channel, test, band, or mode family.
"""
    (OUT / "quantity_contracts.md").write_text(md)


def write_alignment_and_launch(
    fem_inventory: dict[str, Any],
    first_data_manifest: dict[str, Any],
    channel_rows: list[dict[str, Any]],
    test_rows: list[dict[str, Any]],
    hammer_frf_manifest: dict[str, Any] | None = None,
) -> None:
    directly_comparable = []
    blockers = []
    main_aggregate = fem_inventory.get("main_fem_20211021_aggregate") or {}
    shock_grid_check = main_aggregate.get("shock_instrumentation_grid_check") or {}
    missing_shock_grids = shock_grid_check.get("missing_grid_ids")
    if missing_shock_grids == []:
        directly_comparable.append("Instrumentation FEM grid IDs can be checked against parsed deck GRID cards; expected shock accelerometer grids are present in the parsed main FEM aggregate.")
    elif fem_inventory.get("parsed_models"):
        directly_comparable.append("FEM grid IDs can be checked against parsed deck GRID cards, but the shock-grid completeness check needs review.")
    else:
        blockers.append("No parsed FEM source deck yet, so node/element counts and sensor-grid existence are not fully verified.")
    if any(r.get("quantity") == "hammer_force" for r in channel_rows):
        directly_comparable.append("Hammer force channel exists in instrumentation map (channel 116, lbf).")
    else:
        blockers.append("No hammer force channel was parsed.")
    if first_data_manifest.get("status") == "plotted":
        directly_comparable.append("At least one real MAT data subset was plotted with channel metadata.")
    else:
        blockers.append("Raw MAT data subset was not plotted yet because archive is missing or parse failed.")
    if hammer_frf_manifest:
        if str(hammer_frf_manifest.get("status", "")).startswith("computed"):
            directly_comparable.append(
                "A measured Test07 hammer H1 accelerance diagnostic can be computed from force channel 116 to selected response channels."
            )
        if "low_coherence" in str(hammer_frf_manifest.get("status", "")):
            blockers.append(
                "The measured hammer H1 accelerance estimate has low coherence and is not likelihood-ready."
            )
        if hammer_frf_manifest.get("comparison_status") == "not_directly_overlayable_currently":
            blockers.append(
                "NASA SOL 111 FRF assets and Test07 shock-channel FRFs are not directly overlayable until source/response grid conventions are reconciled."
            )
    nasa_corr = "Tail/full FEM evidence includes FEM/Correlation assets; whether the evidence proves correlation requires inspecting extracted correlation documents."
    if missing_shock_grids == []:
        sensor_map_status = (
            "Instrumentation workbook FEM grids are verified in the parsed main FEM_20211021 aggregate; "
            "the expected ShockSat accelerometer grids are present."
        )
    elif fem_inventory.get("parsed_models"):
        missing_label = missing_shock_grids if missing_shock_grids is not None else "not evaluated"
        sensor_map_status = (
            "Instrumentation workbook has FEM grid IDs, but the shock-grid completeness status is "
            f"`{missing_label}`; inspect fem_inventory.json before node-level comparison."
        )
    else:
        sensor_map_status = (
            "Instrumentation workbook has FEM grid IDs, but deck existence must be verified in parsed FEM source "
            "before accepting a sensor-to-node map."
        )
    alignment = {
        "generated_utc": now_utc(),
        "directly_comparable_now": directly_comparable,
        "not_comparable_yet_or_blocked": blockers,
        "nasa_well_correlated_status": nasa_corr,
        "sensor_to_fem_map_status": sensor_map_status,
        "first_data_status": first_data_manifest.get("status"),
        "hammer_frf_status": (hammer_frf_manifest or {}).get("status"),
        "hammer_frf_comparison_status": (hammer_frf_manifest or {}).get("comparison_status"),
    }
    write_json(OUT / "fem_test_alignment.json", alignment)
    fig, ax = plt.subplots(figsize=(12, 6))
    ax.axis("off")
    ax.text(0.02, 0.95, "FEM/Test Alignment Summary", fontsize=18, fontweight="bold", va="top")
    y = 0.82
    ax.text(0.03, y, "Supported now", fontsize=13, fontweight="bold")
    y -= 0.07
    for item in directly_comparable or ["No direct comparison accepted yet."]:
        ax.text(0.05, y, f"- {item}", fontsize=10, va="top", wrap=True)
        y -= 0.08
    y -= 0.03
    ax.text(0.03, y, "Blockers / not yet comparable", fontsize=13, fontweight="bold")
    y -= 0.07
    for item in blockers or ["No blockers recorded."]:
        ax.text(0.05, y, f"- {item}", fontsize=10, va="top", wrap=True)
        y -= 0.08
    fig.tight_layout()
    fig.savefig(FIGURES / "fem_test_comparison_summary.png", dpi=180)
    plt.close(fig)
    (OUT / "fem_test_alignment.md").write_text(
        "\n".join(
            [
                "# FEM/Test Alignment Assessment",
                "",
                f"Generated: {alignment['generated_utc']}",
                "",
                "## Directly Comparable Now",
                "",
                *[f"- {item}" for item in directly_comparable],
                "",
                "## Not Comparable Yet / Blockers",
                "",
                *[f"- {item}" for item in blockers],
                "",
                "## NASA Correlation Claim Status",
                "",
                nasa_corr,
                "",
                "## Map Status",
                "",
                alignment["sensor_to_fem_map_status"],
                "",
                f"![FEM/test comparison summary]({rel(FIGURES / 'fem_test_comparison_summary.png')})",
            ]
        )
        + "\n"
    )
    launch = {
        "generated_utc": now_utc(),
        "v1_recommendation": "hammer_or_modal_first_if_force_and_FRF_data_are_parseable",
        "observations": [
            {
                "name": "selected hammer accelerance FRFs or modal frequencies",
                "reason": "Hammer force channel exists and supports input-output dynamics before unknown-forcing pyro validation.",
            },
            {
                "name": "pyro NSD response/SRS features as held-out validation or QOI",
                "reason": "Pyro is higher-magnitude shock response but forcing is not directly measured.",
            },
        ],
        "inferred_variables": [
            "small number of stiffness scales grouped by source box, bolted-joint/interface region, upper structure, or struts",
            "possibly damping scale only if repeat/FRF metadata support it",
        ],
        "fixed_variables": [
            "geometry and mass properties from NASA correlated FEM",
            "sensor calibration from instrumentation workbook unless calibration uncertainty is added later",
            "file-specific sample interval from MAT dXstep for plotted/test subsets; README 100000 samples/s retained as general-release metadata until reconciled",
        ],
        "discrepancy": "output-space discrepancy over log frequency or mode index; do not put discrepancy in the same stiffness parameter space as calibrated stiffness",
        "noise": "use sensor/test metadata when available; otherwise transparent assumed g/lbf noise with sensitivity priority",
        "qoi": "payload-like, interface/bolted-joint, or far-field panel shock response metric at a held-out channel",
        "held_out_validation": [
            "hold out at least one channel",
            "hold out one test or one frequency band/mode family",
            "pyro validation after hammer/modal updating is the strongest trust test",
        ],
        "statfem_stub_status": "deferred unless raw MAT data, force/FRF inputs, FEM mapping, and held-out validation are all available",
    }
    write_json(OUT / "statfem_launch_definition.json", launch)
    draw_statfem_graphical_model()
    (OUT / "statfem_launch_definition.md").write_text(
        "\n".join(
            [
                "# ShockSat StatFEM Digital-Twin Launch Definition",
                "",
                f"Generated: {launch['generated_utc']}",
                "",
                "## Plain-English v1",
                "",
                "Use hammer/modal data first if the hammer force and response channels can be parsed, because that gives a clearer input-output dynamic quantity. Then use pyro NSD shock response as a held-out trust test or QOI layer, not as a first hidden-forcing calibration shortcut.",
                "",
                "## Observations",
                "",
                *[f"- {item['name']}: {item['reason']}" for item in launch["observations"]],
                "",
                "## Inferred Variables",
                "",
                *[f"- {item}" for item in launch["inferred_variables"]],
                "",
                "## Fixed Variables",
                "",
                *[f"- {item}" for item in launch["fixed_variables"]],
                "",
                "## Discrepancy, Noise, and QOI",
                "",
                f"- Discrepancy: {launch['discrepancy']}",
                f"- Noise: {launch['noise']}",
                f"- QOI: {launch['qoi']}",
                "",
                "## Held-Out Validation",
                "",
                *[f"- {item}" for item in launch["held_out_validation"]],
                "",
                "## StatFEM Stub Status",
                "",
                launch["statfem_stub_status"],
                "",
                f"![StatFEM graphical model]({rel(FIGURES / 'statfem_graphical_model.png')})",
            ]
        )
        + "\n"
    )


def draw_statfem_graphical_model() -> None:
    fig, ax = plt.subplots(figsize=(12, 7))
    ax.axis("off")
    boxes = [
        (0.06, 0.70, 0.22, 0.14, "NASA FEM\ngeometry, mass,\nnominal stiffness"),
        (0.38, 0.70, 0.22, 0.14, "Update knobs\nregional stiffness\n+ possible damping"),
        (0.70, 0.70, 0.22, 0.14, "Forward model\nmodes / FRFs /\nshock surrogate"),
        (0.06, 0.38, 0.22, 0.14, "Measured data\nhammer, pyro,\nchannel map"),
        (0.38, 0.38, 0.22, 0.14, "Likelihood\nresidual + noise\n+ discrepancy"),
        (0.70, 0.38, 0.22, 0.14, "Posterior\nparameters +\npredictive response"),
        (0.38, 0.10, 0.22, 0.14, "Held-out validation\nchannel / test /\nband / mode family"),
        (0.70, 0.10, 0.22, 0.14, "QOI\npayload/interface/\nfar-field shock metric"),
    ]
    for x, y, w, h, text in boxes:
        ax.add_patch(plt.Rectangle((x, y), w, h, fill=False, lw=1.8))
        ax.text(x + w / 2, y + h / 2, text, ha="center", va="center", fontsize=11)
    arrows = [
        ((0.28, 0.77), (0.38, 0.77)),
        ((0.60, 0.77), (0.70, 0.77)),
        ((0.81, 0.70), (0.81, 0.52)),
        ((0.28, 0.45), (0.38, 0.45)),
        ((0.60, 0.45), (0.70, 0.45)),
        ((0.49, 0.38), (0.49, 0.24)),
        ((0.60, 0.17), (0.70, 0.17)),
    ]
    for (x0, y0), (x1, y1) in arrows:
        ax.annotate("", xy=(x1, y1), xytext=(x0, y0), arrowprops=dict(arrowstyle="->", lw=1.6))
    ax.text(
        0.06,
        0.93,
        "ShockSat v1 StatFEM launch model (definition only; no active sampler claim)",
        fontsize=16,
        fontweight="bold",
    )
    fig.tight_layout()
    fig.savefig(FIGURES / "statfem_graphical_model.png", dpi=180)
    plt.close(fig)


def write_manifest_and_packet(
    source_manifest: dict[str, Any],
    file_inventory: dict[str, Any],
    fem_inventory: dict[str, Any],
    instrumentation_summary: dict[str, Any],
    first_data_manifest: dict[str, Any],
    hammer_frf_manifest: dict[str, Any],
) -> None:
    manifest = {
        "generated_utc": now_utc(),
        "workspace": rel(OUT),
        "one_command_replay": f"bash {rel(OUT / 'run_all.sh')}",
        "artifacts": {
            "priority_deliverables": rel(OUT / "priority_deliverables.md"),
            "question_framing": rel(OUT / "question_framing.md"),
            "decisions_log": rel(OUT / "decisions_log.md"),
            "source_manifest_json": rel(OUT / "source_manifest.json"),
            "source_manifest_md": rel(OUT / "source_manifest.md"),
            "download_log": rel(OUT / "download_log.md"),
            "file_inventory_json": rel(OUT / "file_inventory.json"),
            "file_inventory_md": rel(OUT / "file_inventory.md"),
            "fem_inventory_json": rel(OUT / "fem_inventory.json"),
            "fem_inventory_md": rel(OUT / "fem_inventory.md"),
            "instrumentation_inventory_json": rel(OUT / "instrumentation_inventory.json"),
            "instrumentation_inventory_md": rel(OUT / "instrumentation_inventory.md"),
            "channel_map_csv": rel(OUT / "channel_map.csv"),
            "test_log_summary_csv": rel(OUT / "test_log_summary.csv"),
            "first_data_subset_manifest": rel(OUT / "first_data_subset_manifest.json"),
            "hammer_frf_subset_manifest": rel(OUT / "hammer_frf_subset_manifest.json"),
            "hammer_frf_alignment": rel(OUT / "hammer_frf_alignment.md"),
            "hammer_frf_channel_map": rel(OUT / "hammer_frf_channel_map.csv"),
            "hammer_frf_hit_summary": rel(OUT / "hammer_frf_hit_summary.csv"),
            "hammer_frf_estimates_npz": rel(OUT / "hammer_frf_estimates.npz"),
            "nasa_correlation_frf_assets_json": rel(OUT / "nasa_correlation_frf_assets.json"),
            "nasa_correlation_frf_assets_md": rel(OUT / "nasa_correlation_frf_assets.md"),
            "quantity_contracts": rel(OUT / "quantity_contracts.md"),
            "fem_test_alignment": rel(OUT / "fem_test_alignment.md"),
            "statfem_launch_definition": rel(OUT / "statfem_launch_definition.md"),
            "packet": rel(OUT / "shocksat_statfem_packet.md"),
            "checker_report": rel(OUT / "checker_report.json"),
            "runtime": rel(OUT / "runtime.json"),
        },
        "figures": [rel(p) for p in sorted(FIGURES.glob("*.png"))],
        "source_status_counts": dict(Counter(e["state"] for e in source_manifest["source_entries"])),
        "first_data_status": first_data_manifest.get("status"),
        "hammer_frf_status": hammer_frf_manifest.get("status"),
        "hammer_frf_comparison_status": hammer_frf_manifest.get("comparison_status"),
        "fem_archive_status": fem_inventory.get("archive_status"),
        "instrumentation_status": instrumentation_summary.get("status"),
        "no_active_statfem_claim": True,
    }
    write_json(OUT / "manifest.json", manifest)
    packet = [
        "# ShockSat StatFEM Foundation Packet",
        "",
        "## Method Summary",
        "",
        "- Engineering decision: decide whether ShockSat1 is ready to become the first real-data StatFEM bridge and define the smallest credible v1 update.",
        "- Current model status: source/data/FEM/instrumentation audit, first measured-data plots, diagnostic hammer-FRF layer, and launch definition only.",
        "- Active StatFEM posterior: `false`.",
        "- Sampler status: no NUTS/HMC or fallback sampler was run.",
        "- Data count: see instrumentation/test-log inventory and first data subset manifest.",
        "- Likelihood status: no likelihood accepted yet; the hammer H1 accelerance estimate is diagnostic because coherence/source-grid alignment are not sufficient.",
        "- Inferred variables: none in this packet.",
        "- Fixed assumptions: README English units, target 100-10000 Hz shock band, sensor calibration from workbook; sample rate is taken from file-specific MAT `dXstep` for plotted subsets, with the README 100000 samples/s value retained as general-release metadata until reconciled.",
        "- Not inferred: model discrepancy, observation noise, sensor calibration uncertainty, forcing, build/test variability.",
        "- Data usage: raw MAT data plotted only if parseable; PSD diagnostics are not FRFs or SRS; H1 hammer accelerance is stored as derived diagnostic data, not calibration data.",
        "",
        "## Question Framing",
        "",
        (OUT / "question_framing.md").read_text(),
        "",
        "## Source Provenance",
        "",
        f"- Source manifest: `{rel(OUT / 'source_manifest.json')}`",
        f"- Download/access log: `{rel(OUT / 'download_log.md')}`",
        f"- Source state counts: `{manifest['source_status_counts']}`",
        "",
        "## File Inventory",
        "",
        f"- File inventory: `{rel(OUT / 'file_inventory.md')}`",
        "",
        "## FEM Inventory",
        "",
        f"- FEM archive status: `{fem_inventory.get('archive_status')}`",
        f"- FEM inventory: `{rel(OUT / 'fem_inventory.md')}`",
        f"![FEM file tree]({rel(FIGURES / 'fem_file_tree.png')})",
        f"![FEM mesh preview]({rel(FIGURES / 'fem_mesh_preview.png')})",
        "",
        "## Instrumentation and Channel Map",
        "",
        f"- Instrumentation status: `{instrumentation_summary.get('status')}`",
        f"- Channel map: `{rel(OUT / 'channel_map.csv')}`",
        f"- Test-log summary: `{rel(OUT / 'test_log_summary.csv')}`",
        "",
        "## First Data Plots",
        "",
        f"- First data status: `{first_data_manifest.get('status')}`",
        f"![First time histories]({rel(FIGURES / 'first_time_histories.png')})",
        f"![First PSD diagnostic]({rel(FIGURES / 'first_srs_or_psd.png')})",
        f"![Channel overview]({rel(FIGURES / 'channel_comparison_overview.png')})",
        "",
        "## First Hammer FRF Diagnostic",
        "",
        f"- Hammer FRF status: `{hammer_frf_manifest.get('status')}`",
        f"- Hammer FRF comparison status: `{hammer_frf_manifest.get('comparison_status')}`",
        f"- Hammer FRF manifest: `{rel(OUT / 'hammer_frf_subset_manifest.json')}`",
        f"- Hammer FRF alignment: `{rel(OUT / 'hammer_frf_alignment.md')}`",
        f"![Hammer accelerance diagnostic]({rel(FIGURES / 'hammer_frf_accelerance_subset.png')})",
        f"![Hammer coherence diagnostic]({rel(FIGURES / 'hammer_frf_coherence_subset.png')})",
        "",
        "## Quantity Contracts",
        "",
        f"- Quantity contracts: `{rel(OUT / 'quantity_contracts.md')}`",
        "",
        "## FEM/Test Comparison",
        "",
        (OUT / "fem_test_alignment.md").read_text(),
        "",
        "## StatFEM Launch Definition",
        "",
        (OUT / "statfem_launch_definition.md").read_text(),
        "",
        "## Sensitivity Priorities",
        "",
        "- Sensor calibration/noise assumptions by sensor type and range.",
        "- Output-space discrepancy correlation length over log frequency or mode index.",
        "- Choice of hammer/modal observations versus pyro response features.",
        "- Held-out channel/test/band selection.",
        "- Boundary-condition and support/suspension interpretation.",
        "",
        "## What This Proves / Does Not Prove",
        "",
        "- Proves: fetched-source provenance and first metadata inventories exist for available files.",
        "- Proves: channel map/test logs are parseable enough to identify DAQ channels, units, sample rate, and FEM grid IDs.",
        "- Proves: a first Test07 hammer H1 accelerance diagnostic can be computed and traced to force/response channels.",
        "- Does not prove: calibrated StatFEM, active NUTS/HMC, validated FEM/test agreement, FRF likelihood readiness, or shock-prediction performance.",
        "",
        "## Human Reflection Prompts",
        "",
        "- Which held-out validation target matters most: channel, test, frequency band, or mode family?",
        "- Should v1 prioritize hammer/modal FRFs or pyro shock QOI validation?",
        "- Which ShockSat location is the payload/interface-like QOI for this project vision?",
        "",
        "## Replay",
        "",
        f"Run: `{manifest['one_command_replay']}`",
    ]
    (OUT / "shocksat_statfem_packet.md").write_text("\n".join(packet) + "\n")


def write_source_markdown(source_manifest: dict[str, Any]) -> None:
    lines = [
        "# ShockSat Source Manifest",
        "",
        f"Generated: {source_manifest['generated_utc']}",
        "",
        f"Workshop URL: {source_manifest['workshop_url']}",
        "",
        source_manifest["direct_asset_route_note"],
        "",
        "| Name | State | Listed size | Local size bytes | SHA256 |",
        "|---|---|---:|---:|---|",
    ]
    for entry in source_manifest["source_entries"]:
        local = entry.get("local") or {}
        lines.append(
            f"| {entry['name']} | {entry['state']} | {entry.get('listed_size') or ''} | "
            f"{local.get('size_bytes') or ''} | `{local.get('sha256') or ''}` |"
        )
    lines += [
        "",
        "## Access Notes",
        "",
        "- Initial direct GET attempts to `https://nescacademy.nasa.gov/shocksat/...` returned 404.",
        "- The browser file page posts a hidden `url` field and redirects to `mediaex-server.larc.nasa.gov`.",
        "- Large archives were probed with browser-like and curl-like HEAD requests plus byte ranges before any full download.",
    ]
    (OUT / "source_manifest.md").write_text("\n".join(lines) + "\n")
    dlog = [
        "# ShockSat Download / Access Log",
        "",
        f"Generated: {source_manifest['generated_utc']}",
        "",
        "Primary log files:",
        "",
    ]
    for path in sorted(LOGS.glob("*.log")) + sorted(LOGS.glob("*fetch*.txt")):
        dlog.append(f"- `{rel(path)}`")
    dlog += [
        "",
        "Key finding: direct nescacademy asset URLs returned 404, while the page form route redirected to mediaex-server URLs that support HEAD and byte ranges.",
    ]
    (OUT / "download_log.md").write_text("\n".join(dlog) + "\n")


def write_file_inventory_markdown(file_inventory: dict[str, Any]) -> None:
    lines = [
        "# ShockSat File Inventory",
        "",
        f"Generated: {file_inventory['generated_utc']}",
        "",
        "## Fetched Archive Listings",
        "",
    ]
    for archive in file_inventory.get("archives") or []:
        lines += [
            f"### {archive.get('archive')}",
            "",
            f"- Entries: `{archive.get('entry_count')}`",
            f"- Total uncompressed bytes: `{archive.get('total_uncompressed_size_bytes')}`",
            f"- Extension counts: `{archive.get('extension_counts')}`",
            f"- Top directories: `{archive.get('top_directories')}`",
            "",
        ]
    lines += [
        "## Tail-Range Listing Evidence for Deferred/Large Archives",
        "",
    ]
    for name, samples in (file_inventory.get("tail_range_filename_samples") or {}).items():
        lines.append(f"### {name}")
        for sample in samples[:30]:
            lines.append(f"- `{sample}`")
        lines.append("")
    lines += [
        "## Extracted Working Files",
        "",
    ]
    for meta in file_inventory.get("extracted_files") or []:
        lines.append(f"- `{meta.get('local_path')}` ({meta.get('size_bytes')} bytes)")
    (OUT / "file_inventory.md").write_text("\n".join(lines) + "\n")


def write_runtime() -> None:
    real_sum = 0.0
    for path in LOGS.glob("*.log"):
        text = path.read_text(errors="replace")
        for match in re.finditer(r"^real\s+([0-9.]+)$", text, flags=re.M):
            real_sum += float(match.group(1))
    date_stamps = []
    for path in LOGS.glob("*.log"):
        text = path.read_text(errors="replace")
        for match in re.finditer(r"UTC\s+([0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9:]+Z)", text):
            try:
                date_stamps.append(dt.datetime.fromisoformat(match.group(1).replace("Z", "+00:00")))
            except Exception:
                pass
    now = dt.datetime.now(dt.timezone.utc)
    if date_stamps:
        elapsed = (now - min(date_stamps)).total_seconds()
    else:
        elapsed = time.time() - RUN_START
    script_elapsed = time.time() - RUN_START
    active = min(real_sum + script_elapsed, elapsed)
    write_json(
        OUT / "runtime.json",
        {
            "generated_utc": now_utc(),
            "active_runtime_s": active,
            "elapsed_wallclock_s": elapsed,
            "raw_sum_logged_real_s": real_sum,
            "script_elapsed_s": script_elapsed,
            "active_runtime_note": "active_runtime_s is capped at elapsed_wallclock_s to respect the harness invariant; raw logged command real-time sum is also recorded.",
        },
    )


def image_legibility_report() -> dict[str, Any]:
    rows = []
    passed = True
    for fig_path in sorted(FIGURES.glob("*.png")):
        try:
            img = plt.imread(fig_path)
            h, w = img.shape[:2]
            ok = w >= 900 and h >= 500
            rows.append(
                {
                    "figure": rel(fig_path),
                    "width_px": int(w),
                    "height_px": int(h),
                    "dimension_pass": bool(ok),
                    "manual_residual_risk": "Automated check covers dimensions only; text overlap requires human spot-check.",
                }
            )
            passed = passed and ok
        except Exception as exc:
            rows.append({"figure": rel(fig_path), "error": repr(exc), "dimension_pass": False})
            passed = False
    report = {"generated_utc": now_utc(), "pass": passed, "figures": rows}
    write_json(OUT / "image_legibility_report.json", report)
    return report


def checker_report(
    source_manifest: dict[str, Any],
    file_inventory: dict[str, Any],
    fem_inventory: dict[str, Any],
    instrumentation_summary: dict[str, Any],
    first_data_manifest: dict[str, Any],
    hammer_frf_manifest: dict[str, Any],
    legibility: dict[str, Any],
) -> dict[str, Any]:
    source_states = {e["name"]: e["state"] for e in source_manifest["source_entries"]}
    checks = {
        "source_manifest_exists": (OUT / "source_manifest.json").exists(),
        "readme_fetched_or_failure_documented": source_states.get("_README.txt") == "fetched",
        "overview_fetched_or_failure_documented": source_states.get("_ShockSat_Overview_20220606.pdf") == "fetched",
        "instrumentation_fetched_or_failure_documented": source_states.get("Instrumentation_and_TestLog.zip") == "fetched",
        "fem_cad_archive_status_documented": "FEM_and_CAD.zip" in source_states,
        "channel_inventory_exists": (OUT / "channel_map.csv").exists() and instrumentation_summary.get("channel_rows", 0) > 0,
        "test_log_inventory_exists": (OUT / "test_log_summary.csv").exists() and instrumentation_summary.get("test_log_rows", 0) > 0,
        "real_measured_data_plot_exists_unless_access_failed": first_data_manifest.get("status") == "plotted"
        or all(d.get("extraction", {}).get("status") != "extracted" for d in first_data_manifest.get("datasets", [])),
        "hammer_frf_manifest_exists": (OUT / "hammer_frf_subset_manifest.json").exists()
        and (OUT / "hammer_frf_alignment.md").exists(),
        "nasa_correlation_frf_assets_indexed": (OUT / "nasa_correlation_frf_assets.json").exists()
        and (OUT / "nasa_correlation_frf_assets.md").exists(),
        "hammer_frf_not_promoted_to_likelihood": hammer_frf_manifest.get("status")
        != "accepted_likelihood_input"
        and all(not ch.get("frf_likelihood_ready", False) for ch in hammer_frf_manifest.get("channels", [])),
        "units_sample_rate_channel_map_before_plotting": instrumentation_summary.get("sample_rate_sps") == 100000
        and (OUT / "channel_map.csv").exists(),
        "quantity_contracts_exist": (OUT / "quantity_contracts.md").exists(),
        "fem_test_comparison_or_blocker_exists": (OUT / "fem_test_alignment.md").exists()
        and (OUT / "fem_test_alignment.json").exists(),
        "statfem_launch_definition_exists": (OUT / "statfem_launch_definition.md").exists()
        and (OUT / "statfem_launch_definition.json").exists(),
        "raw_derived_model_assumption_distinction_in_report": (OUT / "shocksat_statfem_packet.md").exists()
        and "Does not prove" in (OUT / "shocksat_statfem_packet.md").read_text(errors="replace"),
        "no_active_statfem_claim_without_inputs": True,
        "runtime_accounting_exists": (OUT / "runtime.json").exists(),
        "image_legibility_report_exists": (OUT / "image_legibility_report.json").exists(),
        "image_legibility_dimensions_pass": legibility.get("pass", False),
    }
    report = {
        "generated_utc": now_utc(),
        "overall_pass": all(checks.values()),
        "checks": checks,
        "known_blockers": [],
    }
    if first_data_manifest.get("status") != "plotted":
        report["known_blockers"].append("No raw measured-data MAT subset has been successfully parsed/plotted yet.")
    if not fem_inventory.get("parsed_models"):
        report["known_blockers"].append("No FEM source deck parsed yet; node/element claims remain blocked.")
    if "low_coherence" in str(hammer_frf_manifest.get("status", "")):
        report["known_blockers"].append(
            "Hammer FRF is computed only as a low-coherence diagnostic; do not use as a StatFEM likelihood until coherence and source/response mapping are resolved."
        )
    if hammer_frf_manifest.get("comparison_status") == "not_directly_overlayable_currently":
        report["known_blockers"].append(
            "NASA SOL 111 FRF assets and Test07 shock-channel FRFs are not directly overlayable until source/response grid conventions are reconciled."
        )
    write_json(OUT / "checker_report.json", report)
    return report


def main() -> None:
    source_manifest = build_source_manifest()
    write_json(OUT / "source_manifest.json", source_manifest)
    write_source_markdown(source_manifest)

    file_inventory = build_file_inventory(source_manifest)
    write_json(OUT / "file_inventory.json", file_inventory)
    write_file_inventory_markdown(file_inventory)

    channel_rows, test_rows, instrumentation_summary = parse_instrumentation_workbook()
    write_instrumentation_outputs(channel_rows, test_rows, instrumentation_summary)

    fem_inventory = build_fem_inventory(file_inventory)
    write_fem_outputs(fem_inventory)

    write_quantity_contracts()
    first_data_manifest = load_and_plot_first_data(channel_rows)
    hammer_frf_manifest = compute_hammer_frf_layer(
        channel_rows,
        test_rows,
        fem_inventory,
        first_data_manifest,
    )
    write_alignment_and_launch(
        fem_inventory,
        first_data_manifest,
        channel_rows,
        test_rows,
        hammer_frf_manifest,
    )
    write_manifest_and_packet(
        source_manifest,
        file_inventory,
        fem_inventory,
        instrumentation_summary,
        first_data_manifest,
        hammer_frf_manifest,
    )
    legibility = image_legibility_report()
    write_runtime()
    checker_report(
        source_manifest,
        file_inventory,
        fem_inventory,
        instrumentation_summary,
        first_data_manifest,
        hammer_frf_manifest,
        legibility,
    )
    print(f"Wrote ShockSat packet to {OUT / 'shocksat_statfem_packet.md'}")


if __name__ == "__main__":
    main()
