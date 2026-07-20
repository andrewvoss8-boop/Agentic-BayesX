#!/usr/bin/env python3
"""check.py — IMMUTABLE checker for the EXACT-EVIDENCE COMPLETION card (20260716).

Written and SHA-locked BEFORE any science was run (run once on the empty workspace: must be RED
"science not run"). Never edited afterwards. Exits non-zero ONLY on RED (AGENTS Result Status Standard:
GREEN/YELLOW/RED; documented YELLOW does not abort replay).

It encodes the D17 lessons the ORIGINAL study's checker missed (review findings C1/C6/C8):
  G05  every reported statistic is asserted FINITE — a JSON null / NaN / Inf anywhere in
       out/verdicts_final.json is RED (the original G09 validated key-presence, not finiteness, and shipped
       NaN S1/S2).
  G04  T1 fold-MAP provenance — fold k's MAP must record train_keys EXCLUDING drive k, and the 4 folds must
       use 4 DISTINCT MAP files (the original reused fold-1's MAP for all 4 folds -> 3/4 folds leaked).
  G06  T2 completeness — exactly 28 candidates carry an exact score or an excluded-with-reason record
       (the original exact-rescored only the 2 screening winners).
  G07  S2 reported under BOTH selection conventions + pipeline reproduction of the study's exact D/R scores.
  G08  figures scripted (.py) + linted + legibility-QA'd, and no F=R row.
  G02  no file writes outside this workspace; the read-only workspaces are hash-verified unchanged.
  G10  runtime.json (active <= elapsed).
  G12  checker self-SHA.

Gates: G01 pre-registration | G02 isolation/integrity | G03 no-per-mode-LSQ | G04 arm-C exact (T1) |
       G05 verdicts finiteness (T3) | G06 exact re-rank completeness (T2) | G07 S2 both conventions (T2) |
       G08 figures | G09 sampler/labeling honesty | G10 runtime | G11 continuity | G12 checker self-SHA
"""
from __future__ import annotations
import hashlib, json, math, os, re, sys

WS = os.path.dirname(os.path.abspath(__file__))
RANK = {"GREEN": 0, "YELLOW": 1, "RED": 2}
DEV_KEYS = ["m_xpos_990x", "m_zpos_990z", "m_ypos_990y", "m_zpos_900z"]
BANDS = ["sub200", "b200_500"]
FORBIDDEN = ("lstsq", "polyfit", "curve_fit")          # per-channel/per-mode amplitude LSQ tokens
# read-only workspaces this card may IMPORT/READ but must never WRITE into:
RO_WS = ("shocksat_full_spectrum_frf_20260714", "shocksat_fullspec_review_gpt56_20260716",
         "shocksat_full_spectrum_frf_repair_20260716", "shocksat_true_remodel_loop_20260706",
         "shocksat_frf_damping_updating_20260710")
WRITE_TOK = ("open(", "savez", "savetxt", "np.save", "json.dump", "savefig", "to_csv", "mkdir", "makedirs",
             "shutil.copy", "shutil.move", "os.remove", "unlink", "rmtree")
# the study's exact-basis freeze numbers this card's pipeline must reproduce (out/exact_freeze_scores.json)
STUDY_EXACT = {"D": 0.16344, "R": 0.16506}             # sub-200 exact fold-means, tol 0.01
STUDY_S2_A = -0.0017163324443401767                    # repair S2 (screening-selected winners, exact-scored)


def load_json(rel):
    p = os.path.join(WS, rel)
    if not os.path.exists(p):
        return None
    try:
        with open(p) as f:
            return json.load(f)
    except Exception:
        return "PARSE_ERROR"


def load_jsonl(rel):
    p = os.path.join(WS, rel)
    if not os.path.exists(p):
        return None
    out = []
    with open(p) as f:
        for line in f:
            if line.strip():
                try:
                    out.append(json.loads(line))
                except Exception:
                    return "PARSE_ERROR"
    return out


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def my_code_files():
    out = []
    cd = os.path.join(WS, "code")
    if os.path.isdir(cd):
        for fn in sorted(os.listdir(cd)):
            if fn.endswith(".py"):
                out.append(os.path.join(cd, fn))
    return out


def walk_numbers(obj, path=""):
    """Yield (path, value) for every scalar leaf. Used for the finiteness gate."""
    if isinstance(obj, dict):
        for k, v in obj.items():
            yield from walk_numbers(v, f"{path}.{k}")
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            yield from walk_numbers(v, f"{path}[{i}]")
    else:
        yield path, obj


# ------------------------------------------------------------------ G01 pre-registration
def gate01_prereg():
    bad = []
    for f in ("priority_deliverables.md", "question_framing.md", "decisions_log.md", "CHECKER.sha256"):
        if not os.path.exists(os.path.join(WS, f)):
            bad.append(f"{f} missing")
    dl = os.path.join(WS, "decisions_log.md")
    if os.path.exists(dl):
        t = open(dl).read()
        if "D0" not in t:
            bad.append("decisions_log.md has no D0 re-grounding entry")
        if "Sampler Decision" not in t and "SAMPLER DECISION" not in t:
            bad.append("decisions_log.md states no Sampler Decision (AGENTS Sampler Decision gate)")
    qf = os.path.join(WS, "question_framing.md")
    if os.path.exists(qf):
        t = open(qf).read()
        if not re.search(r"Q1", t) or not re.search(r"Q2", t):
            bad.append("question_framing.md does not pre-register both Q1 and Q2")
    if bad:
        return "RED", "; ".join(bad[:5])
    return "GREEN", "pre-registration present (priorities, Q1/Q2 framing, D0 + sampler decision, checker lock)"


# ------------------------------------------------------------------ G02 isolation + integrity
def gate02_isolation():
    bad = []
    for p in my_code_files() + [os.path.join(WS, "check.py")]:
        for i, line in enumerate(open(p).read().splitlines(), 1):
            s = line.split("#")[0]
            if any(w in s for w in RO_WS) and any(t in s for t in WRITE_TOK):
                if re.search(r'open\([^)]*,\s*["\'](?:r|rb)["\']', s) or 'open(' in s and '"w"' not in s \
                        and "'w'" not in s and '"a"' not in s and "'a'" not in s and 'savez' not in s \
                        and 'json.dump' not in s and 'savefig' not in s and 'np.save' not in s:
                    continue
                bad.append(f"{os.path.basename(p)}:{i} write into read-only workspace")
    lock = os.path.join(WS, "REUSED_code.sha256")
    if not os.path.exists(lock):
        bad.append("REUSED_code.sha256 missing (reused read-only code not hashed)")
    else:
        n_ok, n_bad = 0, []
        for line in open(lock):
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            try:
                dig, rel = line.split(None, 1)
            except ValueError:
                continue
            ap = os.path.abspath(os.path.join(WS, "..", "..", "..", rel.strip()))
            if not os.path.exists(ap):
                n_bad.append(f"{rel} vanished")
            elif sha256(ap) != dig:
                n_bad.append(f"{rel} MODIFIED")
            else:
                n_ok += 1
        if n_bad:
            bad.append(f"read-only inputs changed: {n_bad[:3]}")
        elif n_ok == 0:
            bad.append("REUSED_code.sha256 hashes nothing")
    if bad:
        return "RED", "; ".join(bad[:5])
    return "GREEN", "no writes into read-only workspaces; all reused read-only inputs hash-verified unchanged"


# ------------------------------------------------------------------ G03 no per-channel/per-mode LSQ
def gate03_no_lsq():
    hits = []
    for p in my_code_files():
        for i, line in enumerate(open(p).read().splitlines(), 1):
            s = line.split("#")[0]
            for tok in FORBIDDEN:
                if tok in s:
                    hits.append(f"{os.path.basename(p)}:{i} {tok}")
    if hits:
        return "RED", f"per-channel/per-mode amplitude LSQ tokens present: {hits[:4]}"
    if not my_code_files():
        return "RED", "science not run (no code/*.py)"
    return "GREEN", "no lstsq/polyfit/curve_fit in scoring path (one global gain per fold only)"


# ------------------------------------------------------------------ G04 arm-C exact, leakage-free (T1)
def gate04_armC():
    d = load_json("out/armC_exact.json")
    if d is None:
        return "RED", "science not run: out/armC_exact.json missing"
    if d == "PARSE_ERROR":
        return "RED", "out/armC_exact.json unparseable"
    bad = []
    folds = d.get("folds") or {}
    if sorted(folds) != sorted(DEV_KEYS):
        bad.append(f"expected 4 LODO folds {DEV_KEYS}, got {sorted(folds)}")
    seen_maps, seen_hash = {}, {}
    for k, rec in folds.items():
        tk = rec.get("train_keys")
        if not isinstance(tk, list) or len(tk) != 3:
            bad.append(f"{k}: train_keys must list 3 train drives, got {tk}")
        elif k in tk:
            bad.append(f"LEAKAGE: fold {k} MAP trained on its own held-out drive")
        elif sorted(tk) != sorted([x for x in DEV_KEYS if x != k]):
            bad.append(f"{k}: train_keys != the other 3 dev drives ({tk})")
        mf = rec.get("map_file")
        if not mf:
            bad.append(f"{k}: no map_file provenance")
        else:
            if mf in seen_maps:
                bad.append(f"CROSS-FOLD MAP REUSE: {k} and {seen_maps[mf]} share map_file {mf}")
            seen_maps[mf] = k
            ap = os.path.join(WS, mf)
            if not os.path.exists(ap):
                bad.append(f"{k}: map_file {mf} does not exist")
            else:
                h = sha256(ap)
                if h in seen_hash:
                    bad.append(f"CROSS-FOLD MAP REUSE (identical bytes): {k} == {seen_hash[h]}")
                seen_hash[h] = k
        ns = rec.get("n_starts")
        if not isinstance(ns, int) or ns < 4:
            bad.append(f"{k}: multi-start >=4 required, got {ns}")
        for b in BANDS:
            v = (rec.get("bands") or {}).get(b)
            if not isinstance(v, (int, float)) or isinstance(v, bool) or not math.isfinite(v):
                bad.append(f"{k}: band {b} P1' not finite ({v})")
    for b in BANDS:
        m = (d.get("fold_mean") or {}).get(b)
        if not isinstance(m, (int, float)) or not math.isfinite(m):
            bad.append(f"fold_mean {b} not finite ({m})")
    pd_ = d.get("paired_delta_vs_A1_exact") or {}
    for b in BANDS:
        rec = pd_.get(b) or {}
        for f in ("delta_mean", "delta_se"):
            v = rec.get(f)
            if not isinstance(v, (int, float)) or not math.isfinite(v):
                bad.append(f"paired_delta_vs_A1_exact.{b}.{f} not finite ({v})")
        pf = rec.get("per_fold")
        if not isinstance(pf, list) or len(pf) != 4 or not all(
                isinstance(x, (int, float)) and math.isfinite(x) for x in pf):
            bad.append(f"paired_delta_vs_A1_exact.{b}.per_fold must be 4 finite values")
    if d.get("basis") != "A0_wide__enr":
        bad.append(f"arm-C exact must score on the enriched exact basis A0_wide__enr, got {d.get('basis')}")
    if bad:
        return "RED", "; ".join(bad[:6])
    dm = pd_["sub200"]["delta_mean"]
    return "GREEN", (f"arm-C exact: 4 per-fold refits, 4 distinct MAPs, no fold saw its own drive; "
                     f"sub-200 fold-mean {d['fold_mean']['sub200']:.4f}, delta vs A1-exact {dm:+.4f}")


# ------------------------------------------------------------------ G05 verdicts finiteness (T3)
def gate05_verdicts_finite():
    d = load_json("out/verdicts_final.json")
    if d is None:
        return "RED", "science not run: out/verdicts_final.json missing"
    if d == "PARSE_ERROR":
        return "RED", "out/verdicts_final.json unparseable"
    bad = []
    for path, v in walk_numbers(d):
        if v is None:
            bad.append(f"NULL at {path}")
        elif isinstance(v, float) and not math.isfinite(v):
            bad.append(f"NON-FINITE ({v}) at {path}")
    for s in ("S1", "S2", "S3", "S4", "S5"):
        if s not in d:
            bad.append(f"{s} missing")
    for s in ("S3", "S4"):
        st = (d.get(s) or {}).get("status")
        if st != "CANNOT-VERIFY":
            bad.append(f"{s} must be CANNOT-VERIFY (net-CG port failed reference reproduction), got {st}")
    if "armC_exact" not in d:
        bad.append("armC_exact block missing from verdicts_final.json")
    s2 = d.get("S2") or {}
    for conv in ("screening_selected", "exact_selected"):
        if conv not in s2:
            bad.append(f"S2.{conv} missing (S2 must be reported under BOTH selection conventions)")
    if bad:
        return "RED", "; ".join(bad[:6])
    return "GREEN", f"verdicts_final.json: all {sum(1 for _ in walk_numbers(d))} leaves finite; S1/S2/S5 " \
                    f"reported, S3/S4 CANNOT-VERIFY, S2 under both selection conventions"


# ------------------------------------------------------------------ G06 exact re-rank completeness (T2)
def gate06_rerank():
    d = load_json("out/exact_rerank.json")
    if d is None:
        return "RED", "science not run: out/exact_rerank.json missing"
    if d == "PARSE_ERROR":
        return "RED", "out/exact_rerank.json unparseable"
    bad = []
    rows = d.get("rows") or []
    exc = d.get("excluded") or []
    if len(rows) + len(exc) != 28:
        bad.append(f"expected 28 loop candidates (rows+excluded), got {len(rows)}+{len(exc)}")
    tracks = {}
    for r in rows + exc:
        t = r.get("track")
        if t not in ("agent", "random"):
            bad.append(f"{r.get('cid')}: bad track {t}")
        tracks[t] = tracks.get(t, 0) + 1
    if tracks.get("agent") != 14 or tracks.get("random") != 14:
        bad.append(f"expected 14 agent + 14 random, got {tracks}")
    cids = set()
    for r in rows:
        cid = r.get("cid")
        if cid in cids:
            bad.append(f"duplicate cid {cid}")
        cids.add(cid)
        for f in ("screening_sub200", "exact_sub200"):
            v = r.get(f)
            if not isinstance(v, (int, float)) or isinstance(v, bool) or not math.isfinite(v):
                bad.append(f"{cid}: {f} not finite ({v})")
        ef = r.get("exact_folds")
        if not isinstance(ef, dict) or sorted(ef) != sorted(DEV_KEYS):
            bad.append(f"{cid}: exact_folds must carry all 4 dev folds")
        elif not all(isinstance(x, (int, float)) and math.isfinite(x) for x in ef.values()):
            bad.append(f"{cid}: non-finite exact fold score")
    for r in exc:
        if not r.get("reason"):
            bad.append(f"{r.get('cid')}: excluded without a reason (substitution is forbidden)")
    eig = load_jsonl("out/eigensolve_log.jsonl")
    if not eig or eig == "PARSE_ERROR":
        bad.append("out/eigensolve_log.jsonl missing/empty (every eigensolve must be logged)")
    else:
        logged = {e.get("cid") for e in eig}
        missing = [c for c in cids if not any(str(c) in str(l) for l in logged)]
        if missing:
            bad.append(f"{len(missing)} scored candidates have no logged eigensolve: {missing[:3]}")
    if bad:
        return "RED", "; ".join(bad[:6])
    return "GREEN", f"exact re-rank complete: {len(rows)} candidates exact-scored on 4 folds " \
                    f"({len(exc)} excluded-with-reason), every eigensolve logged"


# ------------------------------------------------------------------ G07 S2 both conventions + reproduction
def gate07_s2():
    d = load_json("out/exact_rerank.json")
    if d is None or d == "PARSE_ERROR":
        return "RED", "science not run: out/exact_rerank.json missing"
    bad, warn = [], []
    s2 = d.get("S2") or {}
    for conv in ("screening_selected", "exact_selected"):
        rec = s2.get(conv) or {}
        for f in ("agent_cid", "random_cid"):
            if not rec.get(f):
                bad.append(f"S2.{conv}.{f} missing")
        for f in ("delta_mean", "delta_se"):
            v = rec.get(f)
            if not isinstance(v, (int, float)) or not math.isfinite(v):
                bad.append(f"S2.{conv}.{f} not finite ({v})")
        pf = rec.get("per_fold")
        if not isinstance(pf, list) or len(pf) != 4 or not all(
                isinstance(x, (int, float)) and math.isfinite(x) for x in pf):
            bad.append(f"S2.{conv}.per_fold must be 4 finite values")
    ra = d.get("rank_agreement") or {}
    for t in ("agent", "random"):
        rec = ra.get(t) or {}
        v = rec.get("spearman_screening_vs_exact")
        if not isinstance(v, (int, float)) or not math.isfinite(v):
            bad.append(f"rank_agreement.{t}.spearman_screening_vs_exact not finite ({v})")
        for f in ("top3_screening", "top3_exact"):
            if not isinstance(rec.get(f), list) or len(rec.get(f)) != 3:
                bad.append(f"rank_agreement.{t}.{f} must list 3 cids")
    # pipeline reproduction: my exact scores for the study's two winners must match the study's numbers
    rep = d.get("reproduction_check") or {}
    for arm, ref in STUDY_EXACT.items():
        v = (rep.get(arm) or {}).get("mine_exact_sub200")
        if not isinstance(v, (int, float)) or not math.isfinite(v):
            bad.append(f"reproduction_check.{arm}.mine_exact_sub200 not finite ({v})")
        elif abs(v - ref) > 0.01:
            bad.append(f"PIPELINE MISMATCH: {arm} exact sub-200 {v:.4f} vs study {ref:.4f} (tol 0.01)")
    sa = (s2.get("screening_selected") or {}).get("delta_mean")
    if isinstance(sa, (int, float)) and math.isfinite(sa) and abs(sa - STUDY_S2_A) > 0.005:
        warn.append(f"S2(screening-selected) {sa:+.4f} does not reproduce the repair's {STUDY_S2_A:+.4f}")
    if bad:
        return "RED", "; ".join(bad[:6])
    if warn:
        return "YELLOW", "; ".join(warn)
    return "GREEN", (f"S2 reported both ways: screening-selected {s2['screening_selected']['delta_mean']:+.4f}"
                     f" +/- {s2['screening_selected']['delta_se']:.4f}, exact-selected "
                     f"{s2['exact_selected']['delta_mean']:+.4f} +/- {s2['exact_selected']['delta_se']:.4f}; "
                     f"pipeline reproduces the study's exact D/R within 0.01")


# ------------------------------------------------------------------ G08 figures
def gate08_figures():
    m = load_json("out/fig_manifest.json")
    if m is None or m == "PARSE_ERROR":
        return "RED", "science not run: out/fig_manifest.json missing"
    bad = []
    figs = m.get("figures") or []
    if len(figs) < 2:
        bad.append(f"expected >=2 corrected figures (arms x bands, screening-vs-exact), got {len(figs)}")
    for f in figs:
        fp = os.path.join(WS, f.get("file", ""))
        if not os.path.exists(fp):
            bad.append(f"{f.get('file')} missing")
        sp = f.get("script", "")
        if not sp.endswith(".py") or not os.path.exists(os.path.join(WS, sp)):
            bad.append(f"{f.get('file')}: plotting code must be a saved .py (got {sp})")
        if not f.get("data_label"):
            bad.append(f"{f.get('file')}: no data/run label")
    if not os.path.exists(os.path.join(WS, "out/tufte_lint.txt")):
        bad.append("out/tufte_lint.txt missing (tufte_lint.py not run on the plotting script)")
    qa = load_json("out/fig_qa.json")
    if qa is None or qa == "PARSE_ERROR":
        bad.append("out/fig_qa.json missing (image-legibility QA)")
    else:
        fails = [k for k, v in (qa.get("figures") or {}).items() if not v.get("pass")]
        if fails:
            bad.append(f"legibility QA fail: {fails}")
        pend = [k for k, v in (qa.get("figures") or {}).items()
                if "PENDING" in str(v.get("visual_review", ""))]
        if pend:
            bad.append(f"visual review still PENDING: {pend}")
    # the corrected arms table must NOT carry the invalid F=R row (review C8)
    v = load_json("out/verdicts_final.json")
    if isinstance(v, dict):
        arms = v.get("arms_bands_table") or {}
        if "F" in arms:
            fr = arms.get("F")
            if isinstance(fr, dict) and fr.get("identity") in ("R", "random"):
                bad.append("INVALID F=R row present (F must follow the pre-registered rule, not best-arm)")
    if bad:
        return "RED", "; ".join(bad[:6])
    return "GREEN", f"{len(figs)} figures scripted (.py), labeled, linted, legibility-QA'd; no F=R row"


# ------------------------------------------------------------------ G09 sampler / labeling honesty
def gate09_labeling():
    """No sampler runs in this card. Any MAP-derived number must be labeled a deterministic optimizer
    result, and the study's non-converged diagnostics must ride along with any MAP-derived bar."""
    v = load_json("out/verdicts_final.json")
    if v is None or v == "PARSE_ERROR":
        return "RED", "science not run: out/verdicts_final.json missing"
    bad = []
    sd = v.get("sampler_decision") or {}
    if not sd.get("sampler_run") is False:
        bad.append("sampler_decision.sampler_run must be false (this card runs no sampler)")
    if not sd.get("rationale"):
        bad.append("sampler_decision.rationale missing (AGENTS Sampler Decision gate)")
    ac = v.get("armC_exact") or {}
    if "deterministic" not in str(ac.get("method", "")).lower():
        bad.append("armC_exact.method must label the MAP as a deterministic optimizer result")
    diag = v.get("nonconvergence_carried") or {}
    for f in ("worst_rhat", "worst_ess"):
        if not isinstance(diag.get(f), (int, float)) or not math.isfinite(diag.get(f)):
            bad.append(f"nonconvergence_carried.{f} must carry the study's worst-case diagnostic")
    fin = os.path.join(WS, "findings.md")
    if os.path.exists(fin):
        t = open(fin).read()
        for phrase in ("NUTS active", "posterior converged", "converged posterior"):
            if phrase.lower() in t.lower():
                bad.append(f"findings.md claims '{phrase}' but no sampler was run")
    if bad:
        return "RED", "; ".join(bad[:5])
    return "GREEN", (f"no sampler run (deterministic MAP refits + exact scoring only); MAP labeled as "
                     f"optimizer result; study's worst R-hat {diag['worst_rhat']} / ESS {diag['worst_ess']} "
                     f"carried alongside every MAP-derived number")


# ------------------------------------------------------------------ G10 runtime
def gate10_runtime():
    r = load_json("runtime.json")
    if r is None or r == "PARSE_ERROR":
        return "RED", "runtime.json missing"
    a, e = r.get("active_runtime_s"), r.get("elapsed_wallclock_s")
    if not isinstance(a, (int, float)) or not isinstance(e, (int, float)) \
            or not math.isfinite(a) or not math.isfinite(e):
        return "RED", f"runtime fields not finite (active {a}, elapsed {e})"
    if a > e:
        return "RED", f"active_runtime_s ({a}) > elapsed_wallclock_s ({e})"
    return "GREEN", f"active {a:.0f}s <= elapsed {e:.0f}s on {r.get('machine', 'unstated')}"


# ------------------------------------------------------------------ G11 continuity
def gate11_continuity():
    bad = []
    fin = os.path.join(WS, "findings.md")
    if not os.path.exists(fin):
        bad.append("findings.md missing")
    else:
        t = open(fin).read()
        if "Q1" not in t or "Q2" not in t:
            bad.append("findings.md does not answer both pre-registered questions Q1/Q2")
        if len(t) < 1500:
            bad.append("findings.md too thin to be a review packet")
    if not os.path.exists(os.path.join(WS, "run_all.sh")):
        bad.append("run_all.sh missing (one-command replay)")
    if bad:
        return "RED", "; ".join(bad[:4])
    return "GREEN", "findings.md answers Q1/Q2; run_all.sh replay present"


# ------------------------------------------------------------------ G12 checker self-SHA
def gate12_self_sha():
    lock = os.path.join(WS, "CHECKER.sha256")
    if not os.path.exists(lock):
        return "RED", "CHECKER.sha256 missing (checker not SHA-locked)"
    want = open(lock).read().split()[0]
    got = sha256(os.path.abspath(__file__))
    if want != got:
        return "RED", f"CHECKER MODIFIED DURING TRIAL: locked {want[:12]} != current {got[:12]}"
    return "GREEN", f"checker self-SHA matches lock ({got[:12]})"


GATES = [
    ("G01", "pre-registration (priorities, Q1/Q2, D0, sampler decision)", gate01_prereg),
    ("G02", "isolation: no writes outside workspace; read-only inputs unchanged", gate02_isolation),
    ("G03", "no per-channel/per-mode amplitude LSQ", gate03_no_lsq),
    ("G04", "T1 arm-C exact: per-fold refits, leakage-free provenance", gate04_armC),
    ("G05", "T3 verdicts: every asserted statistic FINITE", gate05_verdicts_finite),
    ("G06", "T2 exact re-rank: all 28 candidates", gate06_rerank),
    ("G07", "T2 S2 under BOTH selection conventions + pipeline reproduction", gate07_s2),
    ("G08", "figures scripted/linted/QA'd; no F=R row", gate08_figures),
    ("G09", "sampler decision + honest MAP/non-convergence labeling", gate09_labeling),
    ("G10", "runtime accounting", gate10_runtime),
    ("G11", "continuity: findings answer Q1/Q2, replay present", gate11_continuity),
    ("G12", "checker self-SHA (immutability)", gate12_self_sha),
]


def main():
    rows, worst = [], "GREEN"
    for gid, name, fn in GATES:
        try:
            status, detail = fn()
        except Exception as ex:                      # a crashing gate is RED, never silently green
            status, detail = "RED", f"gate raised {type(ex).__name__}: {ex}"
        rows.append({"gate": gid, "name": name, "status": status, "detail": detail})
        if RANK[status] > RANK[worst]:
            worst = status
    rep = {"overall": worst, "gates": rows,
           "card": "EXACT-EVIDENCE COMPLETION for the full-spectrum FRF study (post-review items 1-3)",
           "note": "Exits non-zero only on RED. YELLOW = documented, non-fatal, never reported as success."}
    with open(os.path.join(WS, "checker_report.json"), "w") as f:
        json.dump(rep, f, indent=1)
    print(f"OVERALL: {worst}")
    for r in rows:
        print(f"  {r['gate']} {r['status']:6s} {r['name']}\n         {r['detail']}")
    sys.exit(2 if worst == "RED" else 0)


if __name__ == "__main__":
    main()
