from __future__ import annotations

import importlib.util
import json
from pathlib import Path


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "export_to_site.py"
spec = importlib.util.spec_from_file_location("export_to_site", SCRIPT)
assert spec is not None
assert spec.loader is not None
export_to_site = importlib.util.module_from_spec(spec)
spec.loader.exec_module(export_to_site)


def write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def test_draft_payload_has_declared_public_card_fields(tmp_path: Path):
    write(
        tmp_path / "inbox" / "big-d-drive-in.md",
        """# Draft: Big D Drive-In

Category: food
Area: Bathurst
Tags: drive-in | burger | family

## Description
Classic burger drive-in on St Peter Ave in Bathurst.

## Notes
Home of the Big D Burger.

## Public data to carry forward
- Address: 2035 St Peter Ave, Bathurst, NB
- Phone: 506-546-3585
- Hours: Mon-Sun 11:00–19:00

## Public source
- In person
""",
    )

    payload = export_to_site.build_payload(tmp_path)
    item = payload["items"][0]

    assert payload["schema_version"] == 1
    assert item["status"] == "draft"
    assert item["public_area"] == "Acadie-Bathurst"
    assert item["tags"] == ["drive-in", "burger", "family"]
    assert item["contact"]["phone"] == "506-546-3585"
    assert item["phone"] == "506-546-3585"  # backwards compatibility for current renderer
    assert item["source_type"] == "inbox"


def test_official_entry_prefers_meta_json_contract(tmp_path: Path):
    write(
        tmp_path / "entries" / "pizza-delight-bathurst-st-peter-ave" / "entry.md",
        """# Pizza Delight — Bathurst St Peter Ave

Family restaurant in Bathurst.

## Public notes
Known local branch with sit-down service.

## Contact
- Phone: 506-000-0000

## Sources
- https://example.test/pizza
""",
    )
    write(
        tmp_path / "entries" / "pizza-delight-bathurst-st-peter-ave" / "meta.json",
        json.dumps(
            {
                "slug": "pizza-delight-bathurst-st-peter-ave",
                "name": "Pizza Delight — Bathurst St Peter Ave",
                "brand_name": "Pizza Delight",
                "branch_name": "Bathurst St Peter Ave",
                "aliases": ["Pizza Delight Bathurst"],
                "status": "published",
                "category": "food",
                "short_description": "Family restaurant in Bathurst.",
                "location": {"municipality": "Bathurst", "public_area": "Acadie-Bathurst"},
                "tags": ["pizza", "family"],
                "contact": {"phone": "506-111-1111", "address": "123 St Peter Ave"},
            }
        ),
    )

    payload = export_to_site.build_payload(tmp_path)
    item = payload["items"][0]

    assert payload["published_count"] == 1
    assert payload["draft_count"] == 0
    assert item["status"] == "published"
    assert item["brand_name"] == "Pizza Delight"
    assert item["aliases"] == ["Pizza Delight Bathurst"]
    assert item["description"] == "Family restaurant in Bathurst."
    assert item["contact"]["phone"] == "506-111-1111"  # meta is canonical
    assert item["public_area"] == "Acadie-Bathurst"
