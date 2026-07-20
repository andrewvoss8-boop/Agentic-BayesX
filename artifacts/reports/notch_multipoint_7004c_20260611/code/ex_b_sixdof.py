"""
EX-B: What multi-point mounting + 6-DOF motion adds to the 7004C picture.

Rigid box (6 kg) on 4 feet at (+/-0.09, +/-0.07) m, CG 0.08 m up, enforced
uniform base motion (the shaker idealization). Outputs:
 1. the 6x6 interface apparent-mass MATRIX (the scalar M(f) of 7004C Q2 becomes
    a matrix; off-diagonals = CG-offset coupling),
 2. effective masses per DOF incl. ROTARY effective inertia (7004C App. A
    generalization; sum check = rigid mass/inertia, p.56),
 3. the RESULTANT-FORCE TRAP: at a rocking mode the per-foot forces are large
    while their sum (the quantity 7004C p.10 says is normally limited) nearly
    cancels and the interface moment is large.

Verification (checker-backed): numeric fixed-base modes vs closed-form 2x2/1x1
eigenvalues; M(omega->0) == rigid-body mass matrix about O; effective-mass sums.
"""
import os
import numpy as np
import scipy.linalg as sla
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from common import (M_PAY, H_CG, AX, AY, KZ_FOOT, KXY_FOOT, box_inertia,
                    payload_6dof_matrices, transform_O_from_CG,
                    apparent_mass_matrix_6dof, FIG, RES, save_json, stamp)

SCRIPT = "ex_b_sixdof.py"
DOFS = ["x", "y", "z", "rx", "ry", "rz"]


def fixed_base_modes():
    """Numeric modes of the payload on fixed feet (real stiffness)."""
    p = payload_6dof_matrices(hysteretic=False)
    lam, vec = sla.eigh(p["K"].real, p["M"])
    f = np.sqrt(np.maximum(lam, 0)) / (2 * np.pi)
    return f, vec, p


def analytic_modes():
    """Closed-form checks: bounce, torsion, two coupled lateral-rocking pairs."""
    m = M_PAY
    Ixx, Iyy, Izz = np.diag(box_inertia())
    kz, kxy, h = KZ_FOOT, KXY_FOOT, H_CG
    out = {}
    out["bounce_z"] = np.sqrt(4 * kz / m) / (2 * np.pi)
    out["torsion_rz"] = np.sqrt(4 * kxy * (AX**2 + AY**2) / Izz) / (2 * np.pi)
    # x - ry pair (rotation about y): K=[[4kxy, 4kxy h],[4kxy h, 4kxy h^2 + 4 kz AX^2]]
    K2 = np.array([[4 * kxy, 4 * kxy * h],
                   [4 * kxy * h, 4 * kxy * h**2 + 4 * kz * AX**2]])
    lam = sla.eigh(K2, np.diag([m, Iyy]), eigvals_only=True)
    out["x_ry_pair"] = list(np.sqrt(lam) / (2 * np.pi))
    # y - rx pair: K=[[4kxy, -4kxy h],[-4kxy h, 4kxy h^2 + 4 kz AY^2]]
    K2 = np.array([[4 * kxy, -4 * kxy * h],
                   [-4 * kxy * h, 4 * kxy * h**2 + 4 * kz * AY**2]])
    lam = sla.eigh(K2, np.diag([m, Ixx]), eigvals_only=True)
    out["y_rx_pair"] = list(np.sqrt(lam) / (2 * np.pi))
    return out


def rigid_mass_matrix_about_O():
    """Exact rigid-body 6x6 about the interface reference point O."""
    p = payload_6dof_matrices(hysteretic=False)
    T = transform_O_from_CG(p["r_ocg"])      # u_CG = T u_O
    return T.T @ p["M"] @ T


def effective_masses():
    """7004C Appendix A: participation-based effective masses about O.
    Modes of fixed-base payload; Gamma = Phi^T M T ; m_eff,n = Gamma_n p^2 / m_nn."""
    f, vec, p = fixed_base_modes()
    T = transform_O_from_CG(p["r_ocg"])
    Mcg = p["M"]
    meff = np.zeros((6, 6))
    for n in range(6):
        phi = vec[:, n]
        mnn = phi @ Mcg @ phi
        Gam = phi @ Mcg @ T          # (6,) participation vs base DOF about O
        meff[n] = Gam**2 / mnn
    return f, meff


def main():
    freqs = np.unique(np.concatenate([np.linspace(20, 250, 1800),
                                      np.linspace(85, 150, 1800)]))
    # ---------- apparent-mass matrix (symmetric case) ----------
    Mw = apparent_mass_matrix_6dof(freqs, ex=0.0)
    M0 = apparent_mass_matrix_6dof(np.array([0.05]), ex=0.0)[0].real  # quasi-static
    Mrb = rigid_mass_matrix_about_O()
    static_err = float(np.max(np.abs(M0 - Mrb)) / np.max(np.abs(Mrb)))

    fnum, vec, _ = fixed_base_modes()
    fan = analytic_modes()
    fan_sorted = np.sort(np.array([fan["bounce_z"], fan["torsion_rz"],
                                   *fan["x_ry_pair"], *fan["y_rx_pair"]]))
    mode_err = float(np.max(np.abs(np.sort(fnum) - fan_sorted) / fan_sorted))

    fE, meff = effective_masses()
    sums = meff.sum(axis=0)
    eff_sum_err = float(np.max(np.abs(sums - np.diag(Mrb)) / np.diag(Mrb)))

    # ---------- resultant trap: enforced base drives ----------
    # response of payload to unit base accel in z (uniform) vs x (lateral)
    p = payload_6dof_matrices(ex=0.0)
    Mcg, K, feet = p["M"], p["K"], p["feet"]
    T = transform_O_from_CG(p["r_ocg"])
    trap = {}
    for dn, dvec in [("z", 2), ("x", 0)]:
        Ff = np.zeros((len(freqs), 4), dtype=complex)   # vertical foot forces
        Fl = np.zeros((len(freqs), 4), dtype=complex)   # lateral (x) foot forces
        for i, fh in enumerate(freqs):
            w = 2 * np.pi * fh
            ab = np.zeros(6); ab[dvec] = 1.0            # base accel about O
            ub_O = ab / (-(w**2))
            ub_CG = T @ ub_O
            # relative formulation: K u = Kc ub ; here feet move rigidly with base
            rhs = np.zeros(6, dtype=complex)
            for ft in feet:
                JO = np.hstack([np.eye(3), -np.array([[0, -ft["r_o"][2], ft["r_o"][1]],
                                                      [ft["r_o"][2], 0, -ft["r_o"][0]],
                                                      [-ft["r_o"][1], ft["r_o"][0], 0]])])
                kf = np.diag(ft["k_diag"] * (1 + 0.04j))
                rhs += ft["J"].T @ kf @ (JO @ ub_O)
            u = np.linalg.solve(K - w**2 * Mcg, rhs)
            for jf, ft in enumerate(feet):
                JO = np.hstack([np.eye(3), -np.array([[0, -ft["r_o"][2], ft["r_o"][1]],
                                                      [ft["r_o"][2], 0, -ft["r_o"][0]],
                                                      [-ft["r_o"][1], ft["r_o"][0], 0]])])
                kf = np.diag(ft["k_diag"] * (1 + 0.04j))
                df = kf @ (JO @ ub_O - ft["J"] @ u)     # force ON payload
                Ff[i, jf] = df[2]
                Fl[i, jf] = df[0]
        netF = Ff.sum(axis=1)
        # moment about O: My = sum(z-forces * -x_i) + sum(x-forces * z arm (=0 at plane))
        xf = np.array([ft["r_o"][0] for ft in feet])
        My = -(Ff * xf).sum(axis=1)
        trap[dn] = dict(Ffoot=np.abs(Ff), netF=np.abs(netF), My=np.abs(My),
                        Flat=np.abs(Fl))

    # trap metric at the rocking-dominant mode under x-drive
    ry_modes = fan["x_ry_pair"]
    i_rock = np.argmin(np.abs(freqs - ry_modes[1]))
    i_rock = int(np.argmax(trap["x"]["Ffoot"].max(axis=1)
                           * (np.abs(freqs - ry_modes[1]) < 12)))  # peak near mode
    cancel = dict(freq=float(freqs[i_rock]),
                  foot_peak=float(trap["x"]["Ffoot"][i_rock].max()),
                  net=float(trap["x"]["netF"][i_rock]),
                  My=float(trap["x"]["My"][i_rock]))
    cancel["net_over_4foot"] = cancel["net"] / (4 * cancel["foot_peak"])

    results = dict(
        fixed_base_modes_numeric=sorted(fnum.tolist()),
        fixed_base_modes_analytic=fan_sorted.tolist(),
        analytic_detail={k: v for k, v in analytic_modes().items()},
        mode_match_max_rel_err=mode_err,
        static_limit_vs_rigid_mass_rel_err=static_err,
        rigid_mass_matrix_about_O=Mrb.tolist(),
        effective_mass_table=dict(mode_freqs=fE.tolist(), meff=meff.tolist(),
                                  col_sums=sums.tolist(),
                                  rigid_diag=np.diag(Mrb).tolist(),
                                  sum_rel_err=eff_sum_err),
        resultant_trap=cancel)
    save_json(os.path.join(RES, "ex_b_results.json"), results)

    # ================= figures =================
    plt.rcParams.update({"font.size": 8, "axes.spines.top": False,
                         "axes.spines.right": False})

    # --- fig_b1: 6x6 apparent mass matrix, small multiples ---
    fig, axes = plt.subplots(6, 6, figsize=(12.5, 11), sharex=True)
    units = {0: "kg", 1: "kg", 2: "kg", 3: "kg·m²", 4: "kg·m²", 5: "kg·m²"}
    for i in range(6):
        for j in range(6):
            ax = axes[i, j]
            mag = np.abs(Mw[:, i, j])
            on_diag = (i == j)
            big = mag.max() > 1e-6 * np.abs(Mw).max()
            ax.semilogy(freqs, np.maximum(mag, 1e-12),
                        color=("0.1" if on_diag else ("#c0392b" if big else "0.8")),
                        lw=1.2 if on_diag else 0.9)
            ax.axhline(max(abs(Mrb[i, j]), 1e-12), color="#2980b9", lw=0.7, ls=":")
            ax.set_ylim(1e-6, 3e3)
            ax.set_yticks([1e-4, 1e0, 1e3])
            if i == 5:
                ax.set_xlabel(f"$a_{{{DOFS[j]}}}$", fontsize=9)
            if j == 0:
                ax.set_ylabel(f"$F_{{{DOFS[i]}}}$", fontsize=9)
            ax.tick_params(labelsize=6)
    fig.suptitle("EX-B — The scalar 'apparent mass' of 7004C becomes a 6×6 MATRIX "
                 "(rigid box, 4 feet, uniform base drive about O).\n"
                 "Black=diagonal terms, red=non-negligible off-diagonal coupling "
                 "(CG height & geometry), gray≈0, dotted blue=rigid-body value "
                 "(f→0 limit = exact rigid mass matrix).\nRows: interface "
                 "force/moment about O (N, N·m); columns: base accel DOF; magnitude, "
                 "log y; x = 20–250 Hz linear (narrow band; modes at 88–135 Hz)",
                 fontsize=9.5)
    fig.tight_layout(rect=(0, 0.015, 1, 0.925))
    stamp(fig, SCRIPT, "linear f-axis: narrow 20-250 Hz band, modes legible")
    fig.savefig(os.path.join(FIG, "fig_b1_apparent_mass_matrix.png"), dpi=150)
    plt.close(fig)

    # --- fig_b2: effective masses incl rotary ---
    fig, axes = plt.subplots(1, 6, figsize=(12.5, 3.4), sharey=False)
    for j, ax in enumerate(axes):
        vals = meff[:, j]
        ax.bar(range(1, 7), vals / max(np.diag(Mrb)[j], 1e-12), color="0.25", width=0.6)
        ax.axhline(1.0, color="#2980b9", lw=0.8, ls=":")
        ax.set_title(f"dir {DOFS[j]}\nΣ={sums[j]:.3g} {units[j]}\nrigid={np.diag(Mrb)[j]:.3g}",
                     fontsize=8)
        ax.set_xlabel("mode #")
        ax.set_ylim(0, 1.15)
        if j == 0:
            ax.set_ylabel("effective mass / rigid total")
    fig.suptitle("EX-B — Effective masses per base DOF about O (7004C Appendix A, "
                 "generalized): rocking modes own ROTARY effective inertia; sums equal "
                 "the rigid totals exactly (p.56 check)", fontsize=9.5)
    fig.tight_layout(rect=(0, 0.02, 1, 0.88))
    stamp(fig, SCRIPT)
    fig.savefig(os.path.join(FIG, "fig_b2_effective_masses.png"), dpi=170)
    plt.close(fig)

    # --- fig_b3: resultant trap ---
    fig, axes = plt.subplots(1, 2, figsize=(11.5, 4.6), sharey=True)
    for ax, dn, ttl in [(axes[0], "z", "uniform vertical base drive (bounce):\n"
                         "net force = 4× foot force — net-force limiting SEES the mode"),
                        (axes[1], "x", "lateral base drive (CG-offset → rocking):\n"
                         "foot forces CANCEL in the net — the trap")]:
        t = trap[dn]
        ax.semilogy(freqs, t["Ffoot"][:, 0], color="#c0392b", lw=1.3)
        ax.semilogy(freqs, t["netF"], color="0.1", lw=1.3)
        ax.semilogy(freqs, t["My"], color="#27ae60", lw=1.2, ls="--")
        ax.set_xlabel("frequency, Hz (linear; modes 88–135 Hz)")
        ax.set_title(ttl, fontsize=9, loc="left")
    axes[0].set_ylabel("force / moment per unit base accel.\n(N per m/s²; N·m per m/s², log)")
    axes[0].annotate("|F| one foot (vertical)", (30, 8), fontsize=8, color="#c0392b")
    axes[0].annotate("|ΣF| net vertical", (30, 28), fontsize=8, color="0.1")
    axes[0].annotate("|My| interface moment ≈ 0", (30, 2e-3), fontsize=8, color="#27ae60")
    axes[1].annotate(f"at {cancel['freq']:.1f} Hz rocking mode:\n"
                     f"foot peak {cancel['foot_peak']:.1f}, net {cancel['net']:.2g}\n"
                     f"net/(4·foot) = {cancel['net_over_4foot']:.1%}\n"
                     f"moment |My| = {cancel['My']:.1f} N·m",
                     (cancel["freq"], cancel["foot_peak"]),
                     textcoords="offset points", xytext=(12, -42), fontsize=8,
                     arrowprops=dict(arrowstyle="-", color="0.4", lw=0.7))
    fig.suptitle("EX-B — The resultant-force trap: 7004C p.10 default practice limits the "
                 "NET in-axis force; rocking loads live in per-foot forces and the moment",
                 fontsize=10)
    fig.tight_layout(rect=(0, 0.02, 1, 0.93))
    stamp(fig, SCRIPT)
    fig.savefig(os.path.join(FIG, "fig_b3_resultant_trap.png"), dpi=170)
    plt.close(fig)

    print("EX-B done.")
    print("  modes numeric :", np.round(np.sort(fnum), 2))
    print("  modes analytic:", np.round(fan_sorted, 2))
    print(f"  mode err {mode_err:.2e} | static-limit err {static_err:.2e} | "
          f"eff-mass sum err {eff_sum_err:.2e}")
    print(f"  trap: net/(4*foot) = {cancel['net_over_4foot']:.3%} at {cancel['freq']:.1f} Hz")


if __name__ == "__main__":
    main()
