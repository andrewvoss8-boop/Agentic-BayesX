"""Shared INPUT geometry for Phase-1 hexapod (SI). Each tool re-derives its own model."""
from __future__ import annotations

import math

E_AL = 68.9e9
NU_AL = 0.33
RHO_AL = 2700.0

TRAY_LX = 0.300
TRAY_LY = 0.300
TRAY_T = 0.0127
TRAY_Z_TOP = 0.098
TRAY_Z_BOT = TRAY_Z_TOP - TRAY_T
TRAY_MASS_LUMP = 3.09

STRUT_A = 22.0e-6
JOINT_K = 1.0e9

APEX = {
    "A0": (0.0, 0.110, TRAY_Z_TOP),
    "A1": (-0.095, -0.055, TRAY_Z_TOP),
    "A2": (0.095, -0.055, TRAY_Z_TOP),
}

FEET = {
    "F0": (-0.065, 0.267, 0.0),
    "F1": (0.065, 0.267, 0.0),
    "F2": (-0.199, -0.190, 0.0),
    "F3": (-0.264, -0.077, 0.0),
    "F4": (0.264, -0.077, 0.0),
    "F5": (0.199, -0.190, 0.0),
}

STRUTS = [
    ("A0", "F0", "b90+"),
    ("A0", "F1", "b90-"),
    ("A1", "F2", "b210+"),
    ("A1", "F3", "b210-"),
    ("A2", "F4", "b330+"),
    ("A2", "F5", "b330-"),
]


def strut_length_m(a_key: str, f_key: str) -> float:
    ax, ay, az = APEX[a_key]
    fx, fy, fz = FEET[f_key]
    return math.sqrt((fx - ax) ** 2 + (fy - ay) ** 2 + (fz - az) ** 2)
