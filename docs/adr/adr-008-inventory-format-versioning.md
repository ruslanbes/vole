# ADR-008: Inventory format versioning

- **Status:** Accepted
- **Date:** 2026-10-13

## Context

Inventory JSON files carry a top-level `format` integer. We need a single rule for when
that number changes, how migrations run, and how old or newer vole binaries behave.

## Decision

**Every registered migration bumps `format` by 1.** The integer is the migration epoch:
file at format `N` has all migrations through step `N` applied. Code’s `FORMAT` is the
latest epoch this vole knows how to read and write.

| Situation | Bump `format`? | Action |
|-----------|----------------|--------|
| New optional field, code reads missing as absent, no rewrite needed | No | Just start writing the field; no migration module |
| Any change that needs a one-shot rewrite (strip/rename/remove/retype/reshape) | Yes | Add a migration module; `FORMAT` becomes `N+1` |
| Rename / remove hand-written fields, type or meaning change, top-level reshape | Yes | Same — always via a migration |

Migration rules:

1. Migrations live as an ordered registry. Step `k`
   transforms files from format `k` to `k+1` (formats are 1-based epochs matching
   “after migration k”).
2. On load (or `vole migrate`), while `file.format < CODE_FORMAT`, apply the next step,
   write a bak, rewrite the file at `format + 1`.
3. Before rewriting, keep a copy beside the file, e.g. `software.json.format1.bak`
   (source format in the name).
4. If `file.format > CODE_FORMAT`, refuse and ask the user to upgrade vole.
5. If `file.format <` the oldest format this build can still migrate from, refuse with a
   clear “upgrade via intermediate vole” / restore-from-bak message (floor documented
   when old steps are deleted).

Retiring migrations: delete the oldest module(s) and raise the minimum supported
input format only when wild installs are past that floor.

## Consequences

- One number answers “which world is this file in?”.
- Old vole cannot read a file after a cleanup migration (format moved on); that is
  accepted — upgrade vole, or restore the bak.
- Additive fields that need no rewrite still do not require a migration or bump.
