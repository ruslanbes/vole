# Status

Last updated: 2026-10-13

## Current focus

Prepare / cut `v0.2.0` (changelog + version bumped; task cleanup deferred).

## Active task

_None — release prep._

## Blockers

_None._

## Next action

1. Review unstaged `CHANGELOG.md` + `vole/__init__.py` (`0.2.0`).
2. Commit when ready: `Release 0.2.0`, then `git tag -a v0.2.0` and push with tags (see `dev/RELEASE.md`).
3. Update Homebrew tap formula URL/sha for `v0.2.0` after the GitHub Release exists.
4. Cleanup done task docs later (`dev/CLEANUP.md`) — skipped for this cut.

## Session notes

- 2026-10-13: Prepared `0.2.0` — migrations/format 2, why/keep/get, purge, no user-facing edit, Steam, last_used, case-insensitive sort. Task docs not cleaned.
- 2026-10-12: `v0.1.1` tag ran but release tests failed (brew mock). Prepared `0.1.2` with push/PR Tests workflow and the mock fix. Push commit before tagging so the workflow is registered.
- 2026-10-12: `v0.1.0` tagged (no workflow yet). `0.1.1` added tag-triggered GitHub Releases. Task docs not cleaned.
- 2026-10-11: `cli-restructure` done — help default, `scan`/`--dry-run`, `reset`,
  archive-on-edit; removed `prune-dropped` / `clean` / top-level `--report`.
- 2026-10-10: `curl-install` done — `install.sh` → `~/.local/share/vole` + `~/.local/bin/vole`.
- 2026-10-09: Dropped `migrate` and all TOML inventory code/fixtures/tests — JSON only.
