# Inventory migration framework

- **Task ID:** `inventory-migrations`
- **Status:** done
- **Blocks:** `drop-source-from-software` (and any later schema rewrites)
- **Related:** [ADR-008](../../docs/adr/adr-008-inventory-format-versioning.md)

## Problem

There is no code home for inventory migrations: no registry, naming, runner, or cleanup
story. The old TOML `vole migrate` was removed. ADR-008 now says **every registered
migration bumps `format`**; we need the framework that implements that before the first
real step (`drop-source-from-software`).

## Goal

Ship a small migration framework:

1. Ordered, named steps under `vole/migrations/`.
2. Each step transforms format `N` → `N+1` (ADR-008).
3. Safe apply: bak + rewrite; refuse newer format; optional floor for deleted steps.
4. Easy to see what exists and delete old steps later without hunting call sites.
5. Unblocks `drop-source-from-software` as the first production migration (1→2).

## Open questions

| # | Topic | Status | Decision |
|---|--------|--------|----------|
| 1 | Bump format on every migration, or two kinds? | locked | **A — bump on every migration.** ADR-008 rewritten accordingly. No breaking/non-breaking split; no applied-id list |
| 2 | Where do migration modules live? | locked | `vole/migrations/` shipped with the package. One module per step: `m002_strip_software_source.py` (zero-padded **target** format + snake id). Registry lists them in order |
| 3 | How is “already applied” recorded? | locked | **`format` integer only.** File at format `N` has migrations through N applied. No parallel field |
| 4 | Trigger: auto on load vs explicit `vole migrate`? | locked | **Auto on load** before commands that need inventory + optional `vole migrate` that runs/reports the same runner. Refuse if `format` > code `FORMAT` |
| 5 | Bak naming? | locked | `software.json.format{N}.bak` where N is the format *before* the step. **One bak per file per step** |
| 6 | Scope of a migration step? | locked | One step may touch software / dropped / versions together. Runner baks then writes all touched files, or stops |
| 7 | ADR update? | locked | **Done** — [ADR-008](../../docs/adr/adr-008-inventory-format-versioning.md) rewritten for always-bump |
| 8 | Retiring old migrations? | locked | Raise minimum readable format when deleting modules; document floor in module docstring / STATUS (“safe to drop m002 after vole ≥ X”) |

## Done when

- [x] `vole/migrations/` registry + runner + tests (harness steps in unit tests).
- [x] Auto-apply on load; `vole migrate`; bak + refuse-newer per ADR-008.
- [x] ADR-008 + package docstring / README / ground rules for add/retire.
- [x] `drop-source-from-software` unblocked as `m002_…` (1→2).

## Notes

Shipped: `vole/migrations/{types,runner,__init__}.py`; empty `STEPS` → `FORMAT` 1;
`inventory.render/save(..., format=)`; CLI `_ensure_migrated` + `migrate` command.
