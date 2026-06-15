#!/usr/bin/env python3
"""Export directory markdown into the website's JSON payload.

Canonical source of truth:
- acadie_sol_directory/inbox/*.md for draft previews
- acadie_sol_directory/entries/*/entry.md + meta.json for official entries

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
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable


DEFAULT_DIRECTORY_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SITE_ROOT = DEFAULT_DIRECTORY_ROOT.with_name("acadie_sol")
CONTACT_KEYS = {"address", "hours", "phone", "email", "website"}
SCHEMA_VERSION = 1


def clean_text(value: str) -> str:
    return re.sub(r"\s+", " ", str(value or "")).strip()


def parse_tags(value: str | list[str] | None) -> list[str]:
    if not value:
        return []
    if isinstance(value, list):
        raw = value
    else:
        raw = re.split(r"[|,]", value)
    tags: list[str] = []
    seen: set[str] = set()
    for tag in raw:
        cleaned = clean_text(str(tag)).strip("# ")
        key = cleaned.casefold()
        if cleaned and key not in seen:
            tags.append(cleaned)
            seen.add(key)
    return tags


def public_area(area: str, meta: dict | None = None) -> str:
    if meta:
        location = meta.get("location") or {}
        explicit = clean_text(location.get("public_area", ""))
        if explicit:
            return explicit
        municipality = clean_text(location.get("municipality", ""))
        if municipality:
            area = municipality
    area = clean_text(area)
    if re.search(r"bathurst", area, re.I):
        return "Acadie-Bathurst"
    return area or "Unsorted"


def timestamp_for(path: Path) -> tuple[str, int]:
    stat = path.stat()
    modified_ts = int(stat.st_mtime)
    modified_at = datetime.fromtimestamp(stat.st_mtime, tz=timezone.utc).isoformat().replace("+00:00", "Z")
    return modified_at, modified_ts


def display_path(path: Path) -> str:
    try:
        return str(path.relative_to(DEFAULT_DIRECTORY_ROOT))
    except ValueError:
        for marker in ("inbox", "entries"):
            if marker in path.parts:
                idx = path.parts.index(marker)
                return str(Path(*path.parts[idx:]))
        return str(path)


def markdown_sections(lines: list[str]) -> dict[str, list[str]]:
    sections: dict[str, list[str]] = {"preamble": []}
    current = "preamble"
    for line in lines:
        stripped = line.strip()
        if stripped.startswith("## "):
            current = stripped[3:].strip().casefold()
            sections.setdefault(current, [])
            continue
        sections.setdefault(current, []).append(line)
    return sections


def bullet_values(lines: list[str]) -> list[str]:
    return [line.strip()[2:].strip() for line in lines if line.strip().startswith("- ") and line.strip()[2:].strip()]


def parse_contact_lines(lines: list[str]) -> tuple[dict[str, str], list[str]]:
    contact = {key: "" for key in CONTACT_KEYS}
    public_data: list[str] = []
    for line in lines:
        stripped = line.strip()
        if not stripped.startswith("- "):
            continue
        value = stripped[2:].strip()
        if not value or value.startswith("["):
            continue
        public_data.append(value)
        if ":" not in value:
            continue
        key, val = value.split(":", 1)
        key_norm = key.strip().lower()
        if key_norm in contact:
            contact[key_norm] = clean_text(val)
    return contact, public_data


def first_heading(markdown: str, fallback: str) -> str:
    for line in markdown.splitlines():
        stripped = line.strip()
        if stripped.startswith("# "):
            return re.sub(r"^#\s*Draft:\s*", "", stripped[2:].strip()).strip()
    return fallback


def source_type(path: Path, draft: bool, sources: list[str]) -> str:
    if draft:
        return "inbox"
    if any(src.casefold() == "in person" for src in sources):
        return "in-person"
    if sources:
        return "public-source"
    return "entry"


def build_item(
    *,
    path: Path,
    title: str,
    status: str,
    category: str = "",
    area: str = "",
    tags: list[str] | None = None,
    description: str = "",
    notes: str = "",
    note_points: list[str] | None = None,
    contact: dict[str, str] | None = None,
    public_data: list[str] | None = None,
    related_places: list[str] | None = None,
    sources: list[str] | None = None,
    meta: dict | None = None,
) -> dict:
    draft = status == "draft"
    contact = {**{key: "" for key in CONTACT_KEYS}, **(contact or {})}
    tags = tags or []
    note_points = note_points or []
    related_places = related_places or []
    sources = sources or []
    public_data = public_data or []
    modified_at, modified_ts = timestamp_for(path)
    summary = clean_text(" ".join(part for part in [description, notes] if part))[:220]
    area_value = area or clean_text((meta or {}).get("location", {}).get("municipality", ""))
    public_area_value = public_area(area_value, meta)
    name = clean_text((meta or {}).get("name", "")) or title

    return {
        "title": name,
        "name": name,
        "sort_name": clean_text((meta or {}).get("sort_name", "")) or name,
        "brand_name": clean_text((meta or {}).get("brand_name", "")),
        "branch_name": clean_text((meta or {}).get("branch_name", "")),
        "aliases": (meta or {}).get("aliases", []) if isinstance((meta or {}).get("aliases", []), list) else [],
        "slug": clean_text((meta or {}).get("slug", "")) or (path.stem if path.name != "entry.md" else path.parent.name),
        "status": status,
        "draft": draft,
        "badge": "DRAFT" if draft else "",
        "category": category,
        "area": area_value,
        "public_area": public_area_value,
        "description": description,
        "notes": notes,
        "note_points": note_points,
        "summary": summary,
        "tags": tags,
        "contact": contact,
        # Backwards-compatible flat fields for the current static renderer.
        "address": contact["address"],
        "hours": contact["hours"],
        "phone": contact["phone"],
        "email": contact["email"],
        "website": contact["website"],
        "public_data": public_data,
        "related_places": related_places,
        "sources": sources,
        "source_type": source_type(path, draft, sources),
        "path": display_path(path),
        "source_modified_at": modified_at,
        "source_modified_ts": modified_ts,
    }


def parse_draft(path: Path) -> dict:
    text = path.read_text(encoding="utf-8")
    lines = text.splitlines()
    title_line = lines[0].strip() if lines else "# Draft: Untitled"
    title = re.sub(r"^#\s*Draft:\s*", "", title_line.lstrip("# ")).strip()
    category = ""
    area = ""
    tags: list[str] = []
    body: list[str] = []

    for line in lines[1:]:
        if line.startswith("Category:"):
            category = clean_text(line.split(":", 1)[1])
            continue
        if line.startswith("Area:"):
            area = clean_text(line.split(":", 1)[1])
            continue
        if line.startswith("Tags:"):
            tags = parse_tags(line.split(":", 1)[1])
            continue
        body.append(line)

    sections = markdown_sections(body)
    description = clean_text(" ".join(sections.get("description", [])))
    note_lines = sections.get("notes", [])
    notes = clean_text(" ".join(note_lines))
    note_points = bullet_values(note_lines)
    contact_lines = sections.get("public data to carry forward", []) or sections.get("public data", []) or sections.get("details", []) or sections.get("contact", [])
    contact, public_data = parse_contact_lines(contact_lines)
    sources = bullet_values(sections.get("public source", []) or sections.get("details and sources", []) or sections.get("sources", []))
    related_places = bullet_values(sections.get("related places", []))

    return build_item(
        path=path,
        title=title,
        status="draft",
        category=category,
        area=area,
        tags=tags,
        description=description,
        notes=notes,
        note_points=note_points,
        contact=contact,
        public_data=public_data,
        related_places=related_places,
        sources=sources,
    )


def parse_entry(entry_md: Path) -> dict:
    entry_dir = entry_md.parent
    meta_path = entry_dir / "meta.json"
    meta = json.loads(meta_path.read_text(encoding="utf-8")) if meta_path.exists() else {}
    text = entry_md.read_text(encoding="utf-8")
    lines = text.splitlines()
    title = first_heading(text, entry_dir.name.replace("-", " ").title())
    sections = markdown_sections(lines[1:] if lines else [])

    description = clean_text(meta.get("short_description", ""))
    if not description:
        # First non-empty preamble line becomes description.
        description = clean_text(" ".join(line for line in sections.get("preamble", []) if line.strip()))
    note_lines = sections.get("public notes", []) or sections.get("notes", [])
    notes = clean_text(" ".join(note_lines))
    note_points = bullet_values(note_lines)

    raw_contact = meta.get("contact")
    meta_contact: dict = raw_contact if isinstance(raw_contact, dict) else {}
    contact_lines = sections.get("contact", [])
    contact, public_data = parse_contact_lines(contact_lines)
    contact.update({key: clean_text(meta_contact.get(key, contact[key])) for key in CONTACT_KEYS})

    sources = bullet_values(sections.get("sources", []) or sections.get("public source", []))
    related_lines = bullet_values(sections.get("related places", []))
    related_meta = meta.get("related", []) if isinstance(meta.get("related", []), list) else []
    related_places = related_lines + [clean_text(item.get("slug", "")) for item in related_meta if isinstance(item, dict) and item.get("slug")]
    raw_location = meta.get("location")
    location: dict = raw_location if isinstance(raw_location, dict) else {}

    return build_item(
        path=entry_md,
        title=title,
        status=clean_text(meta.get("status", "published")) or "published",
        category=clean_text(meta.get("category", "")),
        area=clean_text(location.get("public_area") or location.get("municipality") or ""),
        tags=parse_tags(meta.get("tags")),
        description=description,
        notes=notes,
        note_points=note_points,
        contact=contact,
        public_data=public_data,
        related_places=[item for item in related_places if item],
        sources=sources,
        meta=meta,
    )


def collect_drafts(directory_root: Path) -> list[Path]:
    inbox = directory_root / "inbox"
    if not inbox.exists():
        return []
    sources = []
    for path in sorted(inbox.glob("*.md")):
        name = path.name.lower()
        if name.startswith("_") or "template" in name:
            continue
        sources.append(path)
    return sources


def collect_entries(directory_root: Path) -> list[Path]:
    entries = directory_root / "entries"
    if not entries.exists():
        return []
    sources = []
    for path in sorted(entries.glob("*/entry.md")):
        if any(part.startswith("_") for part in path.relative_to(entries).parts):
            continue
        sources.append(path)
    return sources


def build_payload(directory_root: Path) -> dict:
    items = [parse_entry(path) for path in collect_entries(directory_root)]
    items.extend(parse_draft(path) for path in collect_drafts(directory_root))
    items.sort(key=lambda item: (0 if item["status"] == "published" else 1, item["title"].lower()))

    return {
        "schema_version": SCHEMA_VERSION,
        "generated_from": str(directory_root),
        "entry_count": len(items),
        "draft_count": sum(1 for item in items if item["draft"]),
        "published_count": sum(1 for item in items if item["status"] == "published"),
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
