# `vole keep` — set the keep reason in one short verb

- **Task ID:** `cli-keep`
- **Status:** done
- **Related:** `cli-why`, `cli-edit-coverage` (`edit --keep`), README Keep section

## Problem

Marking something as kept (`keep`) is a common inventory edit after a scan flags a
DROP CANDIDATE. Today that is `vole edit NAME --keep "…"`. `vole why` already covers
the why field; keep deserves the same short write path.

## Goal

```sh
vole keep NAME "mdm"        # set keep (same persistence rules as edit --keep)
vole keep NAME ""           # clear keep (same as edit --keep '')
```

**Write only** — no `vole keep NAME` read mode. Use `vole get NAME` (or `list`) to see
the current value. `edit --keep` stays; `keep` is the short path for the common case.

## Open questions

| # | Topic | Status | Decision |
|---|--------|--------|----------|
| 1 | Resolve software then dropped (like `edit` / `why`)? | locked | **Yes** — same name resolution as `edit` |
| 2 | Read mode? | locked | **None** — write only (per request). Inspect via `get` / `list` |
| 3 | Reason required? | locked | **Yes** — positional arg required; bare `vole keep NAME` is a usage error (exit 2) |
| 4 | Empty reason `vole keep NAME ""`? | locked | Same as `edit --keep ''` — clears the field |
| 5 | Missing entry? | locked | Refuse (exit 1); do not auto-`add` |
| 6 | Output shape on write? | locked | Reuse `edit`’s entry dump / confirmation (same as `why` write) |

## Non-goals

- Not a read/print path for `keep` (use `get`).
- Not replacing `edit` for `--why` / `--status`.
- Not batch keep / interactive prompts.
- Not changing inventory schema or keep semantics (still free-form; still suppresses staleness only).

## Done when

- [x] `vole keep NAME "Reason"` persists keep (software or dropped).
- [x] Missing entry → exit 1; empty reason clears like `edit --keep ''`; bare name → usage error.
- [x] README documents the command (next to `why`).
- [x] Tests for write, clear, missing entry, dropped, bare-name refusal.
