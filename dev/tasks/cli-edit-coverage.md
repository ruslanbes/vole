# CLI coverage for remaining hand edits

- **Task ID:** `cli-edit-coverage`
- **Status:** done
- **Related:** `cli-restructure` (archive-on-drop shipped; undrop/rename parked here)

## Problem

`vole edit` could only touch `software.json`. Remaining gaps: edit while archived, undrop,
add, permanent delete. Rename/merge deferred pending user feedback.

## Goal

Those operations are first-class CLI verbs so users need not edit JSON by hand (except
rename/merge until feedback).

## Open questions

| # | Topic | Status | Decision |
|---|--------|--------|----------|
| 1 | Un-drop + edit while archived? | locked | **`edit` resolves software then dropped.** Field changes in place. **`--status active`** / **`vole restore`** undrop. **`--status dropped`** archives |
| 2 | Rename / merge? | deferred | Not in this task — wait for user feedback |
| 3 | Add surface? | locked | **`vole add NAME`** — create if missing both; refuse if in software; undrop+set if only in dropped |
| 4 | Permanent delete? | locked | **`vole delete NAME`** (+ versions row); confirm unless `--force` |
| 5 | Separate subcommands vs flags? | locked | Hybrid: `edit` + `add` / `delete` / `restore` |

## Done when

- [x] Edit-across-files + undrop (OQ1), add/delete/restore (OQ3–5) work from the CLI.
- [x] README documents the new behaviour.
- [x] Tests green on Python 3.9+.
- [x] Rename explicitly left out pending feedback.
