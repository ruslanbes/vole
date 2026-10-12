# Status

Last updated: 2026-10-12

## Current focus

`v0.1.1` prepared (auto-release workflow). Tag after commit so the workflow runs.

## Active task

_None._ Next after tag: `homebrew-formula` (needs a GitHub release archive for `url`/`sha256`).

## Blockers

_None._

## Next action

1. Commit `__version__` / CHANGELOG / `.github/workflows/release.yml` / `dev/RELEASE.md` (task docs kept).
2. `git tag -a v0.1.1 -m "Release 0.1.1"` and `git push origin HEAD --tags`.
3. Confirm the Release workflow created the GitHub Release, then `homebrew-formula`.

## Session notes

- 2026-10-12: `v0.1.0` tagged (no workflow yet). Prepared `0.1.1` for tag-triggered GitHub Releases. `scan-auto-archive`, `drop`, keep wording, `audit`→`scan` already in `0.1.0`. Task docs not cleaned.
- 2026-10-11: `cli-restructure` done — help default, `scan`/`--dry-run`, `reset`,
  archive-on-edit; removed `prune-dropped` / `clean` / top-level `--report`.
- 2026-10-10: `curl-install` done — `install.sh` → `~/.local/share/vole` + `~/.local/bin/vole`.
- 2026-10-09: Dropped `migrate` and all TOML inventory code/fixtures/tests — JSON only.
