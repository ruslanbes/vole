# `vole get` — show one inventory entry (no scan)

- **Task ID:** `cli-get`
- **Status:** done
- **Related:** `cli-why`, `list`, `_print_entry` in `cli.py`

## Naming

**`get`** (not `view`) — list/get pair; short; no UI/pager connotation.

## Problem

`vole list` is a truncated table (terminal width, why column clipped). There is no
read-only way to dump **everything stored** for one name without opening JSON or
running a write-shaped `edit`/`why` path. Agents and humans both need a precise
“show me this record” command that does **not** rescan the machine.

## Goal

```sh
vole get NAME
```

Print all inventory fields for that entry (software or dropped), plus the matching
`versions.json` row when present. No discovery, no signals, no writes.

## Open questions

| # | Topic | Status | Decision |
|---|--------|--------|----------|
| 1 | Command name? | locked | **`get`** (not `view`) |
| 2 | Resolve software then dropped (like `edit`/`why`)? | locked | **Yes** |
| 3 | Missing entry? | locked | stderr + exit 1, same `_no_entry` style as `why` |
| 4 | Output shape? | locked | Reuse `_print_entry`. **No** file suffix — `status` / `archived_by` show archive state |
| 5 | Include `versions.json`? | locked | **Yes** — `versions:` section after entry; omit if no row |
| 6 | Machine-readable / extra flags? | locked | **None in v1** |
| 7 | Only-in-versions? | locked | Exit 1 + note to run `scan` / `add` |

## Non-goals

- Not a scan / dry-run substitute.
- Not editing fields.
- Not replacing `list`.
- Not a `--json` flag in v1.

## Done when

- [x] `vole get NAME` prints all stored entry fields + versions section when present.
- [x] Missing / versions-only → exit 1; dropped resolved like `edit` (no file suffix).
- [x] No filesystem writes; no `discover_all` / signals.
- [x] README documents `get`.
- [x] Tests for software hit, dropped hit, missing, versions section, versions-only.
