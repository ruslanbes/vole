# Release runbook

Related: [CHANGELOG.md](../CHANGELOG.md), [CLEANUP.md](CLEANUP.md)

## When to release

Cut a release when:

- [CHANGELOG.md](../CHANGELOG.md) `[Unreleased]` contains a significant work chunk.
- Project tests / build (and CI on the default branch, if any) are green.

Ad-hoc changelog updates without a version tag are fine anytime; this runbook is for **promoting `[Unreleased]` → `[X.Y.Z]`**, bumping any other version sources this project uses, and tagging. Promote and delete finished task artifacts with [CLEANUP.md](CLEANUP.md) first if needed.

## Pre-release checklist

<!-- Replace with this repo’s real commands. -->

- [ ] Tests pass.
- [ ] Build / package (if any) succeeds.
- [ ] Manual smoke checks for user-facing changes (if applicable).

## Finalize the changelog

Edit [CHANGELOG.md](../CHANGELOG.md):

1. Review `[Unreleased]` — group under **Added** / **Changed** / **Removed** / **Fixed** (Keep a Changelog).
2. Add a new dated section, e.g. `## [0.2.0] - YYYY-MM-DD`.
3. Move items from `[Unreleased]` into that section.
4. Leave `[Unreleased]` empty (or with a placeholder comment) for the next cycle.
5. Rephrase for **readers of the repo** — user-facing behavior, not internal implementation trivia. Link ADRs or other project docs where useful.
6. Do **not** add a “Completed task specs” line under Removed.

## Bump the version

Set `__version__` in [`vole/__init__.py`](../vole/__init__.py) to `X.Y.Z` (no `v` prefix).
It is the only version source; `vole --version` and the Homebrew formula `test do` read it.

```sh
python3 -m vole --version   # → vole X.Y.Z
```

## Execute the release

1. Stage the changes.
2. Publish:

```sh
git commit -m "Release X.Y.Z"
git tag -a vX.Y.Z -m "Release X.Y.Z"
git push origin HEAD --tags
```

Pushing a `v*` tag runs [`.github/workflows/release.yml`](../.github/workflows/release.yml):
tests on Python 3.9 and 3.12, checks `__version__` matches the tag (without the `v`), then
creates a GitHub Release (source archives are attached automatically — what Homebrew needs).

<!-- Adjust branch name and deploy verification for this project. -->
