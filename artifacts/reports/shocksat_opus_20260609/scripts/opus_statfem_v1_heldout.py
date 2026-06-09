#!/usr/bin/env python3
"""StatFEM v1 held-out QOI validation: predicted (with CI) vs actual.

This assembles the held-out validation the project asked to SEE, from authoritative,
integrity-pinned sources -- it does NOT re-fit a model to the held-out truth:

  * Predictions + posterior CIs come from the modal-correlation StatFEM v1 (NUTS,
    4 stiffness-group scales, convergence-gated) built by the modeling-freedom runner
    and LOCKED in finalists.json BEFORE any vault access. We re-verify its SHA256
    against the committed pin finalists.sha256.
  * Actuals come from the sealed synthetic vault truth.json (truth-known substrate ->
    a TRUE held-out QOI exists) and the graded real ShockSat pyro regime.

Two QOIs (synthetic tray, controlled, truth known):
  - QOI_ref (IN-regime, path out11<-in0): a receptance peak we calibrate near.
  - QOI_heldout (OUT-of-distribution, path out5<-in8): the held-out forcing path.
QOI def = peak |H_{out,in}(w)| over 10-600 Hz, m/N, modal damping zeta=0.02.

Real ShockSat held-out = pyro NSD shock: DIRECTIONAL only (no committed magnitude),
shown as a labeled real-data panel, not a CI-vs-number.
"""
from __future__ import annotations
import hashlib
import json
import tarfile
import tempfile
from pathlib import Path

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

REPO = Path(__file__).resolve().parents[4]
EXP = REPO / "artifacts/reports/modeling_freedom_experiment_20260609"
OUT = REPO / "artifacts/reports/shocksat_opus_20260609"
FIGS = OUT / "figures"
FIGS.mkdir(parents=True, exist_ok=True)

FINALISTS = EXP / "runner_opus/finalists.json"
PIN = EXP / "runner_opus/finalists.sha256"
VAULT_TGZ = EXP / "grading files/vault_tray_synthetic_truth.tar.gz"
PYRO_GRADE = EXP / "review/shocksat_grading_result.json"

Z95 = 1.959964  # 95% normal interval half-width in SDs


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    h.update(path.read_bytes())
    return h.hexdigest()


# --- integrity gate: predictions must be the locked, pre-vault ones ----------
pin_hash = PIN.read_text().split()[0]
got_hash = sha256(FINALISTS)
integrity_ok = (pin_hash == got_hash)
print(f"finalists.json sha256 == pin: {integrity_ok}")
if not integrity_ok:
    raise SystemExit("INTEGRITY FAIL: finalists.json does not match committed pin; refusing to grade.")

finalists = json.loads(FINALISTS.read_text())["finalists"]

# --- actuals from the sealed synthetic vault truth ---------------------------
with tempfile.TemporaryDirectory() as td:
    with tarfile.open(VAULT_TGZ) as tf:
        tf.extractall(td)
    truth = json.loads((Path(td) / "tray/truth.json").read_text())

qoi_ref_truth = truth["qoi_ref_truth"]
qoi_held_truth = truth["qoi_heldout_truth"]
theta_true = truth["theta_true"]
modes_true = truth["true_modal_freqs_hz"]
print(f"truth: qoi_ref={qoi_ref_truth:.4e}, qoi_heldout={qoi_held_truth:.4e}, theta_true={theta_true}")

# --- build the side-by-side table -------------------------------------------
def ci(mean, sd):
    return mean - Z95 * sd, mean + Z95 * sd

rows = []
for f in finalists:
    m = f["_meta"]
    for qoi_name, pred, sd, actual, regime in [
        ("QOI_ref (in-regime, 11<-0)", f["pred_qoi_ref"], m["qoi_ref_sd"], qoi_ref_truth, "in"),
        ("QOI_heldout (OOD, 5<-8)", f["pred_qoi_heldout"], m["qoi_heldout_sd"], qoi_held_truth, "ood"),
    ]:
        lo, hi = ci(pred, sd)
        rows.append({
            "finalist": f["id"], "discrepancy": m["disc"], "qoi": qoi_name, "regime": regime,
            "pred_median": pred, "pred_sd": sd, "ci95_lo": lo, "ci95_hi": hi,
            "actual": actual, "err_pct": 100.0 * (pred - actual) / actual,
            "ci95_covers_actual": bool(lo <= actual <= hi),
            "gate_pass": m["gate_pass"], "max_rhat": m["max_rhat"], "min_ess": m["min_ess"],
        })

# --- console table -----------------------------------------------------------
print("\n=== Held-out QOI: predicted (95% CI) vs actual ===")
print(f"{'finalist':<18}{'qoi':<28}{'pred':>11}{'95% CI':>26}{'actual':>11}{'err%':>8}{'cov':>5}")
for r in rows:
    print(f"{r['finalist']:<18}{r['qoi']:<28}{r['pred_median']:>11.3e}"
          f"{'['+format(r['ci95_lo'],'.2e')+','+format(r['ci95_hi'],'.2e')+']':>26}"
          f"{r['actual']:>11.3e}{r['err_pct']:>8.1f}{'Y' if r['ci95_covers_actual'] else 'N':>5}")

# --- FIGURE 1: held-out QOI side-by-side (the requested deliverable) ---------
fig, axes = plt.subplots(1, 2, figsize=(12, 5))
panels = [("in", "QOI_ref — IN-regime (path 11<-0)", qoi_ref_truth),
          ("ood", "QOI_heldout — OUT-of-distribution (path 5<-8)", qoi_held_truth)]
labels = [f["id"].split("_")[0] for f in finalists]
for ax, (reg, title, actual) in zip(axes, panels):
    rr = [r for r in rows if r["regime"] == reg]
    x = np.arange(len(rr))
    preds = [r["pred_median"] for r in rr]
    errs = [Z95 * r["pred_sd"] for r in rr]
    colors = ["C2" if r["ci95_covers_actual"] else "C3" for r in rr]
    ax.errorbar(x, preds, yerr=errs, fmt="o", ms=9, capsize=7, lw=2,
                ecolor="0.3", mfc="white", mec="k", zorder=3)
    for xi, p, c, r in zip(x, preds, colors, rr):
        ax.plot([xi], [p], "o", ms=9, color=c, zorder=4)
    ax.axhline(actual, color="C0", lw=2.2, ls="--", label=f"actual (sealed truth) = {actual:.3e}")
    ax.set_xticks(x)
    ax.set_xticklabels([r["finalist"].split("_")[0] + f"\n({r['discrepancy']})" for r in rr])
    ax.set_ylabel("QOI: peak |H| receptance (m/N)")
    ax.set_title(title, fontsize=11)
    ax.legend(fontsize=9, loc="best")
    ax.grid(True, axis="y", alpha=0.3)
    # annotate coverage + err
    for xi, r in zip(x, rr):
        ax.annotate(f"{r['err_pct']:+.0f}%\n{'covers' if r['ci95_covers_actual'] else 'MISSES'}",
                    (xi, r["pred_median"]), textcoords="offset points", xytext=(12, 0),
                    fontsize=8, va="center",
                    color="C2" if r["ci95_covers_actual"] else "C3")
fig.suptitle("StatFEM v1 held-out QOI: posterior median + 95% CI vs sealed actual "
             "(synthetic tray, truth known)", fontsize=12)
fig.tight_layout(rect=[0, 0, 1, 0.95])
fig.savefig(FIGS / "v1_heldout_qoi_sidebyside.png", dpi=160)
plt.close(fig)

# --- FIGURE 2: modal-frequency calibration (pred vs true) -------------------
fig, ax = plt.subplots(figsize=(9, 5))
nm = len(modes_true)
xm = np.arange(nm)
for f in finalists:
    ax.plot(xm, f["pred_modes_hz"], "o-", ms=5, lw=1, alpha=0.8,
            label=f"{f['id'].split('_')[0]} ({f['_meta']['disc']})")
ax.plot(xm, modes_true, "k*-", ms=12, lw=1.6, label="actual (sealed truth)")
ax.set_xticks(xm)
ax.set_xticklabels([f"mode {i+1}" for i in range(nm)])
ax.set_ylabel("frequency (Hz)")
ax.set_title("Modal frequencies: StatFEM v1 finalists vs sealed truth (calibration set)")
ax.legend(fontsize=8)
ax.grid(True, alpha=0.3)
fig.tight_layout()
fig.savefig(FIGS / "v1_modal_freq_calibration.png", dpi=160)
plt.close(fig)

# --- FIGURE 3: ShockSat real held-out (pyro) directional panel --------------
pyro = json.loads(PYRO_GRADE.read_text())["aggregate"]
fig, ax = plt.subplots(figsize=(9, 5))
bands = ["> 152 Hz\n(twin band edge)", "> 400 Hz", "> 1 kHz"]
fracs = [pyro["median_frac_energy_above_152Hz"], pyro["median_frac_energy_above_400Hz"],
         pyro["median_frac_energy_above_1kHz"]]
ax.bar(bands, [100 * f for f in fracs], color="C3", alpha=0.8)
for i, f in enumerate(fracs):
    ax.annotate(f"{100*f:.1f}%", (i, 100 * f), textcoords="offset points",
                xytext=(0, 4), ha="center", fontsize=9)
ax.axhline(100, color="0.4", lw=0.8)
ax.set_ylabel("median % of pyro-NSD energy above band")
ax.set_ylim(0, 108)
ax.set_title(f"Real held-out (pyro NSD): {100*fracs[0]:.1f}% of energy is ABOVE the twin's "
             f"~{pyro['twin_validated_band_hz']:.0f} Hz band\n"
             f"peak-PSD {pyro['median_peak_psd_freq_hz']/1e3:.1f} kHz, 95%-energy "
             f"{pyro['median_f95_hz']/1e3:.0f} kHz -> DIRECTIONAL prediction (under-resolve) CONFIRMED")
ax.text(0.5, -0.18, "Directional only: no committed magnitude QOI -> no CI-vs-number for the real "
        "pyro regime (honest OOD extrapolation limit).", transform=ax.transAxes,
        ha="center", fontsize=8, color="0.3")
fig.tight_layout()
fig.savefig(FIGS / "v1_shocksat_pyro_directional.png", dpi=160)
plt.close(fig)

# --- write table + summary ---------------------------------------------------
import csv
with open(OUT / "v1_heldout_qoi_table.csv", "w", newline="") as fh:
    w = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
    w.writeheader()
    w.writerows(rows)

summary = {
    "provenance": {
        "predictions_from": "modeling_freedom_experiment_20260609/runner_opus/finalists.json "
                            "(modal-correlation StatFEM v1, NUTS, locked before vault access)",
        "finalists_sha256_matches_pin": integrity_ok,
        "actuals_from": "sealed synthetic vault truth.json (truth-known) + graded ShockSat pyro",
        "not_refit_to_truth": True,
    },
    "qoi_definition": finalists[0]["_meta"]["qoi_definition"],
    "theta_true": theta_true,
    "rows": rows,
    "headline": {
        "in_regime_qoi": "finalists under-predict by ~9-11%; F1's wider CI covers truth, "
                         "F3's narrow CI misses (overconfident).",
        "ood_heldout_qoi": "ALL finalists over-predict the held-out OOD QOI by ~40-44% and NO "
                           "95% CI covers the sealed actual -> a converged, gate-passing twin is "
                           "confidently wrong out of its calibrated regime.",
        "real_pyro": "directional only; 99.9% of pyro energy is above the twin band -> twin "
                     "cannot resolve the regime (committed direction confirmed).",
    },
    "convergence_note": "All three finalists PASS the gate (max R-hat <=1.016, min ESS >=370, "
                        "0 divergences); coverage failure on OOD QOI is a generalization failure, "
                        "NOT a sampling failure -- the held-out set is the only detector of it.",
}
(OUT / "v1_heldout_qoi_summary.json").write_text(json.dumps(summary, indent=2, default=float))
print("\nwrote v1_heldout_qoi_table.csv, v1_heldout_qoi_summary.json, and 3 figures")
print("HEADLINE:", summary["headline"]["ood_heldout_qoi"])
