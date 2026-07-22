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
DOCX = WORK / "ShockSat_Bayesian_FEM_StatFEM_closure_brief_fable.docx"
MD = WORK / "ShockSat_Bayesian_FEM_StatFEM_closure_brief_fable.md"

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


SELECTION_RULE = ("Rank the 31 held-out channels of frozen split seed 10 by the median of "
                  "|log10(updated median / measured)| over 45-260 Hz, ascending; show ranks "
                  "1, 7, 13, 19, 25, 31. Rule fixed before plotting (decisions_log.md F2).")


def make_frf_figure(path: Path) -> dict:
    plt.rcParams.update({"font.size": 9, "axes.spines.top": False, "axes.spines.right": False,
                         "legend.frameon": False, "axes.edgecolor": "#666666"})
    cache = np.load(FRF_CACHE, allow_pickle=True)
    freqs = np.asarray(cache["freqs"], float)
    split = next(s for s in cache["splits"] if int(s["seed"]) == 10)
    band = (freqs >= 45.0) & (freqs <= 260.0)

    def miss(channel) -> float:
        med = np.asarray(channel["param"], float)[1]
        tru = np.asarray(channel["tru"], float)
        return float(np.median(np.abs(np.log10(med[band] / tru[band]))))

    ranked = sorted(split["chans"], key=miss)
    ranks = [1, 7, 13, 19, 25, 31]
    picks = [(r, ranked[r - 1]) for r in ranks]
    fig, axes = plt.subplots(2, 3, figsize=(10.8, 7.1), sharex=True, sharey=True)
    fig.subplots_adjust(left=0.075, right=0.985, top=0.84, bottom=0.155, wspace=0.10, hspace=0.28)
    for ax, (rank, channel) in zip(axes.ravel(), picks):
        measured = np.asarray(channel["tru"], float)
        original = np.asarray(channel["det"], float)
        param = np.asarray(channel["param"], float)
        total = np.asarray(channel["total"], float)
        ax.fill_between(freqs, total[0], total[1], color="#EFC17D", alpha=0.46, lw=0, zorder=1)
        ax.fill_between(freqs, param[0], param[2], color="#8FC1E3", alpha=0.74, lw=0, zorder=2)
        ax.plot(freqs, original, color="#7A7F83", lw=0.9, ls=(0, (4, 2)), zorder=3)
        ax.plot(freqs, param[1], color=f"#{BLUE}", lw=1.35, zorder=4)
        ax.plot(freqs, measured, color="#171717", lw=1.0, zorder=5)
        ax.set_xscale("log")
        ax.set_yscale("log")
        ax.set_xlim(45, 260)
        ax.grid(True, axis="y", color="#E2E5E7", lw=0.45)
        ax.set_title(f"DAQ {int(channel['daq'])}  (miss rank {rank} of 31)", loc="left",
                     fontsize=9.6, color=f"#{INK}")
    for ax in axes[1]:
        ax.set_xlabel("frequency [Hz, log]")
    for ax in axes[:, 0]:
        ax.set_ylabel("|H| [g/lbf, log]")
    handles = [
        Line2D([0], [0], color="#171717", lw=1.2, label="measured data"),
        Line2D([0], [0], color="#7A7F83", lw=1.1, ls=(0, (4, 2)), label="original FEM"),
        Line2D([0], [0], color=f"#{BLUE}", lw=1.5, label="updated median"),
        Patch(facecolor="#8FC1E3", alpha=0.74, label="parameter 5–95%"),
        Patch(facecolor="#EFC17D", alpha=0.46, label="parameter + discrepancy 5–95%"),
    ]
    fig.legend(handles=handles, loc="upper left", bbox_to_anchor=(0.075, 0.93), ncol=5, fontsize=8.0,
               columnspacing=1.1, handlelength=2.3)
    fig.suptitle("Held-out channels from best to worst: the update is calibrated by widening, not by repairing every FRF",
                 x=0.075, y=0.985, ha="left", fontsize=12.5, color=f"#{INK}")
    fig.text(0.075, 0.055,
             "Frozen split seed 10; 45–260 Hz. Channel selection preregistered: median |log10(updated median / measured)| over the plotted band, ranks 1, 7, 13, 19, 25, 31 of 31.",
             fontsize=7.5, color=f"#{GREY}")
    fig.text(0.075, 0.030,
             f"Modal NUTS stage converged (max R-hat {float(split['rhat']):.4f}); outer band adds the marginal log-amplitude discrepancy σ = {float(split['sig']):.3f} estimated on observed channels.",
             fontsize=7.5, color=f"#{GREY}")
    fig.text(0.075, 0.005,
             "Two-stage modular prediction, not a jointly converged whole-FRF StatFEM posterior.",
             fontsize=7.5, color=f"#{GREY}")
    fig.savefig(path, dpi=240, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    return {"split_seed": 10, "rhat": float(split["rhat"]), "sigma": float(split["sig"]),
            "source_sha256": sha256(FRF_CACHE), "selection_rule": SELECTION_RULE,
            "ranks": ranks, "daqs": [int(c["daq"]) for _, c in picks],
            "miss_stat_by_daq": {str(int(c["daq"])): round(miss(c), 4) for _, c in picks},
            "band_hz": [45, 260]}


def write_md(a1, a2, a3, a4, a5, pilot) -> None:
    """Markdown mirror of the brief; content lives in brief_fable_md_source.md."""
    MD.write_text((HERE.parent / "brief_fable_md_source.md").read_text())


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
    doc.add_paragraph().paragraph_format.space_after = Pt(1)
    callout(doc, "CENTRAL FINDING", "(1) The posterior mean does not move enough toward the data because the only converged likelihood sees modal frequencies — it has no mechanism that can raise a specific channel's amplitude in a specific band, and only four of nine prior-whitened stiffness combinations are learned — and because the discrepancy I added afterward was zero-mean by construction, so it could widen the band but never shift the mean. (2) The uncertainty bands remain unusably large because that zero-mean, single-scale discrepancy can achieve coverage only by being wide everywhere; parameter-only bands are already near baseline width yet under-cover, so width is the only currency the discrepancy has. A structured-mean discrepancy over sensor location and frequency could move the mean instead; it was never tested, so its failure is not established.", PALE_AMBER, AMBER)
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
        ["CRPS", "Continuous ranked probability score: a proper score comparing an entire predictive distribution with one observed value; rewards closeness and honest spread. Lower is better; in the load's units."],
        ["IFT / β", "Inferred-physics-trust comparator; β is the bounded physics-trust multiplier. Reproducible TMCMC, but over-wide band GRMS."],
        ["Model-form score", "P1′ = median per-channel Pearson correlation of log10 FRF magnitude below 200 Hz, averaged over 4 leave-one-drive-out folds; unitless."],
        ["Counts / bands", "Modal: 18 pairs, 9 stiffness scales, 4×1,000 NUTS draws. Whole FRF: 6,525 points, 3 training drives, 45–400 Hz. Working twin: split 10, six channels by preregistered miss rank, 45–260 Hz, 5th–95th bands. Load: 5 measured held-out drives per shear axis; normal-Z synthetic only (Appendix B)."],
    ]
    add_table(doc, ["Term", "Definition used here"], rows, [1.35, 6.25], font=7.25)
    p(doc, "Implemented modal likelihood — one formulation of eight:", bold_lead="Implemented modal likelihood — one formulation of eight:", size=8.8, after=1)
    p(doc, "log f_meas,m  ~  Normal(log f_pred,m(θ), σf)", size=10.2, color=NAVY, after=2, align=WD_ALIGN_PARAGRAPH.CENTER)
    p(doc, "I implemented eight likelihood formulations across the project — modal frequency; frequency + MAC; iid whole-FRF magnitude; phase/complex FRF; time-domain damping; Beck-style shape field; free response discrepancy; bounded physics trust — and this modal-frequency one is the only formulation that passed the convergence gate. The full inventory with outcomes is the ledger in Section 3. The nine positive stiffness scales had lognormal priors centered at the inherited FEM. The primary run inferred them and the iid log-frequency residual σf from modal frequencies. FRF amplitudes did not enter this likelihood, and MAC was not used as a generative shape likelihood.", size=8.4, after=3)
    add_figure(doc, FIG / "fig1_method_map.png", 7.25, "Figure 1. Research sequence from the original StatFEM question through modal updating, response evaluation, and model-form remodeling.", "Flow diagram. The study reconstructs ShockSat, updates stiffness from modal frequencies, propagates uncertainty to FRFs, adds response discrepancy, and checks held-out channels and loads. Remaining response errors lead to response-data experiments, discrepancy tests, residual diagnosis, and model-form edits.")

    # Page 3 — modal analysis.
    page(doc, "2. What the modal update showed", "Direct yes/no answers first; the subspace and prior-sensitivity detail behind them is Figure A1 in Appendix A.")
    add_table(doc, ["Bayesian question", "Answer"], [
        ["Did the prior simply prevent movement?", "**No.** The data contract four prior-whitened log-θ combinations to 0.0187, 0.0286, 0.2593, 0.3546; five directions remain prior-like at 0.8718–1.1657. The data moved everything it could see. Subspace result, not nine identifiable marginals."],
        ["Was σf forced by its prior?", "**No.** Reference HalfNormal(.05) reproduces 4.60% vs 4.63% stored (R-hat 1.009, ESS 464). A loose converged HalfNormal(.15) gives 4.80%. All five medians span 4.16–4.82%."],
        ["Are the predictive checks obviously inconsistent?", "**No.** All five prior-predictive variants cover 18/18 frequencies. The reference posterior-predictive PIT — probability integral transform: where each observation falls inside its own predictive distribution, ideally uniform — spans 0.079–0.906 without boundary pile-up."],
        ["What remains unresolved?", "**Three things, at the scale of the whole project:** whether a structured-mean discrepancy could move response predictions (never tested); whether any response-level likelihood yields a converged, decision-grade posterior on this article; whether model-form editing beats parameter updating. Narrower: three of five sensitivity chains fail convergence, so their intervals are not trustworthy, and I interpret the modal result only at the level of parameter combinations."],
    ], [2.1, 5.5], font=7.65)
    doc.add_heading("Why the mean cannot move — and what could still move it", level=2)
    p(doc, "The converged likelihood sees 18 modal frequencies. Moving a resonance is the only way it can change any FRF, and only four stiffness combinations are learned from the data. Nothing in the model can express “the sensors at this location need higher amplitude between 20 and 80 Hz.” The discrepancy added at the prediction stage was zero-mean by construction: it can widen the band, never shift the mean. That is a modeling choice, not a law. A discrepancy with a structured mean over sensor location and frequency — exactly the mechanism the residuals suggest — could move the mean toward the data, and I did not implement or test it.", size=8.8)
    callout(doc, "PLAIN STATEMENT", "The mean does not move because the converged likelihood has no amplitude mechanism and the chosen discrepancy was zero-mean — not because moving the mean has been shown impossible. Weakening the σf prior does not eliminate the residual floor.", PALE_BLUE, BLUE)

    # Page 4 — response attempts.
    page(doc, "3. Experiments with response data", "The full ledger of the eight likelihood formulations, then the recovered diagnostics behind them.")
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
    p(doc, "The iid whole-FRF likelihood used 6,525 log-magnitude observations, per-drive gains, a residual scale, and nine stiffness scales. With gains and residual scale profiled at each of 41 points, both sensitive slices contain about 10 local maxima. The stored chains occupy different modes (worst R-hat 44.7, ESS 2.0). For this likelihood, the profile supports a diagnosis of global under-identification and multimodality. It does not establish a general failure of response-level StatFEM.", size=8.8)
    add_table(doc, ["Recovered diagnostic", "Result", "Meaning"], [
        ["Phase (original artifact found)", "Single hit; 46 channels; 12 modes; circular variance 0.854; complex slice no sharper than magnitude", "Phase did not supply a sharper parameter direction for that dataset."],
        ["Time-domain damping", "14/16 modes converged; worst R-hat 1.020; ESS 250; ζ = 0.33–0.76%", "Damping was measurable, but correcting it raised peaks because the FEM used 1%; the envelope decision did not improve."],
        ["Free discrepancy vs bounded physics trust", "Free variance sought a boundary; bounded alternative reproduced across TMCMC populations", "Different failure modes: confounding/boundary behavior versus reproducible but over-wide prediction."],
    ], [1.65, 2.55, 3.4], font=7.45)
    callout(doc, "LIMIT", "More iterations alone do not address multiple separated likelihood modes or parameter–discrepancy confounding. A different response likelihood/covariance and a better-observed forcing/shape model would be a method change, not a sampler tune-up.", PALE_AMBER, AMBER)

    # Page 5 — method ledger + FRF.
    page(doc, "4. The modular working twin", "The parameter update and response discrepancy were estimated in two stages. Six held-out channels, best to worst by a preregistered rule.")
    add_figure(doc, FIG / "fig2_modular_frf_panels.png", 7.3, "Figure 2. Six held-out FRF channels, ranked best to worst by a rule fixed before plotting: median |log10(updated median / measured)| over 45–260 Hz, ranks 1, 7, 13, 19, 25, 31 of 31. Inner band: parameter-only. Outer band: parameter plus marginal discrepancy.", "Six log-log FRF panels arranged best to worst by preregistered miss rank. In the best panels the updated median tracks the measured curve; in the worst panels the median departs from the data and only the wide outer parameter-plus-discrepancy band covers it.")
    p(doc, "In the best-ranked panels the updated median tracks the measurement. By the middle ranks the median already departs from the data over parts of the band, and at the worst ranks the outer band envelopes a structurally wrong mean — enveloping is not repairing the FEM. The posterior mean moves only as far as the mechanisms in the modal likelihood allow; a stronger or weaker discrepancy prior cannot add missing channel physics. The large observed-channel discrepancy is why the band remains unusably wide even though the modal NUTS stage converged. A structured discrepancy could redistribute that uncertainty, and a structured discrepancy mean could remove part of it; both remain untested.", size=8.6, after=0)

    # Page 6 — load comparison.
    page(doc, "5. What the load comparison showed", "Shear evidence is measured. Normal-Z is a synthetic self-consistency check, not relevant to the central finding; it is reported in Appendix B.")
    add_table(doc, ["Axis / evidence", "FEM + 6 dB\ncoverage; width", "Parameter only\ncoverage; width", "Discrepancy aware\ncoverage; width", "Measured CRPS\nbaseline → updated"], [
        ["Shear X\nmeasured", "0.865; 1.000", "0.984; 1.068", "0.995; 1.508", "1.252 → 1.137"],
        ["Shear Y\nmeasured", "0.706; 1.000", "0.947; 1.215", "0.982; 2.301", "0.771 → 0.709"],
    ], [1.35, 1.45, 1.5, 1.6, 1.55], font=7.45)
    p(doc, "Coverage rises, and the discrepancy-aware method has lower mean CRPS (continuous ranked probability score, defined in Section 1: it scores the whole predictive distribution against the measured value; lower is better) than FEM + 6 dB on both measured shear axes. It wins 8/10 measured drive-axis cells under all three probability conventions used to interpret the baseline envelope. The method achieves this calibration with bands 1.51× the baseline width in shear X and 2.30× in shear Y. That width still prevents industry use.", size=9.0)
    callout(doc, "WHY WIDE?", "Parameter uncertainty is not the driver: parameter-only bands are 1.068× and 1.215× baseline yet under-cover. The zero-mean marginal discrepancy must absorb channel-dependent FRF shape and participation errors that nine stiffness scales cannot express, and a single broad scale can achieve coverage only by being wide everywhere. A structured discrepancy might allocate uncertainty where the error lives — and a structured discrepancy mean might remove part of it — but neither was implemented.", PALE_BLUE, BLUE)
    doc.add_heading("What the evidence comparison measured, in more detail", level=2)
    p(doc, "The +54.02 result is a difference in log Bayesian evidence (marginal likelihood). Evidence is the probability a model class assigns to the observed data after averaging over its prior, so it trades fit against flexibility rather than rewarding fit alone. A difference of +54.02 in natural-log units says the winning class makes the matched modal data about e^54 times more probable than the baseline class — decisive if taken at face value.", size=8.7)
    p(doc, "Three caveats prevent taking it at face value. First, it uses a local linearization of the FEM around a point, so the number is a Laplace-style approximation, trustworthy only if the posterior is close to Gaussian there. Second, it carries no Monte Carlo or approximation error bar, so the magnitude cannot be separated from approximation error. Third, it is conditional on one target — matched squared frequencies plus MAC, with residual scales set by type-II maximum likelihood, meaning those scales were chosen by maximizing rather than integrated over. It therefore ranks model classes for that modal target only; it says nothing about held-out response or load prediction, which is the separate question this section's table answers, and the two comparisons can disagree.", size=8.7)
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
    add_table(doc, ["Work completed", "Where explained", "Limit that must travel with it"], [
        ["Real-data separation between converged modal Bayesian updating and non-converged response inference", "§2, §3", "One ShockSat article; no build/flight variability"],
        ["Prior-whitened subspace diagnosis: four learned combinations", "§2, Appendix A", "Not nine raw-parameter identifiability claims"],
        ["Residual floor survives a loose converged prior", "§2, Appendix A", "Three of five sensitivity variants did not converge"],
        ["Modular prediction separates parameter and output-discrepancy bands", "§4, Figure 2", "Wide marginal discrepancy; not a joint StatFEM posterior"],
        ["Matched coverage/proper-score comparison against FEM + 6 dB", "§5, Appendix B", "Normal-Z has no measured answer key; shear gain costs width"],
        ["Controlled exact-basis model-form search with random controls", "§6", "Positive model-form classes; no demonstrated agent advantage"],
    ], [3.4, 1.0, 3.2], font=7.65)
    doc.add_heading("Guidance I need for the final month", level=1)
    p(doc, "i've got less than a month until I'm done with my PSL studies. What is the best way to bring it to closure? I want to make sure I capture the right lessons learned from this personally on if/why it failed and if I embarked on the wrong direction/problem at the outset, and make sure I make sure I document any meaningful contributions i've made to this field and the research of our lab.", size=9.4)

    # Appendix — modal identification detail and normal-Z status.
    page(doc, "Appendix", "Detail moved out of the main line: modal identification evidence and the normal-Z status.")
    doc.add_heading("Appendix A. Modal identification detail", level=2)
    add_figure(doc, FIG / "figA1_modal_identification.png", 7.35, "Figure A1. Prior-whitened posterior subspace and σf prior sensitivity. Non-converged variants show their worst diagnostics on the plot; those intervals are not trustworthy.", "Left: nine posterior-to-prior variance ratios with four below one half. Right: five sigma-f prior variants with medians near 4.2 to 4.8 percent; two converged variants are filled and three non-converged variants are hollow with R-hat and ESS labels.")
    p(doc, "The four contracted prior-whitened log-stiffness directions have posterior/prior variance ratios 0.0187, 0.0286, 0.2593, and 0.3546, dominated by bottom/top box, plates, and cross-beam combinations. The remaining five directions are prior-like (0.8718–1.1657). The frozen HalfNormal(0.05) reference reproduces σf = 4.60% versus 4.63% stored, with worst R-hat 1.009 and minimum ESS 464; a looser converged HalfNormal(0.15) gives 4.80%; across all five priors the medians span 4.16–4.82%, and every prior predictive check covers 18/18 frequencies. Three sensitivity runs did not converge; their intervals are not trustworthy.", size=8.6)
    doc.add_heading("Appendix B. Normal-Z evidence status", level=2)
    p(doc, "Normal Z, synthetic self-consistency only: baseline FEM + 6 dB coverage 0.738 (width 1.000); parameter-only 0.969 (width 1.016); discrepancy-aware 0.987 (width 2.526); no measured validation exists for this axis. The delivered reference width is 2.526× FEM + 6 dB. The later tier-updated configuration is 2.958× because observed cross-drive ln-amplitude scatter (1.393) exceeded the assumed unmeasured-tier value (0.80). These are different configurations, not inconsistent reproductions. Normal-Z remains synthetic self-consistency — not validation.", size=8.6)

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
    make_modal_figure(FIG / "figA1_modal_identification.png", a1, a2)
    frf = make_frf_figure(FIG / "fig2_modular_frf_panels.png")
    (OUT / "frf_figure_source.json").write_text(json.dumps(frf, indent=2) + "\n")
    write_md(a1, a2, a3, a4, a5, pilot)
    build_doc(a1, a2, a3, a4, a5, pilot)
    (OUT / "numeric_trace.json").write_text(json.dumps(trace_spec(), indent=2) + "\n")
    paths = [A1_PATH, A2_PATH, A3_PATH, A4_PATH, A5_PATH, DAMP_PATH, DAMP_PACKET, FRF_CACHE,
             PILOT_PATH, EVID_PATH, TIER_PATH,
             REPORTS / "shocksat_results_summary_20260721" / "references_verified.md"]
    (OUT / "source_manifest.json").write_text(json.dumps(source_manifest(paths), indent=2) + "\n")
    print(json.dumps({"docx": str(DOCX), "markdown": str(MD), "figures": 3,
                      "numeric_trace_checks": len(trace_spec())}, indent=2))


if __name__ == "__main__":
    main()
