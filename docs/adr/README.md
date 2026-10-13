# Architecture Decision Records

ADRs capture **durable** choices (stack, boundaries, contracts) that should outlive any single task.

## When to write an ADR

- Choosing or changing language, frameworks, hosting, or major libraries.
- Defining system boundaries or data/API contracts that other work depends on.
- Recording a trade-off and reasons for picking one solution against another.

Prefer a **task doc** (`dev/tasks/…`) for short-lived design while building a feature. On cleanup, promote lasting decisions from the task doc into an ADR (or a layer README / other project doc) before deleting the task file — see [`dev/CLEANUP.md`](../../dev/CLEANUP.md).

## Conventions

- Files: `docs/adr/adr-NNN-short-title.md` (zero-padded number, kebab-case title).
- Status: `Proposed` | `Accepted` | `Superseded` | `Deprecated`.
- Link related ADRs and other **durable** project docs.
- Do not link the task doc files from ADRs - task docs are temporary.
- Keep code references to a minimum (no file, function or constant names). An ADR records a
  decision; it should not need editing when the code is refactored.
- Copy [`TEMPLATE.md`](TEMPLATE.md) for a new record.

## Index

ADR-001 to ADR-007 are mentioned in older task docs but were never written; numbering
continues after them.

| ADR | Title | Status |
|-----|-------|--------|
| [008](adr-008-inventory-format-versioning.md) | Inventory format versioning | Accepted |
