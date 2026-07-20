#!/usr/bin/env python3
"""extended_peaks — measured peaks in the extended band (>200 Hz) from the wide caches (H4 groundwork).
Per drive: peak-pick the channel-median log|H| (prominence 0.15 dex, min spacing 2 bins) over 200-1000 Hz,
keep peaks with median coherence >= 0.6 at the peak bin. Cross-drive matching: greedy clustering with 1%
frequency tolerance; a cluster 'measured' if seen in >=3 dev drives (vault excluded from this analysis).
Writes out/extended_peaks.json. Feeds the mode-tier update (ledger A5 addendum) and the H4 normal-band
tiers. NO model quantities involved — data only."""
import json, os, sys
import numpy as np
from scipy.signal import find_peaks

WS = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
WIDE = os.path.join(WS, "data", "multiref_wide")
DEV_KEYS = ["m_xpos_990x", "m_zpos_990z", "m_ypos_990y", "m_zpos_900z"]


def drive_peaks(key):
    z = np.load(os.path.join(WIDE, key + "_wide.npz"), allow_pickle=True)
    fc = np.asarray(z["freqs"], float)
    H = np.asarray(z["H1"]); coh = np.asarray(z["coherence"], float)
    bm = (fc >= 200.0) & (fc <= 1000.0)
    med = np.median(np.log10(np.abs(H[:, bm]) + 1e-300), axis=0)
    medcoh = np.median(coh[:, bm], axis=0)
    pk, props = find_peaks(med, prominence=0.15, distance=2)
    fcb = fc[bm]
    out = []
    for i, p in enumerate(pk):
        if medcoh[p] < 0.6:
            continue
        out.append({"hz": round(float(fcb[p]), 1), "prom_dex": round(float(props["prominences"][i]), 3),
                    "med_coh": round(float(medcoh[p]), 3),
                    "amp_med_log10": round(float(med[p]), 3)})
    return out


def main():
    per_drive = {}
    for k in DEV_KEYS:
        p = os.path.join(WIDE, k + "_wide.npz")
        if os.path.exists(p):
            per_drive[k] = drive_peaks(k)
    # cross-drive clustering (1% tolerance, greedy by frequency)
    allp = sorted([(d["hz"], k) for k, ds in per_drive.items() for d in ds])
    clusters = []
    for hz, k in allp:
        if clusters and hz <= clusters[-1]["hz_list"][-1] * 1.01:
            clusters[-1]["hz_list"].append(hz); clusters[-1]["drives"].add(k)
        else:
            clusters.append({"hz_list": [hz], "drives": {k}})
    cl = [{"hz_mean": round(float(np.mean(c["hz_list"])), 1), "n_drives": len(c["drives"]),
           "drives": sorted(c["drives"]),
           "measured_3plus": len(c["drives"]) >= 3} for c in clusters]
    out = {"per_drive": per_drive, "clusters": cl,
           "n_clusters_measured_3plus": sum(1 for c in cl if c["measured_3plus"]),
           "note": "dev drives only (vault untouched); peaks 200-1000 Hz; coherence-gated"}
    json.dump(out, open(os.path.join(WS, "out", "extended_peaks.json"), "w"), indent=1)
    print(f"drives {list(per_drive)}: {len(cl)} clusters, "
          f"{out['n_clusters_measured_3plus']} measured in >=3 drives")


if __name__ == "__main__":
    main()
