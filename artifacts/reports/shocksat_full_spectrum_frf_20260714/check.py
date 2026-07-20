#!/usr/bin/env python3
"""check.py — immutable checker for the ShockSat FULL-SPECTRUM FRF study (20260714).

SHA-locked (CHECKER.sha256) BEFORE any science; never edited afterward. Encodes every gate in card §9.
Statuses per the Result Status Standard: GREEN / YELLOW / RED; overall = worst gate; exits non-zero ONLY
on RED. On an empty workspace it must report RED (science not run).

Artifact interface (frozen with this file):
  out/continuity.json          {"A0_dev_P1p": f, "A1_dev_P1p": f}
  out/overlap_validation.json  {"drives": {k: {"pass","excluded","corr_median","med_abs_dlog10","reason"}},
                                "n_wide_drives": int, "blocked_reason": str?}
  out/selection_files.json     {"files": [relpaths]}  — every code path whose numbers feed a selection score
  out/spot_checks.json         {"freeze_set": [{"cid", "max_freq_err_pct"}], "pairing_frozen": bool}
  out/query_log.jsonl          lines {"track": "agent"|"random", "train_keys": [...], "fold": k, "seed"?}
  out/leakage_audit.json       {"pass": bool, "checked_files": [...], "notes": str}
  out/score_log.jsonl          dev/vault score records {"arm","stage","fold_key"?,"train_keys"?,"ts"...}
  VAULT_FREEZE.sha256 + out/vault_freeze_meta.json {"frozen_unix_ts": f}
  out/nuts_diagnostics.json    {"posteriors": [{"name","rhat_max","ess_min","div_frac"}]}
  out/arms_bands_table.json    {"arms": {arm: {band: {"mean","se"}|{"status": "not_certified"|"blocked"}}}}
  out/arm_E.json               {"spearman": f, "n_candidates": int}
  out/verdicts.json            {"S1".."S5": {"status","numbers"}, "H1".."H5": {"status","summary"}}
  out/netcg_results.json       {"shear_x","shear_y","normal_z": {"width_ratio","coverage","widen_audit"}}
  out/fig_manifest.json        {"figures": [{"file","script","data_label"}]}
  out/tufte_lint.txt, out/fig_qa.json, runtime.json, findings.md
"""
from __future__ import annotations
import hashlib, json, os, re, sys

WS = os.path.dirname(os.path.abspath(__file__))
RANK = {"GREEN": 0, "YELLOW": 1, "RED": 2}
BANDS = ["sub200", "b200_500", "b500_ceiling"]
TABLE_ARMS = ["A0", "A1", "B", "C", "D", "R", "F"]      # R = equal-budget random control
FORBIDDEN = ("lstsq", "polyfit", "curve_fit")            # per-channel/per-mode amplitude LSQ tokens


def load_json(rel):
    p = os.path.join(WS, rel)
    if not os.path.exists(p):
        return None
    with open(p) as f:
        return json.load(f)


def load_jsonl(rel):
    p = os.path.join(WS, rel)
    if not os.path.exists(p):
        return None
    out = []
    for line in open(p):
        if line.strip():
            out.append(json.loads(line))
    return out


def gate01_continuity():
    c = load_json("out/continuity.json")
    if c is None:
        return "RED", "science not run: out/continuity.json missing"
    msgs = []
    a0, a1 = c.get("A0_dev_P1p"), c.get("A1_dev_P1p")
    if a0 is None or abs(a0 - 0.1969) > 0.002:
        return "RED", f"A0 HARD GATE fail: dev P1'={a0} vs 0.1969±0.002"
    msgs.append(f"A0={a0:.4f} in 0.1969±0.002")
    if a1 is None or abs(a1 - 0.2371) > 0.005:
        return "RED", f"A1 continuity fail: dev P1'={a1} vs 0.2371±0.005"
    msgs.append(f"A1={a1:.4f} in 0.2371±0.005")
    return "GREEN", "; ".join(msgs)


def gate02_overlap():
    v = load_json("out/overlap_validation.json")
    if v is None:
        return "RED", "science not run: out/overlap_validation.json missing"
    if v.get("n_wide_drives", 0) == 0:
        if v.get("blocked_reason"):
            return "YELLOW", f"no wide drives; documented: {v['blocked_reason']}"
        return "RED", "n_wide_drives=0 with no blocked_reason"
    bad = []
    for k, d in v.get("drives", {}).items():
        if d.get("pass"):
            if d.get("corr_median", 0) < 0.999 or d.get("med_abs_dlog10", 1) > 0.01:
                bad.append(f"{k}: pass claimed but numbers miss (corr {d.get('corr_median')}, "
                           f"dlog {d.get('med_abs_dlog10')})")
        elif d.get("excluded") and d.get("reason"):
            continue
        else:
            bad.append(f"{k}: neither passed nor excluded-with-reason")
    if bad:
        return "RED", "; ".join(bad)
    n_pass = sum(1 for d in v["drives"].values() if d.get("pass"))
    n_excl = sum(1 for d in v["drives"].values() if d.get("excluded"))
    st = "GREEN" if n_excl == 0 else "YELLOW"
    return st, f"{n_pass} wide drives validated (corr>=0.999, med|dlog10|<=0.01); {n_excl} excluded+reported"


def gate03_no_amplitude_lsq():
    sf = load_json("out/selection_files.json")
    if sf is None:
        return "RED", "science not run: out/selection_files.json missing"
    hits, warn = [], []
    for rel in sf.get("files", []):
        p = os.path.join(WS, rel)
        if not os.path.exists(p):
            hits.append(f"{rel}: listed but missing")
            continue
        for i, line in enumerate(open(p, errors="replace"), 1):
            if any(t in line for t in FORBIDDEN) and "CHECKER-OK" not in line:
                hits.append(f"{rel}:{i}: {line.strip()[:80]}")
    code_dir = os.path.join(WS, "code")
    listed = {os.path.normpath(f) for f in sf.get("files", [])}
    if os.path.isdir(code_dir):
        for fn in sorted(os.listdir(code_dir)):
            if not fn.endswith(".py"):
                continue
            rel = os.path.normpath(os.path.join("code", fn))
            if rel in listed:
                continue
            for i, line in enumerate(open(os.path.join(code_dir, fn), errors="replace"), 1):
                if any(t in line for t in FORBIDDEN) and "CHECKER-OK" not in line:
                    warn.append(f"{rel}:{i} (non-selection)")
    if hits:
        return "RED", "forbidden amplitude-LSQ token in selection score path: " + "; ".join(hits[:5])
    if warn:
        return "YELLOW", "LSQ tokens outside selection paths (review): " + "; ".join(warn[:5])
    return "GREEN", f"{len(sf.get('files', []))} selection files clean (one global gain per fold only)"


def gate04_exact_basis():
    s = load_json("out/spot_checks.json")
    if s is None:
        return "RED", "science not run: out/spot_checks.json missing"
    if not s.get("pairing_frozen"):
        return "RED", "pairing_frozen flag not set"
    fs = s.get("freeze_set", [])
    if not fs:
        return "RED", "empty freeze_set"
    bad = [f"{r['cid']}: {r['max_freq_err_pct']:.3f}%" for r in fs
           if r.get("max_freq_err_pct", 99) > 0.3]
    if bad:
        return "RED", "exact-basis spot check >0.3%: " + "; ".join(bad)
    worst = max(r["max_freq_err_pct"] for r in fs)
    return "GREEN", f"{len(fs)} freeze-set candidates spot-checked, worst {worst:.3f}% <= 0.3%"


def gate05_budgets():
    q = load_jsonl("out/query_log.jsonl")
    if q is None:
        return "RED", "science not run: out/query_log.jsonl missing"
    n_agent = sum(1 for r in q if r.get("track") == "agent")
    n_rand = sum(1 for r in q if r.get("track") == "random")
    if n_agent > 80 or n_rand > 80:
        return "RED", f"budget exceeded: agent {n_agent}/80, random {n_rand}/80"
    if n_rand and not all("seed" in r for r in q if r.get("track") == "random"):
        return "RED", "random-control queries missing seed"
    if n_agent == 0 or n_rand == 0:
        return "RED", f"missing track records (agent {n_agent}, random {n_rand})"
    return "GREEN", f"agent {n_agent}/80, random {n_rand}/80, random seeded"


def gate06_leakage():
    a = load_json("out/leakage_audit.json")
    if a is None:
        return "RED", "science not run: out/leakage_audit.json missing"
    if not a.get("pass"):
        return "RED", f"leakage audit failed: {a.get('notes')}"
    bad = []
    for rel in ("out/query_log.jsonl", "out/score_log.jsonl"):
        recs = load_jsonl(rel) or []
        for r in recs:
            fold, tks = r.get("fold") or r.get("fold_key"), r.get("train_keys")
            if fold and tks and fold in tks:
                bad.append(f"{rel}: fold {fold} in its own train_keys")
    if bad:
        return "RED", "; ".join(bad[:3])
    return "GREEN", f"leakage audit pass ({len(a.get('checked_files', []))} files); fold/train_keys consistent"


def gate07_vault():
    if not os.path.exists(os.path.join(WS, "VAULT_FREEZE.sha256")):
        return "RED", "VAULT_FREEZE.sha256 missing"
    meta = load_json("out/vault_freeze_meta.json")
    if meta is None or "frozen_unix_ts" not in meta:
        return "RED", "out/vault_freeze_meta.json missing/incomplete"
    recs = load_jsonl("out/score_log.jsonl") or []
    vrecs = [r for r in recs if r.get("stage") == "vault"]
    if not vrecs:
        return "RED", "no vault grade recorded (science not run)"
    arms = [r.get("arm") for r in vrecs]
    if len(arms) != len(set(arms)):
        return "RED", f"an arm graded on the vault more than once: {arms}"
    early = [r["arm"] for r in vrecs if r.get("unix_ts", 0) < meta["frozen_unix_ts"]]
    if early:
        return "RED", f"vault read before freeze: {early}"
    unlabeled = [r["arm"] for r in vrecs if "third program read" not in str(r.get("note", "")).lower()]
    if unlabeled:
        return "RED", f"vault records missing the honest third-program-read label: {unlabeled}"
    return "GREEN", f"{len(vrecs)} arms vault-graded once each, post-freeze, labeled third program read"


def gate08_nuts():
    d = load_json("out/nuts_diagnostics.json")
    if d is None or not d.get("posteriors"):
        return "RED", "science not run: out/nuts_diagnostics.json missing/empty"
    worst, yellow = [], []
    for p in d["posteriors"]:
        ok = (p.get("rhat_max", 9) <= 1.05 and p.get("ess_min", 0) >= 200
              and p.get("div_frac", 1) < 0.02)
        if not ok:
            yellow.append(f"{p['name']}: rhat {p.get('rhat_max')}, ess {p.get('ess_min')}, "
                          f"div {p.get('div_frac')}")
        worst.append(p.get("rhat_max", 9))
    if yellow:
        return "YELLOW", "non-converged posterior(s), intervals not-trustworthy: " + "; ".join(yellow[:4])
    return "GREEN", f"{len(d['posteriors'])} posteriors converged (worst R-hat {max(worst):.4f})"


def gate09_results():
    t = load_json("out/arms_bands_table.json")
    if t is None:
        return "RED", "science not run: out/arms_bands_table.json missing"
    bad = []
    for arm in TABLE_ARMS:
        cell = t.get("arms", {}).get(arm)
        if cell is None:
            bad.append(f"arm {arm} missing from bands table")
            continue
        for b in BANDS:
            e = cell.get(b)
            if e is None:
                bad.append(f"{arm}/{b} missing")
            elif "mean" not in e and e.get("status") not in ("not_certified", "blocked"):
                bad.append(f"{arm}/{b} has neither numbers nor a documented status")
    e = load_json("out/arm_E.json")
    if e is None or "spearman" not in e:
        bad.append("out/arm_E.json missing spearman")
    v = load_json("out/verdicts.json")
    if v is None:
        bad.append("out/verdicts.json missing")
    else:
        for k in ["S1", "S2", "S3", "S4", "S5", "H1", "H2", "H3", "H4", "H5"]:
            if k not in v or v[k].get("status") not in RANK:
                bad.append(f"verdicts.json missing/invalid {k}")
    n = load_json("out/netcg_results.json")
    if n is None:
        bad.append("out/netcg_results.json missing")
    else:
        for q in ["shear_x", "shear_y", "normal_z"]:
            if q not in n or not all(x in n[q] for x in ("width_ratio", "coverage", "widen_audit")):
                bad.append(f"netcg_results missing {q} fields")
    fp = os.path.join(WS, "findings.md")
    if not os.path.exists(fp):
        bad.append("findings.md missing")
    else:
        txt = open(fp).read()
        for h in ["H1", "H2", "H3", "H4", "H5"]:
            if not re.search(rf"\b{h}\b.*(GREEN|YELLOW|RED)", txt):
                bad.append(f"findings.md lacks an explicit statused {h} verdict")
    if bad:
        return "RED", "; ".join(bad[:8])
    return "GREEN", "bands table complete for all arms; S/H verdicts + netcg + findings present"


def gate10_figures():
    m = load_json("out/fig_manifest.json")
    if m is None or len(m.get("figures", [])) < 6:
        return "RED", "science not run: fig_manifest missing or <6 figures"
    bad = []
    for fg in m["figures"]:
        if not os.path.exists(os.path.join(WS, fg.get("file", ""))):
            bad.append(f"figure {fg.get('file')} missing")
        sc = fg.get("script", "")
        if not sc.endswith(".py") or not os.path.exists(os.path.join(WS, sc)):
            bad.append(f"{fg.get('file')}: no saved .py script")
        if not fg.get("data_label"):
            bad.append(f"{fg.get('file')}: no run/dataset label recorded")
    lint = os.path.join(WS, "out", "tufte_lint.txt")
    if not os.path.exists(lint):
        bad.append("out/tufte_lint.txt missing")
    qa = load_json("out/fig_qa.json")
    if qa is None:
        bad.append("out/fig_qa.json missing")
    elif not all(r.get("pass") for r in qa.get("figures", [])):
        fails = [r["file"] for r in qa.get("figures", []) if not r.get("pass")]
        bad.append(f"legibility QA fail: {fails}")
    if bad:
        return "RED", "; ".join(bad[:6])
    return "GREEN", f"{len(m['figures'])} figures scripted, labeled, linted, QA-passed"


def gate11_runtime():
    r = load_json("runtime.json")
    if r is None:
        return "RED", "runtime.json missing"
    a, e = r.get("active_runtime_s"), r.get("elapsed_wallclock_s")
    if a is None or e is None or a > e:
        return "RED", f"runtime fields invalid (active {a}, elapsed {e})"
    return "GREEN", f"active {a:.0f}s <= elapsed {e:.0f}s"


def gate12_self_sha():
    lock = os.path.join(WS, "CHECKER.sha256")
    if not os.path.exists(lock):
        return "RED", "CHECKER.sha256 missing (checker not locked)"
    want = open(lock).read().split()[0]
    have = hashlib.sha256(open(os.path.abspath(__file__), "rb").read()).hexdigest()
    if want != have:
        return "RED", "check.py MODIFIED after lock"
    return "GREEN", f"check.py sha256 {have[:12]}... matches lock"


GATES = [("G01_continuity_bars", gate01_continuity), ("G02_wide_cache_overlap", gate02_overlap),
         ("G03_no_amplitude_lsq_in_selection", gate03_no_amplitude_lsq),
         ("G04_frozen_pairing_exact_basis", gate04_exact_basis), ("G05_query_budgets", gate05_budgets),
         ("G06_fold_leakage", gate06_leakage), ("G07_vault_discipline", gate07_vault),
         ("G08_nuts_convergence", gate08_nuts), ("G09_results_and_verdicts", gate09_results),
         ("G10_figures", gate10_figures), ("G11_runtime", gate11_runtime),
         ("G12_checker_immutable", gate12_self_sha)]


def main():
    report, overall = {}, "GREEN"
    for name, fn in GATES:
        try:
            st, detail = fn()
        except Exception as e:                                     # a crashing gate is RED, never a skip
            st, detail = "RED", f"gate crashed: {type(e).__name__}: {e}"
        report[name] = {"status": st, "detail": detail}
        if RANK[st] > RANK[overall]:
            overall = st
        print(f"[{st:6s}] {name}: {detail}")
    report["OVERALL"] = overall
    with open(os.path.join(WS, "checker_report.json"), "w") as f:
        json.dump(report, f, indent=1)
    print(f"\nOVERALL: {overall}")
    sys.exit(1 if overall == "RED" else 0)


if __name__ == "__main__":
    main()
