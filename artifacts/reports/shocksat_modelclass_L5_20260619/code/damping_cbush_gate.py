#!/usr/bin/env python3
"""Damping IDENTIFIABILITY gate for Andrew's idea: a COMPLEX / structural loss-factor on the INTERFACE CBUSHes
(bush_801..807 = bolted joints, bush_902 = contact). AGENTS Modal/Eigenproblem Identifiability gate, run BEFORE
any damping study.

Physics: a structural (hysteretic) loss factor eta_g on a CBUSH = imaginary stiffness i*eta_g*K_g. Its
contribution to MODAL damping of mode k is  zeta_k += 0.5 * eta_g * f_{k,g},  f_{k,g} = phi_k^T (theta_g B_g) phi_k
/ lambda_k = the strain-energy FRACTION mode k stores in CBUSH g (mass-normalized M=I). So eta_g is identifiable
from mode k ONLY if (a) f_{k,g} is appreciable AND (b) mode k's half-power bandwidth Delta f = 2 zeta_k f_k is
resolvable in the measured FRF (Discretization gate). The participation/damping confound is on peak HEIGHT, NOT
on bandwidth, so bandwidth is the un-confounded observable.

Output: out/identifiability_M3_cbush.json. Reuses Card E per-PID blocks + Card A L5 MAP + measured FRF (read-only).
"""
from __future__ import annotations
import json, sys
from pathlib import Path
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import realfrf as rf
import modal_feature as mf
import cardE_richmodel as rm

WS = Path(__file__).resolve().parent.parent
OUT = WS / "out"
CARD_A_OUT = WS.parent / "statfem_real_validation_20260617" / "out"
INTERFACE = ["bush_801", "bush_802", "bush_803", "bush_804", "bush_805", "bush_806", "bush_807", "bush_902"]
# nominal structural loss factors to probe identifiability against (typical bolted-joint range)
ETA_PROBE = [0.02, 0.05, 0.10]


def main():
    A = json.loads((CARD_A_OUT / "modal_feature.json").read_text())
    theta_map = {g: v["med"] for g, v in A["theta_post"].items()}
    sig_w2 = float(A["sigma_w2_rel"]["med"])
    pp = rm.build_perpid()
    R, idx, wmeas, _ = rm.matched_modes()
    theta9 = rf.core.theta_vector(theta_map)
    K = R.A_fix + np.einsum("g,gij->ij", theta9, R.A)
    lam, V = np.linalg.eigh(K)
    Vm = V[:, idx]                       # (74, n) matched eigenvectors (mass-norm)
    lam_m = lam[idx]
    n = len(idx)

    # measured FRF frequency resolution (Discretization gate) + measured modal damping range (Card D)
    meas = rf.reprocess_measured(list(range(1, rf.N_ACCEL_RECORDERS + 1)))
    fr = meas["freqs"]; bm = (fr >= rf.BAND[0]) & (fr <= rf.BAND[1])
    df_hz = float(np.median(np.diff(fr[bm])))
    zeta_pct = json.loads((OUT / "cardD_inputs" / "damping_gate.json").read_text())["zeta_meas_pct"]
    zeta_typ = float(np.median(zeta_pct)) / 100.0
    zeta_max = float(np.max(zeta_pct)) / 100.0

    # SE fraction f_{k,g} for each interface CBUSH (and group totals for context)
    def se_frac(block):
        # block already in reduced coords; scale by its group's MAP theta
        return np.einsum("ik,ij,jk->k", Vm, block, Vm) / lam_m   # (n,) per matched mode

    rows = {}
    # interface CBUSHes (each its own param)
    for pid in INTERFACE:
        grp = rm.PID2GROUP[pid]
        blk = theta_map[grp] * rm.block_of(pp, pid)
        f = se_frac(blk)
        kmax = int(np.argmax(f))
        f_peak = float(f[kmax]); f_typ = float(np.median(f))
        f_mode_hz = float(wmeas[kmax])
        # identifiable-zeta contribution at probe loss factors, vs the per-mode bandwidth-resolution floor:
        # bandwidth Delta f = 2 zeta f must exceed ~ a few df bins to be measurable. Express the floor as the
        # zeta at which Delta f = 2*df (2 bins): zeta_floor = df / f.
        zeta_floor_at_peak = df_hz / f_mode_hz
        dz = {f"eta_{e}": float(0.5 * e * f_peak) for e in ETA_PROBE}   # modal-zeta contribution if eta=e
        # identifiable if the BEST-case contribution (eta=0.10) exceeds both the modal-zeta scatter AND can be
        # seen via bandwidth (i.e. the mode itself is resolvable: 2*zeta_typ*f > 2*df)
        bw_resolvable = (2.0 * zeta_typ * f_mode_hz) > (2.0 * df_hz)
        contrib_max = 0.5 * max(ETA_PROBE) * f_peak
        verdict = ("IDENTIFIABLE" if (f_peak > 0.05 and bw_resolvable and contrib_max > zeta_typ * 0.5)
                   else ("SE-DILUTED-WEAK" if f_peak > 0.01 else "BELOW-FLOOR"))
        rows[pid] = {"group": grp, "se_frac_peak": f_peak, "se_frac_typical": f_typ,
                     "peak_mode_hz": f_mode_hz, "peak_mode_idx_matched": kmax,
                     "modal_zeta_contrib_at_probe": dz, "zeta_floor_bw_at_peak": float(zeta_floor_at_peak),
                     "bandwidth_resolvable": bool(bw_resolvable), "verdict": verdict}

    # group-level context (joints total, contact, top_box, plates) — the Card D comparison
    grp_rows = {}
    for g in ["joints", "contact", "top_box", "plates", "cross_beam", "bottom_box"]:
        blk = theta_map[g] * rm.group_block(pp, g)
        f = se_frac(blk); kmax = int(np.argmax(f))
        grp_rows[g] = {"se_frac_peak": float(f[kmax]), "se_frac_typical": float(np.median(f)),
                       "peak_mode_hz": float(wmeas[kmax])}

    n_ident = sum(1 for v in rows.values() if v["verdict"] == "IDENTIFIABLE")
    out = {
        "gate": "complex/structural-damping identifiability on INTERFACE CBUSHes (Andrew's idea)",
        "observable_note": ("damping is FREQUENCY-blind (Stage-1) and peak-HEIGHT is participation-confounded; "
                            "the un-confounded observable is peak half-power BANDWIDTH Delta f = 2 zeta f."),
        "n_matched_modes": n, "frf_df_hz": df_hz, "zeta_typical": zeta_typ, "zeta_max": zeta_max,
        "interface_cbush": rows, "group_context": grp_rows,
        "n_interface_cbush_identifiable": n_ident,
        "verdict": ("AT LEAST ONE interface CBUSH is identifiable from a single impact" if n_ident
                    else ("NO interface CBUSH clears the identifiability gate from this single-impact modal data: "
                          "their loss factors are SE-diluted (joints store ~3%% SE; Card D). A complex CBUSH "
                          "damping parameter is PHYSICALLY sound but the data cannot pin it per-CBUSH; the "
                          "identifiable quantity is per-MODE modal damping (from bandwidth), which can still "
                          "tighten the QOI but cannot be uniquely attributed to a specific interface bush.")),
    }
    (OUT / "identifiability_M3_cbush.json").write_text(json.dumps(out, indent=2))

    print(f"FRF df={df_hz:.2f} Hz | zeta typ={zeta_typ*100:.2f}% max={zeta_max*100:.2f}% | bandwidth 2*zeta*f "
          f"at 100Hz typ={2*zeta_typ*100:.2f}Hz (need >~{2*df_hz:.2f}Hz)")
    print("interface CBUSH SE-fraction (peak over modes) + verdict:")
    for pid, v in rows.items():
        print(f"  {pid:9s} ({v['group']:8s}) SE_peak={v['se_frac_peak']:.4f} @ {v['peak_mode_hz']:.0f}Hz "
              f"bw_ok={v['bandwidth_resolvable']} -> {v['verdict']}")
    print("group context SE_peak:", {g: round(r["se_frac_peak"], 3) for g, r in grp_rows.items()})
    print(f"\nVERDICT: {out['verdict'][:120]}...")


if __name__ == "__main__":
    main()
