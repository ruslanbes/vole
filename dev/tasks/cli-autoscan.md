# `vole autoscan` — scheduled background scans

- **Task ID:** `cli-autoscan`
- **Status:** backlog
- **Related:** `scan`, privacy (local-only), macOS launchd / scheduling

## Problem

Inventory drifts between manual `vole scan` runs. Users who want vole to stay current
must remember to scan (or wire cron/launchd themselves). There is no first-class way to
turn periodic scanning on/off or set a human schedule from the CLI.

## Goal

A writeable, inspectable autoscan control surface — **all from the command line**:

```sh
vole autoscan                     # status (if on: schedule + next run)
vole autoscan on                  # enable (uses current / default schedule)
vole autoscan off                 # disable
vole autoscan schedule weekly     # free-form schedule
vole autoscan schedule monthly
vole autoscan schedule "every 3 days"
vole autoscan schedule "every 10 minutes"
```

Combinations that should work without a TUI, e.g.:

```sh
vole autoscan on
vole autoscan schedule weekly
# or enable + set in one shot if we allow:
vole autoscan on --schedule weekly   # OQ
```

When autoscan is **on**, bare `vole autoscan` prints at least: on/off, the schedule
string, and the **next run** time. When **off**, print that clearly (schedule may still
be stored for the next `on`).

## Open questions

| # | Topic | Status | Decision |
|---|--------|--------|----------|
| 1 | Scheduler backend? | open | **Proposal:** user LaunchAgent (`launchd`) — macOS-native, survives reboot. Not cron unless we need Linux later |
| 2 | Free-form schedule parsing? | open | Accept phrases like `weekly` / `monthly` / `every N days|hours|minutes`. Refuse unclear input with examples. Exact grammar TBD (library-free parser) |
| 3 | Default schedule when `on` with none set? | open | **Proposal:** `weekly` (or refuse `on` until `schedule` is set) |
| 4 | One-shot enable + schedule? | open | **Proposal:** allow `vole autoscan on --schedule "…"` and/or `schedule` implies keep current on/off |
| 5 | What does a scheduled run execute? | open | **Proposal:** write-mode `vole scan` (same as interactive). Optional later: `--dry-run` only — not v1 |
| 6 | Where is state stored? | open | **Proposal:** small file under `~/.config/vole/` (e.g. `autoscan.json`: on/off, schedule string, last/next) + LaunchAgent plist vole owns |
| 7 | How is “next run” computed? | open | From schedule + last run (or launchd NextCalendarInterval / StartInterval). Show local time in status |
| 8 | Output / notifications on scheduled scan? | open | **Proposal v1:** log to a file under the data dir (or `~/Library/Logs/vole/`); no Notification Center yet |
| 9 | Path to `vole` in the agent? | open | Pin absolute path at `on` time (brew Cellar / `~/.local/bin` / which). Warn if binary moves |
| 10 | Interaction with `VOLE_DATA_DIR`? | open | Agent should pass the same data dir the user used when enabling, or always default `~/.config/vole/` |

## Non-goals

- Not a GUI or menu-bar app.
- Not cloud sync / remote triggers.
- Not auto-uninstall or auto-`drop` from DROP CANDIDATES.
- Not Linux/cron support in v1 (macOS only, like the rest of vole).
- Not parsing full cron expressions unless free-form proves insufficient.

## Implementation (sketch)

- CLI subparser `autoscan` with optional subcommands `on` / `off` / `schedule`.
- Bare `autoscan` → status printer.
- Schedule parser → normalized interval or calendar rule → LaunchAgent plist fields.
- `on` installs/loads agent; `off` unloads/disables; `schedule` rewrites plist + state file.
- Status reads state file + best-effort next fire time from launchd or computed locally.

## Done when

- [ ] `vole autoscan` / `on` / `off` / `schedule …` work entirely from the CLI.
- [ ] Free-form schedules covering weekly, monthly, every N days/hours/minutes (as locked).
- [ ] Status shows on/off; when on, schedule + next run.
- [ ] Scheduled runs invoke write-mode scan (or whatever OQ5 locks) without user interaction.
- [ ] README + PRIVACY note if the agent/log surface expands what vole touches.
- [ ] Tests for schedule parsing + status shape; agent install smoke-tested on macOS.

## Notes

- Pair with DROP CANDIDATES / `last_used`: background scan keeps staleness current without nagging the user to remember `scan`.
- Keep agent identity stable (label like `com.ruslanbes.vole.autoscan`) so `off`/`on` are idempotent.
