#!/usr/bin/env python3
"""Generate the Card D correlated-update edit specs (JSON) for edit_solve.py.

Each spec is a dict {scale:{block:factor}} or {bush_k:{pid:[6 k]}}.
groups.json maps the 9 calibration groups -> per-PID stiffness blocks.
The calibrated-theta spec applies the modal-twin NUTS posterior theta (the
actual data-driven FEM update) by expanding each group's theta over its blocks.
"""
import json, os
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
groups = json.load(open(f"{HERE}/groups.json"))["groups"]

# modal-twin posterior median theta (nuts_full / theta_full.json; converged)
THETA = {"al_welds":1.0186,"angle_brackets":1.0104,"bottom_box":0.9636,
         "contact":0.9836,"cross_beam":1.0383,"joints":1.0928,"plates":0.9761,
         "steel_welds":1.0120,"top_box":1.0475}

def grp_scale(theta_by_group):
    s = {}
    for g, blocks in groups.items():
        if g in theta_by_group:
            for b in blocks:
                s[b] = theta_by_group[g]
    return s

specs = {}
# 1. THE data-driven update: full calibrated theta
specs["e01_calibrated_theta"] = {"scale": grp_scale(THETA),
    "note":"modal-twin NUTS posterior median theta (the data-driven FEM update)"}
# 2-3. joint/interface stiffness (region local physics; joints store ~3% SE)
specs["e02_joints_soft"]  = {"scale": grp_scale({"joints":0.5,"contact":0.5}),
    "note":"soften all bolted/contact joints x0.5"}
specs["e03_joints_stiff"] = {"scale": grp_scale({"joints":2.0,"contact":2.0}),
    "note":"stiffen all joints x2"}
# 4-7. SE-dominant box moduli brackets (the actual modal drivers)
specs["e04_bottombox_soft"] = {"scale": grp_scale({"bottom_box":0.9}),"note":"bottom_box x0.9"}
specs["e05_bottombox_stiff"]= {"scale": grp_scale({"bottom_box":1.1}),"note":"bottom_box x1.1"}
specs["e06_topbox_stiff"]   = {"scale": grp_scale({"top_box":1.1}),"note":"top_box x1.1"}
specs["e07_topbox_soft"]    = {"scale": grp_scale({"top_box":0.9}),"note":"top_box x0.9"}
# 8. targeted bolted joint at ch52 (PBUSH 801)
specs["e08_joint801_soft"]  = {"scale": {"bush_801":0.3},"note":"bolted joint PID801 x0.3 (ch52)"}
# 9. targeted strut base at ch92 (PBUSH 807)
specs["e09_strut807_soft"]  = {"scale": {"bush_807":0.3},"note":"strut base PID807 x0.3 (ch92)"}
# 10. add contact stiffness at ch92 (PBUSH 902 nearly zero -> x20)
specs["e10_contact902_stiff"]={"scale":{"bush_902":20.0},"note":"plate contact PID902 x20 (ch92)"}

od = f"{HERE}/out/edit_specs"; os.makedirs(od, exist_ok=True)
for eid, spec in specs.items():
    json.dump(spec, open(f"{od}/{eid}.json","w"), indent=1)
print(f"wrote {len(specs)} edit specs to out/edit_specs/:")
for eid in specs: print("  ", eid, specs[eid].get("note"))
