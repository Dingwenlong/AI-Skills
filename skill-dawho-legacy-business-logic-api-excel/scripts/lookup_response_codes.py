#!/usr/bin/env python3
"""
Lookup response codes from Api_Response_Codes workbook without external deps.

Usage:
  python lookup_response_codes.py --module-sheet E_Exchange --codes 0000 9997 9998 9999
  python lookup_response_codes.py --xlsx "<path>" --module-sheet E_Exchange --codes 0000 9997 9998 9999
  python lookup_response_codes.py --xlsx-dir "../references/raw" --module-sheet E_Exchange --codes 0000 9997 9998 9999

Output format (TSV):
  ResponseCode<TAB>ResponseMessage<TAB>SourceSheet
"""

from __future__ import annotations

import argparse
import re
import sys
import zipfile
from pathlib import Path
from typing import Dict, List, Tuple
import xml.etree.ElementTree as ET

NS = {
    "main": "http://schemas.openxmlformats.org/spreadsheetml/2006/main",
    "pkg": "http://schemas.openxmlformats.org/package/2006/relationships",
    "r": "http://schemas.openxmlformats.org/officeDocument/2006/relationships",
}


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
    v = cell.find("main:v", NS)
    if ctype == "s" and v is not None:
        idx = int(v.text or "0")
        return shared[idx] if 0 <= idx < len(shared) else ""
    if ctype == "inlineStr":
        t = cell.find(".//main:t", NS)
        return (t.text or "") if t is not None else ""
    if v is not None:
        return v.text or ""
    return ""


def _sheet_path(zf: zipfile.ZipFile, sheet_name: str) -> str:
    wb = ET.fromstring(zf.read("xl/workbook.xml"))
    rels = ET.fromstring(zf.read("xl/_rels/workbook.xml.rels"))
    rel_map = {r.attrib["Id"]: r.attrib["Target"] for r in rels.findall("pkg:Relationship", NS)}

    for s in wb.findall("main:sheets/main:sheet", NS):
        if s.attrib.get("name") == sheet_name:
            rid = s.attrib.get(f"{{{NS['r']}}}id")
            if not rid or rid not in rel_map:
                raise ValueError(f"Missing relationship for sheet: {sheet_name}")
            target = rel_map[rid]
            if not target.startswith("worksheets/"):
                target = "worksheets/" + target.split("/")[-1]
            return "xl/" + target
    raise ValueError(f"Sheet not found: {sheet_name}")


def _read_code_sheet(zf: zipfile.ZipFile, sheet_name: str) -> Dict[str, str]:
    shared = _load_shared_strings(zf)
    sheet_xml = ET.fromstring(zf.read(_sheet_path(zf, sheet_name)))
    sheet_data = sheet_xml.find("main:sheetData", NS)
    if sheet_data is None:
        return {}

    by_ref: Dict[int, Dict[str, str]] = {}
    for row in sheet_data.findall("main:row", NS):
        rnum = int(row.attrib.get("r", "0"))
        row_map: Dict[str, str] = {}
        for cell in row.findall("main:c", NS):
            cref = cell.attrib.get("r", "")
            m = re.match(r"([A-Z]+)", cref)
            if not m:
                continue
            col = m.group(1)
            row_map[col] = _cell_text(cell, shared).strip()
        if row_map:
            by_ref[rnum] = row_map

    # expected structure:
    # A: ResponseCode, B: ResponseMessage (header in row 1)
    result: Dict[str, str] = {}
    for rnum in sorted(by_ref):
        if rnum == 1:
            continue
        code = by_ref[rnum].get("A", "").strip()
        msg = by_ref[rnum].get("B", "").strip()
        if code:
            result[code] = msg
    return result


def lookup_codes(xlsx_path: Path, module_sheet: str, codes: List[str]) -> List[Tuple[str, str, str]]:
    with zipfile.ZipFile(xlsx_path) as zf:
        module_map = _read_code_sheet(zf, module_sheet)
        common_map = _read_code_sheet(zf, "O_Common")

    rows: List[Tuple[str, str, str]] = []
    for code in codes:
        if code in module_map and module_map[code]:
            rows.append((code, module_map[code], module_sheet))
        elif code in common_map and common_map[code]:
            rows.append((code, common_map[code], "O_Common"))
        elif code in module_map:
            rows.append((code, "", module_sheet))
        else:
            rows.append((code, "", "NOT_FOUND"))
    return rows


def _extract_latest_date_token(path: Path) -> int:
    # Prefer filenames containing yyyymmdd date fragments.
    nums = re.findall(r"(?<!\d)(\d{8})(?!\d)", path.stem)
    valid_dates = [int(n) for n in nums if 19000101 <= int(n) <= 29991231]
    if valid_dates:
        return max(valid_dates)
    return 0


def _resolve_latest_workbook(xlsx_dir: Path, pattern: str) -> Path:
    if not xlsx_dir.exists():
        raise FileNotFoundError(f"Workbook directory not found: {xlsx_dir}")

    candidates = [p for p in xlsx_dir.glob(pattern) if p.is_file()]
    if not candidates:
        raise FileNotFoundError(f"No workbook matched pattern '{pattern}' under: {xlsx_dir}")

    # Sort by: embedded yyyymmdd desc, then modified time desc, then name desc.
    candidates.sort(
        key=lambda p: (_extract_latest_date_token(p), p.stat().st_mtime, p.name),
        reverse=True,
    )
    return candidates[0]


def main() -> int:
    parser = argparse.ArgumentParser(description="Lookup response code messages from workbook.")
    parser.add_argument("--xlsx", help="Path to Api_Response_Codes workbook. If omitted, auto-pick latest in --xlsx-dir.")
    parser.add_argument(
        "--xlsx-dir",
        default=str((Path(__file__).resolve().parents[1] / "references" / "raw")),
        help="Directory containing Api_Response_Codes workbooks for auto-pick.",
    )
    parser.add_argument(
        "--xlsx-pattern",
        default="Api_Response_Codes*.xlsx",
        help="Glob pattern used when auto-picking workbook from --xlsx-dir.",
    )
    parser.add_argument("--module-sheet", required=True, help="Module sheet, e.g. E_Exchange.")
    parser.add_argument("--codes", nargs="+", required=True, help="Codes to lookup.")
    args = parser.parse_args()

    try:
        if args.xlsx:
            xlsx = Path(args.xlsx)
        else:
            xlsx = _resolve_latest_workbook(Path(args.xlsx_dir), args.xlsx_pattern)
            print(f"Using workbook: {xlsx}", file=sys.stderr)
    except FileNotFoundError as ex:
        print(str(ex), file=sys.stderr)
        return 2

    if not xlsx.exists():
        print(f"Workbook not found: {xlsx}", file=sys.stderr)
        return 2

    rows = lookup_codes(xlsx, args.module_sheet, args.codes)
    print("ResponseCode\tResponseMessage\tSourceSheet")
    for code, message, source in rows:
        print(f"{code}\t{message}\t{source}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
