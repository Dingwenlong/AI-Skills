param(
    [Parameter(Mandatory = $true)]
    [string]$InputTsv,

    [string]$OutputXlsx = "",

    [string]$ApiPath = "",

    [string]$SheetName = "API_Detail",

    [string]$StyleSpecPath = ""
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

function Resolve-PathStrict {
    param(
        [Parameter(Mandatory = $true)]
        [string]$PathValue
    )

    if ([string]::IsNullOrWhiteSpace($PathValue)) {
        return $PathValue
    }

    if ([System.IO.Path]::IsPathRooted($PathValue)) {
        return [System.IO.Path]::GetFullPath($PathValue)
    }

    return [System.IO.Path]::GetFullPath((Join-Path (Get-Location).Path $PathValue))
}

function Get-ApiBaseName {
    param([string]$ApiPathValue)

    if ([string]::IsNullOrWhiteSpace($ApiPathValue)) {
        return ""
    }

    $normalized = $ApiPathValue.Trim().Replace("/", "\")
    $fileName = [System.IO.Path]::GetFileName($normalized)
    if ([string]::IsNullOrWhiteSpace($fileName)) {
        return ""
    }

    return [System.IO.Path]::GetFileNameWithoutExtension($fileName)
}

function Get-DefaultOutputDir {
    $skillRoot = [System.IO.Path]::GetFullPath((Join-Path $PSScriptRoot ".."))
    $codexHome = [System.IO.Path]::GetFullPath((Join-Path $skillRoot "..\.."))
    $dir = Join-Path $codexHome "skill-outputs"
    return [System.IO.Path]::GetFullPath($dir)
}

function Get-NextAutoOutputPath {
    param(
        [string]$OutputDir,
        [string]$ApiBaseName,
        [string]$DateToken
    )

    for ($i = 1; $i -le 99; $i++) {
        $seq = $i.ToString("00")
        $name = "{0}_API_{1}_{2}.xlsx" -f $ApiBaseName, $seq, $DateToken
        $candidate = Join-Path $OutputDir $name
        if (-not (Test-Path $candidate)) {
            return $candidate
        }
    }

    throw "No available output file slot for $ApiBaseName on $DateToken in $OutputDir"
}

function Get-TempTsvPathFromOutput {
    param([string]$OutputXlsxPath)

    $dir = Split-Path -Path $OutputXlsxPath -Parent
    $base = [System.IO.Path]::GetFileNameWithoutExtension($OutputXlsxPath)
    return Join-Path $dir ("{0}_Temp.tsv" -f $base)
}

function ConvertFromJsonCompat {
    param([string]$JsonText)

    if ([string]::IsNullOrWhiteSpace($JsonText)) {
        return $null
    }

    $cmd = Get-Command ConvertFrom-Json -ErrorAction Stop
    if ($cmd.Parameters.ContainsKey("Depth")) {
        return ($JsonText | ConvertFrom-Json -Depth 100)
    }

    return ($JsonText | ConvertFrom-Json)
}

function Convert-JsonIfNeeded {
    param([string]$Text)

    if ([string]::IsNullOrWhiteSpace($Text)) {
        return $Text
    }

    $trim = $Text.Trim()
    if (($trim.StartsWith("{") -or $trim.StartsWith("[")) -and $trim.Contains(":")) {
        try {
            $obj = ConvertFromJsonCompat -JsonText $trim
            return ($obj | ConvertTo-Json -Depth 100)
        }
        catch {
            return $Text
        }
    }

    return $Text
}

function Normalize-ExcelLineBreaks {
    param([string]$Text)

    if ($null -eq $Text) {
        return $Text
    }

    return (($Text -replace "`r`n", "`n") -replace "`r", "`n")
}

function Expand-LiteralEscapedLineBreaks {
    param([string]$Text)

    if ($null -eq $Text) {
        return $Text
    }

    # Convert literal "\n" markers to real LF for in-cell Alt+Enter rendering.
    return ($Text -replace '(?<!\\)\\n', "`n")
}

function Format-LogicStepLine {
    param([string]$Line)

    if ([string]::IsNullOrWhiteSpace($Line)) {
        return $Line
    }

    $trim = $Line.Trim()
    if ($trim -match '^(\d+(?:\.\d+)+)(?:[:.]|\s|$)') {
        $depth = ($Matches[1] -split '\.').Count - 1
        $indent = "  " * [Math]::Max(1, $depth)
        return "$indent$trim"
    }

    return $trim
}

function Normalize-LogicCell {
    param([string]$Text)

    if ([string]::IsNullOrWhiteSpace($Text)) {
        return $Text
    }

    $expanded = Expand-LiteralEscapedLineBreaks -Text $Text
    $normalized = Normalize-ExcelLineBreaks -Text $expanded
    $resultLines = New-Object System.Collections.Generic.List[string]
    $rawLines = $normalized -split "`n"

    foreach ($raw in $rawLines) {
        if ([string]::IsNullOrWhiteSpace($raw)) {
            continue
        }

        $parts = @($raw)
        $stepSeparatorPattern = "(?:\uFF1B|;)\s*(?=\d+(?:\.\d+)*(?:[:.]|\s))"
        if ($raw -match $stepSeparatorPattern) {
            $parts = [regex]::Split($raw, $stepSeparatorPattern)
        }

        foreach ($p in $parts) {
            if ([string]::IsNullOrWhiteSpace($p)) {
                continue
            }
            $resultLines.Add((Format-LogicStepLine -Line $p))
        }
    }

    if ($resultLines.Count -eq 0) {
        return $normalized
    }

    return ($resultLines -join "`n")
}

function Ensure-Dir {
    param([string]$FilePath)

    $dir = Split-Path -Path $FilePath -Parent
    if (-not [string]::IsNullOrWhiteSpace($dir) -and -not (Test-Path $dir)) {
        New-Item -Path $dir -ItemType Directory -Force | Out-Null
    }
}

function Normalize-TsvColumns {
    param(
        [string[]]$Columns,
        [int]$ExpectedColumns = 7
    )

    $normalized = New-Object System.Collections.Generic.List[string]
    foreach ($col in $Columns) {
        $normalized.Add([string]$col)
    }

    if ($normalized.Count -gt $ExpectedColumns) {
        $head = New-Object System.Collections.Generic.List[string]
        for ($i = 0; $i -lt ($ExpectedColumns - 1); $i++) {
            $head.Add($normalized[$i])
        }
        $tail = ($normalized.GetRange($ExpectedColumns - 1, $normalized.Count - ($ExpectedColumns - 1)) -join "`t")
        $head.Add($tail)
        $normalized = $head
    }

    while ($normalized.Count -lt $ExpectedColumns) {
        $normalized.Add("")
    }

    return ,$normalized.ToArray()
}

function Get-LastContentColumn {
    param([string[]]$Columns)

    for ($i = $Columns.Length; $i -ge 1; $i--) {
        if (-not [string]::IsNullOrWhiteSpace([string]$Columns[$i - 1])) {
            return $i
        }
    }

    return 1
}

function Test-IsContinuationLine {
    param(
        [string]$Line,
        [string[]]$CurrentRow
    )

    if ($null -eq $CurrentRow) {
        return $false
    }

    # Any TAB means it is a new row in TSV (even if not all 7 cols are populated).
    if ($Line.Contains("`t")) {
        return $false
    }

    $trim = $Line.Trim()
    if ([string]::IsNullOrWhiteSpace($trim)) {
        return $false
    }

    # Strong row-start patterns should not be merged into previous row.
    if ($trim -match '^(#|API  Name|Request|Response|範例|For中台開發人員|API 內部業務邏輯|涉及BackendAPI|情境說明|正向情境|連接數據庫失敗|查詢成功後,返回的數據為null|未輸入必填請求參數)$') {
        return $false
    }
    if ($trim -match '^\d+(?:\.\d+)*:') {
        return $false
    }

    # Merge only when previous row already has content beyond col A.
    for ($i = 2; $i -le $CurrentRow.Length; $i++) {
        if (-not [string]::IsNullOrWhiteSpace([string]$CurrentRow[$i - 1])) {
            return $true
        }
    }

    return $false
}

function Get-TsvRows {
    param(
        [string]$Path,
        [int]$ExpectedColumns = 7
    )

    $physicalLines = Get-Content -Path $Path -Encoding UTF8
    $rows = New-Object System.Collections.Generic.List[object]
    $currentRow = $null
    $appendCol = 1

    foreach ($line in $physicalLines) {
        if (Test-IsContinuationLine -Line $line -CurrentRow $currentRow) {
            if ([string]::IsNullOrWhiteSpace([string]$currentRow[$appendCol - 1])) {
                $currentRow[$appendCol - 1] = $line
            }
            else {
                $currentRow[$appendCol - 1] = ([string]$currentRow[$appendCol - 1]) + "`n" + $line
            }
            continue
        }

        if ($null -ne $currentRow) {
            $rows.Add($currentRow)
        }

        $cols = $line.Split(@([char]9), [System.StringSplitOptions]::None)
        $currentRow = Normalize-TsvColumns -Columns $cols -ExpectedColumns $ExpectedColumns
        $appendCol = Get-LastContentColumn -Columns $currentRow
    }

    if ($null -ne $currentRow) {
        $rows.Add($currentRow)
    }

    return $rows
}

function Resolve-RowRangeAddress {
    param(
        [int]$Row,
        [string]$RangeSpec
    )

    if ([string]::IsNullOrWhiteSpace($RangeSpec)) {
        return "A$Row:G$Row"
    }

    $range = $RangeSpec.Trim().ToUpperInvariant()
    if ($range -match '^([A-Z]+):([A-Z]+)$') {
        return "$($Matches[1])${Row}:$($Matches[2])${Row}"
    }
    if ($range -match '^([A-Z]+)$') {
        return "$($Matches[1])$Row"
    }

    return $range
}

function Get-RuleRangeSpecs {
    param($Rule)

    $ranges = New-Object System.Collections.Generic.List[string]
    if ($null -ne $Rule.PSObject.Properties["ranges"]) {
        foreach ($r in $Rule.ranges) {
            if (-not [string]::IsNullOrWhiteSpace([string]$r)) {
                $ranges.Add([string]$r)
            }
        }
    }
    elseif ($null -ne $Rule.PSObject.Properties["range"]) {
        $ranges.Add([string]$Rule.range)
    }
    else {
        $ranges.Add("A:G")
    }

    return $ranges
}

function Test-RuleTitleMatch {
    param(
        [string]$Title,
        $Rule
    )

    if ($null -ne $Rule.PSObject.Properties["title_regex"]) {
        return $Title -match [string]$Rule.title_regex
    }
    if ($null -ne $Rule.PSObject.Properties["title"]) {
        return $Title -eq [string]$Rule.title
    }
    return $false
}

function Apply-RowFormatRule {
    param(
        $Worksheet,
        [int]$Row,
        $Rule
    )

    $ranges = Get-RuleRangeSpecs -Rule $Rule
    foreach ($rangeSpec in $ranges) {
        $address = Resolve-RowRangeAddress -Row $Row -RangeSpec $rangeSpec
        $target = $Worksheet.Range($address)

        if ($null -ne $Rule.PSObject.Properties["fill_color"]) {
            $target.Interior.Color = [int]$Rule.fill_color
        }
        if ($null -ne $Rule.PSObject.Properties["bold"]) {
            $target.Font.Bold = [bool]$Rule.bold
        }
        if ($null -ne $Rule.PSObject.Properties["horizontal_alignment"]) {
            $target.HorizontalAlignment = [int]$Rule.horizontal_alignment
        }
        if ($null -ne $Rule.PSObject.Properties["vertical_alignment"]) {
            $target.VerticalAlignment = [int]$Rule.vertical_alignment
        }
        if ($null -ne $Rule.PSObject.Properties["wrap_text"]) {
            $target.WrapText = [bool]$Rule.wrap_text
        }
    }
}

function Merge-RowByRule {
    param(
        $Worksheet,
        [int]$Row,
        $Rule
    )

    $ranges = Get-RuleRangeSpecs -Rule $Rule
    foreach ($rangeSpec in $ranges) {
        $address = Resolve-RowRangeAddress -Row $Row -RangeSpec $rangeSpec
        $target = $Worksheet.Range($address)
        if ($target.MergeCells) {
            $target.UnMerge()
        }
        $target.Merge() | Out-Null
    }
}

function Apply-RuleSet {
    param(
        $Worksheet,
        [int]$LastRow,
        [object[]]$Rules,
        [string]$Kind # "format" / "merge"
    )

    if ($null -eq $Rules -or $Rules.Count -eq 0) {
        return
    }

    foreach ($rule in $Rules) {
        $mode = "current_row"
        if ($null -ne $rule.PSObject.Properties["mode"]) {
            $mode = [string]$rule.mode
        }

        $anchorRows = New-Object System.Collections.Generic.List[int]
        for ($r = 1; $r -le $LastRow; $r++) {
            $title = ([string]$Worksheet.Cells.Item($r, 1).Value2).Trim()
            if ([string]::IsNullOrWhiteSpace($title)) {
                continue
            }
            if (Test-RuleTitleMatch -Title $title -Rule $rule) {
                $anchorRows.Add($r)
            }
        }

        foreach ($anchor in $anchorRows) {
            $startOffset = 0
            if ($null -ne $rule.PSObject.Properties["start_offset"]) {
                $startOffset = [int]$rule.start_offset
            }
            $startRow = $anchor + $startOffset

            if ($mode -eq "current_row") {
                if ($startRow -lt 1 -or $startRow -gt $LastRow) {
                    continue
                }
                if ($Kind -eq "merge") {
                    Merge-RowByRule -Worksheet $Worksheet -Row $startRow -Rule $rule
                }
                else {
                    Apply-RowFormatRule -Worksheet $Worksheet -Row $startRow -Rule $rule
                }
                continue
            }

            if ($mode -ne "block_until_blank") {
                continue
            }

            $stopWhenBlank = $false
            if ($null -ne $rule.PSObject.Properties["stop_when_colA_blank"]) {
                $stopWhenBlank = [bool]$rule.stop_when_colA_blank
            }

            $maxRows = [int]::MaxValue
            if ($null -ne $rule.PSObject.Properties["max_rows"]) {
                $maxRows = [int]$rule.max_rows
            }

            $count = 0
            for ($rr = $startRow; $rr -le $LastRow; $rr++) {
                if ($count -ge $maxRows) {
                    break
                }
                if ($stopWhenBlank) {
                    $titleA = ([string]$Worksheet.Cells.Item($rr, 1).Value2).Trim()
                    if ([string]::IsNullOrWhiteSpace($titleA)) {
                        break
                    }
                }

                if ($Kind -eq "merge") {
                    Merge-RowByRule -Worksheet $Worksheet -Row $rr -Rule $rule
                }
                else {
                    Apply-RowFormatRule -Worksheet $Worksheet -Row $rr -Rule $rule
                }
                $count++
            }
        }
    }
}

function Is-BlankText {
    param([string]$Text)

    return [string]::IsNullOrWhiteSpace($Text)
}

function Clear-RangeVisualStyle {
    param($Range)

    # xlNone for border line style
    $Range.Borders.LineStyle = -4142
    # No fill
    $Range.Interior.Pattern = -4142
}

function Remove-StyleFromBlankAreas {
    param(
        $Worksheet,
        [int]$LastRow,
        [int]$LastCol
    )

    for ($r = 1; $r -le $LastRow; $r++) {
        $rowHasContent = $false

        for ($c = 1; $c -le $LastCol; $c++) {
            $cell = $Worksheet.Cells.Item($r, $c)
            if ($cell.MergeCells) {
                $merge = $cell.MergeArea
                $topRow = [int]$merge.Row
                $leftCol = [int]$merge.Column
                if ($r -ne $topRow -or $c -ne $leftCol) {
                    continue
                }
            }

            $val = [string]$cell.Value2
            if (-not (Is-BlankText -Text $val)) {
                $rowHasContent = $true
                break
            }
        }

        if (-not $rowHasContent) {
            $rowRange = $Worksheet.Range("A${r}:G${r}")
            Clear-RangeVisualStyle -Range $rowRange
            continue
        }

        for ($c = 1; $c -le $LastCol; $c++) {
            $cell = $Worksheet.Cells.Item($r, $c)
            if ($cell.MergeCells) {
                $merge = $cell.MergeArea
                $topRow = [int]$merge.Row
                $leftCol = [int]$merge.Column
                if ($r -ne $topRow -or $c -ne $leftCol) {
                    continue
                }

                $val = [string]$cell.Value2
                if (Is-BlankText -Text $val) {
                    # Keep structural style for intentionally merged blank areas.
                    continue
                }
            }
            else {
                $val = [string]$cell.Value2
                if (Is-BlankText -Text $val) {
                    Clear-RangeVisualStyle -Range $cell
                }
            }
        }
    }
}

function Expand-RowHeightForWrappedContent {
    param(
        $Worksheet,
        [int]$LastRow,
        [int]$LastCol,
        [double]$BaseRowHeight = 15.0
    )

    for ($r = 1; $r -le $LastRow; $r++) {
        $maxLines = 1

        for ($c = 1; $c -le $LastCol; $c++) {
            $cell = $Worksheet.Cells.Item($r, $c)
            if ($cell.MergeCells) {
                $merge = $cell.MergeArea
                $topRow = [int]$merge.Row
                $leftCol = [int]$merge.Column
                if ($r -ne $topRow -or $c -ne $leftCol) {
                    continue
                }
                if (-not [bool]$merge.WrapText) {
                    continue
                }
            }
            else {
                if (-not [bool]$cell.WrapText) {
                    continue
                }
            }

            $text = Normalize-ExcelLineBreaks -Text ([string]$cell.Value2)
            if (Is-BlankText -Text $text) {
                continue
            }

            $lineCount = [regex]::Matches($text, "`n").Count + 1
            if ($lineCount -gt $maxLines) {
                $maxLines = $lineCount
            }
        }

        if ($maxLines -gt 1) {
            $targetHeight = ($BaseRowHeight * $maxLines) + 2
            # Excel row height hard limit is around 409.5; clamp to avoid COMException.
            if ($targetHeight -gt 409.0) {
                $targetHeight = 409.0
            }
            $rowObj = $Worksheet.Rows.Item($r)
            if ([double]$rowObj.RowHeight -lt $targetHeight) {
                try {
                    $rowObj.RowHeight = $targetHeight
                }
                catch {
                    # Keep workbook generation resilient if Excel rejects specific row-height writes.
                }
            }
        }
    }
}

$apiBase = Get-ApiBaseName -ApiPathValue $ApiPath
if ([string]::IsNullOrWhiteSpace($OutputXlsx)) {
    if ([string]::IsNullOrWhiteSpace($apiBase)) {
        throw "OutputXlsx is empty. Provide -OutputXlsx or -ApiPath (example: ws/bank/timedeposit/ws_querytd.ashx)."
    }

    $dateToken = Get-Date -Format "yyyyMMdd"
    $defaultOutDir = Get-DefaultOutputDir
    $OutputXlsx = Get-NextAutoOutputPath -OutputDir $defaultOutDir -ApiBaseName $apiBase -DateToken $dateToken
}

$InputTsv = Resolve-PathStrict -PathValue $InputTsv
$OutputXlsx = Resolve-PathStrict -PathValue $OutputXlsx
if (-not [string]::IsNullOrWhiteSpace($StyleSpecPath)) {
    $StyleSpecPath = Resolve-PathStrict -PathValue $StyleSpecPath
}

if (-not (Test-Path $InputTsv)) {
    throw "Input TSV not found: $InputTsv"
}

if ([System.IO.Path]::GetExtension($OutputXlsx).ToLowerInvariant() -ne ".xlsx") {
    $OutputXlsx = [System.IO.Path]::ChangeExtension($OutputXlsx, ".xlsx")
}

Ensure-Dir -FilePath $OutputXlsx

$workingInputTsv = $InputTsv
$tempTsvPath = ""
$removeTempTsv = $false
if (-not [string]::IsNullOrWhiteSpace($apiBase)) {
    $tempTsvPath = Get-TempTsvPathFromOutput -OutputXlsxPath $OutputXlsx
    Copy-Item -Path $InputTsv -Destination $tempTsvPath -Force
    $workingInputTsv = $tempTsvPath
    $removeTempTsv = $true
}

if ([string]::IsNullOrWhiteSpace($StyleSpecPath)) {
    $StyleSpecPath = Join-Path (Split-Path -Parent $PSScriptRoot) "references\excel-style-spec-insurance.json"
}
if (-not (Test-Path $StyleSpecPath)) {
    throw "Style spec not found: $StyleSpecPath"
}

$styleSpecRaw = Get-Content -Path $StyleSpecPath -Raw -Encoding UTF8
$styleSpec = ConvertFromJsonCompat -JsonText $styleSpecRaw

$excel = $null
$workbook = $null
$worksheet = $null

try {
    $excel = New-Object -ComObject Excel.Application
    $excel.Visible = $false
    $excel.DisplayAlerts = $false

    $workbook = $excel.Workbooks.Add()
    $worksheet = $workbook.Worksheets.Item(1)

    if (-not [string]::IsNullOrWhiteSpace($SheetName)) {
        $worksheet.Name = $SheetName.Substring(0, [Math]::Min(31, $SheetName.Length))
    }

    $rowsData = Get-TsvRows -Path $workingInputTsv -ExpectedColumns 7
    $sectionTitle = [string]$styleSpec.context_rules.api_logic_section_title
    $inApiLogicSection = $false
    $row = 1

    foreach ($cols in $rowsData) {
        $colA = ""
        if ($cols.Length -ge 1) {
            $colA = [string]$cols[0]
        }
        if ($colA.Trim() -eq $sectionTitle) {
            $inApiLogicSection = $true
        }

        for ($c = 1; $c -le 7; $c++) {
            $val = ""
            if ($c -le $cols.Length) {
                $val = [string]$cols[$c - 1]
            }

            if ($inApiLogicSection -and $c -eq 2) {
                $val = Normalize-LogicCell -Text $val
            }
            else {
                # Expand literal "\n" markers for all non-logic cells,
                # especially JSON examples and explanatory text blocks.
                $val = Expand-LiteralEscapedLineBreaks -Text $val
            }

            $val = Convert-JsonIfNeeded -Text $val
            $val = Normalize-ExcelLineBreaks -Text $val
            $worksheet.Cells.Item($row, $c).Value2 = $val
        }

        $row++
    }

    $lastRow = [Math]::Max(1, $row - 1)
    $lastCol = 7
    $used = $worksheet.Range($worksheet.Cells.Item(1, 1), $worksheet.Cells.Item($lastRow, $lastCol))

    # Base format from portable style spec.
    $used.HorizontalAlignment = [int]$styleSpec.base.horizontal_alignment
    $used.VerticalAlignment = [int]$styleSpec.base.vertical_alignment
    $used.WrapText = [bool]$styleSpec.base.wrap_text
    $used.Font.Name = "Times New Roman"
    $used.Font.Size = [double]$styleSpec.base.font_size
    if ($null -ne $styleSpec.base.PSObject.Properties["base_fill_color"]) {
        $used.Interior.Color = [int]$styleSpec.base.base_fill_color
    }

    foreach ($width in $styleSpec.column_widths.PSObject.Properties) {
        $worksheet.Columns.Item($width.Name).ColumnWidth = [double]$width.Value
    }

    if ($styleSpec.borders.enabled -eq $true) {
        $borders = $used.Borders
        $borders.LineStyle = [int]$styleSpec.borders.line_style
        $borders.Weight = [int]$styleSpec.borders.weight
        if ($null -ne $styleSpec.borders.PSObject.Properties["color"]) {
            $borders.Color = [int]$styleSpec.borders.color
        }
    }

    # Merge rules by title/section.
    if ($null -ne $styleSpec.PSObject.Properties["merge_rules"]) {
        Apply-RuleSet -Worksheet $worksheet -LastRow $lastRow -Rules @($styleSpec.merge_rules) -Kind "merge"
    }

    # Title-based styling rules.
    $apiNameTitle = [string]$styleSpec.context_rules.api_name_title
    $apiLogicLeftTitle = [string]$styleSpec.context_rules.api_logic_left_title
    $apiLogicLeftRegex = [string]$styleSpec.context_rules.api_logic_left_regex
    $apiLogicLeftFillColor = [int]$styleSpec.context_rules.api_logic_left_fill_color
    $apiNameNextRowDescFill = [int]$styleSpec.context_rules.api_name_next_row_description_fill
    $prevNonEmptyTitle = ""
    $inApiLogicSection = $false

    for ($r = 1; $r -le $lastRow; $r++) {
        $title = ([string]$worksheet.Cells.Item($r, 1).Value2).Trim()
        if ([string]::IsNullOrWhiteSpace($title)) {
            continue
        }

        if ($title -eq $sectionTitle) {
            $inApiLogicSection = $true
        }

        foreach ($rule in $styleSpec.title_rules) {
            if (Test-RuleTitleMatch -Title $title -Rule $rule) {
                Apply-RowFormatRule -Worksheet $worksheet -Row $r -Rule $rule
            }
        }

        if ($prevNonEmptyTitle -eq $apiNameTitle) {
            $worksheet.Range("B$r").Interior.Color = $apiNameNextRowDescFill
        }

        if ($inApiLogicSection -and ($title -eq $apiLogicLeftTitle -or $title -match $apiLogicLeftRegex)) {
            $worksheet.Range("A$r").Interior.Color = $apiLogicLeftFillColor
        }

        $prevNonEmptyTitle = $title
    }

    # Alignment rules by title/section.
    if ($null -ne $styleSpec.PSObject.Properties["alignment_rules"]) {
        Apply-RuleSet -Worksheet $worksheet -LastRow $lastRow -Rules @($styleSpec.alignment_rules) -Kind "format"
    }

    # Remove visual style for blank cells/blank separator rows to keep focus on content.
    Remove-StyleFromBlankAreas -Worksheet $worksheet -LastRow $lastRow -LastCol $lastCol

    # Chinese chars -> 微軟正黑體, others remain Times New Roman
    $pattern = '[\u3400-\u4DBF\u4E00-\u9FFF\uF900-\uFAFF\u3000-\u303F\uFF00-\uFFEF]'
    for ($r = 1; $r -le $lastRow; $r++) {
        for ($c = 1; $c -le $lastCol; $c++) {
            $cell = $worksheet.Cells.Item($r, $c)
            $text = [string]$cell.Text
            if ([string]::IsNullOrEmpty($text)) {
                continue
            }

            $cell.Characters(1, $text.Length).Font.Name = "Times New Roman"
            $matches = [regex]::Matches($text, $pattern)
            foreach ($m in $matches) {
                $cell.Characters($m.Index + 1, $m.Length).Font.Name = "微軟正黑體"
            }
        }
    }

    $used.EntireRow.AutoFit() | Out-Null
    $baseRowHeight = 15.0
    if ($null -ne $styleSpec.base.PSObject.Properties["default_row_height"]) {
        $baseRowHeight = [double]$styleSpec.base.default_row_height
    }
    Expand-RowHeightForWrappedContent -Worksheet $worksheet -LastRow $lastRow -LastCol $lastCol -BaseRowHeight $baseRowHeight
    $workbook.SaveAs($OutputXlsx, 51)
}
finally {
    if ($workbook -ne $null) {
        $workbook.Close($false)
        [void][System.Runtime.InteropServices.Marshal]::ReleaseComObject($workbook)
    }
    if ($worksheet -ne $null) {
        [void][System.Runtime.InteropServices.Marshal]::ReleaseComObject($worksheet)
    }
    if ($excel -ne $null) {
        $excel.Quit()
        [void][System.Runtime.InteropServices.Marshal]::ReleaseComObject($excel)
    }

    [GC]::Collect()
    [GC]::WaitForPendingFinalizers()

    if ($removeTempTsv -and -not [string]::IsNullOrWhiteSpace($tempTsvPath) -and (Test-Path $tempTsvPath)) {
        Remove-Item -Path $tempTsvPath -Force -ErrorAction SilentlyContinue
    }
}

Write-Output "Wrote: $OutputXlsx"
