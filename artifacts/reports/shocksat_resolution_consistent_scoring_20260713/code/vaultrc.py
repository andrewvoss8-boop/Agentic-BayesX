#!/usr/bin/env python3
"""Vault protocol (card §3.1): freeze THEN one grading pass of the fixed arm set on +XY/Test04.
  python3 code/vaultrc.py freeze  -> VAULT_FREEZE.sha256 (hashes: score_log dev entries, packages, code)
  python3 code/vaultrc.py grade   -> the SINGLE post-freeze vault grading pass (all 6 arms, one script run);
                                     every record labeled second_program_read=True (the damping run read this
                                     cache once on 2026-07-10; zero-search arm set is the mitigation).
"""
import hashlib, json, os, sys, time

MY = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, MY)
import wscore as SC
import femlib as F

WS = SC.WS
ERA_BZ = [0.00099, 0.00301, 0.00542, 0.00236]
ARMS = [
    ("B0", "A0_enr", {"kind": "fixed", "zeta": 0.01}, False),
    ("B1", "A0_enr", {"kind": "permode_survey_interp"}, False),
    ("B2", "A0_enr", {"kind": "permode_survey_interp"}, True),
    ("B3", "A0_enr", {"kind": "fixed", "zeta": 0.01}, True),
    ("B4", "A0_enr", {"kind": "band", "zeta": ERA_BZ}, True),
    ("B5", "c06_tb_xface_enr", {"kind": "permode_survey_interp"}, True),
]


def freeze():
    dev = SC.existing("dev")
    missing = [a for a, *_ in ARMS if a not in dev]
    if missing:
        raise SystemExit(f"cannot freeze: dev arms missing {missing}")
    files = [os.path.join(WS, "out", "score_log.jsonl"),
             os.path.join(WS, "out", "gate_K.json"), os.path.join(WS, "out", "gate_R.json"),
             os.path.join(WS, "out", "gate_W.json")]
    for cid in sorted({cid for _, cid, _, _ in ARMS}):
        files.append(os.path.join(os.path.dirname(F.NETCG_DATA), "..", "..",
                                  "shocksat_frf_damping_updating_20260710", "data", "packages", cid + ".npz"))
    for f in sorted(os.listdir(MY)):
        if f.endswith(".py"):
            files.append(os.path.join(MY, f))
    lines = []
    for f in files:
        f = os.path.abspath(f)
        if os.path.exists(f):
            d = hashlib.sha256(open(f, "rb").read()).hexdigest()
            lines.append(f"{d}  {os.path.relpath(f, WS)}")
    open(os.path.join(WS, "VAULT_FREEZE.sha256"), "w").write("\n".join(lines) + "\n")
    print("FROZEN before vault:\n" + "\n".join(lines))


def grade():
    t0 = time.time()
    if not os.path.exists(os.path.join(WS, "VAULT_FREEZE.sha256")):
        raise SystemExit("freeze first")
    done = SC.existing("vault")
    open(os.path.join(WS, "out", "vault_read.log"), "a").write(
        f"single post-freeze vault grading pass ({F.VAULT_KEY}) at {time.strftime('%Y-%m-%dT%H:%M:%S')}; "
        f"SECOND program read of this cache (first: damping run 2026-07-10)\n")
    for arm, cid, dmp, win in ARMS:
        if arm in done:
            print(f"{arm} vault-graded already (resume-skip)"); continue
        r = SC.score_vault(arm, cid, dmp, windowed=win)
        print(f"vault {arm}: P1'={r['P1p_mean']:.4f} P2'={r['P2p_mean']:.4f} P4={r['P4_mean']:.2f} dB")
    with open(os.path.join(WS, "out", "runtime_log.jsonl"), "a") as f:
        f.write(json.dumps({"step": "vault_grade", "active_s": round(time.time() - t0, 1)}) + "\n")


if __name__ == "__main__":
    {"freeze": freeze, "grade": grade}[sys.argv[1]]()
