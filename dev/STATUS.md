# Status

Last updated: 2026-10-12

## Current focus

`v0.1.0` ready to tag. Next product work: `homebrew-formula`.

## Active task

_None._ Next: `homebrew-formula` (needs the tagged release for `url`/`sha256`).

## Blockers

_None for the tag._ Homebrew still needs the GitHub release archive after push.

## Next action

1. Commit the product tree (task docs kept on purpose for now).
2. `git tag -a v0.1.0 -m "Release 0.1.0"` and push with `--tags`.
3. Implement `homebrew-formula` against the tagged archive.

## Session notes

- 2026-10-12: `pre-release-review` closed for the tag — B/S items fixed; 2.2 and 4.11 deferred to Homebrew; 1.10 / 4.10 won't fix. Version `0.1.0`, changelog promoted. Task docs not cleaned yet.
- 2026-10-11: `cli-restructure` done — help default, `scan`/`--dry-run`, `reset`,
  archive-on-edit; removed `prune-dropped` / `clean` / top-level `--report`.
- 2026-10-10: `curl-install` done — `install.sh` → `~/.local/share/vole` + `~/.local/bin/vole`.
- 2026-10-09: Dropped `migrate` and all TOML inventory code/fixtures/tests — JSON only.
