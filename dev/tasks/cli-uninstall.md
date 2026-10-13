# `vole uninstall` — source-specific uninstallers

- **Task ID:** `cli-uninstall`
- **Status:** backlog
- **Related:** sources registry, `drop` / `purge`, DROP CANDIDATES, `versions.json` source id

## Problem

Vole tells you what to drop or keep, but uninstalling is still a manual, source-by-source
chore (`brew uninstall`, `pipx uninstall`, drag `.app` to Trash, …). After a DROP CANDIDATE
or a intentional cleanup, the user leaves the CLI to remove the bits from the machine.
That gap is large and easy to get wrong (wrong formula name, cask vs formula, leftover
shims).

## Goal

A high-level **`vole uninstall NAME`** (exact verb TBD) that:

1. Resolves the install **source** from `versions.json` (live) or dropped provenance.
2. Invokes a **source-specific uninstaller** (brew, pipx, cargo, app, …).
3. Updates inventory afterward (likely archive / purge — see OQs).

**Not for the current release.** This is a multi-source, multi-OQ project; ship only when
source coverage and safety rules are locked.

## Open questions

| # | Topic | Status | Decision |
|---|--------|--------|----------|
| 1 | Command name? | open | **`uninstall`** vs keep inventory `drop` separate. Possible later: **rename `drop` → `uninstall`** for the archive-only verb, or make `uninstall` mean “remove from machine + archive” and keep/repurpose `drop` — decide when designing the UX |
| 2 | Relation to `drop` / `purge`? | open | Uninstall-from-disk vs archive-only vs permanent inventory wipe must not collide. Proposal sketch: uninstall = machine remove (+ auto-archive?); `drop` stays sticky ignore without uninstalling; `purge` stays inventory-only erase |
| 3 | Source coverage (v1)? | open | Which sources get real uninstallers first (brew / cask / pipx / …)? Unsupported source → refuse with a clear message |
| 4 | Dry-run / confirm? | open | Always confirm? `--force`? `--dry-run` prints the exact shell/API action? |
| 5 | Failure / partial uninstall? | open | Inventory update only after successful uninstall? Leave machine state alone on failure |
| 6 | Only-in-versions / not tracked? | open | Allow uninstall from versions row alone, or require a software/dropped entry? |
| 7 | Apps / Steam / bins? | open | Many sources have no clean CLI uninstall — Trash? refuse? best-effort? |

## Non-goals (for now)

- Not implementing any uninstaller in the current version.
- Not auto-uninstalling DROP CANDIDATES on scan.
- Not renaming `drop` / `dropped.json` / DROP CANDIDATES wording until OQ1 is locked.
- Not a package-manager GUI or privileged system uninstallers beyond what each source already exposes.

## Implementation (sketch)

- Per-source `uninstall(ctx, name) -> Result` (or similar) beside `discover`, registered like sources.
- CLI resolves source from versions (active) or entry `source` (dropped), dispatches, then inventory step.
- Split into follow-up tasks per source once OQs lock (e.g. `uninstall-brew`, `uninstall-pipx`).

## Done when

- [ ] OQs locked; follow-up tasks filed if this stays an epic.
- [ ] At least one source path works end-to-end with confirm/dry-run as decided.
- [ ] Unsupported sources refuse safely; inventory rules vs `drop`/`purge` documented.
- [ ] README / CHANGELOG updated; naming decision (`drop` rename or not) applied consistently.

## Notes

- Product language today: **drop** = archive / sticky ignore; **purge** = wipe inventory row. Uninstall would be the third axis: **remove from the machine**.
- If `drop` is later renamed to `uninstall`, DROP CANDIDATES / `dropped.json` need an explicit rename-or-keep plan — do not treat that as a drive-by.
