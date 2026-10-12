# Source: Yarn global

- **Task ID:** `source-yarn`
- **Status:** done
- **Related:** `npm_global` already covers `npm install -g`; Yarn classic globals are a parallel path

## Problem

Some environments still use `yarn global add` for CLI packages. Those never appear in
`npm ls -g`, so vole misses them today.

## Goal

`vole scan` lists Yarn global packages with versions under source id `yarn-global`, when a
Yarn that still supports globals is present.

## Open questions

| # | Topic | Status | Decision |
|---|--------|--------|----------|
| 1 | Yarn classic vs Berry? | locked | **Classic only** — Berry no-op (no error) |
| 2 | Prefer npm when the same package is in both? | locked | **First-wins** — register after `npm_global`, before `pnpm_global` |
| 3 | Discovery command? | locked | **`yarn global list --json --depth 0`** (NDJSON info lines); Berry failure → empty |

## Done when

- [x] Classic Yarn globals appear in scan.
- [x] Berry / missing yarn does not error the scan.
- [x] Tests + README updated.
