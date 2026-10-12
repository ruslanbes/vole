# Curl install script

- **Task ID:** `curl-install`
- **Status:** done
- **Parent / blocked by:** <!-- python-only-restructure done -->
- **Related:** ADR-005

## Problem

Clone-only install is too heavy as the secondary path beside Homebrew.

## Goal

`curl -fsSL <raw-github-url>/install.sh | sh` installs the `vole` CLI on PATH and prints how to
run the first scan.

## Open questions

| # | Topic | Status | Decision |
|---|--------|--------|----------|
| 1 | Install from GitHub release tarball or pin to a tag vs main? | locked | **`main`** — same pattern as Mole and Homebrew's own installer (`…/main/install.sh` / `HEAD`) |
| 2 | Default inventory path for curl installs? | locked | `~/.config/vole/` — same as brew, decided in `python-only-restructure` |

## Non-goals

- Not a Homebrew formula (see `homebrew-formula`).
- Not pinning to release tags for the first ship (can revisit later if needed).

## Done when

- [x] `install.sh` in-repo, documented in README.
- [x] Idempotent enough to re-run safely.
- [x] Works with only the Command Line Tools `/usr/bin/python3` (3.9) — no pip, no extra Python.
