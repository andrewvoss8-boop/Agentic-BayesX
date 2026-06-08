"""
Shared Phase-1 hexapod model INPUTS — RAW NUMBERS ONLY (identical across all tools).

INTEGRITY RULE: this module holds ONLY the shared spec inputs (node coordinates,
materials, section properties, masses, boundary conditions) that the runner prompt
requires to be identical across builds. It contains NO element matrices, NO assembly,
NO solver. Each tool (CalculiX / TensorMesh / JAX / Nastran deck) independently
re-derives its own K and M from these inputs. Nothing here is ported between tools.

Units: SI (m, kg, N, Pa). Coordinate frame: origin at tray center; +z up;
tray mid-plane at z = 0.098 m; base (ground) plane at z = 0.
Source: docs/lab/fem_phase1_runner_prompt.md and docs/lab/FEM_architecture.md (PHASE 1).
"""

import numpy as np

# ----------------------------------------------------------------------------
# Geometry — node coordinates (runner prompt table), millimetres -> metres.
# Three apex points on the tray (radius 110 mm, 120 deg apart, z = 98 mm);
# six grounded feet on the base (z = 0). Each apex carries a bipod (2 struts).
# ----------------------------------------------------------------------------
MM = 1.0e-3

# Tray apex points (each shared by a strut pair / bipod)
APEX_MM = {
    "A1_b90":  (   0.0, 110.0, 98.0),   # serves struts b90+, b90-
    "A2_b210": ( -95.0, -55.0, 98.0),   # serves struts b210+, b210-
    "A3_b330": (  95.0, -55.0, 98.0),   # serves struts b330+, b330-
}

# Grounded feet (base, z = 0) — FIXED in Phase 1
FOOT_MM = {
    "b90p":  ( -65.0,  267.0, 0.0),
    "b90m":  (  65.0,  267.0, 0.0),
    "b210p": (-199.0, -190.0, 0.0),
    "b210m": (-264.0,  -77.0, 0.0),
    "b330p": ( 264.0,  -77.0, 0.0),
    "b330m": ( 199.0, -190.0, 0.0),
}

# Strut connectivity: (name, apex_key, foot_key)
STRUTS = [
    ("b90p",  "A1_b90",  "b90p"),
    ("b90m",  "A1_b90",  "b90m"),
    ("b210p", "A2_b210", "b210p"),
    ("b210m", "A2_b210", "b210m"),
    ("b330p", "A3_b330", "b330p"),
    ("b330m", "A3_b330", "b330m"),
]


def apex_m():
    return {k: np.array(v) * MM for k, v in APEX_MM.items()}


def foot_m():
    return {k: np.array(v) * MM for k, v in FOOT_MM.items()}


# ----------------------------------------------------------------------------
# Materials
# ----------------------------------------------------------------------------
# Tray: 6061-T6 solid aluminium plate (Thorlabs MB3030/M, 300 x 300 x 12.7 mm)
TRAY = dict(
    E=68.9e9,          # Pa
    nu=0.33,           # -
    rho=2700.0,        # kg/m^3
    Lx=0.300,          # m
    Ly=0.300,          # m
    t=0.0127,          # m  (12.7 mm)
    z_mid=0.098,       # m  (tray mid-plane height)
    mass_lumped=3.09,  # kg (use only if lumping; meshed mass is emergent = rho*V)
)
# emergent solid-plate mass check: 0.300*0.300*0.0127*2700 = 3.0861 kg ~ 3.09 kg

# Struts: aluminium tube, 8 mm OD, 1 mm wall, 196 mm eye-to-eye
_OD = 0.008                  # m
_WALL = 0.001                # m
_ID = _OD - 2.0 * _WALL      # 0.006 m
STRUT = dict(
    E=68.9e9,                # Pa
    rho=2700.0,              # kg/m^3
    OD=_OD, ID=_ID, wall=_WALL,
    A=np.pi / 4.0 * (_OD**2 - _ID**2),                 # ~2.199e-5 m^2
    I=np.pi / 64.0 * (_OD**4 - _ID**4),                # ~1.374e-10 m^4 (2nd moment)
    J=np.pi / 32.0 * (_OD**4 - _ID**4),                # ~2.749e-10 m^4 (polar)
    G=68.9e9 / (2.0 * (1.0 + 0.33)),                   # shear modulus, Pa
    L_nominal=0.196,         # m (eye-to-eye)
)

# Joints: RIGID this phase, modeled as stiff translational springs at explicit
# joint nodes so finite compliance is a future parameter change. Moment-free
# (spherical) -> rotational DOF released at strut ends.
JOINT = dict(
    k_trans=1.0e9,   # N/m  per translational DOF (stiff "rigid" joint)
    release_rotations=True,
)

# Boundary condition: strut feet FIXED (grounded); source plate NOT modeled.
BC = "feet_fixed"


def strut_length(name):
    a = apex_m()
    f = foot_m()
    for nm, ak, fk in STRUTS:
        if nm == name:
            return float(np.linalg.norm(a[ak] - f[fk]))
    raise KeyError(name)


if __name__ == "__main__":
    print("Strut lengths (m) and elevation angles (deg):")
    a, f = apex_m(), foot_m()
    for nm, ak, fk in STRUTS:
        v = a[ak] - f[fk]
        L = np.linalg.norm(v)
        elev = np.degrees(np.arcsin(abs(v[2]) / L))
        print(f"  {nm:6s}  L={L*1e3:7.2f} mm  elev={elev:5.2f} deg")
    print(f"Strut A = {STRUT['A']*1e6:.3f} mm^2,  I = {STRUT['I']*1e12:.3f} mm^4")
    print(f"Tray emergent mass = {TRAY['rho']*TRAY['Lx']*TRAY['Ly']*TRAY['t']:.4f} kg")
    ka = STRUT['E'] * STRUT['A'] / STRUT['L_nominal']
    print(f"Single-strut axial stiffness EA/L = {ka:.4e} N/m")
