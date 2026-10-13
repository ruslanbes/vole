# Case-insensitive name sorting in list / scan

- **Task ID:** `case-insensitive-sort`
- **Status:** done
- **Related:** `inventory.render` (already case-insensitive on disk), `list`, `scan` classify/render

## Problem

Human-facing name lists should read like a phone book: `Alfred` next to `azure`, not
all-caps / code-point order (`A`…`Z` then `a`…`z`).

**Today (not “JSON file order”):**

| Surface | How names are ordered |
|---------|------------------------|
| `software.json` / `dropped.json` / `versions.json` on disk | Already case-insensitive: `sorted(…, key=lambda n: (n.lower(), n))` in `inventory.render` |
| `vole list` | Already `sorted(installed, key=str.lower)` (versions keys, not software file order) |
| `vole scan` report sections | **Case-sensitive** — `classify` and `versions.diff` use bare `sorted(…)` |

So scan NEW / DROP CANDIDATES / MISSING A REASON / VERSIONS / etc. still use Python’s
default string order. That is the main user-visible gap. `list` is close but uses a
slightly different key (`str.lower` alone vs inventory’s `(lower, original)` tie-break).

## Goal

All human-facing name lists (scan report + list) sort **case-insensitively**, matching
the on-disk inventory convention: compare `name.lower()`, then original name for ties.

## Open questions

| # | Topic | Status | Decision |
|---|--------|--------|----------|
| 1 | Scope? | locked | `scan` classify + `versions.diff` + align `list` to the same helper. Not suggestion/`_close` lists unless we centralize |
| 2 | Sort key? | locked | `(n.lower(), n)` — same as inventory; not `casefold()` |
| 3 | Shared helper? | locked | One small helper (e.g. `inventory.name_sort_key`) used by render, list, classify, versions.diff |
| 4 | Change on-disk order? | locked | **No rewrite** — disk already uses this key; helper just shares it. No format bump |
| 5 | Tests? | locked | **Omit** — not critical enough for dedicated unit tests |


## Non-goals

- Not changing discovery / first-wins source order.
- Not sorting by last_used, source, or why.
- Not a user-facing `--sort` flag.
- Not locale-aware collation beyond `.lower()`.

## Done when

- [x] Scan report name lists are case-insensitive (same key as inventory).
- [x] `list` uses the same key (not a divergent `str.lower`-only sort).
- [x] Shared helper; inventory.render uses it (behavior unchanged).
- [x] No inventory format bump / no mass rewrite of user files.
- [x] No dedicated unit tests (OQ5).
