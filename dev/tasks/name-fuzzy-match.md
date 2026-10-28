# Fuzzy entry name match (typo tolerance)

- **Task ID:** `name-fuzzy-match`
- **Status:** backlog
- **Related:** `name-case-insensitive`, `name-glob`, `name-shell-completion`

## Problem

Long GUI app names (`Foxit PDF Reader`, `Google Chrome`) are easy to mistype. Today
resolution is exact (case-sensitive); on miss, `_near` only suggests **substring**
contains — not edit-distance. A single close typo still fails the command.

## Goal

When no exact / case-insensitive unique hit:

- Find inventory names within **≤ 2 edits** (insert/delete/substitute; details in OQs).
- If **exactly one** candidate → use it (and ideally print what was assumed).
- If zero or many → refuse; on many, list candidates (like today’s “did you mean”).

Stdlib only — small Levenshtein / similar DIY (no third-party fuzzy libs).

## Open questions

| # | Topic | Status | Decision |
|---|--------|--------|----------|
| 1 | Edit distance metric? | open | **Proposal:** Unicode code-point Levenshtein on casefolded strings; max distance **2** |
| 2 | Short-name safety? | open | **Proposal:** require `len(query) ≥ 4` (or distance ≤ 1 for shorter) so `go` cannot snap to random 2-letter names |
| 3 | Silence vs announce auto-pick? | open | **Proposal:** stderr one-liner `using 'Google Chrome'` when query ≠ resolved name |
| 4 | Apply before or after case-insensitive? | open | **Proposal:** exact → unique case-insensitive → unique fuzzy ≤2 → fail + suggestions |
| 5 | Destructive verbs (`drop` / `purge`)? | open | **Proposal:** same resolver, but auto-pick still announces; optional stricter refuse-fuzzy for `purge` |
| 6 | Multi-word / spaces? | open | Fuzzy does not remove need for quotes; it only fixes typos inside the quoted string |

## Non-goals

- Not glob / multi-target (see `name-glob`).
- Not phonetic match (Soundex) in v1.
- Not rewriting stored names.
- Not shell completion.

## Done when

- [ ] Unique ≤2-edit match auto-resolves with announcement; ambiguous / none refuse + list.
- [ ] Short-query guard prevents wild snaps.
- [ ] Resolution order documented; tests for typo hit, ambiguous, short query, exact still preferred.
