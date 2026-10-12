# Restructure into a Python-only `vole` package

- **Task ID:** `python-only-restructure`
- **Status:** done
- **Parent / blocked by:** blocked by `project-naming` and `switch-to-json`; implements ADRs 002 + 006

## Problem

Shell enumeration + `_audit.py` script dispatch cannot grow new sources cleanly or ship as one
`vole` command.

## Goal

A `vole` Python package with argparse CLI, `sources/` + `signals/` registries, inventory helpers
imported as a module, and no required shell half. Behaviour preserved; tests cover discovery
fixtures and extracted version-diff.

## Open questions

| # | Topic | Status | Decision |
|---|--------|--------|----------|
| 1 | Data-file location? | locked | **`~/.config/vole/`** for every install method, for now. Replaces "next to the tool" |
| 2 | Keep a thin `audit-software.sh` shim during transition? | locked | **No.** `audit-software.sh` is deleted; `vole` is the only entrypoint |
| 3 | How do existing data files next to the tool reach `~/.config/vole/`? | locked | **`vole migrate` moves them** into `~/.config/vole/`, with the same refuse-to-overwrite rule as the TOML→JSON conversion |

## Non-goals

- Not adding new sources or Mole integration in this task.
- Not the curl/brew packaging itself (`curl-install`, `homebrew-formula`).

## Done when

- [x] `python -m vole` / `bin/vole` runs scan, `--report`, `list`, `edit`, `prune-dropped`, `migrate`.
- [x] `audit-software.sh` and `_audit.py` deleted; README and help text only show `vole`.
- [x] Data files read from and written to `~/.config/vole/` (`$VOLE_DATA_DIR` override); created on first write.
- [x] ADR-007 updated for the new location.
- [x] At least one source and one signal unit-tested without a live machine scan (`bins`, `ollama`, `shell_history`).
- [x] Version diff is a tested helper (`vole.versions.diff`).
- [x] `END OF HELPERS` exec hack gone.
- [x] ADRs 002/006 reflected in `dev/README.md`.

## Notes

Target shape: `dev/tasks/architecture-review.md` → Target architecture.
