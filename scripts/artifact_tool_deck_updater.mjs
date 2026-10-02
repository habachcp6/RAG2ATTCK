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
 * - Declarative Shape-Table Map: Injects all 59 numeric slots across Slides 4, 6, 7, 8, 9.
 * - Enforces separate counts for numeric_slot_edits (== 59) and disclaimer_edits.
 * - Fail-closed if numeric_slot_edits === 0 or actual_numeric_slots_count !== expected_numeric_slots_count.
 * - Removes legacy causal/intrinsic phrases from Slide 8 and speaker notes.
 *
 * Usage:
 *   node scripts/artifact_tool_deck_updater.mjs [--fixture-slots path/to/slots.json] [--output-deck path/to/candidate.pptx]
 */

import fs from "node:fs/promises";
import fsSync from "node:fs";
import path from "node:path";
import crypto from "node:crypto";
import { fileURLToPath, pathToFileURL } from "node:url";

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
const DEFAULT_MAP_PATH = path.join(
  REPO_ROOT,
  "outputs",
  "reproduction",
  "fixture_diagnostics",
  "declarative_shape_table_map.json"
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
const EXPECTED_NUMERIC_SLOTS_COUNT = 59;

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
 * Loads and validates declarative shape table map.
 * @param {string} mapPath
 * @returns {Promise<Array<Record<string, any>>>}
 */
async function loadAndValidateDeclarativeMap(mapPath) {
  if (!fsSync.existsSync(mapPath)) {
    throw new Error(
      `[FAIL_CLOSED] Declarative shape table map not found: ${mapPath}`
    );
  }
  const raw = await fs.readFile(mapPath, "utf-8");
  const mapData = JSON.parse(raw);
  if (!Array.isArray(mapData) || mapData.length !== EXPECTED_NUMERIC_SLOTS_COUNT) {
    throw new Error(
      `[FAIL_CLOSED] Declarative map must contain exactly ${EXPECTED_NUMERIC_SLOTS_COUNT} items, got ${mapData?.length}`
    );
  }
  for (const item of mapData) {
    if (!item.slot_name || !item.shape_id || !item.slide_number || item.injected_value === undefined) {
      throw new Error(
        `[FAIL_CLOSED] Incomplete declarative map entry: ${JSON.stringify(item)}`
      );
    }
  }
  return mapData;
}

/**
 * Replaces a specific line within a shape textbox using substring matching.
 * @param {any} presentation
 * @param {any} snapshot
 * @param {string} shapeId
 * @param {string} targetSubstring
 * @param {string} replacementLine
 */
function replaceLineInShape(presentation, snapshot, shapeId, targetSubstring, replacementLine) {
  const rec = snapshot.records.find((r) => r.id === shapeId);
  if (!rec) {
    throw new Error(`[FAIL_CLOSED] Shape not found in inspect snapshot: ${shapeId}`);
  }
  const lines = rec.text.split("\n");
  const targetLine = lines.find((l) => l.includes(targetSubstring));
  if (!targetLine) {
    throw new Error(
      `[FAIL_CLOSED] Target substring "${targetSubstring}" not found in shape ${shapeId}`
    );
  }
  const sh = presentation.resolve(shapeId);
  if (!sh || !sh.text) {
    throw new Error(`[FAIL_CLOSED] Could not resolve shape with text: ${shapeId}`);
  }
  sh.text.replace(targetLine, replacementLine);
  rec.text = rec.text.replace(targetLine, replacementLine);
}

/**
 * Resolves the artifact-tool module dynamically across supported runtime locations.
 * Resolution precedence:
 * 1. Explicitly provided module path (via --artifact-tool-module)
 * 2. Process environment variable (ARTIFACT_TOOL_MODULE)
 * 3. Known local cache path if it exists on disk
 * 4. Standard node_modules lookup (@oai/artifact-tool)
 *
 * @param {string} [explicitPath]
 * @returns {Promise<{ PresentationFile: any, FileBlob: any } | null>}
 */
async function resolveArtifactToolModule(explicitPath) {
  const tryImport = async (candidate) => {
    try {
      let target = candidate;
      if (
        path.isAbsolute(candidate) ||
        candidate.startsWith(".") ||
        candidate.startsWith("file://") ||
        fsSync.existsSync(candidate)
      ) {
        if (!candidate.startsWith("file://") && !fsSync.existsSync(candidate)) {
          return null;
        }
        target = candidate.startsWith("file://")
          ? candidate
          : pathToFileURL(path.resolve(candidate)).href;
      }
      const mod = await import(target);
      if (mod && mod.PresentationFile && mod.FileBlob) {
        return {
          PresentationFile: mod.PresentationFile,
          FileBlob: mod.FileBlob,
        };
      }
    } catch {
      return null;
    }
    return null;
  };

  if (explicitPath) {
    return await tryImport(explicitPath);
  }
  if (process.env.ARTIFACT_TOOL_MODULE) {
    return await tryImport(process.env.ARTIFACT_TOOL_MODULE);
  }

  const defaultLocalCache =
    "C:/Users/hahoa/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/@oai/artifact-tool/dist/artifact_tool.mjs";
  if (fsSync.existsSync(defaultLocalCache)) {
    const localMod = await tryImport(defaultLocalCache);
    if (localMod) return localMod;
  }

  return await tryImport("@oai/artifact-tool");
}

/**
 * Executes the verified @oai/artifact-tool presentation workflow.
 */
async function runArtifactToolDeckUpdater(options = {}) {
  const slotsPath = options.slotsPath || DEFAULT_SLOTS_PATH;
  const mapPath = options.mapPath || DEFAULT_MAP_PATH;
  const sourceDeckPath = options.sourceDeckPath || DEFAULT_SOURCE_DECK_PATH;
  const candidateDeckPath =
    options.candidateDeckPath || DEFAULT_CANDIDATE_DECK_PATH;
  const qaOutputDir = options.qaOutputDir || DEFAULT_QA_OUTPUT_DIR;
  const auditReportPath =
    options.auditReportPath || DEFAULT_AUDIT_REPORT_PATH;
  const isDryRun = Boolean(options.dryRun);
  const explicitArtifactToolModule = options.artifactToolModule;

  console.log(`[+] Initializing JS Artifact-Tool Deck Updater (bundled runtime)...`);
  console.log(`[+] Safety Policy: STRICTLY FIXTURES ONLY (fail-closed)`);
  console.log(`[+] Disclaimer: ${DISCLAIMER_TEXT}`);

  // 1. Validate slots and declarative shape table map (dependency-free)
  const slots = await loadAndValidateFixtureSlots(slotsPath);
  const declMap = await loadAndValidateDeclarativeMap(mapPath);
  console.log(`[+] Loaded ${declMap.length} declarative slot definitions.`);

  // 2. Read source deck and compute before hash (dependency-free)
  if (!fsSync.existsSync(sourceDeckPath)) {
    throw new Error(`[FAIL_CLOSED] Source presentation deck not found: ${sourceDeckPath}`);
  }
  const sourceBytes = await fs.readFile(sourceDeckPath);
  const beforeSha = crypto.createHash("sha256").update(sourceBytes).digest("hex");
  console.log(`[+] Source deck Before SHA-256: ${beforeSha}`);

  // 3. Resolve artifact-tool module dynamically
  const artifactTool = await resolveArtifactToolModule(explicitArtifactToolModule);
  if (!artifactTool || !artifactTool.PresentationFile || !artifactTool.FileBlob) {
    throw new Error(
      `[DEPENDENCY_UNAVAILABLE] Required presentation runtime (@oai/artifact-tool) could not be resolved.`
    );
  }
  const { PresentationFile, FileBlob } = artifactTool;

  // 4. Import PPTX using real @oai/artifact-tool PresentationFile
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

  const modifiedShapeIds = new Set();
  let disclaimerEditsCount = 0;

  // 4. Inject Numeric Slots into Slide Shapes

  // Slide 4: Shape sh/sna103ap (Dataset Topology - 6 slots)
  replaceLineInShape(
    presentation,
    snapshot,
    "sh/sna103ap",
    "Phân chia tập:",
    `•  Phân chia tập: ${slots["{{S2_TOTAL_TEST_VIEWS}}"]} TEST views (${slots["{{S2_SCORABLE_VIEWS}}"]} scorable views across ${slots["{{S2_DISTINCT_ELIGIBLE_CLUSTERS}}"]} distinct clusters) và 60 DEV views.`
  );
  replaceLineInShape(
    presentation,
    snapshot,
    "sh/sna103ap",
    "Toàn vẹn mật mã:",
    `•  Toàn vẹn mật mã: Khóa SHA-256 trong lock v1 | Cohort pairs: ${slots["{{S2_COMPLETE_SCORABLE_PAIRS}}"]} complete pairs, ${slots["{{S2_CONTEXTUAL_ONLY_PAIRS}}"]} contextual-only pairs, ${slots["{{S2_NEITHER_MAPPED_PAIRS}}"]} neither-mapped pairs.`
  );
  modifiedShapeIds.add("sh/sna103ap");

  // Slide 6: Shape sh/7m98ru9g (RQ2 Retrieval Quality - 3 slots)
  replaceLineInShape(
    presentation,
    snapshot,
    "sh/7m98ru9g",
    "Hit@10:",
    `  • Hit@10: 45.11% (341 / 756) -> [Diagnostic Fixture: Hit@10 = ${slots["{{S2_HIT_RATE_AT_K}}"]}]`
  );
  replaceLineInShape(
    presentation,
    snapshot,
    "sh/7m98ru9g",
    "Tỷ lệ vắng mặt trong Top-10",
    `•  Tỷ lệ vắng mặt trong Top-10 (Retrieval Failure): 54.89% (415 / 756) -> [Fixture Miss Rate: ${slots["{{S2_RETRIEVAL_MISS_RATE_K10}}"]}]`
  );
  replaceLineInShape(
    presentation,
    snapshot,
    "sh/7m98ru9g",
    "Macro Recall@10:",
    `•  Macro Recall@10: 43.14% [Fixture Macro Recall@10: ${slots["{{S2_RECALL_AT_K}}"]}]  |  Mean Rank khi trúng: 5.21.`
  );
  modifiedShapeIds.add("sh/7m98ru9g");

  // Slide 6: Disclaimer banner sh/h4bupgn6
  const sh6Banner = presentation.resolve("sh/h4bupgn6");
  if (sh6Banner && sh6Banner.text) {
    const targetPhrase = "đang được kiểm chứng đối chứng trên ma trận TEST.";
    const rBanner = sh6Banner.text.get(targetPhrase);
    if (!rBanner.isEmpty) {
      sh6Banner.text.replace(
        targetPhrase,
        `đang được kiểm chứng đối chứng trên ma trận TEST [${DISCLAIMER_TEXT}].`
      );
      disclaimerEditsCount++;
      modifiedShapeIds.add("sh/h4bupgn6");
    }
  }

  // Slide 7: Shape sh/fi9c369c (Pairwise Views Comparison - 12 slots + pending disclaimer)
  const sh7 = presentation.resolve("sh/fi9c369c");
  if (sh7 && sh7.text) {
    const rPending = sh7.text.get("[PENDING]");
    if (!rPending.isEmpty) {
      sh7.text.replace("[PENDING]", `[${DISCLAIMER_TEXT}]`);
      disclaimerEditsCount++;
    }
  }
  replaceLineInShape(
    presentation,
    snapshot,
    "sh/fi9c369c",
    "Schema So Sánh Đối Chứng Scaffold",
    `•  Schema So Sánh Đối Chứng Scaffold [${DISCLAIMER_TEXT}]:\n` +
      `  • Diagnostic Cohort Pairwise Comparison (n=718 views across 440 clusters):\n` +
      `    • Marginal Views: Single-event Acc = ${slots["{{S2_SINGLE_VIEW_ACC_E2E}}"]} vs Contextual-event Acc = ${slots["{{S2_CONTEXT_VIEW_ACC_E2E}}"]} (Delta = ${slots["{{S2_VIEW_ACC_DELTA}}"]})\n` +
      `    • Paired Cohort (278 complete pairs): Single Acc = ${slots["{{S2_PAIRED_SINGLE_ACC}}"]} vs Context Acc = ${slots["{{S2_PAIRED_CONTEXT_ACC}}"]} (Delta = ${slots["{{S2_PAIRED_DELTA_PP}}"]} pp)\n` +
      `    • Pair Concordance: Both Correct = ${slots["{{S2_BOTH_CORRECT_COUNT}}"]}, Single-only Correct = ${slots["{{S2_SINGLE_ONLY_CORRECT}}"]}, Context-only Correct = ${slots["{{S2_CONTEXT_ONLY_CORRECT}}"]}, Both Incorrect = ${slots["{{S2_BOTH_INCORRECT_COUNT}}"]}\n` +
      `    • McNemar Exploratory Test: p_asympt = ${slots["{{S2_MCNEMAR_P_ASYMPT}}"]}, p_exact = ${slots["{{S2_MCNEMAR_P_EXACT}}"]}`
  );
  modifiedShapeIds.add("sh/fi9c369c");

  // Slide 7: Speaker note nt/gnmp4jqx (remove pending execution / causal claim)
  const nt7 = presentation.resolve("nt/gnmp4jqx");
  if (nt7 && typeof nt7.text === "string") {
    const oldText7 =
      "[PENDING EXECUTION] chờ toàn bộ ma trận TEST hoàn tất để đưa ra kết luận khoa học chính thức.";
    if (nt7.text.includes(oldText7)) {
      nt7.text = nt7.text.replace(
        oldText7,
        `[${DISCLAIMER_TEXT}]; kết quả đối chứng trên diagnostic cohort (n=718 views across 440 clusters) ghi nhận quan sát mô tả độc lập.`
      );
      disclaimerEditsCount++;
    }
  }

  // Slide 8: Shape sh/98rehwve (RQ1 5 conditions table & RQ2 error decomposition - 23 slots)
  const sh98 = presentation.resolve("sh/98rehwve");
  sh98.text.color = "#0F172A";
  sh98.text.fontSize = 11;
  sh98.text.bold = false;

  const header8 = `[${DISCLAIMER_TEXT}]`;
  const table8 = [
    header8,
    "Bảng Đối Chứng Hiệu Năng RQ1 (Diagnostic Fixture):",
    "Condition      Accuracy    Macro-F1    Delta vs No-RAG",
    "-------------------------------------------------------",
    `no_rag         ${slots["{{S2_ACC_E2E_NO_RAG}}"]}      ${slots["{{S2_MACRO_F1_NO_RAG}}"]}      baseline`,
    `rag_k1         ${slots["{{S2_ACC_E2E_RAG_K1}}"]}      ${slots["{{S2_MACRO_F1_RAG_K1}}"]}      ${slots["{{S2_BEST_RAG_ACC_DELTA}}"]} (${slots["{{S2_BEST_RAG_F1_DELTA}}"]} F1)`,
    `rag_k3         ${slots["{{S2_ACC_E2E_RAG_K3}}"]}      ${slots["{{S2_MACRO_F1_RAG_K3}}"]}      ${slots["{{S2_BEST_RAG_ACC_DELTA}}"]} (${slots["{{S2_BEST_RAG_F1_DELTA}}"]} F1)`,
    `rag_k5         ${slots["{{S2_ACC_E2E_RAG_K5}}"]}      ${slots["{{S2_MACRO_F1_RAG_K5}}"]}      ${slots["{{S2_BEST_RAG_ACC_DELTA}}"]} (${slots["{{S2_BEST_RAG_F1_DELTA}}"]} F1)`,
    `rag_k10        ${slots["{{S2_ACC_E2E_RAG_K10}}"]}      ${slots["{{S2_MACRO_F1_RAG_K10}}"]}      ${slots["{{S2_BEST_RAG_ACC_DELTA}}"]} (${slots["{{S2_BEST_RAG_F1_DELTA}}"]} F1)`,
    `★ Best Condition: ${slots["{{S2_BEST_RAG_CONDITION}}"]} (Delta Acc = ${slots["{{S2_BEST_RAG_ACC_DELTA}}"]}, Delta F1 = ${slots["{{S2_BEST_RAG_F1_DELTA}}"]})`,
    `• 95% CI: no_rag/k1/k3/k5/k10 = ${slots["{{S2_CI_95_NO_RAG}}"]} (chi tiết trong Speaker Notes)`,
    `• RQ2 Phân rã lỗi (k=10): Wrong Class = ${slots["{{S2_WRONG_CLASS_RATE_K10}}"]} | Overlaps: Miss&Wrong=${slots["{{S2_OVERLAP_MISS_AND_WRONG_K10}}"]}, Prov=${slots["{{S2_OVERLAP_MISS_AND_PROV_K10}}"]}, Parse=${slots["{{S2_OVERLAP_MISS_AND_PARSE_K10}}"]}, Inval=${slots["{{S2_OVERLAP_MISS_AND_INVAL_K10}}"]}`,
  ].join("\n");

  const rec98 = snapshot.records.find((r) => r.id === "sh/98rehwve");
  sh98.text.replace(rec98.text, table8);
  rec98.text = table8;

  // Style header red and small
  const rH8 = sh98.text.get(header8);
  if (!rH8.isEmpty) {
    rH8.color = "#DC2626";
    rH8.fontSize = 9.5;
    rH8.bold = true;
  }
  disclaimerEditsCount++;
  modifiedShapeIds.add("sh/98rehwve");

  // Slide 8: Shape sh/id0fu50z (Conditional metrics & failure axes - 5 slots + causal phrase removal)
  replaceLineInShape(
    presentation,
    snapshot,
    "sh/id0fu50z",
    "P(Correct | GT in Top-k)",
    `•  P(Correct | GT Retrieved) = ${slots["{{S2_P_CORRECT_GIVEN_RETRIEVED}}"]}: Xác suất gán đúng quan sát được khi kỹ thuật mục tiêu hiện diện trong Top-k.`
  );
  replaceLineInShape(
    presentation,
    snapshot,
    "sh/id0fu50z",
    "P(Correct | GT NOT in Top-k)",
    `•  P(Correct | GT Absent) = ${slots["{{S2_P_CORRECT_GIVEN_ABSENT}}"]}: Xác suất gán đúng quan sát được khi kỹ thuật mục tiêu vắng mặt trong Top-k (không giả định tự sửa sai nội tại).`
  );
  replaceLineInShape(
    presentation,
    snapshot,
    "sh/id0fu50z",
    "Fail-Closed Invariant",
    `•  Fail-Closed Invariant: Provider Fail = ${slots["{{S2_PROVIDER_FAIL_RATE_K10}}"]}, Parse Fail = ${slots["{{S2_PARSE_FAIL_RATE_K10}}"]}, Invalid ID = ${slots["{{S2_INVALID_ATTACK_ID_RATE_K10}}"]} (tính vào mẫu số).`
  );
  modifiedShapeIds.add("sh/id0fu50z");

  // Slide 8: Speaker note nt/fu1gfa1s (remove causal phrase "tự sửa sai" + add secondary stats)
  const nt8 = presentation.resolve("nt/fu1gfa1s");
  if (nt8 && typeof nt8.text === "string") {
    let noteText = nt8.text;
    const oldCausal8 = "hay có khả năng tự sửa sai.";
    if (noteText.includes(oldCausal8)) {
      noteText = noteText.replace(
        oldCausal8,
        "hay có thể gán đúng khi thiếu ngữ cảnh truy xuất (không giả định năng lực tự sửa sai nội tại)."
      );
      disclaimerEditsCount++;
    }
    const secondaryStats =
      `\n[DIAGNOSTIC TEST FIXTURE STATS] Khoảng tin cậy 95% Bootstrap (B=1000): ` +
      `no_rag=${slots["{{S2_CI_95_NO_RAG}}"]}, rag_k1=${slots["{{S2_CI_95_RAG_K1}}"]}, ` +
      `rag_k3=${slots["{{S2_CI_95_RAG_K3}}"]}, rag_k5=${slots["{{S2_CI_95_RAG_K5}}"]}, ` +
      `rag_k10=${slots["{{S2_CI_95_RAG_K10}}"]}. ` +
      `Đo lường phân rã lỗi D2i độc lập: Wrong Class Rate=${slots["{{S2_WRONG_CLASS_RATE_K10}}"]}, ` +
      `Overlaps (Miss & Wrong=${slots["{{S2_OVERLAP_MISS_AND_WRONG_K10}}"]}, ` +
      `Miss & Prov=${slots["{{S2_OVERLAP_MISS_AND_PROV_K10}}"]}, ` +
      `Miss & Parse=${slots["{{S2_OVERLAP_MISS_AND_PARSE_K10}}"]}, ` +
      `Miss & Inval=${slots["{{S2_OVERLAP_MISS_AND_INVAL_K10}}"]}).`;
    if (!noteText.includes("[DIAGNOSTIC TEST FIXTURE STATS]")) {
      noteText += secondaryStats;
    }
    nt8.text = noteText;
  }

  // Slide 9: Subtitle sh/mdonql4z (Provenance clarification)
  const shSub9 = presentation.resolve("sh/mdonql4z");
  if (shSub9 && shSub9.text) {
    const targetSub9 =
      "Dữ liệu DEV pilot (synthetic split), hạch toán token ước tính và kiểm soát ngân sách";
    const rSub = shSub9.text.get(targetSub9);
    if (!rSub.isEmpty) {
      shSub9.text.replace(
        targetSub9,
        `Dữ liệu DEV pilot (synthetic split) đối chiếu Dự phóng Hạch toán Fixture [DIAGNOSTIC TEST FIXTURE ONLY]`
      );
      disclaimerEditsCount++;
      modifiedShapeIds.add("sh/mdonql4z");
    }
  }

  // Slide 9: Shape sh/ofq5svm5 (Separate DEV pilot telemetry vs Diagnostic Fixture Projection - 10 slots)
  const shOfq = presentation.resolve("sh/ofq5svm5");
  shOfq.text.fontSize = 11;
  const slide9Content = [
    `DEV Pilot Telemetry & Hạch Toán Dự Phóng [${DISCLAIMER_TEXT}]`,
    "",
    "▶ [HISTORICAL DEV PILOT BASELINE (20 Requests)]",
    "• Bản chất: DEV split tổng hợp (4 views x 5 điều kiện). Gửi request thực tế không biến log tổng hợp thành in-the-wild telemetry.",
    "• Quy mô: 20 requests thực tế Responses API (100% VALID, 0 retry, trễ TB 8,127.6 ms).",
    "• Tiêu thụ tài nguyên & chi phí quan sát được (Observed Telemetry):",
    `  • no_rag (k=0): ${slots["{{S2_MEAN_PROMPT_TOK_NO_RAG}}"]} mean prompt tokens, med lat ${slots["{{S2_MEDIAN_LAT_NO_RAG_SEC}}"]}s (~${slots["{{S2_COST_LOGICAL_REQ_NO_RAG}}"]} USD / logical req)`,
    `  • rag_k10 (k=10): ${slots["{{S2_MEAN_PROMPT_TOK_K10}}"]} mean prompt tokens, med lat ${slots["{{S2_MEDIAN_LAT_K10_SEC}}"]}s (~${slots["{{S2_COST_LOGICAL_REQ_K10}}"]} USD / logical req)`,
    `  • Giữ chỗ thận trọng tạm thời: ${slots["{{S2_PRIOR_PILOT_HOLD_USD}}"]} USD (prior_pilot_provisional_hold_usd).`,
    "",
    "▶ [DIAGNOSTIC FIXTURE PROJECTION (N=718 SCORABLE VIEWS)]",
    "• Hạch toán toàn thể nghiên cứu theo fixture (Whole Study Accounting Fixture):",
    `  • Hạch toán điều kiện chuẩn (Canonical Total): ${slots["{{S2_CANONICAL_TOTAL_USD}}"]} USD cho 6,400 requests.`,
    `  • Ngân sách chưa cam kết còn lại (Net Remaining): ${slots["{{S2_NET_REMAINING_USD}}"]} USD.`,
    `  • Trần ngân sách đóng băng cứng: ${slots["{{S2_TOTAL_STUDY_BUDGET_USD}}"]} USD (hard_budget_limit_usd).`,
  ].join("\n");

  const recOfq = snapshot.records.find((r) => r.id === "sh/ofq5svm5");
  shOfq.text.replace(recOfq.text, slide9Content);
  recOfq.text = slide9Content;
  disclaimerEditsCount++;
  modifiedShapeIds.add("sh/ofq5svm5");

  // Slide 9: Card sh/oza1gfyh (Bottom right summary card)
  const shOza = presentation.resolve("sh/oza1gfyh");
  if (shOza && shOza.text) {
    const targetOza =
      "•  Dự báo chuẩn tắc tập TEST (< $10 USD) nằm an toàn dưới trần ngân sách đóng băng $19.99 USD.";
    const rOza = shOza.text.get(targetOza);
    if (!rOza.isEmpty) {
      shOza.text.replace(
        targetOza,
        `•  Dự báo chuẩn tắc tập TEST: ${slots["{{S2_CANONICAL_TOTAL_USD}}"]} USD nằm an toàn dưới trần ngân sách đóng băng ${slots["{{S2_TOTAL_STUDY_BUDGET_USD}}"]} USD [DIAGNOSTIC FIXTURE].`
      );
      disclaimerEditsCount++;
      modifiedShapeIds.add("sh/oza1gfyh");
    }
  }

  // Slide 9: Speaker note nt/udsvah03 (Clarify canonical forecast vs historical pilot)
  const nt9 = presentation.resolve("nt/udsvah03");
  if (nt9 && typeof nt9.text === "string") {
    const oldForecast9 = "$8.20 – $8.99 USD cho 6,400 requests";
    if (nt9.text.includes(oldForecast9)) {
      nt9.text = nt9.text.replace(
        oldForecast9,
        `hạch toán điều kiện chuẩn $${slots["{{S2_CANONICAL_TOTAL_USD}}"]} USD (dự báo 6,400 requests) [DIAGNOSTIC FIXTURE PROJECTION]`
      );
      disclaimerEditsCount++;
    }
  }

  // 5. Verify all 59 declarative slot entries are injected into shapes
  let actualNumericSlotsCount = 0;
  const enrichedDeclarativeMapping = [];

  for (const item of declMap) {
    const sh = presentation.resolve(item.shape_id);
    if (!sh || !sh.text) {
      throw new Error(
        `[FAIL_CLOSED] Declarative slot target shape ${item.shape_id} not found or has no text`
      );
    }
    const shapeContent =
      typeof sh.text === "string" ? sh.text : sh.text.toString();
    if (!shapeContent || !shapeContent.includes(item.injected_value)) {
      throw new Error(
        `[FAIL_CLOSED] Numeric value injection failed for slot "${item.slot_name}". ` +
          `Expected value "${item.injected_value}" not found in shape ${item.shape_id}`
      );
    }
    actualNumericSlotsCount++;
    enrichedDeclarativeMapping.push({
      slot_name: item.slot_name,
      input_field: item.input_field,
      units: item.units,
      source_pointer: item.source_pointer,
      shape_id: item.shape_id,
      slide_number: item.slide_number,
      injected_value: item.injected_value,
    });
  }

  console.log(
    `[+] Declarative verification: ${actualNumericSlotsCount} / ${EXPECTED_NUMERIC_SLOTS_COUNT} slots verified.`
  );

  if (actualNumericSlotsCount !== EXPECTED_NUMERIC_SLOTS_COUNT) {
    throw new Error(
      `[FAIL_CLOSED] Actual numeric slots count (${actualNumericSlotsCount}) does not match expected (${EXPECTED_NUMERIC_SLOTS_COUNT})`
    );
  }

  const numericSlotEdits = actualNumericSlotsCount;
  if (numericSlotEdits === 0) {
    throw new Error(
      `[FAIL_CLOSED] Zero numeric slot edits performed on target presentation. Aborting.`
    );
  }

  const totalSubstitutions = numericSlotEdits + disclaimerEditsCount;
  console.log(
    `[+] Total substitutions performed: ${totalSubstitutions} ` +
      `(${numericSlotEdits} numeric slots, ${disclaimerEditsCount} disclaimer/causal edits) ` +
      `across ${modifiedShapeIds.size} shapes.`
  );

  // 6. Export candidate deck
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

  // 7. Export all 12 slides as PNGs to QA directory
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

  // 8. Write comprehensive audit report
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
    expected_numeric_slots_count: EXPECTED_NUMERIC_SLOTS_COUNT,
    actual_numeric_slots_count: actualNumericSlotsCount,
    numeric_slot_edits: numericSlotEdits,
    disclaimer_edits: disclaimerEditsCount,
    substitutions_performed: totalSubstitutions,
    declarative_mapping: enrichedDeclarativeMapping,
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
  const mapPath = getArg("--declarative-map");
  const sourceDeckPath = getArg("--source-deck");
  const candidateDeckPath = getArg("--output-deck");
  const qaOutputDir = getArg("--output-qa-dir");
  const auditReportPath = getArg("--audit-report");
  const artifactToolModule = getArg("--artifact-tool-module");

  runArtifactToolDeckUpdater({
    dryRun,
    slotsPath,
    mapPath,
    sourceDeckPath,
    candidateDeckPath,
    qaOutputDir,
    auditReportPath,
    artifactToolModule,
  })
    .then(() => {
      console.log(`[+] JS Deck Updater completed successfully.`);
      process.exit(0);
    })
    .catch((err) => {
      console.error(`[-] Fatal Error in JS deck updater:`, err.message);
      if (err.message && err.message.includes("[DEPENDENCY_UNAVAILABLE]")) {
        process.exit(2);
      }
      process.exit(1);
    });
}

export {
  runArtifactToolDeckUpdater,
  resolveArtifactToolModule,
  loadAndValidateFixtureSlots,
  loadAndValidateDeclarativeMap,
  DISCLAIMER_TEXT,
  EXPECTED_NUMERIC_SLOTS_COUNT,
};
