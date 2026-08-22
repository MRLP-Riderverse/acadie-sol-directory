from __future__ import annotations

import importlib.util
import json
import time
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


def write_event_fixture(root: Path, *, summary: str = "Bring a chair.") -> None:
    write(
        root / "events" / "big-d-community-placeholder" / "event.md",
        """# Big D Community Placeholder

Community event at the drive-in.
""",
    )
    write(
        root / "events" / "big-d-community-placeholder" / "meta.json",
        json.dumps(
            {
                "id": "big-d-community-placeholder",
                "status": "active",
                "title": "Big D Community Placeholder",
                "summary": summary,
                "starts_at": "2026-07-19T15:00:00Z",
                "ends_at": "2026-07-19T17:00:00Z",
                "location_id": "big-d-drive-in",
                "calendar": {"ics_enabled": True},
            }
        ),
    )
    write(
        root / "locations" / "big-d-drive-in" / "location.md",
        """# Big D Drive-In

Classic local drive-in.
""",
    )
    write(
        root / "locations" / "big-d-drive-in" / "meta.json",
        json.dumps(
            {
                "id": "big-d-drive-in",
                "name": "Big D Drive-In",
                "kind": "venue",
                "address": "2035 St Peter Ave, Bathurst, NB",
            }
        ),
    )


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


def test_hours_schedule_expands_weekly_ranges_and_marks_missing_days_closed():
    rows = export_to_site.parse_hours_schedule("Mon-Fri 09:00–17:00; Sat 10:00–14:00")
    assert [row["day"] for row in rows] == ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    assert rows[0]["hours"] == "09:00–17:00"
    assert rows[5]["hours"] == "10:00–14:00"
    assert rows[6]["hours"] == "Closed"


def test_hours_schedule_keeps_ambiguous_prose_as_fallback():
    assert export_to_site.parse_hours_schedule("seasonal / closed for winter") == []
    assert export_to_site.parse_hours_schedule("most evenings and some matinee showings") == []


def test_hours_schedule_splits_multiple_ranges_on_one_line():
    rows = export_to_site.parse_hours_schedule("Sun-Tue 12:00-18:00, Wed 12:00-20:00, Thu-Sat 12:00-23:00")
    assert [row["hours"] for row in rows] == [
        "12:00-18:00", "12:00-18:00", "12:00-20:00",
        "12:00-23:00", "12:00-23:00", "12:00-23:00", "12:00-18:00",
    ]


def test_official_entry_prefers_meta_json_contract(tmp_path: Path):
    write(
        tmp_path / "entries" / "pizza-delight-bathurst-st-peter-ave" / "entry.md",
        """# Pizza Delight — Bathurst St Peter Ave

Family restaurant in Bathurst.

## Public notes
- Known local branch with sit-down service.
- Good for family meals.

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
                "thumbnail": {"src": "assets/entries/pizza-delight/thumbnail.jpg", "alt": "Photo of Pizza Delight Bathurst"},
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
    assert item["note_points"] == ["Known local branch with sit-down service.", "Good for family meals."]
    assert item["contact"]["phone"] == "506-111-1111"  # meta is canonical
    assert item["public_area"] == "Acadie-Bathurst"
    assert item["thumbnail_src"] == "assets/entries/pizza-delight/thumbnail.jpg"
    assert item["thumbnail_alt"] == "Photo of Pizza Delight Bathurst"


def test_official_entry_uses_authored_markdown_before_metadata_summary(tmp_path: Path):
    write(
        tmp_path / "entries" / "authored-prose" / "entry.md",
        """# Authored Prose

This is the exact public sentence written by the steward.

## Public notes
- First authored note.
- Second authored note.
""",
    )
    write(
        tmp_path / "entries" / "authored-prose" / "meta.json",
        json.dumps(
            {
                "status": "published",
                "category": "community",
                "short_description": "An editorial replacement sentence.",
                "tags": ["explicit-tag"],
            }
        ),
    )

    item = export_to_site.build_payload(tmp_path)["items"][0]

    assert item["description"] == "This is the exact public sentence written by the steward."
    assert item["category"] == "community"
    assert item["tags"] == ["explicit-tag"]
    assert item["note_points"] == ["First authored note.", "Second authored note."]


def test_official_entry_exports_localized_public_notes(tmp_path: Path):
    write(
        tmp_path / "entries" / "bilingual-entry" / "entry.md",
        """# Bilingual Entry

English public description.

## Public notes
- English public note.

## Notes publiques
- Note publique en français.
""",
    )
    write(
        tmp_path / "entries" / "bilingual-entry" / "meta.json",
        json.dumps(
            {
                "slug": "bilingual-entry",
                "name": "Bilingual Entry",
                "status": "published",
                "category": "community",
                "short_description": "English public description.",
                "summary": {"en": "English public description.", "fr": "Description publique en français."},
            }
        ),
    )

    item = export_to_site.build_payload(tmp_path)["items"][0]

    assert item["note_points_localized"] == {
        "en": ["English public note."],
        "fr": ["Note publique en français."],
        "shiac": [],
    }
    assert item["notes_localized"]["fr"] == "- Note publique en français."


def test_calendar_ics_is_stable_across_repeat_exports(tmp_path: Path):
    directory_root = tmp_path / "directory"
    site_root = tmp_path / "site"
    write_event_fixture(directory_root)

    export_to_site.export_all(directory_root, site_root)
    ics_path = site_root / "assets" / "calendar" / "big-d-community-placeholder.ics"
    first = ics_path.read_text(encoding="utf-8")

    time.sleep(1.1)
    export_to_site.export_all(directory_root, site_root)
    second = ics_path.read_text(encoding="utf-8")

    assert second == first


def test_calendar_ics_changes_when_event_source_changes(tmp_path: Path):
    directory_root = tmp_path / "directory"
    site_root = tmp_path / "site"
    write_event_fixture(directory_root, summary="Bring a chair.")

    export_to_site.export_all(directory_root, site_root)
    ics_path = site_root / "assets" / "calendar" / "big-d-community-placeholder.ics"
    first = ics_path.read_text(encoding="utf-8")

    time.sleep(1.1)
    write_event_fixture(directory_root, summary="Bring a chair and a blanket.")
    export_to_site.export_all(directory_root, site_root)
    second = ics_path.read_text(encoding="utf-8")

    assert "DESCRIPTION:Bring a chair and a blanket." in second
    assert second != first
