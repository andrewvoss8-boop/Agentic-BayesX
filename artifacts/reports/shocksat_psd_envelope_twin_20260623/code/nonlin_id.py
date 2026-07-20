#!/usr/bin/env python3
"""Identify cable/joint NONLINEARITY masquerading as damping (Andrew). For a LINEAR structure the force-normalized
FRF H1=Y/F is force-INDEPENDENT. The 6 modal-hammer hits span a wide force range (~500-1080 lbf), so:
  - if the resonance FREQUENCY drops with hit force  -> softening nonlinearity (cable/joint slip),
  - if the peak-to-floor DYNAMIC RANGE drops with force (peaks broaden) -> apparent damping RISES with amplitude
    = amplitude-dependent (nonlinear) damping, NOT a structural property.
Both are roving-robust-ish (frequency + per-mode DR are level-normalized, so the roving φ_d level cancels).

Per reference, per hit i: windowed single-FFT H_i (channel-median |H| to denoise), per consensus mode r extract
sub-bin resonance freq f_{r,i} (parabolic) and DR_{r,i}=peak/local-floor; regress {f, ln DR} vs ln(force_i).
Negative df/dF and negative dDR/dF (=> ζ rises with amplitude) = the nonlinearity signature. Output: out/nonlin_id.json.
"""
from __future__ import annotations
import json, sys
from pathlib import Path
import numpy as np
from scipy.signal import find_peaks
sys.path.insert(0, str(Path(__file__).resolve().parent))

FS = 250000.0; N = 122880; pre_gap = 200; half = int(2e-3 * FS); BAND = (45., 260.)
BAD = {29, 30, 31, 101}; DAQS = [d for d in range(1, 116) if d not in BAD]
EXTR = Path(__file__).resolve().parent.parent.parent / "shocksat_multiref_explore_20260623" / "data" / "extracted"
REFS = {"Test04_+XY": "Test04_ModalHammer_990xy", "Test02_+Z": "Test02_ModalHammer_990z",
        "Test01_+X": "Test01_ModalHammer_990x"}
EW = np.exp(np.log(0.05) * np.arange(N) / (N - 1))
FR = np.fft.rfftfreq(N, 1 / FS); BM = (FR >= BAND[0]) & (FR <= BAND[1]); FB = FR[BM]


def per_hit(folder):
    import scipy.io as sio
    out = []
    for fp in sorted((EXTR / folder).glob("*.mat")):
        M = sio.loadmat(str(fp), variable_names=["Recorder116"] + [f"Recorder{d}" for d in DAQS],
                        struct_as_record=False, squeeze_me=True)
        F = np.asarray(M["Recorder116"].Channels.Segments.Data.Samples, float)
        ip = int(np.argmax(np.abs(F))); st = max(0, ip - pre_gap)
        if st + N > len(F): continue
        sl = slice(st, st + N); pk = ip - st
        fw = np.zeros(N); fw[max(0, pk - half):pk + half] = 1.0
        Ff = np.fft.rfft(F[sl] * fw)
        Y = np.array([np.asarray(M[f"Recorder{d}"].Channels.Segments.Data.Samples, float) for d in DAQS])
        Yf = np.fft.rfft(Y[:, sl] * EW, axis=1)
        H = np.abs(Yf[:, BM] / Ff[BM][None, :])
        out.append({"force": float(np.max(np.abs(F))), "Hmed": np.median(H, axis=0)})
    return out


def subbin_peak(mag, i):
    if 0 < i < len(mag) - 1:
        y0, y1, y2 = np.log(mag[i-1]+1e-30), np.log(mag[i]+1e-30), np.log(mag[i+1]+1e-30)
        d = (y0 - y2) / (2 * (y0 - 2*y1 + y2) + 1e-30)
        return FB[i] + d * (FB[1] - FB[0])
    return FB[i]


def analyze(folder):
    hits = per_hit(folder)
    if len(hits) < 4:
        return None
    ens = np.median(np.array([h["Hmed"] for h in hits]), axis=0)
    pk, _ = find_peaks(np.log(ens + 1e-30), prominence=0.3, distance=max(1, int(3.0/(FB[1]-FB[0]))))
    forces = np.array([h["force"] for h in hits]); lnF = np.log(forces)
    modes = []
    for i in pk:
        lo, hi = max(0, i-4), min(len(FB), i+5)
        frq, dr = [], []
        for h in hits:
            j = lo + int(np.argmax(h["Hmed"][lo:hi]))
            frq.append(subbin_peak(h["Hmed"], j))
            floor = np.percentile(h["Hmed"][max(0,i-12):i+13], 25)
            dr.append(20*np.log10(h["Hmed"][j] / (floor + 1e-30)))
        frq = np.array(frq); dr = np.array(dr)
        # slopes vs ln force
        df_dlnF = np.polyfit(lnF, frq, 1)[0]                 # Hz per e-fold force (softening if <0)
        ddr_dlnF = np.polyfit(lnF, dr, 1)[0]                 # dB per e-fold (peaks broaden / more damping if <0)
        modes.append({"f_hz": round(float(np.mean(frq)), 1),
                      "freq_shift_pct_over_range": round(float((frq.max()-frq.min())/np.mean(frq)*100), 2),
                      "df_dlnForce_hz": round(float(df_dlnF), 2),
                      "DR_dB": round(float(np.mean(dr)), 1),
                      "dDR_dlnForce_dB": round(float(ddr_dlnF), 2),
                      "corr_f_vs_force": round(float(np.corrcoef(lnF, frq)[0,1]), 2),
                      "corr_DR_vs_force": round(float(np.corrcoef(lnF, dr)[0,1]), 2)})
    return {"folder": folder, "n_hits": len(hits), "force_range_lbf": [round(forces.min()), round(forces.max())],
            "modes": modes}


def main():
    res = {}
    for label, folder in REFS.items():
        r = analyze(folder)
        if r is None:
            print(f"{label}: insufficient hits"); continue
        res[label] = r
        soft = [m for m in r["modes"] if m["df_dlnForce_hz"] < 0 and m["corr_f_vs_force"] < -0.5]
        damp = [m for m in r["modes"] if m["dDR_dlnForce_dB"] < 0 and m["corr_DR_vs_force"] < -0.5]
        print(f"{label} (force {r['force_range_lbf']} lbf, {r['n_hits']} hits, {len(r['modes'])} modes):")
        print(f"  SOFTENING modes (freq drops w/ force, corr<-0.5): {len(soft)}/{len(r['modes'])}")
        print(f"  apparent-DAMPING-rises modes (DR drops w/ force, corr<-0.5): {len(damp)}/{len(r['modes'])}")
        med_df = np.median([m['df_dlnForce_hz'] for m in r['modes']])
        med_ddr = np.median([m['dDR_dlnForce_dB'] for m in r['modes']])
        print(f"  median df/dlnF = {med_df:+.2f} Hz/efold; median dDR/dlnF = {med_ddr:+.2f} dB/efold "
              f"(negative dDR => damping rises with amplitude = nonlinearity)")
    (Path(__file__).resolve().parent.parent / "out" / "nonlin_id.json").write_text(json.dumps(res, indent=2))
    print("wrote out/nonlin_id.json")


if __name__ == "__main__":
    main()
