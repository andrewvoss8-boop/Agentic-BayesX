#!/usr/bin/env python3
"""STAGE-3 review packet PPTX: assembles the headline numbers + figures for a labmate audit.
Reads report/blind3_*.json + figures. Writes report/packet.pptx (Stage-3)."""
from __future__ import annotations
import json
from pathlib import Path
from pptx import Presentation
from pptx.util import Inches, Pt

REP = Path(__file__).resolve().parents[1] / "report"; FIG = REP / "figures"


def load(name):
    p = REP / name
    return json.loads(p.read_text()) if p.exists() else {}


def main():
    res = load("blind3_results.json"); qoi = load("blind3_qoi_results.json")
    comp = load("blind3_companions.json"); heldout = load("blind3_heldout.json")
    prs = Presentation(); prs.slide_width = Inches(13.33); prs.slide_height = Inches(7.5)
    blank = prs.slide_layouts[6]; title_only = prs.slide_layouts[5]

    def add_title(s, txt):
        tb = s.shapes.add_textbox(Inches(0.4), Inches(0.15), Inches(12.5), Inches(0.7))
        p = tb.text_frame.paragraphs[0]; p.text = txt; p.font.size = Pt(22); p.font.bold = True

    def add_bullets(s, lines, top=1.0, size=13, left=0.5, width=12.3):
        tb = s.shapes.add_textbox(Inches(left), Inches(top), Inches(width), Inches(6.0)); tf = tb.text_frame
        tf.word_wrap = True
        for i, ln in enumerate(lines):
            p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
            p.text = ln; p.font.size = Pt(size)

    def add_img(s, name, left=0.4, top=1.0, height=6.0):
        f = FIG / name
        if f.exists():
            s.shapes.add_picture(str(f), Inches(left), Inches(top), height=Inches(height))

    conv = res.get("convergence", {}); lw = res.get("learned_with_d", {})
    # Slide 1: title + headline
    s = prs.slides.add_slide(blank); add_title(s, "Stage-3 BLIND StatFEM — structure-aware fix vs independent truth")
    gate = "PASS" if res.get("gate_pass") else "FAIL"
    add_bullets(s, [
        "Three coupled fixes the blind failure pointed to: (1) ASYMMETRIC per-strut forward (x≠y, rx≠ry),",
        "(2) STRUCTURE/feature-based per-strut discrepancy in PARAMETER space (not freq-only GP),",
        "(3) COMPLEX (real+imag) likelihood. netCG via the canonical FBS contract (fixes the ~2× drive-point bias).",
        "",
        f"CONVERGENCE GATE (all latents): {gate}  —  worst R-hat {conv.get('worst_rhat','?'):.3f}, "
        f"min bulk ESS {conv.get('min_ess_bulk','?'):.1f}, divergences {conv.get('divergences','?')}.",
        f"σ_e (misfit) median {lw.get('sigma_e',[None,'?'])[1]:.3f}; σ_d median "
        f"{(lw.get('sigma_d') or [None,'?'])[1]}; σ_build {lw.get('sigma_build',[None,'?'])[1]:.3f}.",
        "",
        "HONEST headline: structure-based discrepancy DOES represent the azimuthal x≠y / rx≠ry splits, BUT",
        "the coarse model still MISSES higher modes (z: 62/77/120 Hz) → σ_e floor ~1.9 is largely",
        "irreducible. Never claim 'NUTS active' unless the gate passes; reported either way.",
    ], size=14)

    # Slide 2: netCG transfer (FBS contract)
    s = prs.slides.add_slide(title_only); add_title(s, "netCG QOI — canonical FBS contract (f→0 limit + resonance)")
    add_img(s, "blind3_netcg_transfer.png", left=0.4, top=1.0, height=5.6)
    if qoi:
        add_bullets(s, [
            f"f→0 rigid limit M_L/(M_S+M_L) = {qoi.get('netcg_fzero_rigid_limit',0):.3f} "
            f"(m_src≈{qoi.get('m_source_z_kg',0):.0f}, m_load={qoi.get('m_load_kg',0):.0f})",
            "NOT drive-point F/M_zz; NOT a constant mass ratio (both FORBIDDEN by contract).",
        ], top=6.4, size=12)

    # Slide 3: full-uncertainty netCG vs truth
    s = prs.slides.add_slide(title_only); add_title(s, "Full-uncertainty netCG vs published truth (D13 closed)")
    add_img(s, "blind3_netcg_grms_vs_truth.png", left=0.3, top=1.0, height=5.4)
    if qoi:
        g = qoi.get("netcg_3grms_g", {}); t = qoi.get("published_observed_netcg_g", {})
        add_bullets(s, [
            f"pred 3·GRMS p50 {g.get('p50',0):.2f} g [95% {g.get('p2p5',0):.2f}–{g.get('p97p5',0):.2f}] "
            f"vs truth {t.get('mean',0):.2f} ({t.get('min',0):.2f}–{t.get('max',0):.2f})",
            f"bias {qoi.get('bias_ratio_median',0):.2f}×, 95% cov {qoi.get('coverage_of_published_95',0):.2f}, "
            f"99% cov {qoi.get('coverage_of_published_99',0):.2f}",
            f"propagated: parameter (epistemic)+build+flight (aleatory)+discrepancy d.",
        ], top=6.3, size=12)

    # Slide 4: PSD vs spec
    s = prs.slides.add_slide(title_only); add_title(s, "Interface netCG PSD vs spec — narrow-band exceedance")
    add_img(s, "blind3_netcg_psd_vs_spec.png", left=0.4, top=1.0, height=5.6)

    # Slide 5: AM overlay held-out
    s = prs.slides.add_slide(title_only); add_title(s, "Posterior-predictive apparent mass vs data (held-out build 6)")
    add_img(s, "blind3_ppc_heldout_b6.png", left=0.3, top=1.0, height=5.6)

    # Slide 6: with/without discrepancy splits + hyperparams
    s = prs.slides.add_slide(title_only); add_title(s, "Does the structure-based discrepancy catch the spatial split?")
    add_img(s, "blind3_split_with_d.png", left=0.2, top=1.0, height=4.6)
    add_img(s, "blind3_hyperparams.png", left=0.2, top=5.7, height=1.5)

    # Slide 7: companions + held-out
    s = prs.slides.add_slide(blank); add_title(s, "Trust studies — companions + held-out calibration")
    wo = comp.get("with_vs_without", {}); esc = res.get("effective_sample_count", {})
    add_bullets(s, [
        f"WITH vs WITHOUT discrepancy: σ_e {wo.get('sigma_e_with','?')} (with) vs "
        f"{wo.get('sigma_e_without','?')} (without); worst R-hat {wo.get('worst_rhat_with','?'):.2f} vs "
        f"{wo.get('worst_rhat_without','?'):.2f}.",
        f"Held-out builds 6,7 coverage95 {heldout.get('build_coverage95','?')}, log-width "
        f"{heldout.get('build_logwidth','?')}; held-out band {heldout.get('heldout_band_hz','?')} "
        f"coverage95 {heldout.get('band_coverage95','?')} (read coverage WITH width).",
        f"Effective vs nominal sample count: n_eff(k_pop) {esc.get('n_eff_k_pop','?'):.1f} vs nominal "
        f"{esc.get('n_nominal_obs','?')} (ratio {esc.get('ratio','?'):.4f}) → correlation-limited, not data-deluge.",
        f"Starve-data (1 build, 40-100 Hz): see blind3_companions.json. Grid-invariance: blind3_gridinv.json.",
        "",
        "BLINDNESS: consumed ONLY codex_truth/dataset/. Sealed truth NOT opened. Master scores vs sealed truth.",
    ], size=13)

    prs.save(str(REP / "packet.pptx"))
    print("wrote", REP / "packet.pptx")


if __name__ == "__main__":
    main()
