#!/usr/bin/env python3
"""IMMUTABLE checker — ShockSat Resolution-Consistent FRF Scoring (20260713).

SHA-locked before science (CHECKER.sha256). Result Status Standard: every gate GREEN/YELLOW/RED; overall =
RED if any red, else YELLOW if any yellow, else GREEN; exit nonzero ONLY on RED. A falsified pre-registered
claim is YELLOW (honest outcome), never RED; a missing/fabricated artifact or integrity violation is RED.

Encodes (card §5.3): gate files; Gates W/K/R; fixed arm set B0-B5 (no-search audit); pre-registered damping
specs only (no fitting); no-LSQ grep; freeze-before-vault ordering + touched-once + second-read label;
S1 fold-SE margin rule; S2 decomposition present; S3 graded separately; figures + legibility QA + tufte lint;
runtime accounting; reused-source SHA integrity.
"""
import json, os, re, subprocess, sys

WS = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(WS, "out")
FIGS = os.path.join(WS, "figures")
gates = []


def add(name, status, detail):
    gates.append({"gate": name, "status": status, "detail": detail})


def jload(p):
    try:
        with open(p) as f:
            return json.load(f)
    except Exception:
        return None


# ---------------------------------------------------------------- 1. pre-registration gate files
for fn in ("priority_deliverables.md", "question_framing.md", "quantity_contracts.md",
           "assumptions_ledger.md", "decisions_log.md", "REUSED_code.sha256"):
    p = os.path.join(WS, fn)
    ok = os.path.exists(p) and os.path.getsize(p) > 200
    add(f"gatefile:{fn}", "GREEN" if ok else "RED", "present" if ok else "missing/empty")

# ---------------------------------------------------------------- 2. reused-source SHA integrity
try:
    r = subprocess.run(["shasum", "-a", "256", "-c", os.path.join(WS, "REUSED_code.sha256")],
                       capture_output=True, text=True, cwd=os.path.join(WS, "..", "..", ".."))
    bad = [l for l in r.stdout.splitlines() if l and not l.endswith(": OK")]
    add("reused_sha_integrity", "GREEN" if r.returncode == 0 and not bad else "RED",
        "all reused sources unchanged" if r.returncode == 0 and not bad else f"MODIFIED: {bad[:5]}")
except Exception as e:
    add("reused_sha_integrity", "RED", f"could not verify: {e}")

# ---------------------------------------------------------------- 3. Gate K (synthetic kernel correctness)
gk = jload(os.path.join(OUT, "gate_K.json"))
if gk is None:
    add("gate_K_kernel", "RED", "out/gate_K.json missing")
else:
    ok = gk.get("pass") is True and abs(gk.get("light_peak_err_frac", 9)) <= 0.05 \
        and abs(gk.get("broad_peak_change_frac", 9)) <= 0.05
    add("gate_K_kernel", "GREEN" if ok else "RED",
        f"light-zeta peak err {gk.get('light_peak_err_frac')}, broad-peak change "
        f"{gk.get('broad_peak_change_frac')} (both must be <=0.05)")

# ---------------------------------------------------------------- 4. Gate W (window model vs raw data)
gw = jload(os.path.join(OUT, "gate_W.json"))
if gw is None:
    add("gate_W_window", "RED", "out/gate_W.json missing")
else:
    mode = gw.get("pass_mode")
    if mode == "direct":
        add("gate_W_window", "GREEN",
            f"recomputed-vs-stored median dex {gw.get('median_dex_direct')}, "
            f"frac channels<=0.05dex {gw.get('frac_ok_direct')} (>=0.80)")
    elif mode == "labeled":
        add("gate_W_window", "YELLOW",
            f"passed on LABELED comparison ({gw.get('labeled_basis')}); Test01-vs-Test07 repeatability "
            f"{gw.get('t01_t07_median_dex')} dex reported as bonus; direct frac_ok {gw.get('frac_ok_direct')}")
    else:
        add("gate_W_window", "RED", f"gate W FAILED (pass_mode={mode}); window operator unverified — "
            "arm scores must not be interpreted")

# ---------------------------------------------------------------- 5. Gate R (reproduction / pipeline drift)
gr = jload(os.path.join(OUT, "gate_R.json"))
REF_P1 = 0.196949
if gr is None:
    add("gate_R_reproduction", "RED", "out/gate_R.json missing")
else:
    b0 = gr.get("B0_P1p_mean")
    ok = b0 is not None and abs(b0 - REF_P1) <= 0.002 and gr.get("B1_lt_B0") is True
    add("gate_R_reproduction", "GREEN" if ok else "RED",
        f"B0 P1'={b0} (ref {REF_P1}±0.002); B1<B0={gr.get('B1_lt_B0')}")

# ---------------------------------------------------------------- 6. score log: fixed arm set (no-search audit)
ARMS = ["B0", "B1", "B2", "B3", "B4", "B5"]
slog_p = os.path.join(OUT, "score_log.jsonl")
dev_rows, vault_rows = {}, {}
if os.path.exists(slog_p):
    for line in open(slog_p):
        if not line.strip():
            continue
        r = json.loads(line)
        (vault_rows if r.get("stage") == "vault" else dev_rows).setdefault(r.get("arm"), []).append(r)
extra = [a for a in dev_rows if a not in ARMS]
missing = [a for a in ARMS if a not in dev_rows]
multi = [a for a, v in dev_rows.items() if len(v) > 1 and a in ARMS]
ok = not extra and not missing
add("arm_set_fixed", "GREEN" if ok and not multi else ("YELLOW" if ok and multi else "RED"),
    f"dev arms {sorted(dev_rows)}; extra={extra}, missing={missing}, duplicated={multi} "
    "(exactly B0-B5, once each; duplicates=resume artifacts must be explained)")

# pre-registered damping specs only (nothing fit); eta absent; dim<=10
ERA_BZ = [0.00099, 0.00301, 0.00542, 0.00236]


def spec_ok(arm, r):
    d = r.get("damping", {})
    if d.get("eta"):
        return False
    if arm in ("B0", "B3"):
        return d.get("kind") == "fixed" and abs(d.get("zeta", 0) - 0.01) < 1e-12
    if arm in ("B1", "B2", "B5"):
        return d.get("kind") == "permode_survey_interp"
    if arm == "B4":
        z = d.get("zeta", [])
        return d.get("kind") == "band" and len(z) == 4 and all(abs(a - b) < 5e-5 for a, b in zip(z, ERA_BZ))
    return False


bad_specs = [a for a in ARMS if a in dev_rows and not all(spec_ok(a, r) for r in dev_rows[a])]
add("damping_specs_preregistered", "GREEN" if not bad_specs and not missing else "RED",
    f"non-conforming arms: {bad_specs}" if bad_specs else "all specs match the card table; no eta; nothing fit")

win_flags = {a: dev_rows[a][0].get("windowed") for a in ARMS if a in dev_rows}
expect_win = {"B0": False, "B1": False, "B2": True, "B3": True, "B4": True, "B5": True}
bad_win = [a for a, w in win_flags.items() if w is not expect_win.get(a)]
add("windowed_flags", "GREEN" if not bad_win and not missing else "RED",
    f"windowed flags {win_flags}; mismatches: {bad_win}")

# ---------------------------------------------------------------- 7. anti-LSQ code audit
lsq_hits, markers = [], 0
for root, _, files in os.walk(os.path.join(WS, "code")):
    for f in files:
        if not f.endswith(".py"):
            continue
        src = open(os.path.join(root, f)).read()
        markers += ("NO-PER-MODE-LSQ" in src) + ("LOW-DIM-PHYSICAL-DAMPING-ONLY" in src)
        for pat in (r"lstsq", r"per_mode_gain", r"per_channel_gain", r"curve_fit"):
            if re.search(pat, src):
                lsq_hits.append(f"{f}:{pat}")
add("anti_lsq", "GREEN" if not lsq_hits and markers >= 2 else "RED",
    f"markers={markers} (need >=2), forbidden hits={lsq_hits}")

# ---------------------------------------------------------------- 8. freeze-before-vault + touched-once + label
fz = os.path.join(WS, "VAULT_FREEZE.sha256")
if not vault_rows:
    add("vault_protocol", "RED", "no vault entries in score_log")
elif not os.path.exists(fz):
    add("vault_protocol", "RED", "VAULT_FREEZE.sha256 missing but vault was read")
else:
    fz_t = os.path.getmtime(fz)
    early = [a for a, v in vault_rows.items() for r in v if r.get("unix_ts", 0) < fz_t]
    once = all(len(v) == 1 for v in vault_rows.values())
    labeled = all(r.get("second_program_read") is True for v in vault_rows.values() for r in v)
    cover = sorted(vault_rows) == ARMS
    ok = not early and once and labeled and cover
    add("vault_protocol", "GREEN" if ok else "RED",
        f"freeze-before-read={not early}, touched-once={once}, second-read-labeled={labeled}, "
        f"all-6-arms={cover}")

# ---------------------------------------------------------------- 9. verdicts: S1 margin rule, S2, S3
vd = jload(os.path.join(OUT, "verdicts.json"))
if vd is None or not all(k in vd for k in ("S1", "S2", "S3")):
    add("verdicts_present", "RED", "out/verdicts.json missing or lacks S1/S2/S3")
else:
    add("verdicts_present", "GREEN", "S1/S2/S3 present with numbers")
    s1 = vd["S1"]
    need = {"delta_dev_P1p", "fold_se_delta", "vault_B2_gt_B0", "pass"}
    if not need.issubset(s1):
        add("S1_margin_rule", "RED", f"S1 lacks fields {need - set(s1)}")
    else:
        recomputed = (s1["delta_dev_P1p"] >= 0.03 and s1["delta_dev_P1p"] >= 2 * s1["fold_se_delta"]
                      and s1["vault_B2_gt_B0"] is True)
        if bool(s1["pass"]) is not recomputed:
            add("S1_margin_rule", "RED", f"S1 pass flag inconsistent with numbers: {s1}")
        elif s1["pass"]:
            add("S1_margin_rule", "GREEN", f"S1 PASS: dP1'={s1['delta_dev_P1p']:+.4f} "
                f">= max(0.03, 2x fold-SE {s1['fold_se_delta']:.4f}); vault confirms")
        else:
            add("S1_margin_rule", "YELLOW", "PRE-REGISTERED CLAIM FALSIFIED (honest outcome): "
                f"dP1'={s1['delta_dev_P1p']:+.4f} vs need >=+0.03 & >=2xSE({s1['fold_se_delta']:.4f}) "
                f"& vault_B2_gt_B0={s1['vault_B2_gt_B0']}")
    s2 = vd["S2"]
    need2 = {"window_alone", "damping_alone", "interaction", "total"}
    add("S2_decomposition", "GREEN" if need2.issubset(s2) else "RED",
        f"decomposition {'present: ' + json.dumps({k: round(s2[k], 4) for k in need2 & set(s2)}) if need2.issubset(s2) else 'incomplete'}")
    s3 = vd["S3"]
    if not {"B2_minus_B1_dev_P1p", "gate_W_pass", "pass"}.issubset(s3):
        add("S3_mechanism", "RED", "S3 lacks fields")
    else:
        rec3 = (s3["B2_minus_B1_dev_P1p"] >= 0.02 and bool(s3["gate_W_pass"]))
        if bool(s3["pass"]) is not rec3:
            add("S3_mechanism", "RED", f"S3 pass flag inconsistent: {s3}")
        elif s3["pass"]:
            add("S3_mechanism", "GREEN", f"mechanism confirmed: B2-B1={s3['B2_minus_B1_dev_P1p']:+.4f}"
                f" >= +0.02 and Gate W passed")
        else:
            add("S3_mechanism", "YELLOW", f"mechanism NOT confirmed (documented finding): "
                f"B2-B1={s3['B2_minus_B1_dev_P1p']:+.4f} (need >=+0.02), gateW={s3['gate_W_pass']}")

# ---------------------------------------------------------------- 10. figures + QA + lint
REQ_FIGS = ["fig_money.png", "fig_s2_decomp.png", "fig_gateW_overlay.png", "fig_apparent_zeta.png",
            "fig_peak_zoom.png"]
missing_f = [f for f in REQ_FIGS if not os.path.exists(os.path.join(FIGS, f))]
add("figures_exist", "GREEN" if not missing_f else "RED", f"missing: {missing_f}" if missing_f else "all 5 present")
qa = jload(os.path.join(OUT, "fig_qa.json"))
if qa is None:
    add("figure_qa", "RED", "out/fig_qa.json missing")
else:
    fails = [k for k, v in qa.items() if isinstance(v, dict) and v.get("pass") is not True]
    add("figure_qa", "GREEN" if not fails else "RED", f"legibility fails: {fails}" if fails else "all pass")
lint = os.path.join(OUT, "tufte_lint.txt")
add("tufte_lint_run", "GREEN" if os.path.exists(lint) else "RED",
    "lint output saved" if os.path.exists(lint) else "out/tufte_lint.txt missing")

# ---------------------------------------------------------------- 11. deliverables + runtime
for fn, mn in (("packet.md", 3000), ("findings.md", 500), ("run_all.sh", 100)):
    p = os.path.join(WS, fn)
    ok = os.path.exists(p) and os.path.getsize(p) >= mn
    add(f"deliverable:{fn}", "GREEN" if ok else "RED", "present" if ok else f"missing or <{mn}B")
rt = jload(os.path.join(WS, "runtime.json"))
if rt is None:
    add("runtime_accounting", "RED", "runtime.json missing")
else:
    ok = 0 < rt.get("active_runtime_s", -1) <= rt.get("elapsed_wallclock_s", 0)
    add("runtime_accounting", "GREEN" if ok else "RED",
        f"active={rt.get('active_runtime_s')}s wall={rt.get('elapsed_wallclock_s')}s")

# ---------------------------------------------------------------- report
counts = {s: sum(1 for g in gates if g["status"] == s) for s in ("GREEN", "YELLOW", "RED")}
overall = "RED" if counts["RED"] else ("YELLOW" if counts["YELLOW"] else "GREEN")
report = {"overall": overall, "counts": counts, "gates": gates}
with open(os.path.join(WS, "checker_report.json"), "w") as f:
    json.dump(report, f, indent=1)
print(f"OVERALL {overall}  " + json.dumps(counts))
for g in gates:
    print(f"  [{g['status']:6s}] {g['gate']}: {g['detail']}")
sys.exit(1 if counts["RED"] else 0)
