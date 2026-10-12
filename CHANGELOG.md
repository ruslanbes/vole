# Changelog

All notable changes to this project. Format based on [Keep a Changelog](https://keepachangelog.com/).

## [Unreleased]

### Added

- Homebrew install via `brew install ruslanbes/vole/vole`.
- Steam source: installed games.

### Changed

- KEEP header shortened.

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
