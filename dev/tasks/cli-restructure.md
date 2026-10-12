# CLI command restructure

- **Task ID:** `cli-restructure`
- **Status:** done
- **Parent / blocked by:** —

## Problem

The CLI grew flags and leftovers from the shell era (`vole` alone scans, `--report`
instead of a dry-run flag, `clean` as the wipe verb, a separate `prune-dropped` that
only makes sense if people hand-edit JSON). The surface should read as a small set of
subcommands a stranger can learn from `vole help`.

## Goal

A short, consistent command set documented in the README. Default invocation shows help.
Scan is explicit. Dry-run is a scan flag. Inventory wipe is `reset`. Dropping an entry
is one CLI action (no separate prune).

## Surface

| Command | Behavior |
|---------|----------|
| `vole` / `vole help` | Print help (same as `-h` / `--help`) |
| `vole scan` | Scan the machine, update inventory + versions, print the report |
| `vole scan --dry-run` | Same report, never write |
| `vole list [filter]` | Table of installed software (unchanged) |
| `vole edit NAME …` | Set `why` / `keep` / `status` |
| `vole reset` | Delete inventory data (was `clean`); confirm unless `--force` |

Removed:

| Today | Fate |
|-------|------|
| Bare `vole` → scan | Becomes help |
| `vole --report` / `scan --report` | Replaced by `vole scan --dry-run` |
| `vole clean` | Renamed to `vole reset` |
| `vole prune-dropped` | Removed; archive happens inside `edit` |

### Drop / archive flow

```
vole edit NAME --status dropped
  → entry removed from software.json
  → entry written into dropped.json (reasons kept)
  → if still installed, next scan still reports DROPPED BUT PRESENT
```

Leftover soft-`status: dropped` rows already in `software.json` stay tolerated by scan
(no silent migration). Prefer re-running `edit --status dropped` to archive them.

## Open questions

| # | Topic | Status | Decision |
|---|--------|--------|----------|
| 1 | How does dropping work without `prune-dropped`? | locked | **archive-on-edit** — `edit --status dropped` moves the entry into `dropped.json` immediately |
| 2 | Keep `dropped.json` at all? | locked | **yes** — archived reasons are product data |
| 3 | Rename `clean` → `reset` only, or change behavior? | locked | **rename only** — same files, same confirm / `--force` |
| 4 | `vole help` as a real subcommand vs alias of `-h`? | locked | **real subcommand**; bare `vole` also prints help (exit 0) |
| 5 | Top-level `--report` / `--months` without `scan`? | locked | **remove** — only `vole scan [--dry-run] [--months N]` |

## Non-goals

- No new edit verbs (`drop`, `undrop`, rename, …) — that stays `cli-edit-coverage`.
- No Homebrew / install changes.
- No inventory format bump; no migration of existing soft-dropped rows.

## Done when

- [x] Commands match the locked table above.
- [x] README command list matches.
- [x] Tests updated and green.
- [x] CHANGELOG notes the rename/removals (breaking CLI change, pre-1.0).
