# Source: pnpm global

- **Task ID:** `source-pnpm`
- **Status:** done
- **Related:** `npm_global`, `source-yarn`

## Problem

`pnpm add -g` / `pnpm install -g` is another path for Node CLIs. Those packages do not show
up in `npm ls -g`.

## Goal

`vole scan` lists pnpm global packages with versions under source id `pnpm-global`.

## Open questions

| # | Topic | Status | Decision |
|---|--------|--------|----------|
| 1 | Discovery API? | locked | **`pnpm list -g --depth 0 --json`** when `pnpm` is on PATH |
| 2 | Dedup vs npm / yarn? | locked | **First-wins** — register after `npm_global` (and yarn if/when present) so npm keeps shared names |
| 3 | Global bin dir only vs package list? | locked | **Package list from pnpm** (identity + version), not a raw directory walk |

## Done when

- [x] Scan lists pnpm globals when pnpm is present.
- [x] Missing pnpm is a no-op.
- [x] Tests + README updated.
