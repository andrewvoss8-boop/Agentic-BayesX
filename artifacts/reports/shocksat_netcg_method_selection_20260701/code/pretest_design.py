#!/usr/bin/env python3
"""Follow-on #3 — PRE-TEST DESIGN: the >200 Hz plate/drumhead test that buys down the NORMAL-QOI band.

Turns the "next test dollar" recommendation into numbers (NO NUTS, reduced-model shapes):
  1. Identify the drumhead modes (228-260 Hz) that are UNMEASURED yet drive tray_normal_Z.
  2. Show the CURRENT instrumented sensors sit near the drumhead NODE RING (small modal |Z|) and miss the
     plate-center antinode -> that is why the shape is unresolved (shape-trust 45%).
  3. Propose a candidate plate sensor grid; GREEDILY place accelerometers (E-optimal: maximize the min eigenvalue
     of the drumhead-subspace Fisher information Phi^T Phi) so all target shapes become resolvable.
  4. BUY-DOWN: normal-QOI 95% band factor vs number of added plate sensors (resolved drumhead modes move from the
     unmeasured tier SD_A_U=0.80 to the measured tier SD_A_M=0.35).
  5. Recommend the DRIVE (from Stage-0 observability) + sensor count + placement.

Reuses netcg_qoi (reduced-model field) + the cached L5 theta_map. Writes out/pretest_design.json.
"""
from __future__ import annotations
import sys, json
from pathlib import Path
import numpy as np

WS = Path(__file__).resolve().parent.parent
BASE = WS.parent / "shocksat_psd_envelope_twin_20260623"
sys.path.insert(0, str(BASE / "code")); sys.path.insert(0, str(WS / "code"))
import realfrf as rf
import netcg_qoi as NC

DRUM = (228.0, 260.0); TRAY_Z = 55.0
SD_A_M, SD_A_U, SD_F_M, SD_F_U = 0.35, 0.80, 0.01, 0.06
N_MC = 300


def band_factor(model, theta_map, resolved_sda):
    """normal_Z 95% band factor with per-mode amplitude sigma `resolved_sda` (nM,)."""
    rng = np.random.default_rng(0)
    sdf = np.where(model.is_meas, SD_F_M, SD_F_U)
    gr = np.empty(N_MC)
    for t in range(N_MC):
        amp = np.exp(rng.normal(0, 1, model.nM) * resolved_sda)
        fsc = 1 + rng.normal(0, 1, model.nM) * sdf
        s = NC.octave_smooth(NC.FGRID, model.spectrum(theta_map, 2, amp=amp, fscale=fsc))
        gr[t] = NC.grms(s)
    p = np.percentile(gr, [2.5, 97.5]); return float(p[1] / max(p[0], 1e-30))


def main():
    model = NC.QOIModel()
    z = np.load(WS / "out" / "theta_post_L5.npz", allow_pickle=True)
    theta_map = np.median(z["theta_post"], 0)
    f, Q = model.modes(theta_map)

    # reduced-model full-field Z displacement on the plate
    R = model.R
    keep_arr = np.empty(len(R.keeprow), np.int64)
    for dof, row in R.keeprow.items():
        keep_arr[row] = dof
    node_of = keep_arr // 6; axis_of = keep_arr % 6
    U = np.asarray(R.vk[:, :80], np.float64) @ R.T
    zc = R.xyz[node_of, 2]
    plateZ = (zc >= TRAY_Z) & (axis_of == 2)
    fieldZ = U[plateZ] @ Q[:, model.inb]                # (n_plateZ, nM)
    coords = R.xyz[node_of[plateZ]]                     # (n_plateZ, 3)
    rad = np.sqrt(coords[:, 0] ** 2 + coords[:, 1] ** 2)

    # drumhead target modes = in-band, 228-260 Hz, UNMEASURED, with real normal participation
    g = model.g_axis(Q, 2); part = np.abs(g) / (np.abs(g).sum() + 1e-30)
    drum = np.array([(DRUM[0] <= model.fnom[j] <= DRUM[1]) and (not model.is_meas[j]) and part[j] > 0.01
                     for j in range(model.nM)])
    drum_idx = np.where(drum)[0]
    drum_hz = [round(float(model.fnom[j]), 1) for j in drum_idx]

    # current instrumented sensors on the plate (Z axis)
    meas = rf.reprocess_measured(list(range(1, rf.N_ACCEL_RECORDERS + 1)))
    ch = rf.build_channels(model.R, meas["daq"])
    cc = ch.coords; cz = np.array(ch.axes)
    on_plate_Z = [(cc[i, 2] >= TRAY_Z and ch.axes[i] == "Z") for i in range(len(ch.axes))]
    n_plate_Z_now = int(np.sum(on_plate_Z))

    # drumhead node-ring evidence: |Z| of each drumhead mode at the plate ANTINODE (max) vs plate EDGE (r>7in)
    edge = rad > 0.8 * rad.max()
    ring_evidence = []
    for j in drum_idx:
        amp = np.abs(fieldZ[:, j]); anti = amp.max() + 1e-30
        ring_evidence.append({"hz": round(float(model.fnom[j]), 1),
                              "edge_over_antinode_amp": round(float(np.median(amp[edge]) / anti), 3),
                              "antinode_radius_in": round(float(rad[np.argmax(amp)]), 1)})

    # candidate plate sensor grid (subsample plate nodes: rings x spokes)
    cand = []
    for rr in np.linspace(0, rad.max(), 6):
        ring = np.where(np.abs(rad - rr) < 1.0)[0]
        if len(ring):
            for th in np.linspace(0, 2 * np.pi, 8, endpoint=False):
                x, y = rr * np.cos(th), rr * np.sin(th)
                k = ring[np.argmin((coords[ring, 0] - x) ** 2 + (coords[ring, 1] - y) ** 2)]
                cand.append(int(k))
    cand = sorted(set(cand))
    Phi = fieldZ[cand][:, drum_idx]                     # (n_cand, n_drum) un-normalized real shapes
    full_energy = (Phi ** 2).sum(0) + 1e-30             # per-mode energy over the FULL candidate array (reference)

    # greedy captured-energy (EfI-style) placement: add the candidate that most raises the WORST mode's captured
    # fraction (protect every target mode). resolved_i = captured shape energy / full-array energy (relative to
    # what a dense ~candidate-size plate array achieves). Also report subspace separability (min-eig) honestly.
    sel = []; avail = list(range(len(cand)))
    curve = []
    base_sda = np.where(model.is_meas, SD_A_M, SD_A_U)
    curve.append({"n_sensors": 0, "min_resolved_frac": 0.0, "n_resolved_modes": 0, "subspace_min_eig": 0.0,
                  "normal_band_factor": round(band_factor(model, theta_map, base_sda.copy()), 2)})
    for step in range(min(12, len(cand))):
        best, bj = -1e18, None
        for j in avail:
            rf_ = (Phi[sel + [j]] ** 2).sum(0) / full_energy      # (n_drum,)
            score = rf_.min()                                     # protect the worst-observed mode
            if score > best:
                best, bj = score, j
        sel.append(bj); avail.remove(bj)
        resolved_frac = np.clip((Phi[sel] ** 2).sum(0) / full_energy, 0, 1)
        Pn = Phi[sel] / (np.linalg.norm(Phi[sel], axis=0, keepdims=True) + 1e-30)
        min_eig = float(np.linalg.eigvalsh(Pn.T @ Pn).min())     # separability of the modes (secondary diagnostic)
        sda = base_sda.copy()
        sda[drum_idx] = SD_A_U + (SD_A_M - SD_A_U) * resolved_frac
        curve.append({"n_sensors": len(sel), "min_resolved_frac": round(float(resolved_frac.min()), 3),
                      "n_resolved_modes": int((resolved_frac >= 0.5).sum()),
                      "subspace_min_eig": round(min_eig, 3),
                      "normal_band_factor": round(band_factor(model, theta_map, sda), 2)})

    # fully-resolved FLOOR: all drumhead net-drivers measured (sda -> SD_A_M) = the max achievable buy-down
    sda_floor = np.where(model.is_meas, SD_A_M, SD_A_U); sda_floor[drum_idx] = SD_A_M
    floor = round(band_factor(model, theta_map, sda_floor), 2)
    cur = curve[0]["normal_band_factor"]; got = curve[-1]["normal_band_factor"]
    pct_of_floor = round(100 * (cur - got) / (cur - floor + 1e-9), 0)

    # recommended drive from Stage-0 observability (which drives excite the drumhead band)
    obs = json.load(open(WS / "out" / "stage0_observability.json"))
    drive_hits = {}
    for row in obs["drumhead_band_observability_with_Y"]:
        for d in row["by"]:
            drive_hits[d] = drive_hits.get(d, 0) + 1
    rec_drives = sorted(drive_hits.items(), key=lambda x: -x[1])

    out = {"target_drumhead_modes_hz": drum_hz, "n_target_modes": len(drum_idx),
           "note_on_targets": "NET-CG normal is driven by the PARTIAL-cancellation drumhead modes (246/249/254/258 Hz "
                              "with net tray-Z participation), NOT the pure 234/252 Hz modes (net~0 -> cancel). This "
                              "is why net-normal (45% trust) beats the point mount_response (13%).",
           "current_plate_Z_sensors": n_plate_Z_now,
           "node_ring_evidence": ring_evidence,
           "candidate_grid_size": len(cand),
           "buy_down_curve": curve,
           "fully_resolved_floor_band_factor": floor,
           "buy_down_pct_of_floor_at_12_sensors": pct_of_floor,
           "modes_individually_separable": bool(curve[-1]["subspace_min_eig"] > 0.05),
           "recommended_drive_by_drumhead_coverage": rec_drives,
           "recommendation": (f"Current plate is essentially UNINSTRUMENTED for Z ({n_plate_Z_now} sensor). Add "
                              f"plate accelerometers on a center+ring grid: {curve[-1]['n_sensors']} well-placed Z "
                              f"accels cut the normal-QOI band factor from {cur}x to {got}x "
                              f"(~{100*(cur-got)/cur:.0f}% reduction, {pct_of_floor:.0f}% of the way to the "
                              f"fully-resolved floor {floor}x). The 246-258 Hz net-drivers have FINE spatial "
                              f"structure (worst-mode captured only {curve[-1]['min_resolved_frac']:.2f} at 12 "
                              f"sensors) -> a denser array (or accepting the partial buy-down) is needed for full "
                              f"resolution. They are not individually SEPARABLE by point sensors (measure their net "
                              f"combination = the QOI, which is enough). DRIVE: +Y covers the most drumhead peaks "
                              f"(incl the unique 230.6 Hz); +Z(990)/+XY tie next. THIS is the next test dollar."),
           "note": "NO NUTS; reduced-model shapes; uniform-mass proxy; captured-energy (EfI-style) placement "
                   "referenced to a full ~candidate-size plate array; band factor via MC over mode uncertainty."}
    # compact figure data: plate scatter (|Z| of the top net-driver) + selected/current sensor xy
    top_mode = drum_idx[int(np.argmax(part[drum_idx]))]
    ss = np.linspace(0, len(coords) - 1, min(600, len(coords))).astype(int)
    fig_npz = WS / "out" / "pretest_figdata.npz"
    np.savez(fig_npz, plate_xy=coords[ss, :2], plate_absZ=np.abs(fieldZ[ss, top_mode]),
             top_mode_hz=float(model.fnom[top_mode]),
             sel_xy=coords[[cand[s] for s in sel], :2],
             cur_xy=np.array([[cc[i, 0], cc[i, 1]] for i in range(len(ch.axes)) if on_plate_Z[i]]).reshape(-1, 2),
             ns=np.array([c["n_sensors"] for c in curve]),
             band=np.array([c["normal_band_factor"] for c in curve]),
             floor=floor, cur_band=cur, rec_drives=np.array([f"{k}:{v}" for k, v in rec_drives]))
    (WS / "out" / "pretest_design.json").write_text(json.dumps(out, indent=2))
    print(f"target drumhead modes ({len(drum_idx)}): {drum_hz}")
    print(f"current plate-Z sensors: {n_plate_Z_now}  (node-ring: edge/antinode amp "
          f"{[r['edge_over_antinode_amp'] for r in ring_evidence]})")
    print("buy-down (n_sensors -> normal band factor, n_resolved of 4, worst-mode captured, separability):")
    for c in curve:
        print(f"   {c['n_sensors']:2d} sensors -> {c['normal_band_factor']:.2f}x  "
              f"({c['n_resolved_modes']} resolved, worst-captured {c['min_resolved_frac']:.2f}, "
              f"sep-min-eig {c['subspace_min_eig']:.3f})")
    print("recommended drive (drumhead coverage):", rec_drives)


if __name__ == "__main__":
    main()
