# Changelog

All notable changes to this project. Format based on [Keep a Changelog](https://keepachangelog.com/).

## [Unreleased]

## [0.2.0] - 2026-10-13

### Added

- Homebrew install via `brew install ruslanbes/vole/vole`.
- Steam source: installed games.
- Persist `last_used` per inventory entry across scans (only advances on newer dated signals).
- `vole why NAME` — print or set why.
- `vole keep NAME "…"` — set keep (write only).
- `vole get NAME` — show all stored fields for one entry (plus versions row; no scan).
- Inventory migration framework (`vole migrate` / auto on load); each step bumps `format` ([ADR-008](docs/adr/adr-008-inventory-format-versioning.md)).

### Changed

- KEEP header and DROP CANDIDATES wording shortened; shell history also reads bash with a bounded mtime guess for untimestamped lines.
- Active `software.json` entries no longer store `source` (lives on `versions.json`; copied onto dropped at archive time). Inventory format **1→2**. `vole add` no longer takes `--source`.
- `list` and `scan` name lists sort case-insensitively (same order as on-disk inventory).
- Renamed `vole delete` → `vole purge` (permanent remove; `drop` remains archive / sticky ignore).

### Removed

- User-facing `vole edit`; use `why` / `keep` / `drop` / `restore`.

## [0.1.2] - 2026-10-12

### Added

- GitHub Actions test workflow.

### Fixed

- Brew discover unit test no longer fails on Linux CI when resolving the Caskroom.

## [0.1.1] - 2026-10-12

### Added

- GitHub Actions release workflow.

## [0.1.0] - 2026-10-12

### Added

- Initial product version: macOS CLI that scans installed software and records why each piece is there.
- Sources: Homebrew formulae and casks, Applications, cargo, pipx, uv tool, npm/yarn/pnpm globals, asdf, mise, ollama, `~/.local/bin`.
- Usage signals: shell history (zsh, fish), Spotlight last-used, Library app-state mtimes, config-file references.
- Commands: `scan` / `scan --dry-run`, `list`, `edit`, `add`, `restore`, `delete`, `reset`, `--version`.
- Inventory in `~/.config/vole/` (`software.json`, `dropped.json`, `versions.json`).
- Install via `install.sh` (curl or local checkout). Homebrew tap planned separately.
