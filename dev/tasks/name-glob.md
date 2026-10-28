# Glob-like multi-name selection (`*` / `?`)

- **Task ID:** `name-glob`
- **Status:** backlog
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

- `*` → any substring (including empty); `?` → one character (OQ for exact semantics).
- Match is case-insensitive by default (align with `name-case-insensitive`).
- Commands that accept a pattern apply the mutation to **all** matches (or list-only for
  read verbs — OQ).

**Shell note:** unquoted `Google*` is expanded by the shell against the **filesystem**,
not vole. Users must quote patterns (or disable globbing). Document this prominently.

## Open questions

| # | Topic | Status | Decision |
|---|--------|--------|----------|
| 1 | Which verbs support globs? | open | **Proposal:** `why` (write), `keep`, maybe `get`/`why` read; **not** `purge` without `--force` + confirm listing matches; `drop` needs explicit confirm when >1 |
| 2 | Zero matches? | open | Refuse exit 1 |
| 3 | Confirm when N>1? | open | **Proposal:** write verbs print matched names then proceed (or require `--yes` when N>5) |
| 4 | Glob vs fuzzy? | open | If pattern contains `*` or `?`, use glob only — no fuzzy on the pattern string |
| 5 | `**` / character classes? | open | **Proposal:** only `*` and `?` in v1 (`fnmatch`-style) |
| 6 | `add` / create? | open | Glob never creates names |

## Non-goals

- Not full regex.
- Not recursive directory globs (names are flat inventory keys).
- Not changing how `list [filter]` works (substring already).

## Done when

- [ ] Quoted `*` / `?` patterns select inventory names; multi-match writes work for locked verbs.
- [ ] README warns to quote patterns (shell globbing).
- [ ] Destructive verbs gated as locked; tests for match-all, zero, confirm policy.
