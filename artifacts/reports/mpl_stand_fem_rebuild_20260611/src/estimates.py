#!/usr/bin/env python3
"""Single source of truth for ALL estimated and human-confirmed values
(MPL stand rebuild, FABLE 2026-06-11). The assumptions ledger and the assembly
read from here so numbers can never diverge between code and report.

STATUS field: CONFIRMED (Andrew, live chat 2026-06-11) or ESTIMATED
(ANDREW-CONFIRM-REQUIRED; photo-based per Andrew's instruction). Units stated
per entry. Mass unit: lbf*s^2/in ("snail"); 1 lbm = 1/386.089 lbf*s^2/in.
"""
G_IN = 386.089  # in/s^2, standard gravity (converts lbm -> lbf*s^2/in)
LBM = 1.0 / G_IN
MM = 1.0 / 25.4  # mm -> in

# ---- material (deck MAT1, CONFIRMED by deck) --------------------------------
STEEL = dict(E=2.9e7, nu=0.29, rho=7.324e-4)  # psi, -, lbf*s^2/in^4
# 6105-T5 aluminum (typical 80/20 extrusion alloy)
ALU = dict(E=1.0e7, nu=0.33, rho=2.54e-4)     # psi, -, lbf*s^2/in^4

# 80/20 Inc. 1515 series (1.5 in square) PUBLISHED T-slot section properties
# (catalog): A=0.7174 in^2, Ix=Iy=0.2842 in^4. J/shear estimated (T-slot is
# mostly-closed): J~0.42 in^4, shear factor ~0.4. ANDREW-CONFIRM the SERIES
# (1010 1" / 1515 1.5" / 40mm change A,I by ~10x = the dominant subframe knob).
TSLOT_1515 = dict(A=0.7174, I1=0.2842, I2=0.2842, J=0.42,
                  K1=0.40, K2=0.40)

ESTIMATES = {
    # --------------------------------------------------------------- shield
    "shield_thickness_in": dict(
        value=1.7 * MM, units="in", status="CONFIRMED",
        source="Andrew live chat 2026-06-11: shield is 1.7 mm thick",
        sensitivity="HIGH (panel modes ~ t for bending)",
        rationale="1.7 mm = 0.066929 in"),
    "shield_material": dict(
        value="steel (deck MAT1: E=2.9e7 psi, rho=7.324e-4)", units="-",
        status="ESTIMATED (Andrew 2026-06-11: 'probably steel')",
        sensitivity="LOW for frequencies (steel and "
        "aluminum have nearly equal E/rho specific bending stiffness), "
        "HIGH for panel mass (x2.9) and frame coupling",
        source="Andrew: 'probably steel'; also welded to the steel frame "
        "(aluminum would not weld to steel)",
        rationale="welded attachment strongly implies steel; kept yellow "
        "until 'probably' becomes 'confirmed'"),
    "shield_upper_extent": dict(
        value=dict(x=61.50, y0=0.0, y1=-47.9999, z0=22.5, z1=48.5),
        units="in (deck frame)", status="ESTIMATED",
        sensitivity="MEDIUM (sets panel aspect/modes)",
        source="photos IMG_9842/9846 + deck rails at z=22.5 and 48.5",
        rationale="big sticker panel spans full width, between the z=22.5 and "
        "z=48.5 front rails; ~1.5 in overhang above top rail ignored (coarse)"),
    "shield_lower_extent": dict(
        value=dict(x=61.50, y0=0.0, y1=-47.9999, z0=0.0, z1=14.5),
        units="in (deck frame)", status="ESTIMATED",
        sensitivity="MEDIUM",
        source="photos IMG_9842 + deck rails at z=0 and 14.5",
        rationale="smaller lower panel between ground rail z=0 and z=14.5 "
        "rail; gap band z=14.5-22.5 = engine/thrust-plate band (blue visible "
        "between panels in IMG_9842)"),
    "shield_mesh": dict(
        value=dict(upper_nx=10, upper_nz=6, lower_nx=10, lower_nz=3),
        units="elements", status="ESTIMATED",
        sensitivity="LOW-MEDIUM (discretization; h-refinement spot-check run)",
        source="-", rationale="deliberately coarse per Andrew: ~4.8 in panels; "
        "~2 elements per half-wave at 500 Hz, ~4 at 150 Hz"),
    "shield_screw_k_trans": dict(
        value=1.0e6, units="lbf/in", status="ESTIMATED",
        sensitivity="HIGH (top calibration knob: panel boundary condition)",
        source="Andrew 2026-06-11: shield 'welded on at a few points' -> "
        "WELD SPOTS, not screws",
        rationale="spot/plug weld of 1.7mm sheet to tube wall: ~10x a sheet "
        "screw, below a continuous weld; parametric group s_shield_att, "
        "prior should still span x0.01-x100"),
    "shield_screw_k_rot": dict(
        value=1.0e4, units="in*lbf/rad", status="ESTIMATED",
        sensitivity="MEDIUM", source="weld spot on thin sheet (Andrew: welded)",
        rationale="local sheet flexure around a weld spot still allows "
        "pivoting; stiffer than a screw head"),
    "shield_screws_upper": dict(
        value=[(-4.8, 48.5), (-24.0, 48.5), (-43.2, 48.5),
               (-4.8, 22.5), (-24.0, 22.5), (-43.2, 22.5),
               (0.0, 35.5), (-47.9999, 35.5)],
        units="(y,z) in", status="ESTIMATED", sensitivity="MEDIUM",
        source="IMG_9842 visible fasteners along edges",
        rationale="3 top + 3 bottom + 1 per side"),
    "shield_screws_lower": dict(
        value=[(-4.8, 14.5), (-24.0, 14.5), (-43.2, 14.5),
               (-4.8, 0.0), (-24.0, 0.0), (-43.2, 0.0)],
        units="(y,z) in", status="ESTIMATED", sensitivity="MEDIUM",
        source="IMG_9842", rationale="3 top + 3 bottom edge screws"),
    # ------------------------------------------------- mounted masses (QOI)
    # valve assembly = HIGHER-FIDELITY 80/20 frame model (D38), defined below
    # in VALVE_FRAME (not a single CONM2). The mounted-mass loop no longer
    # handles 'valve_panel'.
    "valve_frame": dict(
        value=dict(
            series="1515 (1.5 in, ASSUMED)", material="6105-T5 aluminum",
            center=[50.0, -12.0, 9.0], L_x=18.0, W_y=10.0, H_z=14.0,
            n_bays=3,                       # stations along x = n_bays+1
            mount_k_trans=1.0e5, mount_k_rot=1.0e4,
            tank_mass_lbm_each=2.5, n_tanks=4,
            valve_manifold_mass_lbm=6.0),
        units="in; lbf/in; in*lbf/rad; lbm",
        status="ESTIMATED (Andrew 2026-06-11 round 7: 'much higher fidelity "
        "model that has the 80/20 extrusion frame' + photo; series/size + "
        "cage dims + tank/valve masses ANDREW-CONFIRM-REQUIRED)",
        sensitivity="HIGH (QOI item = valve acceleration; the EXTRUSION SERIES "
        "is the dominant subframe-stiffness knob, ~10x between 1\"/1.5\"/40mm)",
        source="Andrew round 7 photo: ~3-bay rectangular 80/20 cage, 4 black "
        "accumulator tanks low + valve manifolds/regulators across, bolted to "
        "the stand base; replaces the rev<=6 single rigid CONM2",
        rationale="cage modeled as Timoshenko aluminum beam members (1515 "
        "published A=0.717 in^2, I=0.284 in^4); tanks (4x2.5) + manifold/"
        "valves (6) lumped on the frame nodes; bottom corners bushed to the "
        "nearest stand base grids. Frame self-mass from A*L*rho_alu. Gives "
        "REAL frame bending/rocking modes instead of one rigid rock."),
    "electronics_box": dict(
        value=dict(mass_lbm=3.0, cg=[58.5, -10.5, 33.0],
                   dims_in=[10.0, 8.0, 6.0], k_att_trans=5.0e4,
                   k_att_rot=5.0e3, n_attach=3,
                   shield_bolts_yz=[(-6.0, 37.0), (-15.0, 37.0),
                                    (-10.5, 29.0)]),
        units="lbm; in; lbf/in; in*lbf/rad", status="ESTIMATED -> PRIOR "
        "(Andrew 2026-06-11 round 4: mass 'between 2 and 4 pounds' = a "
        "statistical prior; see priors.py. Point value 3.0 lbm = range "
        "midpoint for the deterministic mode table only. Location CONFIRMED "
        "qualitatively, round 3. Stays YELLOW until the posterior update.)",
        sensitivity="HIGH (QOI item: box acceleration; ALSO mass-loads the "
        "1.7mm shield -- sets mode 1 of the whole stand)",
        source="Andrew round 3: box ON the shield over the LabJack sticker, "
        "3 mounting-feet bolts (IMG_9853/9842/9846); round 4: mass 2-4 lbm",
        rationale="silver fan enclosure ~10x8x6 in; the OLD 10 lbm was an "
        "over-guess -- Andrew narrowed to 2-4 lbm (D34); CG 3 in behind the "
        "panel; 3 bolts in series with local 1.7mm panel compliance, "
        "~5e4 lbf/in each"),
    "white_box_upper": dict(
        value=dict(mass_lbm=8.0, cg=[55.0, -10.5, 33.0],
                   dims_in=[10.0, 8.0, 5.0], k_att_trans=1.0e4,
                   k_att_rot=5.0e3, n_attach=2),
        units="lbm; in; lbf/in; in*lbf/rad", status="ESTIMATED (guess authorized by Andrew 2026-06-11, stays YELLOW)",
        sensitivity="MEDIUM-HIGH (QOI item)",
        source="photos IMG_9843/9844/9845: the BEIGE electrical box mounted "
        "on the back-side blue panel/frame (distinct from the silver "
        "electronics box on the shield, D33)",
        rationale="~10x8x5 in box ~8 lbm; lighter bracket -> local mode "
        "~110 Hz"),
    # psu_box DELETED (D33): it was the electronics box double-counted.
    # ------------------------------------------------------- later coupling
    "f_clamp_mass": dict(
        value=415.3e-3 / 0.45359237, units="lbm (=415.3 g)", status="CONFIRMED",
        sensitivity="n/a this task (ruler/clamp NOT modeled here)",
        source="Andrew live chat 2026-06-11",
        rationale="Jorgensen F-clamp; ledgered for the later coupling task"),
    # ------------------------------------------------------------- modeling
    "joint_bush_k": dict(
        value=1.0e7, units="lbf/in and in*lbf/rad (all 6 DOF)",
        status="CONFIRMED (deck PBUSH 37)",
        sensitivity="MEDIUM (near-rigid; parametric group s_bush)",
        source="deck", rationale="Femap generic stiff joint springs"),
    "foot_spring_k": dict(
        value=1.0e8, units="lbf/in and in*lbf/rad (all 6 DOF)",
        status="ESTIMATED (variant only; nominal feet are SPC fixed)",
        sensitivity="MEDIUM (base flexibility knob for later calibration)",
        source="-", rationale="stiff grounding springs, ~10x joint stiffness"),
    "drill_scale": dict(
        value=1e-4, units="fraction of mean membrane diagonal",
        status="ESTIMATED (numerical device)",
        sensitivity="LOW (checked by x100 arm)",
        source="PARAM K6ROT=100 intent (deck)",
        rationale="small artificial drilling stiffness on shell normal "
        "rotations; sensitivity arm verifies modes are insensitive"),
}
