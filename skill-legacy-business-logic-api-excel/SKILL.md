name: skill-legacy-business-logic-api-excel
description: Analyze legacy code business logic and produce migration-ready API detail output in Excel format. Use when Codex needs to reverse-engineer old systems, trace business workflows, map module dependencies, extract business rules, and generate ../../skill-outputs/<api>_API_XX_YYYYMMDD.xlsx.
---

# Analyze Legacy Logic To API Excel

## Workflow

1. Confirm analysis scope
- Confirm target modules, entry points, and expected business scenarios.
- Prioritize files that contain controller/service/DAO flow and database access.

2. Build code map quickly
- Use fast file discovery first (`rg --files`) and pattern search (`rg "keyword"`).
- Build a module map: input source, processing layer, data layer, external dependencies.

3. Trace end-to-end business flow
- Start from external entry points (API, UI action, batch job, message consumer).
- Follow function calls across layers until persistence/output side effects are clear.
- Record preconditions, branch conditions, and error paths.
- For each `*.ashx` entry, locate backend bridge variables first (for example: `_presenter`).
- Trace chain in strict order:
  - `ashx` -> `_presenter` target method
  - target method -> `XXXService` invoked methods
  - `XXXService` -> AppService(Release) `Service.Method`
- In AppService(Release), global-search the corresponding `Service.Method`, then continue tracing to:
  - DB table + SQL statement
  - or external system URL + method name
- If one API uses multiple common/shared methods, trace and document each method chain separately.

4. Extract business rules
- Separate technical behavior from business intent.
- Convert conditions, validations, and calculations into explicit business rules.
- Flag hidden rules from magic numbers, status codes, and hardcoded exceptions.

5. Resolve response codes from config workbook (required every run)
- Read response code config workbook before producing deliverables.
- Workbook source:
  - `references/raw/Api_Response_Codes*.xlsx` (pick the latest by filename date token, e.g. `20260213`).
- Determine module sheet by API domain (e.g., Exchange -> `E_Exchange`), then lookup codes in:
  1) module sheet
  2) `O_Common` fallback
- Do not invent `responseCode/responseMessage` when code exists in workbook.
- Prefer using:
  - `scripts/lookup_response_codes.py`
  - Example: `python scripts/lookup_response_codes.py --module-sheet E_Exchange --codes 0000 9997 9998 9999`

6. Produce analysis intermediate file (TSV)
- Write source TSV output to `../../skill-outputs/{apiName}_API_{seq:00}_{yyyyMMdd}_temp.tsv`.
- Use the section template in `references/report-template.md`.
- Keep each rule traceable to source locations.
- Keep one physical line per TSV row; do not insert raw multiline cell text directly in TSV.
- For in-cell line breaks, use literal `\n` markers in TSV and let converter render Excel LF.
- The `_temp.tsv` file is temporary and should be auto-deleted after conversion.

7. Convert TSV to final Excel deliverable (required)
- Run:
  - `powershell -ExecutionPolicy Bypass -File scripts/tsv_to_api_excel.ps1 -InputTsv ../../skill-outputs/{apiName}_API_{seq:00}_{yyyyMMdd}_temp.tsv -ApiPath ws/bank/timedeposit/ws_querytd.ashx`
- Auto filename rule (when `-OutputXlsx` not provided):
  - `<ashx檔名>_API_<序號2位>_<yyyyMMdd>.xlsx`
  - Example: `ws_querytd_API_01_20260304.xlsx`
  - Same day repeated runs auto-increment sequence (`01`, `02`, `03`...) to avoid overwrite.
- If fixed filename is required, pass `-OutputXlsx <path>`.
- Final delivery file must be `.xlsx`.
- Do not deliver `.md` as final output.
- Converter script reads portable style spec from:
  - `references/excel-style-spec-insurance.json`
- Style is applied by title/section rules, not fixed row numbers.
- Merge cells are applied by title/section merge rules in style spec.
- Alignment is applied by title/section alignment rules in style spec.
- Optional override:
  - `-StyleSpecPath <custom-style-spec-json>`

## Output Format (Excel Direct Paste)

- Style profile source reference:
  - `references/excel-style-spec-insurance.json`
- Keep style portable inside skill package (no external template file dependency at runtime).
- Output as tab-separated rows aligned to Excel columns `A~G`.
- Ensure the generated file can be copied and pasted into Excel without manual reformatting.
- Do not output Markdown tables, fenced code blocks, or nested bullet formatting in the final deliverable file.
- Keep block order fixed:
  - `API Name/API Description`
  - `Request`
  - `Response`
  - `範例`
  - `For中台開發人員`
  - `API 內部業務邏輯`
- Always include and fully expand:
  - `涉及BackendAPI`
  - `API 內部業務邏輯` step-by-step breakdown
- `API 內部業務邏輯` must be written as cross-layer flow:
  - `web(ashx)` -> `AppService(Release)` -> `DB/外圍系統`
- For common utility methods, expand nested DB dependencies in sub-items.
- Build example JSON based on actual Request/Response rows in current output.
- Request/Response `範例`欄位格式固定為 JSON 片段樣式：
  - `"<欄位名稱>": <範例值>`
  - string 值需加雙引號；number/boolean 值不加雙引號。
  - 例如：`"debitAcctValue":"18900100286661"`、`"availBalance":12345.89`
- Request/Response 的 `資料型態` 必須依 `範例` 值與業務語意推斷，不可預設全部寫 `string`。
  - `true/false` -> `boolean`
  - 不含小數點的數值 -> `int`
  - 含小數點的數值/金額/利率 -> `decimal`
  - `{...}` -> `json`
  - `[...]` -> `array`
  - 帳號/卡號/代碼/ID/可能有前導零或固定長度值 -> `string`（即使看起來像數字）
  - 日期時間若契約為文字格式（如 `yyyy/MM/dd HH:mm:ss`） -> `string`
- `資料型態` 與 `範例` 必須一致（例如 `decimal` 不可給 `"1.535%"` 這種帶符號字串）。
- In `範例` block:
  - Positive scenario: include Request JSON + Response JSON.
  - Other scenarios: leave Request column empty; only provide Response JSON.
- JSON in `範例` must be pretty-printed (multi-line, indented) for direct Excel readability.
- In-cell line breaks must be Excel `Alt+Enter` style (`LF` / `CHAR(10)`), not extra rows.
- Cell content that exceeds column width must wrap automatically.
- Apply merged cell layout using style spec merge rules (not hardcoded row numbers).
- Apply horizontal/vertical alignment using style spec alignment rules.
- Blank areas (including section separator rows and empty tail cells like `C1:G1`) must be rendered with no visual style (no fill, no border).
- In `範例`, Request/Response content cells must be vertically centered.
- Wrapped-content row height must expand based on content.
- Font rule for final `.xlsx`:
  - Chinese characters: `微軟正黑體`
  - Non-Chinese text: `Times New Roman`
  - Font size: `10`
- In `API 內部業務邏輯`:
  - One step per line.
  - Sub-steps are also one line each.
  - Sub-step lines must start with two spaces for indentation.
  - Do not chain multiple steps in one line with punctuation such as `；`.

## Quality Bar

- Keep terminology consistent with old system naming to avoid ambiguity.
- Distinguish confirmed behavior from inferred behavior.
- Mark unknowns with explicit follow-up questions.
- Include migration notes for each core rule: preserve, simplify, or redesign.

## Deliverable Rules

- Fill request/response fields with concrete values and examples; do not leave placeholder tokens.
- Keep source pointers (`path:line`) in backend logic section where critical.
- Request/Response 備註欄位不強制填寫 Source。
- If value is computed, write formula explicitly in notes when needed (for example: `A + B`, `substring(x,0,10)`, `sum(list.amount)`).
- Use concise, implementation-facing wording suitable for API detail documents.
- If inference is used, clearly mark it as inference in the relevant row/notes.
- Keep `responseCode/responseMessage` aligned with latest `Api_Response_Codes*.xlsx`; if unmatched, mark as `Inference`.
