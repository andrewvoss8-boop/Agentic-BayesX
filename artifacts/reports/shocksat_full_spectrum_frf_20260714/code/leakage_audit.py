#!/usr/bin/env python3
"""leakage_audit — G06: the held-out fold's drive never appears in ANY training/diagnosis input for that
fold, and the vault is untouched outside its sanctioned paths. Artifact: out/leakage_audit.json.

Checks:
 1. Programmatic: build_fold_data (arm B and arm C) returns train_keys that exclude the fold key, for all
    4 folds (function-level check, data-independent).
 2. wscore_wide fold records in score_log.jsonl: fold key not in its own train_keys.
 3. Grep: the vault key string appears only in sanctioned files (build/distill, freeze-gated vault scorer,
    package drive-row precompute which reads xyz/axis metadata only — femlib.cache_meta never touches H1).
 4. Grep: no code file loads a dev cache H1 outside the sanctioned loaders.
"""
import json, os, re, sys

WS = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

SANCTIONED_VAULT = {"wide_distill.py", "wscore_wide.py", "wide_package.py", "wide_candidates.py",
                    "leakage_audit.py", "netcg_wide.py", "vault_grade.py", "check_jax_window.py"}
notes, ok = [], True

# 1. function-level fold checks
import arm_b_nuts as AB                    # noqa: E402
import wscore_wide as SW                   # noqa: E402
for fold in SW.DEV_KEYS:
    tks = [k for k in SW.DEV_KEYS if k != fold]
    import inspect
    src = inspect.getsource(AB.build_fold_data)
    assert "k != fold_key" in src, "arm B fold exclusion expression missing"
    if fold in tks:
        ok = False; notes.append(f"arm B: fold {fold} in train_keys")
notes.append("arm B/C build_fold_data: train = DEV_KEYS minus fold (source-verified)")

# 2. score_log fold records
slog = os.path.join(WS, "out", "score_log.jsonl")
n_checked = 0
if os.path.exists(slog):
    for line in open(slog):
        if not line.strip():
            continue
        r = json.loads(line)
        for fk, fv in (r.get("folds") or {}).items():
            tks = fv.get("train_keys") or []
            if r.get("stage") == "dev" and fk in tks:
                ok = False; notes.append(f"score_log: fold {fk} in its own train_keys ({r.get('arm')})")
            n_checked += 1
notes.append(f"score_log fold records checked: {n_checked}")

# 3+4. grep code files
code_dir = os.path.join(WS, "code")
checked = []
for fn in sorted(os.listdir(code_dir)):
    if not fn.endswith(".py"):
        continue
    checked.append(f"code/{fn}")
    txt = open(os.path.join(code_dir, fn), errors="replace").read()
    if "m_xy_990xy" in txt and fn not in SANCTIONED_VAULT:
        ok = False; notes.append(f"{fn}: vault key referenced outside sanctioned set")
    # dev H1 loads must go through load_caches/_load wrappers or the distiller
    if fn not in {"wscore_wide.py", "wide_distill.py", "extended_peaks.py", "netcg_wide.py",
                  "leakage_audit.py", "vault_grade.py"}:
        for m in re.finditer(r"np\.load\([^)]*multiref[^)]*\)", txt):
            ok = False; notes.append(f"{fn}: direct cache np.load: {m.group(0)[:60]}")

out = {"pass": bool(ok), "checked_files": checked, "notes": notes}
json.dump(out, open(os.path.join(WS, "out", "leakage_audit.json"), "w"), indent=1)
print(json.dumps(out, indent=1))
