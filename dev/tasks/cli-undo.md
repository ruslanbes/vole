# `vole undo` — reverse the last inventory change

- **Task ID:** `cli-undo`
- **Status:** done
- **Related:** `why` / `keep` / `drop` / `restore` / `add` / `purge`, `scan`, inventory save

## Problem

Write verbs mutate `software.json` / `dropped.json` (and sometimes `versions.json`) with
no way to take the last change back. A mistyped `why`, accidental `drop`, or over-eager
`purge` means hand-editing JSON or reconstructing state from memory. That is especially
painful after batch writes (`name-glob`) or a write-mode `scan` that archives many
rows at once.

## Goal

A first-class **`vole undo`** that restores inventory to the previous checkpoint after a
mutating command, entirely from the CLI:

```sh
vole why jq "wrong reason"
vole undo                 # restores prior why (or clears if none)
```

Observable: after a supported mutation, `undo` restores the previous shadow checkpoint from
a stack (default depth 20). Repeated `undo` walks the stack; empty stack → refuse.

## Open questions

| # | Topic | Status | Decision |
|---|--------|--------|----------|
| 1 | Depth — one step only, or a stack? | locked | **Stack, default depth 20** (configurable later if needed) |
| 2 | What is undoable? | locked | **Anything that updates the local library** — user write verbs **and write-mode `scan`** |
| 3 | How is history stored? | locked | **Shadow copy of touched files** under the data dir, taken **before** the mutating save; push onto the undo stack |
| 4 | `purge` / destructive? | locked | **Not special** — snapshot-before-mutate covers purge; `undo` restores the last stack entry like any other write |
| 5 | Interaction with `reset`? | locked | **`reset` wipes everything** (inventory + undo stack) and **cannot be undone** |
| 6 | Output / dry-run? | locked | **`--dry-run` supported** — show what would be restored without applying |
| 7 | Autoscan / agent scans? | locked | **`autoscan run` does not create a checkpoint** — undo is for **interactive** commands only |
| 8 | Format / migrations? | locked | Checkpoint must be same inventory `format` or **refuse** restore after migrate |

## Non-goals

- Not a full time-machine / arbitrary date restore.
- Not undoing Homebrew / disk uninstalls (machine state) — inventory only.
- Not git-backed versioning of `~/.config/vole/`.
- Not multi-user or sync conflict resolution.

## Implementation (sketch)

- `vole/undo.py` — stack under `undo/` (`stack.json` + frame dirs).
- Checkpoint before why/keep/drop/restore/add/purge and interactive write-scan.
- `autoscan run` → `scan.run(..., checkpoint=False)`.
- `migrate` clears the stack; format mismatch on restore refuses.

## Done when

- [x] `vole undo` restores the last interactive library mutation from the stack; nothing-to-undo is explicit.
- [x] Stack depth default 20; purge + interactive scan covered; autoscan run does not checkpoint.
- [x] `reset` clears undo stack and cannot be undone; `--dry-run` on undo; format mismatch refuses.
- [x] README documents undo scope; PRIVACY notes any new files under the data dir.
- [x] Tests cover happy path, empty stack, depth cap, reset wipe, autoscan skip, dry-run, format guard.

## Notes

- Data files are the product — undo must not corrupt `format` or leave partial writes (use the same atomic save path).
- Glob multi-name writes share one checkpoint per command.
