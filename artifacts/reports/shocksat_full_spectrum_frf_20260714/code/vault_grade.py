#!/usr/bin/env python3
"""vault_grade — the SINGLE post-freeze vault read (card §3.5; G07). Grades the PRE-REGISTERED finalist
set on the wide +XY cache (per-band P1'/P3) and computes the +XY net-CG QOI answer-key coverage for the
delivered arm, all in ONE event. Verifies VAULT_FREEZE.sha256 hashes before reading. Every record is
labeled the program's THIRD read of +XY. Refuses to run twice (out/vault_done.flag)."""
import hashlib, json, os, sys, time
import numpy as np

WS = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
ROOT = os.path.abspath(os.path.join(WS, "..", "..", ".."))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import wide_package as WP                      # noqa: E402
import wscore_wide as SW                       # noqa: E402

FLAG = os.path.join(WS, "out", "vault_done.flag")


def verify_freeze():
    for line in open(os.path.join(WS, "VAULT_FREEZE.sha256")):
        h, name = line.split(None, 1)
        name = name.strip()
        if name.startswith("overlap_validation_record"):
            ov = json.load(open(os.path.join(WS, "out", "overlap_validation.json")))["drives"]["m_xy_990xy"]
            got = hashlib.sha256(json.dumps(ov, sort_keys=True).encode()).hexdigest()
        else:
            got = hashlib.sha256(open(os.path.join(ROOT, name), "rb").read()).hexdigest()
        assert got == h, f"VAULT FREEZE VIOLATION: {name}"
    print("vault freeze verified")


def main():
    if os.path.exists(FLAG):
        raise SystemExit("vault already graded once — refusing a second read")
    verify_freeze()
    t0 = time.time()
    finalists = json.load(open(os.path.join(WS, "out", "vault_finalists.json")))
    qoi_w = None
    qp = os.path.join(WS, "out", "qoi_sensor_weights.json")
    if os.path.exists(qp):
        qoi_w = {int(k): v for k, v in json.load(open(qp))["weights"].items()}
    results = {}
    for f in finalists["set"]:
        arm = f["arm"]
        pkg = WP.load(f["cid"])
        theta = np.asarray(f["theta"], float)
        fwd = None
        if f.get("shapes_npz"):
            import arm_c_nuts as AC
            z = np.load(os.path.join(WS, f["shapes_npz"]), allow_pickle=True)
            fwd = AC.shapes_forward(pkg, theta, np.asarray(z["raw_mean"]),
                                    np.asarray(z["ks"], int), int(z["r0"]))
        rec = SW.score_vault_wide(arm, pkg, theta, note=f.get("note", ""),
                                  windowed=f.get("windowed", True), flat_zeta=f.get("flat_zeta"),
                                  qoi_w=qoi_w, fwd=fwd)
        results[arm] = rec["bands_agg"]
        print(arm, json.dumps(rec["bands_agg"]), flush=True)
    open(FLAG, "w").write(time.strftime("%Y-%m-%dT%H:%M:%S"))
    json.dump(results, open(os.path.join(WS, "out", "vault_results.json"), "w"), indent=1)
    with open(os.path.join(WS, "out", "runtime_log.jsonl"), "a") as f:
        f.write(json.dumps({"step": "vault_grade", "active_s": round(time.time() - t0, 1)}) + "\n")


if __name__ == "__main__":
    main()
