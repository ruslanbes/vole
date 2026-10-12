# Source: uv tool

- **Task ID:** `source-uv`
- **Status:** done
- **Related:** `source-pipx` (same niche); `bins` / `~/.local/bin` often holds uv tool shims

## Problem

`uv tool install` is replacing pipx for many people. Those CLIs land as shims (often under
`~/.local/bin`) that vole already sees as opaque `local-bin` entries without package or
version.

## Goal

`vole scan` lists tools installed via `uv tool`, with versions, under source id `uv-tool`.

## Open questions

| # | Topic | Status | Decision |
|---|--------|--------|----------|
| 1 | Discovery API? | locked | **`uv tool list --output-format=json` when supported**, else parse **`uv tool list --show-paths`**. Skip if `uv` missing |
| 2 | Source id string? | locked | **`uv-tool`** |
| 3 | Dedup vs pipx and `local-bin`? | locked | **Register after pipx, before `bins`**; union of pipx + uv shim names skipped in `local-bin`. Same package name: pipx wins |
| 4 | Also track `uv python` installs? | locked | **No** — only `uv tool` |

## Done when

- [x] Scan lists `uv tool` installs when uv is present.
- [x] No double-count as `local-bin` for the same shim.
- [x] Tests + README updated.
