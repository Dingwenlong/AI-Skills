#!/usr/bin/env python3
"""Send change records to a WeCom WeDoc smartsheet webhook."""

from __future__ import annotations

import argparse
import json
import sys
import urllib.error
import urllib.request
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Any

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")


SCHEMA = {
    "fwsRq0": "備註",
    "fbPZt1": "調整內容",
    "fm3WC4": "調整日期",
    "fa80iy": "調整人(人员)",
    "fPWtj7": "所屬類型",
    "faSRWW": "調整接口",
}


def date_to_ms(value: str | None) -> str:
    if not value:
        dt = datetime.now(timezone(timedelta(hours=8)))
    else:
        normalized = value.replace("-", "/")
        parts = [int(x) for x in normalized.split("/")]
        if len(parts) != 3:
            raise ValueError(f"Unsupported date: {value}")
        dt = datetime(parts[0], parts[1], parts[2], tzinfo=timezone(timedelta(hours=8)))
    start = datetime(dt.year, dt.month, dt.day, tzinfo=timezone(timedelta(hours=8)))
    return str(int(start.timestamp() * 1000))


def person_value(user_id: str | None, user_text: str | None) -> list[Any]:
    if user_id:
        return [{"user_id": user_id}]
    if user_text:
        return [user_text]
    return [{"user_id": ""}]


def normalize_record(raw: dict[str, Any]) -> dict[str, str]:
    return {
        "note": str(raw.get("note") or raw.get("備註") or ""),
        "content": str(raw.get("content") or raw.get("調整內容") or ""),
        "type": str(raw.get("type") or raw.get("所屬類型") or ""),
        "api": str(raw.get("api") or raw.get("調整接口") or ""),
    }


def build_add_payload(records: list[dict[str, Any]], date_ms: str, person: list[Any]) -> dict[str, Any]:
    return {
        "schema": SCHEMA,
        "add_records": [
            {
                "values": {
                    "fwsRq0": r["note"],
                    "fbPZt1": r["content"],
                    "fm3WC4": date_ms,
                    "fa80iy": person,
                    "fPWtj7": r["type"],
                    "faSRWW": r["api"],
                }
            }
            for r in (normalize_record(x) for x in records)
        ],
    }


def build_update_user_payload(record_ids: list[str], person: list[Any]) -> dict[str, Any]:
    return {
        "schema": SCHEMA,
        "update_records": [
            {"record_id": rid, "values": {"fa80iy": person}}
            for rid in record_ids
            if rid
        ],
    }


def post_json(webhook: str, payload: dict[str, Any]) -> dict[str, Any]:
    body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    req = urllib.request.Request(
        webhook,
        data=body,
        headers={"Content-Type": "application/json; charset=utf-8"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            data = resp.read().decode("utf-8")
    except urllib.error.HTTPError as exc:
        data = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"HTTP {exc.code}: {data}") from exc
    return json.loads(data)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--webhook", required=True)
    parser.add_argument("--excel", help="Optional source workbook used as evidence for list style.")
    parser.add_argument("--records-json", help="JSON array with note/content/type/api records.")
    parser.add_argument("--date")
    parser.add_argument("--user-id")
    parser.add_argument("--user-text")
    parser.add_argument("--update-user-record-ids", help="Comma-separated record ids to update fa80iy only.")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    if args.excel and not Path(args.excel).exists():
        raise FileNotFoundError(args.excel)

    person = person_value(args.user_id, args.user_text)
    if args.update_user_record_ids:
        ids = [x.strip() for x in args.update_user_record_ids.split(",")]
        payload = build_update_user_payload(ids, person)
    else:
        if not args.records_json:
            raise ValueError("--records-json is required when adding records")
        records = json.loads(Path(args.records_json).read_text(encoding="utf-8-sig"))
        payload = build_add_payload(records, date_to_ms(args.date), person)

    print(json.dumps(payload, ensure_ascii=False, indent=2))
    if args.dry_run:
        return 0
    response = post_json(args.webhook, payload)
    print(json.dumps(response, ensure_ascii=False, indent=2))
    return 0 if response.get("errcode") == 0 else 2


if __name__ == "__main__":
    raise SystemExit(main())
