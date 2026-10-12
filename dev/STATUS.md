# Status

Last updated: 2026-10-12

## Current focus

`homebrew-formula` — local `Formula/vole.rb` for `v0.1.2`; push tap and smoke-test install.

## Active task

`homebrew-formula`

## Blockers

_None._

## Next action

1. Update Command Line Tools (Xcode 27) — local `brew install` is blocked until then.
2. Commit + push `ruslanbes/homebrew-vole` (`Formula/vole.rb`, tap README).
3. `brew install ruslanbes/vole/vole` / `brew test vole` / `vole --version`.
4. Commit vole README + CHANGELOG Unreleased (task docs kept).

## Session notes

- 2026-10-12: `v0.1.1` tag ran but release tests failed (brew mock). Prepared `0.1.2` with push/PR Tests workflow and the mock fix. Push commit before tagging so the workflow is registered.
- 2026-10-12: `v0.1.0` tagged (no workflow yet). `0.1.1` added tag-triggered GitHub Releases. Task docs not cleaned.
- 2026-10-11: `cli-restructure` done — help default, `scan`/`--dry-run`, `reset`,
  archive-on-edit; removed `prune-dropped` / `clean` / top-level `--report`.
- 2026-10-10: `curl-install` done — `install.sh` → `~/.local/share/vole` + `~/.local/bin/vole`.
- 2026-10-09: Dropped `migrate` and all TOML inventory code/fixtures/tests — JSON only.
