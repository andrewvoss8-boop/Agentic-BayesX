#!/usr/bin/env python3
"""Agentic remodeling track — CANDIDATE GENERATION (task card §3). O(100+) model-form candidates within the
ALLOWED families only (local interface/joint compliance incl. new DOFs; per-region thickness/offset [K-block
modulus-proxy, labeled]; connectivity variants; weld/contact representations; mass-distribution variants).
FORBIDDEN: from-scratch geometry rebuild (Card D verdict) — none generated.

Seeded from the diagnosis (shocksat_fem_remesh_20260618/region_diagnosis.md: bolted joint ch52/PID801, steel
bottom corner, 150-210 Hz dense cluster, bulkhead/strut interfaces, dish + impact face local modes) PLUS a
random-exploration tranche (fixed seed). Every candidate = a remodel.py edit dict (scale / bush_k / couple /
mass_scale / cable_mass_factor) + family + rationale. Output: out/candidates.json.
"""
from __future__ import annotations
import json, sys
from pathlib import Path
import numpy as np

WS = Path(__file__).resolve().parent.parent
TWIN = WS.parent / "shocksat_fem_modal_twin_20260609"

fm = np.load(TWIN / "fem_model.npz", allow_pickle=True)
PBUSH = {int(k): v["k"] for k, v in json.loads(str(fm["pbush"])).items()}
SHELLS = sorted(int(p) for p in json.loads(str(fm["pshell"])))
JOINT_PIDS = [801, 802, 803, 804, 805, 806, 807]
CONTACT_PID = 902
WELD_STEEL = [104, 105, 106]; WELD_AL = [204, 205, 206]
BOTTOM = [101, 102, 103]; TOP = [201, 202, 203]; PLATES = [501, 601, 701]; CROSS = [401]; BRACKETS = [301, 302]

C = []  # candidates


def add(cid, family, edit, rationale, seed_source):
    C.append({"id": cid, "family": family, "edit": edit, "rationale": rationale, "seed": seed_source})


# ---- 1. joint/interface compliance (bush_k anisotropic variants; NOT the failed uniform theta-scale) ----
# diagnosis: joints finite+non-identifiable under UNIFORM scaling; anisotropic re-representation is the
# allowed fresh lever (trans-vs-rot split, per-joint).
for pid in JOINT_PIDS:
    k0 = np.array(PBUSH[pid], float)
    for tag, tf, rf in [("transSoft", 0.2, 1.0), ("transStiff", 5.0, 1.0), ("rotSoft", 1.0, 0.1),
                        ("rotStiff", 1.0, 10.0), ("allSoft", 0.3, 0.3)]:
        k = k0.copy(); k[:3] *= tf; k[3:] *= rf
        add(f"bush{pid}_{tag}", "joint_compliance", {"bush_k": {str(pid): k.tolist()}},
            f"PID {pid} anisotropic {tag} (trans x{tf}, rot x{rf}); joint stiffness re-representation at a "
            f"bolted/bulkhead interface", "diagnosis:joints")
# contact 902 (strut base contact: k=[6800,0,0,0,0,0] nominal — add shear/normal terms or scale)
k9 = np.array(PBUSH.get(CONTACT_PID, [6800, 0, 0, 0, 0, 0]), float)
for tag, kk in [("soft", (k9 * 0.1).tolist()), ("stiff", (k9 * 10).tolist()),
                ("shear", [k9[0], 3400.0, 3400.0, 0, 0, 0]), ("full", [6800.0] * 3 + [0.0] * 3)]:
    add(f"contact902_{tag}", "joint_compliance", {"bush_k": {str(CONTACT_PID): kk}},
        f"strut-base contact PID902 {tag}: add/scale contact terms (diagnosis: strut_base region MAC 0.48)",
        "diagnosis:strut_base")

# ---- 2. connectivity variants (NEW DOF couple springs; reuse proven pair-generators from correlate_all) ----
sys.path.insert(0, str(WS.parent / "shocksat_psd_envelope_twin_20260623" / "code"))
import correlate_all as CA  # noqa: E402  (read-only import; provides CORR_EDITS with couple pair lists)
for src in ["cross_bolt", "cross_weld", "cross_bolt_trans"]:
    e = CA.CORR_EDITS[src]
    if "couple" not in e:
        continue
    pairs = e["couple"]["pairs"]
    for tag, kv in [("k1e4", [1e4] * 3 + [0.0] * 3), ("k1e5", [1e5] * 3 + [0.0] * 3),
                    ("k1e6", [1e6] * 3 + [0.0] * 3), ("k1e5_rot", [1e5] * 6)]:
        add(f"{src}_{tag}", "connectivity", {"couple": {"pairs": pairs, "k": kv}},
            f"cross-beam-to-wall coincident-node coupling ({src}), spring {tag}; connectivity at the bulkhead "
            f"interfaces driving the 150-210 Hz cluster", "diagnosis:150-210Hz_cluster")

# ---- 3. weld / contact representations (per-PID weld stiffness re-representation) ----
for pid in WELD_STEEL + WELD_AL:
    for tag, s in [("soft", 0.3), ("stiff", 3.0)]:
        add(f"weld{pid}_{tag}", "weld_contact", {"scale": {f"shell_{pid}": s}},
            f"weld shell PID {pid} x{s} (steel-corner/aluminum weld representation; diagnosis: steel bottom "
            f"corner + NASA weld knob)", "diagnosis:welds")
for tag, s in [("steelwelds_soft", {"shell_104": 0.3, "shell_105": 0.3, "shell_106": 0.3}),
               ("steelwelds_stiff", {"shell_104": 3.0, "shell_105": 3.0, "shell_106": 3.0}),
               ("alwelds_soft", {"shell_204": 0.3, "shell_205": 0.3, "shell_206": 0.3}),
               ("alwelds_stiff", {"shell_204": 3.0, "shell_205": 3.0, "shell_206": 3.0})]:
    add(tag, "weld_contact", {"scale": s}, "grouped weld representation variant", "diagnosis:welds")

# ---- 4. per-region thickness/offset field (K-block modulus-proxy, LABELED: scales K like E; t^3-bending
#         vs t-membrane not separated in the block basis — an offset/thickness FIELD proxy) ----
for pid in SHELLS:
    for tag, s in [("lo", 0.7), ("hi", 1.4)]:
        add(f"shell{pid}_{tag}", "thickness_offset_proxy", {"scale": {f"shell_{pid}": s}},
            f"per-PID stiffness field x{s} on shell {pid} (finer granularity than the 9-group theta)",
            "diagnosis:regions")
# targeted bottom-corner / cluster combos
add("bottomcorner_soft", "thickness_offset_proxy",
    {"scale": {"shell_101": 0.7, "shell_104": 0.5}}, "steel bottom corner: panel+weld soft combo",
    "diagnosis:steel_bottom_corner")
add("bottomcorner_stiff", "thickness_offset_proxy",
    {"scale": {"shell_101": 1.4, "shell_104": 2.0}}, "steel bottom corner: panel+weld stiff combo",
    "diagnosis:steel_bottom_corner")
add("cluster_cross_plates", "thickness_offset_proxy",
    {"scale": {"shell_401": 1.3, "shell_501": 0.8}}, "150-210 Hz cluster: cross stiffer + plate softer",
    "diagnosis:150-210Hz_cluster")
add("cluster_cross_plates2", "thickness_offset_proxy",
    {"scale": {"shell_401": 0.75, "shell_501": 1.25}}, "150-210 Hz cluster: cross softer + plate stiffer",
    "diagnosis:150-210Hz_cluster")

# ---- 5. mass-distribution variants ----
for region in ["steel", "aluminum", "dish", "cross"]:
    for tag, f in [("lo", 0.85), ("hi", 1.15)]:
        add(f"mass_{region}_{tag}", "mass_distribution", {"mass_scale": {region: f}},
            f"region mass x{f} ({region}); mass-distribution model form", "diagnosis:mass")
for tag, f in [("half", 0.5), ("full", 1.0), ("double", 2.0)]:
    add(f"cablemass_{tag}", "mass_distribution", {"cable_mass_factor": f},
        f"cable-harness mass at sensor nodes x{f} of accel mass (known un-modeled mass)", "diagnosis:cable")
add("dishmass_lo", "mass_distribution", {"mass_scale": {"dish": 0.8}}, "dish mass low", "diagnosis:dish")
add("dishmass_hi", "mass_distribution", {"mass_scale": {"dish": 1.25}}, "dish mass high", "diagnosis:dish")

# ---- 6. RANDOM exploration tranche (card §3; fixed seed, 2-4 knobs each, log-uniform) ----
rng = np.random.default_rng(20260702)
shell_names = [f"shell_{p}" for p in SHELLS]
for i in range(30):
    nk = int(rng.integers(2, 5))
    edit = {}; parts = []
    for _ in range(nk):
        kind = rng.choice(["scale", "bush", "mass"], p=[0.6, 0.25, 0.15])
        if kind == "scale":
            nm = str(rng.choice(shell_names)); s = float(np.exp(rng.uniform(np.log(0.5), np.log(2.0))))
            edit.setdefault("scale", {})[nm] = round(s, 3); parts.append(f"{nm}x{s:.2f}")
        elif kind == "bush":
            pid = int(rng.choice(JOINT_PIDS)); k0 = np.array(PBUSH[pid], float)
            tf = float(np.exp(rng.uniform(np.log(0.1), np.log(10.0))))
            rf = float(np.exp(rng.uniform(np.log(0.1), np.log(10.0))))
            k = k0.copy(); k[:3] *= tf; k[3:] *= rf
            edit.setdefault("bush_k", {})[str(pid)] = [round(x, 1) for x in k.tolist()]
            parts.append(f"bush{pid}(t{tf:.2f},r{rf:.2f})")
        else:
            region = str(rng.choice(["steel", "aluminum", "dish", "cross"]))
            f = float(np.exp(rng.uniform(np.log(0.85), np.log(1.18))))
            edit.setdefault("mass_scale", {})[region] = round(f, 3); parts.append(f"m_{region}x{f:.2f}")
    add(f"rand{i:02d}", "random_tranche", edit, "random exploration: " + ", ".join(parts), "random")

# baseline reference (M0 — scored through the same screen as a sanity anchor, not an M1 candidate)
add("baseline", "reference", {}, "inherited FEM unchanged (M0 anchor for the screen)", "reference")

out = {"n_candidates": len(C), "families_within_allowed": True,
       "forbidden_check": "no candidate rebuilds geometry from scratch; all edits are scale/bush_k/couple/"
                          "mass_scale/cable_mass on the inherited mesh",
       "seed_rng": 20260702, "candidates": C}
(WS / "out").mkdir(exist_ok=True)
(WS / "out" / "candidates.json").write_text(json.dumps(out, indent=1))
fam = {}
for c in C:
    fam[c["family"]] = fam.get(c["family"], 0) + 1
print(f"{len(C)} candidates:", fam)
