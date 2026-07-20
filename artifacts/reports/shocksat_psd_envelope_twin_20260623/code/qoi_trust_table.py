#!/usr/bin/env python3
"""'WHAT CAN THIS TWIN CARRY' TABLE (Andrew "continue"): one consistent per-QOI modal-trust report across several loads.

For each load QOI we build its modal coefficient matrix G (n_components, n_modes) so QOI(w)=sqrt(sum_comp |sum_i
G[comp,i]/D_i(w)|^2), then report, on the SAME basis (flat modal drive, common MC mode-uncertainties):
  - TRUST = QOI band-RMS using MEASURED modes only / using all modes  (share carried by data-anchored modes)
  - BAND  = 95% Monte-Carlo band (+/-% of median) from mode uncertainty (measured tight, unmeasured wide)
  - share of band variance from UNMEASURED modes
  - the top driving modes (freq, measured?)

QOIs: net base shear X/Y/Z (sum_{axis} omega^2 phi, uniform mass); top-plate-center mount response (omega^2 phi_mount^2);
strut-connection force (real CBUSH k*(phi_a-phi_b), pbush 803-807). All NO NUTS; labeled proxies where noted.
Output: figures/qoi_trust_table.png + out/qoi_trust_table.json.
"""
from __future__ import annotations
import json, sys
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

sys.path.insert(0, str(Path(__file__).resolve().parent))
import realfrf as rf
import shape_borrow_diag as SB

WS = Path(__file__).resolve().parent.parent
FEMNPZ = WS.parent / "shocksat_fem_modal_twin_20260609" / "fem_model.npz"
BAND = (45.0, 260.0); ZETA = 0.01
MOUNT = (0.0, 0.0, 57.74989); STRUT_PIDS = {803, 804, 805, 806, 807}
N_MC = 600
SD_F_M, SD_A_M = 0.01, 0.35
SD_F_U, SD_A_U = 0.06, 0.80


def main():
    R = rf.load_reduced()
    K1 = R.A_fix + R.A.sum(0); w2, Q = np.linalg.eigh(K1)
    fmodes = np.sqrt(np.clip(w2, 0, None)) / (2 * np.pi)
    inb = np.where((fmodes >= BAND[0]) & (fmodes <= BAND[1]))[0]
    fb = fmodes[inb]; wi2 = (2 * np.pi * fb) ** 2; nM = len(inb)
    keep_arr = np.empty(len(R.keeprow), np.int64)
    for dof, row in R.keeprow.items():
        keep_arr[row] = dof
    axis = keep_arr % 6
    U = np.asarray(R.vk[:, :80], np.float64) @ R.T
    field = U @ Q[:, inb]                                   # (Ndof, nM)
    keeprow = R.keeprow

    D = SB.build_dofs(R); _, pairs = SB.match_modes(D, Q)
    matched = {int(p[1]): float(D["mfr"][p[0]]) for p in pairs}
    is_meas = np.array([int(k) in matched for k in inb])
    meas_f = np.array([matched.get(int(k), fb[j]) for j, k in enumerate(inb)])

    fm = np.load(FEMNPZ, allow_pickle=True)
    gid2i = {int(g): i for i, g in enumerate(fm["gids"])}
    cb = np.asarray(fm["cbush"]); pb = json.loads(str(fm["pbush"]))

    def phi(gid, a):
        d = 6 * gid2i[int(gid)] + a
        return field[keeprow[d]] if d in keeprow else None

    # --- QOI coefficient matrices G (n_comp, nM)
    G = {}
    for a, lab in [(0, "base_shear_X"), (1, "base_shear_Y"), (2, "base_shear_Z")]:
        G[lab] = (wi2 * field[axis == a].sum(0))[None, :]
    mrow, _, _ = R.reduced_row(MOUNT, "Z"); phim = (mrow @ Q)[inb]
    G["mount_response"] = (-wi2 * phim ** 2)[None, :]
    Gs = []
    for row in cb:
        pid = int(row[1])
        if pid not in STRUT_PIDS or str(pid) not in pb:
            continue
        k = pb[str(pid)]["k"]; ok = True; rows = []
        for a in range(3):
            pa, pbb = phi(row[2], a), phi(row[3], a)
            if pa is None or pbb is None:
                ok = False; break
            rows.append(k[a] * (pa - pbb))
        if ok:
            Gs.extend(rows)
    G["strut_force"] = np.array(Gs)

    fg = np.linspace(40, 300, 600); w = 2 * np.pi * fg
    bmask = (fg >= BAND[0]) & (fg <= BAND[1])

    def rms(Gc, fmod, amp):
        wi = 2 * np.pi * fmod
        qt = 1.0 / (wi[:, None] ** 2 - w[None, :] ** 2 + 2j * ZETA * wi[:, None] * w[None, :])
        resp = (Gc * amp[None, :]) @ qt
        F = np.sqrt((np.abs(resp) ** 2).sum(0))
        return float(np.sqrt(np.mean(F[bmask] ** 2)))

    rng = np.random.default_rng(0)
    sdf = np.where(is_meas, SD_F_M, SD_F_U); sda = np.where(is_meas, SD_A_M, SD_A_U)
    # shared MC draws
    DF = rng.normal(0, 1, (N_MC, nM)); DA = rng.normal(0, 1, (N_MC, nM))

    results = {}
    for lab, Gc in G.items():
        nom = rms(Gc, fb, np.ones(nM))
        meas_only = rms(Gc, fb, is_meas.astype(float))
        def mc(mask):
            o = np.empty(N_MC)
            for t in range(N_MC):
                fp = fb * (1 + np.where(mask, DF[t] * sdf, 0.0))
                ap = np.exp(np.where(mask, DA[t] * sda, 0.0))
                o[t] = rms(Gc, fp, ap)
            return o
        a_all, a_unm, a_meas = mc(np.ones(nM, bool)), mc(~is_meas), mc(is_meas)
        p = np.percentile(a_all, [2.5, 50, 97.5])
        vU, vM = np.var(np.log(a_unm)), np.var(np.log(a_meas))
        # top driving modes by |contribution| (RMS over components of |G[:,i]|)
        contr = np.sqrt((np.abs(Gc) ** 2).sum(0)); contr_n = contr / (contr.sum() + 1e-30)
        topc = np.argsort(contr_n)[::-1][:3]
        results[lab] = {
            "trust_pct": round(100 * meas_only / (nom + 1e-30), 0),
            "band_pm_pct": round(float((p[2] - p[0]) / 2 / p[1] * 100), 0),
            "band_factor": round(float(p[2] / max(p[0], 1e-9)), 1),
            "var_share_unmeasured_pct": round(100 * float(vU / (vU + vM + 1e-30)), 0),
            "top_modes": [{"hz": round(float(fb[c]), 0), "pct": round(float(contr_n[c] * 100), 0),
                           "measured": bool(is_meas[c])} for c in topc]}

    rec = {"deliverable": "per-QOI modal-trust table: what loads can this twin carry, and what to measure",
           "basis": "flat modal drive; trust = measured-mode-only RMS / all-mode RMS; band = MC over mode uncertainty "
                    "(meas freq 1%/amp 0.35, UNMEAS freq 6%/amp 0.80)",
           "qois": results,
           "caveats": "base shear uniform mass; mount response = drive-point accelerance residue; strut force = real "
                      "CBUSH (basic frame); flat modal drive; band scales with assumed unmeasured-mode uncertainty.",
           "note": "EXPLORATORY; YELLOW; NO NUTS."}
    (WS / "out" / "qoi_trust_table.json").write_text(json.dumps(rec, indent=2))

    # figure: trust + band per QOI
    order = ["base_shear_X", "base_shear_Y", "base_shear_Z", "mount_response", "strut_force"]
    order = [q for q in order if q in results]
    fig, (axT, axB) = plt.subplots(1, 2, figsize=(13.5, 4.6))
    y = np.arange(len(order))[::-1]
    tr = [results[q]["trust_pct"] for q in order]
    axT.barh(y, tr, color="#2ca02c")
    axT.barh(y, [100 - t for t in tr], left=tr, color="#d62728", alpha=0.55)
    for yi, q in zip(y, order):
        tm = " ".join(f"{m['hz']:.0f}{'*' if m['measured'] else '!'}" for m in results[q]["top_modes"])
        axT.text(2, yi, f"{q}   top: {tm}", va="center", fontsize=8)
    axT.set_yticks([]); axT.set_xlim(0, 100); axT.set_xlabel("trust = % of load carried by MEASURED modes", fontsize=9)
    axT.set_title("green=measured/trusted, red=unmeasured.  top modes: * measured, ! not", fontsize=9)
    axT.spines[["top", "right", "left"]].set_visible(False)

    bp = [results[q]["band_pm_pct"] for q in order]; vu = [results[q]["var_share_unmeasured_pct"] for q in order]
    axB.barh(y, bp, color="#1f77b4")
    for yi, q, b, v in zip(y, order, bp, vu):
        axB.text(b + 3, yi, f"+/-{b:.0f}%  ({v:.0f}% from unmeasured)", va="center", fontsize=8)
    axB.set_yticks(y); axB.set_yticklabels(order, fontsize=8)
    axB.set_xlabel("95% band (+/- % of median)", fontsize=9)
    axB.set_title("uncertainty band and how much comes from UNMEASURED modes", fontsize=9)
    axB.spines[["top", "right"]].set_visible(False)
    cap = ("Per-QOI modal-trust: which loads the twin can carry. TRUST = share of the load on data-anchored modes; "
           "BAND = MC over mode uncertainty (unmeasured modes wide). Net loads do NOT escape via cancellation (prior "
           "pilot) -> trust is set by whether the FEW load-bearing modes are measured. High trust + small band = usable "
           "now; low trust + big-band-from-unmeasured = needs test data on those modes (mostly >200 Hz). NO NUTS.")
    fig.text(0.01, -0.04, cap, fontsize=7.2, wrap=True, va="top")
    fig.tight_layout(rect=[0, 0.06, 1, 1])
    outp = WS / "figures" / "qoi_trust_table.png"
    fig.savefig(outp, dpi=150, bbox_inches="tight"); plt.close(fig)

    print(f"{'QOI':<16}{'trust%':>7}{'band+-%':>9}{'factor':>8}{'unmeas%':>9}  top modes (Hz, *=measured)")
    for q in order:
        r = results[q]
        tm = " ".join(f"{m['hz']:.0f}{'*' if m['measured'] else '!'}({m['pct']:.0f}%)" for m in r["top_modes"])
        print(f"{q:<16}{r['trust_pct']:>7.0f}{r['band_pm_pct']:>9.0f}{r['band_factor']:>8.1f}"
              f"{r['var_share_unmeasured_pct']:>9.0f}  {tm}")
    print(f"wrote {outp}")
    return rec


if __name__ == "__main__":
    main()
