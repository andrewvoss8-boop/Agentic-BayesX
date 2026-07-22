#!/usr/bin/env python3
"""Build the ShockSat advisor closure brief and its report-native figures.

Editorial synthesis only. All numbers are loaded from frozen, checker-backed
artifacts; this script performs no inference, eigensolve, or new scoring.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from matplotlib.patches import FancyBboxPatch, Patch
import numpy as np
from docx import Document
from docx.enum.section import WD_SECTION
from docx.enum.table import WD_CELL_VERTICAL_ALIGNMENT, WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Inches, Pt, RGBColor


HERE = Path(__file__).resolve()
WORK = HERE.parent.parent
REPO = HERE.parents[4]
REPORTS = REPO / "artifacts" / "reports"
OUT = WORK / "out"
FIG = WORK / "figures"
DOCX = WORK / "ShockSat_Bayesian_FEM_StatFEM_closure_brief.docx"
MD = WORK / "ShockSat_Bayesian_FEM_StatFEM_closure_brief.md"

A = REPORTS / "shocksat_closure_analyses_20260722" / "out"
A1_PATH = A / "a1_subspace.json"
A2_PATH = A / "a2_sigma_f_sweep.json"
A3_PATH = A / "a3_calibration_table.json"
A4_PATH = A / "a4_profile_likelihood.json"
A5_PATH = A / "a5_phase_diagnostic.json"
DAMP_PATH = REPORTS / "shocksat_latent_force_damping_20260623" / "out" / "layer1_nuts.json"
DAMP_PACKET = REPORTS / "shocksat_latent_force_damping_20260623" / "packet.md"
FRF_CACHE = REPORTS / "statfem_real_validation_20260617" / "out" / "mc_cache.npz"
PILOT_PATH = REPORTS / "shocksat_modelform_pilot_20260716" / "out" / "verdicts.json"
EVID_PATH = REPORTS / "shocksat_composite_bakeoff_20260702" / "out" / "tier3_evidence.json"
TIER_PATH = REPORTS / "shocksat_netcg_validated_port_20260716" / "out" / "verdicts_S3S4.json"

NAVY = "17324D"
BLUE = "2A648E"
TEAL = "1F7A78"
AMBER = "B46A16"
PALE_BLUE = "EAF2F7"
PALE_AMBER = "FFF3DF"
PALE_GREY = "F2F4F5"
INK = "20252A"
GREY = "5E6872"
WHITE = "FFFFFF"


def load(path: Path) -> dict:
    return json.loads(path.read_text())


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def rgb(hex_color: str) -> RGBColor:
    return RGBColor.from_string(hex_color)


def shade(cell, fill: str) -> None:
    tc_pr = cell._tc.get_or_add_tcPr()
    shd = tc_pr.find(qn("w:shd"))
    if shd is None:
        shd = OxmlElement("w:shd")
        tc_pr.append(shd)
    shd.set(qn("w:fill"), fill)


def set_cell_margins(cell, top=55, start=70, bottom=55, end=70) -> None:
    tc = cell._tc
    tc_pr = tc.get_or_add_tcPr()
    tc_mar = tc_pr.first_child_found_in("w:tcMar")
    if tc_mar is None:
        tc_mar = OxmlElement("w:tcMar")
        tc_pr.append(tc_mar)
    for side, value in (("top", top), ("start", start), ("bottom", bottom), ("end", end)):
        node = tc_mar.find(qn(f"w:{side}"))
        if node is None:
            node = OxmlElement(f"w:{side}")
            tc_mar.append(node)
        node.set(qn("w:w"), str(value))
        node.set(qn("w:type"), "dxa")


def configure(doc: Document) -> None:
    sec = doc.sections[0]
    sec.top_margin = Inches(0.52)
    sec.bottom_margin = Inches(0.50)
    sec.left_margin = Inches(0.62)
    sec.right_margin = Inches(0.62)
    sec.header_distance = Inches(0.20)
    sec.footer_distance = Inches(0.22)
    styles = doc.styles
    normal = styles["Normal"]
    normal.font.name = "Arial"
    normal.font.size = Pt(9.2)
    normal.font.color.rgb = rgb(INK)
    normal.paragraph_format.space_after = Pt(3.6)
    normal.paragraph_format.line_spacing = 1.04
    for name, size, color in (("Title", 22, NAVY), ("Heading 1", 15, NAVY), ("Heading 2", 11.2, BLUE)):
        st = styles[name]
        st.font.name = "Arial"
        st.font.size = Pt(size)
        st.font.bold = True
        st.font.color.rgb = rgb(color)
        st.paragraph_format.space_before = Pt(5)
        st.paragraph_format.space_after = Pt(4)
        st.paragraph_format.keep_with_next = True
    styles["Heading 1"].paragraph_format.page_break_before = False


def set_repeat_table_header(row) -> None:
    tr_pr = row._tr.get_or_add_trPr()
    tbl_header = OxmlElement("w:tblHeader")
    tbl_header.set(qn("w:val"), "true")
    tr_pr.append(tbl_header)


def add_table(doc: Document, headers: list[str], rows: list[list[str]], widths=None, font=7.45) -> None:
    table = doc.add_table(rows=1, cols=len(headers))
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    table.autofit = False
    table.style = "Table Grid"
    hdr = table.rows[0]
    set_repeat_table_header(hdr)
    for i, text in enumerate(headers):
        cell = hdr.cells[i]
        shade(cell, NAVY)
        cell.vertical_alignment = WD_CELL_VERTICAL_ALIGNMENT.CENTER
        p = cell.paragraphs[0]
        p.paragraph_format.space_after = Pt(0)
        r = p.add_run(text)
        r.bold = True
        r.font.color.rgb = rgb(WHITE)
        r.font.size = Pt(font)
    for ridx, row in enumerate(rows):
        cells = table.add_row().cells
        for i, text in enumerate(row):
            if ridx % 2 == 1:
                shade(cells[i], PALE_GREY)
            cells[i].vertical_alignment = WD_CELL_VERTICAL_ALIGNMENT.CENTER
            p = cells[i].paragraphs[0]
            p.paragraph_format.space_after = Pt(0)
            for j, part in enumerate(str(text).split("**")):
                r = p.add_run(part)
                r.bold = j % 2 == 1
                r.font.size = Pt(font)
            set_cell_margins(cells[i])
    if widths:
        for row in table.rows:
            for cell, width in zip(row.cells, widths):
                cell.width = Inches(width)
    doc.add_paragraph().paragraph_format.space_after = Pt(0)


def p(doc: Document, text: str = "", *, bold_lead: str | None = None, size=9.2,
      color=INK, after=3.6, italic=False, align=None) -> None:
    para = doc.add_paragraph()
    para.paragraph_format.space_after = Pt(after)
    if align is not None:
        para.alignment = align
    if bold_lead and text.startswith(bold_lead):
        r = para.add_run(bold_lead)
        r.bold = True
        rest = text[len(bold_lead):]
        r2 = para.add_run(rest)
        runs = [r, r2]
    else:
        runs = [para.add_run(text)]
    for run in runs:
        run.font.name = "Arial"
        run.font.size = Pt(size)
        run.font.color.rgb = rgb(color)
        run.italic = italic


def bullet(doc: Document, lead: str, body: str, *, size=8.9) -> None:
    para = doc.add_paragraph(style="List Bullet")
    para.paragraph_format.left_indent = Inches(0.22)
    para.paragraph_format.first_line_indent = Inches(-0.12)
    para.paragraph_format.space_after = Pt(2.5)
    r = para.add_run(lead)
    r.bold = True
    r.font.color.rgb = rgb(NAVY)
    r2 = para.add_run(body)
    for run in (r, r2):
        run.font.name = "Arial"
        run.font.size = Pt(size)


def callout(doc: Document, label: str, text: str, fill=PALE_AMBER, accent=AMBER) -> None:
    table = doc.add_table(rows=1, cols=2)
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    table.autofit = False
    set_repeat_table_header(table.rows[0])
    table.columns[0].width = Inches(0.9)
    table.columns[1].width = Inches(6.7)
    c0, c1 = table.rows[0].cells
    for c in (c0, c1):
        shade(c, fill)
        set_cell_margins(c, 80, 100, 80, 100)
    r = c0.paragraphs[0].add_run(label)
    r.bold = True
    r.font.color.rgb = rgb(accent)
    r.font.size = Pt(9)
    r = c1.paragraphs[0].add_run(text)
    r.font.size = Pt(9)
    r.font.color.rgb = rgb(INK)


def add_footer(doc: Document) -> None:
    for section in doc.sections:
        fp = section.footer.paragraphs[0]
        fp.clear()
        fp.alignment = WD_ALIGN_PARAGRAPH.RIGHT
        r = fp.add_run("ShockSat closure brief  |  Andrew Voss  |  22 July 2026  |  ")
        r.font.name = "Arial"
        r.font.size = Pt(7.5)
        r.font.color.rgb = rgb(GREY)
        begin = OxmlElement("w:fldChar")
        begin.set(qn("w:fldCharType"), "begin")
        instr = OxmlElement("w:instrText")
        instr.set(qn("xml:space"), "preserve")
        instr.text = "PAGE"
        end = OxmlElement("w:fldChar")
        end.set(qn("w:fldCharType"), "end")
        r._r.append(begin)
        r._r.append(instr)
        r._r.append(end)


def set_alt_text(inline_shape, title: str, description: str) -> None:
    doc_pr = inline_shape._inline.docPr
    doc_pr.set("title", title)
    doc_pr.set("descr", description)


def add_figure(doc: Document, path: Path, width: float, caption: str, alt: str) -> None:
    para = doc.add_paragraph()
    para.alignment = WD_ALIGN_PARAGRAPH.CENTER
    para.paragraph_format.space_after = Pt(2)
    shape = para.add_run().add_picture(str(path), width=Inches(width))
    set_alt_text(shape, path.stem, alt)
    cp = doc.add_paragraph()
    cp.paragraph_format.space_after = Pt(4)
    cp.paragraph_format.keep_together = True
    r = cp.add_run(caption)
    r.font.name = "Arial"
    r.font.size = Pt(7.7)
    r.font.italic = True
    r.font.color.rgb = rgb(GREY)


def page(doc: Document, title: str, kicker: str | None = None) -> None:
    doc.add_page_break()
    doc.add_heading(title, level=1)
    if kicker:
        p(doc, kicker, size=8.5, color=GREY, after=5, italic=True)


def make_method_map(path: Path) -> None:
    fig, ax = plt.subplots(figsize=(11, 3.35))
    ax.set_xlim(0, 11)
    ax.set_ylim(0, 3.35)
    ax.axis("off")

    def box(x, y, w, h, text, fc, ec=NAVY, fs=9.2):
        patch = FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.04,rounding_size=0.06",
                               facecolor=fc, edgecolor=f"#{ec}", linewidth=1.0)
        ax.add_patch(patch)
        ax.text(x + w / 2, y + h / 2, text, ha="center", va="center", fontsize=fs, color=f"#{INK}")

    def arrow(x0, y0, x1, y1, color=BLUE):
        ax.annotate("", xy=(x1, y1), xytext=(x0, y0),
                    arrowprops=dict(arrowstyle="-|>", color=f"#{color}", lw=1.2))

    ax.text(0.15, 3.05, "Research sequence from the original StatFEM question", fontsize=11.5,
            weight="bold", color=f"#{NAVY}")
    box(0.2, 1.85, 1.65, 0.72, "Reconstruct\nShockSat test case", f"#{PALE_BLUE}", fs=8.8)
    box(2.25, 1.85, 2.05, 0.72, "Update stiffness from\n18 modal frequencies", f"#{PALE_BLUE}", fs=8.6)
    box(4.7, 1.85, 1.8, 0.72, "Propagate parameter\nuncertainty to FRFs", f"#{PALE_BLUE}", fs=8.8)
    box(6.9, 1.85, 1.85, 0.72, "Add response-level\nmodel discrepancy", f"#{PALE_BLUE}", fs=8.8)
    box(9.15, 1.85, 1.65, 0.72, "Check held-out\nchannels and loads", f"#{PALE_AMBER}", AMBER, fs=8.6)
    for a, b in ((1.85, 2.25), (4.3, 4.7), (6.5, 6.9), (8.75, 9.15)):
        arrow(a, 2.21, b, 2.21)
    ax.text(0.15, 1.18, "When response errors remained, I changed the question", fontsize=10.5,
            weight="bold", color=f"#{NAVY}")
    box(0.2, 0.23, 2.15, 0.68, "Try response data directly\nFRF, phase, MAC, damping", f"#{PALE_GREY}", fs=8.5)
    box(2.95, 0.23, 2.15, 0.68, "Test discrepancy models\nand likelihood assumptions", f"#{PALE_GREY}", fs=8.5)
    box(5.7, 0.23, 2.0, 0.68, "Diagnose residuals\nand information limits", f"#{PALE_GREY}", fs=8.7)
    box(8.3, 0.23, 2.5, 0.68, "Test model-form edits\nconnectivity, mesh, elements, geometry", f"#{PALE_AMBER}", AMBER, fs=8.1)
    for a, b in ((2.35, 2.95), (5.1, 5.7), (7.7, 8.3)):
        arrow(a, 0.57, b, 0.57, AMBER)
    fig.text(0.02, 0.015, "Source: frozen ShockSat study records. Run-specific diagram; no literature figure was copied.",
             fontsize=7.8, color=f"#{GREY}")
    fig.savefig(path, dpi=220, bbox_inches="tight", facecolor="white")
    plt.close(fig)


def make_modal_figure(path: Path, a1: dict, a2: dict) -> None:
    plt.rcParams.update({"font.size": 9, "axes.spines.top": False, "axes.spines.right": False,
                         "legend.frameon": False, "axes.edgecolor": "#666666"})
    fig, axes = plt.subplots(1, 2, figsize=(10.8, 4.35), gridspec_kw={"width_ratios": [1.02, 1.15]})
    fig.subplots_adjust(left=0.075, right=0.985, top=0.82, bottom=0.22, wspace=0.30)
    vals = np.array(a1["eigenvalues_ascending"])
    cis = np.array(a1["eigenvalues_ci95"])
    x = np.arange(1, len(vals) + 1)
    colors = [f"#{TEAL}" if v < 0.5 else "#9AA1A6" for v in vals]
    axes[0].errorbar(x, vals, yerr=np.vstack([vals - cis[:, 0], cis[:, 1] - vals]), fmt="none",
                     ecolor="#7A848C", elinewidth=0.8, capsize=2)
    axes[0].scatter(x, vals, c=colors, s=34, zorder=3)
    axes[0].axhline(1.0, color="#7A848C", ls=(0, (4, 3)), lw=1)
    axes[0].axhline(0.5, color=f"#{TEAL}", ls=(0, (2, 2)), lw=0.9)
    axes[0].set_xlabel("prior-whitened log-θ direction")
    axes[0].set_ylabel("posterior variance / prior variance")
    axes[0].set_xticks(x)
    axes[0].set_ylim(0, 1.38)
    axes[0].set_title("A. Four combinations contract", loc="left", color=f"#{INK}", fontsize=10.5)
    axes[0].text(4.25, 0.13, "4 learned combinations", color=f"#{TEAL}", fontsize=8.3)
    axes[0].text(8.95, 1.04, "prior-like", color="#6D747A", fontsize=8.3, ha="right")

    keys = ["hn002", "hn005_reference", "hn015", "hc005", "exp005"]
    labels = ["HalfNormal .02", "HalfNormal .05", "HalfNormal .15", "HalfCauchy .05", "Exponential .05"]
    y = np.arange(5)[::-1]
    for yi, key, label in zip(y, keys, labels):
        v = a2["variants"][key]
        med = 100 * v["sigma_f_median"]
        lo, hi = [100 * q for q in v["sigma_f_ci95"]]
        ok = v["convergence"]["gate_pass"]
        col = f"#{TEAL}" if ok else f"#{AMBER}"
        axes[1].plot([lo, hi], [yi, yi], color=col, lw=1.5 if ok else 1.0, alpha=1 if ok else 0.62)
        axes[1].scatter([med], [yi], s=42, facecolor=col if ok else "white", edgecolor=col, zorder=3)
        if not ok:
            rh = v["convergence"]["worst_rhat"]
            ess = v["convergence"]["min_ess"]
            axes[1].text(hi + 0.18, yi, f"R̂ {rh:.3f}, ESS {ess:.0f}", va="center", fontsize=7.4,
                         color=f"#{AMBER}")
    axes[1].axvspan(4.2, 4.8, color=f"#{PALE_BLUE}", zorder=0)
    axes[1].set_yticks(y, labels)
    axes[1].set_xlim(2.7, 8.8)
    axes[1].set_xlabel("σf median and 95% interval [% log-frequency]")
    axes[1].set_title("B. Residual floor persists across priors", loc="left", color=f"#{INK}", fontsize=10.5)
    axes[1].grid(True, axis="x", color="#E2E5E7", lw=0.5)
    fig.suptitle("What the modal-frequency data actually identify", x=0.075, y=0.96, ha="left",
                 fontsize=13, color=f"#{INK}")
    fig.text(0.075, 0.055,
             "Source: closure analyses A1/A2. Reference and loose HalfNormal(.15) runs converged. Three sensitivity runs did not; their intervals are not trustworthy. All variants cover 18/18 prior-predictive frequencies.",
             fontsize=7.7, color=f"#{GREY}")
    fig.savefig(path, dpi=240, bbox_inches="tight", facecolor="white")
    plt.close(fig)


def make_profile_figure(path: Path, a4: dict) -> None:
    plt.rcParams.update({"font.size": 9, "axes.spines.top": False, "axes.spines.right": False,
                         "legend.frameon": False, "axes.edgecolor": "#666666"})
    fig, axes = plt.subplots(1, 2, figsize=(10.8, 3.95), sharey=True)
    fig.subplots_adjust(left=0.075, right=0.985, top=0.78, bottom=0.25, wspace=0.16)
    for ax, name, label in zip(axes, ("bottom_box", "top_box"), ("bottom-box scale", "top-box scale")):
        profile = a4["profiles"][name]
        pts = profile["points"]
        theta = np.array([v["theta"] for v in pts])
        lp = np.array([v["profile_logpost_penalized"] for v in pts])
        rel = lp - lp.max()
        ax.plot(theta, rel, color=f"#{BLUE}", lw=1.35)
        maxima = profile["local_maxima_theta"]
        idx = [int(np.argmin(np.abs(theta - m))) for m in maxima]
        ax.scatter(theta[idx], rel[idx], s=25, facecolor=f"#{AMBER}", edgecolor="white", lw=0.4, zorder=3)
        for cm in profile["chain_means_theta"]:
            ax.axvline(cm, color="#6A7278", lw=0.65, alpha=0.65)
        ax.set_xscale("log")
        ax.set_xlabel(label + " θ")
        ax.set_title(f"{label}: {profile['n_local_maxima']} local maxima", loc="left", fontsize=10.3,
                     color=f"#{INK}")
        ax.grid(True, axis="y", color="#E2E5E7", lw=0.5)
    axes[0].set_ylabel("relative profiled log posterior [max = 0]")
    fig.suptitle("The iid whole-FRF target is genuinely multimodal", x=0.075, y=0.95, ha="left",
                 fontsize=13, color=f"#{INK}")
    fig.text(0.075, 0.065,
             "Source: Task Card A A4; 41 log-spaced points per slice, gains and residual scale profiled at every point and gradient-verified. Gray lines are the four stored NUTS chain means. Diagnostic only; the response-level posterior did not converge (worst R̂ 44.7, ESS 2.0).",
             fontsize=7.7, color=f"#{GREY}")
    fig.savefig(path, dpi=240, bbox_inches="tight", facecolor="white")
    plt.close(fig)


def make_frf_figure(path: Path) -> dict:
    cache = np.load(FRF_CACHE, allow_pickle=True)
    freqs = np.asarray(cache["freqs"], float)
    split = next(s for s in cache["splits"] if int(s["seed"]) == 10)
    by_daq = {int(c["daq"]): c for c in split["chans"]}
    panels = [("Update moves toward data", by_daq[20]), ("Persistent model-to-test miss", by_daq[24])]
    fig, axes = plt.subplots(1, 2, figsize=(10.8, 4.55), sharex=True, sharey=True)
    fig.subplots_adjust(left=0.083, right=0.985, top=0.72, bottom=0.20, wspace=0.12)
    for ax, (story, channel) in zip(axes, panels):
        measured = np.asarray(channel["tru"], float)
        original = np.asarray(channel["det"], float)
        param = np.asarray(channel["param"], float)
        total = np.asarray(channel["total"], float)
        ax.fill_between(freqs, total[0], total[1], color="#EFC17D", alpha=0.46, lw=0, zorder=1)
        ax.fill_between(freqs, param[0], param[2], color="#8FC1E3", alpha=0.74, lw=0, zorder=2)
        ax.plot(freqs, original, color="#7A7F83", lw=1.05, ls=(0, (4, 2)), zorder=3)
        ax.plot(freqs, param[1], color=f"#{BLUE}", lw=1.5, zorder=4)
        ax.plot(freqs, measured, color="#171717", lw=1.1, zorder=5)
        ax.set_xscale("log")
        ax.set_yscale("log")
        ax.set_xlim(45, 260)
        ax.grid(True, axis="y", color="#E2E5E7", lw=0.45)
        ax.set_xlabel("frequency [Hz, log]")
        ax.set_title(f"DAQ {int(channel['daq'])}: {story}", loc="left", fontsize=10.3, color=f"#{INK}")
    axes[0].set_ylabel("accelerance magnitude |H| [g/lbf, log]")
    handles = [
        Line2D([0], [0], color="#171717", lw=1.2, label="measured data"),
        Line2D([0], [0], color="#7A7F83", lw=1.1, ls=(0, (4, 2)), label="original FEM"),
        Line2D([0], [0], color=f"#{BLUE}", lw=1.5, label="updated median"),
        Patch(facecolor="#8FC1E3", alpha=0.74, label="parameter 5–95%"),
        Patch(facecolor="#EFC17D", alpha=0.46, label="parameter + discrepancy 5–95%"),
    ]
    fig.legend(handles=handles, loc="upper left", bbox_to_anchor=(0.08, 0.90), ncol=3, fontsize=8.1,
               columnspacing=1.15, handlelength=2.5)
    fig.suptitle("The modular twin is calibrated by widening, not by repairing every FRF", x=0.083, y=0.97,
                 ha="left", fontsize=13, color=f"#{INK}")
    fig.text(0.083, 0.055,
             f"Frozen split seed 10; 45–260 Hz. Modal NUTS stage converged (max R̂ {float(split['rhat']):.4f}). Outer band adds marginal log-amplitude discrepancy σ = {float(split['sig']):.3f} estimated on observed channels. It is a two-stage modular prediction, not a jointly converged whole-FRF StatFEM posterior.",
             fontsize=7.7, color=f"#{GREY}")
    fig.savefig(path, dpi=240, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    return {"split_seed": 10, "rhat": float(split["rhat"]), "sigma": float(split["sig"]),
            "source_sha256": sha256(FRF_CACHE), "daqs": [20, 24], "band_hz": [45, 260]}


def write_md(a1, a2, a3, a4, a5, pilot) -> None:
    text = """# Evaluating StatFEM on ShockSat: What I Tried and What I Need Help Deciding

**Advisor closure brief for Ilias Bilionis — Andrew Voss — 22 July 2026**

## Where this work started

The last project document you reviewed was my “Stress Testing StatFEM” proposal. Your guidance was: build and evaluate the StatFEM approach, identify its gaps, and suggest improvements. You also cautioned that validation might not be possible if the method itself was not working. I treated that as the research question.

The proposal aimed to update an aerospace finite-element model from vibration data, represent the difference between the FEM and the real structure, and propagate both sources of uncertainty to a structural load. I moved to NASA's public ShockSat test article because it offered a realistic FEM, a modal survey, and impact-hammer response data on the same structure.

I have less than one month remaining in my PSL studies. I want your direction on how to close this work, what I should learn from the problem choice, and which parts merit documentation for the field and the lab.

## How the work evolved

| Step | Why I did it | What I tried |
|---|---|---|
| 1. Establish a real test case | The earlier synthetic and small-model examples could test software, but they could not expose the problems created by a realistic aerospace FEM and sparse test data. | Reconstructed the ShockSat FEM/test alignment and defined modal, FRF, held-out-response, and load quantities. |
| 2. Start with modal updating | Natural frequencies offered the cleanest common observable between the FEM and test. This stage also checked the FEM assembly and Bayesian sampler before adding response discrepancy. | Inferred nine stiffness-group scales and a residual frequency-error scale from 18 paired modes using NUTS. |
| 3. Move to response-level StatFEM | Modal frequencies do not determine channel amplitudes, phase, damping, or forcing participation. The original objective required response prediction. | Tested whole-FRF magnitude, phase, MAC/shape, damping, Beck-style shape inference, and several discrepancy formulations. |
| 4. Test prediction rather than fit | A posterior fit to the data used for updating would not show whether the method supports an engineering decision. | Held out response channels and drive locations, propagated predictions to a load proxy, and compared them with the existing FEM + 6 dB practice. |
| 5. Investigate model form | The fixed nine-parameter FEM class could move resonance frequencies but left channel-dependent response errors. | Tested changes to connectivity, mesh density, element formulation, and geometry, then compared an agent-guided search with equal-budget random search. |

## What I modeled and measured

| Term | Definition used here |
|---|---|
| FEM / StatFEM | Finite-element model / statistical finite-element method. StatFEM treats the FEM prediction, model discrepancy, and observation process as one probabilistic data-generating model. |
| FRF / H1 | Frequency-response function; here accelerance magnitude, response acceleration divided by impact force, in g/lbf. H1 is the force-referenced estimator. |
| NUTS / R-hat / ESS | No-U-Turn Sampler; a gradient-based Hamiltonian Monte Carlo method. R-hat compares between- and within-chain variation; effective sample size (ESS) estimates independent-equivalent draws. Convergence criterion: R-hat no greater than 1.05, ESS at least 200, divergence fraction below 2%. |
| IFT / β | “Inferred physics trust” comparator; β is its bounded physics-trust multiplier. This TMCMC arm was reproducible but produced over-wide band GRMS and is not the delivered method. |
| Model-form score | P1-prime: median per-channel Pearson correlation of log10 FRF magnitude below 200 Hz, averaged over four leave-one-drive-out folds; unitless. |
| Counts and bands | Modal update: 18 paired frequencies, 9 stiffness scales, 4 NUTS chains by 1,000 retained draws. Whole-FRF diagnosis: 6,525 log-magnitude points from 3 training drives, 45–400 Hz. Working-twin figure: one article, split seed 10, held-out DAQ 20/24, 45–260 Hz, 5th–95th percentile bands. Load comparison: five measured held-out drives per shear axis; normal-Z is synthetic self-consistency only. |

## Bayesian model used for the first update

For modal pair m, the implemented likelihood was `log f_meas,m ~ Normal(log f_pred,m(theta), sigma_f)`. The implementation was already in this direction; the earlier report wrote it backwards. The nine positive stiffness scales had lognormal priors centered at the inherited FEM. The primary run inferred those scales and the iid log-frequency residual sigma_f with NUTS. It used modal frequencies, not FRF amplitudes, and did not use MAC as a generative shape likelihood.

This first model estimates stiffness from modal frequencies. It cannot learn channel-specific response amplitude, phase, or forcing participation because those quantities do not enter its likelihood. I therefore treated modal updating as the first stage of the StatFEM evaluation, then tested response likelihoods and discrepancy models separately.

## Research sequence

![Research sequence from modal updating through response evaluation and model-form remodeling](figures/fig1_method_map.png)

## What the modal update showed

![Prior-whitened modal contraction and sigma_f prior sensitivity](figures/fig2_modal_identification.png)

The four contracted prior-whitened log-stiffness directions have posterior/prior variance ratios 0.0187, 0.0286, 0.2593, and 0.3546. They are dominated by bottom/top box, plates, and cross-beam combinations. The remaining five directions are prior-like (0.8718–1.1657). This is a subspace result; it does not establish nine separately identifiable parameters.

The frozen HalfNormal(0.05) reference reproduces sigma_f = 4.60% versus 4.63% stored, with worst R-hat 1.009 and minimum ESS 464. A looser converged HalfNormal(0.15) gives 4.80%. Across all five priors the medians span 4.16–4.82%, and every prior predictive check covers 18/18 frequencies. Three sensitivity runs did not converge; their intervals are not trustworthy.

## Response-level StatFEM attempts and recovered diagnostics

![Profile likelihood diagnosis of whole-FRF nonconvergence](figures/fig3_wholefrf_profile.png)

The iid whole-FRF likelihood used 6,525 log-magnitude observations, per-drive gains, a residual scale, and nine stiffness scales. With gains and residual scale profiled at each of 41 points, the two most sensitive parameter slices each contain about 10 local maxima. The stored chains occupy different modes (worst R-hat 44.7, ESS 2.0). That is evidence of global under-identification/multimodality for this likelihood, not proof that response-level StatFEM is generally invalid.

The original phase diagnostic was found rather than re-derived. On one single-hit dataset (46 channels, 12 matched modes), circular variance was 0.854 and the complex parameter slice was no sharper than magnitude. A separate time-domain damping study did converge for 14/16 modes (worst R-hat 1.020, minimum ESS 250; damping 0.33–0.76% of critical), but replacing the nominal damping did not solve the envelope decision. The FEM was more heavily damped than the measured article, so the correction raised peaks; response-shape error remained binding.

### Response methods I tried

| Method | Data and Bayesian target | Why I tried it | Result and limitation |
|---|---|---|---|
| Modal-frequency NUTS | 18 paired log frequencies; 9 stiffness scales plus sigma_f | Establish a stable parameter-updating baseline before adding response discrepancy | Converged reference; it estimates FEM parameters from modal frequencies |
| Frequency + MAC arm | Modal frequencies plus a MAC pseudo-likelihood | Test whether mode-shape agreement adds information beyond frequencies | 82 divergences in the original arm; sensitivity study only |
| Beck-style inferred shape field | Modal frequencies/shapes with the shape field itself inferred | Test whether allowing the measured shape field to move could sharpen response amplitudes | Useful amplitude/shape diagnostic; did not support the load objective |
| Modular working twin | Converged modal posterior, then observed-channel marginal discrepancy | Propagate the stable parameter posterior while acknowledging remaining response error | Two-stage construction; the discrepancy was not sampled jointly with the parameters |
| iid whole-FRF NUTS | Whole log-magnitude curves; stiffness, gain, residual | Use the response curves directly instead of modal summaries | Not converged; no trustworthy joint interval |
| Free-discrepancy M2 / bounded IFT | TMCMC alternatives for a response discrepancy / physics-trust term | Test free and bounded ways of allocating error between parameters and discrepancy | Neither produced a sharp, validated load product |
| Evidence ranking | Matched squared frequencies plus MAC; type-II ML residual scales | Compare FEM classes under the same modal target | +54.02 was an approximate ranking diagnostic, not held-out validation |
| Schneider-style correlated FRF surrogate | Frequency/space-correlated error with rational surrogate | Consider a literature-grounded way to model correlated FRF error | Not implemented in this project |

## The retained working twin

![Good and bad held-out FRF channels with separated uncertainty bands](figures/fig4_modular_frf.png)

The inner blue band propagates the converged modal-parameter posterior. The outer amber band then adds a marginal log-amplitude discrepancy estimated on observed channels and transferred to held-out channels. DAQ 20 moves toward the measurement. DAQ 24 does not. The outer band can envelope a structurally wrong mean, but that is not the same as repairing the FEM.

The posterior mean moves only as far as the information and mechanisms in the modal likelihood allow; a stronger or weaker discrepancy prior cannot add missing channel physics. The band is wide because the observed response mismatch requires a large discrepancy, not because NUTS failed in the first stage. A structured discrepancy could redistribute uncertainty, but orthogonal discrepancy, coherence-derived covariance, and the Schneider surrogate remain unimplemented future options.

## Load result: calibration versus usefulness

| Axis / evidence | FEM + 6 dB coverage; width | Parameter-only coverage; width | Discrepancy-aware coverage; width | Measured CRPS: baseline -> discrepancy-aware |
|---|---:|---:|---:|---:|
| Shear X, measured held-out drives | 0.865; 1.000 | 0.984; 1.068 | 0.995; 1.508 | 1.252 -> 1.137 |
| Shear Y, measured held-out drives | 0.706; 1.000 | 0.947; 1.215 | 0.982; 2.301 | 0.771 -> 0.709 |
| Normal Z, synthetic self-consistency only | 0.738; 1.000 | 0.969; 1.016 | 0.987; 2.526 | no measured validation |

Coverage rises, and the discrepancy-aware method has lower mean continuous ranked probability score (CRPS; lower is better) than FEM + 6 dB on both measured shear axes. It wins 8/10 measured drive-axis cells under all three baseline-envelope probability conventions. The method achieves this calibration with bands 1.51 times the baseline width in shear X and 2.30 times in shear Y. That width still prevents industry use.

The delivered normal-Z reference width is 2.526 times FEM + 6 dB. The later tier-updated configuration is 2.958 because observed cross-drive log-amplitude scatter (1.393) exceeded the assumed unmeasured-tier value (0.80); these are different configurations, not inconsistent reproductions. Normal-Z remains synthetic self-consistency, not validation.

## Why I pivoted to model-form remodeling

Parameter updating changes values inside a fixed FEM class. The residual evidence instead pointed to missing or wrong response mechanisms: channel-dependent participation, interface representation, element formulation, geometry idealization, and local shape fidelity. “Agentic remodeling” therefore means a bounded loop over registered model-form edits: propose -> build -> verify mechanics -> fit continuous parameters -> score held-out data -> diagnose -> revise. The agent proposes; deterministic code owns mesh construction, mechanical checks, data splits, budgets, and scoring.

The pilot tested connectivity, mesh density, element formulation, and geometry with exact candidate-basis scoring. All four classes had positive class-mean controls. However, this study failed to demonstrate an agent advantage. The preregistered primary comparison was best-exact versus best-exact: agent minus random = -0.0077 +/- 0.0177 in unitless score, below the one-standard-error minimum detectable effect of 0.0177. The secondary track-mean difference was +0.0028 +/- 0.0056 and also did not clear its bar. Model-form freedom was a useful lever in this pilot. The agent-guided search did not outperform the equal-budget random search.

The future harness is a CLI-mediated version of this same loop, with versioned candidate and diagnostic schemas and immutable verifier controls. `remodelctl` is not yet the scientific contribution and is not required to close the ShockSat result. It is a possible way to make later agent training reproducible.

## Work products I could preserve, with their limits

| Work product | Limit that must travel with it |
|---|---|
| A real-data separation between converged modal-frequency Bayesian updating and non-converged response-level inference | One ShockSat article; no build-to-build or flight-to-flight variability |
| Prior-whitened subspace diagnosis showing four learned combinations | Not nine raw-parameter identifiability claims |
| Prior-sensitivity analysis showing that the modal residual floor survives a loose converged prior | Three of five sensitivity variants did not converge |
| A modular predictive construction that separates parameter and output-discrepancy bands | Wide marginal discrepancy; not a joint StatFEM posterior |
| Matched coverage and proper-score comparison against FEM + 6 dB | Normal-Z has no measured answer key; shear gain costs width |
| A controlled model-form search with exact-basis and random controls | Positive model-form classes, but no demonstrated agent advantage |

Classical FEM-updating literature limits parameter correction to mechanisms represented by the chosen model class [2–3]. StatFEM and computer-model calibration add discrepancy, while flexible discrepancy can confound physical parameters and widen prediction [4–6]. Held-out prediction answers a different question from conditional marginal likelihood [7–8]. NUTS diagnostics determine whether the reported Monte Carlo intervals can be trusted [9–10]. Schneider's correlated-error surrogate offers one possible next method; I did not implement it [11].

## Guidance I need for the final month

1. Is the strongest closure a methodological evaluation of where modal updating stops being response-level StatFEM, rather than another attempt to force a converged whole-FRF posterior?
2. Which two or three contributions above are strong enough to document as lab contributions, and which are merely project lessons?
3. Looking back, was ShockSat/indirect load prediction the wrong problem framing for evaluating StatFEM, or was exposing the observability and discrepancy limits a worthwhile outcome?
4. What final artifact would best capture the personal lesson: a short paper-style report, a reproducible negative-result case study, or a lab methods note and harness?

## References

1. NASA Engineering and Safety Center Academy. *ShockSat*. https://nescacademy.nasa.gov/workshops/ShockSat
2. Mottershead, J. E., & Friswell, M. I. (1993). Model Updating in Structural Dynamics: A Survey. *Journal of Sound and Vibration*, 167(2), 347–375. https://doi.org/10.1006/jsvi.1993.1340
3. Mottershead, J. E., Link, M., & Friswell, M. I. (2011). The sensitivity method in finite element model updating: A tutorial. *MSSP*, 25(7), 2275–2296. https://doi.org/10.1016/j.ymssp.2010.10.012
4. Beck, J. L., & Katafygiotis, L. S. (1998). Updating Models and Their Uncertainties. I. *Journal of Engineering Mechanics*, 124(4), 455–461. https://doi.org/10.1061/(ASCE)0733-9399(1998)124:4(455)
5. Girolami, M., Febrianto, E., Yin, G., & Cirak, F. (2021). The statistical finite element method for coherent synthesis of observation data and model predictions. *CMAME*, 375, 113533. https://doi.org/10.1016/j.cma.2020.113533
6. Brynjarsdottir, J., & O'Hagan, A. (2014). Learning about physical parameters: the importance of model discrepancy. *Inverse Problems*, 30(11), 114007. https://doi.org/10.1088/0266-5611/30/11/114007
7. Mthembu, L., Marwala, T., Friswell, M. I., & Adhikari, S. (2011). Model selection in finite element model updating using the Bayesian evidence statistic. *MSSP*, 25(7), 2399–2412. https://doi.org/10.1016/j.ymssp.2011.04.001
8. Vehtari, A., Gelman, A., & Gabry, J. (2017). Practical Bayesian model evaluation using leave-one-out cross-validation and WAIC. *Statistics and Computing*, 27, 1413–1432. https://doi.org/10.1007/s11222-016-9696-4
9. Hoffman, M. D., & Gelman, A. (2014). The No-U-Turn Sampler. *JMLR*, 15, 1593–1623. https://www.jmlr.org/papers/v15/hoffman14a.html
10. Vehtari, A., Gelman, A., Simpson, D., Carpenter, B., & Bürkner, P.-C. (2021). Rank-normalization, folding, and localization: An improved R-hat. *Bayesian Analysis*, 16(2), 667–718. https://doi.org/10.1214/20-BA1221
11. Schneider, R., Papaioannou, I., & Straub, D. (2022). Bayesian parameter updating in linear structural dynamics with frequency transformed data using rational surrogate models. *MSSP*, 166, 108407. https://doi.org/10.1016/j.ymssp.2021.108407
12. Kennedy, M. C., & O'Hagan, A. (2001). Bayesian calibration of computer models. *JRSS B*, 63(3), 425–464. https://doi.org/10.1111/1467-9868.00294
13. ASME V&V 10-2019 (R2025). *Standard for Verification and Validation in Computational Solid Mechanics*. https://www.asme.org/codes-standards/find-codes-standards/standard-for-verification-and-validation-in-computational-solid-mechanics
"""
    MD.write_text(text)


def build_doc(a1, a2, a3, a4, a5, pilot) -> None:
    doc = Document()
    configure(doc)
    add_footer(doc)

    # Page 1 — memo masthead + the advisor's last context and research sequence.
    top = doc.add_table(rows=1, cols=2)
    top.autofit = False
    set_repeat_table_header(top.rows[0])
    top.columns[0].width = Inches(5.6)
    top.columns[1].width = Inches(2.0)
    for c in top.rows[0].cells:
        shade(c, NAVY)
        set_cell_margins(c, 90, 120, 90, 120)
    r = top.cell(0, 0).paragraphs[0].add_run("SHOCKSAT  |  ADVISOR CLOSURE BRIEF")
    r.bold = True; r.font.color.rgb = rgb(WHITE); r.font.size = Pt(9)
    top.cell(0, 1).paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.RIGHT
    r = top.cell(0, 1).paragraphs[0].add_run("22 JULY 2026")
    r.bold = True; r.font.color.rgb = rgb(WHITE); r.font.size = Pt(9)
    doc.add_paragraph().paragraph_format.space_after = Pt(0)
    t = doc.add_paragraph()
    t.paragraph_format.space_after = Pt(2)
    r = t.add_run("Evaluating StatFEM on ShockSat")
    r.font.name = "Arial"; r.font.size = Pt(21); r.font.bold = True; r.font.color.rgb = rgb(NAVY)
    p(doc, "What I tried, why the work changed direction, and guidance I need for the final month", size=11.2, color=BLUE, after=4)
    p(doc, "Andrew Voss  |  for Ilias Bilionis", size=8.8, color=GREY, after=8)
    callout(doc, "STARTING POINT", "The last project document you reviewed was my “Stress Testing StatFEM” proposal. Your guidance was to build and evaluate the approach, identify its gaps, and suggest improvements. You cautioned that validation might not be possible if the method itself was not working. I treated that as the research question.", PALE_BLUE, BLUE)
    doc.add_heading("Where this work started", level=1)
    p(doc, "The proposal aimed to update an aerospace finite-element model from vibration data, represent the difference between the FEM and the real structure, and propagate both sources of uncertainty to a structural load. I moved to NASA's public ShockSat test article because it offered a realistic FEM, a modal survey, and impact-hammer response data on the same structure. I now have less than one month remaining in my PSL studies and need your direction on how to close the work and what lessons and contributions are worth documenting.", size=8.8)
    doc.add_heading("How the work evolved", level=1)
    add_table(doc, ["Step", "Why", "What I tried"], [
        ["1. Real test case", "Expose problems hidden by synthetic examples", "Aligned the ShockSat FEM, modal survey, impact FRFs, held-out responses, and load quantities."],
        ["2. Modal update", "Start with the cleanest FEM/test observable", "Inferred 9 stiffness-group scales and a residual frequency-error scale from 18 modal pairs using NUTS."],
        ["3. Response StatFEM", "Modal frequencies do not determine amplitude, phase, damping, or participation", "Tested FRF magnitude, phase, MAC/shape, damping, Beck-style shape inference, and discrepancy models."],
        ["4. Predictive checks", "Fit alone does not establish engineering usefulness", "Held out channels and drives, propagated to a load proxy, and compared with FEM + 6 dB."],
        ["5. Model form", "The fixed FEM class left channel-dependent errors", "Tested connectivity, mesh, element formulation, and geometry; compared agent-guided and random search."],
    ], [1.25, 2.45, 3.9], font=7.15)

    # Page 2 — definitions + model map.
    page(doc, "1. What I modeled and measured", "The modal update came first; response likelihoods and discrepancy models followed because the original objective required response prediction.")
    rows = [
        ["FEM / StatFEM", "Finite-element model / statistical finite-element method: a probabilistic data-generating model for FEM prediction, model discrepancy, and observations."],
        ["FRF / H1", "Frequency-response function; accelerance magnitude |response acceleration / impact force| [g/lbf]. H1 is the force-referenced estimator."],
        ["NUTS / R-hat / ESS", "No-U-Turn Sampler; gradient-based Hamiltonian Monte Carlo. Convergence criterion: R-hat ≤1.05, ESS ≥200, divergences <2%."],
        ["IFT / β", "Inferred-physics-trust comparator; β is the bounded physics-trust multiplier. Reproducible TMCMC, but over-wide band GRMS."],
        ["Model-form score", "P1′ = median per-channel Pearson correlation of log10 FRF magnitude below 200 Hz, averaged over 4 leave-one-drive-out folds; unitless."],
        ["Counts / bands", "Modal: 18 pairs, 9 stiffness scales, 4×1,000 NUTS draws. Whole FRF: 6,525 points, 3 training drives, 45–400 Hz. Figure 4: split 10, DAQ 20/24, 45–260 Hz, 5th–95th bands. Load: 5 measured held-out drives per shear axis; normal-Z synthetic only."],
    ]
    add_table(doc, ["Term", "Definition used here"], rows, [1.35, 6.25], font=7.25)
    p(doc, "Implemented modal likelihood:", bold_lead="Implemented modal likelihood:", size=8.8, after=1)
    p(doc, "log f_meas,m  ~  Normal(log f_pred,m(θ), σf)", size=10.2, color=NAVY, after=2, align=WD_ALIGN_PARAGRAPH.CENTER)
    p(doc, "The nine positive stiffness scales had lognormal priors centered at the inherited FEM. The primary run inferred them and the iid log-frequency residual σf from modal frequencies. FRF amplitudes did not enter this likelihood, and MAC was not used as a generative shape likelihood.", size=8.4, after=3)
    add_figure(doc, FIG / "fig1_method_map.png", 7.25, "Figure 1. Research sequence from the original StatFEM question through modal updating, response evaluation, and model-form remodeling.", "Flow diagram. The study reconstructs ShockSat, updates stiffness from modal frequencies, propagates uncertainty to FRFs, adds response discrepancy, and checks held-out channels and loads. Remaining response errors lead to response-data experiments, discrepancy tests, residual diagnosis, and model-form edits.")

    # Page 3 — modal analysis.
    page(doc, "2. What the modal update showed", "The reference posterior and loose-prior sensitivity run converged. Three other sensitivity runs did not.")
    add_figure(doc, FIG / "fig2_modal_identification.png", 7.35, "Figure 2. Prior-whitened posterior subspace and σf prior sensitivity. Non-converged variants show their worst diagnostics on the plot; those intervals are not trustworthy.", "Left: nine posterior-to-prior variance ratios with four below one half. Right: five sigma-f prior variants with medians near 4.2 to 4.8 percent; two converged variants are filled and three non-converged variants are hollow with R-hat and ESS labels.")
    add_table(doc, ["Bayesian question", "What the analyses showed"], [
        ["Did the prior simply prevent movement?", "The data contract four prior-whitened log-θ combinations at 0.0187, 0.0286, 0.2593, 0.3546; five directions remain 0.8718–1.1657. This is a subspace result, not nine identifiable marginals."],
        ["Was σf forced by its prior?", "Reference HalfNormal(.05) reproduces 4.60% vs 4.63% stored (R-hat 1.009, ESS 464). A loose converged HalfNormal(.15) gives 4.80%. All five medians span 4.16–4.82%."],
        ["Are the predictive checks obviously inconsistent?", "All five prior-predictive variants cover 18/18 frequencies. The reference posterior-predictive PIT spans 0.079–0.906 without an obvious boundary pile-up."],
        ["What remains unresolved?", "Three sensitivity chains fail convergence. Prior choices for raw θ and the iid residual assumption still matter. I interpret the result only at the level of parameter combinations."],
    ], [2.25, 5.35], font=7.65)
    callout(doc, "INTERPRETATION", "The posterior mean cannot move every FRF toward the data because the likelihood learns resonance locations and only four stiffness combinations. It has no channel-specific participation or amplitude mechanism. Weakening the σf prior does not eliminate the residual floor.", PALE_BLUE, BLUE)

    # Page 4 — response attempts.
    page(doc, "3. Experiments with response data", "Whole-FRF, phase, damping, and discrepancy models followed the modal update.")
    add_figure(doc, FIG / "fig3_wholefrf_profile.png", 7.35, "Figure 3. Profiled iid whole-FRF target. Each sensitive one-parameter slice contains about ten local maxima after optimizing gains and residual scale at every grid point.", "Two relative profile-posterior curves for bottom-box and top-box stiffness scales. Amber points mark roughly ten local maxima in each slice; gray vertical lines show four stored NUTS chain means in separated modes.")
    p(doc, "The iid whole-FRF likelihood used 6,525 log-magnitude observations, per-drive gains, a residual scale, and nine stiffness scales. With gains and residual scale profiled at each of 41 points, both sensitive slices contain about 10 local maxima. The stored chains occupy different modes (worst R-hat 44.7, ESS 2.0). For this likelihood, the profile supports a diagnosis of global under-identification and multimodality. It does not establish a general failure of response-level StatFEM.", size=8.8)
    add_table(doc, ["Recovered diagnostic", "Result", "Meaning"], [
        ["Phase (original artifact found)", "Single hit; 46 channels; 12 modes; circular variance 0.854; complex slice no sharper than magnitude", "Phase did not supply a sharper parameter direction for that dataset."],
        ["Time-domain damping", "14/16 modes converged; worst R-hat 1.020; ESS 250; ζ = 0.33–0.76%", "Damping was measurable, but correcting it raised peaks because the FEM used 1%; the envelope decision did not improve."],
        ["Free discrepancy vs bounded physics trust", "Free variance sought a boundary; bounded alternative reproduced across TMCMC populations", "Different failure modes: confounding/boundary behavior versus reproducible but over-wide prediction."],
    ], [1.65, 2.55, 3.4], font=7.45)
    callout(doc, "LIMIT", "More iterations alone do not address multiple separated likelihood modes or parameter–discrepancy confounding. A different response likelihood/covariance and a better-observed forcing/shape model would be a method change, not a sampler tune-up.", PALE_AMBER, AMBER)

    # Page 5 — method ledger + FRF.
    page(doc, "4. The modular working twin", "The parameter update and response discrepancy were estimated in two stages.")
    add_table(doc, ["Method", "Data / target", "Result and limitation"], [
        ["Modal-frequency NUTS", "18 log-frequency pairs; 9 θ + σf", "The converged parameter stage estimates FEM stiffness from modal frequencies."],
        ["Frequency + MAC arm", "Modal frequencies + MAC pseudo-likelihood", "82 divergences; sensitivity arm only."],
        ["Beck-style inferred shape field", "Infer modal shape field, not only θ", "Useful amplitude/shape diagnostic; did not support the load objective."],
        ["Modular working twin", "Converged modal posterior, then observed-channel discrepancy", "Two-stage prediction; the discrepancy was not sampled jointly with θ."],
        ["iid whole-FRF NUTS", "Whole log-magnitude curves; θ, gains, residual", "Separated modes; no trustworthy posterior interval."],
        ["Free discrepancy / bounded IFT", "TMCMC response-discrepancy / physics-trust alternatives", "Boundary-seeking or over-wide; neither supported a sharp load product."],
        ["Evidence ranking", "Squared frequencies + MAC; type-II ML residual scales", "+54.02 approximate ranking: local linearization, no MC-error estimate, conditional modal target."],
        ["Schneider-style surrogate", "Correlated frequency/space error + rational surrogate", "Literature-grounded future option; unimplemented."],
    ], [1.75, 2.3, 3.55], font=7.1)
    add_figure(doc, FIG / "fig4_modular_frf.png", 7.35, "Figure 4. Two held-out FRF channels showing the updated mean and separate parameter-only and parameter-plus-discrepancy intervals.", "Two log-log FRF panels. DAQ 20 updated median moves toward measured data. DAQ 24 remains far from data. Nested blue parameter and amber parameter-plus-discrepancy 5th to 95th percentile bands show the uncertainty decomposition.")
    p(doc, "DAQ 20 moves toward the measurement; DAQ 24 does not. The outer band can envelope a structurally wrong mean, but that is not the same as repairing the FEM. The large observed-channel discrepancy is why the band remains unusably wide even though the modal NUTS stage converged.", size=8.6, after=0)

    # Page 6 — load comparison.
    page(doc, "5. What the load comparison showed", "Shear evidence is measured; normal-Z remains a synthetic self-consistency check.")
    add_table(doc, ["Axis / evidence", "FEM + 6 dB\ncoverage; width", "Parameter only\ncoverage; width", "Discrepancy aware\ncoverage; width", "Measured CRPS\nbaseline → updated"], [
        ["Shear X\nmeasured", "0.865; 1.000", "0.984; 1.068", "0.995; 1.508", "1.252 → 1.137"],
        ["Shear Y\nmeasured", "0.706; 1.000", "0.947; 1.215", "0.982; 2.301", "0.771 → 0.709"],
        ["Normal Z\nSYNTHETIC ONLY", "0.738; 1.000", "0.969; 1.016", "0.987; 2.526", "no measured validation"],
    ], [1.35, 1.45, 1.5, 1.6, 1.55], font=7.45)
    p(doc, "Coverage rises, and the discrepancy-aware method has lower mean continuous ranked probability score (CRPS; lower is better) than FEM + 6 dB on both measured shear axes. It wins 8/10 measured drive-axis cells under all three probability conventions used to interpret the baseline envelope. The method achieves this calibration with bands 1.51× the baseline width in shear X and 2.30× in shear Y. That width still prevents industry use.", size=9.0)
    callout(doc, "WHY WIDE?", "Parameter uncertainty is not the dominant remaining term. The output-discrepancy model must cover channel-dependent FRF shape and participation errors that nine stiffness scales cannot express. A marginal discrepancy achieves coverage by being broad; a structured discrepancy might allocate it better, but was not implemented.", PALE_BLUE, BLUE)
    doc.add_heading("Normal-Z reconciliation", level=2)
    p(doc, "The delivered reference width is 2.526× FEM + 6 dB. The later tier-updated configuration is 2.958× because observed cross-drive ln-amplitude scatter (1.393) exceeded the assumed unmeasured-tier value (0.80). These are different configurations, not inconsistent reproductions. Normal-Z remains synthetic self-consistency—not validation.")
    doc.add_heading("What the evidence comparison measured", level=2)
    p(doc, "The +54.02 log-evidence result ranks model classes for matched squared frequencies and MAC with type-II maximum-likelihood residual scales. It is an approximate diagnostic because it uses a local linearization, has no Monte Carlo error estimate, and is conditional on that modal target. It ranks classes only for the modal target; it does not test held-out load prediction.")
    add_table(doc, ["What improved", "What did not"], [
        ["Measured shear coverage and average CRPS", "Sharpness; direct net-CG force validation; normal-Z answer key"],
        ["Calibration across three baseline probability conventions", "Build-to-build, flight-to-flight, and forcing variability"],
    ], [3.8, 3.8], font=7.6)

    # Page 7 — remodeling pivot.
    page(doc, "6. Why I moved from parameter updating to model-form remodeling", "The fixed parameterization left response errors, so I tested changes to the FEM class itself.")
    p(doc, "Parameter updating changes values inside a fixed FEM class. The residual evidence instead pointed to missing or wrong response mechanisms: channel-dependent participation, interface representation, element formulation, geometry idealization, and local shape fidelity. Agentic remodeling therefore means a bounded loop over registered model-form edits.")
    callout(doc, "CURRENT LOOP", "PROPOSE registered edit  →  BUILD candidate FEM  →  VERIFY mechanics  →  FIT continuous parameters  →  SCORE held-out data  →  DIAGNOSE  →  REVISE", PALE_BLUE, BLUE)
    p(doc, "The agent proposes. Deterministic code owns mesh construction, mechanical checks, immutable data splits, budgets, exact-basis scoring, and the final evaluation. Remeshing is one operator family; remodeling also includes connectivity, joint representation, element formulation, geometry, and regional parameterization.")
    add_table(doc, ["Pilot question", "Pre-registered evidence", "Conclusion"], [
        ["Does genuine model-form freedom help?", "Connectivity, mesh, element formulation, and geometry all had positive class-mean controls; strongest selected class result was formulation +0.0711 ± 0.0120.", "Yes within the tested operators/ranges; selected bests remain selection-biased."],
        ["Did agent guidance beat equal-budget random?", "Primary best-exact vs best-exact: −0.0077 ± 0.0177. One-SE minimum detectable effect = 0.0177. Secondary track mean: +0.0028 ± 0.0056.", "This study failed to demonstrate an advantage under either convention."],
    ], [2.0, 3.35, 2.25], font=7.7)
    p(doc, "The study can detect only effects at its four-fold noise floor, and the observed agent-versus-random differences were smaller. The model-form edits improved the score within the tested ranges. The agent-guided search did not outperform the equal-budget random search.", size=8.8)
    doc.add_heading("Future harness", level=2)
    p(doc, "The future harness is a CLI-mediated version of this loop, with versioned candidate/diagnostic schemas and immutable verifier controls. remodelctl is not yet the scientific contribution and is not required to close ShockSat. It is a possible way to make later agent training reproducible.", size=8.7)
    doc.add_heading("Literature-grounded interpretation", level=2)
    p(doc, "Classical updating cannot repair mechanisms outside its parameterization [2–3]. StatFEM/calibration needs discrepancy, but flexible discrepancy can confound parameters and widen prediction [4–6,12]. Conditional evidence and held-out prediction answer different questions [7–8]. NUTS diagnostics decide whether Monte Carlo intervals are trustworthy [9–10]. Schneider's correlated-error surrogate is relevant future work, not a completed method here [11].", size=8.7)

    # Page 8 — work products, limits, and questions.
    page(doc, "7. Closing decisions and guidance needed", "Completed work is separated from the limits that affect how I should document it.")
    add_table(doc, ["Work completed", "Limit that must travel with it"], [
        ["Real-data separation between converged modal Bayesian updating and non-converged response inference", "One ShockSat article; no build/flight variability"],
        ["Prior-whitened subspace diagnosis: four learned combinations", "Not nine raw-parameter identifiability claims"],
        ["Residual floor survives a loose converged prior", "Three of five sensitivity variants did not converge"],
        ["Modular prediction separates parameter and output-discrepancy bands", "Wide marginal discrepancy; not a joint StatFEM posterior"],
        ["Matched coverage/proper-score comparison against FEM + 6 dB", "Normal-Z has no measured answer key; shear gain costs width"],
        ["Controlled exact-basis model-form search with random controls", "Positive model-form classes; no demonstrated agent advantage"],
    ], [4.0, 3.6], font=7.65)
    doc.add_heading("Guidance I need for the final month", level=1)
    qs = [
        "Is the strongest closure a methodological evaluation of where modal updating stops being response-level StatFEM, rather than another attempt to force a converged whole-FRF posterior?",
        "Which two or three contributions above are strong enough to document as lab contributions, and which are merely project lessons?",
        "Looking back, was ShockSat/indirect load prediction the wrong problem framing for evaluating StatFEM, or was exposing the observability and discrepancy limits a worthwhile outcome?",
        "What final artifact would best capture the personal lesson: a short paper-style report, a reproducible negative-result case study, or a lab methods note and harness?",
    ]
    for i, q in enumerate(qs, 1):
        bullet(doc, f"{i}. ", q, size=9.1)
    callout(doc, "POSSIBLE CLOSEOUT", "I could close by documenting why modal calibration did not produce a sharp response prediction, which evaluations exposed that gap, and what evidence would be needed before revisiting structured discrepancy or model-form search. I want your direction before committing the remaining month to that form.", PALE_BLUE, BLUE)
    doc.add_heading("Suggested final-month deliverables", level=2)
    add_table(doc, ["Artifact", "Purpose"], [
        ["Paper-style negative-result case study", "Methods, Bayesian assumptions, closure analyses, and the calibrated-but-wide predictive result"],
        ["Reproducible lab packet", "Frozen data contracts, likelihoods, checks, and the model-form search evaluation traps"],
        ["Personal lessons note", "Problem selection, observability, stopping rules, and what should have been preregistered earlier"],
    ], [3.0, 4.6], font=7.7)

    # Page 9 — references.
    page(doc, "References", "Publisher/author/standards/NASA links were verified in the predecessor report workspace on 21 July 2026.")
    refs = [
        "[1] NASA Engineering and Safety Center Academy. ShockSat. https://nescacademy.nasa.gov/workshops/ShockSat",
        "[2] Mottershead, J. E., & Friswell, M. I. (1993). Model Updating in Structural Dynamics: A Survey. Journal of Sound and Vibration, 167(2), 347–375. doi:10.1006/jsvi.1993.1340.",
        "[3] Mottershead, J. E., Link, M., & Friswell, M. I. (2011). The sensitivity method in finite element model updating: A tutorial. MSSP, 25(7), 2275–2296. doi:10.1016/j.ymssp.2010.10.012.",
        "[4] Beck, J. L., & Katafygiotis, L. S. (1998). Updating Models and Their Uncertainties. I. Journal of Engineering Mechanics, 124(4), 455–461. doi:10.1061/(ASCE)0733-9399(1998)124:4(455).",
        "[5] Girolami, M., Febrianto, E., Yin, G., & Cirak, F. (2021). The statistical finite element method for coherent synthesis of observation data and model predictions. CMAME, 375, 113533. doi:10.1016/j.cma.2020.113533.",
        "[6] Brynjarsdottir, J., & O'Hagan, A. (2014). Learning about physical parameters: the importance of model discrepancy. Inverse Problems, 30(11), 114007. doi:10.1088/0266-5611/30/11/114007.",
        "[7] Mthembu, L., Marwala, T., Friswell, M. I., & Adhikari, S. (2011). Model selection in finite element model updating using the Bayesian evidence statistic. MSSP, 25(7), 2399–2412. doi:10.1016/j.ymssp.2011.04.001.",
        "[8] Vehtari, A., Gelman, A., & Gabry, J. (2017). Practical Bayesian model evaluation using leave-one-out cross-validation and WAIC. Statistics and Computing, 27, 1413–1432. doi:10.1007/s11222-016-9696-4.",
        "[9] Hoffman, M. D., & Gelman, A. (2014). The No-U-Turn Sampler. JMLR, 15, 1593–1623. https://www.jmlr.org/papers/v15/hoffman14a.html",
        "[10] Vehtari, A., Gelman, A., Simpson, D., Carpenter, B., & Bürkner, P.-C. (2021). Rank-normalization, folding, and localization: An improved R-hat. Bayesian Analysis, 16(2), 667–718. doi:10.1214/20-BA1221.",
        "[11] Schneider, R., Papaioannou, I., & Straub, D. (2022). Bayesian parameter updating in linear structural dynamics with frequency transformed data using rational surrogate models. MSSP, 166, 108407. doi:10.1016/j.ymssp.2021.108407.",
        "[12] Kennedy, M. C., & O'Hagan, A. (2001). Bayesian calibration of computer models. JRSS B, 63(3), 425–464. doi:10.1111/1467-9868.00294.",
        "[13] ASME V&V 10-2019 (R2025). Standard for Verification and Validation in Computational Solid Mechanics. https://www.asme.org/codes-standards/find-codes-standards/standard-for-verification-and-validation-in-computational-solid-mechanics",
    ]
    for ref in refs:
        para = doc.add_paragraph()
        para.paragraph_format.left_indent = Inches(0.22)
        para.paragraph_format.first_line_indent = Inches(-0.22)
        para.paragraph_format.space_after = Pt(4.1)
        r = para.add_run(ref)
        r.font.name = "Arial"; r.font.size = Pt(8.0); r.font.color.rgb = rgb(INK)
    p(doc, "Repository evidence map: Task Card A packet/out artifacts; time-domain damping packet; real-data modular cache; net-CG method-selection/validated-port packets; model-form pilot; verified-reference ledger. Full paths and hashes are in this report workspace's source manifest and numeric trace.", size=7.7, color=GREY, after=0)
    doc.save(DOCX)


def trace_spec() -> list[dict]:
    # Values selected to cover every main quantitative claim family.
    return [
        {"label": "A1 contracted count", "display": "four learned combinations", "source": str(A1_PATH), "path": "n_contracted_below_half", "expected": 4},
        *[{"label": f"A1 eig {i+1}", "display": f"{v:.4f}", "source": str(A1_PATH), "path": f"eigenvalues_ascending.{i}", "expected": v} for i, v in enumerate([0.0187, 0.0286, 0.2593, 0.3546])],
        {"label": "A1 prior-like low", "display": "0.8718", "source": str(A1_PATH), "path": "eigenvalues_ascending.4", "expected": 0.8718},
        {"label": "A1 prior-like high", "display": "1.1657", "source": str(A1_PATH), "path": "eigenvalues_ascending.8", "expected": 1.1657},
        {"label": "A2 ref sigma", "display": "4.60%", "source": str(A2_PATH), "path": "variants.hn005_reference.sigma_f_median", "expected": 0.046024907755116265},
        {"label": "A2 stored sigma", "display": "4.63%", "source": str(A2_PATH), "path": "reference_reproduction.stored_sigma_f_median", "expected": 0.046264696389052784},
        {"label": "A2 ref rhat", "display": "1.009", "source": str(A2_PATH), "path": "variants.hn005_reference.convergence.worst_rhat", "expected": 1.0087049511320176},
        {"label": "A2 ref ess", "display": "464", "source": str(A2_PATH), "path": "variants.hn005_reference.convergence.min_ess", "expected": 463.6493760841175},
        {"label": "A2 loose sigma", "display": "4.80%", "source": str(A2_PATH), "path": "variants.hn015.sigma_f_median", "expected": 0.04802172785526972},
        {"label": "A2 prior predictive", "display": "18/18", "source": str(A2_PATH), "path": "variants.hn015.prior_predictive_covered", "expected": "18/18"},
        {"label": "A3 X baseline cov", "display": "0.865", "source": str(A3_PATH), "path": "known_answer_gate.recomputed_scorecard.shear_X.baseline_fem+6dB.weighted_coverage", "expected": 0.865},
        {"label": "A3 Y baseline cov", "display": "0.706", "source": str(A3_PATH), "path": "known_answer_gate.recomputed_scorecard.shear_Y.baseline_fem+6dB.weighted_coverage", "expected": 0.706},
        {"label": "A3 X stat cov", "display": "0.995", "source": str(A3_PATH), "path": "known_answer_gate.recomputed_scorecard.shear_X.statfem_Fk.weighted_coverage", "expected": 0.995},
        {"label": "A3 X width", "display": "1.508", "source": str(A3_PATH), "path": "known_answer_gate.recomputed_scorecard.shear_X.statfem_Fk.sharpness_band_grms_ratio_vs_fem6db", "expected": 1.508},
        {"label": "A3 Y stat cov", "display": "0.982", "source": str(A3_PATH), "path": "known_answer_gate.recomputed_scorecard.shear_Y.statfem_Fk.weighted_coverage", "expected": 0.982},
        {"label": "A3 Y width", "display": "2.301", "source": str(A3_PATH), "path": "known_answer_gate.recomputed_scorecard.shear_Y.statfem_Fk.sharpness_band_grms_ratio_vs_fem6db", "expected": 2.301},
        {"label": "A3 X CRPS baseline", "display": "1.252", "source": str(A3_PATH), "path": "crps.measured_aggregate_strong_drives.shear_X.fem6db_log_uniform_primary", "expected": 1.2516},
        {"label": "A3 X CRPS stat", "display": "1.137", "source": str(A3_PATH), "path": "crps.measured_aggregate_strong_drives.shear_X.statfem_Fk", "expected": 1.1369},
        {"label": "A3 Y CRPS baseline", "display": "0.771", "source": str(A3_PATH), "path": "crps.measured_aggregate_strong_drives.shear_Y.fem6db_log_uniform_primary", "expected": 0.7711},
        {"label": "A3 Y CRPS stat", "display": "0.709", "source": str(A3_PATH), "path": "crps.measured_aggregate_strong_drives.shear_Y.statfem_Fk", "expected": 0.709},
        {"label": "A3 normal reference", "display": "2.526", "source": str(A3_PATH), "path": "normal_z_widths.delivered_reference", "expected": 2.526},
        {"label": "A3 normal tier", "display": "2.958", "source": str(A3_PATH), "path": "normal_z_widths.tier_updated", "expected": 2.958},
        {"label": "A4 points", "display": "6,525", "source": str(A4_PATH), "path": "likelihood_form_documented", "expected": "N=6525"},
        {"label": "A4 bottom maxima", "display": "10 local maxima", "source": str(A4_PATH), "path": "profiles.bottom_box.n_local_maxima", "expected": 10},
        {"label": "A4 top maxima", "display": "10 local maxima", "source": str(A4_PATH), "path": "profiles.top_box.n_local_maxima", "expected": 10},
        {"label": "A5 phase variance", "display": "0.854", "source": str(A5_PATH), "path": "circular_variance", "expected": 0.8536364364877632},
        {"label": "pilot primary delta", "display": "-0.0077", "source": str(PILOT_PATH), "path": "HQ1.primary.delta_mean", "expected": -0.007656033372189102},
        {"label": "pilot primary se", "display": "0.0177", "source": str(PILOT_PATH), "path": "HQ1.primary.delta_se", "expected": 0.017729278569034886},
        {"label": "pilot secondary delta", "display": "+0.0028", "source": str(PILOT_PATH), "path": "HQ1.secondary.delta_mean", "expected": 0.002799626851847495},
        {"label": "pilot secondary se", "display": "0.0056", "source": str(PILOT_PATH), "path": "HQ1.secondary.delta_se", "expected": 0.005558059112433576},
        {"label": "evidence gain", "display": "+54.02", "source": str(EVID_PATH), "path": "headline.logZ_winner_minus_baseline", "expected": 54.02},
    ]


def source_manifest(paths: list[Path]) -> dict:
    return {"generated_by": str(HERE), "sources": [{"path": str(x), "sha256": sha256(x)} for x in paths]}


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    FIG.mkdir(parents=True, exist_ok=True)
    a1, a2, a3, a4, a5, pilot = map(load, (A1_PATH, A2_PATH, A3_PATH, A4_PATH, A5_PATH, PILOT_PATH))
    make_method_map(FIG / "fig1_method_map.png")
    make_modal_figure(FIG / "fig2_modal_identification.png", a1, a2)
    make_profile_figure(FIG / "fig3_wholefrf_profile.png", a4)
    frf = make_frf_figure(FIG / "fig4_modular_frf.png")
    (OUT / "frf_figure_source.json").write_text(json.dumps(frf, indent=2) + "\n")
    write_md(a1, a2, a3, a4, a5, pilot)
    build_doc(a1, a2, a3, a4, a5, pilot)
    (OUT / "numeric_trace.json").write_text(json.dumps(trace_spec(), indent=2) + "\n")
    paths = [A1_PATH, A2_PATH, A3_PATH, A4_PATH, A5_PATH, DAMP_PATH, DAMP_PACKET, FRF_CACHE,
             PILOT_PATH, EVID_PATH, TIER_PATH,
             REPORTS / "shocksat_results_summary_20260721" / "references_verified.md"]
    (OUT / "source_manifest.json").write_text(json.dumps(source_manifest(paths), indent=2) + "\n")
    print(json.dumps({"docx": str(DOCX), "markdown": str(MD), "figures": 4,
                      "numeric_trace_checks": len(trace_spec())}, indent=2))


if __name__ == "__main__":
    main()
