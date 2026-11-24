# `vole autoscan` — scheduled background scans

- **Task ID:** `cli-autoscan`
- **Status:** done
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
vole autoscan schedule            # print current schedule; change nothing
vole autoscan schedule weekly     # set schedule and turn on
vole autoscan schedule monthly
vole autoscan schedule "every 3 days"
vole autoscan schedule "every 10 minutes"
```

When autoscan is **on**, bare `vole autoscan` prints at least: on/off, the schedule
string, and the **next run** time. When **off**, print that clearly (schedule may still
be stored for the next `on`).

## Open questions

| # | Topic | Status | Decision |
|---|--------|--------|----------|
| 1 | Scheduler backend? | locked | User LaunchAgent (`launchd`) — macOS-native, survives reboot. Not cron in v1 |
| 2 | Free-form schedule parsing? | locked | Yes — accept phrases like `weekly` / `monthly` / `every N days\|hours\|minutes`. Refuse unclear input with examples. Exact grammar TBD (library-free parser) |
| 3 | Default schedule when `on` with none set? | locked | `weekly` |
| 4 | One-shot enable + schedule? | locked | `vole autoscan schedule` with no args prints the current schedule and changes nothing. Passing a schedule **sets on implicitly** (no `on --schedule`) |
| 5 | What does a scheduled run execute? | locked | Write-mode `vole scan` (same as interactive). No dry-run agent in v1 |
| 6 | Where is state stored? | locked | `~/.config/vole/autoscan.json` (on/off, schedule string, last/next as needed) + LaunchAgent plist vole owns (`~/Library/LaunchAgents/…`) |
| 7 | How is “next run” computed? | locked | From schedule + last run (and/or launchd timing). Status shows **local** time |
| 8 | Output / notifications on scheduled scan? | locked | Log file only — **no Notification Center**. Location: `~/Library/Logs/vole/autoscan.log` (keeps scan noise out of the curated data dir; macOS-conventional for agents) |
| 9 | Path to `vole` in the agent? | locked | Pin absolute path at `on` / `schedule <expr>` time (brew Cellar / `~/.local/bin` / `which`). Warn if binary moves |
| 10 | Interaction with `VOLE_DATA_DIR`? | locked | Pin the data dir in effect when enabling (`--data-dir` / `$VOLE_DATA_DIR`) into the agent so scheduled scans use that inventory |

## Non-goals

- Not a GUI or menu-bar app.
- Not cloud sync / remote triggers.
- Not auto-uninstall or auto-`drop` from DROP CANDIDATES.
- Not Linux/cron support in v1 (macOS only, like the rest of vole).
- Not parsing full cron expressions unless free-form proves insufficient.

## Implementation (sketch)

- CLI subparser `autoscan` with optional subcommands `on` / `off` / `schedule`.
- Bare `autoscan` → status printer; bare `schedule` → print schedule only.
- Schedule parser → normalized interval or calendar rule → LaunchAgent plist fields.
- `on` installs/loads agent; `off` unloads/disables; `schedule <expr>` rewrites plist + state and turns on; scheduled job runs write-mode `vole scan`.
- Status reads state file + best-effort next fire time from launchd or computed locally.

## Done when

- [x] `vole autoscan` / `on` / `off` / `schedule …` work entirely from the CLI.
- [x] Free-form schedules covering weekly, monthly, every N days/hours/minutes (as locked).
- [x] Status shows on/off; when on, schedule + next run.
- [x] Scheduled runs invoke write-mode scan (or whatever OQ5 locks) without user interaction.
- [x] README + PRIVACY note if the agent/log surface expands what vole touches.
- [x] Tests for schedule parsing + status shape; agent install smoke-tested on macOS.

## Notes

- Pair with DROP CANDIDATES / `last_used`: background scan keeps staleness current without nagging the user to remember `scan`.
- Keep agent identity stable (label like `com.ruslanbes.vole.autoscan`) so `off`/`on` are idempotent.
- Implementation: `vole/autoscan.py`; agent entry `vole autoscan run` (hidden); test hooks `VOLE_AUTOSCAN_SKIP_LAUNCHCTL` / `_LOG` / `_PLIST`.
