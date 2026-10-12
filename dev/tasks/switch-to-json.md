# Switch the inventory from TOML to JSON

- **Task ID:** `switch-to-json`
- **Status:** done
- **Parent / blocked by:** decision and analysis in `storage-format`; lands before `python-only-restructure`

## Problem

The inventory is stored as TOML, which Python 3.9 can neither read nor write with the stdlib.
The tool works around that with a regex parser, raw-text block editing, key quoting, and a rule
never to split version lists on commas (ADR-003). Users will edit through `vole` commands rather
than by hand, so TOML's readability-for-editing no longer pays for that code.

## Goal

`software`, `dropped` and `versions` data are stored as pretty-printed JSON, read and written
with the stdlib `json` module. Existing TOML inventories migrate once, with nothing lost.

## Format

One object per file, deterministic output (`sort_keys=True`, `indent=2`, `ensure_ascii=False`,
trailing newline), written through a single atomic writer (temp file + `os.replace`).

```json
{
  "format": 1,
  "apps": {
    "zoom.us": {
      "added": "2026-09-13",
      "projects": [],
      "source": "brew-cask",
      "status": "active",
      "why": "client calls"
    }
  }
}
```

- `format` is the version of the file layout, for future migrations. Not named `version`: the
  `versions` file already uses `versions` for installed software versions, and vole itself will
  have release versions. `format` is neither.
- Optional fields (`keep`, `note`) are absent when unset, never `null`.
- Entry names are plain string keys, so no quoting rules.
- `versions` entries: `{"source": "...", "versions": ["..."]}`.

## Open questions

Do not implement while any row is `open`.

| # | Topic | Status | Decision |
|---|--------|--------|----------|
| 1 | Do this before `python-only-restructure` (on today's `_audit.py`) or as part of it? | locked | **Before**, on today's `_audit.py` |
| 2 | Keep three files, or fold `dropped` into the main file as `status: dropped`? | locked | **Three files**: `software.json`, `dropped.json`, `versions.json` |
| 3 | File location? | locked | **Next to the tool**, as today. A data dir is decided later (`homebrew-formula`) |
| 4 | Migrate once and delete the TOML parser, or keep reading TOML indefinitely? | locked | **Migrate once.** TOML reading exists only inside the migration |
| 5 | Migration trigger? | locked | **Explicit `migrate` command.** Until the CLI is renamed it is `./audit-software.sh migrate`. Other modes, finding TOML and no JSON, stop and tell the user to run it |

## Non-goals

- Not adding the missing CLI commands (add, drop, un-drop, rename, remove a field) — separate
  task. Until it lands, the README can still show how to edit the JSON by hand.
- Not changing what fields exist or what they mean.
- Not changing staleness logic or discovery.

## Implementation

- Replace `split_entries` / `field` / `set_field` / `toml_key` / `write_file` with
  `load(path) -> dict` and `save(path, data)`; the single-writer and atomic-replace rules stay.
- Edit, list, prune, scan and the version diff operate on dicts instead of raw blocks.
- Migration reads the old files with the existing regex parser (works on 3.9), writes JSON,
  renames the originals to `*.toml.bak`, and prints what it did. Refuses to overwrite an
  existing JSON file.
- Check the converted data round-trips: every entry and every field present before is present
  after, values unchanged.
- Convert `tests/fixtures/` to JSON; keep one TOML fixture set for the migration test.
- `software.example.toml` becomes `software.example.json`.

## Done when

- [x] All modes read and write JSON only; no TOML code outside the migration path.
- [x] Migrating the real inventory (149 entries) loses no entry or field — checked by test on
  fixtures, and on a copy of this machine's files: 149 entries / 935 fields identical to
  `tomllib`'s reading. The real files in the repo root are left for the user to migrate.
- [x] Writing unchanged data produces a byte-identical file.
- [x] Tests pass on `/usr/bin/python3` (3.9) and a current Python (44 tests; 1 skips on 3.9).
- [x] New ADR for JSON storage (ADR-007); ADR-003 marked Superseded (single-writer rule carried over).
- [x] README: "Entry format" and "Quote any name" sections replaced; `.gitignore` covers the new
  file names.
- [x] `inventory-check` updated to validate JSON (no 3.11 caveat).

## Notes

Comparison of formats and the measurements behind this choice: `dev/tasks/storage-format.md`.
Bug rows 1, 2 and 8 in `architecture-review` are the TOML-specific ones; 1 and 2 disappear
with JSON, 8 (atomic sorted writer) must survive.
