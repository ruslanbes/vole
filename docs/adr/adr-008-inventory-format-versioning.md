# ADR-008: Inventory format versioning

- **Status:** Acccepted
- **Date:** 2026-10-12

## Context

Software inventory file staretd with `"format": 1` as format version identifier. We need clear rules
about compatibility and when we bump the version.

## Decision

`FORMAT` changes only for breaking changes. Adding new fields does not change the number.


| Change                                         | Bump `FORMAT`? | Action                                       |
| ---------------------------------------------- | -------------- | -------------------------------------------- |
| New optional field                             | No             | Add it to `ENTRY_FIELDS` / `VERSION_FIELDS`. |
| New allowed value (e.g. a status)              | No             | Add it to `STATUSES`.                        |
| Rename a field                                 | Yes            | Migration                                    |
| Change a field's type or meaning               | Yes            | Migration                                    |
| Remove a field that holds hand-written text    | Yes            | Migration                                    |
| Change the top-level shape (`format` / `apps`) | Yes            | Migration                                    |


Migration rules:

1. The new vole reads format `N-1` and rewrites it as `N`. The command
  is either `vole migrate` or automatic on first load.
2. Before rewriting, it keeps a copy of the old file next to it, e.g.
  `software.json.format1.bak`.
3. A vole that finds a **newer** format than it knows refuses the file and says to upgrade.

## Consequences

- Most schema work (new optional fields) needs no migration code.
