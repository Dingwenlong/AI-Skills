---
name: skill-dawho-legacy-business-logic-api-excel
description: Analyze DAWHO legacy code business logic and produce migration-ready API detail output in Excel format. Use when Codex needs to reverse-engineer DAWHO old systems, trace business workflows, map module dependencies, extract business rules, and write Excel deliverables to the skill-relative output folder ../../skill-outputs for direct use in API detail sheets.
---

# Analyze DAWHO Legacy Logic To API Excel

## Path Rule

- Treat `../../skill-outputs` as a relative path from this skill folder.
- Resolve it to `<CODEX_HOME>/skill-outputs`.
- Do not hardcode machine-specific absolute paths such as `C:\Users\...\.codex\skill-outputs`.
- When passing `-OutputXlsx`, prefer a relative path under `../../skill-outputs` unless the user explicitly requires another location.

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

6. Resolve T24Query endpoint to IRIS key mapping (required when endpoint appears)
- Read IRIS summary workbook before writing `涉及BackendAPI` and `API 內部業務邏輯`.
- Workbook source:
  - `references/raw/TW T24 IRIS_OpenAPI_Summary_20230714.xlsx`
- For each endpoint text like `NetMMAQ/T24Query/WTMB_AC_BAL_DTL_LIST_ENQ.aspx`, derive lookup token by:
  1) take filename `WTMB_AC_BAL_DTL_LIST_ENQ.aspx`
  2) replace `_` with `.` -> `WTMB.AC.BAL.DTL.LIST.ENQ.aspx`
  3) keep substring starting from `TMB` -> `TMB.AC.BAL.DTL.LIST.ENQ.aspx`
  4) remove extension -> `TMB.AC.BAL.DTL.LIST.ENQ`
- For each AppService/common call text like `NCBSerialize.TMBI_B0100_TD_DTL_ENQ`, derive lookup token by:
  1) take method name after dot -> `TMBI_B0100_TD_DTL_ENQ`
  2) replace `_` with `.` -> `TMBI.B0100.TD.DTL.ENQ`
  3) keep substring starting from `TMB` (if already starts with `TMB`, keep as is)
- Use this token to lookup workbook column `Original VERSION/ENQUIRY`, then get corresponding `KEY`.
- Output replacement rules:
  - In `涉及BackendAPI`, output `IRIS -> <KEY>` (instead of raw `.../T24Query/...aspx` path or `NCBSerialize.TMB...` method text).
  - In `API 內部業務邏輯` step text, output `呼叫IRIS(<KEY>)`.
  - Example:
    - `NetMMAQ/T24Query/WTMB_AC_BAL_DTL_LIST_ENQ.aspx` -> token `TMB.AC.BAL.DTL.LIST.ENQ` -> `IRIS -> <KEY>`
    - `NCBSerialize.TMBI_B0100_TD_DTL_ENQ` -> token `TMBI.B0100.TD.DTL.ENQ` -> `IRIS -> <KEY>`

7. Resolve Common/utility method to NEWDA API detail mapping (required when common methods appear)
- Read common util mapping workbook before writing `涉及BackendAPI` and `API 內部業務邏輯`.
- Workbook source:
  - `references/raw/NEWDA_API_DETAIL_CommonUtil_20260209.xlsx`
- Lookup sheet:
  - `Api List`
- When logic includes common/shared methods (for example `Common.*`, `CommonLogic.*`, `Utility.*`), lookup related API entry in `Api List`.
- If related backend API entry exists, replace output format:
  - In `涉及BackendAPI`, use: `{Module} -> {API Name}({API Description})`
  - In step text, use: `{Module}.{API Name}({API Description})`

8. Produce analysis intermediate file (TSV)
- Write source TSV output to `../../skill-outputs/{apiName}_API_{seq:00}_{yyyyMMdd}_temp.tsv` relative to the skill folder (`<CODEX_HOME>/skill-outputs/...`).
- Use the section template in `references/report-template.md`.
- Keep each rule traceable to source locations.
- Keep one physical line per TSV row; do not insert raw multiline cell text directly in TSV.
- For in-cell line breaks, use literal `\n` markers in TSV and let converter render Excel LF.
- The `_temp.tsv` file is temporary and should be auto-deleted after conversion.

9. Convert TSV to final Excel deliverable (required)
- Run:
  - `powershell -ExecutionPolicy Bypass -File scripts/tsv_to_api_excel.ps1 -InputTsv ../../skill-outputs/{apiName}_API_{seq:00}_{yyyyMMdd}_temp.tsv -ApiPath ws/bank/timedeposit/ws_querytd.ashx`
- Auto filename rule (when `-OutputXlsx` not provided):
  - Write to `../../skill-outputs/<ashx檔名>_API_<序號2位>_<yyyyMMdd>.xlsx`
  - Example: `ws_querytd_API_01_20260304.xlsx`
  - Same day repeated runs auto-increment sequence (`01`, `02`, `03`...) to avoid overwrite.
- If fixed filename is required, pass `-OutputXlsx <relative-path-under-../../skill-outputs or explicit target path>`.
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
- If chain contains T24Query endpoint (`NetMMAQ/T24Query/...`) or NCBSerialize TMB method (`NCBSerialize.TMB...`), replace endpoint/method output with IRIS mapping result:
  - `涉及BackendAPI`: `IRIS -> <KEY>`
  - step text: `呼叫IRIS(<KEY>)`
- If chain contains common/shared methods and `Api List` has mapped API entry, replace output with NEWDA mapping result:
  - `涉及BackendAPI`: `{Module} -> {API Name}({API Description})`
  - step text: `{Module}.{API Name}({API Description})`
- Build example JSON based on actual Request/Response rows in current output.
- Request/Response `範例`欄位格式固定為 JSON 片段樣式：
  - `"<欄位名稱>": <範例值>`
  - string 值需加雙引號；number/boolean 值不加雙引號。
  - 例如：`"debitAcctValue":"18900100286661"`、`"availBalance":12345.89`
- Request/Response 欄位名稱統一使用 `camelCase`（lower camel case）。
- 產出的 Request/Response 欄位名稱需依欄位說明與業務語意推斷最合適命名（使用 `camelCase`），不可僅機械沿用舊欄位名。
- 原始欄位名稱需在同列 `備註` 補充說明（例如：`原欄位名稱: XXX`）。
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
  - Do not output `Source`/`path:line` in logic step content.

## Quality Bar

- Keep terminology consistent with old system naming to avoid ambiguity.
- Distinguish confirmed behavior from inferred behavior.
- Mark unknowns with explicit follow-up questions.
- Include migration notes for each core rule: preserve, simplify, or redesign.

## Deliverable Rules

- Fill request/response fields with concrete values and examples; do not leave placeholder tokens.
- Do not output `Source`/`path:line` in `API 內部業務邏輯` (including step rows and `涉及BackendAPI` row).
- Request/Response 備註欄位不強制填寫 Source。
- If value is computed, write formula explicitly in notes when needed (for example: `A + B`, `substring(x,0,10)`, `sum(list.amount)`).
- Use concise, implementation-facing wording suitable for API detail documents.
- If inference is used, clearly mark it as inference in the relevant row/notes.
- Keep `responseCode/responseMessage` aligned with latest `Api_Response_Codes*.xlsx`; if unmatched, mark as `Inference`.
- For T24Query endpoint mapping, if no `KEY` is found in `TW T24 IRIS_OpenAPI_Summary_20230714.xlsx`, mark as `Inference` and keep both derived token + original endpoint in notes.
- For common util mapping, if no matching row is found in `NEWDA_API_DETAIL_CommonUtil_20260209.xlsx` (`Api List`), mark as `Inference` and keep original common method signature in notes.
