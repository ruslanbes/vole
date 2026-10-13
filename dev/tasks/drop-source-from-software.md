# Stop storing `source` on active software entries

- **Task ID:** `drop-source-from-software`
- **Status:** done
- **Blocked by:** _none_ (framework shipped; this becomes format 1→2 / `m002_…`)
- **Related:** [ADR-008](../../docs/adr/adr-008-inventory-format-versioning.md), `cli-get`, scan auto-archive, `vole add`

## Problem

`source` lives on both `software.json` / `dropped.json` entries and on every
`versions.json` row. For installed software, the versions copy is authoritative
(rewritten every write scan) and is what `list` already shows. The software copy
is frozen at stub/`add` time, can diverge from discovery, and is unused by
classify / staleness.

The only durable need for an entry-level `source` is **after uninstall**: versions
rows go away with the install, but a dropped archive should still say where it
came from.

## Goal

- **Active** `software.json` entries do **not** store `source`.
- Live source comes from `versions.json` (discovery).
- At **drop / scan-archive** time, copy `source` from the current versions row onto
  the dropped entry (so archives keep provenance).
- `vole add` no longer takes `--source`; stubs write no source.
- Migration **1→2** strips `source` from active software (ADR-008: every migration
  bumps format). No history repair when software/versions sources disagreed.

## Open questions

| # | Topic | Status | Decision |
|---|--------|--------|----------|
| 1 | Strip `source` from active software only? | locked | **Yes.** Dropped entries keep or gain `source` at archive time |
| 2 | Copy source at drop when versions row missing? | locked | Omit `source` on the dropped entry; warn once on stderr |
| 3 | `vole add --source`? | locked | **Remove** `--source` from `add`. Source appears on next scan via versions |
| 4 | Format bump? | locked | **Yes — bump 1→2** (ADR-008 always-bump). Migration module strips active `source`; leave dropped as-is |
| 5 | `get` / edit dump? | locked | Active: source only under `versions:`. Dropped: `source` on the entry |
| 6 | `list`? | locked | Unchanged (already uses versions source) |
| 7 | Scan stub creation? | locked | `inventory.stub(today)` — no source arg |
| 8 | Existing divergent active sources? | locked | Strip software `source`; versions wins afterward. No history fix |

## Migrations

Framework: [`inventory-migrations`](inventory-migrations.md). This task is the first
production step (format 1→2).

## Non-goals

- Not merging software + versions into one file.
- Not letting users edit `source` via CLI.
- Not changing first-wins discovery order.
- Not building the migrations package here (blocked on `inventory-migrations`).

## Done when

- [x] Active software stubs / entries have no `source` field.
- [x] Manual drop and scan-archive copy `source` from versions when present; warn + omit if missing.
- [x] `add` no longer takes `--source`.
- [x] Migration 1→2 strips `source` from active software; `ENTRY_FIELDS` / `FORMAT` updated.
- [x] `get`, README, tests, CHANGELOG updated.
- [x] No attempt to reconcile past software/versions source mismatches.
