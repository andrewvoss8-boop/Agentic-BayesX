"""Raw Phase-1 hexapod inputs shared by the Codex tool builds."""

from __future__ import annotations

import math
import numpy as np

AGENT = "codex"
UNITS = "SI: m, kg, N, Hz"
FRAME = "Origin at tray center; +z up; tray mid-plane at z=0.098 m; base feet at z=0 fixed."
MASS_CASE = "bare tray, no ballast"

E_AL = 68.9e9
NU_AL = 0.33
RHO_AL = 2700.0
TRAY_L = 0.300
TRAY_T = 0.0127
TRAY_Z = 0.098
TRAY_MASS = TRAY_L * TRAY_L * TRAY_T * RHO_AL

STRUT_OD = 0.008
STRUT_WALL = 0.001
STRUT_AREA = math.pi / 4.0 * (STRUT_OD**2 - (STRUT_OD - 2.0 * STRUT_WALL) ** 2)
JOINT_K = 1.0e9

STRUT_NAMES = ["b90+", "b90-", "b210+", "b210-", "b330+", "b330-"]
APEX = np.array(
    [
        [0.000, 0.110, 0.098],
        [0.000, 0.110, 0.098],
        [-0.095, -0.055, 0.098],
        [-0.095, -0.055, 0.098],
        [0.095, -0.055, 0.098],
        [0.095, -0.055, 0.098],
    ],
    dtype=float,
)
FOOT = np.array(
    [
        [-0.065, 0.267, 0.0],
        [0.065, 0.267, 0.0],
        [-0.199, -0.190, 0.0],
        [-0.264, -0.077, 0.0],
        [0.264, -0.077, 0.0],
        [0.199, -0.190, 0.0],
    ],
    dtype=float,
)
