# Source: pipx

- **Task ID:** `source-pipx`
- **Status:** done
- **Related:** `bins` already sees many pipx shims in `~/.local/bin`; `source-uv` is the competing tool installer

## Problem

pipx is the usual way to install Python CLIs globally (`httpie`, `poetry`, `ansible`, …).
vole already lists the shim names under `local-bin`, but without the package identity or
version pipx knows.

## Goal

`vole scan` lists pipx-managed apps with versions under source id `pipx`, preferring pipx’s
identity over a bare `local-bin` hit for the same binary name when both would apply.

## Open questions

| # | Topic | Status | Decision |
|---|--------|--------|----------|
| 1 | Discovery API? | locked | **`pipx list --json`** when `pipx` is on PATH; skip silently if missing |
| 2 | Entry name = package or exposed binary? | locked | **Package name** from pipx (one entry per venv/app) |
| 3 | Dedup vs `local-bin`? | locked | **Register pipx before `bins.discover`**, and skip `local-bin` names that pipx exposes as binaries so shims are not double-counted |
| 4 | Include pipx itself if installed via brew? | locked | **No special case** — brew owns the `pipx` formula; this source only lists *apps installed through* pipx |

## Done when

- [x] Scan lists pipx apps with versions when pipx is installed.
- [x] Same binary is not also reported as `local-bin` when pipx owns it.
- [x] Tests + README updated.
