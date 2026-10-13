# `vole why` — read/write the reason in one short verb

- **Task ID:** `cli-why`
- **Status:** done
- **Related:** `cli-edit-coverage` (`edit --why`), README Use section

## Problem

The most common inventory edit is setting or checking `why`. Today that is
`vole edit NAME --why "…"` (write) or scanning `vole list` / opening JSON (read).
A dedicated verb matches how people talk about the tool (“why is this here?”).

## Goal

```sh
vole why NAME           # print the current why (text only)
vole why NAME "Reason"  # set why (same persistence rules as edit --why)
```

`edit --why` stays; `why` is the short path for the common case.

## Open questions

| # | Topic | Status | Decision |
|---|--------|--------|----------|
| 1 | Resolve software then dropped (like `edit`)? | locked | **Yes** — same name resolution as `edit` |
| 2 | Read mode when entry missing? | locked | stderr + exit 1 (`why: no entry named '…'`) |
| 3 | Read mode when `why` is missing / `TODO` / empty? | locked | Print the stored value as scan sees it (`TODO` when that is stored; empty line if cleared). Exit 0 |
| 4 | Write mode with empty reason `vole why NAME ""`? | locked | Same as `edit --why ''` — existing `set_field` clear rules |
| 5 | Write mode when entry missing? | locked | Refuse (exit 1); do not auto-`add` |
| 6 | Output shape on read? | locked | Single line = why text only (no `NAME:` prefix) |
| 7 | Output shape on write? | locked | Reuse `edit`’s entry dump / confirmation |

## Non-goals

- Not replacing `edit` for `--keep` / `--status`.
- Not batch why / interactive prompts.
- Not changing inventory schema.
- Not a separate `because` write verb.

## Done when

- [x] `vole why NAME` prints current why (text only).
- [x] `vole why NAME "Reason"` persists why (software or dropped).
- [x] Missing entry → exit 1 on read and write; empty reason clears like `edit --why ''`.
- [x] README documents the command.
- [x] Tests for read, write, missing entry, clear, dropped.
