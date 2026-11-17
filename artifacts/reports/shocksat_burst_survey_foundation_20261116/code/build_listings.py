#!/usr/bin/env python3
"""Build exact member listings and a tiered byte-range fetch plan for the NASA
ShockSat archives, using only the archive TAILS captured on 2026-06-09.

No NASA host is contacted. Inputs are the last bytes of each archive (the ZIP
"central directory", i.e. the table of contents). The 4 MiB tails were fetched by
the June runner (logs/large_file_tail_range_listing_attempts.log) and survive only
in the private disk backup; the directory-only slices cut from them are stored
here in data/zip_tails/ so this script replays from the repository alone.

Usage:
  build_listings.py                 replay from data/zip_tails/*.cd_tail.bin
  build_listings.py --tails-dir D   (re)cut the slices from the 4 MiB tails in D first

Outputs (all under out/):
  zip_listings/<archive>.json   every member: name, sizes, CRC-32, byte offset
  zip_directory_summary.json    integrity checks and cross-checks against June records
  fetch_plan.json               tiered byte ranges for the gated download
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
WS = os.path.dirname(HERE)
REPO = os.path.abspath(os.path.join(WS, "..", "..", ".."))
sys.path.insert(0, HERE)
import zipdir      # noqa: E402
import zipfetch    # noqa: E402

JUNE = os.path.join(REPO, "artifacts", "reports", "shocksat_statfem_runner_20260609")
BASE_URL = "https://mediaex-server.larc.nasa.gov/shocksat/"
ARCHIVES = {
    # archive name -> path below BASE_URL
    "FEM_and_CAD.zip": "FEM_and_CAD.zip",
    "Test07_ImpactHammer_990x.zip": "Test_Data_Impact/Test07_ImpactHammer_990x.zip",
    "Test08_ImpactHammer_990z.zip": "Test_Data_Impact/Test08_ImpactHammer_990z.zip",
    "Test_Data_Pyro_NSI_NSD.zip": "Test_Data_Pyro_NSI_NSD.zip",
    "Test_Data_Parametric.zip": "Test_Data_Parametric.zip",
    "Test_Data_Pyro_Frangible_Joints.zip": "Test_Data_Pyro_Frangible_Joints.zip",
}

# Download tiers for FEM_and_CAD.zip, smallest and most informative first.
# Each tier is (key, plain-English purpose, regex that selects members).
CORR = r"^FEM/Correlation/"
MT = CORR + r"Modal_Test_Data_Use_in_Correlation2021/"
TIERS = [
    ("tier0_documents_and_shapes",
     "Test log, test reports, mode-shape summaries, all five shape files, display models and run decks. "
     "Answers what each run is (channels, sample rate, shaker blocks) before any large download.",
     r"(" + MT + r".*\.(xlsx|docx|ash|blk|dat)$)|(" + CORR + r"Test_Mode_Shapes/.*)|(" + CORR + r"ShockSat_TAM_101521\.dat$)"),
    ("tier1_plans_and_reduced_models",
     "Modal test plan, fixed-base data review deck, reduced test-analysis models and the fixed-base solver listing.",
     MT + r".*\.(pptx|pch|f06)$"),
    ("tier2_burst_frf_file",
     "Frequency response functions computed by the test team for free-free burst-random run 78.",
     MT + r".*\.afu$"),
    ("tier3_burst_time_histories",
     "Raw burst-random time histories: runs 78 and 99 (free-free, two force levels) and run 139 (fixed base).",
     MT + r".*\.ati$"),
    ("tier4_frf_verification_plots",
     "NASA's own test-versus-FEM FRF plots (impact tests, no shaker blocks) and the FEM FRF punch files.",
     CORR + r"FRF_Verification/"),
    ("tier5_shape_animations_optional",
     "Animated test mode shapes for runs 78 and 139. Optional; the file names alone give rounded mode frequencies.",
     MT + r".*\.gif$"),
]
NOT_PLANNED = {
    "modal_test_pictures": CORR + r"Modal_Test_Pictures/",
    "fixed_base_op2": MT + r".*\.op2$",
    "summary_deck_already_in_hand": CORR + r"Final_Summary_Documentation_101521_rev1\.pptx$",
    "root_spreadsheets_already_in_hand": CORR + r"(Instrumentation_locations|ShockSat_measured_weights)\.xlsx$",
}


def sha256(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def june_sizes() -> dict:
    """Archive sizes (bytes) from the content-length lines the June runner logged."""
    path = os.path.join(JUNE, "logs", "large_file_header_range_probes.log")
    out, cur = {}, None
    for line in open(path, errors="replace"):
        m = re.match(r"==== LARGE PROBE (\S+)", line)
        if m:
            cur = m.group(1)
        m = re.match(r"content-length: (\d+)", line.strip())
        if m and cur and cur not in out:
            out[cur] = int(m.group(1))
    return out


def june_tail_sha() -> dict:
    """SHA-256 of each 4 MiB tail as printed by the June runner (where it printed one)."""
    path = os.path.join(JUNE, "logs", "large_file_tail_range_listing_attempts.log")
    out = {}
    for line in open(path, errors="replace"):
        m = re.match(r"([0-9a-f]{64})\s+\S*range_(\S+)\.tail_4MiB\.bin", line.strip())
        if m:
            out[m.group(2)] = m.group(1)
    return out


def cut_slices(tails_dir: str, sizes: dict) -> dict:
    """Cut the directory-only slice out of each 4 MiB tail and record provenance."""
    os.makedirs(os.path.join(WS, "data", "zip_tails"), exist_ok=True)
    prov = {}
    for name, size in sizes.items():
        src = os.path.join(tails_dir, f"range_{name}.tail_4MiB.bin")
        raw = open(src, "rb").read()
        d = zipdir.parse_tail(raw, size)
        keep = size - d.cd_offset                     # directory + end records
        sl = raw[-keep:]
        dst = os.path.join(WS, "data", "zip_tails", f"{name}.cd_tail.bin")
        open(dst, "wb").write(sl)
        prov[name] = {"tail_4MiB_sha256": sha256(raw), "tail_4MiB_bytes": len(raw),
                      "slice_bytes": len(sl), "slice_sha256": sha256(sl),
                      "slice_is_suffix_of_tail": raw.endswith(sl)}
    json.dump(prov, open(os.path.join(WS, "data", "zip_tails", "PROVENANCE.json"), "w"), indent=1)
    return prov


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--tails-dir")
    a = ap.parse_args()
    sizes = {k: v for k, v in june_sizes().items() if k in ARCHIVES}
    missing = sorted(set(ARCHIVES) - set(sizes))
    if missing:
        print("no logged size for", missing, file=sys.stderr)
        return 1
    if a.tails_dir:
        cut_slices(a.tails_dir, sizes)
    prov = json.load(open(os.path.join(WS, "data", "zip_tails", "PROVENANCE.json")))
    june_sha = june_tail_sha()
    inv = json.load(open(os.path.join(JUNE, "file_inventory.json")))
    june_arch = {os.path.basename(x["archive"]): x for x in inv["archives"]}

    os.makedirs(os.path.join(WS, "out", "zip_listings"), exist_ok=True)
    summary = {"base_url": BASE_URL, "archives": {}}
    dirs = {}
    for name, size in sizes.items():
        sl = open(os.path.join(WS, "data", "zip_tails", f"{name}.cd_tail.bin"), "rb").read()
        d = zipdir.parse_tail(sl, size)
        dirs[name] = d
        c = zipdir.consistency(d)
        rec = {
            "url": BASE_URL + ARCHIVES[name],
            "size_bytes_logged_2026_06_09": size,
            "size_bytes_inferred_from_tail": zipdir.infer_total_size(sl),
            "slice_sha256": sha256(sl),
            "slice_sha256_matches_provenance": sha256(sl) == prov[name]["slice_sha256"],
            "tail_4MiB_sha256": prov[name]["tail_4MiB_sha256"],
            "tail_4MiB_sha256_logged_2026_06_09": june_sha.get(name),
            "consistency": c,
        }
        j = june_arch.get(name)
        if j and j.get("entry_count"):
            by = {e.name: e for e in d.entries}
            mism = [s["name"] for s in j["entries_sample"]
                    if s["name"] not in by
                    or by[s["name"]].usize != s["uncompressed_size"]
                    or by[s["name"]].csize != s["compressed_size"]]
            rec["june_full_zip_crosscheck"] = {
                "entry_count_june": j["entry_count"], "entry_count_here": d.n_entries,
                "total_uncompressed_june": j["total_uncompressed_size_bytes"],
                "total_uncompressed_here": c["sum_usize"],
                "entries_compared": len(j["entries_sample"]), "entries_mismatched": len(mism),
            }
        summary["archives"][name] = rec
        json.dump({"archive": name, "url": rec["url"], "size_bytes": size,
                   "members": [e.to_json() for e in sorted(d.entries, key=lambda e: e.lho)]},
                  open(os.path.join(WS, "out", "zip_listings", name + ".json"), "w"), indent=0)
    json.dump(summary, open(os.path.join(WS, "out", "zip_directory_summary.json"), "w"), indent=1)

    # ---- fetch plan for FEM_and_CAD.zip
    d = dirs["FEM_and_CAD.zip"]
    plan = {"url": BASE_URL + ARCHIVES["FEM_and_CAD.zip"], "archive_size": d.total_size, "tiers": [], "not_planned": {}}
    seen = set()
    for key, purpose, rx in TIERS:
        es = [e for e in zipfetch.select(d, rx) if e.name not in seen]
        seen.update(e.name for e in es)
        p = zipfetch.plan(d, es)
        plan["tiers"].append({"tier": key, "purpose": purpose, "regex": rx, "n_members": p["n_members"],
                              "compressed_bytes": p["compressed_bytes"], "uncompressed_bytes": p["uncompressed_bytes"],
                              "contiguous_runs": p["contiguous_runs"],
                              "members": [{"name": m["name"], "csize": m["csize"], "usize": m["usize"],
                                           "lho": m["lho"], "crc32": m["crc32"]} for m in p["members"]]})
    for key, rx in NOT_PLANNED.items():
        es = zipfetch.select(d, rx)
        plan["not_planned"][key] = {"regex": rx, "n_members": len(es), "compressed_bytes": sum(e.csize for e in es)}
    corr = zipfetch.select(d, CORR)
    plan["correlation_folder_total"] = {"n_members": len(corr), "compressed_bytes": sum(e.csize for e in corr),
                                        "uncompressed_bytes": sum(e.usize for e in corr)}
    plan["planned_total"] = {"n_members": sum(t["n_members"] for t in plan["tiers"]),
                             "compressed_bytes": sum(t["compressed_bytes"] for t in plan["tiers"]),
                             "uncompressed_bytes": sum(t["uncompressed_bytes"] for t in plan["tiers"])}
    # Every Correlation member must be either planned or explicitly not planned.
    unplanned = [e.name for e in corr if e.name not in seen
                 and not any(re.search(rx, e.name) for rx in NOT_PLANNED.values())]
    plan["correlation_members_unaccounted"] = unplanned

    # ---- torque-sweep archive: one row per torque level
    dp = dirs["Test_Data_Parametric.zip"]
    levels = {}
    for e in dp.files():
        m = re.search(r"Parametric_990x_(\d+)ip(\d+)_", e.name)
        if m:
            lv = levels.setdefault(int(m.group(1)), {"n_files": 0, "compressed_bytes": 0, "uncompressed_bytes": 0, "hits": []})
            lv["n_files"] += 1; lv["compressed_bytes"] += e.csize; lv["uncompressed_bytes"] += e.usize
            lv["hits"].append(int(m.group(2)))
    plan["torque_sweep_archive"] = {
        "url": BASE_URL + ARCHIVES["Test_Data_Parametric.zip"], "archive_size": dp.total_size,
        "n_files": len(dp.files()), "levels_in_lb": {str(k): v for k, v in sorted(levels.items())},
        "note": "Level label read from the file name (e.g. 025ip). NASA's test log sheet TestLog_Parametric "
                "states 'Name shows bolted joint torque'. The unit in-lb is an interpretation of 'ip'.",
    }
    json.dump(plan, open(os.path.join(WS, "out", "fetch_plan.json"), "w"), indent=1)

    for t in plan["tiers"]:
        print(f"{t['tier']:34} {t['n_members']:>4} files {t['compressed_bytes']/1e6:>8.2f} MB compressed "
              f"{t['uncompressed_bytes']/1e6:>8.2f} MB unpacked  runs={len(t['contiguous_runs'])}")
    print("planned total", plan["planned_total"], "| Correlation folder", plan["correlation_folder_total"],
          "| unaccounted", len(unplanned))
    print("torque levels", {k: (v["n_files"], sorted(v["hits"])) for k, v in plan["torque_sweep_archive"]["levels_in_lb"].items()})
    return 0


if __name__ == "__main__":
    sys.exit(main())
