#!/usr/bin/env python3
"""
Validate generated API detail workbooks against Regression_Example.xlsx.

This script uses the regression example as a structural baseline and checks:
1) sheet name and sheet count
2) A:G column widths
3) required section order
4) fixed header rows
5) scenario row labels
6) merge layout in scenario / middle-office / API-logic blocks

It intentionally focuses on stable layout signals rather than business content.
"""

from __future__ import annotations

import argparse
import re
import sys
import zipfile
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Tuple
import xml.etree.ElementTree as ET

NS = {
    "main": "http://schemas.openxmlformats.org/spreadsheetml/2006/main",
    "pkg": "http://schemas.openxmlformats.org/package/2006/relationships",
    "r": "http://schemas.openxmlformats.org/officeDocument/2006/relationships",
}

SECTION_TITLES = [
    "API  Name",
    "Request",
    "Response",
    "範例",
    "For中台開發人員",
    "API 內部業務邏輯",
]


@dataclass
class SheetModel:
    sheet_names: List[str]
    selected_sheet: str
    cells: Dict[Tuple[int, int], str]
    widths: Dict[int, float]
    merges: List[Tuple[int, int, int, int]]
    max_row: int


def _load_shared_strings(zf: zipfile.ZipFile) -> List[str]:
    if "xl/sharedStrings.xml" not in zf.namelist():
        return []

    root = ET.fromstring(zf.read("xl/sharedStrings.xml"))
    result: List[str] = []
    for si in root.findall("main:si", NS):
        text = "".join((t.text or "") for t in si.findall(".//main:t", NS))
        result.append(text)
    return result


def _cell_text(cell: ET.Element, shared: List[str]) -> str:
    ctype = cell.attrib.get("t")
    value = cell.find("main:v", NS)
    if ctype == "s" and value is not None:
        idx = int(value.text or "0")
        return shared[idx] if 0 <= idx < len(shared) else ""
    if ctype == "inlineStr":
        text = cell.find(".//main:t", NS)
        return (text.text or "") if text is not None else ""
    if value is not None:
        return value.text or ""
    return ""


def _get_sheet_entries(zf: zipfile.ZipFile) -> List[Tuple[str, str]]:
    workbook = ET.fromstring(zf.read("xl/workbook.xml"))
    rels = ET.fromstring(zf.read("xl/_rels/workbook.xml.rels"))
    rel_map = {r.attrib["Id"]: r.attrib["Target"] for r in rels.findall("pkg:Relationship", NS)}

    entries: List[Tuple[str, str]] = []
    for sheet in workbook.findall("main:sheets/main:sheet", NS):
        name = sheet.attrib.get("name", "")
        rel_id = sheet.attrib.get(f"{{{NS['r']}}}id", "")
        target = rel_map.get(rel_id, "")
        if target and not target.startswith("worksheets/"):
            target = "worksheets/" + target.split("/")[-1]
        entries.append((name, "xl/" + target))
    return entries


def _col_to_index(col: str) -> int:
    value = 0
    for ch in col:
        value = value * 26 + (ord(ch) - 64)
    return value


def _index_to_col(index: int) -> str:
    result = ""
    while index > 0:
        index, rem = divmod(index - 1, 26)
        result = chr(65 + rem) + result
    return result


def _parse_cell_ref(ref: str) -> Tuple[int, int]:
    match = re.match(r"^([A-Z]+)(\d+)$", ref)
    if not match:
        raise ValueError(f"Unsupported cell ref: {ref}")
    return _col_to_index(match.group(1)), int(match.group(2))


def _parse_merge_ref(ref: str) -> Tuple[int, int, int, int]:
    start_ref, end_ref = ref.split(":")
    start_col, start_row = _parse_cell_ref(start_ref)
    end_col, end_row = _parse_cell_ref(end_ref)
    return start_row, start_col, end_row, end_col


def load_sheet_model(path: Path, sheet_name: str | None = None) -> SheetModel:
    with zipfile.ZipFile(path) as zf:
        shared = _load_shared_strings(zf)
        entries = _get_sheet_entries(zf)
        if not entries:
            raise ValueError(f"No sheets found in workbook: {path}")

        sheet_names = [name for name, _ in entries]
        selected_name, selected_path = entries[0]
        if sheet_name:
            for name, target in entries:
                if name == sheet_name:
                    selected_name, selected_path = name, target
                    break
            else:
                raise ValueError(f"Sheet not found: {sheet_name}")

        root = ET.fromstring(zf.read(selected_path))
        cells: Dict[Tuple[int, int], str] = {}
        max_row = 0

        sheet_data = root.find("main:sheetData", NS)
        if sheet_data is not None:
            for row in sheet_data.findall("main:row", NS):
                row_num = int(row.attrib.get("r", "0"))
                max_row = max(max_row, row_num)
                for cell in row.findall("main:c", NS):
                    ref = cell.attrib.get("r", "")
                    if not ref:
                        continue
                    col_idx, row_idx = _parse_cell_ref(ref)
                    text = _cell_text(cell, shared).strip()
                    cells[(row_idx, col_idx)] = text

        widths: Dict[int, float] = {}
        cols = root.find("main:cols", NS)
        if cols is not None:
            for col in cols.findall("main:col", NS):
                min_col = int(col.attrib.get("min", "0"))
                max_col = int(col.attrib.get("max", "0"))
                width = float(col.attrib.get("width", "0"))
                for idx in range(min_col, max_col + 1):
                    widths[idx] = width

        merges: List[Tuple[int, int, int, int]] = []
        merge_cells = root.find("main:mergeCells", NS)
        if merge_cells is not None:
            for merge_cell in merge_cells.findall("main:mergeCell", NS):
                ref = merge_cell.attrib.get("ref", "")
                if ":" not in ref:
                    continue
                merges.append(_parse_merge_ref(ref))

        return SheetModel(
            sheet_names=sheet_names,
            selected_sheet=selected_name,
            cells=cells,
            widths=widths,
            merges=merges,
            max_row=max_row,
        )


def cell_value(model: SheetModel, row: int, col: int) -> str:
    return model.cells.get((row, col), "").strip()


def row_values(model: SheetModel, row: int, start_col: int = 1, end_col: int = 7) -> List[str]:
    return [cell_value(model, row, col) for col in range(start_col, end_col + 1)]


def row_spans(model: SheetModel, row: int) -> List[str]:
    spans: List[Tuple[int, str]] = []
    for start_row, start_col, end_row, end_col in model.merges:
        if start_row == row and end_row == row:
            if start_col == end_col:
                spec = _index_to_col(start_col)
            else:
                spec = f"{_index_to_col(start_col)}:{_index_to_col(end_col)}"
            spans.append((start_col, spec))
    spans.sort(key=lambda item: item[0])
    return [spec for _, spec in spans]


def find_rows_in_col_a(model: SheetModel, text: str) -> List[int]:
    rows = [row for row in range(1, model.max_row + 1) if cell_value(model, row, 1) == text]
    return rows


def require_single_row(model: SheetModel, text: str, failures: List[str]) -> int | None:
    rows = find_rows_in_col_a(model, text)
    if len(rows) != 1:
        failures.append(f'Expected exactly one row with A="{text}", found {len(rows)}.')
        return None
    return rows[0]


def collect_scenario_labels(model: SheetModel, failures: List[str]) -> List[str]:
    example_row = require_single_row(model, "範例", failures)
    middle_row = require_single_row(model, "For中台開發人員", failures)
    if example_row is None or middle_row is None:
        return []

    labels: List[str] = []
    for row in range(example_row + 2, middle_row):
        label = cell_value(model, row, 1)
        if label:
            labels.append(label)
    return labels


def compare_row_values(label: str, expected: List[str], actual: List[str], failures: List[str]) -> None:
    if expected != actual:
        failures.append(
            f'{label} row mismatch. Expected {expected!r}, got {actual!r}.'
        )


def compare_row_spans(label: str, expected: List[str], actual: List[str], failures: List[str]) -> None:
    if expected != actual:
        failures.append(
            f'{label} merge mismatch. Expected {expected!r}, got {actual!r}.'
        )


def validate(example: SheetModel, target: SheetModel, tolerance: float) -> List[str]:
    failures: List[str] = []

    if len(target.sheet_names) != len(example.sheet_names):
        failures.append(
            f"Sheet count mismatch. Expected {len(example.sheet_names)}, got {len(target.sheet_names)}."
        )
    if target.selected_sheet != example.selected_sheet:
        failures.append(
            f'Sheet name mismatch. Expected "{example.selected_sheet}", got "{target.selected_sheet}".'
        )

    for idx in range(1, 8):
        exp_width = example.widths.get(idx)
        act_width = target.widths.get(idx)
        if exp_width is None or act_width is None:
            failures.append(f"Missing column width for {_index_to_col(idx)}.")
            continue
        if abs(exp_width - act_width) > tolerance:
            failures.append(
                f"Column width mismatch for {_index_to_col(idx)}. Expected {exp_width:.2f}, got {act_width:.2f}."
            )

    example_section_rows: Dict[str, int] = {}
    target_section_rows: Dict[str, int] = {}
    for title in SECTION_TITLES:
        exp_row = require_single_row(example, title, failures)
        act_row = require_single_row(target, title, failures)
        if exp_row is not None:
            example_section_rows[title] = exp_row
        if act_row is not None:
            target_section_rows[title] = act_row

    if list(example_section_rows) == SECTION_TITLES and list(target_section_rows) == SECTION_TITLES:
        example_order = [example_section_rows[title] for title in SECTION_TITLES]
        target_order = [target_section_rows[title] for title in SECTION_TITLES]
        if example_order != sorted(example_order):
            failures.append("Regression example section order is invalid.")
        if target_order != sorted(target_order):
            failures.append("Target workbook section order is invalid.")

    row_pairs = [
        ("API title", example_section_rows.get("API  Name"), target_section_rows.get("API  Name")),
        ("Request header", (example_section_rows.get("Request") or 0) + 1, (target_section_rows.get("Request") or 0) + 1),
        ("Response header", (example_section_rows.get("Response") or 0) + 1, (target_section_rows.get("Response") or 0) + 1),
        ("Scenario header", (example_section_rows.get("範例") or 0) + 1, (target_section_rows.get("範例") or 0) + 1),
        ("API logic header", (example_section_rows.get("API 內部業務邏輯") or 0) + 1, (target_section_rows.get("API 內部業務邏輯") or 0) + 1),
    ]
    for label, exp_row, act_row in row_pairs:
        if not exp_row or not act_row:
            continue
        compare_row_values(label, row_values(example, exp_row), row_values(target, act_row), failures)

    expected_scenarios = collect_scenario_labels(example, failures)
    actual_scenarios = collect_scenario_labels(target, failures)
    if expected_scenarios and actual_scenarios and expected_scenarios != actual_scenarios:
        failures.append(
            f"Scenario labels mismatch. Expected {expected_scenarios!r}, got {actual_scenarios!r}."
        )

    example_scenario_header = example_section_rows.get("範例", 0) + 1
    target_scenario_header = target_section_rows.get("範例", 0) + 1
    if example_scenario_header > 1 and target_scenario_header > 1:
        compare_row_spans(
            "Scenario header",
            row_spans(example, example_scenario_header),
            row_spans(target, target_scenario_header),
            failures,
        )

    if expected_scenarios and actual_scenarios:
        exp_first_scenario_row = example_scenario_header + 1
        expected_scenario_spans = row_spans(example, exp_first_scenario_row)
        for offset, label in enumerate(actual_scenarios, start=1):
            actual_row = target_scenario_header + offset
            compare_row_spans(
                f'Scenario row "{label}"',
                expected_scenario_spans,
                row_spans(target, actual_row),
                failures,
            )

    exp_middle_row = example_section_rows.get("For中台開發人員")
    act_middle_row = target_section_rows.get("For中台開發人員")
    if exp_middle_row and act_middle_row:
        compare_row_spans(
            "For中台開發人員",
            row_spans(example, exp_middle_row),
            row_spans(target, act_middle_row),
            failures,
        )

    exp_logic_anchor = example_section_rows.get("API 內部業務邏輯")
    act_logic_anchor = target_section_rows.get("API 內部業務邏輯")
    if exp_logic_anchor and act_logic_anchor:
        expected_logic_spans = row_spans(example, exp_logic_anchor + 1)
        logic_end = target.max_row + 1
        for row in range(act_logic_anchor + 1, logic_end):
            label = cell_value(target, row, 1)
            if not label:
                continue
            compare_row_spans(
                f'API logic row "{label}"',
                expected_logic_spans,
                row_spans(target, row),
                failures,
            )

    return failures


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate generated workbook against Regression_Example.xlsx.")
    parser.add_argument("--xlsx", required=True, help="Generated workbook to validate.")
    parser.add_argument(
        "--example",
        default=str(Path(__file__).resolve().parents[1] / "references" / "raw" / "Regression_Example.xlsx"),
        help="Regression example workbook path.",
    )
    parser.add_argument("--sheet-name", default="API_Detail", help="Sheet name to validate.")
    parser.add_argument("--width-tolerance", type=float, default=0.25, help="Allowed A:G column width delta.")
    args = parser.parse_args()

    xlsx = Path(args.xlsx)
    example = Path(args.example)
    if not xlsx.exists():
        print(f"Target workbook not found: {xlsx}", file=sys.stderr)
        return 2
    if not example.exists():
        print(f"Regression example workbook not found: {example}", file=sys.stderr)
        return 2

    try:
        example_model = load_sheet_model(example, args.sheet_name)
        target_model = load_sheet_model(xlsx, args.sheet_name)
    except Exception as exc:  # noqa: BLE001
        print(f"Failed to load workbook: {exc}", file=sys.stderr)
        return 2

    failures = validate(example_model, target_model, args.width_tolerance)
    if failures:
        print("REGRESSION_CHECK=FAILED")
        for item in failures:
            print(f"- {item}")
        return 1

    print("REGRESSION_CHECK=PASSED")
    print(f"TARGET={xlsx}")
    print(f"EXAMPLE={example}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
