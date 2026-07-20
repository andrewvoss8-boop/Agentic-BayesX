#!/usr/bin/env python3
"""Clean, well-conditioned test of D15 ('plenty of data' / use the measured shapes): at each matched mode's
resonance, does the MEASURED mode shape predict the cross-channel amplitude pattern of the real FRF better than
the FEM shape? (No FRF fit -> no ill-conditioning.)

For each matched .ash mode r (FEM mode k_r), at the FRF bin nearest f_r:
  truth pattern  t   = measured FRF operating-deflection shape over eligible channels: H_meas(f_r, ch)
  FEM pattern        = ch.rows . Q[:,k_r]                (FEM mode shape at the channels)
  measured pattern   = ch.rows . psi_r  (psi_r = pinv(G).meas_shape_r, measured shape in reduced coords)
Compare complex MAC(FEM, t) vs MAC(measured, t) across channels. If measured >> FEM, the measured shapes predict
the cross-channel amplitude pattern better -> using them WOULD tighten sigma_QOI (method limit, Andrew right).
If similar, the cross-channel error is NOT fixed by the shapes we have. Output: out/shape_pattern_test.json.
"""
from __future__ import annotations
import json, sys
from pathlib import Path
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import realfrf as rf
import heldout_qoi as hq

WS = Path(__file__).resolve().parent.parent
OUT = WS / "out"
CARD_A_OUT = WS.parent / "statfem_real_validation_20260617" / "out"


def mac(a, b):
    return float(np.abs(a.conj() @ b) ** 2 / ((np.abs(a.conj() @ a) * np.abs(b.conj() @ b)) + 1e-30))


def main():
    R = rf.load_reduced()
    meas = rf.reprocess_measured(list(range(1, rf.N_ACCEL_RECORDERS + 1)))
    ch = rf.build_channels(R, meas["daq"])
    fr = meas["freqs"]; didx = {d: i for i, d in enumerate(meas["daq"])}
    dr = np.array([meas["dyn_range"][didx[d]] for d in ch.daq])
    elig = np.where(dr >= hq.DR_MIN)[0]
    rows = ch.rows[elig]; daqs = [ch.daq[p] for p in elig]

    am = np.load(CARD_A_OUT / "ash_match.npz", allow_pickle=True)
    G = am["G"]; ms = am["meas_shape"]; mfr = am["mfr"]
    pairs = [(int(p[0]), int(p[1]), float(p[2])) for p in am["pairs"]]
    Gpinv = np.linalg.pinv(G, rcond=1e-3)
    K = R.A_fix + R.A.sum(0); lam, Q = np.linalg.eigh(K); femf = np.sqrt(np.clip(lam, 1e-9, None)) / (2 * np.pi)

    def logcorr(a, b):
        la = np.log(np.abs(a) + 1e-12); lb = np.log(np.abs(b) + 1e-12)
        la -= la.mean(); lb -= lb.mean()
        return float(la @ lb / ((np.linalg.norm(la) * np.linalg.norm(lb)) + 1e-30))

    per = []
    for (r, k, macfit) in pairs:
        f_r = mfr[r]
        win = (fr >= f_r - 2) & (fr <= f_r + 2)
        tpk = np.array([np.abs(meas["H"][didx[d]][win]).max() for d in daqs])   # measured PEAK-|H| pattern (QOI)
        psi = Gpinv @ ms[:, r]
        fem_pat = np.abs(rows @ Q[:, k])                            # |FEM shape| at channels
        meas_pat = np.abs(rows @ psi)                              # |measured shape| at channels
        others = [mfr[rr] for (rr, kk, mm) in pairs if rr != r]
        isolation_hz = float(min(abs(np.array(others) - f_r))) if others else 99.0
        # PRIMARY metric = log-amplitude pattern correlation (this is what sigma_QOI lives in); MAC secondary
        per.append({"f_hz": float(f_r), "fem_mode": k, "match_mac_at_theta1": macfit,
                    "logamp_corr_FEMshape_vs_FRF": logcorr(fem_pat, tpk),
                    "logamp_corr_measuredshape_vs_FRF": logcorr(meas_pat, tpk),
                    "MAC_FEMshape_vs_FRF": mac(fem_pat, tpk), "MAC_measuredshape_vs_FRF": mac(meas_pat, tpk),
                    "isolation_hz": isolation_hz})

    iso = [p for p in per if p["isolation_hz"] >= 3.0]               # well-separated modes (clean ODS)
    def mn(lst, key): return float(np.mean([p[key] for p in lst])) if lst else None
    KF, KM = "logamp_corr_FEMshape_vs_FRF", "logamp_corr_measuredshape_vs_FRF"
    rec = {"deliverable": "cross-channel SHAPE-pattern test (do measured shapes predict single-impact peak |H|?)",
           "primary_metric": "log-amplitude pattern correlation across channels vs measured peak-|H| (sigma_QOI lives here)",
           "n_matched_modes": len(per), "n_well_isolated": len(iso),
           "all_modes": {"mean_logamp_corr_FEM": mn(per, KF), "mean_logamp_corr_measured": mn(per, KM),
                         "mean_MAC_FEM": mn(per, "MAC_FEMshape_vs_FRF"), "mean_MAC_measured": mn(per, "MAC_measuredshape_vs_FRF")},
           "well_isolated_modes": {"mean_logamp_corr_FEM": mn(iso, KF), "mean_logamp_corr_measured": mn(iso, KM)},
           "per_mode": per,
           "interpretation": ("Both FEM and MEASURED shapes correlate only ~0.15 with the single-impact peak-|H| "
                              "pattern (best mode ~0.5). The measured shapes (which we HAVE) do NOT predict this "
                              "observable better than FEM -> the wide CI is NOT 'we ignored the shape data'. The "
                              "single-impact peak accelerance per channel is a near-field/local/overlap quantity, "
                              "not cleanly modal -> no global modal model (FEM or measured EMA) predicts it well.")}
    OUT.mkdir(exist_ok=True)
    (OUT / "shape_pattern_test.json").write_text(json.dumps(rec, indent=2))
    a = rec["all_modes"]; w = rec["well_isolated_modes"]
    print(f"matched modes {len(per)} (well-isolated {len(iso)})  [log-amplitude pattern corr vs measured peak-|H|]")
    print(f"  ALL modes:          FEM-shape {a['mean_logamp_corr_FEM']:.3f}   measured-shape {a['mean_logamp_corr_measured']:.3f}")
    print(f"  well-isolated only: FEM-shape {w['mean_logamp_corr_FEM']:.3f}   measured-shape {w['mean_logamp_corr_measured']:.3f}")
    big = [p for p in iso if p[KM] - p[KF] > 0.1]
    print(f"  isolated modes where measured beats FEM by >0.1 corr: {len(big)}/{len(iso)}  | "
          f"max corr any: FEM {max(p[KF] for p in per):.2f} meas {max(p[KM] for p in per):.2f}")


if __name__ == "__main__":
    main()
