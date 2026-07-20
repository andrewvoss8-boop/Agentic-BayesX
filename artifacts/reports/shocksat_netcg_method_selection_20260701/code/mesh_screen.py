#!/usr/bin/env python3
"""Axis-B step 1: MESH SCREEN on a cheap, BLIND, QOI(shear)-weighted proxy. Keeps the top ~3 candidate meshes.

Reuses (imports, never edits) correlate_all's solve machinery (RS=rescore_sigma reduction, RM=remodel edits,
.ash measured modes). For each edit we:
  - solve reduced modes (full-order build_K/build_M -> RS.T reduction -> eigsh k=80) [expensive -> detached],
  - MAC-match to the .ash survey (MAC>=0.3),
  - PROXY score = matched-mode frequency RMS error to measured .ash, band-weighted to the SHEAR band
    (114-197 Hz, where the measured global modes drive tray_shear) + global matched MAC. NO amplitude LSQ
    (blind -> avoids the in-sample §1.1 artifact). This is an IMPERFECT PROXY; it does NOT select the twin.
  - drumhead check: RMS shift of the FEM modes in 228-260 Hz (the normal-QOI band) vs inherited = the
    "does this mesh degrade NORMAL" flag (frequency only; the drumhead SHAPE/amplitude is unmeasurable).

Resumable: writes out/mesh_screen/<edit>.json, skips finished. Run: python3 mesh_screen.py [--pool subset|all]
"""
from __future__ import annotations
import sys, json, time
from pathlib import Path
import numpy as np
from scipy.sparse.linalg import eigsh

WS = Path(__file__).resolve().parent.parent
BASE = WS.parent / "shocksat_psd_envelope_twin_20260623"
sys.path.insert(0, str(BASE / "code"))
import rescore_sigma as RS
import remodel as RM
import correlate_all as CA           # for CORR_EDITS + modelform edits via RM.EDITS

OUT = WS / "out" / "mesh_screen"; OUT.mkdir(parents=True, exist_ok=True)
SHEAR_BAND = (114.0, 197.0)          # measured global modes that drive tray_shear
DRUM_BAND = (228.0, 260.0)           # normal-QOI drumhead band

SUBSET = ["baseline", "bottombox_E_lo", "plates_E_hi", "cross_bolt_trans", "plates_E_lo", "bottombox_E_hi",
          "dish_mass_lo", "dish_mass_hi", "al_rho_lo", "steelLight_alHeavy", "joints_all_soft", "cross_bolt"]


def edit_dict(eid):
    return CA.CORR_EDITS.get(eid, RM.EDITS.get(eid, {}))


def solve_and_score(eid):
    op = OUT / f"{eid}.json"
    if op.exists():
        return json.load(open(op))
    t0 = time.time()
    edit = edit_dict(eid)
    Kr = (RS.T.T @ RM.build_K(edit) @ RS.T).tocsc(); Mr = (RS.T.T @ RM.build_M(edit) @ RS.T).tocsc()
    vals, vecs = eigsh(Kr, k=80, M=Mr, sigma=-1.0e3, which="LM")
    o = np.argsort(vals); vals, vecs = vals[o], vecs[:, o]
    ffem = np.sqrt(np.clip(vals, 0, None)) / (2 * np.pi)
    mshapes, mmask, mfreqs = RS.mm["shapes"], RS.mm["measured"], RS.mm["freqs"]
    obs_dofs = np.array([6 * RM.G2I[int(n)] + cc for n in RS.mm["nodes"] for cc in range(3)])
    obs_V = np.asarray(RS.T[obs_dofs, :] @ vecs); live = mmask.reshape(-1)
    pf_, pt = obs_V[live, :], mshapes.reshape(33, -1)[:, live]
    MAC = (pt @ pf_) ** 2 / (np.sum(pt ** 2, 1)[:, None] * np.sum(pf_ ** 2, 0)[None, :] + 1e-300)
    ridx, kidx, macs = [], [], []
    for it in range(33):
        jf = int(np.argmax(MAC[it, 6:]) + 6)
        if MAC[it, jf] > 0.3:
            ridx.append(it); kidx.append(jf); macs.append(float(MAC[it, jf]))
    fmeas = mfreqs[ridx]; ffem_m = ffem[kidx]
    ferr = (ffem_m - fmeas) / fmeas                                       # relative freq error per matched mode
    # SHEAR-band weight (emphasize the measured global modes that drive tray_shear)
    w = np.where((fmeas >= SHEAR_BAND[0]) & (fmeas <= SHEAR_BAND[1]), 1.0, 0.25)
    freq_rms_shear = float(np.sqrt(np.sum(w * ferr ** 2) / np.sum(w)))
    freq_rms_all = float(np.sqrt(np.mean(ferr ** 2)))
    mac_shear = float(np.average([m for m, f in zip(macs, fmeas) if SHEAR_BAND[0] <= f <= SHEAR_BAND[1]]
                                 or [np.mean(macs)]))
    # drumhead band FEM freqs (for the degrade-normal check)
    drum = sorted(round(float(f), 1) for f in ffem if DRUM_BAND[0] <= f <= DRUM_BAND[1])
    # single screen score: lower is better -> convert to higher-better = mac_shear - 3*freq_rms_shear
    screen = round(mac_shear - 3.0 * freq_rms_shear, 4)
    rec = {"edit_id": eid, "n_matched": len(kidx), "global_MAC": round(float(np.mean(macs)), 3),
           "mac_shear_band": round(mac_shear, 3),
           "freq_rms_shear_pct": round(100 * freq_rms_shear, 2), "freq_rms_all_pct": round(100 * freq_rms_all, 2),
           "screen_score": screen, "drum_freqs_hz": drum, "runtime_s": round(time.time() - t0, 1)}
    json.dump(rec, open(op, "w"), indent=1)
    print(f"[{eid:18s}] screen={screen:+.3f} MAC_shear={mac_shear:.3f} fRMS_shear={100*freq_rms_shear:.2f}% "
          f"({rec['runtime_s']}s) drum={drum}", flush=True)
    return rec


def main(pool):
    ids = SUBSET if pool == "subset" else (list(CA.CORR_EDITS) + [e for e in RM.EDITS if e not in CA.CORR_EDITS])
    rows = [solve_and_score(e) for e in ids]
    # inherited drumhead freqs for the degrade check
    inh = next((r for r in rows if r["edit_id"] == "baseline"), None)
    inh_drum = np.array(inh["drum_freqs_hz"]) if inh else None
    for r in rows:
        if inh_drum is not None and r["drum_freqs_hz"]:
            df = np.array(r["drum_freqs_hz"])
            n = min(len(df), len(inh_drum))
            r["drum_shift_vs_inherited_pct"] = round(float(100 * np.sqrt(np.mean(
                ((df[:n] - inh_drum[:n]) / inh_drum[:n]) ** 2))), 2) if n else None
    ranked = sorted([r for r in rows if r["edit_id"] != "baseline"], key=lambda r: -r["screen_score"])
    top3 = [r["edit_id"] for r in ranked[:3]]
    kept = ["baseline"] + top3            # inherited + top 3 = the mesh axis for Stage 2
    summary = {"proxy": "BLIND shear-band-weighted matched-mode freq RMS error + MAC; NO amplitude fit; "
                        "IMPERFECT PROXY (does NOT select the twin — the post-update held-out-QOI bake-off does)",
               "shear_band_hz": list(SHEAR_BAND), "drum_band_hz": list(DRUM_BAND),
               "n_screened": len(rows), "ranking": [(r["edit_id"], r["screen_score"]) for r in
                                                    sorted(rows, key=lambda r: -r["screen_score"])],
               "kept_meshes_for_bakeoff": kept, "baseline_screen": inh["screen_score"] if inh else None,
               "rows": rows}
    (WS / "out" / "mesh_screen_summary.json").write_text(json.dumps(summary, indent=2))
    print("\n=== MESH SCREEN (proxy, imperfect) ===")
    for r in sorted(rows, key=lambda r: -r["screen_score"]):
        tag = " <= INHERITED" if r["edit_id"] == "baseline" else (" *KEEP*" if r["edit_id"] in top3 else "")
        print(f"  {r['edit_id']:18s} screen={r['screen_score']:+.3f} MAC_sh={r['mac_shear_band']:.3f} "
              f"fRMS_sh={r['freq_rms_shear_pct']:.2f}% drumShift={r.get('drum_shift_vs_inherited_pct')}%{tag}")
    print(f"\nKEPT for bake-off (inherited + top 3): {kept}")


if __name__ == "__main__":
    pool = "all" if "--pool" in sys.argv and sys.argv[sys.argv.index("--pool") + 1] == "all" else "subset"
    main(pool)
