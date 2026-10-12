# Inventory shape checks on scan

- **Task ID:** `inventory-check`
- **Status:** done
- **Parent / blocked by:** —

## Problem

Valid JSON with the right `format` can still hold bad entries: wrong types, unknown
`status`, leftover fields (`projects`, `note`, …). The tool then silently ignores them.

## Goal

No dedicated `check` command. On a normal `vole scan` (including `--dry-run`), after the
inventory loads successfully, report every entry that does not match the expected shape.
Warnings only — scan continues. Works on Python 3.9, stdlib only.

## Open questions

| # | Topic | Status | Decision |
|---|--------|--------|----------|
| 1 | Should unknown `keep` values be errors, warnings, or allowed? | locked | **Allowed** — `keep` is a free-form string; README samples (`mdm`, `dependency`, `in-use`) are examples only |
| 2 | Should a normal scan run the same checks and warn? | locked | **Yes** — and there is **no** dedicated `vole check` / `--check` command |

## Non-goals

- Not a JSON Schema dependency.
- Not failing the scan on shape warnings (hard JSON/`format` errors still exit non-zero as today).
- Not migrating/removing unknown fields automatically.

## Expected shape

**software.json / dropped.json** entry fields:

| Field | Rule |
|-------|------|
| `source`, `why`, `added` | string when present |
| `status` | string; if present must be `active` or `dropped` |
| `keep` | string when present (any value) |
| anything else | unknown field → warning |

Entry itself must be an object.

**versions.json** entry:

| Field | Rule |
|-------|------|
| `source` | string when present |
| `versions` | list of strings |
| anything else | unknown field → warning |

## Done when

- [x] Scan prints each problem with file, entry and field (stderr).
- [x] Tests cover: wrong type for `versions`, unknown `status`, unknown field.
- [x] No `check` subcommand.
