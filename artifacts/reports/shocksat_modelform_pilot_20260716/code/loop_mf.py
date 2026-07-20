#!/usr/bin/env python3
"""loop_mf — stratified round planner (card §3). STRATIFICATION IS THE RULE: each round, EACH track
scores exactly 2 candidates per class x 5 classes. The RANDOM track draws seeded uniform proposals
from the SAME grammar menus (no diagnosis, no learning; every draw's seed recorded). The AGENT track's
specs are authored from the diagnosis (diag_mf output) and written to out/pending_specs/ by the runner
with an explicit diagnosis->class->edit link per proposal (round summaries); this module only ENQUEUES
and ACCOUNTS. Duds are replaced (same class/track/round, fresh recorded seed), never silently skipped.

Commands:
  plan_random <round>    enqueue the round's 10 random specs (2/class), seeds recorded
  fill_random <round>    enqueue replacement random specs for classes short of quota (dud replacement)
  status                 quota table from partials + pending queue
"""
from __future__ import annotations
import json
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _common as C                                  # noqa: E402
import mfops as MO                                   # noqa: E402

F = C.F
PENDD = os.path.join(C.MY_OUT, "pending_specs")
os.makedirs(PENDD, exist_ok=True)
SEED_BASE = 20260716
SEEDS_P = os.path.join(C.MY_OUT, "seeds.json")
SHELL_PIDS = MO.ACT.SHELL_PIDS
QUAD_CAP = 8000


def record_seed(rec):
    d = json.load(open(SEEDS_P)) if os.path.exists(SEEDS_P) else \
        {"seed_base": SEED_BASE, "scheme": "seed = base + 1000*round + slot + 100000*attempt",
         "draws": []}
    d["draws"].append(rec)
    json.dump(d, open(SEEDS_P, "w"), indent=1)


def _quad_counts():
    m = F.load_model()
    q = np.asarray(m["cquad4"])
    return {p: int((q[:, 1] == p).sum()) for p in SHELL_PIDS}


def _spider_eids():
    m = F.load_model()
    return [int(e) for e in np.asarray(m["rbe2"])[:, 0]]


# ------------------------------------------------------------------ class menus (uniform random)
def draw_connectivity(rng, k):
    eids = _spider_eids()
    n = int(rng.integers(1, 21))
    chosen = [int(e) for e in rng.choice(eids, size=min(n, len(eids)), replace=False)]
    if rng.random() < 0.5:
        return [{"op": "rbe2_soften", "eids": chosen,
                 "k_trans": float(10 ** rng.uniform(4, 7)),
                 "k_rot": float(10 ** rng.uniform(3, 6)), "name": f"rconn{k}"}]
    return [{"op": "rbe3_convert", "eids": chosen, "name": f"rrbe3{k}"}]


def draw_mesh(rng, k):
    qc = _quad_counts()
    for _ in range(50):
        pids = [int(p) for p in rng.choice(SHELL_PIDS, size=int(rng.integers(1, 3)),
                                           replace=False)]
        if sum(qc[p] for p in pids) <= QUAD_CAP:
            return [{"op": "refine", "pids": pids}]
    raise ValueError("no refine draw under quad cap after 50 tries")


def draw_formulation(rng, k):
    pids = [int(p) for p in rng.choice(SHELL_PIDS, size=int(rng.integers(1, 4)), replace=False)]
    mode = rng.choice(["br", "ts", "both"])
    op = {"op": "formulation", "pids": pids, "name": f"rform{k}"}
    if mode in ("br", "both"):
        for _ in range(50):
            br = float(np.exp(rng.uniform(np.log(0.7), np.log(1.4))))
            if abs(br - 1.0) >= 0.05:
                break
        op["br_scale"] = br
    if mode in ("ts", "both"):
        op["ts_t"] = float(rng.choice([0.35, 5.0]))
    if "br_scale" not in op and "ts_t" not in op:
        op["ts_t"] = 0.35
    return [op]


def draw_geometry(rng, k):
    m = F.load_model()
    if rng.random() < 0.5:
        pid = int(rng.choice(sorted(MO.FLAT_PANEL_PIDS)))
        t = float(m["pshell"][str(pid)]["t"])
        cap = min(2.0 * t, MO.WARP_AMP_CAP_IN)
        mag = float(rng.uniform(0.05, cap)) if cap > 0.05 else float(rng.uniform(0.5 * cap, cap))
        amp = float(mag * (1 if rng.random() < 0.5 else -1))
        return [{"op": "warp_panel", "pid": pid, "amp": amp, "name": f"rwarp{k}"}]
    eids = _spider_eids()
    n = int(rng.integers(1, 4))
    chosen = [int(e) for e in rng.choice(eids, size=n, replace=False)]
    d = rng.normal(0, 1, 3)
    d /= np.linalg.norm(d)
    mag = float(rng.uniform(0.1, MO.JOINT_D_CAP_IN))
    return [{"op": "joint_offset", "eids": chosen, "vec": [float(x) for x in mag * d],
             "name": f"rjoint{k}"}]


def draw_property(rng, k):
    if rng.random() < 0.5:
        pids = [int(p) for p in rng.choice(SHELL_PIDS, size=int(rng.integers(1, 4)),
                                           replace=False)]
        for _ in range(50):
            ts = float(np.exp(rng.uniform(np.log(0.6), np.log(1.6))))
            if abs(np.log(ts)) >= 0.05:
                break
        return [{"op": "thickness", "pids": pids, "t_scale": ts, "name": f"rthick{k}"}]
    for _ in range(50):
        fa = float(np.exp(rng.uniform(np.log(0.5), np.log(2.0))))
        if abs(np.log(fa)) >= 0.05:
            break
    return [{"op": "scale", "group": str(rng.choice(F.GNAMES)), "factor": fa}]


MENUS = {"connectivity": draw_connectivity, "mesh_density": draw_mesh,
         "element_formulation": draw_formulation, "geometry": draw_geometry,
         "property_control": draw_property}


def enqueue(spec):
    p = os.path.join(PENDD, f"{spec['cid']}.json")
    json.dump(spec, open(p, "w"), indent=1)
    return p


def _counts(rnd, track):
    """(scored_ok, pending_unprocessed) per class for a round/track."""
    ok = {c: 0 for c in C.CLASSES}
    pend = {c: 0 for c in C.CLASSES}
    for fn in os.listdir(C.PARTD):
        if not fn.endswith(".json") or fn.endswith(".build.json"):
            continue
        r = json.load(open(os.path.join(C.PARTD, fn)))
        if r.get("round") == rnd and r.get("track") == track and not r.get("dud"):
            if r.get("cls") in ok:
                ok[r["cls"]] += 1
    for fn in os.listdir(PENDD):
        s = json.load(open(os.path.join(PENDD, fn)))
        if s.get("round") == rnd and s.get("track") == track and \
                not os.path.exists(os.path.join(C.PARTD, fn)):
            pend[s["cls"]] += 1
    return ok, pend


def plan_random(rnd, attempt=0):
    n_new = 0
    ok, pend = _counts(rnd, "random")
    slot = 0
    for cls in C.CLASSES:
        for i in range(2):
            have = ok[cls] + pend[cls]
            if have >= 2:
                slot += 1
                continue
            seed = SEED_BASE + 1000 * rnd + slot + 100000 * attempt
            rng = np.random.default_rng(seed)
            ops = MENUS[cls](rng, f"{rnd}{slot}a{attempt}")
            cid = f"mr{rnd}_{cls[:4]}{slot}" + (f"_a{attempt}" if attempt else "")
            spec = {"cid": cid, "track": "random", "round": rnd, "cls": cls, "seed": seed,
                    "ops": ops, "rationale": "stratified seeded uniform draw (control track)",
                    "evidence": "none (random)"}
            enqueue(spec)
            record_seed({"cid": cid, "seed": seed, "round": rnd, "cls": cls, "attempt": attempt})
            n_new += 1
            slot += 1
            pend[cls] += 1
    print(f"random r{rnd} attempt {attempt}: enqueued {n_new}")
    return n_new


def fill_random(rnd):
    """Replace duds: draw with the next attempt index until quota is enqueuable."""
    for attempt in range(1, 20):
        ok, pend = _counts(rnd, "random")
        need = {c: 2 - ok[c] - pend[c] for c in C.CLASSES if ok[c] + pend[c] < 2}
        if not need:
            print(f"random r{rnd}: quota covered (scored {ok})")
            return
        slot = 0
        n_new = 0
        for cls in C.CLASSES:
            for i in range(2):
                if ok[cls] + pend[cls] >= 2:
                    slot += 1
                    continue
                seed = SEED_BASE + 1000 * rnd + slot + 100000 * attempt
                rng = np.random.default_rng(seed)
                try:
                    ops = MENUS[cls](rng, f"{rnd}{slot}a{attempt}")
                except ValueError as e:
                    print(f"  draw failed ({cls}): {e}")
                    slot += 1
                    continue
                cid = f"mr{rnd}_{cls[:4]}{slot}_a{attempt}"
                if os.path.exists(os.path.join(PENDD, f"{cid}.json")):
                    slot += 1
                    continue
                spec = {"cid": cid, "track": "random", "round": rnd, "cls": cls, "seed": seed,
                        "ops": ops, "rationale": "dud replacement draw", "evidence": "none (random)"}
                enqueue(spec)
                record_seed({"cid": cid, "seed": seed, "round": rnd, "cls": cls,
                             "attempt": attempt})
                pend[cls] += 1
                n_new += 1
                slot += 1
        if n_new:
            print(f"random r{rnd} attempt {attempt}: enqueued {n_new} replacements")
            return
    raise RuntimeError("fill_random: 20 attempts exhausted")


def status():
    for rnd in (1, 2, 3):
        for tr in ("agent", "random"):
            ok, pend = _counts(rnd, tr)
            tot = sum(ok.values())
            if tot or sum(pend.values()):
                print(f"r{rnd} {tr:6s}: scored {tot}/10  " +
                      "  ".join(f"{c[:4]}={ok[c]}+{pend[c]}p" for c in C.CLASSES))
    duds = 0
    dp = os.path.join(C.MY_OUT, "duds.jsonl")
    if os.path.exists(dp):
        duds = sum(1 for line in open(dp) if line.strip())
    print(f"duds: {duds}")


if __name__ == "__main__":
    cmd = sys.argv[1]
    if cmd == "plan_random":
        plan_random(int(sys.argv[2]))
    elif cmd == "fill_random":
        fill_random(int(sys.argv[2]))
    elif cmd == "status":
        status()
