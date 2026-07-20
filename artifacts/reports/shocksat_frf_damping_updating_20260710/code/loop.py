#!/usr/bin/env python3
"""Closed FRF-domain damping updating loop (card §6). Agent track: >=3 rounds of diagnose (train-side, via
score.diagnose_train) -> propose (damping + shape + theta-scale, diagnosis-tied) -> screen (train_proxy,
NO-sampler) -> dev-score top-K (budgeted) -> learn (round summary). Random track: uniform random from the SAME
action space (seed 20260710), no diagnosis/learning. This module reads NO drive cache directly (checker greps);
every dev read is inside score.py and returns scalars only. Resumable: skips cids already in query_log.

Action space (candidate = base package cid + optional theta-scale on theta_MAP + damping spec):
  damping_only : cid=A0, damping in {band zeta, rayleigh, joint eta}          (the new capability)
  shape_only   : cid in reused shape packages, damping fixed 1%               (proven-null comparator)
  both         : cid in reused shape packages, damping = a fitted family
  parametric   : cid=A0, theta-scale (proven-dead control)
"""
import json, os, sys, shutil, time
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import femdamp as D
import femlib as F
import score as SC

WS = D.WS
TRL_PKG = os.path.join(F.ROOT, "artifacts/reports/shocksat_true_remodel_loop_20260706/data/packages")
SHAPE_PKGS = ["a04_welds_t074", "a16_bb_splits_combo", "c06_tb_xface", "a11_ref_202", "a03_welds_t130"]
BUDGET = 60


def setup_shape_pkgs():
    """Copy reused genuine-shape packages (byte-identical femlib, same drive/channel setup) into our workspace
    so they load with F.Package.load. Read-only reuse inputs (hashed via the packages they came from)."""
    dst = os.path.join(WS, "data", "packages")
    os.makedirs(dst, exist_ok=True)
    got = []
    for cid in SHAPE_PKGS:
        src = os.path.join(TRL_PKG, cid + ".npz")
        if os.path.exists(src) and not os.path.exists(os.path.join(dst, cid + ".npz")):
            shutil.copy2(src, os.path.join(dst, cid + ".npz"))
        if os.path.exists(os.path.join(dst, cid + ".npz")):
            got.append(cid)
    return got


def a0d_damping():
    p = os.path.join(WS, "out", "a0d.json")
    if os.path.exists(p):
        return json.load(open(p))["best_damping"]
    return {"kind": "band", "zeta": [0.0032] * 4}


def theta_map(cid):
    return np.asarray(F.Package.load(cid).theta_map()[0], float)


def already_scored(track):
    p = os.path.join(WS, "out", "query_log.jsonl")
    s = set()
    if os.path.exists(p):
        for line in open(p):
            if line.strip():
                r = json.loads(line)
                if r.get("track") == track:
                    s.add(r.get("label", r["cid"]))
    return s


def dev(cands, track):
    """Dev-score a list of candidate dicts (budget-enforced, resumable). cand: {cid,label,theta_scale,damping,
    family,ablation,rationale}."""
    done = already_scored(track)
    n = len(done)
    out = []
    for c in cands:
        if n >= BUDGET:
            print(f"  [budget] {track} at {n}/{BUDGET}; stopping", flush=True)
            break
        label = c["label"]
        if label in done:
            continue
        base = c["cid"]
        th = theta_map(base)
        if c.get("theta_scale") is not None:
            th = th * np.asarray(c["theta_scale"], float)
        rec = SC.score_candidate(base, track, damping=c["damping"], theta_override=th,
                                 family=c["family"], ablation=c["ablation"], rationale=c["rationale"],
                                 evidence=c.get("evidence", ""), enforce_budget=True, label=label)
        # store under the candidate LABEL so shape+damping variants of one base pkg are distinct in the log
        rec_disk = os.path.join(WS, "out", "cand_scores"); os.makedirs(rec_disk, exist_ok=True)
        json.dump({**rec, "label": label}, open(os.path.join(rec_disk, f"{track}_{label}.json"), "w"))
        out.append({"label": label, **{k: rec[k] for k in ("P1p_mean", "P3_mean", "P2p_mean",
                                                            "alignment_gain", "P1p_folds", "family",
                                                            "ablation", "damping_dim")}})
        n += 1
        print(f"  [{track} {n}/{BUDGET}] {label:26s} P1'={rec['P1p_mean']} P3={rec['P3_mean']} "
              f"P2'={rec['P2p_mean']}", flush=True)
    return out


def screen(cands, keep):
    """NO-sampler train_proxy screen; keep top `keep` by proxy_P1p (tie-break lower proxy_P2p)."""
    scored = []
    for c in cands:
        th = theta_map(c["cid"])
        if c.get("theta_scale") is not None:
            th = th * np.asarray(c["theta_scale"], float)
        p = SC.train_proxy(c["cid"], damping=c["damping"], theta_override=th)
        c["proxy_P1p"], c["proxy_P2p"] = p["proxy_P1p"], p["proxy_P2p"]
        scored.append(c)
    scored.sort(key=lambda c: (-(c["proxy_P1p"] or -9), c["proxy_P2p"] or 9))
    return scored[:keep]


# ------------------------------------------------------------- proposal generators (diagnosis-tied)
def band_variants(base_z, worst_band):
    """+/- damping in the worst-mismatch band, around a base 4-vector."""
    outs = []
    for scale, tag in [(1.5, "hi"), (0.66, "lo")]:
        z = list(base_z); z[worst_band] = float(np.clip(z[worst_band] * scale, D.ZETA_LO, D.ZETA_HI))
        outs.append((z, f"band_w{worst_band}_{tag}"))
    return outs


def agent_round1(diag, a0d):
    z_a0d = a0d.get("zeta", [0.0032] * 4)
    wb = diag["worst_band"]
    cands = []
    # damping_only
    cands.append(dict(cid="A0", label="d_a0d", theta_scale=None, damping=a0d,
                      family="damping_band", ablation="damping_only",
                      rationale=f"A0d best-fit damping; worst train band {wb}"))
    for z, tag in band_variants(z_a0d, wb):
        cands.append(dict(cid="A0", label=f"d_{tag}", theta_scale=None,
                          damping={"kind": "band", "zeta": z}, family="damping_band",
                          ablation="damping_only", rationale=f"band zeta perturb targeting band {wb}"))
    for a, b, tag in [(0.5, 2e-6, "ray1"), (1.5, 5e-7, "ray2")]:
        cands.append(dict(cid="A0", label=f"d_{tag}", theta_scale=None,
                          damping={"kind": "rayleigh", "alpha": a, "beta": b}, family="damping_rayleigh",
                          ablation="damping_only", rationale="Rayleigh proportional damping"))
    for eta, tag in [(0.03, "eta_lo"), (0.08, "eta_hi")]:
        cands.append(dict(cid="A0", label=f"d_{tag}", theta_scale=None,
                          damping={"kind": "band", "zeta": [0.0032] * 4,
                                   "eta": {g: eta for g in D.JOINT_GROUPS}}, family="damping_joint_eta",
                          ablation="damping_only", rationale=f"joint loss factor eta={eta} on CBUSH groups"))
    # shape_only (reused genuine-shape packages, fixed 1%)
    for cid in setup_shape_pkgs():
        cands.append(dict(cid=cid, label=f"s_{cid}", theta_scale=None,
                          damping={"kind": "fixed", "zeta": 0.01}, family="shape",
                          ablation="shape_only", rationale=f"reused genuine-shape edit {cid} (proven-null fam)"))
    # parametric controls (theta-scale on A0)
    rng = np.random.default_rng(101)
    for i in range(2):
        sc = np.exp(rng.normal(0, 0.15, len(F.Package.load("A0").free_names)))
        cands.append(dict(cid="A0", label=f"p_ctrl{i}", theta_scale=sc.tolist(),
                          damping={"kind": "fixed", "zeta": 0.01}, family="parametric",
                          ablation="shape_only", rationale="theta-scale parametric control (proven-dead fam)"))
    return cands


def agent_round2(prior, a0d):
    """Refine whichever damping family moved P1'/P2' most; add shape+damping 'both' candidates."""
    # which family had best dev P1' among damping_only in round 1
    dcands = [r for r in prior if r["ablation"] == "damping_only" and r["P1p_mean"] is not None]
    best_d = max(dcands, key=lambda r: r["P1p_mean"]) if dcands else None
    cands = []
    z_a0d = a0d.get("zeta", [0.0032] * 4)
    # refine around best damping band values
    for f in (0.8, 1.25):
        z = [float(np.clip(v * f, D.ZETA_LO, D.ZETA_HI)) for v in z_a0d]
        cands.append(dict(cid="A0", label=f"d_refine_{f}", theta_scale=None,
                          damping={"kind": "band", "zeta": z}, family="damping_band",
                          ablation="damping_only", rationale=f"refine band zeta x{f} around A0d"))
    # 'both': best shape pkgs + fitted damping
    for cid in ["a04_welds_t074", "a16_bb_splits_combo", "c06_tb_xface"]:
        if os.path.exists(os.path.join(WS, "data", "packages", cid + ".npz")):
            cands.append(dict(cid=cid, label=f"b_{cid}", theta_scale=None, damping=a0d,
                              family="shape_plus_damping", ablation="both",
                              rationale=f"shape {cid} + A0d damping (both families)"))
    return cands


def agent_round3(prior, a0d):
    """Best combo + a joint eta + band combo."""
    cands = []
    z_a0d = a0d.get("zeta", [0.0032] * 4)
    cands.append(dict(cid="A0", label="d_band_eta", theta_scale=None,
                      damping={"kind": "band", "zeta": z_a0d, "eta": {g: 0.05 for g in D.JOINT_GROUPS}},
                      family="damping_combo", ablation="damping_only",
                      rationale="band zeta + joint eta combined (<=6 params)"))
    # best 'both' from round 2 refined
    both = [r for r in prior if r["ablation"] == "both" and r["P1p_mean"] is not None]
    if both:
        best_both = max(both, key=lambda r: r["P1p_mean"])
        cid = best_both["label"][2:]
        if os.path.exists(os.path.join(WS, "data", "packages", cid + ".npz")):
            cands.append(dict(cid=cid, label=f"b_{cid}_eta", theta_scale=None,
                              damping={"kind": "band", "zeta": z_a0d,
                                       "eta": {g: 0.05 for g in D.JOINT_GROUPS}},
                              family="shape_plus_damping", ablation="both",
                              rationale=f"best 'both' {cid} + band+eta damping"))
    return cands


def random_track(n=40, seed=20260710):
    rng = np.random.default_rng(seed)
    bases = ["A0"] + setup_shape_pkgs()
    npar = len(F.Package.load("A0").free_names)
    cands = []
    for i in range(n):
        base = bases[rng.integers(len(bases))]
        kind = rng.choice(["band", "rayleigh", "eta", "fixed"])
        if kind == "band":
            dmp = {"kind": "band", "zeta": np.clip(rng.uniform(D.ZETA_LO, D.ZETA_HI, 4),
                                                   D.ZETA_LO, D.ZETA_HI).tolist()}
        elif kind == "rayleigh":
            dmp = {"kind": "rayleigh", "alpha": float(rng.uniform(0.05, 3.0)),
                   "beta": float(rng.uniform(1e-7, 5e-6))}
        elif kind == "eta":
            dmp = {"kind": "band", "zeta": [0.0032] * 4,
                   "eta": {g: float(rng.uniform(0.005, D.ETA_HI)) for g in D.JOINT_GROUPS}}
        else:
            dmp = {"kind": "fixed", "zeta": float(rng.uniform(D.ZETA_LO, D.ZETA_HI))}
        ts = np.exp(rng.normal(0, 0.12, npar)).tolist() if (base == "A0" and rng.random() < 0.5) else None
        abl = "both" if (base != "A0" and dmp["kind"] != "fixed") else \
              ("shape_only" if base != "A0" else "damping_only")
        cands.append(dict(cid=base, label=f"rnd{i:03d}", theta_scale=ts, damping=dmp,
                          family="random", ablation=abl, rationale=f"random {kind} on {base}"))
    return cands


def main():
    track = sys.argv[1] if len(sys.argv) > 1 else "agent"
    a0d = a0d_damping()
    if track == "agent":
        diag = SC.diagnose_train("A0", theta_override=theta_map("A0"))
        json.dump(diag, open(os.path.join(WS, "out", "diagnosis_r1.json"), "w"), indent=2)
        print("diagnosis:", json.dumps(diag), flush=True)
        # Round 1
        c1 = screen(agent_round1(diag, a0d), keep=16)
        json.dump([{k: v for k, v in c.items() if k != "damping"} | {"damping": c["damping"]} for c in c1],
                  open(os.path.join(WS, "out", "proposals_r1.json"), "w"), indent=1)
        r1 = dev(c1, "agent")
        _summary(1, r1)
        # Round 2
        c2 = screen(agent_round2(r1, a0d), keep=8)
        r2 = dev(c2, "agent")
        _summary(2, r2)
        # Round 3
        c3 = screen(agent_round3(r1 + r2, a0d), keep=5)
        r3 = dev(c3, "agent")
        _summary(3, r3)
    elif track == "random":
        cr = random_track()
        rr = dev(cr, "random")
        _summary(99, rr)


def _summary(r, recs):
    p = os.path.join(WS, "out", f"round_r{r}_summary.md")
    lines = [f"# Round {r} summary\n"]
    recs2 = [x for x in recs if x.get("P1p_mean") is not None]
    recs2.sort(key=lambda x: -x["P1p_mean"])
    for x in recs2:
        lines.append(f"- {x['label']:26s} P1'={x['P1p_mean']:.4f} P3={x['P3_mean']:.4f} "
                     f"P2'={x['P2p_mean']:.4f} [{x['ablation']}/{x['family']}]")
    open(p, "w").write("\n".join(lines) + "\n")
    print("\n".join(lines), flush=True)


if __name__ == "__main__":
    main()
