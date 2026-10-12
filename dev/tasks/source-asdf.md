# Source: asdf

- **Task ID:** `source-asdf`
- **Status:** done
- **Related:** `mise` already covers the same niche for many users; asdf is the predecessor

## Problem

People who never migrated to mise still manage language runtimes (and some CLIs) with asdf.
Those installs are invisible to vole unless they also appear via brew or a bin dir.

## Goal

`vole scan` lists asdf-installed plugins/versions under source id `asdf`, analogous to the
existing `mise` source.

## Open questions

| # | Topic | Status | Decision |
|---|--------|--------|----------|
| 1 | Discovery API? | locked | **`asdf list`** text parse when `asdf` is on PATH |
| 2 | Entry shape — one row per plugin, versions[] multi-value? | locked | **Same as mise** — one name (plugin), several versions in `versions` |
| 3 | Dedup vs mise when both manage the same runtime? | locked | **First-wins** — mise registered before asdf |
| 4 | asdf “shims” directory as fallback? | locked | **No** — `asdf list` only |

## Non-goals

- Not migrating users from asdf to mise.
- Not inventoring every plugin’s *extra* tools beyond what `asdf list` reports.

## Done when

- [x] Scan lists asdf plugins/versions when asdf is present.
- [x] Coexistence with mise does not crash; first-wins applies.
- [x] Tests + README updated.

## Notes

```
$ asdf list
nodejs
  20.11.0
  22.2.0
python
  3.12.2
```
