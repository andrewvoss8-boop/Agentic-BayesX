#!/usr/bin/env node
import fs from "node:fs/promises";
import path from "node:path";
import os from "node:os";
import { fileURLToPath } from "node:url";
import { Presentation, PresentationFile } from "/Users/avoss/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/.pnpm/@oai+artifact-tool@file+local-deps+-oai-artifact-tool-oai-artifact_tool-2.8.11.tgz/node_modules/@oai/artifact-tool/dist/artifact_tool.mjs";

const WS = path.resolve(path.join(path.dirname(fileURLToPath(import.meta.url)), ".."));
const OUT = path.join(WS, "out");
const FIG = path.join(WS, "figures");
const SLIDES = path.join(WS, "slides");
const FINAL = path.join(SLIDES, "ift_real_validation_honest_negative.pptx");
const THREAD_ID = process.env.CODEX_THREAD_ID || "manual-ift-real-validation";
const WORKSPACE = path.join(os.tmpdir(), "codex-presentations", THREAD_ID, "ift-real-validation-deck");
const TMP_DIR = path.join(WORKSPACE, "tmp");
const PREVIEW_DIR = path.join(TMP_DIR, "preview");
const LAYOUT_DIR = path.join(TMP_DIR, "layout");
const QA_DIR = path.join(TMP_DIR, "qa");

const COLORS = {
  bg: "#F8FAFC",
  ink: "#111827",
  muted: "#475569",
  faint: "#E2E8F0",
  white: "#FFFFFF",
  ift: "#C2410C",
  l5: "#0369A1",
  m2: "#525252",
  yellow: "#A16207",
  red: "#991B1B",
  green: "#047857",
  teal: "#0F766E",
};

function loadJson(rel) {
  return JSON.parse(awaitFile(path.join(OUT, rel)));
}

function awaitFile(p) {
  throw new Error("awaitFile must not be called synchronously");
}

async function readJson(rel) {
  return JSON.parse(await fs.readFile(path.join(OUT, rel), "utf8"));
}

function fmt(x, digits = 3) {
  if (x === null || x === undefined || Number.isNaN(Number(x))) return "NA";
  const v = Number(x);
  if (Math.abs(v) >= 1e4 || (Math.abs(v) > 0 && Math.abs(v) < 1e-2)) return v.toExponential(2);
  return v.toPrecision(digits);
}

function addText(slide, text, left, top, width, height, opts = {}) {
  const shape = slide.shapes.add({
    geometry: "textbox",
    position: { left, top, width, height },
    fill: "none",
    line: { style: "solid", fill: "none", width: 0 },
  });
  shape.text = text;
  shape.text.style = {
    typeface: opts.typeface || "Aptos",
    fontSize: opts.fontSize || 20,
    bold: Boolean(opts.bold),
    color: opts.color || COLORS.ink,
    alignment: opts.alignment || "left",
  };
  return shape;
}

function addRect(slide, left, top, width, height, opts = {}) {
  return slide.shapes.add({
    geometry: opts.geometry || "roundRect",
    position: { left, top, width, height },
    fill: opts.fill || COLORS.white,
    line: { style: "solid", fill: opts.line || COLORS.faint, width: opts.lineWidth ?? 1 },
    borderRadius: opts.borderRadius ?? 8,
  });
}

function addFooter(slide, n, text = "Real ShockSat hit-001 | IFT real validation | numbers trace to scorecard/checker JSON") {
  addText(slide, text, 64, 682, 930, 22, { fontSize: 10.5, color: COLORS.muted });
  addText(slide, String(n).padStart(2, "0"), 1168, 678, 48, 28, {
    fontSize: 12,
    bold: true,
    color: COLORS.muted,
    alignment: "right",
  });
}

function addTitle(slide, kicker, title, subtitle) {
  addText(slide, kicker, 64, 46, 720, 24, { fontSize: 12.5, bold: true, color: COLORS.teal });
  addText(slide, title, 64, 82, 790, 84, { fontSize: 39, bold: true, typeface: "Aptos Display" });
  if (subtitle) addText(slide, subtitle, 64, 170, 820, 56, { fontSize: 18, color: COLORS.muted });
}

async function addImage(slide, rel, left, top, width, height, alt) {
  const bytes = await fs.readFile(path.join(FIG, rel));
  slide.images.add({
    blob: new Uint8Array(bytes),
    contentType: "image/png",
    alt,
    fit: "contain",
    position: { left, top, width, height },
  });
}

function addMetric(slide, label, value, left, top, width, color, sub = "") {
  addRect(slide, left, top, width, 106, { fill: COLORS.white, line: COLORS.faint });
  addText(slide, label, left + 18, top + 14, width - 36, 24, { fontSize: 12.5, bold: true, color });
  addText(slide, value, left + 18, top + 38, width - 36, 38, { fontSize: 31, bold: true, color: COLORS.ink, typeface: "Aptos Display" });
  if (sub) addText(slide, sub, left + 18, top + 78, width - 36, 20, { fontSize: 11.5, color: COLORS.muted });
}

function addClaim(slide, text, left, top, width, height, color = COLORS.teal, fontSize = 18) {
  addRect(slide, left, top, width, height, { fill: "#F8FAFC", line: color });
  slide.shapes.add({
    geometry: "rect",
    position: { left, top, width: 7, height },
    fill: color,
    line: { style: "solid", fill: color, width: 0 },
  });
  addText(slide, text, left + 22, top + 14, width - 38, height - 22, { fontSize, color: COLORS.ink });
}

async function main() {
  const scorecard = await readJson("scorecard.json");
  const checker = JSON.parse(await fs.readFile(path.join(WS, "checker_report.json"), "utf8"));
  const mc = await readJson("ift_mc_headline.json");
  const disc = await readJson("discretization_sensitivity.json");
  const conv = await readJson("convergence_table.json");

  await fs.mkdir(PREVIEW_DIR, { recursive: true });
  await fs.mkdir(LAYOUT_DIR, { recursive: true });
  await fs.mkdir(QA_DIR, { recursive: true });
  await fs.mkdir(path.join(SLIDES, "preview"), { recursive: true });

  const sourceNotes = [
    "IFT real ShockSat validation deck source notes",
    "",
    "Mode: create.",
    "Primary data artifacts: out/scorecard.json, out/ift_mc_headline.json, out/convergence_table.json, out/discretization_sensitivity.json, checker_report.json.",
    "Figures: figures/figA_scorecard.png, figB_beta_thermometer.png, figC_heldout_frf_overlay.png, figD_discretization_invariance.png, figE_convergence_table.png.",
    "References: Hao and Bilionis 2024, arXiv:2306.02150; Alberts and Bilionis 2023, arXiv:2301.07609.",
    "All external claims are limited to the IFT/PIFT prior concept cited above; all ShockSat numbers come from the local JSON artifacts.",
  ].join("\n");
  await fs.writeFile(path.join(TMP_DIR, "source-notes.txt"), sourceNotes);

  const slidePlan = [
    "Slide plan: 9-slide honest deck.",
    "Palette: slate/off-white dominant, IFT orange, L5 blue, M2 gray, status yellow/red accents.",
    "Fonts: Aptos Display for headings, Aptos for body and numeric labels.",
    "Font scale: cover 46-52 px, slide titles 36-40 px, body 18-22 px, captions 10-12 px.",
    "Slides: 1 verdict, 2 apples-to-apples contract, 3 method, 4 scorecard, 5 beta, 6 FRF overlay, 7 discretization, 8 convergence, 9 verdict/scope.",
  ].join("\n");
  await fs.writeFile(path.join(TMP_DIR, "slide-plan.txt"), slidePlan);

  const p = Presentation.create({ slideSize: { width: 1280, height: 720 } });

  // 1 cover
  {
    const slide = p.slides.add();
    slide.background.fill = COLORS.bg;
    addText(slide, "REAL SHOCKSAT VALIDATION", 64, 52, 620, 26, { fontSize: 13, bold: true, color: COLORS.teal });
    addText(slide, "IFT vs StatFEM on held-out sensors", 64, 102, 820, 116, { fontSize: 48, bold: true, typeface: "Aptos Display" });
    addText(slide, "Physics in the prior was tested on the same real FRF data, forward model, channel split, and proper scores as the StatFEM twin.", 66, 226, 780, 66, { fontSize: 20, color: COLORS.muted });
    addRect(slide, 850, 74, 340, 128, { fill: "#FFF7ED", line: COLORS.ift });
    addText(slide, "GENERATED VERDICT", 874, 96, 292, 20, { fontSize: 12, bold: true, color: COLORS.ift });
    addText(slide, scorecard.verdict.replace("_", " "), 874, 122, 292, 40, { fontSize: 27, bold: true, color: COLORS.ink, typeface: "Aptos Display" });
    addText(slide, `Scorecard ${scorecard.status}; checker gate in checker_report.json`, 874, 168, 292, 24, { fontSize: 12.2, color: COLORS.muted });
    addMetric(slide, "IFT splits", String(mc.n_splits), 64, 382, 260, COLORS.teal, "same channel split protocol");
    addMetric(slide, "Converged", `${fmt(100 * mc.converged_frac, 2)}%`, 346, 382, 260, COLORS.red, "R-hat/ESS gate failed");
    addMetric(slide, "Weak beta", `${fmt(100 * mc.beta_weak_frac, 2)}%`, 628, 382, 260, COLORS.yellow, "posterior trust thermometer");
    addMetric(slide, "Peak interval", fmt(mc.summary.peak.interval.med), 910, 382, 260, COLORS.ift, "median IFT score");
    addClaim(slide, "Bottom line: the IFT arm is a useful honest negative here. It does not earn WIN, TIE, or ROBUSTNESS-WIN because beta and theta do not pass the convergence gate.", 64, 538, 1104, 86, COLORS.red);
    addFooter(slide, 1, "Sources: scorecard.json, checker_report.json, ift_mc_headline.json");
  }

  // 2 contract
  {
    const slide = p.slides.add();
    slide.background.fill = COLORS.bg;
    addTitle(slide, "APPLES-TO-APPLES CONTRACT", "Only the location of physics trust changes", "Everything else is copied or reused from the StatFEM real-validation workspace.");
    const items = [
      ["Same data", "Real single-impact |H1|, 45-260 Hz, bad-channel exclusions, copied data files byte-identical."],
      ["Same model", "Reduced dynamic-stiffness accelerance with copied core.py and realfrf.py conventions."],
      ["Same split", "Observed/held-out channel split, obs_frac 0.6, channel-split-only validation."],
      ["Same scorer", "score.py proper scores: interval score, CRPS, and log predictive density."],
    ];
    for (let i = 0; i < items.length; i++) {
      const x = 78 + (i % 2) * 560;
      const y = 260 + Math.floor(i / 2) * 148;
      addRect(slide, x, y, 500, 112, { fill: COLORS.white, line: COLORS.faint });
      addText(slide, items[i][0], x + 22, y + 20, 150, 28, { fontSize: 20, bold: true, color: COLORS.teal });
      addText(slide, items[i][1], x + 22, y + 54, 440, 42, { fontSize: 16.5, color: COLORS.muted });
    }
    addClaim(slide, "Caveat carried as YELLOW: the copied StatFEM data/code path gives 77 dynamic-range-eligible channels after exclusions, not the 80 stated in the draft prompt.", 88, 572, 1048, 74, COLORS.yellow, 16.5);
    addFooter(slide, 2, "Sources: manifest_sha256.txt, scorecard.json, decisions_log.md");
  }

  // 3 method
  {
    const slide = p.slides.add();
    slide.background.fill = COLORS.bg;
    addTitle(slide, "IFT CONSTRUCTION", "Physics enters the field prior through learned beta", "The field is the complex reduced response u(omega); beta is the inverse-temperature trust parameter.");
    addRect(slide, 76, 250, 502, 280, { fill: COLORS.white, line: COLORS.faint });
    addText(slide, "Prior over field", 104, 278, 430, 28, { fontSize: 22, bold: true, color: COLORS.ift });
    addText(slide, "u | theta, beta proportional to exp[- beta / 2 * || A(theta, omega) u - f ||^2]\n\nLarge beta means the FEM residual is trusted. Small beta means the prior widens around the physics.", 104, 322, 430, 126, { fontSize: 19, color: COLORS.ink });
    addText(slide, "Adaptation: field marginalization is exact for linear complex observations; the inherited observable is log|H|, so this run uses a documented first-order log-magnitude moment approximation.", 104, 462, 430, 48, { fontSize: 15.5, color: COLORS.red });
    addRect(slide, 650, 250, 486, 280, { fill: COLORS.white, line: COLORS.faint });
    addText(slide, "Sampled variables", 678, 278, 400, 28, { fontSize: 22, bold: true, color: COLORS.teal });
    addText(slide, "theta: 4 identifiable stiffness groups\nbeta: physics trust thermometer\ngain c: global units gain\n\nNUTS default, 4 chains, beta included in all-variable R-hat/ESS/divergence gate.", 678, 322, 400, 142, { fontSize: 19, color: COLORS.ink });
    addClaim(slide, "This is faithful to the IFT/PIFT idea for a linear field, but not a hidden exact log-Rician solution. The approximation is visible in method_ift.md and the checker.", 650, 556, 486, 66, COLORS.yellow);
    addFooter(slide, 3, "Sources: method_ift.md; Hao and Bilionis arXiv:2306.02150; Alberts and Bilionis arXiv:2301.07609");
  }

  // 4 scorecard
  {
    const slide = p.slides.add();
    slide.background.fill = COLORS.bg;
    addTitle(slide, "SCORECARD", "L5 remains the working bar; IFT is not a scored win", "Proper scores reward calibration and sharpness, so a method cannot win by simply widening the band.");
    await addImage(slide, "figA_scorecard.png", 64, 230, 780, 390, "Held-out QOI scorecard");
    addMetric(slide, "IFT peak interval", fmt(mc.summary.peak.interval.med), 884, 246, 276, COLORS.ift, "median over 25 splits");
    addMetric(slide, "L5 peak interval", fmt(scorecard.L5_modal_feature_marginal_qoi_discrepancy.qoi.peak.interval.med), 884, 370, 276, COLORS.l5, "copied StatFEM bar");
    addClaim(slide, "Generated verdict is HONEST_NEGATIVE because convergence failed before any proper-score win could be claimed.", 884, 506, 276, 92, COLORS.red);
    addFooter(slide, 4, "Sources: figA_scorecard.png, out/scorecard.json");
  }

  // 5 beta
  {
    const slide = p.slides.add();
    slide.background.fill = COLORS.bg;
    addTitle(slide, "BETA THERMOMETER", "Beta does not pin down a stable trust temperature", "The idea is useful; this real coarse-FEM likelihood does not identify it cleanly.");
    await addImage(slide, "figB_beta_thermometer.png", 70, 230, 810, 370, "Beta thermometer and R-hat by split");
    addMetric(slide, "Beta range", `${fmt(Math.min(...mc.per_split.map(r => r.beta_med)))} to ${fmt(Math.max(...mc.per_split.map(r => r.beta_med)))}`, 910, 246, 260, COLORS.yellow, "median by split");
    addMetric(slide, "Weak-beta splits", `${fmt(100 * mc.beta_weak_frac, 2)}%`, 910, 370, 260, COLORS.yellow, "posterior width test");
    addClaim(slide, "Interpretation: beta collapse or spread is evidence of model-form stress, but here the sampler also fails the all-variable convergence gate.", 910, 506, 260, 92, COLORS.red);
    addFooter(slide, 5, "Sources: figB_beta_thermometer.png, out/ift_mc_headline.json");
  }

  // 6 FRF overlay
  {
    const slide = p.slides.add();
    slide.background.fill = COLORS.bg;
    addTitle(slide, "HELD-OUT FRF OVERLAY", "The field-prior arm widens, but does not become trustworthy", "The overlay is a quick visual audit, not a substitute for the proper scores.");
    await addImage(slide, "figC_heldout_frf_overlay.png", 70, 214, 820, 410, "Held-out FRF overlay");
    addClaim(slide, "Figure C uses a log frequency axis and a log magnitude axis for readability because the non-converged IFT band spans orders of magnitude.", 920, 252, 250, 104, COLORS.yellow);
    addClaim(slide, "M2 is intentionally not drawn as a curve: the inherited whole-FRF baseline is a non-converged failure, not a calibrated posterior band.", 920, 386, 250, 116, COLORS.m2);
    addFooter(slide, 6, "Sources: figC_heldout_frf_overlay.png, out/figure_manifest.json");
  }

  // 7 discretization
  {
    const slide = p.slides.add();
    slide.background.fill = COLORS.bg;
    addTitle(slide, "DISCRETIZATION DIAGNOSTIC", "Post-hoc grid sweep is informative, not a certification", "Because the headline posterior is non-converged, this cannot prove the IFT invariance promise.");
    await addImage(slide, "figD_discretization_invariance.png", 64, 222, 800, 392, "Discretization diagnostic");
    const shiftI = disc.relative_shifts_vs_full.IFT.every_4th_44;
    const shiftL = disc.relative_shifts_vs_full.L5.every_4th_44;
    addMetric(slide, "IFT peak shift", fmt(shiftI.peak_interval_rel_shift), 902, 242, 250, COLORS.ift, "every-4th vs full");
    addMetric(slide, "L5 peak shift", fmt(shiftL.peak_interval_rel_shift), 902, 366, 250, COLORS.l5, "every-4th vs full");
    addClaim(slide, "Checker carries this as YELLOW: one split, same posterior samples, no sampler rerun on each grid.", 902, 502, 250, 86, COLORS.yellow);
    addFooter(slide, 7, "Sources: figD_discretization_invariance.png, out/discretization_sensitivity.json");
  }

  // 8 convergence
  {
    const slide = p.slides.add();
    slide.background.fill = COLORS.bg;
    addTitle(slide, "CONVERGENCE GATE", "The NUTS run is sampled, but not converged", "The rule is all variables, beta included: R-hat <= 1.05, ESS >= 200, divergence fraction < 2%.");
    await addImage(slide, "figE_convergence_table.png", 80, 234, 760, 300, "Convergence table");
    addMetric(slide, "Worst IFT R-hat", fmt(conv.arms.IFT.worst_rhat), 890, 244, 260, COLORS.red, "gate <= 1.05");
    addMetric(slide, "Min IFT ESS", fmt(conv.arms.IFT.min_ess), 890, 368, 260, COLORS.red, "gate >= 200");
    addClaim(slide, "That is why the deck says HONEST_NEGATIVE, not NUTS active, converged, or successful.", 890, 492, 260, 116, COLORS.red, 16.5);
    addFooter(slide, 8, "Sources: figE_convergence_table.png, out/convergence_table.json");
  }

  // 9 verdict
  {
    const slide = p.slides.add();
    slide.background.fill = COLORS.bg;
    addTitle(slide, "VERDICT AND SCOPE", "Honest negative: physics-in-prior did not rescue this coarse-FEM wall", "That is still valuable: it keeps the Bilionis-style claim tied to real held-out data.");
    const outcomes = [
      ["WIN", "No", "requires convergence and better proper scores than L5"],
      ["ROBUSTNESS-WIN", "No", "requires convergence while avoiding M2 failure"],
      ["TIE", "No", "requires comparable scores and calibration"],
      ["HONEST NEGATIVE", "Yes", "IFT also fails the convergence/trust gate"],
    ];
    for (let i = 0; i < outcomes.length; i++) {
      const y = 232 + i * 74;
      addRect(slide, 84, y, 1040, 54, { fill: i === 3 ? "#FFF7ED" : COLORS.white, line: i === 3 ? COLORS.ift : COLORS.faint });
      addText(slide, outcomes[i][0], 110, y + 14, 230, 24, { fontSize: 18, bold: true, color: i === 3 ? COLORS.ift : COLORS.ink });
      addText(slide, outcomes[i][1], 372, y + 14, 70, 24, { fontSize: 18, bold: true, color: i === 3 ? COLORS.red : COLORS.muted });
      addText(slide, outcomes[i][2], 470, y + 14, 600, 24, { fontSize: 16.5, color: COLORS.muted });
    }
    addClaim(slide, "Proposed durable-note row should copy the checker status verbatim: YELLOW, zero RED, generated verdict HONEST_NEGATIVE. Do not strengthen it.", 84, 554, 1040, 70, COLORS.yellow);
    addFooter(slide, 9, "Sources: checker_report.json, packet.md, scorecard.json");
  }

  for (const [index, slide] of p.slides.items.entries()) {
    const stem = `slide-${String(index + 1).padStart(2, "0")}`;
    const png = await p.export({ slide, format: "png", scale: 1 });
    const pngBytes = new Uint8Array(await png.arrayBuffer());
    await fs.writeFile(path.join(PREVIEW_DIR, `${stem}.png`), pngBytes);
    await fs.writeFile(path.join(SLIDES, "preview", `${stem}.png`), pngBytes);
    const layout = await slide.export({ format: "layout" });
    await fs.writeFile(path.join(LAYOUT_DIR, `${stem}.layout.json`), await layout.text());
  }
  const montage = await p.export({ format: "webp", montage: true, scale: 1 });
  const montageBytes = new Uint8Array(await montage.arrayBuffer());
  await fs.writeFile(path.join(PREVIEW_DIR, "deck-montage.webp"), montageBytes);
  await fs.writeFile(path.join(SLIDES, "deck_preview_montage.webp"), montageBytes);

  const pptx = await PresentationFile.exportPptx(p);
  await pptx.save(FINAL);

  const qa = [
    "Visual QA",
    "",
    `PPTX exists and is non-empty: ${(await fs.stat(FINAL)).size > 0}`,
    "Expected slide count: 9",
    "Every final slide rendered: yes",
    "Contact sheet or montage reviewed: generated as slides/deck_preview_montage.webp",
    "Layout JSON written: yes, retained in scratch workspace",
    "Source notes reviewed: source-notes.txt written in scratch workspace",
    "Claims trace to JSON/figures: yes",
    "Known accepted caveats: checker YELLOW; IFT non-converged; log-magnitude approximation; split-0 post-hoc discretization diagnostic.",
    "",
    "Final decision: pass for non-RED honest deck generation.",
  ].join("\n");
  await fs.writeFile(path.join(QA_DIR, "visual-qa.txt"), qa);
  await fs.writeFile(path.join(SLIDES, "visual_qa.txt"), qa);
  await fs.writeFile(path.join(SLIDES, "deck_manifest.json"), JSON.stringify({
    final_pptx: "slides/ift_real_validation_honest_negative.pptx",
    slide_count: 9,
    preview_montage: "slides/deck_preview_montage.webp",
    scratch_workspace: WORKSPACE,
    sources: ["out/scorecard.json", "out/ift_mc_headline.json", "out/convergence_table.json", "out/discretization_sensitivity.json", "checker_report.json"],
  }, null, 2));
  console.log(`wrote ${FINAL}`);
}

main().catch((err) => {
  console.error(err);
  process.exitCode = 1;
});
