# Backlog

Flat task list. Status values: `backlog` | `ready` | `in_progress` | `blocked` | `done` | `cancelled`.

On cleanup, move shipped work to [`CHANGELOG.md`](../CHANGELOG.md) and clean the backlog — see [`CLEANUP.md`](CLEANUP.md).

Reorder freely. Cancel by setting status to `cancelled`. Unexpected work becomes a new task with its own ID.

## Format

Each task:

```markdown
## <task-id>
- status: backlog
- parent: <optional-related-task-id>
- blocked_by: <optional-task-id>
- goal: One sentence
- done_when: Observable acceptance criteria
- notes: Optional one-liner
```

Detail lives in `dev/tasks/<task-id>.md` when needed.

---

## project-naming
- status: done
- goal: Pick a name that works as repo and CLI command.
- done_when: See `dev/tasks/project-naming.md`.
- notes: **vole** — README title and Mole pairing line landed; Homebrew still `homebrew-formula`.

## architecture-review
- status: done
- goal: A recorded verdict on each structural decision, plus ADRs for the ones worth keeping.
- done_when: See `dev/tasks/architecture-review.md`.
- notes: Locked; ADRs 001–006 accepted. Implementation split into follow-up tasks.

## storage-format
- status: done
- goal: Pick the inventory format now that users edit through the CLI, not the file.
- done_when: See `dev/tasks/storage-format.md`.
- notes: JSON chosen. Implementation in `switch-to-json`.

## switch-to-json
- status: done
- goal: Store `software`, `dropped` and `versions` as deterministic pretty-printed JSON, with a one-time migration from TOML.
- done_when: See `dev/tasks/switch-to-json.md`.
- notes: Shipped. TOML/`migrate` support later removed after everyone migrated.

## cli-edit-coverage
- status: done
- goal: CLI covers remaining hand edits: undrop, add, restore, delete; edit works on dropped.
- done_when: See `dev/tasks/cli-edit-coverage.md`.
- notes: Shipped. Rename/merge deferred (OQ2).

## python-only-restructure
- status: done
- blocked_by: project-naming, switch-to-json
- goal: One `vole` Python package with pluggable sources/signals; drop the shell half.
- done_when: See `dev/tasks/python-only-restructure.md`.
- notes: Shipped. `python3 -m vole`; data in `~/.config/vole/`; shell half removed.

## curl-install
- status: done
- goal: `curl …/install.sh | sh` installs the `vole` CLI.
- done_when: See `dev/tasks/curl-install.md`.
- notes: `install.sh` fetches `main` (or copies a local checkout); launcher in `~/.local/bin`.

## cli-restructure
- status: done
- goal: Explicit subcommands: help by default, `scan` / `scan --dry-run`, `reset`, archive-on-drop; drop `prune-dropped`.
- done_when: See `dev/tasks/cli-restructure.md`.
- notes: Shipped. Archive-on-edit; no prune; bare `vole` is help.

## pre-release-review
- status: done
- goal: Fix or consciously defer every finding from the pre-v0.1.0 code review (dead code, Intel Caskroom path, broken ADR links, exec bits, privacy note, untested audit core).
- done_when: See `dev/tasks/pre-release-review.md`.
- notes: Closed for `v0.1.0`. Deferred to Homebrew: 2.2 (README brew-first), 4.11 (formula uses `python3 -m vole` / same `main`). Task docs kept for now.

## homebrew-formula
- status: ready
- goal: Users can install vole via a personal Homebrew tap (not core).
- done_when: See `dev/tasks/homebrew-formula.md`.
- notes: Formula + tap README written locally for `v0.1.2`; vole README brew-first. Push tap + CLT update needed before `brew install` smoke on this machine.

## scan-auto-archive
- status: done
- goal: Default-on scan archives gone entries; manual drop is sticky (no auto-reappear).
- done_when: See `dev/tasks/scan-auto-archive.md`.
- notes: Shipped — `archived_by` user\|scan; missing non-sticky; write scan moves; dry-run suggests.

## source-sdkman
- status: backlog
- goal: Discover SDKMAN!-managed SDKs (Java, Groovy, Kotlin, …) under `~/.sdkman/candidates`.
- done_when: See `dev/tasks/source-sdkman.md`.
- notes: OQs open — filesystem walk proposed; after asdf for first-wins.

## source-intellij-jdks
- status: backlog
- goal: Discover JDKs installed by IntelliJ’s built-in Download JDK (not SDKMAN).
- done_when: See `dev/tasks/source-intellij-jdks.md`.
- notes: OQs open — likely `~/Library/Java/JavaVirtualMachines/`; skip bundled JBR.

## source-cargo
- status: done
- goal: Discover `cargo install` CLIs (`~/.cargo/bin`).
- done_when: See `dev/tasks/source-cargo.md`.
- notes: Shipped — `--list` package names; `~/.cargo/bin` fallback; brew first-wins.

## source-pipx
- status: done
- goal: Discover pipx-managed Python CLIs with versions.
- done_when: See `dev/tasks/source-pipx.md`.
- notes: Shipped — `pipx list --json`; skips pipx shims in `local-bin`.

## source-uv
- status: done
- goal: Discover `uv tool install` CLIs with versions.
- done_when: See `dev/tasks/source-uv.md`.
- notes: Shipped — `uv-tool`; after pipx, before bins; JSON or `--show-paths`.

## source-yarn
- status: done
- goal: Discover Yarn classic global packages.
- done_when: See `dev/tasks/source-yarn.md`.
- notes: Shipped — classic NDJSON; Berry no-op; after npm, before pnpm.

## source-pnpm
- status: done
- goal: Discover pnpm global packages.
- done_when: See `dev/tasks/source-pnpm.md`.
- notes: Shipped — `pnpm list -g --json`; after npm for first-wins.

## source-asdf
- status: done
- goal: Discover asdf-managed runtimes (mise-alike).
- done_when: See `dev/tasks/source-asdf.md`.
- notes: Shipped — `asdf list`; mise registered first for first-wins.

## python-39-floor
- status: done
- goal: The test suite runs on `/usr/bin/python3` (3.9), with `tomllib` assertions skipped there.
- done_when: `/usr/bin/python3 -m unittest discover -s tests` passes; same command on 3.11+ still runs every test.
- notes: Fell out of `switch-to-json`: the rewritten tests import `tomllib` only optionally.

## inventory-check
- status: done
- goal: Scan warns on inventory entry shape problems; no dedicated check command.
- done_when: See `dev/tasks/inventory-check.md`.
- notes: Shipped — `keep` free-form; unknown status/fields and bad versions types warn on scan.

## first-public-pass
- status: done
- goal: Every file reads as written for a stranger, with no private detail.
- done_when: See `dev/tasks/first-public-pass.md`.
- notes: README rewritten; rough-edge inventory scrubbed. Author still reviews real examples before publish.

## choose-a-licence
- status: done
- goal: Add a LICENSE file before the first public commit.
- done_when: LICENSE present and referenced from README.
- notes: Apache-2.0 confirmed; linked from README Install section.

## report-mode-creates-the-file
- status: done
- goal: `--report` leaves the filesystem untouched in every case.
- done_when: See `dev/tasks/report-mode-creates-the-file.md`.
- notes: Fixed in the restructure — `--report` with no inventory exits 1 and writes nothing.
