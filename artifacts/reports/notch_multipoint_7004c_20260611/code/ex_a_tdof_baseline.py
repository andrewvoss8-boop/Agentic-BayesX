"""
EX-A: Replicate NASA-HDBK-7004C's own TDOF impedance-method example (Fig 7/9),
the simple-TDOF force-limit chart (Fig 8 / Eq B1-B2), and the semi-empirical
limit (Eq 1/2) on that system. This anchors every later example to the handbook.

Anchors (7004C pages 34-37, evaluated at the handbook's grid r = 0.62, 1.00, 1.62):
  |As(1)|=50.01  |Ms(1)|=0.02  |Ml(0.62)|=1.62  |Ml(1)|=50.01  |Ms+Ml|(1)=50.03
  |A(0.62)|=51.76  |A(1)|=0.02 (the notch)  |F(0.62)|=84.08  |F(1.62)|=5.25
  Fig 8 ordinate at M2/M1=1, Q=50: 2.64 (handbook rounds 1.62^2; exact 2.618)
Verification extra: direct coupled 2-DOF solve must match the impedance method
(Eq 3/4) to machine precision at every frequency.
"""
import os
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from common import (QA, M2, coupled_interface, simple_tdfl_normalized_force,
                    sdof_free_acceleration, source_apparent_mass,
                    load_apparent_mass, FIG, RES, WS, save_json, stamp)

SCRIPT = "ex_a_tdof_baseline.py"


def direct_coupled_solve(r, Q=QA):
    """Direct 2-DOF coupled solve, base accel Ao=1 (verification path).
    Returns interface acceleration (= mass-1 accel) and interface force (= m2*x2'')."""
    m = k = 1.0
    c = 1.0 / Q
    A = np.zeros((len(r), ), dtype=complex)
    F = np.zeros((len(r), ), dtype=complex)
    for i, ri in enumerate(r):
        w = ri
        Xb = -1.0 / w**2                      # unit base acceleration
        K = np.array([[k + 1j*w*c + k + 1j*w*c - w**2*m, -(k + 1j*w*c)],
                      [-(k + 1j*w*c),                      k + 1j*w*c - w**2*m]],
                     dtype=complex)
        rhs = np.array([(k + 1j*w*c) * Xb, 0.0], dtype=complex)
        X = np.linalg.solve(K, rhs)
        A[i] = -w**2 * X[0]
        F[i] = -w**2 * X[1] * M2              # force transmitted to load = m2*a2
    return A, F


def main():
    os.makedirs(FIG, exist_ok=True)
    # dense grid + the handbook's quoted grid points
    r = np.unique(np.concatenate([np.linspace(0.02, 2.0, 1980),
                                  [0.62, 1.0, 1.62],
                                  np.linspace(0.55, 0.70, 600),     # resolve lower peak
                                  np.linspace(0.95, 1.05, 600),     # resolve notch
                                  np.linspace(1.55, 1.70, 600)]))
    As, Ms, Ml, A, F = coupled_interface(r)

    # ---- verification: impedance method == direct coupled solve -------------
    Ad, Fd = direct_coupled_solve(r)
    imp_vs_direct_A = float(np.max(np.abs(np.abs(Ad) - np.abs(A)) / np.abs(A)))
    imp_vs_direct_F = float(np.max(np.abs(np.abs(Fd) - np.abs(F)) / np.abs(F)))

    def at(rq, arr):
        return float(np.abs(arr[np.argmin(np.abs(r - rq))]))

    anchors = {
        "As_at_1": dict(ours=at(1.0, As), handbook=50.01),
        "Ms_at_1": dict(ours=at(1.0, Ms), handbook=0.02),
        "Ml_at_0p62": dict(ours=at(0.62, Ml), handbook=1.62),
        "Ml_at_1": dict(ours=at(1.0, Ml), handbook=50.01),
        "sum_at_1": dict(ours=at(1.0, Ms + Ml), handbook=50.03),
        "A_at_0p62": dict(ours=at(0.62, A), handbook=51.76),
        "A_at_1_notch": dict(ours=at(1.0, A), handbook=0.02),
        "F_at_0p62": dict(ours=at(0.62, F), handbook=84.08),
        "F_at_1p62": dict(ours=at(1.62, F), handbook=5.25),
    }
    # Fig 8 ordinate at mass ratio 1, Q=50 (handbook quotes 2.64 = rounded 1.62^2)
    fig8_at_1 = float(simple_tdfl_normalized_force(1.0, 50.0))
    anchors["fig8_ordinate_mr1_Q50"] = dict(ours=fig8_at_1, handbook=2.64)
    for k_, v in anchors.items():
        v["rel_err"] = abs(v["ours"] - v["handbook"]) / abs(v["handbook"])

    # exact coupled frequencies (Eq B1) and true damped peak (finer than handbook grid)
    golden = dict(r_low=float(np.sqrt(1.5 - np.sqrt(1.25))),
                  r_high=float(np.sqrt(1.5 + np.sqrt(1.25))),
                  A_true_peak=float(np.max(np.abs(A))),
                  note=("handbook Fig 9 values are read on its r-grid (0.62/1.62); the "
                        "exact undamped coupled freqs are golden-ratio 0.618/1.618 and the "
                        "true damped |A| peak there is higher than the 51.76 grid value"))

    # ---- semi-empirical / TDFL story on this system --------------------------
    # Test input = ENVELOPE of the flight interface acceleration (7004C practice:
    # the acceleration spec envelopes the flight environment): flat at max|A|.
    A_spec = float(np.max(np.abs(A)))                  # = 51.76 handbook value
    F_hard = A_spec * np.abs(Ml)                       # hard-mount net force
    C2 = fig8_at_1                       # Fig-8 ordinate IS C^2 (7004C p.33)
    F_semi = np.sqrt(C2) * M2 * A_spec * np.ones_like(r)    # Eq 1a, f<fb
    fb = 1.0
    F_semi = np.where(r <= fb, F_semi, F_semi * (fb / r))   # Eq 1b, n=1
    F_limited = np.minimum(F_hard, F_semi)
    notch_factor = F_limited / F_hard                  # input knockdown per Eq-1 logic
    overtest_unl = float(np.max(F_hard) / np.max(np.abs(F)))
    overtest_lim = float(np.max(F_limited) / np.max(np.abs(F)))

    results = dict(anchors=anchors, golden=golden,
                   impedance_vs_direct=dict(A=imp_vs_direct_A, F=imp_vs_direct_F),
                   C2_from_fig8=C2, A_spec_envelope=A_spec,
                   overtest_factor_unlimited=overtest_unl,
                   overtest_factor_limited=overtest_lim,
                   notch_depth_vs_spec_dB=float(20 * np.log10(A_spec / at(1.0, A))),
                   unnotched_force_estimate=float(np.max(F_hard)),
                   handbook_unnotched_quote="~2500 (7004C p.37)")
    save_json(os.path.join(RES, "ex_a_results.json"), results)

    # ================= figures =================
    plt.rcParams.update({"font.size": 9, "axes.spines.top": False,
                         "axes.spines.right": False})

    # --- fig_a1: six-panel Fig-9 replication (small multiples) ---
    fig, axes = plt.subplots(2, 3, figsize=(11.5, 6.4), sharex=True)
    panels = [(np.abs(As), "a. Free acceleration |As|", [(1.0, 50.01)]),
              (np.abs(Ms), "b. Source apparent mass |Ms|", [(1.0, 0.02)]),
              (np.abs(Ml), "c. Load apparent mass |Ml|", [(0.62, 1.62), (1.0, 50.01)]),
              (np.abs(Ms + Ml), "d. |Ms + Ml|", [(1.0, 50.03)]),
              (np.abs(A), "e. Interface acceleration |A|", [(0.62, 51.76), (1.0, 0.02)]),
              (np.abs(F), "f. Interface force |F|", [(0.62, 84.08), (1.62, 5.25)])]
    for ax, (y, title, marks) in zip(axes.flat, panels):
        ax.semilogy(r, y, color="0.15", lw=1.2)
        for (rm, hv) in marks:
            ax.plot([rm], [hv], "o", ms=5, mfc="none", mec="#c0392b", mew=1.4)
            ax.annotate(f"7004C: {hv:g}", (rm, hv), textcoords="offset points",
                        xytext=(6, 6), fontsize=7.5, color="#c0392b")
        ax.set_title(title, fontsize=9, loc="left")
        ax.set_xlim(0, 2)
    for ax in axes[1]:
        ax.set_xlabel("frequency ratio  $\\omega/\\omega_0$  (linear, matches handbook Fig 9)")
    axes[0, 0].set_ylabel("magnitude (nondim.)")
    axes[1, 0].set_ylabel("magnitude (nondim.)")
    fig.suptitle("EX-A — Replication of 7004C Figure 9 (impedance method, two identical "
                 "oscillators, Q=50): red circles = handbook values, line = this model",
                 fontsize=10)
    fig.tight_layout(rect=(0, 0.02, 1, 0.97))
    stamp(fig, SCRIPT, "linear freq axis deliberately matches handbook Fig 9")
    fig.savefig(os.path.join(FIG, "fig_a1_fig9_replication.png"), dpi=170)
    plt.close(fig)

    # --- fig_a2: Fig-8 replication ---
    mr = np.logspace(-3, 1, 400)
    fig, ax = plt.subplots(figsize=(7.2, 4.8))
    for Q2, c in [(5, "#7f8c8d"), (20, "#2c3e50"), (50, "0.1")]:
        y = simple_tdfl_normalized_force(mr, Q2)
        ax.loglog(mr, y, lw=1.3, color=c)
        ax.annotate(f"Q = {Q2}", (mr[6], y[6] * 0.78), fontsize=8.5, color=c)
    ax.plot([1.0], [2.64], "o", ms=6, mfc="none", mec="#c0392b", mew=1.5)
    ax.annotate("7004C quote at $M_2/M_1$=1: 2.64\n(ours 2.618 = exact golden-ratio value)",
                (1.0, 2.64), textcoords="offset points", xytext=(10, 10),
                fontsize=8, color="#c0392b")
    ax.axhline(50**2, color="0.6", lw=0.7, ls=":")
    ax.annotate("$Q^2$ asymptote (no load effect) — distance below = 'knockdown'",
                (1.2e-3, 50**2 * 1.25), fontsize=8, color="0.4")
    ax.set_xlabel("load/source mass ratio  $M_2/M_1$  (log)")
    ax.set_ylabel("$S_{FF}/(S_{AA} M_2^2)$  =  $C^2$   (log)")
    ax.set_title("EX-A — Replication of 7004C Figure 8 (Eq B1+B2): normalized force limit "
                 "at the lower coupled resonance", fontsize=9.5, loc="left")
    fig.tight_layout()
    stamp(fig, SCRIPT)
    fig.savefig(os.path.join(FIG, "fig_a2_fig8_replication.png"), dpi=170)
    plt.close(fig)

    # --- fig_a3: the notch + overtest story ---
    fig, axes = plt.subplots(1, 2, figsize=(11.5, 4.6))
    ax = axes[0]
    ax.semilogy(r, np.abs(A), color="0.15", lw=1.4)
    ax.semilogy(r, A_spec * np.ones_like(r), color="#2980b9", lw=1.1, ls="--")
    ax.annotate(f"shaker input spec = envelope of flight accel ({A_spec:.1f})",
                (0.05, A_spec * 1.5), fontsize=8, color="#2980b9")
    ax.annotate("flight interface acceleration:\nNOTCH to 0.02 at the load resonance\n"
                f"= {20*np.log10(A_spec/0.02):.0f} dB below the spec the shaker applies",
                (1.0, 0.02), textcoords="offset points", xytext=(14, 6), fontsize=8,
                arrowprops=dict(arrowstyle="-", color="0.4", lw=0.7))
    ax.set_xlabel("frequency ratio $\\omega/\\omega_0$")
    ax.set_ylabel("interface acceleration (nondim., log)")
    ax.set_title("The notch the shaker erases", fontsize=9.5, loc="left")
    ax = axes[1]
    ax.semilogy(r, F_hard, color="#c0392b", lw=1.3)
    ax.semilogy(r, np.abs(F), color="0.15", lw=1.3)
    ax.semilogy(r, F_semi, color="#2980b9", lw=1.1, ls="--")
    ax.semilogy(r, F_limited, color="#27ae60", lw=1.5)
    ax.annotate(f"hard-mount force, spec input:\npeak {np.max(F_hard):.0f} "
                "(handbook: ~2500)", (1.0, np.max(F_hard)),
                textcoords="offset points", xytext=(10, 2), fontsize=8, color="#c0392b")
    ax.annotate("coupled flight force (peak 84 at 0.62)", (0.6, 84.08),
                textcoords="offset points", xytext=(-8, 10), fontsize=8,
                color="0.15", ha="right")
    ax.annotate("semi-empirical limit $C\\,M_2\\,A_{spec}$,\n$C^2$=2.62 from Fig 8 "
                f"→ {np.sqrt(C2)*A_spec:.0f}", (0.05, np.sqrt(C2) * A_spec * 0.45),
                fontsize=8, color="#2980b9")
    ax.annotate(f"force-limited test (green):\npeak/flight peak = {overtest_lim:.2f}x\n"
                f"(unlimited: {overtest_unl:.1f}x = Q/C)", (1.28, 6), fontsize=8,
                color="#27ae60")
    ax.set_xlabel("frequency ratio $\\omega/\\omega_0$")
    ax.set_ylabel("interface force (nondim., log)")
    ax.set_title("What force limiting fixes (scalar world: it works)", fontsize=9.5,
                 loc="left")
    fig.suptitle("EX-A — 7004C baseline: notch, overtest, semi-empirical fix. Test input "
                 "= flat envelope of flight interface accel (7004C practice); amplitudes, "
                 "not PSD", fontsize=10)
    fig.tight_layout(rect=(0, 0.02, 1, 0.95))
    stamp(fig, SCRIPT)
    fig.savefig(os.path.join(FIG, "fig_a3_notch_overtest.png"), dpi=170)
    plt.close(fig)

    print("EX-A done. anchors:")
    for k_, v in anchors.items():
        print(f"  {k_:24s} ours={v['ours']:9.4f} handbook={v['handbook']:8.3f} "
              f"rel_err={v['rel_err']*100:6.2f}%")
    print(f"  impedance==direct: A {imp_vs_direct_A:.2e}, F {imp_vs_direct_F:.2e}")


if __name__ == "__main__":
    main()
