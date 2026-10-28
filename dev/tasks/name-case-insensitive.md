# Case-insensitive entry name match

- **Task ID:** `name-case-insensitive`
- **Status:** done
- **Related:** `name-fuzzy-match`, `name-glob`, `name-shell-completion`; `_Inventory.where` / `_near`

## Problem

Entry names were matched **exactly**, including case. Humans type `Go` or
`google chrome`; inventory keys may differ in casing (`go`, `Google Chrome`).

## Goal

For single-name commands (`why`, `keep`, `get`, `drop`, `restore`, `purge`, …):

1. **Exact** (case-sensitive) hit → use it.
2. Else **case-insensitive** (`lowercase(query) == lowercase(entry)`): if **exactly one**
   hit → use that real key.
3. Else if **several** CI hits → refuse with `did you mean: …`.
4. Else → missing (existing `_no_entry` / substring suggestions).

`add` and `list` stay out of scope.

## Open questions

| # | Topic | Status | Decision |
|---|--------|--------|----------|
| 1 | When does case-insensitive apply? | locked | After no exact hit; any query casing; unique → resolve; several → `did you mean` |
| 2 | Scope of commands? | locked | All name-taking verbs **except** `add` and `list` |
| 3 | Shared resolver? | locked | `inventory.resolve_name` + CLI `_resolve_or_fail` |
| 4 | Interaction with fuzzy / glob? | locked | CI before fuzzy; glob is a separate multi-match path |

## Non-goals

- Not typo tolerance (see `name-fuzzy-match`).
- Not multi-entry patterns (see `name-glob`).
- Not shell completion (see `name-shell-completion`).
- Not renaming inventory keys to lowercase.

## Done when

- [x] Exact match wins; unique CI match resolves to the real key (any query casing).
- [x] Ambiguous CI matches refuse with `did you mean`.
- [x] Shared resolver; `add` / `list` unchanged.
- [x] README + tests updated.
