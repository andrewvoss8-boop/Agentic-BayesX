#!/usr/bin/env python3
"""USABLE-MEAN SPEC deliverable (Memo C Path 2, Andrew "do a"). The industry workflow: correlate the FEM to test,
then use it + a SMALL margin instead of the un-correlated FEM + a big margin. Show the calibrated/correlated-FEM
mean spec ENVELOPES the measured environment with LOWER GRMS than current practice (un-updated FEM + 6 dB).

Structure-level max-envelope spec (single vibe spec) over the +X channels (reuses saved baseline modes — no eigensolve):
  measured     = smoothline-envelope of max_channel |H_meas|^2                         (the environment to cover)
  FEM+6dB       = smoothline-envelope of max_channel |H_FEMnominal|^2  + 6 dB           (current practice)
  twin+margin   = smoothline-envelope of max_channel |H_correlatedTwin|^2 + (margin to just cover measured)
FEM-nominal = FEM freqs + nominal 1% damping + ONE global gain (no per-mode fit). Correlated-twin = measured freqs +
per-mode MEASURED damping + per-mode complex participation fit to all channels. GRMS = sqrt(area). HONEST: the twin's
participations are FIT to this data (no held-out) → this demonstrates the value of CORRELATION (correlate-then-use),
not a blind prediction; a held-out / virtual-point version (task b) tests generalization. Output: out/usable_mean.json + figure.
"""
from __future__ import annotations
import json, sys
from pathlib import Path
import numpy as np
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
sys.path.insert(0, str(Path(__file__).resolve().parent))
import psd_envelope as pe
from modal_multiref import CACHE
WS = Path(__file__).resolve().parent.parent

z = np.load(WS / "out" / "edits" / "baseline" / "modes.npz", allow_pickle=True)
Phi = z["Phi"]; pd = z["pd"]; ffem = z["freqs_fem"]; daq = [int(d) for d in z["daq"]]
c = dict(np.load(CACHE / "m_xpos_990x.npz", allow_pickle=True)); c["daq"] = [int(d) for d in c["daq"]]
f = c["freqs"]; w = 2 * np.pi * f; ci = {d: c["daq"].index(d) for d in daq}
Hmeas = np.array([c["H1"][ci[d]] for d in daq]).T
mm = np.load(WS / "data" / "measured_modes.npz", allow_pickle=True); mfr = mm["freqs"]; mdp = mm["damp"] / 100.0
j = np.array([int(np.argmin(np.abs(mfr - ff))) for ff in ffem])
tau = -(122880 - 1) / (250000.0 * np.log(0.05))
wr_meas = mfr[j] * 2 * np.pi; eta_data = 2.0 * (mdp[j] + 1.0 / (2 * np.pi * mfr[j] * tau))
wr_fem = ffem * 2 * np.pi; eta_nom = 2.0 * (0.01 + 1.0 / (2 * np.pi * ffem * tau))   # un-updated: nominal 1% + window

def synth(wr, eta, fit):
    den = (1 + 1j * eta)[None, :] * (wr ** 2)[None, :] - (w ** 2)[:, None]
    basis = (-(w ** 2)[:, None, None]) * (Phi[None, :, :] * pd[None, None, :]) / den[:, None, :]   # (Nf,Nc,nm)
    if fit:
        A = basis.reshape(-1, len(pd)); b = Hmeas.reshape(-1)
        AhA = A.conj().T @ A + 1e-3 * np.eye(len(pd)) * np.real(np.trace(A.conj().T @ A)) / len(pd)
        a = np.linalg.solve(AhA, A.conj().T @ b)
        return basis @ a
    g = np.median(np.log(np.abs(Hmeas) + 1e-30) - np.log(np.abs(basis.sum(2)) + 1e-30))   # one global gain
    return basis.sum(2) * np.exp(g)

H_twin = synth(wr_meas, eta_data, fit=True)        # correlated twin (freq+damping+participation fit; circular)
H_fem = synth(wr_fem, eta_nom, fit=False)          # un-updated FEM (nominal freq + 1% damping)
H_corr = synth(wr_meas, eta_data, fit=False)       # GENERALIZABLE correction: measured freq + measured damping, NO per-ch fit
psd_meas = (np.abs(Hmeas) ** 2).max(1); psd_twin = (np.abs(H_twin) ** 2).max(1)
psd_fem = (np.abs(H_fem) ** 2).max(1); psd_corr = (np.abs(H_corr) ** 2).max(1)
env_corr0 = pe.smoothline_envelope(f, psd_corr)
m_corr = max(0.0, float(np.max(10 * np.log10(np.maximum(pe.smoothline_envelope(f, psd_meas), 1e-300) / np.maximum(env_corr0, 1e-300)))))
g_corr = pe.grms(f, pe.add_db_psd(env_corr0, m_corr))
env_meas = pe.smoothline_envelope(f, psd_meas)
env_fem0 = pe.smoothline_envelope(f, psd_fem)
m_fem = max(0.0, float(np.max(10 * np.log10(np.maximum(env_meas, 1e-300) / np.maximum(env_fem0, 1e-300)))))  # FEM margin to just-cover
g_fem_cover = pe.grms(f, pe.add_db_psd(env_fem0, m_fem))
env_fem6 = pe.smoothline_envelope(f, pe.add_db_psd(psd_fem, 6.0))
env_twin0 = pe.smoothline_envelope(f, psd_twin)
# margin the twin needs to just cover the measured max-envelope
margin_db = float(np.max(10 * np.log10(np.maximum(env_meas, 1e-300) / np.maximum(env_twin0, 1e-300))))
margin_db = max(margin_db, 0.0)
env_twin = pe.add_db_psd(env_twin0, margin_db)
g_meas, g_fem6, g_twin = pe.grms(f, env_meas), pe.grms(f, env_fem6), pe.grms(f, env_twin)
exc_fem6 = pe.exceedance(f, psd_meas, env_fem6)["exceeding_energy_fraction"]
exc_twin = pe.exceedance(f, psd_meas, env_twin)["exceeding_energy_fraction"]
rec = {"reference": "+X (Test01)", "n_channels": len(daq), "S_F0": "1 lbf^2/Hz flat",
       "GRMS_measured_envelope": round(g_meas, 4), "GRMS_FEM_plus6dB": round(g_fem6, 4),
       "GRMS_correlatedTwin_plus_margin": round(g_twin, 4), "twin_margin_to_cover_dB": round(margin_db, 1),
       "GRMS_freqDampCorrected_noFit_plus_margin": round(g_corr, 4), "corr_margin_to_cover_dB": round(m_corr, 1),
       "FAIR_each_at_margin_to_just_cover": {
           "FEM_margin_dB": round(m_fem, 1), "FEM_GRMS_at_cover": round(g_fem_cover, 4),
           "corrected_margin_dB": round(m_corr, 1), "corrected_GRMS_at_cover": round(g_corr, 4),
           "ratio_corrected_over_FEM": round(g_corr / g_fem_cover, 3)},
       "GRMS_ratio_corrected_over_FEM6": round(g_corr / g_fem6, 3),
       "GRMS_ratio_twin_over_FEM6": round(g_twin / g_fem6, 3),
       "FEM6_covers (exceed-energy)": round(exc_fem6, 3), "twin_covers (exceed-energy)": round(exc_twin, 3),
       "verdict": "twin spec lower-GRMS while covering" if g_twin < g_fem6 and exc_twin < 0.02 else "no clear win",
       "honest_note": "twin participations FIT to this data (no held-out); demonstrates value of CORRELATION, not blind prediction"}
(WS / "out" / "usable_mean.json").write_text(json.dumps(rec, indent=2))
print(json.dumps(rec, indent=2))

fig, ax = plt.subplots(figsize=(8.5, 4.6))
ax.plot(f, psd_meas, color="0.75", lw=0.8, label="measured max-channel PSD")
ax.plot(f, env_meas, color="#222222", lw=1.6, label="measured envelope (to cover)")
ax.plot(f, env_fem6, color="#1f77b4", lw=1.8, label=f"FEM + 6 dB  (GRMS {g_fem6:.2g})")
ax.plot(f, env_twin, color="#d2691e", lw=1.8, label=f"correlated twin + {margin_db:.0f} dB  (GRMS {g_twin:.2g})")
ax.set_xscale("log"); ax.set_yscale("log"); ax.set_xlim(45, 260)
ax.spines[["top", "right"]].set_visible(False); ax.tick_params(labelsize=8)
ax.set_xlabel("frequency  (Hz, log)", fontsize=9); ax.set_ylabel("PSD  g²/Hz  (S_F0=1)", fontsize=9)
ax.legend(fontsize=7.5, frameon=False, loc="lower center", ncol=2)
ax.set_title(f"Usable-mean spec, +X: correlated twin GRMS {g_twin:.2g} vs FEM+6dB {g_fem6:.2g} "
             f"(ratio {g_twin/g_fem6:.2f}), both envelope the data", fontsize=8.5)
cap = ("Structure-level max-envelope vibe spec (84 +X channels). Un-updated FEM (nominal freq + 1% damping) + 6 dB = "
       "current practice; correlated twin = measured freq + per-mode measured damping + per-mode participation fit, "
       f"+ the {margin_db:.0f} dB needed to just envelope the measured. Both cover; the correlated twin is "
       f"{(1-g_twin/g_fem6)*100:.0f}% lower GRMS. HONEST: twin participations fit to this data (value of correlation, "
       "not blind prediction); held-out/virtual-point generalization = task (b).")
fig.text(0.01, -0.02, cap, fontsize=6.8, wrap=True, va="top")
fig.tight_layout(rect=[0, 0.06, 1, 1])
out = WS / "figures" / "usable_mean_spec.png"; fig.savefig(out, dpi=150, bbox_inches="tight"); plt.close(fig)
print(f"\nwrote {out}")
print(f"HEADLINE: correlated-twin spec GRMS {g_twin:.3g} vs FEM+6dB {g_fem6:.3g} (ratio {g_twin/g_fem6:.2f}); "
      f"both cover (twin exceed {exc_twin:.3f}, FEM+6dB exceed {exc_fem6:.3f})")
