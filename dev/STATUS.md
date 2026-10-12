# Status

Last updated: 2026-10-12

## Current focus

`v0.1.2` prepared (push CI + brew test fix). Tag after commit so the release workflow runs.

## Active task

_None._ Next after a successful GitHub Release: `homebrew-formula`.

## Blockers

_None._

## Next action

1. Commit `__version__` / CHANGELOG / test fix / `.github/workflows/test.yml` / STATUS (task docs kept).
2. `git push origin HEAD` first, then `git tag -a v0.1.2 -m "Release 0.1.2"` and `git push origin v0.1.2`.
3. Confirm Tests (on push) and Release (on tag) both green, then `homebrew-formula`.

## Session notes

- 2026-10-12: `v0.1.1` tag ran but release tests failed (brew mock). Prepared `0.1.2` with push/PR Tests workflow and the mock fix. Push commit before tagging so the workflow is registered.
- 2026-10-12: `v0.1.0` tagged (no workflow yet). `0.1.1` added tag-triggered GitHub Releases. Task docs not cleaned.
- 2026-10-11: `cli-restructure` done — help default, `scan`/`--dry-run`, `reset`,
  archive-on-edit; removed `prune-dropped` / `clean` / top-level `--report`.
- 2026-10-10: `curl-install` done — `install.sh` → `~/.local/share/vole` + `~/.local/bin/vole`.
- 2026-10-09: Dropped `migrate` and all TOML inventory code/fixtures/tests — JSON only.
