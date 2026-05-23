# -*- coding: utf-8 -*-
"""整理中文电子发票 PDF：重命名，或按目标金额汇集。"""

from __future__ import annotations

import argparse
import re
import shutil
import sys
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from pathlib import Path
from typing import Iterable


REPORT_NAME = "发票整理_人工处理报告.md"


def configure_output() -> None:
    for stream_name in ("stdout", "stderr"):
        stream = getattr(sys, stream_name, None)
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8", errors="replace")


def cents_to_text(cents: int) -> str:
    return f"{Decimal(cents) / Decimal(100):.2f}"


def amount_to_cents(value: str) -> int | None:
    cleaned = value.replace(",", "").replace("￥", "").replace("¥", "").strip()
    try:
        amount = Decimal(cleaned).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    except (InvalidOperation, ValueError):
        return None
    if amount < 0:
        return None
    return int(amount * 100)


def extract_text(path: Path) -> str:
    try:
        import pdfplumber  # type: ignore

        with pdfplumber.open(path) as pdf:
            return "\n".join((page.extract_text() or "") for page in pdf.pages)
    except Exception:
        pass

    try:
        import fitz  # type: ignore

        with fitz.open(path) as doc:
            return "\n".join(page.get_text("text") for page in doc)
    except Exception:
        return ""


def parse_amount_from_filename(path: Path) -> int | None:
    name = path.stem
    patterns = [
        r"^([0-9]+(?:\.[0-9]{1,2})?)_发票_\d{8}$",
        r"(?<![\d.])([0-9]+(?:\.[0-9]{1,2})?)\s*元",
        r"[￥¥]\s*([0-9]+(?:\.[0-9]{1,2})?)",
    ]
    for pattern in patterns:
        matches = re.findall(pattern, name)
        if matches:
            return amount_to_cents(matches[-1])
    return None


def parse_amount_from_text(text: str) -> int | None:
    compact = re.sub(r"\s+", "", text)
    patterns = [
        r"价税合计.*?[￥¥]?([0-9]+(?:\.[0-9]{1,2})?)",
        r"小写.*?[￥¥]?([0-9]+(?:\.[0-9]{1,2})?)",
        r"合计.*?[￥¥]?([0-9]+(?:\.[0-9]{1,2})?)",
        r"([0-9]+(?:\.[0-9]{1,2})?)元",
    ]
    for pattern in patterns:
        matches = re.findall(pattern, compact)
        for value in reversed(matches):
            cents = amount_to_cents(value)
            if cents is not None:
                return cents
    return None


def normalize_date(year: str, month: str, day: str) -> str | None:
    y, m, d = int(year), int(month), int(day)
    if not (1 <= m <= 12 and 1 <= d <= 31):
        return None
    return f"{y:04d}{m:02d}{d:02d}"


def parse_invoice_date(text: str) -> str | None:
    compact = re.sub(r"\s+", "", text)
    candidates = [
        r"开票日期[:：]?([0-9]{4})年([0-9]{1,2})月([0-9]{1,2})日",
        r"开票日期[:：]?([0-9]{4})[-/.]([0-9]{1,2})[-/.]([0-9]{1,2})",
        r"开票日期[:：]?([0-9]{4})([0-9]{2})([0-9]{2})",
    ]
    for pattern in candidates:
        match = re.search(pattern, compact)
        if match:
            return normalize_date(*match.groups())
    return None


@dataclass(frozen=True)
class Invoice:
    path: Path
    amount_cents: int | None
    invoice_date: str | None
    reasons: tuple[str, ...]

    @property
    def stable_name(self) -> str:
        return self.path.name.casefold()


def scan_current_dir(cwd: Path) -> list[Invoice]:
    invoices: list[Invoice] = []
    for path in sorted(cwd.iterdir(), key=lambda item: item.name.casefold()):
        if not path.is_file() or path.suffix.casefold() != ".pdf":
            continue
        text = extract_text(path)
        amount = parse_amount_from_filename(path)
        if amount is None:
            amount = parse_amount_from_text(text)
        invoice_date = parse_invoice_date(text)

        reasons: list[str] = []
        if amount is None:
            reasons.append("未读取到金额")
        if invoice_date is None:
            reasons.append("未读取到开票日期")
        invoices.append(Invoice(path, amount, invoice_date, tuple(reasons)))
    return invoices


def ensure_backup(path: Path) -> None:
    backup_dir = path.parent / "backup"
    backup_dir.mkdir(exist_ok=True)
    backup_path = backup_dir / f"{path.name}.bak"
    shutil.copy2(path, backup_path)


def unique_destination(path: Path) -> Path:
    if not path.exists():
        return path
    index = 2
    while True:
        candidate = path.with_name(f"{path.stem}_{index}{path.suffix}")
        if not candidate.exists():
            return candidate
        index += 1


def write_manual_report(cwd: Path, invoices: Iterable[Invoice]) -> Path | None:
    manual = [invoice for invoice in invoices if invoice.reasons]
    if not manual:
        return None

    report_path = cwd / REPORT_NAME
    if report_path.exists():
        ensure_backup(report_path)

    lines = [
        "# 发票整理人工处理报告",
        "",
        "| 文件名 | 原因 | 建议 |",
        "| --- | --- | --- |",
    ]
    for invoice in manual:
        reason_text = "、".join(invoice.reasons)
        lines.append(f"| {invoice.path.name} | {reason_text} | 人工补充金额或开票日期后重新执行 |")
    report_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return report_path


def command_rename(cwd: Path) -> int:
    invoices = scan_current_dir(cwd)
    changed = 0
    skipped = 0
    for invoice in invoices:
        if invoice.reasons:
            skipped += 1
            continue
        assert invoice.amount_cents is not None
        assert invoice.invoice_date is not None
        wanted_name = f"{cents_to_text(invoice.amount_cents)}_发票_{invoice.invoice_date}.pdf"
        wanted_path = invoice.path.with_name(wanted_name)
        if invoice.path.resolve() == wanted_path.resolve():
            continue
        destination = unique_destination(wanted_path)
        ensure_backup(invoice.path)
        invoice.path.rename(destination)
        changed += 1

    report = write_manual_report(cwd, invoices)
    print(f"已扫描 PDF：{len(invoices)}")
    print(f"已重命名：{changed}")
    print(f"需人工处理：{skipped}")
    if report:
        print(f"人工处理报告：{report.name}")
    return 0


def better_same_sum(left: tuple[str, ...], right: tuple[str, ...]) -> tuple[str, ...]:
    if len(left) != len(right):
        return left if len(left) < len(right) else right
    return min(left, right)


def select_subset(invoices: list[Invoice], target_cents: int) -> tuple[int, tuple[str, ...]]:
    usable = [invoice for invoice in invoices if invoice.amount_cents is not None]
    usable.sort(key=lambda invoice: invoice.stable_name)
    amounts = {invoice.path.name: invoice.amount_cents for invoice in usable}
    dp: dict[int, tuple[str, ...]] = {0: tuple()}
    for invoice in usable:
        assert invoice.amount_cents is not None
        additions: dict[int, tuple[str, ...]] = {}
        for total, names in dp.items():
            new_total = total + invoice.amount_cents
            new_names = tuple(sorted((*names, invoice.path.name), key=str.casefold))
            current = dp.get(new_total) or additions.get(new_total)
            additions[new_total] = new_names if current is None else better_same_sum(new_names, current)
        for total, names in additions.items():
            current = dp.get(total)
            dp[total] = names if current is None else better_same_sum(names, current)

    def rank(item: tuple[int, tuple[str, ...]]) -> tuple[int, int, int, tuple[str, ...]]:
        total, names = item
        over_flag = 0 if total >= target_cents else 1
        return (abs(total - target_cents), over_flag, len(names), names)

    best_total, best_names = min(
        ((total, names) for total, names in dp.items() if names),
        key=rank,
    )
    _ = amounts
    return best_total, best_names


def command_collect(cwd: Path, target: str) -> int:
    target_cents = amount_to_cents(target)
    if target_cents is None:
        raise SystemExit(f"目标金额格式不正确：{target}")

    invoices = scan_current_dir(cwd)
    usable = [invoice for invoice in invoices if invoice.amount_cents is not None]
    if not usable:
        write_manual_report(cwd, invoices)
        raise SystemExit("没有可用于凑票的 PDF。")

    selected_total, selected_names = select_subset(invoices, target_cents)
    selected = {name.casefold() for name in selected_names}
    target_dir = cwd / f"金额_{cents_to_text(target_cents)}"
    target_dir.mkdir(exist_ok=True)

    moved = 0
    for invoice in sorted(usable, key=lambda item: item.stable_name):
        if invoice.path.name.casefold() not in selected:
            continue
        ensure_backup(invoice.path)
        destination = unique_destination(target_dir / invoice.path.name)
        shutil.move(str(invoice.path), str(destination))
        moved += 1

    report = write_manual_report(cwd, invoices)
    diff = selected_total - target_cents
    print(f"目标金额：{cents_to_text(target_cents)}")
    print(f"选中合计：{cents_to_text(selected_total)}")
    print(f"差额：{Decimal(diff) / Decimal(100):+.2f}")
    print(f"移动文件数：{moved}")
    print(f"目标文件夹：{target_dir.name}")
    if report:
        print(f"人工处理报告：{report.name}")
    return 0


def main() -> int:
    configure_output()
    parser = argparse.ArgumentParser(description="整理中文电子发票 PDF")
    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser("rename", help="整理当前文件夹发票名称")
    collect = subparsers.add_parser("collect", help="按目标金额汇集发票")
    collect.add_argument("--target", required=True, help="目标金额，例如 271.45")

    args = parser.parse_args()
    cwd = Path.cwd()
    if args.command == "rename":
        return command_rename(cwd)
    if args.command == "collect":
        return command_collect(cwd, args.target)
    raise SystemExit(f"未知命令：{args.command}")


if __name__ == "__main__":
    raise SystemExit(main())
