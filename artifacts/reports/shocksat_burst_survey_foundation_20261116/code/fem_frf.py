#!/usr/bin/env python3
"""Accelerance FRFs of the project's nominal ShockSat FEM at the 76 modal-survey
accelerometer nodes, by modal superposition.

    H_rd(f) = sum_m phi_rm phi_dm (-w^2) / (w_m^2 - w^2 + 2 i zeta_m w_m w) / 386.1   [g/lbf]

phi: mass-normalised mode shapes at the sensor rows (obs_V, 228 rows = 76 nodes x X,Y,Z,
inch / sqrt(lbf s^2/in)); w_m: natural frequencies (rad/s) from eigvals. 80 modes: 6
rigid-body modes plus 74 elastic modes up to 321.7 Hz, so predictions above about 260 Hz
lack the higher-mode residual and are not used.

Inputs (repository files, hashed in prereg_frozen_inputs.json):
  artifacts/reports/shocksat_fem_remesh_20260618/matrices/obs_V.npy
  artifacts/reports/shocksat_fem_remesh_20260618/matrices/eigvals.npy
  artifacts/reports/shocksat_fem_modal_twin_20260609/measured_modes.npz   (node order, damping)

Damping rule (primary): per-mode viscous ratio zeta(f_m) interpolated linearly in
frequency between the 33 measured modes of NASA's impact survey (.ash, values stored in
percent), held constant outside 54.2-256.8 Hz; rigid-body modes undamped.
"""
import os

import numpy as np

REPO = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", ".."))
P_OBS = os.path.join(REPO, "artifacts/reports/shocksat_fem_remesh_20260618/matrices/obs_V.npy")
P_EIG = os.path.join(REPO, "artifacts/reports/shocksat_fem_remesh_20260618/matrices/eigvals.npy")
P_MM = os.path.join(REPO, "artifacts/reports/shocksat_fem_modal_twin_20260609/measured_modes.npz")
G = 386.1  # in/s^2 per g
AX = {"X": 0, "Y": 1, "Z": 2}


class FEM:
    def __init__(self):
        self.V = np.load(P_OBS)
        lam = np.load(P_EIG)
        self.wn = np.sqrt(np.clip(lam, 0, None))
        self.fn = self.wn / (2 * np.pi)
        mm = np.load(P_MM, allow_pickle=True)
        self.nodes = [int(n) for n in mm["nodes"]]
        self.measured = mm["measured"].astype(bool)
        self.test_f = np.asarray(mm["freqs"], float)
        self.test_zeta = np.asarray(mm["damp"], float) / 100.0      # stored in percent

    def zeta(self, rule="measured_interp", const=None):
        z = np.zeros_like(self.fn)
        el = self.fn > 5.0
        if rule == "measured_interp":
            z[el] = np.interp(self.fn[el], self.test_f, self.test_zeta)
        elif rule == "constant":
            z[el] = const
        else:
            raise ValueError(rule)
        return z

    def row(self, node, axis):
        return 3 * self.nodes.index(int(node)) + AX[axis]

    def is_measured(self, node, axis):
        return bool(self.measured[self.nodes.index(int(node)), AX[axis]])

    def accelerance(self, f_hz, resp, drive, zeta):
        """|H| in g/lbf. resp, drive: (node, 'X'|'Y'|'Z')."""
        r, d = self.row(*resp), self.row(*drive)
        w = 2 * np.pi * np.asarray(f_hz, float)[:, None]
        num = self.V[r, None, :] * self.V[d, None, :] * (-w ** 2)
        den = self.wn[None, :] ** 2 - w ** 2 + 2j * zeta[None, :] * self.wn[None, :] * w
        return np.abs((num / den).sum(1)) / G

    def column_mean_log10(self, f_centres, hz_per_px, resp, drive, zeta, n_sub=21):
        """Mean of log10|H| across each pixel column (the digitiser's target quantity)."""
        off = np.linspace(-0.5, 0.5, n_sub) * hz_per_px
        f = (np.asarray(f_centres)[:, None] + off[None, :]).ravel()
        return np.log10(self.accelerance(f, resp, drive, zeta)).reshape(len(f_centres), n_sub).mean(1)
