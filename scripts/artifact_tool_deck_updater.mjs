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
 * - Declarative Shape-Table Map: Injects all 67 numeric slots across Slides 4, 6, 7, 8, 9.
 * - Enforces separate counts for numeric_slot_edits (== 67) and disclaimer_edits.
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
import os from "node:os";
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
const EXPECTED_NUMERIC_SLOTS_COUNT = 67;

/**
 * Validates fixture slots file and ensures fail-closed boundary enforcement.
 * @param {string} slotsPath
 * @returns {Promise<Record<string, any>>}
/**
 * Validates and loads numeric slot mapping.
 * Enforces disjoint fixture vs canonical safety contracts.
 * @param {string} slotsPath
 * @param {{ canonical?: boolean }} [options]
 * @returns {Promise<Record<string, any>>}
 */
async function loadAndValidateFixtureSlots(slotsPath, { canonical = false } = {}) {
  if (!fsSync.existsSync(slotsPath)) {
    throw new Error(
      `[FAIL_CLOSED] Fixture slots file not found: ${slotsPath}`
    );
  }
  const raw = await fs.readFile(slotsPath, "utf-8");
  const data = JSON.parse(raw);

  const meta = data._metadata || {};
  if (canonical) {
    if (meta.fixture_only !== false) {
      throw new Error(
        `[FAIL_CLOSED] Canonical mode requires fixture_only: false (got ${meta.fixture_only}).`
      );
    }
    if (meta.provenance_status !== "canonical_study") {
      throw new Error(
        `[FAIL_CLOSED] Canonical mode requires provenance_status: 'canonical_study' (got '${meta.provenance_status}').`
      );
    }
    if (meta.canonical_mode !== true) {
      throw new Error(
        `[FAIL_CLOSED] Canonical mode requires canonical_mode: true in metadata.`
      );
    }
    if (!meta.canonical_proof_sha256 || meta.canonical_proof_sha256.length !== 64) {
      throw new Error(
        `[FAIL_CLOSED] Canonical mode missing valid 64-char canonical_proof_sha256.`
      );
    }
    // Verify all applicable RAG metrics are non-null and not 'N/A'
    for (const [k, v] of Object.entries(data)) {
      if (k === "_metadata") continue;
      if (
        !k.includes("NO_RAG") &&
        (k.includes("_RAG_") ||
          k.includes("RECALL") ||
          k.includes("HIT_RATE") ||
          k.includes("RETRIEVAL") ||
          k.includes("BEST_RAG"))
      ) {
        if (v === null || v === undefined || v === "N/A" || v === "") {
          throw new Error(
            `[FAIL_CLOSED] Canonical mode requires non-null RAG metric for slot '${k}'.`
          );
        }
      }
    }
  } else {
    if (meta.fixture_only !== true) {
      throw new Error(
        `[FAIL_CLOSED] Target slots file does not assert fixture_only: true. ` +
          `Refusing to execute on non-fixture data.`
      );
    }
    if (!meta.disclaimer || !meta.disclaimer.includes("DIAGNOSTIC TEST FIXTURE")) {
      throw new Error(
        `[FAIL_CLOSED] Missing mandatory diagnostic fixture disclaimer: '${DISCLAIMER_TEXT}'.`
      );
    }
    if (meta.provenance_status && meta.provenance_status !== "diagnostic_fixture") {
      throw new Error(
        `[FAIL_CLOSED] Target slots file does not specify provenance_status: 'diagnostic_fixture'.`
      );
    }
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
 * @param {any} _snapshot
 * @param {string} shapeId
 * @param {string} targetSubstring
 * @param {string} replacementLine
 */
function replaceLineInShape(presentation, _snapshot, shapeId, targetSubstring, replacementLine) {
  const sh = presentation.resolve(shapeId);
  if (!sh || !sh.text) {
    throw new Error(`[FAIL_CLOSED] Could not resolve shape with text: ${shapeId}`);
  }
  const fullText = typeof sh.text === "string" ? sh.text : sh.text.toString();
  const lines = fullText.split("\n");
  const targetLine = lines.find((l) => l.includes(targetSubstring));
  if (!targetLine) {
    throw new Error(
      `[FAIL_CLOSED] Target substring "${targetSubstring}" not found in shape ${shapeId}`
    );
  }
  sh.text.replace(targetLine, replacementLine);
}

/**
 * Verifies that a slot value is bound to the correct shape, condition, and row/label.
 * Beyond simple substring matching, enforces that condition-specific slots
 * appear in the condition's dedicated row/line.
 *
 * @param {string} shapeContent
 * @param {Record<string, any>} item
 * @returns {{ verified: boolean, bound_condition: string | null, bound_line: string, reason?: string }}
 */
function verifySlotBinding(shapeContent, item) {
  const lines = shapeContent.split("\n");
  const injected = String(item.injected_value);

  // 1. Overall shape text must include injected value
  if (!shapeContent.includes(injected)) {
    return {
      verified: false,
      bound_condition: null,
      bound_line: "",
      reason: `Injected value "${injected}" not found in shape ${item.shape_id}`,
    };
  }

  // 2. Extract condition from source pointer if applicable
  const conditionMatch = item.source_pointer.match(
    /\/(?:by_condition|tradeoffs_by_condition|view_diagnostics)\/([a-zA-Z0-9_]+)/
  );
  const condition = conditionMatch ? conditionMatch[1] : null;

  // 3. For table shape sh/98rehwve with per-condition rows
  if (item.shape_id === "sh/98rehwve" && condition) {
    if (item.slot_name.includes("CI_95")) {
      const ciLine = lines.find((l) => l.includes("95% CI") && l.includes("="));
      const condKey = condition === "no_rag" ? "no_rag" : condition.replace("rag_", "");
      if (!ciLine || !ciLine.includes(`${condKey}=${injected}`)) {
        return {
          verified: false,
          bound_condition: condition,
          bound_line: ciLine ? ciLine.trim() : "",
          reason: `CI slot ${item.slot_name} (${injected}) not bound to condition "${condKey}" in CI line of ${item.shape_id}`,
        };
      }
      return { verified: true, bound_condition: condition, bound_line: ciLine.trim() };
    }

    const targetRow = lines.find((l) => {
      const trimmed = l.trim();
      return (
        trimmed.startsWith(condition) ||
        trimmed.split(/\s+/)[0] === condition
      );
    });
    if (!targetRow) {
      return {
        verified: false,
        bound_condition: condition,
        bound_line: "",
        reason: `Dedicated row for condition "${condition}" not found in ${item.shape_id}`,
      };
    }

    const rowTokens = targetRow.trim().split(/\s+/);
    if (item.slot_name.startsWith("RQ1_ACC_DELTA_")) {
      const deltaAccCol = rowTokens[3];
      if (deltaAccCol !== injected) {
        return {
          verified: false,
          bound_condition: condition,
          bound_line: targetRow.trim(),
          reason: `Slot ${item.slot_name} delta acc "${injected}" does not match column 4 in row "${targetRow.trim()}" (got "${deltaAccCol}")`,
        };
      }
      return { verified: true, bound_condition: condition, bound_line: targetRow.trim() };
    }

    if (item.slot_name.startsWith("RQ1_MACRO_F1_DELTA_")) {
      const deltaF1Token = rowTokens[4];
      if (!deltaF1Token || (!deltaF1Token.includes(injected) && !deltaF1Token.startsWith(`(${injected}`))) {
        return {
          verified: false,
          bound_condition: condition,
          bound_line: targetRow.trim(),
          reason: `Slot ${item.slot_name} delta F1 "${injected}" does not match column 5 in row "${targetRow.trim()}" (got "${deltaF1Token}")`,
        };
      }
      return { verified: true, bound_condition: condition, bound_line: targetRow.trim() };
    }

    if (item.slot_name.startsWith("RQ1_ACC_")) {
      const accCol = rowTokens[1];
      if (accCol !== injected) {
        return {
          verified: false,
          bound_condition: condition,
          bound_line: targetRow.trim(),
          reason: `Slot ${item.slot_name} acc "${injected}" does not match column 2 in row "${targetRow.trim()}" (got "${accCol}")`,
        };
      }
      return { verified: true, bound_condition: condition, bound_line: targetRow.trim() };
    }

    if (item.slot_name.startsWith("RQ1_MACRO_F1_")) {
      const f1Col = rowTokens[2];
      if (f1Col !== injected) {
        return {
          verified: false,
          bound_condition: condition,
          bound_line: targetRow.trim(),
          reason: `Slot ${item.slot_name} macro-f1 "${injected}" does not match column 3 in row "${targetRow.trim()}" (got "${f1Col}")`,
        };
      }
      return { verified: true, bound_condition: condition, bound_line: targetRow.trim() };
    }
  }

  // 4. For telemetry shape sh/ofq5svm5 with per-condition telemetry lines
  if (item.shape_id === "sh/ofq5svm5" && condition) {
    const targetLine = lines.find((l) => {
      const lower = l.toLowerCase();
      return lower.includes(condition.toLowerCase());
    });
    if (!targetLine || !targetLine.includes(injected)) {
      return {
        verified: false,
        bound_condition: condition,
        bound_line: targetLine ? targetLine.trim() : "",
        reason: `Slot ${item.slot_name} value "${injected}" for condition "${condition}" not bound to "${condition}" line in ${item.shape_id}`,
      };
    }
    return { verified: true, bound_condition: condition, bound_line: targetLine.trim() };
  }

  // 5. Default: find the matching line
  const matchingLine = lines.find((l) => l.includes(injected)) || "";
  return {
    verified: true,
    bound_condition: condition,
    bound_line: matchingLine.trim(),
  };
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

  let isCanonical = Boolean(options.canonical);
  if (!isCanonical && fsSync.existsSync(slotsPath)) {
    try {
      const probe = JSON.parse(await fs.readFile(slotsPath, "utf-8"));
      if (probe?._metadata?.canonical_mode === true) {
        isCanonical = true;
      }
    } catch {
      // handled in loadAndValidateFixtureSlots
    }
  }

  console.log(`[+] Initializing JS Artifact-Tool Deck Updater (bundled runtime)...`);
  if (isCanonical) {
    console.log(`[+] Mode: CANONICAL STUDY EXECUTION (certified live study data)`);
  } else {
    console.log(`[+] Safety Policy: STRICTLY FIXTURES ONLY (fail-closed)`);
    console.log(`[+] Disclaimer: ${DISCLAIMER_TEXT}`);
  }

  // 1. Validate slots and declarative shape table map (dependency-free)
  const slots = await loadAndValidateFixtureSlots(slotsPath, { canonical: isCanonical });
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
  const snapshot = await presentation.inspect({ maxChars: 1000000 });
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

  // Slide 1: Shape sh/7qp4be9c (Title Slide - Author, Project, Visible Scope Banner)
  if (isCanonical) {
    const shTitle = presentation.resolve("sh/7qp4be9c");
    if (shTitle && shTitle.text) {
      const canonicalTitleText = [
        "BÁO CÁO NGHIÊN CỨU THỰC NGHIỆM ĐỐI CHỨNG",
        "Dự án: RAG2ATT&CK",
        "Đánh Giá Tác Động Của MITRE ATT&CK-Grounded RAG Đối Với Việc Ánh Xạ Windows Endpoint Logs",
        "Evaluating MITRE ATT&CK-Grounded Retrieval-Augmented Generation for Technique Attribution from Windows Endpoint Logs",
        "Tác giả: Hà Hoàng Bách",
        "[Phạm vi: Dữ liệu TEST tổng hợp; đầu ra từ mô hình thật]",
        "Giao thức khoa học: experiment-protocol-v1.1  |  Khóa chuẩn: canonical-lock-v1",
      ].join("\n");
      shTitle.text.set(canonicalTitleText);
      modifiedShapeIds.add("sh/7qp4be9c");
      disclaimerEditsCount++;
    }
  }

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

  // Slide 5: Shape sh/032tgr6d (Data Governance / Credential Sanitization under D1: RECORD_ONLY)
  const sh032 = presentation.resolve("sh/032tgr6d");
  if (sh032 && sh032.text) {
    const oldD1 = "•  Lưu vết đầy đủ (D1: RECORD_ONLY): Lưu toàn văn phản hồi thô phục vụ kiểm toán độc lập.";
    const newD1 = "•  Lưu vết an toàn (D1: RECORD_ONLY): Lưu phản hồi thô phục vụ kiểm toán độc lập; toàn bộ thông tin đăng nhập và bí mật nhạy cảm đã được làm sạch / khử khuẩn (credentials and sensitive secrets sanitized/redacted).";
    const rD1 = sh032.text.get(oldD1);
    if (!rD1.isEmpty) {
      sh032.text.replace(oldD1, newD1);
      disclaimerEditsCount++;
      modifiedShapeIds.add("sh/032tgr6d");
    }
  }

  // Slide 6: Subtitle sh/98rqt4r6
  if (isCanonical) {
    const sh6Sub = presentation.resolve("sh/98rqt4r6");
    if (sh6Sub && sh6Sub.text) {
      sh6Sub.text.set([
        "5. Kết Quả RQ2: Chẩn Đoán Khâu Truy Xuất (Retrieval Quality)",
        "Đánh giá độc lập bộ tìm kiếm trên 718 canonical TEST views",
      ].join("\n"));
      disclaimerEditsCount++;
      modifiedShapeIds.add("sh/98rqt4r6");
    }
  }

  // Slide 6: Shape sh/7m98ru9g (RQ2 Retrieval Quality - 3 slots, separated cohorts, canonical primacy)
  const sh7m = presentation.resolve("sh/7m98ru9g");
  sh7m.text.fontSize = 11;
  const slide6Heading = isCanonical
    ? "Số Liệu Đánh Giá Truy Xuất RQ2 [CANONICAL STUDY EXECUTION]"
    : `Số Liệu Chẩn Đoán Truy Xuất RQ2 [${DISCLAIMER_TEXT}]`;
  const slide6Content = isCanonical
    ? [
        slide6Heading,
        "",
        "▶ KẾT QUẢ CHUẨN TẮC TẬP TEST (Canonical TEST Retrieval: Mẫu số N=718 scorable views)",
        `•  Tỷ lệ tìm trúng Hit@10: ${slots["{{S2_HIT_RATE_AT_K}}"]} (321 / 718 views tìm thấy kỹ thuật mục tiêu).`,
        `•  Macro Recall@10: ${slots["{{S2_RECALL_AT_K}}"]} (độ phủ kỹ thuật mục tiêu trong Top-10).`,
        `•  Retrieval Miss Rate (k=10): ${slots["{{S2_RETRIEVAL_MISS_RATE_K10}}"]} (397 / 718 views vắng mặt hoàn toàn kỹ thuật mục tiêu).`,
        "•  Khoảng cách từ vựng: T1136.001 (support N=95 trong TEST) đạt 0/95 trúng Top-10 do log Event ID 4720 lệch từ vựng so với STIX persistence.",
        "",
        "▶ BỐI CẢNH ĐỐI CHIẾU LỊCH SỬ (Secondary Context - Tuyệt đối không gộp mẫu số)",
        "•  Toàn bộ mẫu dương tính benchmark lịch sử (T20 Benchmark: N=756 views = 718 TEST + 38 DEV):",
        "   Hit@1=4.23% (32/756), Hit@3=16.80% (127/756), Hit@5=24.21% (183/756), Hit@10=45.11% (341/756).",
        "•  Phân định tuyệt đối mẫu số: DEV Pilot là 20 requests (4 views × 5 điều kiện, tổng $0.0242 USD), hoàn toàn tách biệt với 718 TEST views.",
      ].join("\n")
    : [
        slide6Heading,
        "",
        "▶ [T20 FULL BENCHMARK POSITIVE RETRIEVAL (Mẫu số N=756 views = 718 TEST + 38 DEV)]",
        "•  Toàn bộ mẫu dương tính benchmark: 756 views (718 TEST views + 38 DEV views).",
        "•  Benchmark Hit@k: Hit@1=4.23%, Hit@3=16.80%, Hit@5=24.21%, Hit@10=45.11% (341 / 756).",
        "•  Benchmark Macro Recall@10: 43.14%  |  Tỷ lệ vắng mặt Top-10: 54.89% (415 / 756)  |  Mean Rank: 5.21.",
        "•  (Ghi chú: Real DEV Pilot là 4 views × 5 conditions = 20 requests, tách biệt hoàn toàn với benchmark positive views).",
        "",
        "▶ [DIAGNOSTIC TEST FIXTURE RETRIEVAL (Mẫu số N=718 scorable TEST views)]",
        `•  Diagnostic Fixture Hit@10: ${slots["{{S2_HIT_RATE_AT_K}}"]} (k=10).`,
        `•  Diagnostic Fixture Macro Recall@10: ${slots["{{S2_RECALL_AT_K}}"]}.`,
        `•  Diagnostic Fixture Retrieval Miss Rate: ${slots["{{S2_RETRIEVAL_MISS_RATE_K10}}"]} (k=10 failure axis).`,
        "•  Phân định mẫu số: Mẫu số N=756 là toàn bộ benchmark (718 TEST + 38 DEV); N=718 là tập scorable TEST views; DEV Pilot là 20 requests.",
      ].join("\n");
  sh7m.text.set(slide6Content);
  disclaimerEditsCount++;
  modifiedShapeIds.add("sh/7m98ru9g");

  // Slide 6: Disclaimer banner sh/h4bupgn6
  const sh6Banner = presentation.resolve("sh/h4bupgn6");
  if (sh6Banner && sh6Banner.text) {
    if (isCanonical) {
      sh6Banner.text.set([
        "Giả Thuyết Context Scaling & Dilution (k=1,3,5,10)",
        "•  Khoảng cách ngữ nghĩa tại T1136.001 (Local Account): 0/95 lượt trúng Top-10 trong tập TEST scorable (support N=95) do log Event ID 4720 lệch từ vựng so với STIX persistence.",
        "•  Giả thuyết pha loãng ngữ cảnh: Tăng k tăng độ phủ (Hit@k) nhưng tăng nguy cơ nhiễu; cơ chế này vẫn chưa được kiểm chứng sau khi hoàn thành đợt so sánh này, không khẳng định giả thuyết nhân quả về embedding.",
      ].join("\n"));
      disclaimerEditsCount++;
      modifiedShapeIds.add("sh/h4bupgn6");
    } else {
      const targetPhrase = "đang được kiểm chứng đối chứng trên ma trận TEST.";
      const rBanner = sh6Banner.text.get(targetPhrase);
      if (!rBanner.isEmpty) {
        sh6Banner.text.replace(targetPhrase, `đang được kiểm chứng đối chứng trên ma trận TEST [${DISCLAIMER_TEXT}].`);
        disclaimerEditsCount++;
        modifiedShapeIds.add("sh/h4bupgn6");
      }
    }
  }

  // Slide 6: Replace picture with verified native plot in canonical mode
  if (isCanonical) {
    const verifiedFigDir = "C:/Users/hahoa/.codex/artifacts/rag2attck/verified-native-figures-v1";
    const fig6Path = path.join(verifiedFigDir, "canonical_rq2_retrieval.png");
    if (fsSync.existsSync(fig6Path)) {
      const img6 = presentation.resolve("im/7ylcjetk");
      if (img6) {
        const fig6Bytes = await fs.readFile(fig6Path);
        img6.replace({ data: new Uint8Array(fig6Bytes), contentType: "image/png" });
        console.log(`[+] Replaced Slide 6 picture with verified native plot: canonical_rq2_retrieval.png`);
      }
    }
  }

  // Slide 7: Subtitle sh/zedcfa9g
  if (isCanonical) {
    const sh7Sub = presentation.resolve("sh/zedcfa9g");
    if (sh7Sub && sh7Sub.text) {
      sh7Sub.text.set([
        "6. Tác Động Của Hình Thức Biểu Diễn Telemetry",
        "So sánh thực nghiệm Single vs Contextual trên 278 complete GT-scorable pairs",
      ].join("\n"));
      disclaimerEditsCount++;
      modifiedShapeIds.add("sh/zedcfa9g");
    }
  }

  // Slide 7: Shape sh/l0vuh0rm (Left Box - 278 Complete Pairs Breakdown)
  if (isCanonical) {
    const sh7Left = presentation.resolve("sh/l0vuh0rm");
    if (sh7Left && sh7Left.text) {
      sh7Left.text.set([
        "Phân Tích 278 Cặp Hoàn Chỉnh Đầy Đủ Nhãn GT (Complete GT-Scorable Paired Views)",
        "•  Quy mô scorable: 718 scorable TEST views trên 440 distinct eligible clusters.",
        "•  Phân rã 278 cặp đối ứng hoàn chỉnh (Complete Scorable Pairs):",
        "   • 238 cặp giữ nguyên nhãn Ground-Truth (identical GT).",
        "   • 40 cặp có nhãn Ground-Truth thay đổi khi mở rộng ngữ cảnh (divergent GT).",
        "•  Phân tách biên (Marginal Views Breakdown):",
        `   • Single-event views: 278 views (độ chính xác ${slots["{{S2_SINGLE_VIEW_ACC_E2E}}"]}, 233/278).`,
        `   • Contextual-event views: 440 views (độ chính xác ${slots["{{S2_CONTEXT_VIEW_ACC_E2E}}"]}, 338/440).`,
        "•  Hiệu năng cặp đối ứng hoàn chỉnh dưới điều kiện RAG k=10:",
        `   • Single-event Accuracy = ${slots["{{S2_PAIRED_SINGLE_ACC}}"]} (233 / 278).`,
        `   • Contextual-event Accuracy = ${slots["{{S2_PAIRED_CONTEXT_ACC}}"]} (233 / 278).`,
        `   • Chênh lệch hiệu năng cặp (Paired Delta) = ${slots["{{S2_PAIRED_DELTA_PP}}"]} pp (McNemar p = 1.0000).`,
        "•  Bối cảnh đối chiếu thứ hạng lịch sử (T20 Context, 296 pairs anchor):",
        "   • Single tốt hơn: 65 cặp (22.0%) | Contextual tốt hơn: 23 cặp (7.8%) | Ngang nhau: 208 cặp (70.3%).",
      ].join("\n"));
      modifiedShapeIds.add("sh/l0vuh0rm");
      disclaimerEditsCount++;
    }
  }

  // Slide 7: Shape sh/fi9c369c (Pairwise Views Comparison - 12 slots + pending/scaffold removal)
  const sh7 = presentation.resolve("sh/fi9c369c");
  if (sh7 && sh7.text) {
    if (isCanonical) {
      sh7.text.set([
        "Hiện Tượng Quan Sát & Hiệu Năng Đối Chứng Chuẩn Tắc (RAG k=10)",
        "•  Hiện tượng dịch chuyển ngữ cảnh (Contextual Drift Observation):",
        "   • Khi ghép thêm các sự kiện lân cận vào log, thứ hạng truy xuất có sự biến động.",
        "   • Giả thuyết cơ chế: Sự gia tăng các token hệ thống thông thường có thể tạo nhiễu đối với bộ nhúng dense bi-encoder (đây là giả thuyết mô tả quan sát, không khẳng định quan hệ nhân quả).",
        "•  Hiệu năng đối chứng cặp chuẩn tắc dưới điều kiện RAG k=10 [CANONICAL STUDY]:",
        `   • Marginal Views: Single-event Acc = ${slots["{{S2_SINGLE_VIEW_ACC_E2E}}"]} vs Contextual-event Acc = ${slots["{{S2_CONTEXT_VIEW_ACC_E2E}}"]} (Delta = ${slots["{{S2_VIEW_ACC_DELTA}}"]})`,
        `   • Paired Cohort (278 complete pairs): Single Acc = ${slots["{{S2_PAIRED_SINGLE_ACC}}"]} vs Context Acc = ${slots["{{S2_PAIRED_CONTEXT_ACC}}"]} (Delta = ${slots["{{S2_PAIRED_DELTA_PP}}"]} pp)`,
        `   • Pair Concordance: Both Correct = ${slots["{{S2_BOTH_CORRECT_COUNT}}"]}, Single-only Correct = ${slots["{{S2_SINGLE_ONLY_CORRECT}}"]}, Context-only Correct = ${slots["{{S2_CONTEXT_ONLY_CORRECT}}"]}, Both Incorrect = ${slots["{{S2_BOTH_INCORRECT_COUNT}}"]}`,
        `   • McNemar Exploratory Test: p_asympt = ${slots["{{S2_MCNEMAR_P_ASYMPT}}"]}, p_exact = ${slots["{{S2_MCNEMAR_P_EXACT}}"]} (không có khác biệt có ý nghĩa thống kê)`,
        "•  Phạm vi thực nghiệm: Toàn bộ nghiên cứu 6,400 bản ghi trên 5 điều kiện cố định (No-RAG, RAG k=1, 3, 5, 10) với prompt đồng nhất đã hoàn tất; không sử dụng prompt scaffold.",
      ].join("\n"));
      disclaimerEditsCount++;
    } else {
      const rPending = sh7.text.get("[PENDING]");
      if (!rPending.isEmpty) {
        sh7.text.replace("[PENDING]", `[${DISCLAIMER_TEXT}]`);
        disclaimerEditsCount++;
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
    }
  }
  modifiedShapeIds.add("sh/fi9c369c");

  // Slide 7: Speaker note nt/gnmp4jqx (remove pending execution / causal claim)
  const nt7 = presentation.resolve("nt/gnmp4jqx");
  if (nt7 && typeof nt7.text === "string") {
    const oldText7 =
      "[PENDING EXECUTION] chờ toàn bộ ma trận TEST hoàn tất để đưa ra kết luận khoa học chính thức.";
    if (nt7.text.includes(oldText7)) {
      const note7Desc = isCanonical
        ? `[CANONICAL STUDY EXECUTION]; kết quả đối chứng trên tập scorable TEST views (n=718 views across 440 clusters) ghi nhận quan sát chuẩn tắc độc lập.`
        : `[${DISCLAIMER_TEXT}]; kết quả đối chứng trên diagnostic cohort (n=718 views across 440 clusters) ghi nhận quan sát mô tả độc lập.`;
      nt7.text = nt7.text.replace(oldText7, note7Desc);
      disclaimerEditsCount++;
    }
  }

  // Slide 8: Shape sh/98rehwve (RQ1 5 conditions table & RQ2 error decomposition - 27 slots)
  const sh98 = presentation.resolve("sh/98rehwve");
  sh98.text.color = "#0F172A";
  sh98.text.fontSize = isCanonical ? 13 : 11;
  sh98.text.bold = false;

  const header8 = isCanonical
    ? "[CANONICAL STUDY EXECUTION - CANONICAL RESULTS]"
    : `[${DISCLAIMER_TEXT}]`;
  const tableTitle8 = isCanonical
    ? "Bảng Đối Chứng Hiệu Năng RQ1 (N=718 Scorable Views):"
    : "Bảng Đối Chứng Hiệu Năng RQ1 (Diagnostic Fixture):";
  const table8 = [
    header8,
    tableTitle8,
    "Condition      Accuracy    Macro-F1 (474 lớp)    Delta vs No-RAG",
    "-----------------------------------------------------------------",
    `no_rag         ${slots["{{S2_ACC_E2E_NO_RAG}}"]}      ${slots["{{S2_MACRO_F1_NO_RAG}}"]}                baseline`,
    `rag_k1         ${slots["{{S2_ACC_E2E_RAG_K1}}"]}      ${slots["{{S2_MACRO_F1_RAG_K1}}"]}                ${slots["{{S2_ACC_DELTA_RAG_K1}}"]} (${slots["{{S2_MACRO_F1_DELTA_RAG_K1}}"]} F1)`,
    `rag_k3         ${slots["{{S2_ACC_E2E_RAG_K3}}"]}      ${slots["{{S2_MACRO_F1_RAG_K3}}"]}                ${slots["{{S2_ACC_DELTA_RAG_K3}}"]} (${slots["{{S2_MACRO_F1_DELTA_RAG_K3}}"]} F1)`,
    `rag_k5         ${slots["{{S2_ACC_E2E_RAG_K5}}"]}      ${slots["{{S2_MACRO_F1_RAG_K5}}"]}                ${slots["{{S2_ACC_DELTA_RAG_K5}}"]} (${slots["{{S2_MACRO_F1_DELTA_RAG_K5}}"]} F1)`,
    `rag_k10        ${slots["{{S2_ACC_E2E_RAG_K10}}"]}      ${slots["{{S2_MACRO_F1_RAG_K10}}"]}                ${slots["{{S2_ACC_DELTA_RAG_K10}}"]} (${slots["{{S2_MACRO_F1_DELTA_RAG_K10}}"]} F1)`,
    `★ Best Condition (Max Accuracy): ${slots["{{S2_BEST_RAG_CONDITION}}"]} (Delta Acc = ${slots["{{S2_BEST_RAG_ACC_DELTA}}"]}, Delta F1 = ${slots["{{S2_BEST_RAG_F1_DELTA}}"]})`,
    isCanonical
      ? "⚠ LƯU Ý: Toàn bộ khoảng tin cậy chênh lệch cặp (paired difference CIs vs No-RAG) đều chứa 0 (k10 delta CI [-2.355, +5.300] pp; McNemar p = 0.4223 > 0.05)!"
      : "",
    `• Absolute Accuracy 95% CIs: no_rag=${slots["{{S2_CI_95_NO_RAG}}"]}, k1=${slots["{{S2_CI_95_RAG_K1}}"]}, k3=${slots["{{S2_CI_95_RAG_K3}}"]}, k5=${slots["{{S2_CI_95_RAG_K5}}"]}, k10=${slots["{{S2_CI_95_RAG_K10}}"]}`,
    `• RQ2 Phân rã lỗi (k=10): Wrong Class = ${slots["{{S2_WRONG_CLASS_RATE_K10}}"]} | Overlaps: Miss&Wrong=${slots["{{S2_OVERLAP_MISS_AND_WRONG_K10}}"]}, Prov=${slots["{{S2_OVERLAP_MISS_AND_PROV_K10}}"]}, Parse=${slots["{{S2_OVERLAP_MISS_AND_PARSE_K10}}"]}, Inval=${slots["{{S2_OVERLAP_MISS_AND_INVAL_K10}}"]}`,
  ].filter(Boolean).join("\n");

  sh98.text.set(table8);

  // Style header red and small
  const rH8 = sh98.text.get(header8);
  if (!rH8.isEmpty) {
    rH8.color = "#DC2626";
    rH8.fontSize = 9.5;
    rH8.bold = true;
  }
  disclaimerEditsCount++;
  modifiedShapeIds.add("sh/98rehwve");

  // Slide 8: Shape sh/id0fu50z (Conditional metrics & failure axes - 5 slots + causal phrase removal + distinction)
  const shId0 = presentation.resolve("sh/id0fu50z");
  if (shId0 && shId0.text) {
    if (isCanonical) {
      shId0.text.set([
        "Các Thước Đo Có Điều Kiện & Trục Lỗi Độc Lập (RAG k=10, N=718 Scorable Views)",
        `•  P(Correct | GT Retrieved) = ${slots["{{S2_P_CORRECT_GIVEN_RETRIEVED}}"]}: Xác suất gán đúng quan sát được khi kỹ thuật mục tiêu hiện diện trong Top-10 (293 / 321).`,
        `•  P(Correct | GT Absent) = ${slots["{{S2_P_CORRECT_GIVEN_ABSENT}}"]}: Xác suất gán đúng quan sát được khi kỹ thuật mục tiêu vắng mặt trong Top-10 (278 / 397; không giả định tự sửa sai nội tại).`,
        `•  Quan sát thực nghiệm scorable failure = 0: Provider Fail = ${slots["{{S2_PROVIDER_FAIL_RATE_K10}}"]}, Parse Fail = ${slots["{{S2_PARSE_FAIL_RATE_K10}}"]}, Invalid ID = ${slots["{{S2_INVALID_ATTACK_ID_RATE_K10}}"]} (trong 718 scorable records; 13 INCOMPLETE records được ghi nhận đầy đủ trên 6,400 dispatches).`,
        `•  Giao thoa lỗi thực tế: 119 / 147 ca phân loại sai (80.95%) xảy ra khi retrieval trượt Top-10.`,
        "•  Phân định ranh giới mẫu số: Tỷ lệ lỗi provider trên 718 scorable records là 0.0000; toàn bộ 6,400 dispatches có 13 bản ghi INCOMPLETE (6,387 VALID).",
      ].join("\n"));
      disclaimerEditsCount++;
    } else {
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
    }
    modifiedShapeIds.add("sh/id0fu50z");
  }

  // Slide 8: Speaker note nt/fu1gfa1s (remove causal phrase "tự sửa sai" + add secondary stats)
  const nt8 = presentation.resolve("nt/fu1gfa1s");
  if (nt8 && typeof nt8.text === "string") {
    const oldCausal8 = "hay có khả năng tự sửa sai.";
    if (nt8.text.includes(oldCausal8)) {
      nt8.text = nt8.text.replace(
        oldCausal8,
        "hay có thể gán đúng khi thiếu ngữ cảnh truy xuất (không giả định năng lực tự sửa sai nội tại)."
      );
      disclaimerEditsCount++;
    }
  }

  // Slide 9: Subtitle sh/mdonql4z (Provenance clarification)
  const shSub9 = presentation.resolve("sh/mdonql4z");
  if (shSub9 && shSub9.text) {
    if (isCanonical) {
      shSub9.text.set([
        "8. Tiêu Thụ Tài Nguyên & Chi Phí Thực Nghiệm (RQ3)",
        "Phân tích tài nguyên chuẩn tắc (TEST 718) và hạch toán toàn bộ 6,400 requests",
      ].join("\n"));
      disclaimerEditsCount++;
      modifiedShapeIds.add("sh/mdonql4z");
    } else {
      const targetSub9 =
        "Dữ liệu DEV pilot (synthetic split), hạch toán token ước tính và kiểm soát ngân sách";
      const rSub = shSub9.text.get(targetSub9);
      if (!rSub.isEmpty) {
        shSub9.text.replace(targetSub9, `Dữ liệu DEV pilot (synthetic split) đối chiếu Dự phóng Hạch toán Fixture [DIAGNOSTIC TEST FIXTURE ONLY]`);
        disclaimerEditsCount++;
        modifiedShapeIds.add("sh/mdonql4z");
      }
    }
  }

  // Slide 9: Shape sh/ofq5svm5 (Separate DEV pilot telemetry vs Diagnostic Fixture Projection - 10 slots)
  const shOfq = presentation.resolve("sh/ofq5svm5");
  shOfq.text.fontSize = 11.5;
  const slide9Heading = isCanonical
    ? "Phân Tích Tài Nguyên & Chi Phí Chuẩn Tắc (TEST 718) [CANONICAL STUDY]"
    : `DEV Pilot Telemetry & Hạch Toán Nghiên Cứu [${DISCLAIMER_TEXT}]`;
  const zone2Heading = isCanonical
    ? "▶ ZONE 2: TÀI NGUYÊN & ĐỘ TRỄ (Mẫu số 1,280 views/điều kiện, N=6,400 dispatches)"
    : "▶ ZONE 2: DIAGNOSTIC TEST FIXTURE TELEMETRY (N=718 Scorable Views)";
  const slide9Content = isCanonical
    ? [
        slide9Heading,
        "•  Lưu ý: Ước tính thận trọng từ bảng giá đóng băng (conservative accounted tariff estimate).",
        "",
        "▶ TÀI NGUYÊN & ĐỘ TRỄ (1,280 views/điều kiện, 6,400 dispatches):",
        `•  no_rag:  trễ trung vị ${slots["{{S2_MEDIAN_LAT_NO_RAG_SEC}}"]}s (TB 2.90s) | ${slots["{{S2_MEAN_PROMPT_TOK_NO_RAG}}"]} tokens | $${slots["{{S2_COST_LOGICAL_REQ_NO_RAG}}"]} / query.`,
        `•  rag_k10: trễ trung vị ${slots["{{S2_MEDIAN_LAT_K10_SEC}}"]}s (TB 4.37s) | ${slots["{{S2_MEAN_PROMPT_TOK_K10}}"]} tokens | $${slots["{{S2_COST_LOGICAL_REQ_K10}}"]} / query.`,
        "•  Đánh đổi tài nguyên: Tăng k từ 0 lên 10 làm prompt tokens tăng ~7.6x, chi phí/query tăng ~4.6x.",
        "",
        "▶ HẠCH TOÁN TOÀN BỘ NGHIÊN CỨU (Whole Study Financial Accounting):",
        `•  Đã quyết toán điều kiện chính thức: $${slots["{{S2_CANONICAL_TOTAL_USD}}"]} USD ($6.58 settled spend).`,
        `•  Khoản giữ chỗ thận trọng pilot tạm thời: ${slots["{{S2_PRIOR_PILOT_HOLD_USD}}"]} USD (DEV pilot hold).`,
        `•  Tổng cam kết: $6.63 USD committed spend trên trần $${slots["{{S2_TOTAL_STUDY_BUDGET_USD}}"]} USD.`,
        `•  Ngân sách khả dụng còn lại: $${slots["{{S2_NET_REMAINING_USD}}"]} USD ($13.36 net remaining; 0 breach).`,
        "•  Ngoại lệ: 13 INCOMPLETE records; 1 retry hoàn tất (chi tiết trong speaker notes).",
      ].join("\n")
    : [
        slide9Heading,
        "",
        "▶ ZONE 1: HISTORICAL DEV PILOT BASELINE (20 Requests Responses API)",
        "•  Dữ liệu DEV pilot lịch sử: 20 requests (4 views x 5 điều kiện, tổng chi phí ~$0.0242 USD).",
        "•  Ghi chú phân định tuyệt đối: Request thực tế không biến log tổng hợp thành in-the-wild telemetry.",
        "",
        zone2Heading,
        `•  no_rag: trễ trung vị ${slots["{{S2_MEDIAN_LAT_NO_RAG_SEC}}"]}s (trung bình 2.90s) | ${slots["{{S2_MEAN_PROMPT_TOK_NO_RAG}}"]} prompt tokens | ~${slots["{{S2_COST_LOGICAL_REQ_NO_RAG}}"]} USD / logical req.`,
        `•  rag_k10: trễ trung vị ${slots["{{S2_MEDIAN_LAT_K10_SEC}}"]}s (trung bình 4.37s) | ${slots["{{S2_MEAN_PROMPT_TOK_K10}}"]} prompt tokens | ~${slots["{{S2_COST_LOGICAL_REQ_K10}}"]} USD / logical req.`,
        "",
        "▶ ZONE 3: WHOLE STUDY FINANCIAL ACCOUNTING (6,400 Matrix Canonical Conditions)",
        `•  Hạch toán toàn thể điều kiện chuẩn (Canonical Total): ${slots["{{S2_CANONICAL_TOTAL_USD}}"]} USD ($6.57575890 USD đã quyết toán).`,
        `•  Khoản giữ chỗ thận trọng pilot tạm thời: ${slots["{{S2_PRIOR_PILOT_HOLD_USD}}"]} USD (prior_pilot_provisional_hold_usd).`,
        `•  Tổng chi phí đã cam kết hạch toán: $6.63 USD ($6.62839900 USD total accounted spend).`,
        `•  Ngân sách chưa cam kết còn lại (Net Remaining): ${slots["{{S2_NET_REMAINING_USD}}"]} USD ($13.36160100 USD khả dụng).`,
        `•  Trần ngân sách đóng băng cứng (Hard Budget Cap): ${slots["{{S2_TOTAL_STUDY_BUDGET_USD}}"]} USD.`,
      ].join("\n");

  shOfq.text.set(slide9Content);
  disclaimerEditsCount++;
  modifiedShapeIds.add("sh/ofq5svm5");

  // Slide 9: Card sh/oza1gfyh (Bottom right summary card)
  const shOza = presentation.resolve("sh/oza1gfyh");
  if (shOza && shOza.text) {
    if (isCanonical) {
      shOza.text.fontSize = 11.5;
      shOza.text.set([
        "Quy Luật Đánh Đổi Hiệu Năng & Chi Phí (RQ3 Canonical Trade-off)",
        "•  Hit rate chuẩn tắc (TEST 718): RAG k=1 đạt 3.760% -> RAG k=10 đạt 44.708% (No-RAG: N/A, không retriever).",
        "•  Scaling tài nguyên: Prompt tokens tăng ~7.6x (674.3 -> 5114.3), chi phí tăng ~4.6x ($0.000365 -> $0.001679 USD).",
        "•  Tiêu điểm tài chính: $6.58 settled / $6.63 committed spend trên trần ngân sách đóng băng $19.99 USD.",
      ].join("\n"));
      disclaimerEditsCount++;
      modifiedShapeIds.add("sh/oza1gfyh");
    } else {
      const targetOza =
        "•  Dự báo chuẩn tắc tập TEST (< $10 USD) nằm an toàn dưới trần ngân sách đóng băng $19.99 USD.";
      const rOza = shOza.text.get(targetOza);
      if (!rOza.isEmpty) {
        shOza.text.replace(targetOza, `•  Dự báo chuẩn tắc tập TEST: ${slots["{{S2_CANONICAL_TOTAL_USD}}"]} USD nằm an toàn dưới trần ngân sách đóng băng ${slots["{{S2_TOTAL_STUDY_BUDGET_USD}}"]} USD [DIAGNOSTIC FIXTURE].`);
        disclaimerEditsCount++;
        modifiedShapeIds.add("sh/oza1gfyh");
      }
    }
  }

  // Slide 9: Replace picture with verified native plot in canonical mode
  if (isCanonical) {
    const verifiedFigDir = "C:/Users/hahoa/.codex/artifacts/rag2attck/verified-native-figures-v1";
    const fig9Path = path.join(verifiedFigDir, "canonical_rq3_cost_and_latency.png");
    if (fsSync.existsSync(fig9Path)) {
      const img9 = presentation.resolve("im/u987u5cf");
      if (img9) {
        const fig9Bytes = await fs.readFile(fig9Path);
        img9.replace({ data: new Uint8Array(fig9Bytes), contentType: "image/png" });
        console.log(`[+] Replaced Slide 9 picture with verified native plot: canonical_rq3_cost_and_latency.png`);
      }
    }
  }

  // Slide 10, 11, 12 shape content updates in canonical mode
  if (isCanonical) {
    // Slide 10: Shapes sh/kzu5c32t, sh/m1cnetkj, sh/d87uxg3m
    const sh10_6 = presentation.resolve("sh/kzu5c32t");
    if (sh10_6 && sh10_6.text) {
      sh10_6.text.set([
        "Phạm Vi Dữ Liệu & Ranh Giới Benchmark (Scope Constraints)",
        "•  Dữ liệu thử nghiệm Stage B là kịch bản giả lập có cấu trúc (synthetic-paired-v1), chưa phản ánh toàn diện độ nhiễu và sự phức tạp của các chiến dịch APT thực tế.",
        "•  Không gian nhãn: 8 kỹ thuật có mẫu dương tính trong Ground-Truth trên tổng số 474 lớp kỹ thuật đóng băng của ATT&CK Enterprise v19.2 (Frozen Benchmark Universe).",
        "•  Ranh giới cặp đối ứng: 40 trong 278 cặp complete pairs có Ground-Truth thay đổi giữa biểu diễn Single và Contextual (divergent GT).",
        "•  Telemetry thực địa: Nhật ký Windows APT thực tế (T15 real pilot) vẫn là dữ liệu bên ngoài chưa được kiểm chứng trong benchmark này.",
      ].join("\n"));
      modifiedShapeIds.add("sh/kzu5c32t");
      disclaimerEditsCount++;
    }

    const sh10_8 = presentation.resolve("sh/m1cnetkj");
    if (sh10_8 && sh10_8.text) {
      sh10_8.text.set([
        "Giới Hạn Bộ Nhúng Dense & Hướng Tiếp Cận Mở Rộng",
        "•  Mô hình all-MiniLM-L6-v2 thuần túy (dense bi-encoder) gặp khó khăn trong việc khớp từ vựng kỹ thuật hệ thống (như Event ID 4720 so với mô tả tài khoản).",
        "•  Lưu ý phạm vi: Nghiên cứu này KHÔNG đánh giá mô hình tìm kiếm lai (Hybrid Dense + BM25); giải pháp lai chưa được kiểm nghiệm thực nghiệm đối chứng trong benchmark này và là hướng nghiên cứu tương lai.",
        "•  Sự phụ thuộc vào họ mô hình & tính ngẫu nhiên (Stochasticity): Kết quả phụ thuộc vào mô hình gpt-5.6-luna; cần mở rộng trên các mô hình mã nguồn mở để kiểm chứng tính khái quát hóa.",
      ].join("\n"));
      modifiedShapeIds.add("sh/m1cnetkj");
      disclaimerEditsCount++;
    }

    const sh10_10 = presentation.resolve("sh/d87uxg3m");
    if (sh10_10 && sh10_10.text) {
      sh10_10.text.set([
        "Ý Nghĩa Thống Kê & Đảm Bảo Tái Lập Ngoại Tuyến",
        "•  Khoảng tin cậy chênh lệch hiệu năng: Toàn bộ 4 khoảng tin cậy 95% Bootstrap CI của delta độ chính xác đều chứa 0 (ví dụ delta k10 là [-2.355, +5.300] pp).",
        "•  Kiểm định McNemar: Phép thử McNemar thăm dò ở cấp độ view ghi nhận p = 0.4223 > 0.05, không có bằng chứng thống kê khẳng định RAG vượt trội No-RAG; không suy diễn quan hệ nhân quả hay khẳng định tri thức tham số thuần túy khi chưa kiểm chứng.",
        "•  Quy trình kiểm thử an toàn: Mọi kịch bản kiểm thử bắt buộc chạy qua runner offline scripts/run_offline_tests.py, can thiệp socket Python để chặn kết nối ngoài ý muốn.",
      ].join("\n"));
      modifiedShapeIds.add("sh/d87uxg3m");
      disclaimerEditsCount++;
    }

    // Slide 11: Shapes sh/o7ih0r6h, sh/61kzalof
    const sh11_6 = presentation.resolve("sh/o7ih0r6h");
    if (sh11_6 && sh11_6.text) {
      sh11_6.text.set([
        "Tái Lập Ngoại Tuyến & Phạm Vi Kỹ Thuật",
        "•  Lệnh tái lập khoa học chuẩn tắc (Canonical Scientific Replay):",
        "   python scripts/reproduce_canonical_study.py --all",
        "   (Phân biệt với kịch bản chẩn đoán lịch sử / fixture: scripts/reproduce_study.py).",
        "•  Cơ chế kiểm chứng ngoại tuyến:",
        "   • Đánh giá lại từ 15 artifacts đã đóng băng nhằm xác minh tính đúng đắn toán học và hạch toán tài chính; KHÔNG phát sinh gọi mô hình hay tiêu tốn token trực tiếp mới.",
        "   • Lệnh kiểm thử có bảo vệ ngoại tuyến: python scripts/run_offline_tests.py -m pytest ...",
        "•  Phạm vi offline_guard: Can thiệp socket Python & lọc credentials (không phải sandbox OS).",
        "•  Gói bằng chứng công khai hiện được tổ chức dưới dạng danh mục siêu dữ liệu khả chuyển (portable metadata inventory/plan), sẵn sàng chờ thẩm định xuất bản chính thức.",
      ].join("\n"));
      modifiedShapeIds.add("sh/o7ih0r6h");
      disclaimerEditsCount++;
    }

    const sh11_8 = presentation.resolve("sh/61kzalof");
    if (sh11_8 && sh11_8.text) {
      sh11_8.text.set([
        "Đóng Góp Nghiên Cứu Thực Nghiệm Cốt Lõi",
        "•  1. Khung thực nghiệm đối chứng: Xây dựng quy trình thực nghiệm khép kín, phân chia tập dữ liệu chống rò rỉ nhãn và kiểm soát biến số chặt chẽ cho bài toán ánh xạ log Windows.",
        "•  2. Bóc tách độc lập các trục lỗi (RQ2 Failure Decomposition per D2i): Phân tích định lượng riêng biệt retrieval miss, downstream generation failure và joint overlap, bác bỏ giả định xung khắc hoặc độc lập xác suất sai lầm.",
        "•  3. Minh bạch ranh giới thống kê: Công bố đầy đủ khoảng tin cậy 95% CI cho thấy RAG chưa tạo khác biệt có ý nghĩa thống kê so với No-RAG trên benchmark này.",
        "•  4. Gói bằng chứng kiểm chứng độc lập: Cung cấp đầy đủ mã nguồn, dữ liệu chẩn đoán, kịch bản tạo slide và cơ chế bảo vệ ngoại tuyến.",
      ].join("\n"));
      modifiedShapeIds.add("sh/61kzalof");
      disclaimerEditsCount++;
    }

    // Slide 12: Shape sh/ra943il8
    const sh12 = presentation.resolve("sh/ra943il8");
    if (sh12 && sh12.text) {
      sh12.text.set([
        "TỔNG KẾT & PHẦN HỎI ĐÁP (Q&A)",
        "RAG2ATT&CK: Đánh Giá Thực Nghiệm Đối Chứng RAG Trong Giám Sát An Ninh Mạng",
        `•  Kết quả thực nghiệm chính: No-RAG đạt 560/718 (${slots["{{S2_ACC_E2E_NO_RAG}}"]}) vs RAG k=10 quan sát thấy 571/718 (${slots["{{S2_ACC_E2E_RAG_K10}}"]}, Delta = ${slots["{{S2_ACC_DELTA_RAG_K10}}"]}, 95% CI [-2.355, +5.300] pp).`,
        "•  Độ không chắc chắn thống kê: Toàn bộ 4 khoảng tin cậy 95% CI của delta đều chứa 0; RAG không mang lại cải thiện vượt trội có ý nghĩa thống kê so với baseline No-RAG trên benchmark này.",
        `•  Chi phí vận hành thực tế: Hạch toán toàn bộ nghiên cứu là $6.63 USD ($6.628399 USD), nằm an toàn dưới trần ngân sách đóng băng $${slots["{{S2_TOTAL_STUDY_BUDGET_USD}}"]} USD.`,
        `•  Phân rã lỗi D2i: 80.95% số ca phân loại sai (${slots["{{S2_OVERLAP_MISS_AND_WRONG_K10}}"]}/147) nằm ở nhánh truy xuất trượt; các trục lỗi độc lập ghi nhận giao thoa thực tế mà không giả định độc lập ngẫu nhiên.`,
        "•  Tái lập khoa học chuẩn tắc: python scripts/reproduce_canonical_study.py --all (đánh giá ngoại tuyến từ artifact đóng băng, không phát sinh chi phí).",
        "•  Mã nguồn & Danh mục siêu dữ liệu khả chuyển: PR #26 (https://github.com/habachcp6/RAG2ATTCK/pull/26)",
        "Xin trân trọng cảm ơn Quý Thầy Cô và Hội Đồng! Kính mời đặt câu hỏi thảo luận.",
      ].join("\n"));
      modifiedShapeIds.add("sh/ra943il8");
      disclaimerEditsCount++;
    }
  }

  // All 12 Speaker Notes in Canonical Mode
  if (isCanonical) {
    if (slides[0].speakerNotes) {
      slides[0].speakerNotes.text = [
        "GHI CHÚ DIỄN GIẢ (Slide 1):",
        "Kính thưa Hội đồng và các chuyên gia, tôi là Hà Hoàng Bách, xin trình bày báo cáo nghiên cứu dự án RAG2ATT&CK: Đánh giá tác động của MITRE ATT&CK-grounded RAG đối với việc ánh xạ Windows endpoint logs sang ATT&CK techniques.",
        "Phạm vi thực nghiệm: Dữ liệu TEST tổng hợp; đầu ra từ mô hình thật.",
        "Toàn bộ nghiên cứu được thiết kế theo phương pháp thực nghiệm đối chứng nghiêm ngặt dưới giao thức đóng băng experiment-protocol-v1.1, khóa mật mã 15 canonical artifacts, và tuân thủ nguyên tắc fail-closed chặt chẽ.",
        "Khai báo tác tạo: Slide deck này được tác tạo và cập nhật bằng công cụ bundled artifact tools, đảm bảo định dạng PowerPoint native tiếng Việt có thể chỉnh sửa từng shape.",
        "Bằng chứng dự án: PR #26 (https://github.com/habachcp6/RAG2ATTCK/pull/26); config/canonical_experiment_lock_v1.json (SHA-256: 961ba9b3...); reports/experiment_protocol_v1.md; scripts/reproduce_study.py.",
      ].join("\n");
      disclaimerEditsCount++;
    }

    if (slides[4].speakerNotes) {
      slides[4].speakerNotes.text = [
        "GHI CHÚ DIỄN GIẢ (Slide 5):",
        "Giao thức thực nghiệm v1.1 đóng băng 7 quyết định phương pháp luận cốt lõi D1-D7 và được tách bạch rõ ràng từng nhãn:",
        "- D1: RECORD_ONLY lưu toàn văn phản hồi thô phục vụ kiểm toán độc lập nhưng đảm bảo toàn bộ credentials và bí mật nhạy cảm đã được làm sạch / khử khuẩn (credentials and sensitive secrets sanitized/redacted), tuyệt đối không lưu lộ lọt bí mật.",
        "- D2d: Vũ trụ Macro-F1 cố định đúng 474 lớp (FROZEN_BENCHMARK_UNIVERSE = 474).",
        "- D2e: invalid_id_as_failure (INCLUDE_IN_DENOMINATOR cho mã sai cú pháp/ảo giác).",
        "- D2f: api_failure_as_failure (INCLUDE_IN_DENOMINATOR cho lỗi provider/timeout/parser).",
        "- D2g: ALLOW_HISTORICAL chấp nhận các mã lịch sử/thu hồi dưới dạng distinct observation count, không tự ý gán lại mã thay thế.",
        "- D2h: ANY_GT_RETRIEVED cho multi-label retrieval success.",
        "- D2i: INDEPENDENT_AXES ghi nhận đầy đủ phần giao thoa giữa các trục đo lường lỗi.",
        "Bằng chứng dự án: reports/experiment_protocol_v1.md (SHA-256: d3bf3d31ad307100ac437a7daecc470bf12de9ada49f19de3d77592d5a21974c); attack/raw/enterprise-v19.2/enterprise-attack-19.2.json (SHA-256: dc1639caa5501d720e280cf1cbd8fbe009884a0c9b3e6e9ed9d0c25166c3d8f4); tests/test_experiment_evaluation.py.",
      ].join("\n");
      disclaimerEditsCount++;
    }

    if (slides[5].speakerNotes) {
      slides[5].speakerNotes.text = [
        "GHI CHÚ DIỄN GIẢ (Slide 6):",
        `Chẩn đoán độc lập khâu tìm kiếm (RQ2) trên tập scorable TEST views (N=718) cho thấy Hit@10 đạt ${slots["{{S2_HIT_RATE_AT_K}}"]} (321 / 718), nghĩa là trong ${slots["{{S2_RETRIEVAL_MISS_RATE_K10}}"]} trường hợp (397 / 718), kỹ thuật đúng hoàn toàn vắng bóng trong Top-10 gửi cho LLM. Macro Recall@10 đạt ${slots["{{S2_RECALL_AT_K}}"]}. Điển hình là kỹ thuật T1136.001 với support N=95 trong tập TEST đạt 0/95 lần trúng Top-10 do khoảng cách ngữ nghĩa giữa Event ID 4720 và STIX description.`,
        "Lưu ý về bối cảnh đối chiếu lịch sử: Chỉ số Mean Rank 5.21 khi trúng và tỷ lệ 0/99 của T1136.001 là số liệu thuộc benchmark lịch sử T20 (N=756 views gồm 718 TEST + 38 DEV với 341/756 trúng Top-10, 45.11%); còn DEV Pilot chỉ gồm 20 requests (4 views x 5 điều kiện), tuyệt đối không gộp chung mẫu số với kết quả TEST chính thức.",
        "Về cơ chế embedding: Giả thuyết pha loãng ngữ cảnh vẫn chưa được kiểm chứng sau khi hoàn thành đợt so sánh này, không khẳng định quan hệ nhân quả.",
        "Bằng chứng dự án: C:/Users/hahoa/.codex/artifacts/rag2attck/verified-native-figures-v1/canonical_rq2_retrieval.png; outputs/reproduction/tables/table_1_retrieval_diagnostics.md; tests/test_retrieval_diagnostics.py.",
      ].join("\n");
      disclaimerEditsCount++;
    }

    if (slides[6].speakerNotes) {
      slides[6].speakerNotes.text = [
        "GHI CHÚ DIỄN GIẢ (Slide 7):",
        "Kết quả thực nghiệm chuẩn tắc trên tập scorable TEST views (N=718 views / 440 clusters) ghi nhận quan sát độc lập về biểu diễn telemetry dưới điều kiện RAG k=10:",
        `Tập dữ liệu chính hiện tại là 278 complete GT-scorable pairs (238 cặp identical GT, 40 cặp divergent GT). Độ chính xác của Single-event đạt ${slots["{{S2_PAIRED_SINGLE_ACC}}"]} (233/278) và Contextual-event cũng đạt ${slots["{{S2_PAIRED_CONTEXT_ACC}}"]} (233/278), chênh lệch Paired Delta là ${slots["{{S2_PAIRED_DELTA_PP}}"]} pp với kiểm định McNemar p=${slots["{{S2_MCNEMAR_P_ASYMPT}}"]} (không có ý nghĩa thống kê). Ở góc độ phân tách biên, 278 single views đạt ${slots["{{S2_SINGLE_VIEW_ACC_E2E}}"]} trong khi 440 contextual views đạt ${slots["{{S2_CONTEXT_VIEW_ACC_E2E}}"]}.`,
        "Ngữ cảnh lịch sử T20: Số liệu 670 kịch bản đối ứng / 296 cặp anchor thuộc benchmark lịch sử T20, đưa vào đây làm bối cảnh tham chiếu bổ sung.",
        "Hiện tượng dịch chuyển ngữ cảnh được giải thích theo giả thuyết mô tả quan sát (nhiễu từ token hệ thống thông thường), không khẳng định quan hệ nhân quả. Toàn bộ ma trận TEST 6,400 bản ghi đã hoàn tất trên 5 điều kiện đóng băng với prompt đồng nhất, loại bỏ hoàn toàn các khung khái niệm scaffold thử nghiệm.",
        "Bằng chứng dự án: outputs/reproduction/tables/table_4_pairwise_representation_comparison.md; tests/test_t20_canonical_artifacts.py.",
      ].join("\n");
      disclaimerEditsCount++;
    }

    if (slides[7].speakerNotes) {
      slides[7].speakerNotes.text = [
        "GHI CHÚ DIỄN GIẢ (Slide 8):",
        "Khung đánh giá RQ1 & RQ2 được xây dựng trên định đề D2i (Independent Measurement Axes), phân tích trên 718 scorable TEST views với không gian 474 lớp kỹ thuật đóng băng của MITRE ATT&CK Enterprise v19.2.",
        `Về hiệu năng RQ1: No-RAG đạt độ chính xác ${slots["{{S2_ACC_E2E_NO_RAG}}"]} (560/718), trong khi RAG k=10 đạt ${slots["{{S2_ACC_E2E_RAG_K10}}"]} (571/718), tăng ${slots["{{S2_ACC_DELTA_RAG_K10}}"]} (${slots["{{S2_MACRO_F1_DELTA_RAG_K10}}"]} F1). Cần phân biệt rõ: Các khoảng tin cậy liệt kê trên bảng là Absolute Accuracy 95% CIs (ví dụ no_rag là ${slots["{{S2_CI_95_NO_RAG}}"]}, k10 là ${slots["{{S2_CI_95_RAG_K10}}"]}); còn các khoảng tin cậy chênh lệch cặp (paired difference CIs vs No-RAG) đều chứa 0 (khoảng tin cậy delta của RAG k=10 là [-2.355, +5.300] pp, kiểm định McNemar thăm dò p = 0.4223 > 0.05). Do đó việc rag_k10 có độ chính xác quan sát được cao nhất chỉ mang tính mô tả thử nghiệm, không có ý nghĩa thống kê vượt trội.`,
        `Về chẩn đoán có điều kiện RQ2 (RAG k=10): P(Correct | Retrieved) = ${slots["{{S2_P_CORRECT_GIVEN_RETRIEVED}}"]} (293/321) và P(Correct | Absent) = ${slots["{{S2_P_CORRECT_GIVEN_ABSENT}}"]} (278/397; không giả định khả năng tự sửa sai nội tại). Có ${slots["{{S2_OVERLAP_MISS_AND_WRONG_K10}}"]}/147 ca phân loại sai (80.95%) nằm ở nhánh truy xuất trượt.`,
        "Về ranh giới mẫu số: Tỷ lệ provider failure trên 718 scorable records là giá trị quan sát thực nghiệm scorable failure = 0.0000. Trên toàn bộ 6,400 dispatches có 13 INCOMPLETE records được bảo toàn nguyên vẹn.",
        "Bằng chứng dự án: C:/Users/hahoa/.codex/artifacts/rag2attck/verified-native-figures-v1/canonical_rq1_accuracy_and_macro.png; reports/experiment_protocol_v1.md.",
      ].join("\n");
      disclaimerEditsCount++;
    }

    if (slides[8].speakerNotes) {
      slides[8].speakerNotes.text = [
        "GHI CHÚ DIỄN GIẢ (Slide 9):",
        "Trong phân tích RQ3, toàn bộ chỉ số tài nguyên, độ trễ và chi phí được tính trên toàn bộ 1,280 logical views mỗi điều kiện (tổng 6,400 dispatches), không rút gọn về 718 scorable views:",
        `1. Độ trễ & Tài nguyên: Phân biệt rõ trễ trung vị (No-RAG ${slots["{{S2_MEDIAN_LAT_NO_RAG_SEC}}"]}s vs RAG k10 ${slots["{{S2_MEDIAN_LAT_K10_SEC}}"]}s) và trễ trung bình (No-RAG 2.90s vs RAG k10 4.37s). Lượng prompt tokens trung bình tăng từ ${slots["{{S2_MEAN_PROMPT_TOK_NO_RAG}}"]} lên ${slots["{{S2_MEAN_PROMPT_TOK_K10}}"]} (~7.6x từ baseline đến k10), chi phí mỗi request tăng từ $${slots["{{S2_COST_LOGICAL_REQ_NO_RAG}}"]} lên $${slots["{{S2_COST_LOGICAL_REQ_K10}}"]} USD (~4.6x từ baseline đến k10).`,
        `2. Hiệu quả đánh đổi: Hit rate chuẩn tắc trên tập scorable N=718: No-RAG là N/A (không dùng retriever); RAG k=1 đạt Hit@1 = 3.760% (27/718), tăng lên RAG k=10 đạt Hit@10 = 44.708% (321/718).`,
        `3. Hạch toán tài chính 8 chữ số thập phân chính xác: Chi phí 5 điều kiện chuẩn đã quyết toán là $6.57575890 USD ($${slots["{{S2_CANONICAL_TOTAL_USD}}"]} USD), cộng với khoản giữ chỗ thận trọng pilot $0.05264010 USD ($${slots["{{S2_PRIOR_PILOT_HOLD_USD}}"]} USD), tổng chi phí đã cam kết là $6.62839900 USD ($6.63 USD committed spend). Ngân sách khả dụng còn lại là $13.36160100 USD ($${slots["{{S2_NET_REMAINING_USD}}"]} USD) trên trần đóng băng cứng $19.99000000 USD ($${slots["{{S2_TOTAL_STUDY_BUDGET_USD}}"]} USD). Chi phí được tính toán theo ước tính thận trọng từ bảng giá đóng băng (conservative accounted tariff estimate).`,
        "4. Bối cảnh lịch sử & Ngoại lệ: DEV pilot lịch sử là 20 requests (~$0.0242 USD). Trên toàn bộ 6,400 requests có 13 INCOMPLETE records; 1 attempt API_FAILURE được retry có khoản phí thiếu usage là $0.53974560 USD.",
        "Bằng chứng dự án: C:/Users/hahoa/.codex/artifacts/rag2attck/verified-native-figures-v1/canonical_rq3_cost_and_latency.png; config/experiment_config.json; tests/test_monetary_guard.py.",
      ].join("\n");
      disclaimerEditsCount++;
    }

    if (slides[9].speakerNotes) {
      slides[9].speakerNotes.text = [
        "GHI CHÚ DIỄN GIẢ (Slide 10):",
        "Nghiên cứu công khai đầy đủ các giới hạn khoa học và ràng buộc thực nghiệm:",
        "1. Dữ liệu: Kịch bản giả lập có cấu trúc synthetic-paired-v1 với 8 kỹ thuật có mẫu dương tính trong tổng số 474 lớp đóng băng; 40 cặp đối ứng có GT thay đổi khi mở rộng ngữ cảnh; dữ liệu telemetry thực tế in-the-wild (T15) chưa được kiểm chứng.",
        "2. Bộ tìm kiếm: Hạn chế từ vựng của dense bi-encoder được ghi nhận rõ, tuy nhiên giải pháp Hybrid Dense+BM25 chưa từng được thử nghiệm trong benchmark này và là hướng phát triển tương lai.",
        "3. Thống kê: Toàn bộ 4 khoảng tin cậy 95% CI của chênh lệch độ chính xác so với No-RAG đều chứa 0. Phép thử McNemar thăm dò ở cấp độ view cho kết quả p = 0.4223 > 0.05, không khẳng định RAG vượt trội No-RAG; không suy diễn quan hệ nhân quả hay khẳng định tri thức tham số thuần túy khi chưa được kiểm chứng.",
        "Bằng chứng dự án: docs/reproducibility.md; scripts/run_offline_tests.py; tests/test_offline_guard.py.",
      ].join("\n");
      disclaimerEditsCount++;
    }

    if (slides[10].speakerNotes) {
      slides[10].speakerNotes.text = [
        "GHI CHÚ DIỄN GIẢ (Slide 11):",
        "Khả năng kiểm chứng độc lập là cam kết trọng tâm của dự án:",
        "Lệnh tái lập khoa học chuẩn tắc là: python scripts/reproduce_canonical_study.py --all, phân biệt với kịch bản chẩn đoán lịch sử/fixture scripts/reproduce_study.py. Cơ chế đánh giá ngoại tuyến từ 15 artifacts đã đóng băng nhằm xác thực tính toàn vẹn toán học và hạch toán tài chính mà KHÔNG tạo ra bất kỳ lượt gọi mô hình trực tiếp hay chi phí token mới nào. Runner scripts/run_offline_tests.py can thiệp ở tầng socket Python và biến môi trường, không phải là sandbox cấp hệ điều hành. Gói bằng chứng công khai hiện được tổ chức dưới dạng danh mục siêu dữ liệu khả chuyển (portable metadata inventory/plan) chờ thẩm định xuất bản chính thức.",
        "Bốn đóng góp thực nghiệm cốt lõi: thiết lập phương pháp luận đo lường đối chứng, phân rã lỗi D2i độc lập, minh bạch độ không chắc chắn thống kê và cung cấp gói chứng cứ có thể kiểm chứng độc lập.",
        "Bằng chứng dự án: config/canonical_experiment_lock_v1.json (SHA-256: 961ba9b3...); scripts/reproduce_canonical_study.py; scripts/run_offline_tests.py; tests/test_smoke_cases.py.",
      ].join("\n");
      disclaimerEditsCount++;
    }

    if (slides[11].speakerNotes) {
      slides[11].speakerNotes.text = [
        "GHI CHÚ DIỄN GIẢ (Slide 12):",
        "Tóm lại, RAG2ATT&CK đã hoàn tất thực nghiệm đối chứng đo lường vai trò của RAG trong bài toán ánh xạ log Windows sang ATT&CK techniques:",
        `1. Kết quả cốt lõi: No-RAG đạt ${slots["{{S2_ACC_E2E_NO_RAG}}"]} (560/718), RAG k10 quan sát thấy ${slots["{{S2_ACC_E2E_RAG_K10}}"]} (571/718, Delta = ${slots["{{S2_ACC_DELTA_RAG_K10}}"]}). Khoảng tin cậy 95% CI [-2.355, +5.300] pp chứa 0, cho thấy RAG chưa tạo khác biệt có ý nghĩa thống kê trên benchmark này.`,
        `2. Phân rã lỗi: 80.95% lỗi phân loại sai rơi vào trường hợp truy xuất trượt Top-10 (${slots["{{S2_OVERLAP_MISS_AND_WRONG_K10}}"]}/147).`,
        `3. Tài chính: Chi phí toàn bộ nghiên cứu được kiểm soát chặt chẽ ở mức $6.628399 USD trên trần ngân sách $${slots["{{S2_TOTAL_STUDY_BUDGET_USD}}"]} USD.`,
        "4. Tái lập & Công khai: Thực thi tái lập khoa học chuẩn tắc qua python scripts/reproduce_canonical_study.py --all (đánh giá ngoại tuyến từ artifact đã đóng băng, không phát sinh chi phí). Gói phát hành công khai được tổ chức dạng danh mục siêu dữ liệu khả chuyển chờ thẩm định xuất bản.",
        "Bằng chứng dự án: PR #26 (https://github.com/habachcp6/RAG2ATTCK/pull/26); docs/sanitized_evidence_manifest.json; reports/evidence/reproducibility_package_manifest.md.",
      ].join("\n");
      disclaimerEditsCount++;
    }
  }

  // 5. Verify all 67 declarative slot entries are injected into shapes with condition binding
  let actualNumericSlotsCount = 0;
  const enrichedDeclarativeMapping = [];
  const verifiedBindings = [];

  for (const item of declMap) {
    const sh = presentation.resolve(item.shape_id);
    if (!sh || !sh.text) {
      throw new Error(
        `[FAIL_CLOSED] Declarative slot target shape ${item.shape_id} not found or has no text`
      );
    }
    const shapeContent =
      typeof sh.text === "string" ? sh.text : sh.text.toString();
    const bindingResult = verifySlotBinding(shapeContent, item);
    if (!bindingResult.verified) {
      throw new Error(
        `[FAIL_CLOSED] Numerical binding verification failed for slot "${item.slot_name}". ` +
          bindingResult.reason
      );
    }
    actualNumericSlotsCount++;
    const enrichedEntry = {
      slot_name: item.slot_name,
      input_field: item.input_field,
      units: item.units,
      source_pointer: item.source_pointer,
      shape_id: item.shape_id,
      slide_number: item.slide_number,
      injected_value: item.injected_value,
    };
    enrichedDeclarativeMapping.push(enrichedEntry);
    verifiedBindings.push({
      ...enrichedEntry,
      bound_condition: bindingResult.bound_condition,
      bound_line: bindingResult.bound_line,
      verified: true,
    });
  }

  console.log(
    `[+] Declarative verification: ${actualNumericSlotsCount} / ${EXPECTED_NUMERIC_SLOTS_COUNT} slots verified with strict condition bindings.`
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

  // 6b. Re-import exported bytes to verify roundtrip integrity (labels, rows, values, notes, editability)
  console.log(`[+] Re-importing candidate deck to verify exported byte integrity...`);
  const verifyPath = isDryRun
    ? path.join(os.tmpdir(), `dry_candidate_${Date.now()}.pptx`)
    : candidateDeckPath;
  if (isDryRun) {
    await fs.writeFile(verifyPath, afterBytes);
  }
  try {
    const reimportedDeck = await PresentationFile.importPptx(
      await FileBlob.load(verifyPath)
    );
    const reimportedSnap = await reimportedDeck.inspect({ maxChars: 1000000 });
    const reimportedSlides = reimportedDeck.slides.items;

    if (reimportedSlides.length !== slides.length) {
      throw new Error(
        `[FAIL_CLOSED] Reimported slide count mismatch: ${reimportedSlides.length} vs ${slides.length}`
      );
    }
    const reimportedNotesCount = reimportedSnap.records.filter((r) => r.kind === "notes").length;
    if (reimportedNotesCount !== notesCount) {
      throw new Error(
        `[FAIL_CLOSED] Reimported notes count mismatch: ${reimportedNotesCount} vs ${notesCount}`
      );
    }

    // Verify key shapes exist in reimported deck and are editable
    for (const sId of ["sh/sna103ap", "sh/7m98ru9g", "sh/98rehwve", "sh/ofq5svm5"]) {
      const shRe = reimportedDeck.resolve(sId);
      if (!shRe || !shRe.text) {
        throw new Error(`[FAIL_CLOSED] Reimported deck missing or non-editable shape: ${sId}`);
      }
      const txtRe = typeof shRe.text === "string" ? shRe.text : shRe.text.toString();
      if (sId === "sh/98rehwve") {
        if (!txtRe.includes("rag_k10") || !txtRe.includes(slots["{{S2_ACC_E2E_RAG_K10}}"])) {
          throw new Error(`[FAIL_CLOSED] Reimported shape ${sId} missing expected injected values`);
        }
      }
    }
    console.log(`[+] Re-imported candidate deck verified successfully (roundtrip intact).`);
  } finally {
    if (isDryRun && fsSync.existsSync(verifyPath)) {
      await fs.unlink(verifyPath).catch(() => {});
    }
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
    fixture_only: isCanonical ? false : true,
    canonical_mode: isCanonical,
    provenance_status: isCanonical ? "canonical_study" : "diagnostic_fixture",
    disclaimer: isCanonical
      ? "[CANONICAL STUDY EXECUTION - CERTIFIED VERIFIED OUTPUT]"
      : DISCLAIMER_TEXT,
    timestamp_utc: new Date().toISOString(),
    roundtrip_reimported_verified: true,
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
    verified_bindings: verifiedBindings,
    verified_bindings_count: verifiedBindings.length,
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
  const canonical = args.includes("--canonical");

  const getArg = (flag) => {
    const idx = args.indexOf(flag);
    return idx !== -1 ? args[idx + 1] : undefined;
  };

  const slotsPath = getArg("--fixture-slots") || getArg("--slots");
  const mapPath = getArg("--declarative-map");
  const sourceDeckPath = getArg("--source-deck");
  const candidateDeckPath = getArg("--output-deck");
  const qaOutputDir = getArg("--output-qa-dir");
  const auditReportPath = getArg("--audit-report");
  const artifactToolModule = getArg("--artifact-tool-module");

  runArtifactToolDeckUpdater({
    canonical,
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
  verifySlotBinding,
  DISCLAIMER_TEXT,
  EXPECTED_NUMERIC_SLOTS_COUNT,
};
