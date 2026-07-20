#!/usr/bin/env python3
"""PILOT -> NUMBER (Andrew "do it"): real strut-connection force QOI with an uncertainty band attributing the
UNMEASURED strut modes.

Upgrade over the displacement proxy: the struts attach via CBUSH elements (pbush pids 803-807, 61 in the strut
region z40-55). The REAL connection force in a CBUSH = stiffness_axis * (u_a - u_b)_axis -- a genuine element force
(lbf per unit modal amplitude), computed from the full-field FEM mode shapes (vk@T@Q) at the two bush nodes.

QOI = band-RMS of the aggregate strut-connection force under a unit drive at the top-plate-center mount (the secondary
scenario): per CBUSH e, per axis, coherent modal sum F_e,axis(w) = sum_i k_axis*(phi_a-phi_b)_i*phi_mount_i / D_i(w);
aggregate F(w)=sqrt(sum_e sum_axis |.|^2); RMS over the band. (Per-unit-mount-drive -> absolute scale needs a specified
input; the BAND and the measured/unmeasured split are input-robust = the headline.)

BAND via Monte Carlo over mode uncertainties (labeled assumptions): measured modes freq sd 1%, log-amp sd 0.35;
UNMEASURED modes freq sd 6% (the observed FEM freq error), log-amp sd 0.80 (full FEM discrepancy). Decompose the band
variance into measured- vs UNMEASURED-mode contributions. 'Twin' = matched modes anchored to measured frequency.
NO NUTS. Output: figures/strut_force_number.png + out/strut_force_number.json.
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
BAND = (45.0, 260.0)
ZETA = 0.01
STRUT_PIDS = {803, 804, 805, 806, 807}
MOUNT = (0.0, 0.0, 57.74989)
N_MC = 1000
SD_F_MEAS, SD_A_MEAS = 0.01, 0.35      # measured-mode freq sd, log-amp sd
SD_F_UNM, SD_A_UNM = 0.06, 0.80        # unmeasured-mode freq sd, log-amp sd


def run():
    R = rf.load_reduced()
    K1 = R.A_fix + R.A.sum(0); w2, Q = np.linalg.eigh(K1)
    fmodes = np.sqrt(np.clip(w2, 0, None)) / (2 * np.pi)
    inb = np.where((fmodes >= BAND[0]) & (fmodes <= BAND[1]))[0]
    fb = fmodes[inb]; nM = len(inb)

    # full-field modal shapes over kept DOFs
    U = np.asarray(R.vk[:, :80], np.float64) @ R.T
    field = U @ Q[:, inb]                                   # (Ndof, nM)
    keeprow = R.keeprow

    fm = np.load(FEMNPZ, allow_pickle=True)
    gids = fm["gids"]; gid2i = {int(g): i for i, g in enumerate(gids)}
    cb = np.asarray(fm["cbush"]); pb = json.loads(str(fm["pbush"]))

    def phi(gid, axis):
        d = 6 * gid2i[int(gid)] + axis
        return field[keeprow[d]] if d in keeprow else None

    # strut CBUSH modal coefficients g[e,axis,mode] = k_axis*(phi_a-phi_b)_mode
    Gs = []
    used = 0
    for row in cb:
        eid, pid, na, nb = int(row[0]), int(row[1]), int(row[2]), int(row[3])
        if pid not in STRUT_PIDS or str(pid) not in pb:
            continue
        k = pb[str(pid)]["k"]
        g_e = np.zeros((3, nM))
        ok = True
        for a in range(3):
            pa, pbb = phi(na, a), phi(nb, a)
            if pa is None or pbb is None:
                ok = False; break
            g_e[a] = k[a] * (pa - pbb)
        if ok:
            Gs.append(g_e); used += 1
    G = np.array(Gs)                                        # (n_cbush, 3, nM)
    # fold in the unit mount drive participation Gamma_i = phi_mount(z)
    mrow, _, _ = R.reduced_row(MOUNT, "Z"); Gamma = (mrow @ Q)[inb]
    G = G * Gamma[None, None, :]

    # match to measured survey -> which modes are anchored
    D = SB.build_dofs(R); _, pairs = SB.match_modes(D, Q)
    matched = {int(p[1]) for p in pairs}
    is_meas = np.array([int(k) in matched for k in inb])

    fg = np.linspace(40, 300, 700); w = 2 * np.pi * fg

    def strut_rms(fmod, ampscale, want_spec=False):
        wi = 2 * np.pi * fmod
        qtil = 1.0 / (wi[:, None] ** 2 - w[None, :] ** 2 + 2j * ZETA * wi[:, None] * w[None, :])   # (nM, nf)
        Gp = G * ampscale[None, None, :]
        resp = np.einsum("eam,mf->eaf", Gp, qtil)          # (ncb,3,nf)
        F = np.sqrt((np.abs(resp) ** 2).sum((0, 1)))       # (nf,)
        bandmask = (fg >= BAND[0]) & (fg <= BAND[1])
        rms = float(np.sqrt(np.mean(F[bandmask] ** 2)))
        return (rms, F) if want_spec else rms

    nom_rms, spec_fem = strut_rms(fb, np.ones(nM), True)
    # twin frequencies: matched -> measured
    meas_f = fb.copy()
    fm_map = {int(p[1]): float(D["mfr"][p[0]]) for p in pairs}
    for j, k in enumerate(inb):
        if int(k) in fm_map:
            meas_f[j] = fm_map[int(k)]
    twin_rms, spec_twin = strut_rms(meas_f, np.ones(nM), True)
    # measured-modes-only nominal (trust)
    meas_only_rms = strut_rms(fb, is_meas.astype(float), False)

    # Monte Carlo band
    rng = np.random.default_rng(0)
    sdf = np.where(is_meas, SD_F_MEAS, SD_F_UNM); sda = np.where(is_meas, SD_A_MEAS, SD_A_UNM)

    def mc(mask):
        out = np.empty(N_MC)
        for t in range(N_MC):
            fpert = fb * (1.0 + np.where(mask, rng.normal(0, sdf), 0.0))
            apert = np.exp(np.where(mask, rng.normal(0, sda), 0.0))
            out[t] = strut_rms(fpert, apert)
        return out

    allm = np.ones(nM, bool)
    mc_all = mc(allm); mc_unm = mc(~is_meas); mc_meas = mc(is_meas)
    pct = lambda a: [float(np.percentile(a, 2.5)), float(np.percentile(a, 50)), float(np.percentile(a, 97.5))]
    v_all = np.var(np.log(mc_all)); v_unm = np.var(np.log(mc_unm)); v_meas = np.var(np.log(mc_meas))

    rec = {"deliverable": "strut-connection force QOI (real CBUSH force) with uncertainty band attributing unmeasured modes",
           "n_strut_cbush_used": int(used), "strut_pids": sorted(STRUT_PIDS), "n_inband_modes": int(nM),
           "n_measured_modes": int(is_meas.sum()),
           "qoi_units": "aggregate strut CBUSH force per unit top-plate-center mount drive (relative; abs needs input spec)",
           "nominal_FEM_rms": nom_rms, "twin_freqanchored_rms": twin_rms, "measured_modes_only_rms": meas_only_rms,
           "trust_fraction_strut_force": round(meas_only_rms / (nom_rms + 1e-30), 3),
           "band_all_2p5_50_97p5": pct(mc_all),
           "band_pct_of_median": round(float((pct(mc_all)[2] - pct(mc_all)[0]) / 2 / pct(mc_all)[1] * 100), 0),
           "band_variance_share_unmeasured": round(float(v_unm / (v_unm + v_meas + 1e-30)), 2),
           "log_sd_all": round(float(np.sqrt(v_all)), 3), "log_sd_unmeasured": round(float(np.sqrt(v_unm)), 3),
           "log_sd_measured": round(float(np.sqrt(v_meas)), 3),
           "assumptions": {"freq_sd_meas": SD_F_MEAS, "freq_sd_unmeas": SD_F_UNM,
                           "logamp_sd_meas": SD_A_MEAS, "logamp_sd_unmeas": SD_A_UNM, "n_mc": N_MC},
           "caveat": "real CBUSH force but unit mount drive (abs scale needs input); CBUSH force in basic frame "
                     "(orientation ignored); twin=freq-anchored; MC assumptions labeled. NO NUTS.",
           "note": "EXPLORATORY; YELLOW."}
    (WS / "out" / "strut_force_number.json").write_text(json.dumps(rec, indent=2))

    # figure
    fig, (axS, axH) = plt.subplots(1, 2, figsize=(13.5, 5), gridspec_kw={"width_ratios": [1.2, 1]})
    axS.semilogy(fg, spec_fem, color="#1f77b4", lw=1.4, label="as-delivered FEM")
    axS.semilogy(fg, spec_twin, color="#d2691e", lw=1.4, label="freq-anchored twin")
    for j, k in enumerate(inb):
        axS.axvline(fb[j], color=("#2ca02c" if is_meas[j] else "#d62728"), lw=0.6, alpha=0.5)
    axS.set_xlim(40, 300); axS.set_xlabel("frequency (Hz)", fontsize=9)
    axS.set_ylabel("strut CBUSH force |F(f)|  (per unit mount drive)", fontsize=9)
    axS.set_title("Strut-connection force spectrum (REAL CBUSH force). green=data-anchored mode, red=unmeasured",
                  fontsize=8.8)
    axS.legend(fontsize=8, frameon=False); axS.spines[["top", "right"]].set_visible(False)

    axH.hist(mc_all, bins=40, color="0.7", label="all modes uncertain")
    axH.hist(mc_unm, bins=40, color="#d62728", alpha=0.6, label="unmeasured only")
    axH.hist(mc_meas, bins=40, color="#2ca02c", alpha=0.6, label="measured only")
    axH.axvline(nom_rms, color="#1f77b4", lw=1.5, label="FEM nominal")
    axH.set_xlabel("strut-force band-RMS (relative)", fontsize=9)
    axH.set_title(f"Band: median {pct(mc_all)[1]:.2g}, +/-{rec['band_pct_of_median']:.0f}%; "
                  f"{100*rec['band_variance_share_unmeasured']:.0f}% of variance from UNMEASURED modes", fontsize=8.5)
    axH.legend(fontsize=7.5, frameon=False); axH.spines[["top", "right"]].set_visible(False)
    cap = (f"REAL strut-connection (CBUSH pid 803-807, {used} elements) force QOI per unit top-plate mount drive. "
           f"Trust = {100*rec['trust_fraction_strut_force']:.0f}% of the nominal strut force is carried by MEASURED "
           f"modes. 95% band ~ +/-{rec['band_pct_of_median']:.0f}% of median, and "
           f"{100*rec['band_variance_share_unmeasured']:.0f}% of that band's variance comes from the UNMEASURED "
           f"~230-258 Hz strut modes -> THAT is where a top-plate test >200 Hz would buy down the risk. Unit mount "
           f"drive (abs needs input); MC assumptions labeled; freq-anchored twin. NO NUTS.")
    fig.text(0.01, -0.03, cap, fontsize=7.2, wrap=True, va="top")
    fig.tight_layout(rect=[0, 0.06, 1, 1])
    outp = WS / "figures" / "strut_force_number.png"
    fig.savefig(outp, dpi=150, bbox_inches="tight"); plt.close(fig)

    print(f"strut CBUSH used: {used}; in-band modes {nM} ({int(is_meas.sum())} measured)")
    print(f"nominal FEM strut-force RMS (rel): {nom_rms:.3g}  | freq-anchored twin: {twin_rms:.3g}")
    print(f"TRUST: measured modes carry {100*rec['trust_fraction_strut_force']:.0f}% of nominal strut force")
    print(f"95% band: [{pct(mc_all)[0]:.3g}, {pct(mc_all)[2]:.3g}], median {pct(mc_all)[1]:.3g}  "
          f"(+/-{rec['band_pct_of_median']:.0f}%)")
    print(f"band variance share from UNMEASURED modes: {100*rec['band_variance_share_unmeasured']:.0f}%  "
          f"(log-sd all {rec['log_sd_all']}, unmeas {rec['log_sd_unmeasured']}, meas {rec['log_sd_measured']})")
    print(f"wrote {outp}")
    return rec


if __name__ == "__main__":
    run()
