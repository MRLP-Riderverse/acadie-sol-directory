#!/usr/bin/env python3
"""Export directory markdown into the website's JSON payload.

Canonical source of truth:
- acadie_sol_directory/inbox/*.md
- acadie_sol_directory/entries/*/entry.md (future-proofed)

Output:
- acadie_sol/assets/directory-data.json

This script is intentionally local and offline. It does not commit or push.
Run it manually after editing the directory, then commit the generated JSON
in the website repo when you're ready.
"""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Iterable


DEFAULT_DIRECTORY_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SITE_ROOT = DEFAULT_DIRECTORY_ROOT.with_name("acadie_sol")


def parse_listing(path: Path) -> dict:
    text = path.read_text(encoding="utf-8")
    lines = text.splitlines()
    title_line = lines[0].strip() if lines else "# Draft: Untitled"
    title = re.sub(r"^#\s*Draft:\s*", "", title_line).strip()

    category = ""
    area = ""
    public_source: list[str] = []
    notes: list[str] = []
    current = None

    for line in lines[1:]:
        stripped = line.strip()
        if line.startswith("Category:"):
            category = line.split(":", 1)[1].strip()
            continue
        if line.startswith("Area:"):
            area = line.split(":", 1)[1].strip()
            continue
        if stripped == "## Notes":
            current = "notes"
            continue
        if stripped == "## Public source":
            current = "source"
            continue
        if stripped == "## Public data to carry forward":
            current = "public_data"
            continue
        if stripped == "## Admin notes":
            current = "admin"
            continue

        if current == "notes" and stripped:
            notes.append(stripped)
        elif current == "public_data" and stripped.startswith("- "):
            notes.append(stripped)
        elif current == "source" and stripped.startswith("- "):
            public_source.append(stripped[2:].strip())

    summary = re.sub(r"\s+", " ", " ".join(notes)).strip()
    draft = path.parent.name == "inbox" or title_line.startswith("# Draft:")

    return {
        "title": title,
        "slug": path.stem,
        "draft": draft,
        "badge": "DRAFT" if draft else "",
        "category": category,
        "area": area,
        "summary": summary[:220],
        "sources": public_source,
        "path": str(path.relative_to(DEFAULT_DIRECTORY_ROOT)),
    }


def collect_sources(directory_root: Path) -> list[Path]:
    sources: list[Path] = []

    inbox = directory_root / "inbox"
    if inbox.exists():
        sources.extend(sorted(inbox.glob("*.md")))

    entries = directory_root / "entries"
    if entries.exists():
        sources.extend(sorted(entries.glob("*/entry.md")))

    return sources


def build_payload(directory_root: Path) -> dict:
    items = [parse_listing(path) for path in collect_sources(directory_root)]
    items.sort(key=lambda item: (0 if item["draft"] else 1, item["title"].lower()))

    return {
        "generated_from": str(directory_root),
        "entry_count": len(items),
        "draft_count": sum(1 for item in items if item["draft"]),
        "published_count": sum(1 for item in items if not item["draft"]),
        "items": items,
    }


def main(argv: Iterable[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Export directory markdown into the website JSON payload.")
    parser.add_argument(
        "--directory",
        type=Path,
        default=DEFAULT_DIRECTORY_ROOT,
        help="Directory repo root (default: this repo).",
    )
    parser.add_argument(
        "--site",
        type=Path,
        default=DEFAULT_SITE_ROOT,
        help="Website repo root to write into (default: sibling 'acadie_sol').",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("assets/directory-data.json"),
        help="Relative output path inside the website repo.",
    )
    parser.add_argument(
        "--stdout",
        action="store_true",
        help="Print JSON to stdout instead of writing to the website repo.",
    )
    args = parser.parse_args(list(argv) if argv is not None else None)

    directory_root = args.directory.resolve()
    site_root = args.site.resolve()
    output_path = args.output if args.output.is_absolute() else site_root / args.output

    if not directory_root.exists():
        raise SystemExit(f"Directory repo not found: {directory_root}")
    if not (directory_root / "inbox").exists() and not (directory_root / "entries").exists():
        raise SystemExit(f"No inbox/entries content found under: {directory_root}")
    if not site_root.exists() and not args.stdout:
        raise SystemExit(f"Website repo not found: {site_root}")

    payload = build_payload(directory_root)

    if args.stdout:
        print(json.dumps(payload, indent=2, ensure_ascii=False))
        return 0

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    print(f"Wrote {output_path}")
    print(f"Entries: {payload['entry_count']}  Drafts: {payload['draft_count']}  Published: {payload['published_count']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
