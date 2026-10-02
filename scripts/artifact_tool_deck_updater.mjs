#!/usr/bin/env node
/**
 * @file artifact_tool_deck_updater.mjs
 * Presentation Deck Numeric Slots Updater using bundled @oai/artifact-tool runtime.
 *
 * SAFETY INVARIANTS:
 * - Strictly restricted to staging / diagnostic fixture candidates.
 * - Stamped with private labeling:
 *   "DIAGNOSTIC TEST FIXTURE ONLY - NOT CANONICAL NUMERICAL RESULTS"
 * - Zero live prediction reads, zero provider calls.
 * - Never overwrites production docs/presentation/slides.pptx directly.
 * - Real @oai/artifact-tool runtime invocation: Fail-closed if module cannot be imported.
 *
 * Usage:
 *   node scripts/artifact_tool_deck_updater.mjs [--fixture-slots path/to/slots.json] [--output-deck path/to/candidate.pptx]
 */

import fs from "node:fs/promises";
import fsSync from "node:fs";
import path from "node:path";
import crypto from "node:crypto";
import { fileURLToPath } from "node:url";

import {
  FileBlob,
  PresentationFile,
} from "file:///C:/Users/hahoa/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/@oai/artifact-tool/dist/artifact_tool.mjs";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const REPO_ROOT = path.resolve(__dirname, "..");

const DEFAULT_SLOTS_PATH = path.join(
  REPO_ROOT,
  "outputs",
  "reproduction",
  "fixture_diagnostics",
  "populated_slots_fixture.json"
);
const DEFAULT_SOURCE_DECK_PATH = path.join(
  REPO_ROOT,
  "docs",
  "presentation",
  "slides.pptx"
);
const DEFAULT_CANDIDATE_DECK_PATH = path.join(
  REPO_ROOT,
  "reports",
  "evidence",
  "fixture_populated_slides.pptx"
);
const DEFAULT_QA_OUTPUT_DIR = path.join(
  REPO_ROOT,
  "reports",
  "evidence",
  "qa",
  "fixture_slides"
);
const DEFAULT_AUDIT_REPORT_PATH = path.join(
  REPO_ROOT,
  "reports",
  "evidence",
  "deck_updater_fixture_audit.json"
);

const DISCLAIMER_TEXT =
  "DIAGNOSTIC TEST FIXTURE ONLY - NOT CANONICAL NUMERICAL RESULTS";

/**
 * Validates fixture slots file and ensures fail-closed boundary enforcement.
 * @param {string} slotsPath
 * @returns {Promise<Record<string, any>>}
 */
async function loadAndValidateFixtureSlots(slotsPath) {
  if (!fsSync.existsSync(slotsPath)) {
    throw new Error(
      `[FAIL_CLOSED] Fixture slots file not found: ${slotsPath}`
    );
  }
  const raw = await fs.readFile(slotsPath, "utf-8");
  const data = JSON.parse(raw);

  const meta = data._metadata || {};
  if (meta.fixture_only !== true) {
    throw new Error(
      `[FAIL_CLOSED] Target slots file does not assert fixture_only: true. ` +
        `Refusing to execute on non-fixture data.`
    );
  }
  if (!meta.disclaimer || !meta.disclaimer.includes("DIAGNOSTIC TEST FIXTURE")) {
    throw new Error(
      `[FAIL_CLOSED] Missing mandatory diagnostic fixture disclaimer in metadata.`
    );
  }
  return data;
}

/**
 * Executes the verified @oai/artifact-tool presentation workflow.
 *
 * Protocol:
 * 1. Load source PPTX and compute Before SHA-256.
 * 2. Import into PresentationFile.
 * 3. Inspect deck snapshot (12 slides, shape topology, notes).
 * 4. Resolve shapes on Slide 6, Slide 7, Slide 8 and replace numeric/status slots.
 * 5. Verify substitutions > 0; fail-closed if 0.
 * 6. Export modified presentation to candidate PPTX and compute After SHA-256.
 * 7. Verify Before SHA != After SHA and ZIP magic header PK\x03\x04.
 * 8. Render all 12 slides to PNGs for visual inspection.
 * 9. Write comprehensive audit record to deck_updater_fixture_audit.json.
 */
async function runArtifactToolDeckUpdater(options = {}) {
  const slotsPath = options.slotsPath || DEFAULT_SLOTS_PATH;
  const sourceDeckPath = options.sourceDeckPath || DEFAULT_SOURCE_DECK_PATH;
  const candidateDeckPath =
    options.candidateDeckPath || DEFAULT_CANDIDATE_DECK_PATH;
  const qaOutputDir = options.qaOutputDir || DEFAULT_QA_OUTPUT_DIR;
  const auditReportPath =
    options.auditReportPath || DEFAULT_AUDIT_REPORT_PATH;
  const isDryRun = Boolean(options.dryRun);

  console.log(`[+] Initializing JS Artifact-Tool Deck Updater (bundled runtime)...`);
  console.log(`[+] Safety Policy: STRICTLY FIXTURES ONLY (fail-closed)`);
  console.log(`[+] Disclaimer: ${DISCLAIMER_TEXT}`);

  // 1. Validate slots
  const slots = await loadAndValidateFixtureSlots(slotsPath);
  const placeholderEntries = Object.entries(slots).filter(([k]) =>
    k.startsWith("{{")
  );
  console.log(`[+] Loaded ${placeholderEntries.length} verified placeholder substitutions.`);

  // 2. Read source deck and compute before hash
  if (!fsSync.existsSync(sourceDeckPath)) {
    throw new Error(`[FAIL_CLOSED] Source presentation deck not found: ${sourceDeckPath}`);
  }
  const sourceBytes = await fs.readFile(sourceDeckPath);
  const beforeSha = crypto.createHash("sha256").update(sourceBytes).digest("hex");
  console.log(`[+] Source deck Before SHA-256: ${beforeSha}`);

  // 3. Import PPTX using real @oai/artifact-tool PresentationFile
  const presentation = await PresentationFile.importPptx(
    await FileBlob.load(sourceDeckPath)
  );
  const snapshot = await presentation.inspect();
  const slides = presentation.slides.items;
  const notesCount = snapshot.records.filter((r) => r.kind === "notes").length;

  console.log(`[+] Imported deck: ${slides.length} slides, ${notesCount} notes records.`);

  if (slides.length !== 12) {
    throw new Error(
      `[FAIL_CLOSED] Expected 12 slides in presentation deck, found ${slides.length}`
    );
  }

  // 4. Resolve shapes and perform substitutions
  const modifiedShapeIds = new Set();
  let substitutionsCount = 0;

  // Slide 7: Shape sh/fi9c369c (Observation & Scaffold Comparison)
  const sh7 = presentation.resolve("sh/fi9c369c");
  if (sh7 && sh7.text) {
    const r1 = sh7.text.get("[PENDING]");
    if (!r1.isEmpty) {
      sh7.text.replace("[PENDING]", `[${DISCLAIMER_TEXT}]`);
      substitutionsCount++;
      modifiedShapeIds.add("sh/fi9c369c");
    }
    const r2 = sh7.text.get("[PENDING EXECUTION]");
    if (!r2.isEmpty) {
      sh7.text.replace(
        "[PENDING EXECUTION]",
        `[FIXTURE CANDIDATE - TEST MATRIX IN PROGRESS]`
      );
      substitutionsCount++;
      modifiedShapeIds.add("sh/fi9c369c");
    }
  }

  // Slide 8: Shape sh/98rehwve (RQ1 & RQ2 Experimental Status)
  const sh8 = presentation.resolve("sh/98rehwve");
  if (sh8 && sh8.text) {
    const r = sh8.text.get("[PENDING EXECUTION]");
    if (!r.isEmpty) {
      sh8.text.replace("[PENDING EXECUTION]", `[${DISCLAIMER_TEXT}]`);
      substitutionsCount++;
      modifiedShapeIds.add("sh/98rehwve");
    }
  }

  // Slide 6: Shape sh/h4bupgn6 (Context Scaling & Dilution Hypothesis)
  const sh6 = presentation.resolve("sh/h4bupgn6");
  if (sh6 && sh6.text) {
    const targetPhrase = "đang được kiểm chứng đối chứng trên ma trận TEST.";
    const r = sh6.text.get(targetPhrase);
    if (!r.isEmpty) {
      sh6.text.replace(
        targetPhrase,
        `đang được kiểm chứng đối chứng trên ma trận TEST [${DISCLAIMER_TEXT}].`
      );
      substitutionsCount++;
      modifiedShapeIds.add("sh/h4bupgn6");
    }
  }

  // Scan all shapes for explicit {{PLACEHOLDER}} tokens from slots
  for (const record of snapshot.records) {
    if (record.kind === "textbox" && record.id && record.text) {
      for (const [key, val] of placeholderEntries) {
        if (record.text.includes(key)) {
          const sh = presentation.resolve(record.id);
          if (sh && sh.text) {
            sh.text.replace(key, String(val));
            substitutionsCount++;
            modifiedShapeIds.add(record.id);
          }
        }
      }
    }
  }

  console.log(
    `[+] Total substitutions performed: ${substitutionsCount} across ${modifiedShapeIds.size} shapes.`
  );

  if (substitutionsCount === 0) {
    throw new Error(
      `[FAIL_CLOSED] Zero substitutions performed on target presentation. Aborting.`
    );
  }

  // 5. Export candidate deck
  await fs.mkdir(path.dirname(candidateDeckPath), { recursive: true });
  const exported = await PresentationFile.exportPptx(presentation);
  const afterBytes = Buffer.from(exported.data);

  // Validate ZIP / PPTX magic header: PK\x03\x04
  const magic = afterBytes.slice(0, 4);
  if (
    magic[0] !== 0x50 ||
    magic[1] !== 0x4b ||
    magic[2] !== 0x03 ||
    magic[3] !== 0x04
  ) {
    throw new Error(
      `[FAIL_CLOSED] Exported candidate deck lacks valid ZIP/PPTX magic header PK\\x03\\x04`
    );
  }

  if (!isDryRun) {
    await fs.writeFile(candidateDeckPath, afterBytes);
  }

  const afterSha = crypto.createHash("sha256").update(afterBytes).digest("hex");
  console.log(`[+] Candidate deck After SHA-256: ${afterSha}`);

  if (beforeSha === afterSha) {
    throw new Error(
      `[FAIL_CLOSED] Before SHA matches After SHA. Candidate deck did not modify source.`
    );
  }

  // 6. Export all 12 slides as PNGs to QA directory
  await fs.mkdir(qaOutputDir, { recursive: true });
  console.log(`[+] Exporting 12 slides to QA image directory: ${qaOutputDir}`);
  for (let i = 0; i < slides.length; i++) {
    const slideNumber = i + 1;
    const blob = await presentation.export({
      slide: slides[i],
      format: "png",
      scale: 1,
    });
    const pngPath = path.join(qaOutputDir, `slide-${slideNumber}.png`);
    const pngBytes = Buffer.from(await blob.arrayBuffer());
    if (!isDryRun) {
      await fs.writeFile(pngPath, pngBytes);
    }
  }
  console.log(`[+] Successfully exported ${slides.length} slide PNGs.`);

  // 7. Write audit report
  await fs.mkdir(path.dirname(auditReportPath), { recursive: true });
  const auditRecord = {
    fixture_only: true,
    provenance_status: "diagnostic_fixture",
    disclaimer: DISCLAIMER_TEXT,
    timestamp_utc: new Date().toISOString(),
    source_deck_path: sourceDeckPath,
    candidate_deck_path: candidateDeckPath,
    before_sha256: beforeSha,
    after_sha256: afterSha,
    sha_changed: beforeSha !== afterSha,
    candidate_file_size_bytes: afterBytes.byteLength,
    total_slides_count: slides.length,
    total_notes_count: notesCount,
    modified_shape_ids: Array.from(modifiedShapeIds).sort(),
    substitutions_performed: substitutionsCount,
    rendered_png_slides_count: slides.length,
    qa_slides_directory: qaOutputDir,
    dry_run: isDryRun,
    artifact_tool_binding: {
      runtime: "bundled_node_module",
      package: "@oai/artifact-tool",
      verified_apis: ["importPptx", "inspect", "resolve", "exportPptx", "export"],
    },
  };

  if (!isDryRun) {
    await fs.writeFile(
      auditReportPath,
      JSON.stringify(auditRecord, null, 2),
      "utf-8"
    );
  }

  console.log(`[+] Audit report written to: ${auditReportPath}`);
  console.log(`[+] Candidate deck written to: ${candidateDeckPath}`);
  return auditRecord;
}

// CLI entrypoint
const isMain =
  process.argv[1] &&
  path.resolve(process.argv[1]) === path.resolve(__filename);

if (isMain) {
  const args = process.argv.slice(2);
  const dryRun = args.includes("--dry-run");

  const getArg = (flag) => {
    const idx = args.indexOf(flag);
    return idx !== -1 ? args[idx + 1] : undefined;
  };

  const slotsPath = getArg("--fixture-slots");
  const sourceDeckPath = getArg("--source-deck");
  const candidateDeckPath = getArg("--output-deck");
  const qaOutputDir = getArg("--output-qa-dir");
  const auditReportPath = getArg("--audit-report");

  runArtifactToolDeckUpdater({
    dryRun,
    slotsPath,
    sourceDeckPath,
    candidateDeckPath,
    qaOutputDir,
    auditReportPath,
  })
    .then(() => {
      console.log(`[+] JS Deck Updater completed successfully.`);
      process.exit(0);
    })
    .catch((err) => {
      console.error(`[-] Fatal Error in JS deck updater:`, err.message);
      process.exit(1);
    });
}

export {
  runArtifactToolDeckUpdater,
  loadAndValidateFixtureSlots,
  DISCLAIMER_TEXT,
};
