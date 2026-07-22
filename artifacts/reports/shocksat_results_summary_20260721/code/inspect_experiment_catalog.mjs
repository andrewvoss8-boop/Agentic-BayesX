#!/usr/bin/env node
import fs from "node:fs/promises";
import path from "node:path";
import { FileBlob, SpreadsheetFile } from "@oai/artifact-tool";

const inputPath = process.argv[2];
const outputDir = process.argv[3];
if (!inputPath || !outputDir) {
  throw new Error("usage: inspect_experiment_catalog.mjs INPUT.xlsx OUTPUT_DIR");
}

await fs.mkdir(outputDir, { recursive: true });
const input = await FileBlob.load(inputPath);
const workbook = await SpreadsheetFile.importXlsx(input);

const summary = await workbook.inspect({
  kind: "workbook,sheet,table",
  maxChars: 12000,
  tableMaxRows: 8,
  tableMaxCols: 14,
  tableMaxCellChars: 160,
});
await fs.writeFile(path.join(outputDir, "workbook_summary.ndjson"), summary.ndjson + "\n");

const records = summary.ndjson
  .split(/\r?\n/)
  .filter(Boolean)
  .map((line) => {
    try { return JSON.parse(line); } catch { return null; }
  })
  .filter(Boolean);
const sheetNames = [...new Set(records
  .filter((record) => record.kind === "sheet" || record.type === "sheet")
  .map((record) => record.name || record.sheetName)
  .filter(Boolean))];

if (sheetNames.length === 0) {
  throw new Error(`No worksheet names found in inspect output:\n${summary.ndjson}`);
}

const manifest = { input: inputPath, sheets: [] };
for (const sheetName of sheetNames) {
  const safe = sheetName.replace(/[^A-Za-z0-9_.-]+/g, "_");
  const region = await workbook.inspect({
    kind: "region",
    sheetId: sheetName,
    range: "A1:AZ250",
    maxChars: 50000,
    tableMaxRows: 250,
    tableMaxCols: 52,
    tableMaxCellChars: 500,
  });
  await fs.writeFile(path.join(outputDir, `${safe}_region.ndjson`), region.ndjson + "\n");

  const preview = await workbook.render({
    sheetName,
    autoCrop: "all",
    scale: 1.5,
    format: "png",
  });
  const previewName = `${safe}.png`;
  await fs.writeFile(
    path.join(outputDir, previewName),
    new Uint8Array(await preview.arrayBuffer()),
  );
  manifest.sheets.push({ name: sheetName, region: `${safe}_region.ndjson`, preview: previewName });
}

await fs.writeFile(path.join(outputDir, "manifest.json"), JSON.stringify(manifest, null, 2) + "\n");
console.log(JSON.stringify(manifest, null, 2));
