#!/usr/bin/env python3
"""Parse ATA/OPoly .ash binary mode-shape file (reverse-engineered layout).

Layout (established empirically in this workspace; see measured_modes_provenance.md):
- Global channel table at byte offset 2560 (word 640): 76 triplets of
  int32 (node_id, node_id, channel_seq).
- Mode records: located by scanning for the int32 signature
  [mode_index, 76, 250, 1, 3] immediately before the float32 frequency word
  (mode_index = 1..n_modes).
  rec[freq_word + 0] = frequency (Hz, f32)
  rec[freq_word + 1] = damping (fraction of critical, f32)
  rec[freq_word + 251 .. +478] = 228 float32 = 76 channels x (X, Y, Z) shape
  components; negative zero (0x80000000) = component not measured.

Validation hooks: frequencies must match NASA pptx test-shape list; the
measured-component pattern must match the ASET slides (e.g. 1101 -> Z only).
"""
import json
import sys
import numpy as np

ASH = "inputs/Final_FF_Test_Shapes_100121.ash"
NEG_ZERO = np.int32(-2147483648)  # 0x80000000 = -0.0f sentinel

def parse(path=ASH):
    d = open(path, "rb").read()
    n4 = len(d) // 4
    i32 = np.frombuffer(d, dtype="<i4", count=n4)
    a32 = np.frombuffer(d, dtype="<f4", count=n4)

    # channel table
    tab = i32[640:640 + 76 * 3].reshape(76, 3)
    assert (tab[:, 0] == tab[:, 1]).all(), "channel table layout changed"
    assert (tab[:, 2] == np.arange(1, 77)).all(), "channel seq not 1..76"
    nodes = tab[:, 0].astype(int)

    # record scan: signature [mode_index, 76, 250, 1, 3] then f32 freq
    starts = []
    for k in range(640, n4 - 480):
        if (i32[k] >= 1 and i32[k + 1] == 76 and i32[k + 2] == 250
                and i32[k + 3] == 1 and i32[k + 4] == 3):
            starts.append(k + 5)
    modes = []
    for s in starts:
        f = float(a32[s])
        z = float(a32[s + 1])
        blk_i = i32[s + 251: s + 251 + 228]
        blk_f = a32[s + 251: s + 251 + 228].astype(np.float64).reshape(76, 3)
        measured = (blk_i != NEG_ZERO).reshape(76, 3)
        if not (0.5 < f < 5000.0):
            continue
        modes.append({"freq_hz": f, "damp_frac": z,
                      "shape": blk_f, "measured": measured})
    return nodes, modes

if __name__ == "__main__":
    nodes, modes = parse()
    freqs = [m["freq_hz"] for m in modes]
    print(f"{len(modes)} modes, {len(nodes)} channels")
    print("freqs:", [round(f, 2) for f in freqs])
    # consistency: measured-component mask identical across modes
    m0 = modes[0]["measured"]
    same = all((m["measured"] == m0).all() for m in modes)
    print("measured mask identical across modes:", same)
    ncomp = int(m0.sum())
    print("measured components per mode:", ncomp)
    # ASET spot checks (slides 65-76): 1101 Z only; 1102 YZ; 1103 XZ; 2101 XYZ
    spot = {1101: (False, False, True), 1102: (False, True, True),
            1103: (True, False, True), 2101: (True, True, True)}
    for nid, exp in spot.items():
        row = m0[list(nodes).index(nid)]
        ok = tuple(row) == exp
        print(f"ASET check node {nid}: {tuple(bool(x) for x in row)} expected {exp} -> {'OK' if ok else 'MISMATCH'}")
    shapes = np.stack([m["shape"] for m in modes])   # (nm, 76, 3)
    measured = m0
    np.savez("measured_modes.npz", nodes=nodes, freqs=np.array(freqs),
             damp=np.array([m["damp_frac"] for m in modes]),
             shapes=shapes, measured=measured)
    json.dump({"n_modes": len(modes), "n_channels": int(len(nodes)),
               "n_measured_components": ncomp,
               "freqs_hz": [round(f, 4) for f in freqs],
               "damp_frac": [round(m["damp_frac"], 6) for m in modes],
               "source": ASH},
              open("measured_modes_summary.json", "w"), indent=1)
    print("wrote measured_modes.npz, measured_modes_summary.json")
