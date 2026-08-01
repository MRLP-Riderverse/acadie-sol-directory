# acadie_sol_directory

Creation date: 2026-06-08
Author signature: MRLP.Acadie.sol

The Acadie.sol Directory Protocol — a digital aboiteau for Acadian cultural continuity.

**Wikipedia answers who the Acadians were. Acadie.sol answers who the Acadians are today.**

This is the **data layer** — the source of truth for the Acadian community directory.
The website (acadie_sol site repo) pulls from this. CLI tools pull from this.
Other communities fork this. Git IS the API.

## Architecture (Data Layering)

- **Markdown = Truth** — Human-readable, human-writable entry content (`entries/*/entry.md`)
- **JSON = Interop** — Agent-readable metadata pointers (`entries/*/meta.json`)
- **YAML = Structure** — Schemas, validation rules, required fields (`schemas/`)
- **RSS = Syndication** — Auto-generated from entries (`feed.xml`)
- **Git = Distribution** — Clone, fork, PR. No API key needed.

## Structure

```
acadie_sol_directory/
├── entries/          ← The heart. Each entry = folder with entry.md + meta.json
├── schemas/          ← YAML schemas defining what fields exist
├── inbox/            ← Draft entries, scratch space
├── feed.xml          ← RSS feed (auto-generated from entries)
├── data/data.json    ← Project-level metadata (counts, regions, categories)
├── logs/             ← Append-only activity notes
├── agents/           ← Rules for how agents read/write/validate entries
├── scripts/          ← Helper scripts (feed generator, validation, etc.)
└── README.md         ← This file
```

**Note:** This repo is DATA ONLY. No HTML, no CSS, no JS, no website.
The website lives in the `acadie_sol` site repo and renders this data.

## Fork & Merge Pattern

This directory is designed to be forked by other communities:

1. **Basque community** forks → adds their entries → maintains their own local directory
2. **Cajun community** forks → same pattern
3. When a local directory discovers an entry worth sharing → they submit a PR
4. **Main directory** reviews, verifies, merges → credit stays in git history
5. The main directory grows because local directories feed it
6. Each local directory gets credit — `git blame` tracks who contributed what

```
Local directories → authoritative for THEIR region/culture
Main directory   → curated merge of verified entries from locals
PR from local    → "We found this, we verified it, here's the data"
You review       → merge or don't → credit lives in git forever
```

## Entry Format

Each directory entry lives in `entries/<slug>/`:

```
entries/
  marie-boudreau/
    entry.md      ← Human-readable content (Markdown = Truth)
    meta.json     ← Agent-readable metadata (JSON = Interop)
```

The `entry.md` is what you write and read. The `meta.json` is the index card that agents parse. The schema (`schemas/entry.schema.yaml`) defines what fields are valid and required.

## Entry Workflow

1. Draft in `inbox/` (freeform, no schema pressure; use `inbox/_template.md` as the light shaping target)
2. Promote to `entries/<slug>/` with `entry.md` + `meta.json` when the public card fields are stable
3. Validate `meta.json` against `schemas/entry.schema.yaml`
4. Run `scripts/generate_feed.py` to update `feed.xml`
5. Run `scripts/export_to_site.py` to regenerate the website payload
6. Commit and push

Promotion guidance lives in `docs/promote-draft-to-entry.md`. The site payload contract lives in `docs/public-payload-contract.md`.

## Website Sync

The site repo is static. It does **not** read this repo live at page-load time.
Instead, this repo exports a JSON payload into the website repo:

```bash
cd /home/midnight/ExoCortex/websites/projects/acadie_sol_directory
python3 scripts/export_to_site.py
```

That writes `../acadie_sol/assets/directory-data.json` by default.
After that, commit/push the website repo so the public site updates.

Use `--stdout` if you only want to inspect the payload without writing it.

## Design Philosophy

1. **The Aboiteau Pattern** — Communal infrastructure maintained by shared labor. Submissions = labor. Curation = dyke maintenance. Mirrors = distributed resilience.
2. **Habitation Model** — Each community node is autonomous. No central server dependency. Forkable by design.
3. **Bilingual Survival** — JSON externally (interoperable), Markdown/YAML internally (sovereign). Interoperable without assimilation.
4. **Elder Vouching** — Trust originates in relationship, not cryptography. Steward verifies = elder vouches. The chain carries it; the person creates it.
5. **Survivability Criteria** — Portable (clone/mirror), human-carried (readable without specialized tools), community-verifiable (trust through people, not platforms).

## Consumers

- **acadie_sol site** — renders entries as a public website
- **RSS readers** — subscribe to feed.xml for signal updates
- **CLI tools** — `git clone` + query locally, no API needed
- **Other communities** — fork, add entries, PR back

---

**The directory is the aboiteau. The protocol is the pattern. The data is the farmland. The community is the labor. "We are still here" is the harvest.**
