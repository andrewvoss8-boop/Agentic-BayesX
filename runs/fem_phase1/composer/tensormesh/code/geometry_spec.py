"""Phase-1 INPUT spec (SI) — TensorMesh/scipy build uses these constants only."""
E_AL = 68.9e9
NU_AL = 0.33
RHO_AL = 2700.0
TRAY_LX = 0.300
TRAY_LY = 0.300
TRAY_T = 0.0127
TRAY_Z_TOP = 0.098
TRAY_Z_BOT = TRAY_Z_TOP - TRAY_T
STRUT_A = 22.0e-6

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
    ("A0", "F0"), ("A0", "F1"),
    ("A1", "F2"), ("A1", "F3"),
    ("A2", "F4"), ("A2", "F5"),
]
