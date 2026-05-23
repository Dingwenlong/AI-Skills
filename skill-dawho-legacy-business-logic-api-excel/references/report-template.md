# Excel Paste Template (A~G)

## Goal
- Produce intermediate plain-text TSV output that can be converted into final API detail Excel sheets.
- The intermediate output must be TSV-style rows (7 columns: A~G, separated by TAB).
- Do not use Markdown tables/fenced code blocks in the final deliverable file.
- Final deliverable must be `.xlsx` (not `.md`).
- Treat `output/skill-dawho-legacy-business-logic-api-excel` as a repo-local path from the current working directory.
- Prefer relative output paths; do not depend on user-specific absolute paths.
- Resolve `responseCode/responseMessage` from:
  - `references/raw/Api_Response_Codes*.xlsx` (自動取檔名日期最新版本，例如 `20260213`)
- Use module sheet first (e.g. `E_Exchange`), then fallback `O_Common`.
- Use `references/raw/Regression_Example.xlsx` as the structural regression baseline before final delivery.

## Excel Rendering Rules
- In-cell line break must use Excel `Alt+Enter` style (LF / `CHAR(10)`).
- `範例` JSON must be pretty-printed (multi-line, indented).
- Cell content overflow must use auto-wrap.
- Request/Response `範例` 欄位格式固定為：
  - `"<欄位名稱>": <範例值>`
  - string 值需加雙引號；number/boolean 值不加雙引號。
  - 例如：`"debitAcctValue":"18900100286661"`、`"availBalance":12345.89`
- Font in final `.xlsx`:
  - Chinese characters: `微軟正黑體`
  - Other characters: `Times New Roman`
  - Font size: `10`
- Style is loaded from portable skill spec:
  - `references/excel-style-spec-insurance.json`
- Background fill must be applied by title/section rules (not fixed row index).
- Merge cells must be applied by title/section merge rules (not fixed row index).
- Horizontal/vertical alignment must be applied by title/section alignment rules.
- Blank area must be unstyled (no fill/no border), including section separator rows and empty tail cells.
- In `範例`, Request/Response content cells use vertical center alignment.
- Wrapped rows must auto-expand row height according to cell content.

## Data Type Inference Rules (Request/Response)
- Do not default all fields to `string`.
- Infer `資料型態` from current row `範例` value + business semantics:
  - `true/false` -> `boolean`
  - integer literal (no decimal point) -> `int`
  - decimal literal (with decimal point) -> `decimal`
  - object literal (`{}`) -> `json`
  - array literal (`[]`) -> `array`
  - identifier-like fields (account/card/id/code/values with possible leading zero) -> `string`
  - datetime formatted text (for example `yyyy/MM/dd HH:mm:ss`) -> `string`
- `資料型態` must be consistent with `範例` value.
  - Example: `decimal` => `"openInterestRate":1.5350`
  - Example: `int` => `"enrollTimes":1`
  - Example: `boolean` => `"stairFlag":true`

## Template-Style Conversion Command
- Run conversion directly (auto filename by API path, style spec auto-loaded):
  - `powershell -ExecutionPolicy Bypass -File scripts/tsv_to_api_excel.ps1 -InputTsv <TSV_PATH> -ApiPath <ASHX_PATH>`
- Auto filename rule:
  - `output/skill-dawho-legacy-business-logic-api-excel/<ashx檔名>_API_<序號2位>_<yyyyMMdd>.xlsx`
  - Example: `ws_querytd_API_01_20260304.xlsx`
- Input TSV temp rule (auto when `-ApiPath` is provided):
  - Converter copies `-InputTsv` to `<ashx檔名>_API_<序號2位>_<yyyyMMdd>_Temp.tsv`
  - `_Temp.tsv` is deleted automatically after conversion.
- If fixed output path is needed:
  - `powershell -ExecutionPolicy Bypass -File scripts/tsv_to_api_excel.ps1 -InputTsv <TSV_PATH> -OutputXlsx output/skill-dawho-legacy-business-logic-api-excel/<OUTPUT_XLSX_PATH>`
- Optional custom style spec:
  - `powershell -ExecutionPolicy Bypass -File scripts/tsv_to_api_excel.ps1 -InputTsv <TSV_PATH> -ApiPath <ASHX_PATH> -StyleSpecPath <STYLE_SPEC_JSON_PATH>`
- Converter auto-runs regression check by default:
  - `powershell -ExecutionPolicy Bypass -File scripts/tsv_to_api_excel.ps1 -InputTsv <TSV_PATH> -ApiPath <ASHX_PATH>`
- Manual fallback regression check:
  - `python scripts/check_regression_example.py --xlsx <OUTPUT_XLSX_PATH>`
- Use `-SkipRegressionCheck` only for temporary debugging.

## Reference Sheet Style
- Spec file: `excel-style-spec-insurance.json`

## Fixed Block Order
1. `API  Name / API Description`
2. `Request`
3. `Response`
4. `範例`
5. `For中台開發人員`
6. `API 內部業務邏輯`

## Required Logic Blocks
- `涉及BackendAPI`
- `API 內部業務邏輯` (step-by-step)
- Expand common utility calls into nested DB dependencies.
- `範例` must be generated from current Request/Response rows.
- `API 內部業務邏輯` must show cross-layer chain:
  - `web(ashx)` -> `_presenter` -> `XXXService` -> `AppService(Release)` -> `DB/外圍系統`
- One API can call multiple common/shared methods; each method chain must be listed separately.
- `API 內部業務邏輯` formatting is strict:
  - One step per line.
  - Sub-step is also one line.
  - Sub-step line must start with two spaces.
  - Do not chain steps in one line with `；` or `;`.

## Row Template (write as TSV with A~G columns)

`API  Name<TAB>API Description<TAB><TAB><TAB><TAB><TAB>`
`<API_NAME><TAB><API_DESCRIPTION><TAB><TAB><TAB><TAB><TAB>`
`<TAB><TAB><TAB><TAB><TAB><TAB>`
`Request<TAB><TAB><TAB><TAB><TAB><TAB>`
`#<TAB>欄位名稱<TAB>資料型態<TAB>必填<TAB>說明<TAB>範例(格式: "欄位名稱":值)<TAB>備註(可寫處理邏輯/公式，不需Source)`
`1<TAB><REQUEST_FIELD_1><TAB><TYPE><TAB>Y/N<TAB><DESC><TAB>"<REQUEST_FIELD_1>":"<STRING_VALUE>"<TAB>Formula: <EXPR or N/A>`
`2<TAB><REQUEST_FIELD_2><TAB><TYPE><TAB>Y/N<TAB><DESC><TAB>"<REQUEST_FIELD_2>":<NUMBER_OR_BOOLEAN><TAB>Formula: <EXPR or N/A>`
`<TAB><TAB><TAB><TAB><TAB><TAB>`
`Response<TAB><TAB><TAB><TAB><TAB><TAB>`
`#<TAB>欄位名稱<TAB>資料型態<TAB>必填<TAB>欄位說明<TAB>範例(格式: "欄位名稱":值)<TAB>備註(可寫處理邏輯/公式，不需Source)`
`1<TAB>isSuccess<TAB>boolean<TAB>Y<TAB>API成功與否<TAB>"isSuccess":true<TAB>true ; false`
`2<TAB>responseCode<TAB>string<TAB>Y<TAB>回應代碼<TAB>"responseCode":"0000"<TAB>成功:0000其餘狀況為失敗`
`3<TAB>responseMessage<TAB>string<TAB>Y<TAB>回應訊息<TAB>"responseMessage":"成功！"<TAB>失敗狀況下回傳錯誤訊息`
`4<TAB>responseDT<TAB>string<TAB>Y<TAB>系統回應時間<TAB>"responseDT":"yyyy/MM/dd HH:mm:ss"<TAB>`
`5<TAB>responseData<TAB>json<TAB>Y<TAB>回應資料框<TAB>"responseData":{}<TAB>`
`5.01<TAB><LIST_NODE><TAB>array<TAB>Y<TAB>清單資料<TAB>"<LIST_NODE>":[]<TAB>`
`5.01.01<TAB><CHILD_FIELD_1><TAB>string<TAB>Y<TAB><DESC><TAB>"<CHILD_FIELD_1>":"<STRING_VALUE>"<TAB><LOGIC_OR_FORMULA>`
`5.01.02<TAB><CHILD_FIELD_2><TAB>int/decimal<TAB>Y<TAB><DESC><TAB>"<CHILD_FIELD_2>":<NUMBER_VALUE><TAB><LOGIC_OR_FORMULA>`
`<TAB><TAB><TAB><TAB><TAB><TAB>`
`範例<TAB><TAB><TAB><TAB><TAB><TAB>`
`情境說明<TAB>Request<TAB><TAB>Response<TAB><TAB><TAB>`
`正向情境<TAB><POSITIVE_REQUEST_JSON><TAB><TAB><POSITIVE_RESPONSE_JSON><TAB><TAB><TAB>`
`連接數據庫或下游服務失敗<TAB><TAB><TAB><DB_FAIL_RESPONSE_JSON><TAB><TAB><TAB>`
`查詢成功後,返回的數據為null<TAB><TAB><TAB><NULL_RESPONSE_JSON><TAB><TAB><TAB>`
`未輸入必填請求參數<TAB><TAB><TAB><PARAM_FAIL_RESPONSE_JSON><TAB><TAB><TAB>`
`<TAB><TAB><TAB><TAB><TAB><TAB>`
`For中台開發人員<TAB><TAB><TAB><TAB><TAB><TAB>`
`<TAB><TAB><TAB><TAB><TAB><TAB>`
`API 內部業務邏輯<TAB><TAB><TAB><TAB><TAB><TAB>`
`#<TAB>邏輯說明<TAB><TAB><TAB><TAB><TAB>`
`涉及BackendAPI<TAB>1. IRIS -> <TRANS_CODE> (<TRANS_NAME>)\n2. <DB_NAME>(<VERSION>) -> dbo.<TABLE_1> (<USAGE>)\n3. CommonUtil -> <METHOD> (<USAGE>)\n  3.1 <DB_NAME>(<VERSION>) -> dbo.<TABLE_2> (<USAGE>)\n  3.2 <DB_NAME>(<VERSION>) -> dbo.<TABLE_3> (<USAGE>)<TAB><TAB><TAB><TAB><TAB>`
`1: 初始化與參數處理<TAB>  1.1 <STEP_DETAIL>\n  1.2 <STEP_DETAIL><TAB><TAB><TAB><TAB><TAB>`
`2: 權限與交易驗證<TAB>  2.1 <STEP_DETAIL>\n  2.2 <STEP_DETAIL><TAB><TAB><TAB><TAB><TAB>`
`3: 核心資料處理<TAB>  3.1 <STEP_DETAIL>\n  3.2 SQL: <SQL_TEXT><TAB><TAB><TAB><TAB><TAB>`
`4: 接收數據,處理返回前端<TAB>  4.1 <STEP_DETAIL>\n  4.2 <STEP_DETAIL><TAB><TAB><TAB><TAB><TAB>`

## Quality Checklist
- Keep exactly 7 columns per row (A~G).
- Keep naming and wording consistent with legacy terms.
- Align section order, header rows, scenario labels, and merge layout with `Regression_Example.xlsx`.
- Mark inferred content clearly (e.g. `Inference`).
- Request/Response `範例` 欄位必須是 `"<欄位名稱>":值` 格式。
- Request/Response `資料型態` 必須依範例值推斷，不可全部寫 `string`。
- Positive scenario Request JSON must be assembled from Request section examples.
- Non-positive scenarios must keep Request column empty.
- Response JSON must use response codes/messages found from response code workbook.
- In-cell multi-line text must use Excel line break (Alt+Enter / LF).
- Request/Response 備註不需寫 Source；若是計算值可補公式。
- Do not output `Source` / `path:line` in `API 內部業務邏輯`.
- Run `python scripts/check_regression_example.py --xlsx <OUTPUT_XLSX_PATH>` before delivery.
