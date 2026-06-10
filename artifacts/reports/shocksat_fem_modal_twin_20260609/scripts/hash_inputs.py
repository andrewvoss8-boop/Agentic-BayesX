#!/usr/bin/env python3
"""Hash the read-only inputs. `python hash_inputs.py end` writes
inputs_sha256_end.json over the SAME file list captured at start, so the
checker can prove no input was modified during the run.
"""
import datetime
import hashlib
import json
import os
import sys


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def _h(v):  # accept either {"sha256":..} or a plain hash string (D30)
    return v["sha256"] if isinstance(v, dict) else v


which = sys.argv[1] if len(sys.argv) > 1 else "end"
start = json.load(open("inputs_sha256_start.json"))
files = sorted(start["files"])
# D30: emit the SAME {sha256, bytes} schema as inputs_sha256_start.json so the
# checker's start==end is a TRUE content comparison, not a dict-vs-string fail.
out = dict(hashed_at=datetime.datetime.now().isoformat(timespec="seconds"),
           files={p: {"sha256": sha256(p), "bytes": os.path.getsize(p)}
                  for p in files})
json.dump(out, open(f"inputs_sha256_{which}.json", "w"), indent=1)
changed = [p for p in files if _h(out["files"][p]) != _h(start["files"][p])]
print(f"hashed {len(files)} inputs -> inputs_sha256_{which}.json; "
      f"{len(changed)} changed")
if changed:
    for p in changed:
        print("  CHANGED:", p)
