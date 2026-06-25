#!/usr/bin/env python3
"""Record visual, semantic, or export issues discovered while using the skill."""

from __future__ import annotations

import argparse
import json
import shutil
from datetime import datetime
from pathlib import Path


SKILL_ROOT = Path(__file__).resolve().parents[1]
LOG_DIR = SKILL_ROOT / "logs"
SCREENSHOT_DIR = LOG_DIR / "screenshots"
JSONL_PATH = LOG_DIR / "issues.jsonl"
MD_PATH = LOG_DIR / "issues.md"


def now_stamp() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def safe_name(text: str) -> str:
    keep = []
    for ch in text.lower().replace(" ", "-"):
        if ch.isalnum() or ch in "-_":
            keep.append(ch)
    return "".join(keep).strip("-")[:80] or "issue"


def copy_screenshots(paths: list[str], issue_slug: str) -> list[str]:
    copied = []
    SCREENSHOT_DIR.mkdir(parents=True, exist_ok=True)
    for idx, raw in enumerate(paths, start=1):
        src = Path(raw).expanduser()
        if not src.exists():
            copied.append(f"missing:{raw}")
            continue
        dest = SCREENSHOT_DIR / f"{issue_slug}-{idx}{src.suffix}"
        shutil.copy2(src, dest)
        copied.append(str(dest.relative_to(SKILL_ROOT)))
    return copied


def main() -> int:
    parser = argparse.ArgumentParser(description="Append a diagram-rendering issue report.")
    parser.add_argument("--title", required=True, help="Short issue title.")
    parser.add_argument("--description", required=True, help="Observed issue description.")
    parser.add_argument("--chart", default="", help="Chart id/name, if known.")
    parser.add_argument("--source", default="", help="Source file or context, if known.")
    parser.add_argument("--status", default="open", choices=["open", "investigating", "fixed", "wontfix"])
    parser.add_argument("--screenshot", action="append", default=[], help="Screenshot path; may repeat.")
    args = parser.parse_args()

    LOG_DIR.mkdir(parents=True, exist_ok=True)
    slug = f"{datetime.now().strftime('%Y%m%d-%H%M%S')}-{safe_name(args.title)}"
    screenshots = copy_screenshots(args.screenshot, slug)

    record = {
        "id": slug,
        "time": now_stamp(),
        "title": args.title,
        "chart": args.chart,
        "source": args.source,
        "status": args.status,
        "description": args.description,
        "screenshots": screenshots,
    }

    with JSONL_PATH.open("a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")

    if not MD_PATH.exists():
        MD_PATH.write_text("# Human Factors Diagram Renderer Issue Log\n\n", encoding="utf-8")
    with MD_PATH.open("a", encoding="utf-8") as f:
        f.write(f"## {record['id']} - {args.title}\n\n")
        f.write(f"- Time: {record['time']}\n")
        f.write(f"- Chart: {args.chart or 'unknown'}\n")
        f.write(f"- Source: {args.source or 'unknown'}\n")
        f.write(f"- Status: {args.status}\n")
        f.write(f"- Description: {args.description}\n")
        if screenshots:
            f.write(f"- Screenshots: {', '.join(screenshots)}\n")
        f.write("\n")

    print(f"Logged issue: {record['id']}")
    print(f"Markdown: {MD_PATH}")
    print(f"JSONL: {JSONL_PATH}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
