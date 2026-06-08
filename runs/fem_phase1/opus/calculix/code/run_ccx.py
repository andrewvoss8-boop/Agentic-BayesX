"""
One-command CalculiX driver: build deck(s), run ccx *FREQUENCY, parse, render,
mesh convergence, runtime. Set CCX to the ccx binary (defaults to the isolated
conda env created during setup).

Run: ../../.venv/bin/python run_ccx.py
"""
import os
import sys
import json
import time
import subprocess
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
MODEL = os.path.abspath(os.path.join(HERE, "..", "model"))
sys.path.insert(0, HERE)
import make_inp
import parse_ccx

CCX = os.environ.get("CCX", os.path.expanduser(
    "~/miniforge3_bayesx_femphase1/envs/ccx/bin/ccx"))


def run_job(jobname):
    t = time.time()
    r = subprocess.run([CCX, jobname], cwd=MODEL, capture_output=True, text=True)
    dt = time.time()-t
    if "Job finished" not in r.stdout:
        print(r.stdout[-1500:]); raise RuntimeError(f"ccx failed for {jobname}")
    return parse_ccx.parse_dat_freqs(os.path.join(MODEL, jobname+".dat")), dt


def main():
    t0 = time.time(); cmds = []
    # baseline + convergence meshes (independent ccx runs)
    make_inp.build_deck(target_h_mm=22.0, nmodes=16, jobname="hexapod")
    f0, d0 = run_job("hexapod"); cmds.append({"name": "baseline_h22", "s": d0})
    make_inp.build_deck(target_h_mm=30.0, nmodes=16, jobname="hexapod_c")
    fc, dc = run_job("hexapod_c"); cmds.append({"name": "coarse_h30", "s": dc})
    make_inp.build_deck(target_h_mm=16.0, nmodes=16, jobname="hexapod_f")
    ff, df = run_job("hexapod_f"); cmds.append({"name": "fine_h16", "s": df})

    # restore baseline meta + parse (figures + results.json)
    make_inp.build_deck(target_h_mm=22.0, nmodes=16, jobname="hexapod")
    parse_ccx.main()

    nmode = min(10, len(f0))
    conv = {
        "coarse_h30_hz": [round(float(x), 3) for x in fc[:nmode]],
        "baseline_h22_hz": [round(float(x), 3) for x in f0[:nmode]],
        "fine_h16_hz": [round(float(x), 3) for x in ff[:nmode]],
        "max_abs_shift_h22_to_h16_hz": round(float(np.max(np.abs(ff[:nmode]-f0[:nmode]))), 3),
        "max_pct_shift_h22_to_h16": round(float(np.max(np.abs((ff[:nmode]-f0[:nmode])/f0[:nmode]))*100), 2),
        "note": "suspension modes (1-4) are nearly mesh-independent; the dense tray-flex cluster (>=mode 5) shifts more as the overhanging-corner bending resolves.",
    }
    res_path = os.path.join(HERE, "..", "results.json")
    results = json.load(open(res_path))
    results["mesh_convergence"] = conv
    results["runtime_s"] = round(time.time()-t0, 2)
    json.dump(results, open(res_path, "w"), indent=2)

    rt = {"commands": cmds,
          "active_runtime_s": round(sum(c["s"] for c in cmds), 2),
          "elapsed_wallclock_s": round(time.time()-t0, 2)}
    json.dump(rt, open(os.path.join(HERE, "..", "runtime.json"), "w"), indent=2)
    print("convergence max %% shift h22->h16:", conv["max_pct_shift_h22_to_h16"])
    print("baseline first 4:", [round(x, 2) for x in f0[:4]])


if __name__ == "__main__":
    main()
