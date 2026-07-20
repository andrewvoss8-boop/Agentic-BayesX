#!/usr/bin/env python3
"""Real-data layer for Card A: REAL matched-path FRF observable on the plain 9-group ShockSat FEM.

Decisions D2-D4 (decisions_log.md). Plain-ShockSat ONLY. Reuses (imports, never edits) the copied
`core.py`/`nuts_arms.py` for the Schneider freq x space correlation + QOI helpers.

Pipeline:
  - reduced model  K(theta) = A_fix + sum_g theta_g A_g   (74x74, mass = I), from reduced_blocks.npz (COPY).
  - place ANY physical FEM DOF in the 74-dim basis:  reduced_row(dof) = V_keep[keeprow(dof), :80] @ T,
    T = lstsq(V_keep[obs_dofs,:80], obs_V)  (reconstructs obs_V to 1e-14, generalises to held-out, P1.5).
  - drive d = nearest kept FEM node to the impact point (9,8,1) in, X axis (D3).
  - response channels s = nearest kept FEM node to each tap_impact DAQ-channel coord, on its axis (D3).
  - FEM matched-path accelerance  H_sd = -w^2 sum_k U_s[k] U_d[k] / ((1+i eta) lam_k - w^2)  -> g/lbf
    via /386.0886, then + a GLOBAL units-gain (handled in the likelihood, D4; ~x100 mass-norm/g constant).
  - measured truth = single-impact FRF of hit-001 (force window on the pulse + exponential response window,
    single FFT), per accel recorder, cached.
  - single-hit data-quality weight  w(f) = S(f)/(S(f)+N0)  (response power vs pre-impact baseline-noise floor),
    the 1-hit substitute for ordinary (multi-average) coherence (D2, YELLOW).

Units: xyz in inches; accelerance in g/lbf. Likelihood grid = native measured df in band (45-260 Hz).
"""
from __future__ import annotations

import csv
import json
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np

import core  # reused (copied, unedited): corr helpers, qoi_peak/qoi_band

WS = Path(__file__).resolve().parent.parent
DATA = WS / "data"
SYN_DATA = WS.parent / "statfem_shocksat_eval_20260616" / "data"      # V_keep.npy referenced read-only
RUN = WS.parent / "shocksat_statfem_runner_20260609"
MAT = RUN / "extracted/Test07_ImpactHammer_990x/Test07_impacthammer_990x_001_5_20_2021_2_32_37 PM.mat"

GNAMES = core.GNAMES
G_IN_S2 = 386.0886
ZETA_NOM = 0.01
BAND = (45.0, 260.0)
AX = {"X": 0, "Y": 1, "Z": 2}
IMPACT_XYZ = (9.0, 8.0, 1.0)
IMPACT_AXIS = "X"
FS = 250000.0
# measured single-impact processing (D4); exp window end-value sets the added damping zeta_w(f)
PROC = {"N": 200000, "force_ms": 2.0, "exp_end": 0.05, "pre_gap": 200, "baseline_N": 60000}
FORCE_RECORDER = 116
N_ACCEL_RECORDERS = 115     # Recorder 1..115 = accels (g); 116 = force (lb); Recorder_k <-> DAQ channel k
# TestLog-flagged bad data (ShockSat1_Instrumentation_and_TestLog xlsx): ch101 "bad at installation...all tests";
# ch29-31 "contains 60 Hz noise...all tests" (inside our 45-260 Hz band). Excluded from all observed/held-out sets.
BAD_DAQ = {29, 30, 31, 101}


# ------------------------------------------------------------------ reduced model + DOF placement
@dataclass
class Reduced:
    A_fix: np.ndarray
    A: np.ndarray
    T: np.ndarray
    vk: np.ndarray
    keeprow: dict
    xyz: np.ndarray

    def reduced_row(self, point_xyz, axis):
        nn = int(np.argmin(np.linalg.norm(self.xyz - np.asarray(point_xyz, float), axis=1)))
        dof = 6 * nn + AX[axis]
        if dof not in self.keeprow:
            # fall back to nearest kept dof on same axis among a few nearest nodes
            order = np.argsort(np.linalg.norm(self.xyz - np.asarray(point_xyz, float), axis=1))[:20]
            for n2 in order:
                d2 = 6 * int(n2) + AX[axis]
                if d2 in self.keeprow:
                    nn, dof = int(n2), d2
                    break
            else:
                raise KeyError(f"no kept DOF near {point_xyz} axis {axis}")
        return np.asarray(self.vk[self.keeprow[dof], :80]) @ self.T, nn, float(
            np.linalg.norm(self.xyz[nn] - np.asarray(point_xyz, float)))


def load_reduced() -> Reduced:
    rb = np.load(DATA / "reduced_blocks.npz", allow_pickle=True)
    assert [str(g) for g in rb["gnames"]] == GNAMES
    obs_V = rb["obs_V"]
    obs_dofs = np.load(DATA / "obs_dofs.npy")
    keep = np.load(DATA / "keep_dofs.npy")
    vk = np.load(SYN_DATA / "V_keep.npy", mmap_mode="r")
    T, *_ = np.linalg.lstsq(np.asarray(vk[obs_dofs, :80]), obs_V, rcond=None)
    fm = np.load(WS.parent / "shocksat_fem_modal_twin_20260609" / "fem_model.npz", allow_pickle=True)
    keeprow = {int(d): i for i, d in enumerate(keep)}
    return Reduced(A_fix=rb["A_fix"], A=rb["A"], T=np.asarray(T), vk=vk, keeprow=keeprow, xyz=fm["xyz"])


# ------------------------------------------------------------------ channel geometry (drive + responses)
@dataclass
class Channels:
    daq: list
    coords: np.ndarray                 # (Nc,3)
    axes: list
    rows: np.ndarray                   # (Nc,74) reduced response rows
    nodes: list
    snap_in: list                      # nearest-node snap distance [in]
    drive_row: np.ndarray              # (74,)
    drive_node: int
    drive_xyz: tuple = field(default=IMPACT_XYZ)


def build_channels(R: Reduced, daqs):
    rows_map = {r["daq_channel"]: r for r in csv.DictReader(open(DATA / "channel_map.csv"))
                if r["configuration"] == "tap_impact"}
    drive_row, drive_node, _ = R.reduced_row(IMPACT_XYZ, IMPACT_AXIS)
    daq_ok, coords, axes, rows, nodes, snaps = [], [], [], [], [], []
    for d in daqs:
        if int(d) in BAD_DAQ:                      # TestLog-flagged bad sensors (ch101 install; ch29-31 60 Hz)
            continue
        r = rows_map.get(str(d))
        if r is None or r["structural_axis"] not in AX:
            continue
        c = (float(r["x_in"]), float(r["y_in"]), float(r["z_in"]))
        try:
            row, nn, snap = R.reduced_row(c, r["structural_axis"])
        except KeyError:
            continue
        daq_ok.append(int(d)); coords.append(c); axes.append(r["structural_axis"])
        rows.append(row); nodes.append(nn); snaps.append(snap)
    return Channels(daq=daq_ok, coords=np.array(coords), axes=axes, rows=np.array(rows),
                    nodes=nodes, snap_in=snaps, drive_row=drive_row, drive_node=drive_node)


# ------------------------------------------------------------------ FEM matched-path forward (g/lbf)
def fem_logmag(R: Reduced, freqs, theta, resp_rows, drive_row, zeta=ZETA_NOM):
    """log|accelerance g/lbf| (Nf, Nc) (numpy, post-processing). Global gain handled in likelihood."""
    K = R.A_fix + np.einsum("g,gij->ij", np.asarray(theta), R.A)
    lam, Q = np.linalg.eigh(K)
    lam = np.clip(lam, 1e-9, None)
    eta = 2.0 * float(zeta)
    Us = resp_rows @ Q                                   # (Nc, r)
    Ud = drive_row @ Q                                   # (r,)
    w = 2 * np.pi * np.asarray(freqs)
    g = (1 + 1j * eta) * lam[None, :] - (w ** 2)[:, None]    # (Nf, r)
    H = -(w ** 2)[:, None] * np.einsum("sk,k,fk->fs", (Us).astype(complex),
                                       Ud.astype(complex), 1.0 / g)
    return np.log(np.abs(H) / G_IN_S2)


def fem_logmag_batch(R: Reduced, freqs, theta_batch, resp_rows, drive_row, zeta=ZETA_NOM, chunk=200):
    """Batched log|accelerance g/lbf|: theta_batch (M,9) -> (M, Nf, Ns). One LAPACK eigh over the population
    (chunked for memory) -> ~10-20x faster than a per-sample Python loop. Used by the TMCMC likelihood."""
    theta_batch = np.atleast_2d(theta_batch)
    M = theta_batch.shape[0]
    w = 2 * np.pi * np.asarray(freqs); eta = 2.0 * float(zeta)
    Nf = len(freqs); Ns = resp_rows.shape[0]
    out = np.empty((M, Nf, Ns))
    for s0 in range(0, M, chunk):
        th = theta_batch[s0:s0 + chunk]                                  # (c,9)
        K = R.A_fix[None] + np.einsum("cg,gij->cij", th, R.A)            # (c,r,r)
        lam, Q = np.linalg.eigh(K)
        lam = np.clip(lam, 1e-9, None)
        Us = np.einsum("sm,cmk->csk", resp_rows, Q)                      # (c,Ns,r)
        ud = np.einsum("m,cmk->ck", drive_row, Q)                        # (c,r)
        g = (1.0 + 1j * eta) * lam[:, None, :] - (w ** 2)[None, :, None] # (c,Nf,r)
        H = -(w ** 2)[None, :, None] * np.einsum("csk,ck,cfk->cfs",
                                                 Us.astype(complex), ud.astype(complex), 1.0 / g)
        out[s0:s0 + chunk] = np.log(np.abs(H) / G_IN_S2)
    return out


def jax_fem_logmag_factory(R: Reduced, freqs, resp_rows, drive_row, zeta=ZETA_NOM):
    """jax log|accelerance g/lbf|(theta) -> (Nf, Nc); eigh-resolvent, degenerate contribs cancel (D10)."""
    import jax.numpy as jnp
    A = jnp.asarray(R.A); A_fix = jnp.asarray(R.A_fix)
    Rr = jnp.asarray(resp_rows); Dr = jnp.asarray(drive_row)
    w = jnp.asarray(2 * np.pi * np.asarray(freqs)); eta = 2.0 * float(zeta)
    logg = float(np.log(G_IN_S2))

    def logmag(theta):
        K = A_fix + jnp.einsum("g,gij->ij", theta, A)
        lam, Q = jnp.linalg.eigh(K)
        lam = jnp.clip(lam, 1e-9, None)
        Us = Rr @ Q
        Ud = Dr @ Q
        g = (1 + 1j * eta) * lam[None, :] - (w ** 2)[:, None]
        H = -(w ** 2)[:, None] * jnp.einsum("sk,k,fk->fs", Us.astype(jnp.complex128),
                                            Ud.astype(jnp.complex128), 1.0 / g)
        return jnp.log(jnp.abs(H)) - logg

    return logmag


# ------------------------------------------------------------------ measured single-impact FRF (cached)
def _exp_window(N, end):
    return np.exp(np.log(end) * np.arange(N) / (N - 1))


def measured_zeta_w(freqs):
    """Added damping from the exponential window: tau = -(N-1)/(fs*ln(end)); zeta_w(f)=1/(2 pi f tau)."""
    tau = -(PROC["N"] - 1) / (FS * np.log(PROC["exp_end"]))
    return 1.0 / (2 * np.pi * np.asarray(freqs) * tau)


def reprocess_measured(daqs, force=False):
    """Single-impact FRF + quality weight for accel DAQ channels, cached to data/measured_frf_cache.npz.
    Returns dict: freqs(native), H(complex (Nc,Nf)), weight(0-1 (Nc,Nf)), daq(list), snr_band(list)."""
    cache = DATA / "measured_frf_cache.npz"
    if cache.exists() and not force:
        z = np.load(cache, allow_pickle=True)
        d = {k: z[k] for k in z.files}
        d["daq"] = list(d["daq"])
        return d
    import scipy.io as sio
    want = [f"Recorder{FORCE_RECORDER}"] + [f"Recorder{d}" for d in daqs]
    M = sio.loadmat(str(MAT), variable_names=want, struct_as_record=False, squeeze_me=True)

    def samp(r):
        return np.asarray(M[f"Recorder{r}"].Channels.Segments.Data.Samples, float)

    F = samp(FORCE_RECORDER)
    ip = int(np.argmax(np.abs(F)))
    N = PROC["N"]; start = max(0, ip - PROC["pre_gap"]); sl = slice(start, start + N)
    pk = ip - start; half = int(PROC["force_ms"] * 1e-3 * FS)
    fwin = np.zeros(N); fwin[max(0, pk - half):pk + half] = 1.0
    ewin = _exp_window(N, PROC["exp_end"])
    freqs = np.fft.rfftfreq(N, 1 / FS)
    Ff = np.fft.rfft(F[sl] * fwin)
    bmask = (freqs >= BAND[0]) & (freqs <= BAND[1])
    # FORCE-present weight: hammer spectrum rolls off above its tip bandwidth; down-weight where |Ff|^2 weak.
    SF = np.abs(Ff) ** 2
    floor_F = np.median(SF[freqs > 8000.0]) if (freqs > 8000.0).any() else np.percentile(SF, 5)
    wF = SF / (SF + 5.0 * floor_F + 1e-30)
    # Single-hit, baseline-free quality weight (D5): response power above the within-band inter-peak floor,
    # times force-present. The 1-hit substitute for ordinary (multi-average) coherence (YELLOW).
    Hs, Ws, snr_band, dynrange, ok = [], [], [], [], []
    for d in daqs:
        y = samp(d)
        Y = np.fft.rfft(y[sl] * ewin)
        H = Y / Ff
        S = np.abs(Y) ** 2
        floor_Y = np.percentile(S[bmask], 25)        # inter-peak / noise level for THIS channel, in band
        wY = S / (S + floor_Y + 1e-30)
        Wq = wY * wF
        Hs.append(H); Ws.append(Wq)
        snr_band.append(float(np.median((S / (floor_Y + 1e-30))[bmask])))
        dynrange.append(float(S[bmask].max() / (floor_Y + 1e-30)))
        ok.append(int(d))
    out = {"freqs": freqs, "H": np.array(Hs), "weight": np.array(Ws), "daq": ok,
           "snr_band": np.array(snr_band), "dyn_range": np.array(dynrange), "proc": json.dumps(PROC)}
    np.savez_compressed(cache, **out)
    out["daq"] = ok
    return out


if __name__ == "__main__":
    R = load_reduced()
    daqs = list(range(1, N_ACCEL_RECORDERS + 1))
    print("reprocessing measured FRFs (loads 256MB .mat once)...")
    meas = reprocess_measured(daqs)
    ch = build_channels(R, meas["daq"])
    fb = (meas["freqs"] >= BAND[0]) & (meas["freqs"] <= BAND[1])
    print(f"channels mapped: {len(ch.daq)} ; band points: {fb.sum()} (df={meas['freqs'][1]-meas['freqs'][0]:.2f} Hz)")
    print(f"drive node {ch.drive_node} ; snap dist max {max(ch.snap_in):.2f} in")
    dr = meas["dyn_range"]
    print(f"in-band dynamic range (peak/floor): median {np.median(dr):.0f}x, "
          f"n with DR>20: {(dr>20).sum()}, >50: {(dr>50).sum()}, >100: {(dr>100).sum()}")
    zw = measured_zeta_w(np.array([60, 120, 240]))
    print(f"window-added damping zeta_w at 60/120/240 Hz: {np.round(zw,4)}")
