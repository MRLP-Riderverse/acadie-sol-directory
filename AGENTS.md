# AGENTS.md for acadie_sol_directory

## Project Identity
- This is the **Acadie.sol Directory Protocol — data layer**.
- This repo is DATA ONLY. No website files. The site lives in the `acadie_sol` site repo.
- The website follows the activity. The activity does not follow the website.
- Trust is the core asset, not the site, not the database, not the domain.

## Data Architecture
- **Markdown = Truth**: `entries/*/entry.md` is the human-readable, human-writable source of truth.
- **JSON = Interop**: `entries/*/meta.json` is the agent-readable metadata pointer.
- **YAML = Structure**: `schemas/entry.schema.yaml` defines what fields exist, required/optional, allowed values.
- **RSS = Syndication**: `feed.xml` is auto-generated from entries. Do not hand-edit.
- **Git = Distribution**: Clone, fork, PR. This repo IS the database.

## Working Rules
- Treat `README.md` as the canonical project intent.
- Treat `schemas/entry.schema.yaml` as the contract for entry structure.
- Never create an entry without both `entry.md` AND `meta.json`.
- Validate `meta.json` fields against the schema before writing.
- After adding/editing entries, run `scripts/generate_feed.py` to update `feed.xml`.
- Write recognizable weekly hours as `Mon-Fri 09:00–17:00; Sat 10:00–14:00`; the exporter expands this into Monday–Sunday rows and marks omitted days `Closed`. Keep seasonal or otherwise ambiguous hours as prose so they are not guessed.
- Keep `logs/` append-only and follow the timestamp format from `projects/README.md`.
- Put project-specific helper scripts in `scripts/`.
- Draft entries go in `inbox/` first, then move to `entries/` when polished.
- NEVER add HTML, CSS, JS, or website files to this repo. That's the site repo's job.

## Entry Workflow
1. Draft in `inbox/` (freeform, no schema pressure)
2. Move to `entries/<slug>/` with `entry.md` + `meta.json`
3. Validate `meta.json` against `schemas/entry.schema.yaml`
4. Run `scripts/generate_feed.py` to update `feed.xml`
5. Commit and push

## Fork & Merge
- Other communities fork this repo, add their entries, maintain their own local directory.
- Verified entries from local directories can be PR'd back to the main directory.
- Credit lives in git history forever — `git blame` tracks contributions.
- Merge policy: steward-verified entries only.

## Design Constraints
- No tracking. No surveillance. Collect needs, not identities.
- Local-first. Git-as-source-of-truth. The website is disposable; the data is sacred.
- Interoperable without assimilation (JSON externally, Markdown internally).
- Every entry must be survivable: portable, human-carried, community-verifiable.

## Project Title/Tag
acadie_sol_directory
