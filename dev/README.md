# Development

How this project is run: setup, ground rules, cleanup, release, and current work tracking.

## What this is

A CLI that answers one question for everything installed on a Mac: **why is this here?** It
records the reason at install time and flags things whose justification has gone quiet.
User-facing documentation is in the root [`README.md`](../README.md).

## Local setup

No build, no third-party deps. macOS plus **Python 3.9+** (the Command Line Tools
`/usr/bin/python3` is enough).

```sh
python3 -m vole scan --dry-run           # scan and report, never writes
python3 -m unittest discover -s tests
/usr/bin/python3 -m unittest discover -s tests   # check the 3.9 floor
```

Package layout: `vole/` with `sources/` (discovery) and `signals/` (usage facts). Data in
`~/.config/vole/` (or `$VOLE_DATA_DIR`). See [`docs/adr/`](../docs/adr/).

## Ground rules

- Track work here in `dev/` — flat backlog, status, optional task docs under `tasks/<kebab-id>.md`.
- Work one task at a time.
- Before implementing, lock the open questions in the task doc rather than guessing.
- **The data files are the product.** `~/.config/vole/software.json` / `dropped.json` hold
  hand-written reasoning. Anything that writes them goes through `inventory.save`
  (deterministic, atomic): rewriting unchanged data must be byte-identical. Schema changes
  follow [ADR-008](../docs/adr/adr-008-inventory-format-versioning.md): optional fields that
  need no rewrite do not bump; any registered migration bumps `format` by 1.
- **Python-only CLI** — no shell enumerator.
  New install routes go under `vole/sources/`; new usage signals under `vole/signals/`.
- **Zero third-party dependencies.** Stdlib only; Python floor 3.9+.
- **macOS-only** core; optional Mole extras must not be required for a scan.
- **`scan --dry-run` never writes.** Write-mode scan archives gone installs and restores
  non-sticky reinstalls; `keep` suppresses staleness only; missing reasons still surface.
  Manual `drop` is sticky (`archived_by: user`).
- Use [Mermaid](https://mermaid.js.org/) for diagrams.
- When cleaning finished work, follow [`CLEANUP.md`](CLEANUP.md). When cutting a version,
  [`RELEASE.md`](RELEASE.md).

## What's in this folder

| Doc | Role | Lifetime |
|-----|------|----------|
| [`README.md`](README.md) (this file) | Setup, ground rules, doc index | Durable |
| [`CLEANUP.md`](CLEANUP.md) | Promote durable content; remove finished tasks | Durable |
| [`RELEASE.md`](RELEASE.md) | Version changelog, tag | Durable |
| [`BACKLOG.md`](BACKLOG.md) | Flat task index | Living |
| [`STATUS.md`](STATUS.md) | Current focus / blockers / session notes | Living |
| [`tasks/`](tasks/) | Optional detail file per task | Temporary |

## Reference docs

| Doc | Role |
|-----|------|
| [`README.md`](../README.md) | User-facing documentation |
| [`docs/adr/`](../docs/adr/) | Architecture Decision Records |
| [`CHANGELOG.md`](../CHANGELOG.md) | Shipped user-facing history |
