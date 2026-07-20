"""
EX-D: What the 7004C toolbox does on a multi-point payload — net-force limiting
vs moment limiting vs (hypothetical) coupled flight truth.

Payload = EX-B box with CG plan offset e_x = 0.03 m (ledger D1) so a UNIFORM
vertical shaker drive excites the rocking (pitch) mode through heave-pitch
coupling — the 7004C p.8 "uniformity of attachment motion" overtest mechanism.

FLIGHT (hypothetical, labeled): payload on the compliant plate (EX-C model),
unit-PSD point force; gives per-foot/net force, My moment, mean-foot accel PSDs.
TEST: same payload on a rigid shaker; input spec = octave-band peak-hold
envelope of the flight mean-foot accel PSD (ledger D2, no extra margin).
Arms: (i) unlimited; (ii) semi-empirical NET-Fz limit, C^2 from Eq B1/B2 at the
total-mass ratio, fb = fixed-base fundamental, n=1 (Eq 2a/2b; the p.10 default
practice); (iii) arm ii + |My| moment limit enveloped from the coupled flight
analysis (7004C §5.8 method extended to the moment channel).

Verification: Newton checks (net Fz = m*az_cg; My about CG = Iyy*th_ddot_y) to
machine precision; rigid low-f apparent mass = M0; limited responses respect
their limits; overtest ratios reported per quantity contract Q9.
"""
import os
import numpy as np
import scipy.linalg as sla
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from common import (M_PAY, AX, box_inertia, KZ_FOOT, plate_modal_system,
                    coupled_plate_payload_frf, payload_vertical_3dof,
                    payload_on_shaker, octave_band_envelope,
                    simple_tdfl_normalized_force, TPL, FIG, RES, save_json, stamp)

SCRIPT = "ex_d_force_limits.py"
EX_OFF = 0.03            # ledger D1
M_PLATE = 2700.0 * 1.0 * 0.8 * TPL


def main():
    # ---------------- flight (coupled, hypothetical) ----------------
    sysd = plate_modal_system(1250.0)
    f0 = test_modes()
    base = np.geomspace(20, 500, 1200)
    refine = np.concatenate([np.linspace(v * 0.8, min(v * 1.2, 500), 500) for v in f0])
    freqs = np.unique(np.concatenate([base, refine]))
    cp = coupled_plate_payload_frf(freqs, sysd, ex=EX_OFF)
    w2 = (2 * np.pi * freqs) ** 2
    acc_feet = -(w2[:, None]) * cp["wfeet"]
    Ff_fl = cp["Ffoot"]                                  # N per N drive
    xfO = np.array([+AX, +AX, -AX, -AX])
    netF_fl = Ff_fl.sum(axis=1)
    My_fl = -(Ff_fl * xfO).sum(axis=1)
    S_aa_fl = (np.abs(acc_feet) ** 2).mean(axis=1)       # mean-foot accel PSD
    S_net_fl = np.abs(netF_fl) ** 2
    S_my_fl = np.abs(My_fl) ** 2
    S_foot_fl = np.abs(Ff_fl) ** 2

    # ---------------- test spec + shaker responses ----------------
    spec = octave_band_envelope(freqs, S_aa_fl)          # ledger D2
    sh = payload_on_shaker(freqs, ex=EX_OFF)
    # Newton verification
    newton_netF = float(np.max(np.abs(sh["Ffoot"].sum(axis=1) - M_PAY * sh["acc_cg"][:, 0])
                               / np.abs(M_PAY * sh["acc_cg"][:, 0])))
    Mp, Lp = payload_vertical_3dof(ex=EX_OFF)
    xf_cg = -Lp[:, 2]                                    # foot x-arm rel CG
    My_cg = -(sh["Ffoot"] * xf_cg).sum(axis=1)
    Iyy = box_inertia()[1, 1]
    newton_my = float(np.max(np.abs(My_cg - Iyy * sh["acc_cg"][:, 2])
                             / np.maximum(np.abs(Iyy * sh["acc_cg"][:, 2]), 1e-12)))
    rigid_lowf = float(np.abs(sh["Ffoot"].sum(axis=1))[0])   # ~M0 at 20 Hz

    S_net_t = np.abs(sh["netF"]) ** 2 * spec
    S_my_t = np.abs(sh["My"]) ** 2 * spec
    S_foot_t = np.abs(sh["Ffoot"]) ** 2 * spec[:, None]
    S_acg_t = np.abs(sh["acc_cg"][:, 0]) ** 2 * spec

    # ---------------- limits ----------------
    mass_ratio = M_PAY / M_PLATE
    Q2 = 25.0
    C2 = float(simple_tdfl_normalized_force(mass_ratio, Q2))
    fb = f0[-1]                                          # highest = bounce-like mode
    rolloff = np.where(freqs <= fb, 1.0, (fb / freqs) ** 2)   # Eq 2b, n=1
    S_fflim = C2 * M_PAY**2 * spec * rolloff             # net-force limit (Q8)
    S_mylim = octave_band_envelope(freqs, S_my_fl)       # §5.8-style moment envelope

    arms = {}
    s2 = np.minimum(1.0, S_fflim / np.maximum(S_net_t, 1e-30))
    s3 = np.minimum(s2, S_mylim / np.maximum(S_my_t, 1e-30))
    for name, s in [("i_unlimited", np.ones_like(freqs)), ("ii_netF", s2),
                    ("iii_netF_plus_My", s3)]:
        arms[name] = dict(scale=s, S_net=S_net_t * s, S_my=S_my_t * s,
                          S_foot=S_foot_t * s[:, None], S_acg=S_acg_t * s)

    # limited responses respect limits?
    lim_ok_ii = float(np.max(arms["ii_netF"]["S_net"] / S_fflim))
    lim_ok_iii = float(np.max(arms["iii_netF_plus_My"]["S_my"] / S_mylim))

    # ---------------- overtest ratios (Q9) ----------------
    def band_peak(S, fc, half=0.10):
        sel = (freqs >= fc * (1 - half)) & (freqs <= fc * (1 + half))
        return float(S[sel].max())

    # NOTE (decisions_log D9): test modes 93.1 (pure thx) and 94.1 (z-thy pitch)
    # are 1% apart - band metrics cannot separate them, so the table reports the
    # two separable z-thy modes only. thx is handled as the undertest finding
    # below (the uniform test excites it EXACTLY zero by symmetry e_y=0).
    table = {}
    for fc, mode_name in [(f0[1], "pitch(z-thy lower)"), (f0[2], "bounce(z-thy upper)")]:
        row = {}
        for name, a in arms.items():
            row[name] = dict(
                foot_worst=max(band_peak(a["S_foot"][:, j], fc)
                               / max(band_peak(S_foot_fl[:, j], fc), 1e-30)
                               for j in range(4)),
                netF=band_peak(a["S_net"], fc) / max(band_peak(S_net_fl, fc), 1e-30),
                My=band_peak(a["S_my"], fc) / max(band_peak(S_my_fl, fc), 1e-30))
        table[f"{mode_name}@{fc:.1f}Hz"] = row

    # thx (roll) channel: flight excites it via plate y-slope; the uniform
    # single-axis test cannot (zero coupling) -> structural UNDERTEST.
    acc_thx_fl = -(w2) * cp["qp"][:, 1]
    thx_undertest = dict(
        flight_peak_acc_thx=float(np.max(np.abs(acc_thx_fl))),
        flight_peak_freq=float(freqs[np.argmax(np.abs(acc_thx_fl))]),
        test_acc_thx_max=float(np.max(np.abs(sh["acc_cg"][:, 1]))),
        statement=("uniform vertical shaker drive with e_y=0 excites thx exactly "
                   "zero; flight thx response peaks near 93 Hz -> a channel no "
                   "force/moment limit can restore (needs multi-point/multi-axis "
                   "excitation)"))

    C2_flight = float(np.max(S_net_fl / (M_PAY**2 * spec)))
    results = dict(
        ex_offset_m=EX_OFF, test_modes_hz=list(map(float, f0)),
        C2_semi_empirical=C2, C2_implied_by_flight=C2_flight,
        mass_ratio_used=mass_ratio, Q2_used=Q2, fb_hz=float(fb),
        newton_netF_relerr=newton_netF, newton_My_relerr=newton_my,
        rigid_lowf_netF_per_ab=rigid_lowf, M0=M_PAY,
        limited_respects_limit=dict(ii_net=lim_ok_ii, iii_my=lim_ok_iii),
        overtest_table=table, thx_undertest=thx_undertest,
        labels=dict(flight="HYPOTHETICAL coupled plate simulation (not flight data)"))
    save_json(os.path.join(RES, "ex_d_results.json"), results)

    # ================= figures =================
    plt.rcParams.update({"font.size": 9, "axes.spines.top": False,
                         "axes.spines.right": False})

    fig, axes = plt.subplots(2, 2, figsize=(12.5, 8.6))
    ax = axes[0, 0]
    ax.loglog(freqs, S_aa_fl, color="0.15", lw=1.1)
    ax.loglog(freqs, spec, color="#2980b9", lw=1.3)
    ax.annotate("flight mean-foot accel PSD\n(HYPOTHETICAL coupled sim)", (22, 2e-6),
                fontsize=8, color="0.15")
    ax.annotate("test input spec =\noctave peak-hold envelope", (22, 3e-1),
                fontsize=8, color="#2980b9")
    ax.set_ylabel("accel PSD, (m/s²)²/Hz per unit drive-force PSD (log)")
    ax.set_title("a. Spec construction (the envelope IS the conservatism)",
                 fontsize=9.5, loc="left")
    ax = axes[0, 1]
    ax.loglog(freqs, arms["i_unlimited"]["S_net"], color="#c0392b", lw=1.1)
    ax.loglog(freqs, arms["ii_netF"]["S_net"], color="#27ae60", lw=1.3)
    ax.loglog(freqs, S_fflim, color="#2980b9", lw=1.0, ls="--")
    ax.loglog(freqs, S_net_fl, color="0.15", lw=1.1)
    ax.annotate("test unlimited", (22, band_peak(arms["i_unlimited"]["S_net"], f0[-1]) * 0.5),
                fontsize=8, color="#c0392b")
    ax.annotate(f"semi-empirical limit, C²={C2:.1f}", (22, S_fflim[0] * 1.6),
                fontsize=8, color="#2980b9")
    ax.annotate("flight net force", (22, S_net_fl[0] * 0.15), fontsize=8, color="0.15")
    ax.set_ylabel("NET vertical force PSD, N²/Hz (log)")
    ax.set_title("b. Net-force limiting works where the net force LOOKS", fontsize=9.5,
                 loc="left")
    ax = axes[1, 0]
    jworst = int(np.argmax(S_foot_t.max(axis=0)))
    ax.loglog(freqs, arms["i_unlimited"]["S_foot"][:, jworst], color="#c0392b", lw=1.0)
    ax.loglog(freqs, arms["ii_netF"]["S_foot"][:, jworst], color="#27ae60", lw=1.3)
    ax.loglog(freqs, arms["iii_netF_plus_My"]["S_foot"][:, jworst], color="#8e44ad", lw=1.2)
    ax.loglog(freqs, S_foot_fl[:, jworst], color="0.15", lw=1.1)
    ax.annotate("test unlimited / net-F-limited (red/green):\nrocking mode keeps "
                "hammering this foot", (60, arms["ii_netF"]["S_foot"][:, jworst].max() * 0.3),
                fontsize=8, color="#c0392b")
    ax.annotate("+ moment limit (purple)", (22, 1e-2), fontsize=8, color="#8e44ad")
    ax.annotate("flight (per-foot)", (22, S_foot_fl[:, jworst].max() * 1e-4), fontsize=8,
                color="0.15")
    ax.set_xlabel("frequency, Hz (log)")
    ax.set_ylabel(f"FOOT {jworst+1} force PSD, N²/Hz (log)")
    ax.set_title("c. ...but the per-foot force is what bends brackets", fontsize=9.5,
                 loc="left")
    ax = axes[1, 1]
    ax.loglog(freqs, arms["i_unlimited"]["S_my"], color="#c0392b", lw=1.0)
    ax.loglog(freqs, arms["ii_netF"]["S_my"], color="#27ae60", lw=1.3)
    ax.loglog(freqs, arms["iii_netF_plus_My"]["S_my"], color="#8e44ad", lw=1.2)
    ax.loglog(freqs, S_mylim, color="#2980b9", lw=1.0, ls="--")
    ax.loglog(freqs, S_my_fl, color="0.15", lw=1.1)
    ax.annotate("moment limit (flight envelope, §5.8 method)", (22, S_mylim[0] * 2),
                fontsize=8, color="#2980b9")
    ax.set_xlabel("frequency, Hz (log)")
    ax.set_ylabel("interface moment |My|² PSD, (N·m)²/Hz (log)")
    ax.set_title("d. The moment channel: invisible to net-force limiting", fontsize=9.5,
                 loc="left")
    fig.suptitle("EX-D — Force-limited test of the multi-point payload (CG offset 0.03 m) "
                 "vs HYPOTHETICAL coupled flight. All PSDs per unit flight drive-force PSD.",
                 fontsize=10)
    fig.tight_layout(rect=(0, 0.02, 1, 0.95))
    stamp(fig, SCRIPT, "flight = hypothetical coupled simulation")
    fig.savefig(os.path.join(FIG, "fig_d1_test_vs_flight.png"), dpi=160)
    plt.close(fig)

    # --- fig_d2: overtest ratio bars + thx undertest panel ---
    fig, axes = plt.subplots(1, 3, figsize=(12.5, 4.6))
    armnames = ["i_unlimited", "ii_netF", "iii_netF_plus_My"]
    armlabels = ["unlimited", "net-F limited\n(7004C p.10 default)", "net-F + moment\nlimited"]
    cols = ["#c0392b", "#27ae60", "#8e44ad"]
    for ax, (mode_key, row) in zip(axes[:2], table.items()):
        vals = [row[a]["foot_worst"] for a in armnames]
        ax.bar(range(3), vals, color=cols, width=0.55)
        for i, v in enumerate(vals):
            ax.annotate(f"{v:.0f}x\n({10*np.log10(v):.0f} dB)", (i, v * 1.15),
                        ha="center", fontsize=8.5)
        ax.axhline(1.0, color="0.3", lw=0.9, ls="--")
        ax.set_yscale("log")
        ax.set_ylim(0.3, 3e4)
        ax.set_xticks(range(3))
        ax.set_xticklabels(armlabels, fontsize=7.5)
        ax.set_title(mode_key, fontsize=9, loc="left")
    axes[0].set_ylabel("worst per-foot overtest ratio\npeak test PSD / peak flight PSD "
                       "(±10% band, log)")
    ax = axes[2]
    ax.semilogy(freqs, np.abs(acc_thx_fl), color="0.15", lw=1.1)
    ax.semilogy(freqs, np.maximum(np.abs(sh["acc_cg"][:, 1]), 1e-18), color="#c0392b",
                lw=1.2)
    ax.annotate("flight roll accel |thx''| (rad/s² per N)", (25, 2e-1), fontsize=8,
                color="0.15")
    ax.annotate("test roll accel = EXACTLY 0\n(uniform drive, e_y=0):\nUNDERTEST no "
                "limit can fix", (40, 1e-14), fontsize=8, color="#c0392b")
    ax.set_xlabel("frequency, Hz")
    ax.set_xscale("log")
    ax.set_ylim(1e-18, 1e2)
    ax.set_title("the channel the test never excites", fontsize=9, loc="left")
    fig.suptitle("EX-D — Per-foot overtest at the two z–thy modes: net-force limiting\n"
                 "leaves a large rocking-foot overtest (moment limit removes it); "
                 "the roll channel is UNDER-tested", fontsize=9.5)
    fig.tight_layout(rect=(0, 0.02, 1, 0.9))
    stamp(fig, SCRIPT, "flight = hypothetical coupled simulation")
    fig.savefig(os.path.join(FIG, "fig_d2_overtest_bars.png"), dpi=170)
    plt.close(fig)

    print("EX-D done.")
    print(f"  test modes: {[f'{x:.1f}' for x in f0]} Hz | C2 semi-emp {C2:.2f} | "
          f"C2 implied by flight {C2_flight:.2f}")
    print(f"  newton netF {newton_netF:.2e} | newton My {newton_my:.2e} | "
          f"lowf netF/ab {rigid_lowf:.4f} (M0={M_PAY})")
    print(f"  limit respected ii {lim_ok_ii:.3f} iii {lim_ok_iii:.3f} (<=1+tol)")
    for k, row in table.items():
        print(f"  {k}: " + " | ".join(f"{a}: foot {row[a]['foot_worst']:.2f}x "
                                      f"My {row[a]['My']:.2f}x" for a in armnames))


def test_modes():
    Mp, Lp = payload_vertical_3dof(ex=EX_OFF)
    Kp = KZ_FOOT * (Lp.T @ Lp)
    lam = sla.eigh(Kp, Mp, eigvals_only=True)
    return np.sqrt(np.maximum(lam, 0)) / (2 * np.pi)


if __name__ == "__main__":
    main()
