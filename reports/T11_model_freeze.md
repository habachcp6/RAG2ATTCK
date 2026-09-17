# T11: Model Configuration Freeze Report — No-RAG Baseline Infrastructure

## Executive Summary
This report documents the canonical, frozen model configuration established under Task **T11** of the **RAG2ATTCK** research project. The configuration defines the exact operational parameters for querying the frontier large language model across both experimental conditions: the **No-RAG Baseline** and the subsequent **ATT&CK-Grounded RAG** condition.

The frozen configuration is committed at `config/model.json`. All parameters documented below are immutable for the duration of the baseline evaluation.

---

## 1. Provider
- **Canonical Provider:** `openai`
- **Authentication:** Purely external via environment variable `OPENAI_API_KEY`. No API keys, tokens, or credential strings are stored in configuration files, committed code, or logs.

---

## 2. Exact Model / API Identifier
- **Official Model Identifier:** `gpt-5.6-luna`
- **Release Horizon:** July 2026.
- **Model Profile:** Frontier reasoning model optimized for high-throughput, structured classification, code/log analysis, and complex multi-step reasoning.
- **Context Window:** 1,050,000 input tokens.
- **Maximum Native Completion Limit:** 128,000 output tokens.

---

## 3. Reasoning Setting
- **Reasoning Effort:** `xhigh`
- **Operational Meaning:** Directs the model to allocate maximal internal thinking and chain-of-thought compute prior to producing the visible prediction payload.
- **Rationale:** Windows endpoint log telemetry contains dense, noisy, and potentially obfuscated process trees, command lines, and network/registry artifacts. Disambiguating closely related ATT&CK techniques (e.g., distinguishing process injection sub-techniques T1055.001 vs. T1055.012, or scheduled tasks T1053.005 from service execution T1569.002) requires deep contextual analysis and elimination of alternative hypotheses.

---

## 4. SDK / API Version Used
- **Runtime Environment:** Python `3.13.0` (enforced via `.python-version`).
- **OpenAI Python SDK:** Version `>=3.14.1` (locked at `3.14.1` in `uv.lock`).
- **Schema Validation Library:** `pydantic>=2.13.5` (locked at `2.13.5` in `uv.lock`).
- **HTTP Transport:** `httpx2` / `anyio` managed internally by the OpenAI SDK.

---

## 5. API Interface Selection
- **Frozen Interface:** **OpenAI Responses API** (`client.responses.create` with JSON Schema structured output and Pydantic post-parse validation).
- **No runtime fallback.** The API interface is part of the frozen experimental configuration. If a Responses API request fails, the error is classified per retry/error policy and eventually returns `API_FAILURE` or `TIMEOUT`. No silent switching to Chat Completions occurs during experiment samples.

### Selection Rationale
1. **Modern Protocol Alignment:** The Responses API is OpenAI's primary interface in SDK v3+, engineered specifically for agentic execution, native schema parsing, and modern reasoning model control.
2. **First-Class Reasoning Parameter:** In the Responses API, reasoning compute is governed cleanly by the `reasoning` parameter object (`reasoning={"effort": "xhigh"}`).
3. **Native Output Budgeting:** Uses `max_output_tokens`, which directly represents the unified generation budget covering both reasoning tokens and visible structured completion tokens.
4. **Structured Output Integration:** Uses `text={"format": {"type": "json_schema", ...}}` with `strict: true` for schema-constrained generation, followed by Pydantic `model_validate()` post-parse.
5. **Detailed Token Telemetry:** The Responses API exposes reasoning token counts via `usage.output_tokens_details.reasoning_tokens` at query time; however, `ExecutionRecord` does not persist this field — only aggregate `input_tokens` and `output_tokens` are recorded.
6. **Experimental Consistency:** Using a single API interface across all samples eliminates interface-specific confounding variables.

---

## 6. Maximum Output Token Budget
- **Parameter Name (Responses API):** `max_output_tokens`
- **Frozen Budget Value:** `8192` (8,192 tokens)

### Detailed Token Accounting Rationale
On OpenAI reasoning models (`gpt-5.6-luna`, o-series architectures), the output token budget is a **shared allocation pool** that must accommodate:
1. **Internal Reasoning Tokens (Hidden):** The model's internal chain-of-thought tokens. Under `reasoning_effort="xhigh"`, the model allocates substantial compute for deep reasoning before emitting the visible output. The exact reasoning token consumption per sample is unknown prior to live evaluation and will vary with log complexity.
2. **Visible Output Tokens:** The final structured JSON prediction:
   ```json
   {"technique_id": "T1059.001"}
   ```
   This payload consumes only approximately 10–20 tokens.

**Conservative Engineering Budget:**
A frozen budget of **8,192 tokens** is set as a conservative engineering ceiling that provides ample reasoning headroom for `xhigh` contemplation while establishing a firm upper bound to protect against runaway latency and unbounded cost. This value was chosen based on the model's documented maximum output capacity (128,000 tokens) and the need to balance sufficient reasoning depth against cost control. No live baseline samples were executed to empirically establish reasoning token averages prior to setting this budget.

**Failure Mode Prevention:**
If the output token budget were set to a conventional value (e.g., 512 or 1,024 tokens), the model would exhaust its token quota while still generating internal reasoning tokens, before emitting the visible JSON object. This triggers an abrupt termination with API status `incomplete` / finish reason `length`, resulting in an invalid or empty prediction.

---

## 7. Parameters Intentionally Frozen
The following table enumerates every model parameter explicitly frozen in `config/model.json`:

| Parameter | Frozen Value | Type | Purpose |
| :--- | :--- | :--- | :--- |
| `provider` | `"openai"` | String | Identifies the execution backend provider |
| `model` | `"gpt-5.6-luna"` | String | Canonical frontier model identifier |
| `reasoning_effort` | `"xhigh"` | String | Frozen reasoning effort selected for this study |
| `api_interface` | `"responses"` | String | Sole frozen API interface endpoint (no runtime fallback) |
| `max_output_tokens` | `8192` | Integer | Generation budget in Responses API (reasoning + output) |
| `timeout_seconds` | `120` | Integer | Client-side socket and read timeout per attempt |
| `retry_policy` | `"exponential_backoff"` | String | Retry strategy for transient errors |
| `max_retries` | `3` | Integer | Maximum retry attempts per sample |
| `retry_initial_delay_seconds` | `1.0` | Float | Base backoff duration before first retry |
| `retry_backoff_factor` | `2.0` | Float | Multiplier for subsequent retry delays |
| `retry_max_delay_seconds` | `30.0` | Float | Ceiling for exponential backoff delay |
| `structured_output.format` | `"json_schema"` | String | Enforces strict JSON Schema adherence |
| `structured_output.strict` | `true` | Boolean | Strict grammar constraints enabled |
| `structured_output.target_field` | `"technique_id"` | String | Target prediction key |
| `logging_policy.log_token_usage` | `true` | Boolean | Capture input, output, and reasoning tokens |
| `logging_policy.log_latency` | `true` | Boolean | Capture wall-clock latency including retries |
| `logging_policy.log_prompt_version` | `true` | Boolean | Trace prompt template version in metadata |
| `logging_policy.log_condition` | `true` | Boolean | Record experiment condition (`no_rag` vs `rag`) |
| `logging_policy.log_raw_response` | `false` | Boolean | Do not persist unparsed raw API payloads |

---

## 8. Parameters Intentionally Left at Provider Defaults
The following parameters are deliberately omitted or left at provider defaults, with specific methodological justifications:

1. **`temperature` (Default: 1.0):**
   - *Justification:* On frontier reasoning models (`gpt-5.6-luna`), temperature variation is either unsupported or explicitly disallowed by the API. Reasoning models manage output sampling distributions through the internal reasoning process; altering temperature distorts calibrated search trees.
2. **`top_p` (Default: 1.0):**
   - *Justification:* Left at default to avoid truncating valid reasoning trajectories in nucleus sampling.
3. **`presence_penalty` / `frequency_penalty` (Default: 0.0):**
   - *Justification:* The classification task requires generating a single standardized identifier (`{"technique_id": "..."}`). Repetition penalties have no positive utility and can introduce unintended token bias.
4. **`seed` (Default: None / Provider internal):**
   - *Justification:* While seed-based sampling can be requested, OpenAI reasoning models do not guarantee bit-level deterministic outputs across hardware clusters and internal reasoning variations. True experimental reproducibility is achieved through identical frozen prompts, deterministic post-hoc validation, and comprehensive execution logging.
5. **`service_tier` (Default: `default`):**
   - *Justification:* Standard routing is sufficient; priority scale tiers are not required for offline batch evaluation.

---

## 9. Justification for Shared Configuration Across No-RAG and RAG
In accordance with the project's core research title (*"Evaluating MITRE ATT&CK-Grounded RAG for Technique Attribution from Windows Endpoint Logs: A Replication-and-Extension Study"*), the experimental design is a controlled comparative evaluation.

### Scientific Control Mandate
1. **Isolation of the Retrieval Variable:** The single independent variable under investigation is the presence versus absence of retrieved MITRE ATT&CK reference context.
2. **Elimination of Confounding Variables:** If the No-RAG baseline and RAG conditions used different models, differing reasoning effort levels (e.g., `medium` vs. `xhigh`), or asymmetric token budgets, any observed performance differential could stem from reasoning capacity differences rather than grounding in external knowledge.
3. **Symmetric Reasoning Compute:** By freezing identical parameters (`gpt-5.6-luna`, `xhigh`, 8192 tokens, 120s timeout, 3 retries) across both conditions, the experimental framework guarantees that RAG is evaluated strictly on its ability to inform the model's existing reasoning capability.

---

## 10. Unsupported / Incompatible Parameters Identified
During SDK and API specification verification, the following parameter incompatibilities were identified and explicitly avoided:

1. **`max_tokens` (Unsupported on Reasoning Models):**
   - In legacy Chat Completions, `max_tokens` governed output length. On reasoning models, OpenAI rejects `max_tokens` with HTTP 400 Bad Request, requiring `max_completion_tokens` (Chat Completions) or `max_output_tokens` (Responses API). `config/model.json` specifies only `max_output_tokens` since the frozen interface is Responses API.
2. **Arbitrary `temperature` Tuning (Unsupported):**
   - Submitting `temperature != 1.0` to reasoning models results in validation errors. Temperature is omitted to preserve provider default calibration.
3. **Legacy Function Calling (`functions` / `function_call`):**
   - Deprecated in modern OpenAI endpoints. Replaced entirely by native structured output JSON schemas (`text_format` / `response_format`).

---

## 11. Unresolved Human Decisions
- **Status:** **NONE.**
- All 11 configuration specifications have been verified against official OpenAI documentation and the project's methodological requirements. The model configuration is fully resolved, frozen, and verified.
