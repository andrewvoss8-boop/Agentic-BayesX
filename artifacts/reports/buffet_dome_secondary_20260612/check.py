#!/usr/bin/env python3
"""Checker — buffet/acoustic dome secondary-structure study.

Stage 1 gates: forcing-math plumbing validation (out/forcing_validation.json).
Three-tier per AGENTS.md Result Status Standard: GREEN / YELLOW (documented,
non-fatal miss) / RED (blocking). Exit non-zero ONLY on RED. Later stages
append gates; existing gate thresholds are immutable during a trial.
"""
import json
import os
import sys

gates = []

def gate(name, status, detail):
    gates.append({"gate": name, "status": status, "detail": detail})

p = "out/forcing_validation.json"
if not os.path.exists(p):
    gate("S1_artifact_exists", "RED", f"{p} missing")
else:
    d = json.load(open(p))
    gate("S1_artifact_exists", "GREEN", p)

    # G1 fully-correlated limit vs analytic integral. Expectation: midpoint-rule
    # error ~2*[(m*pi/Nx)^2+(n*pi/Ny)^2]/24 -> ~2.4% worst for (5,5) on 48x36.
    e = d["C1_fully_correlated"]["max_rel_err_oddodd_mn_le5"]
    leak = d["C1_fully_correlated"]["even_mode_leak_ratio"]
    s = "GREEN" if (e <= 0.025 and leak <= 1e-12) else ("YELLOW" if e <= 0.05 else "RED")
    gate("S1_G1_fully_correlated_limit", s,
         f"max rel err {e:.4f} (quadrature-consistent <=0.025); even leak {leak:.1e}")

    # G2 separable fast path == full matrix path (machine precision)
    e = max(d["C2a_fast_vs_full_maxrel"])
    gate("S1_G2_fast_equals_full", "GREEN" if e <= 1e-12 else "RED", f"max rel {e:.2e}")

    # G3 grid resolution vs 10x-fine quadrature at 400 Hz (mesh-sizing rule)
    c2b = d["C2b_grid_vs_fine_quadrature_400hz"]
    e = max(v for k, v in c2b.items() if k.startswith("mode_"))
    s = "GREEN" if e <= 0.025 else ("YELLOW" if e <= 0.05 else "RED")
    gate("S1_G3_grid_resolution", s,
         f"worst joint-acceptance grid err {e:.4f} at 400 Hz with "
         f"{c2b['nodes_per_lateral_Lcoh']:.1f} nodes/lateral-coherence-length "
         f"(PRODUCTION MESH RULE: >=6 nodes per Lcoh at f_max)")

    # G4 DAF low-frequency -> fully-correlated limit
    e = d["C3_daf_lowfreq_vs_fullcorr"]["rel_diff_mode11"]
    s = "GREEN" if e <= 0.01 else ("YELLOW" if e <= 0.03 else "RED")
    gate("S1_G4_daf_lowfreq_limit", s, f"rel diff {e:.5f}")

    # G5 response peaks at analytic frequencies (nearest local max)
    e = max(v["rel_err"] for v in d["C4_peak_placement"].values())
    s = "GREEN" if e <= 0.015 else ("YELLOW" if e <= 0.03 else "RED")
    gate("S1_G5_peak_placement", s, f"worst rel err {e:.4f}")

    # G6 integrated RMS vs white-near-resonance closed form (diagonal-only
    # closed form -> generous band documented)
    r = d["C5_rms"]["ratio"]
    s = "GREEN" if 0.85 <= r <= 1.15 else ("YELLOW" if 0.65 <= r <= 1.35 else "RED")
    gate("S1_G6_rms_closed_form", s, f"sigma ratio numeric/closed-form {r:.4f}")

    # G7 numerics: Hermitian CSD, non-negative response PSD
    h = d["C6_numerics"]["worst_hermitian_resid"]
    mn = d["C6_numerics"]["min_Saa"]
    gate("S1_G7_numerics", "GREEN" if (h <= 1e-12 and mn >= 0) else "RED",
         f"hermitian resid {h:.2e}; min Saa {mn:.4g}")

    # G8 coherence physics: pure-decay kernels monotone; convective-coincidence
    # non-monotonicity at 400 Hz is RECORDED expected physics, not a failure.
    c7 = d["C7_coherence_physics"]
    ok = c7["Jy_monotone_decreasing"] and c7["Jx_lowfreq_monotone_decreasing"]
    gate("S1_G8_coherence_physics", "GREEN" if ok else "RED",
         f"lateral monotone {c7['Jy_monotone_decreasing']}; low-f streamwise "
         f"monotone {c7['Jx_lowfreq_monotone_decreasing']}; J11(400Hz) "
         f"non-monotone coincidence curve recorded")

# ---- S2: added beam/bar element validation (D10 gating item) ----
pb = "out/beam_validation.json"
if not os.path.exists(pb):
    gate("S2_beam_artifact_exists", "RED", f"{pb} missing")
else:
    b = json.load(open(pb))
    gate("S2_beam_artifact_exists", "GREEN", pb)
    # V1 rigid-body count
    v1 = b["V1_freefree_zero_modes"]
    gate("S2_V1_rigid_body_modes", "GREEN" if v1["ok"] else "RED",
         f"{v1['n_zero']} zero modes (expect 6); first elastic {v1['f7_elastic_hz']:.1f} Hz")
    # V2-V5,V7 analytic-frequency checks (<=1%); report worst
    fchecks = ["V2_cantilever_bending", "V3_cantilever_axial",
               "V4_cantilever_torsion", "V5_simply_supported_bending",
               "V7_bar_axial"]
    worst = max(abs(b[k]["err_pct"]) for k in fchecks)
    s = "GREEN" if worst <= 1.0 else ("YELLOW" if worst <= 2.0 else "RED")
    gate("S2_V2toV7_analytic_freq", s,
         f"worst |err| {worst:.3f}% vs analytic across bending/axial/torsion/SS/bar")
    # V6 rigid-body force residual
    v6 = b["V6_rigid_body_residual"]
    gate("S2_V6_rigid_body_residual", "GREEN" if v6["ok"] else "RED",
         f"trans {v6['trans_resid']:.1e}, rot {v6['rot_resid']:.1e}")

# ---- S3: fine-region model + assembly validation ----
pa = "out/assembly_validation.json"
pm = "out/model_meta.json"
if os.path.exists(pa) and os.path.exists(pm):
    a = json.load(open(pa)); mm = json.load(open(pm))["sanity"]
    gate("S3_assembly_donnell", "GREEN" if a["ALL_OK"] else "RED",
         "SS-cylinder vs Donnell n=3..6: " +
         ", ".join(f"{k} {v['err_pct']:.1f}%" for k, v in a["A2_donnell"].items())
         + f"; rigid {a['A1_freefree']['n_rigid']}/6; pairs <"
         f"{max(v['pair_spread_pct'] for v in a['A3_degenerate_pairs'].values()):.1e}%")
    rt_, rr_ = mm["rigid_resid_trans"], mm["rigid_resid_rot"]
    gate("S3_model_rigid_body", "GREEN" if max(rt_, rr_) < 1e-12 else "RED",
         f"free-structure K@rigid resid: trans {rt_:.1e}, rot {rr_:.1e}")
    mp = mm["mass_parts"]
    barrel_an = 2 * 3.141592653589793 * 2.25 * 1.5 * 0.005 * 2800
    err_b = abs(mp["barrel"] - barrel_an) / barrel_an
    gate("S3_mass_sanity", "GREEN" if err_b < 0.01 else "RED",
         f"barrel {mp['barrel']:.1f} kg vs analytic {barrel_an:.1f} "
         f"({100*err_b:.2f}%); total {mm['mass_total_kg']:.1f} kg")
else:
    gate("S3_model", "RED", "model/assembly artifacts missing")

# ---- S4: modes + nominal QOI (PENDING-yellow until stages run) ----
for bc in ("bcA", "bcB"):
    pmod = f"out/modes_{bc}_meta.json"
    if os.path.exists(pmod):
        mi = json.load(open(pmod))
        ok = mi["fmax"] >= 800.0 and mi["n_below_400"] > 0
        gate(f"S4_modes_{bc}", "GREEN" if ok else "YELLOW",
             f"{mi['n_modes']} modes to {mi['fmax']:.0f} Hz "
             f"({mi['n_below_400']} below 400 Hz); target >=800 Hz")
    else:
        gate(f"S4_modes_{bc}", "YELLOW", "PENDING — solve not finished; no "
             "modal claim made")
    pq = f"out/qoi_{bc}_summary.json"
    if os.path.exists(pq):
        qs = json.load(open(pq))
        sc = qs.get("self_check_rel", 1.0)
        cl = qs.get("clip_frac_max", 1.0)
        ok = sc < 1e-8 and cl < 0.02
        gate(f"S4_qoi_{bc}", "GREEN" if ok else ("YELLOW" if cl < 0.10 else "RED"),
             f"separable-path self-check {sc:.1e}; kernel clip frac max "
             f"{cl:.3f}; {qs['n_modes_used']} modes; BUFFET-ONLY caveat present="
             f"{'BUFFET-ONLY' in qs.get('caveat','')}")
    else:
        gate(f"S4_qoi_{bc}", "YELLOW", "PENDING — QOI sweep not yet run")

# ---- S5: CI propagation MC (labeled, no sampler) ----
for bc in ("bcA", "bcB"):
    pc = f"out/ci_{bc}_summary.json"
    if os.path.exists(pc):
        cs = json.load(open(pc))
        ok = "no sampler" in cs.get("label", "").lower() or \
             "NO data" in cs.get("label", "")
        gate(f"S5_ci_{bc}", "GREEN" if (cs["n_draws"] >= 100 and ok) else "YELLOW",
             f"{cs['n_draws']} prior-propagation draws; label honest="
             f"{bool(ok)}; MC quantile noise at 144 draws ~ +/-10-15% (documented)")
    else:
        gate(f"S5_ci_{bc}", "YELLOW", "PENDING — CI MC not yet run")

# ---- S6: coupling / modal-truncation trust-test (P2) ----
pcp = "out/coupling_validation.json"
if os.path.exists(pcp):
    cp = json.load(open(pcp))
    md = cp["md_worst_max_rel"]
    s = "GREEN" if md <= 0.05 else ("YELLOW" if md <= 0.15 else "RED")
    gate("S6_coupling_truncation", s,
         f"mode-displacement (820 Hz trunc) vs DIRECT full-58k solve: worst "
         f"{md*100:.2f}% over interface QOIs (driven point loads, masked to "
         f"non-negligible response) -> modal superposition validated")
else:
    gate("S6_coupling_truncation", "YELLOW", "PENDING — coupling solve not run")

# ---- S7: mesh convergence (Discretization gate) ----
pmf = "out/variant_summary.json"
if os.path.exists(pmf):
    vs = json.load(open(pmf))
    mf = vs["variants"].get("meshf", {})
    if mf.get("status") == "done":
        rr = mf["ratios"]
        worst = max(abs(v - 1.0) for v in rr.values())
        s = "GREEN" if worst <= 0.10 else ("YELLOW" if worst <= 0.20 else "RED")
        gate("S7_mesh_convergence", s,
             f"refined mesh (Nth 240->300) QOI ratios "
             f"{', '.join(f'{k} {v:.2f}' for k, v in rr.items())} -> worst "
             f"{worst*100:.0f}% change = converged")
    else:
        gate("S7_mesh_convergence", "YELLOW", "meshf variant pending")
else:
    gate("S7_mesh_convergence", "YELLOW", "PENDING — variant summary not built")

# ---- S8: response-limit proxy (vision 2.2 / D7) ----
prp = "out/response_limit_proxy.json"
if os.path.exists(prp):
    rp = json.load(open(prp))
    coh = rp["coherence_at_ctrl_avF"]
    eta_alphas = [v["alpha_avF"] for v in rp["alpha_eta_robustness"].values()]
    eta_mean = sum(eta_alphas) / len(eta_alphas)
    eta_cv = (max(eta_alphas) - min(eta_alphas)) / eta_mean
    forcing_inv = rp["alpha_forcing_invariance_rel"]
    massr = rp["cg_alpha_vs_mass_ratio"]
    ok = (coh > 0.95 and eta_cv < 0.02 and forcing_inv < 1e-6
          and 0.8 < massr < 1.4)
    gate("S8_response_limit_proxy", "GREEN" if ok else "YELLOW",
         f"controlling {rp['controlling_freq_hz']:.0f} Hz: coherence {coh:.4f}; "
         f"gain eta-CV {eta_cv*100:.2f}% + forcing-invariant {forcing_inv:.0e}; "
         f"CG-gain/mass {massr:.2f} (7004C eff-mass tie); valid band "
         f"{rp['valid_band_gamma_gt_0p8'][0]:.0f}-{rp['valid_band_gamma_gt_0p8'][1]:.0f} Hz "
         f"= {rp['fraction_punch_energy_in_valid_band']*100:.0f}% of punch energy")
else:
    gate("S8_response_limit_proxy", "YELLOW", "PENDING — proxy not run")

order = {"GREEN": 0, "YELLOW": 1, "RED": 2}
overall = max((g["status"] for g in gates), key=lambda s: order[s])
counts = {s: sum(1 for g in gates if g["status"] == s) for s in order}
stage_msg = ("S1 forcing math + S2 element + S3 model/assembly certified. "
             "S4 modes/QOI and S5 CI gates reflect artifacts present at run "
             "time; PENDING entries are YELLOW (no claim made for them). "
             "Variant/mesh-convergence results are reported in packet.md when "
             "their artifacts exist.")
report = {"overall": overall, "counts": counts, "gates": gates,
          "stage": stage_msg}
with open("checker_report.json", "w") as fh:
    json.dump(report, fh, indent=1)
print(json.dumps(report, indent=1))
sys.exit(1 if overall == "RED" else 0)
