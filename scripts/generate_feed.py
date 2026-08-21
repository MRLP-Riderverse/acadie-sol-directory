#!/usr/bin/env python3
"""Generate the directory RSS feed from published entry metadata.

The feed is a deterministic derivative of entries/*/meta.json. It intentionally
keeps project logs separate: logs are stewardship history, while this feed is a
public syndication surface for directory entries.
"""

from __future__ import annotations

import argparse
import json
import re
from datetime import datetime, timezone
from email.utils import format_datetime
from pathlib import Path
from xml.etree import ElementTree as ET


ROOT = Path(__file__).resolve().parents[1]
SITE_URL = "https://acadie.sol.site"
ATOM_NS = "http://www.w3.org/2005/Atom"
ET.register_namespace("atom", ATOM_NS)


def clean(value: object) -> str:
    return re.sub(r"\s+", " ", str(value or "")).strip()


def localized(value: object, language: str = "fr") -> str:
    if isinstance(value, dict):
        return clean(value.get(language) or value.get("en") or value.get("shiac"))
    return clean(value)


def parse_timestamp(value: object, fallback: float) -> datetime:
    text = clean(value)
    if text:
        try:
            return datetime.fromisoformat(text.replace("Z", "+00:00")).astimezone(timezone.utc)
        except ValueError:
            pass
    return datetime.fromtimestamp(fallback, tz=timezone.utc)


def entries(root: Path) -> list[tuple[dict, Path]]:
    result: list[tuple[dict, Path]] = []
    for meta_path in sorted((root / "entries").glob("*/meta.json")):
        meta = json.loads(meta_path.read_text(encoding="utf-8"))
        if meta.get("status", "published") != "published":
            continue
        result.append((meta, meta_path))
    return sorted(
        result,
        key=lambda pair: (
            -parse_timestamp(pair[0].get("meta", {}).get("updated"), pair[1].stat().st_mtime).timestamp(),
            clean(pair[0].get("name")) .casefold(),
        ),
    )


def generate(root: Path, output: Path) -> None:
    records = entries(root)
    channel = ET.Element("rss", {"version": "2.0"})
    body = ET.SubElement(channel, "channel")
    ET.SubElement(body, "title").text = "Acadie.sol — Directory"
    ET.SubElement(body, "description").text = "Public Acadian community directory entries from Acadie.sol."
    ET.SubElement(body, "link").text = SITE_URL
    ET.SubElement(body, f"{{{ATOM_NS}}}link", {"href": f"{SITE_URL}/feed.xml", "rel": "self", "type": "application/rss+xml"})
    ET.SubElement(body, "language").text = "fr"

    latest = max(
        (parse_timestamp(meta.get("meta", {}).get("updated"), path.stat().st_mtime) for meta, path in records),
        default=datetime.now(timezone.utc),
    )
    ET.SubElement(body, "lastBuildDate").text = format_datetime(latest, usegmt=True)

    for meta, path in records:
        slug = clean(meta.get("slug")) or path.parent.name
        name = clean(meta.get("name")) or slug
        summary = localized(meta.get("summary")) or clean(meta.get("short_description"))
        item = ET.SubElement(body, "item")
        ET.SubElement(item, "title").text = name
        ET.SubElement(item, "description").text = summary
        ET.SubElement(item, "link").text = f"{SITE_URL}/entry.html#{slug}"
        ET.SubElement(item, "guid", {"isPermaLink": "true"}).text = f"{SITE_URL}/entry.html#{slug}"
        updated = parse_timestamp(meta.get("meta", {}).get("updated"), path.stat().st_mtime)
        ET.SubElement(item, "pubDate").text = format_datetime(updated, usegmt=True)
        ET.SubElement(item, "category").text = clean(meta.get("category")) or "community"
        for tag in meta.get("tags", []):
            tag_text = clean(tag)
            if tag_text:
                ET.SubElement(item, "category").text = tag_text

    tree = ET.ElementTree(channel)
    ET.indent(tree, space="  ")
    output.parent.mkdir(parents=True, exist_ok=True)
    tree.write(output, encoding="utf-8", xml_declaration=True)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--output", type=Path, default=None)
    args = parser.parse_args()
    output = args.output or args.root / "feed.xml"
    generate(args.root, output)
    print(f"Generated {output} from {len(entries(args.root))} published entries")


if __name__ == "__main__":
    main()
