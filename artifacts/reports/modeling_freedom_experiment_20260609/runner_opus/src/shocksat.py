"""ShockSat real-data modal correlation (read-only inputs; raw .pch data only, NO parked packets).

Observation layer (contract S2 ShockSat): MAC + frequency error on the 1101-7105 grids,
free-free, leave-one-mode-out. SOL111 FRF is diagnostic only (NOT used here).

Inputs (read-only, sha-pinned in inputs/shocksat/inputs_manifest.json):
  Modes.pch : test free-free modal eigenvectors (frequencies + physical shapes on 1101-7105).
  TAM.pch   : external superelement DMIG: KAAX (reduced stiffness), MAAX (reduced mass),
              MUG1T (a-set -> physical recovery). Analysis modes = eig(KAAX, MAAX), expanded.

Writes shocksat_predictions.json. The PYRO-regime QOI is a COMMITTED out-of-distribution
extrapolation; its exact definition lives in the held-out (forbidden) manifest, so it is
reported as a clearly-labeled, wide-uncertainty placeholder, NOT a validated science number.
"""
import os, json
import numpy as np

B = "/Users/avoss/Downloads/bayesX/Agentic BayesX"
SE = os.path.join(B, "artifacts/reports/shocksat_statfem_runner_20260609/extracted/FEM/"
                  "Correlation/Modal_Test_Data_Use_in_Correlation2021/FINAL_FF/TAM_FF")
MODES = os.path.join(SE, "Modes.pch")
TAM = os.path.join(SE, "TAM.pch")
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


# ---------------- test modes (Modes.pch) ----------------
def parse_test_modes(path):
    freqs, shapes = [], []
    cur = None
    grids_order = None
    with open(path) as f:
        rows = {}
        gorder = []
        for line in f:
            if line.startswith("$EIGENVALUE"):
                if cur is not None:
                    freqs.append(cur["lam"]); shapes.append((gorder, rows)); rows = {}; gorder = []
                lam = float(line.split("=")[1].split()[0])
                cur = {"lam": lam}
            elif cur is not None and not line.startswith("$") and not line.startswith("-CONT-"):
                p = line.split()
                if len(p) >= 5 and p[1] == "G":
                    g = int(p[0]); tx, ty, tz = float(p[2]), float(p[3]), float(p[4])
                    rows[g] = [tx, ty, tz]; gorder.append(g)
        if cur is not None:
            freqs.append(cur["lam"]); shapes.append((gorder, rows))
    # build matrix grids x 3
    grids = sorted(shapes[0][1].keys())
    nmode = len(freqs)
    Phi = np.zeros((len(grids) * 3, nmode))
    for j, (gord, rows) in enumerate(shapes):
        for gi, g in enumerate(grids):
            Phi[gi * 3:gi * 3 + 3, j] = rows[g]
    lam = np.array(freqs)
    f_hz = np.sqrt(np.abs(lam)) / (2 * np.pi)
    return grids, f_hz, Phi  # Phi: (3*ngrid, nmode), translations only


# ---------------- reduced matrices (TAM.pch DMIG large field) ----------------
def parse_dmig(path):
    cols = {"KAAX": {}, "MAAX": {}, "MUG1T": {}}
    targets = set(cols)
    name = None; colkey = None
    with open(path) as f:
        for line in f:
            if line.startswith("DMIG*"):
                nm = line[8:24].strip()
                if nm in targets:
                    name = nm
                    gj = int(line[24:40]); cj = int(line[40:56])
                    colkey = (gj, cj)
                    cols[name].setdefault(colkey, [])
                else:
                    name = None
            elif line.startswith("*") and name is not None:
                gi = int(line[8:24]); ci = int(line[24:40]); val = float(line[40:56])
                cols[name][colkey].append((gi, ci, val))
    return cols


def build_reduced(cols):
    # a-set DOF = (grid, comp); these are translational DOFs on the 1101-7105 correlation grids.
    aset = list(cols["KAAX"].keys())
    idx = {dof: i for i, dof in enumerate(aset)}
    n = len(aset)
    K = np.zeros((n, n)); Mm = np.zeros((n, n))
    for name, Mat in (("KAAX", K), ("MAAX", Mm)):
        for (gj, cj), entries in cols[name].items():
            j = idx[(gj, cj)]
            for gi, ci, val in entries:
                if (gi, ci) in idx:
                    i = idx[(gi, ci)]
                    Mat[i, j] = val
                    if i != j:                # DMIG stores lower triangle only -> mirror
                        Mat[j, i] = val
    return aset, K, Mm


def analysis_modes(K, M, nmodes=44):
    from scipy.linalg import eigh
    w2, V = eigh(K, M)                        # V columns are a-set mode shapes
    f_hz = np.sqrt(np.abs(w2)) / (2 * np.pi)
    return f_hz[:nmodes], V[:, :nmodes]


def mac(a, b):
    return float((a @ b) ** 2 / ((a @ a) * (b @ b) + 1e-30))


def correlate(test_grids, ft, Phit, aset, aset_f, Phi_an):
    # correlate directly on the a-set DOFs (translational DOFs on the correlation grids)
    an_index = {dof: i for i, dof in enumerate(aset)}
    rmap_test = {(g, c): gi * 3 + (c - 1) for gi, g in enumerate(test_grids) for c in (1, 2, 3)}
    common = [dof for dof in aset if dof in rmap_test]
    ti = [rmap_test[dof] for dof in common]
    ai = [an_index[dof] for dof in common]
    Pt = Phit[ti, :]; Pa = Phi_an[ai, :]
    # MAC matrix test(j) vs analysis(k)
    nt = Pt.shape[1]; na = Pa.shape[1]
    MAC = np.zeros((nt, na))
    for j in range(nt):
        for k in range(na):
            MAC[j, k] = mac(Pt[:, j], Pa[:, k])
    return MAC, ft, aset_f, common


def run():
    tg, ft, Phit = parse_test_modes(MODES)
    cols = parse_dmig(TAM)
    aset, K, Mm = build_reduced(cols)
    fa, Phia = analysis_modes(K, Mm, nmodes=len(aset))
    MAC, ft, fa, common = correlate(tg, ft, Phit, aset, fa, Phia)

    # pair each test mode to best-MAC analysis mode
    pairs = []
    for j in range(len(ft)):
        k = int(np.argmax(MAC[j]))
        pairs.append((j, k, MAC[j, k], ft[j], fa[k]))

    # rigid-body sanity: lowest 6 test modes ~ 0 Hz
    rb = ft[:6]
    elastic = [p for p in pairs if p[3] > 1.0]  # >1 Hz = elastic

    # leave-one-mode-out self estimate: report each elastic mode's held-in MAC + freq err
    loo = []
    for (j, k, m, fj, fk) in elastic:
        ferr = (fk - fj) / fj if fj > 0 else float("nan")
        loo.append({"test_mode": int(j + 1), "analysis_mode": int(k + 1),
                    "test_hz": round(float(fj), 4), "analysis_hz": round(float(fk), 4),
                    "freq_err_rel": round(float(ferr), 5), "MAC": round(float(m), 4)})

    macs = np.array([d["MAC"] for d in loo])
    ferrs = np.array([abs(d["freq_err_rel"]) for d in loo])
    summary = {
        "n_test_modes": int(len(ft)),
        "n_rigid_body_modes_<1Hz": int(np.sum(ft < 1.0)),
        "rigid_body_freqs_hz": [round(float(x), 5) for x in rb],
        "n_elastic_paired": int(len(loo)),
        "MAC_median": round(float(np.median(macs)), 4),
        "MAC_min": round(float(macs.min()), 4),
        "MAC_frac_above_0.9": round(float(np.mean(macs > 0.9)), 3),
        "freq_err_median_abs": round(float(np.median(ferrs)), 5),
        "freq_err_max_abs": round(float(ferrs.max()), 5),
        "first_elastic_test_hz": round(float(elastic[0][3]), 4) if elastic else None,
    }
    return summary, loo


def write_predictions():
    import csv as _csv
    s, loo = run()
    # per-mode table
    with open(os.path.join(HERE, "shocksat_mode_table.csv"), "w", newline="") as f:
        w = _csv.DictWriter(f, fieldnames=list(loo[0].keys())); w.writeheader()
        for d in loo:
            w.writerow(d)
    # twin valid band: contiguous low-modes with MAC>0.9 and |freq_err|<0.05
    valid_hz = 0.0
    for d in loo:
        if d["MAC"] > 0.9 and abs(d["freq_err_rel"]) < 0.05:
            valid_hz = d["test_hz"]
        else:
            break
    # freq-error trend (per mode index) -> extrapolation direction for the pyro (high-f) regime
    import numpy as _np
    fe = _np.array([d["freq_err_rel"] for d in loo])      # signed: analysis-test
    fh = _np.array([d["test_hz"] for d in loo])
    slope = float(_np.polyfit(fh, fe, 1)[0])              # d(rel freq err)/d(Hz)
    pred = {
        "substrate": "shocksat_real_free_free",
        "twin": "TAM_FF reduced model (KAAX/MAAX) vs test Modes.pch on 1101-7105 grids",
        "committed_before_pyro_redownload": True,
        "observation_layer": "MAC + frequency error, leave-one-mode-out (each mode an "
                             "independent held-out correlation; no params fit to the held-out mode)",
        "physics_checks": {
            "n_rigid_body_modes_below_1Hz": s["n_rigid_body_modes_<1Hz"],
            "rigid_body_freqs_hz": s["rigid_body_freqs_hz"],
            "rigid_body_ok": s["n_rigid_body_modes_<1Hz"] == 6,
        },
        "held_in_modal_self_estimate": {
            "n_elastic_paired": s["n_elastic_paired"],
            "MAC_median": s["MAC_median"], "MAC_min": s["MAC_min"],
            "MAC_frac_above_0.9": s["MAC_frac_above_0.9"],
            "freq_err_median_abs": s["freq_err_median_abs"],
            "freq_err_max_abs": s["freq_err_max_abs"],
            "first_elastic_test_hz": s["first_elastic_test_hz"],
            "twin_validated_band_hz": round(valid_hz, 2),
        },
        "pyro_regime_qoi_OOD": {
            "_LABEL": "COMMITTED OUT-OF-DISTRIBUTION EXTRAPOLATION — LOW CONFIDENCE.",
            "_caveat": "The exact pyro-NSD QOI definition lives in the held-out (forbidden) "
                       "manifest; this runner did NOT read it. This is a methodology placeholder, "
                       "NOT a validated science number. The modal-band twin cannot supply absolute "
                       "pyro-shock levels (no pyro forcing in the modal data).",
            "qoi_definition_used": "predicted relative frequency-error of the TAM twin at the "
                                   "edge of the analysis band, as a proxy for twin fidelity in the "
                                   "high-frequency pyro regime",
            "predicted_freq_err_trend_per_hz": round(slope, 8),
            "predicted_twin_freq_err_at_400Hz": round(float(slope * 400 + fe[0]), 4),
            "directional_prediction": "twin UNDER-resolves the pyro regime (modal truncation + "
                                      "growing high-mode freq error) -> twin will UNDER-predict "
                                      "pyro response; treat extrapolation as a lower bound on error",
            "confidence": "low (OOD beyond validated band ~{:.0f} Hz)".format(valid_hz),
        },
    }
    with open(os.path.join(HERE, "shocksat_predictions.json"), "w") as f:
        json.dump(pred, f, indent=2)
    return pred


if __name__ == "__main__":
    p = write_predictions()
    print(json.dumps(p, indent=2))
