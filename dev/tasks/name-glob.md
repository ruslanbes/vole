# Glob-like multi-name selection (`*` / `?`)

- **Task ID:** `name-glob`
- **Status:** done
- **Related:** `name-case-insensitive`, `name-fuzzy-match`, `name-shell-completion`

## Problem

Families of apps share a prefix (`Google Chrome`, `Google Docs`, `Google Drive`, …).
Setting the same `why` / `keep` means repeating long quoted names. There is no
multi-target write path.

## Goal

Allow shell-safe glob patterns against inventory names:

```sh
vole why 'Google*' "workspace suite"
vole keep 'Google*' mdm
```

- `*` → any substring (including empty); `?` → one character (`fnmatch`-style).
- Match is case-insensitive by default (align with `name-case-insensitive`).
- `why` (write) and `keep` apply the mutation to **all** matches after printing the
  matched names.

**Shell note:** unquoted `Google*` is expanded by the shell against the **filesystem**,
not vole. Users must quote patterns (or disable globbing). Document this prominently.

## Open questions

| # | Topic | Status | Decision |
|---|--------|--------|----------|
| 1 | Which verbs support globs? | locked | **`why` (write) + `keep` only** — not get/read, drop, purge, restore |
| 2 | Zero matches? | locked | Refuse, exit 1 |
| 3 | Confirm when N>1? | locked | Write verbs **print matched names then proceed** (no `--yes` gate) |
| 4 | Glob vs fuzzy? | locked | If pattern contains `*` or `?`, **glob only** — no fuzzy on the pattern string |
| 5 | `**` / character classes? | locked | **Only `*` and `?`** in v1 (`fnmatch`-style) |
| 6 | `add` / create? | locked | **Nothing for `add`** — glob never creates names |

## Non-goals

- Not full regex.
- Not recursive directory globs (names are flat inventory keys).
- Not changing how `list [filter]` works (substring already).

## Done when

- [x] Quoted `*` / `?` patterns select inventory names; multi-match writes work for `why` / `keep`.
- [x] README warns to quote patterns (shell globbing).
- [x] Zero matches → exit 1; multi-match prints names then proceeds; tests cover match-all / zero / print policy.

## Notes

- `inventory.is_glob_pattern` / `match_glob` — custom `*` / `?` regex (brackets literal).
- Read `vole why PATTERN` does not glob (single-name resolve only).
