#!/usr/bin/env python3
"""Fetch and summarize public LibTV project template detail data."""

from __future__ import annotations

import argparse
import json
import sys
import urllib.parse
import urllib.request
from collections import Counter
from pathlib import Path


HEADERS = {
    "x-language": "zh",
    "webid": "codex-research",
    "X-Log-ID": "libtv-detail-summary",
    "User-Agent": "Mozilla/5.0",
}


def load_template_uuids(args: argparse.Namespace) -> list[str]:
    uuids: list[str] = list(args.template_uuid)
    if args.input_file:
        path = Path(args.input_file)
        text = path.read_text(encoding="utf-8").strip()
        if not text:
            return uuids
        if path.suffix.lower() == ".json":
            payload = json.loads(text)
            if isinstance(payload, list):
                uuids.extend(str(item) for item in payload)
            else:
                raise ValueError("JSON input must be an array of template UUIDs.")
        else:
            uuids.extend(line.strip() for line in text.splitlines() if line.strip())
    return list(dict.fromkeys(uuids))


def fetch_detail(template_uuid: str) -> dict:
    query = urllib.parse.urlencode({"projectTemplateUuid": template_uuid})
    url = f"https://api.liblib.tv/api/community/project/template/detail?{query}"
    request = urllib.request.Request(url, headers=HEADERS)
    with urllib.request.urlopen(request, timeout=30) as response:
        payload = json.load(response)
    return payload["data"]["detail"]


def summarize(detail: dict) -> dict:
    snapshot = json.loads(detail.get("snapshotData") or "{}")
    nodes = snapshot.get("nodes") or []
    edges = snapshot.get("edges") or []

    node_types = Counter(node.get("type", "unknown") for node in nodes)
    action_types = Counter((node.get("data") or {}).get("action", "none") for node in nodes)
    image_models = sorted(
        {
            ((node.get("data") or {}).get("params") or {}).get("model")
            for node in nodes
            if node.get("type") == "image"
            and ((node.get("data") or {}).get("params") or {}).get("model")
        }
    )
    image_mode_types = sorted(
        {
            ((node.get("data") or {}).get("params") or {}).get("modeType")
            for node in nodes
            if node.get("type") == "image"
            and ((node.get("data") or {}).get("params") or {}).get("modeType")
        }
    )

    script_rows = 0
    storyboard_groups = 0
    ref_image_links = 0
    clip_durations: list[float] = []
    final_duration = None
    final_output = detail.get("finalOutput")

    for node in nodes:
        data = node.get("data") or {}
        if node.get("type") == "group" and data.get("storyboardGroupType"):
            storyboard_groups += 1
        if node.get("type") == "script":
            script_rows += len(data.get("rows") or [])
        if node.get("type") == "image":
            ref_image_links += len(((data.get("params") or {}).get("imageList") or []))
        if node.get("type") == "video":
            for item in ((node.get("resourceMeta") or {}).get("items") or []):
                duration = item.get("durationSec")
                if not duration:
                    continue
                if final_output and final_output in (data.get("url") or []):
                    final_duration = duration
                else:
                    clip_durations.append(duration)

    id_to_type = {node.get("id"): node.get("type", "?") for node in nodes}
    edge_pairs = Counter(
        f"{id_to_type.get(edge.get('source'), '?')}->{id_to_type.get(edge.get('target'), '?')}"
        for edge in edges
    )

    return {
        "templateUuid": detail.get("templateUuid"),
        "title": detail.get("name"),
        "likeCount": detail.get("likeCount") or 0,
        "tags": [tag.get("tagLabel") for tag in detail.get("tags") or []],
        "publishAt": detail.get("publishAt"),
        "description": detail.get("description") or "",
        "totalNodes": len(nodes),
        "totalEdges": len(edges),
        "typeCounts": dict(node_types),
        "actionCounts": dict(action_types),
        "storyboardGroups": storyboard_groups,
        "scriptRows": script_rows,
        "imageModels": image_models,
        "imageModeTypes": image_mode_types,
        "refImageLinks": ref_image_links,
        "clipCount": len(clip_durations),
        "avgClipDurationSec": round(sum(clip_durations) / len(clip_durations), 2)
        if clip_durations
        else None,
        "finalDurationSec": round(final_duration, 2) if final_duration else None,
        "topEdgePairs": edge_pairs.most_common(6),
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Fetch public LibTV template detail and summarize canvas structure."
    )
    parser.add_argument("template_uuid", nargs="*", help="Public LibTV project template UUIDs.")
    parser.add_argument(
        "--input-file",
        help="Optional text file or JSON array containing template UUIDs.",
    )
    parser.add_argument(
        "--json-out",
        help="Write the summaries to this JSON file.",
    )
    parser.add_argument(
        "--text",
        action="store_true",
        help="Print a short human-readable summary instead of raw JSON.",
    )
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    uuids = load_template_uuids(args)
    if not uuids:
        parser.error("Provide at least one template UUID or --input-file.")

    summaries = []
    for template_uuid in uuids:
        try:
            summaries.append(summarize(fetch_detail(template_uuid)))
        except Exception as exc:  # pragma: no cover - network failure path
            summaries.append(
                {
                    "templateUuid": template_uuid,
                    "error": str(exc),
                }
            )

    if args.json_out:
        out_path = Path(args.json_out)
        out_path.write_text(json.dumps(summaries, ensure_ascii=False, indent=2), encoding="utf-8")

    if args.text:
        for item in summaries:
            if "error" in item:
                print(f"{item['templateUuid']}: ERROR {item['error']}")
                continue
            print(
                f"{item['title']} | likes={item['likeCount']} | "
                f"nodes={item['totalNodes']} | scripts={item['scriptRows']} rows | "
                f"clips={item['clipCount']} | models={','.join(item['imageModels']) or '-'}"
            )
    else:
        print(json.dumps(summaries, ensure_ascii=False, indent=2))

    return 0


if __name__ == "__main__":
    sys.exit(main())
