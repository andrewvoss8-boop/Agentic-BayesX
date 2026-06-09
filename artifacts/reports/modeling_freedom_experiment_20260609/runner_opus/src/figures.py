"""Build human-review figures from results_table.csv, saved finalist draws, and shocksat."""
import os, csv, json
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FIG = os.path.join(HERE, "figures")
os.makedirs(FIG, exist_ok=True)


def load_rows():
    with open(os.path.join(HERE, "results_table.csv")) as f:
        return list(csv.DictReader(f))


def fig_observed():
    import sys; sys.path.insert(0, os.path.join(HERE, "src"))
    from data import load_aligned
    d = load_aligned()
    fig, ax = plt.subplots(1, 2, figsize=(11, 4))
    f = np.concatenate([d["train_f"], d["dev_f"]], 0)
    for j in range(6):
        ax[0].scatter(np.full(f.shape[0], j + 1), f[:, j], s=14, alpha=0.6,
                      color="C0" if j == 0 else "C0")
    ax[0].set_xlabel("mode index"); ax[0].set_ylabel("frequency (Hz)")
    ax[0].set_title("Observed modal frequencies\n(12 realizations: 8 train + 4 dev)")
    ax[0].set_yscale("log"); ax[0].grid(True, alpha=0.3)
    # representative mode shape (mode 1) across realizations at the 8 sensors
    phi = np.concatenate([d["train_phi"], d["dev_phi"]], 0)
    sens = [0, 2, 3, 5, 6, 8, 9, 11]
    for r in range(phi.shape[0]):
        ax[1].plot(sens, phi[r, :, 0], color="C1", alpha=0.35)
    ax[1].plot(sens, d["ref"][:, 0], "k-o", lw=2, label="aligned mean (mode 1)")
    ax[1].set_xlabel("sensor DOF"); ax[1].set_ylabel("mass-norm. shape comp.")
    ax[1].set_title("Observed mode-1 shape, 8 sensors\n(scatter = noise across realizations)")
    ax[1].legend(); ax[1].grid(True, alpha=0.3)
    fig.tight_layout(); fig.savefig(os.path.join(FIG, "01_observed_data.png"), dpi=110)
    plt.close(fig)


def fig_overfit_picture():
    rows = load_rows()
    ramp = [r for r in rows if r["stage"] == "PROBE_adaptive"]
    x = np.arange(1, len(ramp) + 1)
    dev = np.array([float(r["dev_lpd"]) for r in ramp])
    # raw train log pointwise predictive density (lppd) = WAIC_elpd + p_waic (no penalty);
    # this is the pure in-sample fit and climbs cleanly with flexibility.
    train = np.array([float(r["waic_elpd"]) + float(r["p_waic"]) for r in ramp])
    th4 = np.array([float(r["theta4"]) for r in ramp])
    gate = np.array([r["gate_pass"] == "True" for r in ramp])

    fig, ax = plt.subplots(1, 2, figsize=(12, 4.6))
    ax[0].plot(x, train, "-s", color="C3", label="train fit (raw lppd) — climbs")
    ax2 = ax[0].twinx()
    ax2.plot(x, dev, "-o", color="C0", label="held-out dev-LPD — plateaus")
    ax[0].set_xlabel("adaptive query (increasing flexibility ->)")
    ax[0].set_ylabel("train lppd (raw in-sample fit)", color="C3")
    ax2.set_ylabel("dev-LPD", color="C0")
    ax[0].set_title("Modal-fit score: discrepancy earns its keep, then BOTH\n"
                    "train & dev plateau — dev does NOT reveal the later overfit")
    ax[0].grid(True, alpha=0.3)
    l1, la1 = ax[0].get_legend_handles_labels(); l2, la2 = ax2.get_legend_handles_labels()
    ax[0].legend(l1 + l2, la1 + la2, loc="center right", fontsize=8)

    # theta4 drift + gate markers
    ax[1].plot(x, th4, "-", color="0.5")
    ax[1].scatter(x[gate], th4[gate], color="C2", s=60, zorder=5, label="passes convergence gate")
    ax[1].scatter(x[~gate], th4[~gate], color="C3", marker="X", s=80, zorder=5,
                  label="FAILS gate (R-hat/divergence)")
    ax[1].axhspan(0.85, 0.92, color="C2", alpha=0.12)
    ax[1].set_xlabel("adaptive query (increasing flexibility ->)")
    ax[1].set_ylabel(r"posterior mean $\theta_4$ (softest group)")
    ax[1].set_title(r"As flexibility grows, $\theta_4$ drifts —"
                    "\nand exactly those configs FAIL the gate")
    ax[1].legend(fontsize=8); ax[1].grid(True, alpha=0.3)
    fig.tight_layout(); fig.savefig(os.path.join(FIG, "02_overfit_picture.png"), dpi=110)
    plt.close(fig)


def fig_probe_curve():
    with open(os.path.join(HERE, "overfit_probe", "probe_curve.csv")) as f:
        rows = list(csv.DictReader(f))
    q = [int(r["query"]) for r in rows]
    naive = [float(r["best_dev_naive"]) for r in rows]
    thr = [float(r["best_dev_thresholdout"]) for r in rows]
    gate = [r["gate_pass"] == "True" for r in rows]
    fig, ax = plt.subplots(figsize=(7, 4.5))
    ax.plot(q, naive, "-o", color="C3", label="naive best-dev (no self-restraint)")
    ax.plot(q, thr, "-s", color="C0", label="reusable-holdout (Thresholdout) registered")
    for i, g in enumerate(gate):
        if not g:
            ax.scatter(q[i], naive[i], facecolors="none", edgecolors="k", s=140, zorder=6)
    ax.scatter([], [], facecolors="none", edgecolors="k", s=140, label="config FAILS convergence gate")
    ax.set_xlabel("adaptive query index"); ax.set_ylabel("best dev-LPD so far")
    ax.set_title("Garden of forking paths: naive dev-chasing climbs to a\n"
                 "GATE-FAILING config; reusable-holdout + gate hold the line")
    ax.legend(fontsize=8); ax.grid(True, alpha=0.3)
    fig.tight_layout(); fig.savefig(os.path.join(FIG, "03_probe_curve.png"), dpi=110)
    plt.close(fig)


def fig_ablations():
    rows = load_rows()
    fig, ax = plt.subplots(figsize=(9, 4.5))
    labels, devs, colors = [], [], []
    sel = [
        ("none (drop disc.)", lambda r: r["stage"] == "ABL_dropdisc"),
        ("freqshape pw0.1", lambda r: r["stage"] == "ABL_prior" and r["prior_width"] == "0.1"),
        ("freqshape pw0.7", lambda r: r["stage"] == "ABL_prior" and r["prior_width"] == "0.7"),
        ("coarsen 4 modes", lambda r: r["stage"] == "ABL_coarse" and r["nmodes"] == "4"),
        ("coarsen 3 modes", lambda r: r["stage"] == "ABL_coarse" and r["nmodes"] == "3"),
        ("centered", lambda r: r["stage"] == "ABL_param" and r["noncentered"] == "False"),
        ("non-centered", lambda r: r["stage"] == "ABL_param" and r["noncentered"] == "True"),
    ]
    for name, fn in sel:
        m = [r for r in rows if fn(r)]
        if m:
            labels.append(name); devs.append(float(m[0]["dev_lpd"]))
            colors.append("C2" if m[0]["gate_pass"] == "True" else "C3")
    ax.barh(labels, devs, color=colors)
    ax.set_xlabel("dev-LPD (higher = better predictive)")
    ax.set_title("Ablations through the same dev pipeline\n(green=passes gate, red=fails gate)")
    ax.grid(True, axis="x", alpha=0.3)
    fig.tight_layout(); fig.savefig(os.path.join(FIG, "04_ablations.png"), dpi=110)
    plt.close(fig)


def fig_convergence():
    files = sorted([f for f in os.listdir(os.path.join(HERE, "diagnostics")) if f.endswith("_draws.npz")])
    fig, axes = plt.subplots(len(files), 2, figsize=(11, 3.2 * len(files)))
    if len(files) == 1:
        axes = axes[None, :]
    for i, fn in enumerate(files):
        d = np.load(os.path.join(HERE, "diagnostics", fn))
        fid = fn.replace("_draws.npz", "")
        lt = d["log_theta"]  # merged draws (D,4)
        # rank-normalized trace proxy: just plot running draws of theta components
        for k in range(4):
            axes[i, 0].plot(np.exp(lt[:, k]), lw=0.6, alpha=0.8, label=f"theta{k+1}")
        axes[i, 0].set_title(f"{fid}: theta draws"); axes[i, 0].set_xlabel("draw")
        axes[i, 0].legend(fontsize=6, ncol=4)
        # histogram of theta1
        axes[i, 1].hist(np.exp(lt[:, 0]), bins=40, color="C0", alpha=0.7)
        axes[i, 1].set_title(f"{fid}: posterior theta1"); axes[i, 1].set_xlabel("theta1")
    fig.tight_layout(); fig.savefig(os.path.join(FIG, "05_convergence_traces.png"), dpi=110)
    plt.close(fig)


def fig_shocksat():
    with open(os.path.join(HERE, "shocksat_mode_table.csv")) as f:
        rows = list(csv.DictReader(f))
    fh = np.array([float(r["test_hz"]) for r in rows])
    mac = np.array([float(r["MAC"]) for r in rows])
    fe = np.array([abs(float(r["freq_err_rel"])) * 100 for r in rows])
    fig, ax = plt.subplots(1, 2, figsize=(12, 4.4))
    ax[0].semilogx(fh, mac, "o-", color="C0")
    ax[0].axhline(0.9, color="C3", ls="--", label="MAC=0.9")
    ax[0].set_xlabel("test frequency (Hz, log)"); ax[0].set_ylabel("MAC (test vs TAM)")
    ax[0].set_title("ShockSat free-free MAC vs frequency"); ax[0].set_ylim(0, 1.02)
    ax[0].legend(); ax[0].grid(True, alpha=0.3, which="both")
    ax[1].semilogx(fh, fe, "s-", color="C1")
    ax[1].axhline(5, color="C3", ls="--", label="5% error")
    ax[1].set_xlabel("test frequency (Hz, log)"); ax[1].set_ylabel("|freq error| (%)")
    ax[1].set_title("ShockSat |frequency error| vs frequency\n(twin degrades at high f -> pyro OOD)")
    ax[1].legend(); ax[1].grid(True, alpha=0.3, which="both")
    fig.tight_layout(); fig.savefig(os.path.join(FIG, "06_shocksat_correlation.png"), dpi=110)
    plt.close(fig)


def fig_finalist_modes():
    import sys; sys.path.insert(0, os.path.join(HERE, "src"))
    from data import load_aligned
    d = load_aligned()
    obs = np.concatenate([d["train_f"], d["dev_f"]], 0).mean(0)
    with open(os.path.join(HERE, "finalists.json")) as f:
        fj = json.load(f)
    fig, ax = plt.subplots(figsize=(8, 4.5))
    idx = np.arange(1, 7)
    ax.plot(idx, obs, "k-o", lw=2, label="observed (mean)")
    for fin in fj["finalists"]:
        ax.plot(idx, fin["pred_modes_hz"], "--s", alpha=0.8, label=fin["id"])
    ax.set_xlabel("mode index"); ax.set_ylabel("frequency (Hz)")
    ax.set_yscale("log")
    ax.set_title("Finalist predicted modal frequencies vs observed\n"
                 "(no-discrepancy F3 misses; discrepancy finalists match)")
    ax.legend(fontsize=8); ax.grid(True, alpha=0.3, which="both")
    fig.tight_layout(); fig.savefig(os.path.join(FIG, "07_finalist_modes.png"), dpi=110)
    plt.close(fig)


if __name__ == "__main__":
    fig_observed(); fig_overfit_picture(); fig_probe_curve(); fig_ablations()
    fig_convergence(); fig_shocksat(); fig_finalist_modes()
    print("figures written to", FIG)
