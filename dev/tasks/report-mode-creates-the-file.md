# `--report` must not create software.toml

- **Task ID:** `report-mode-creates-the-file`
- **Status:** done — fixed by `python-only-restructure`: `--report` errors if there is no inventory and creates nothing

## Problem

`--report` documents itself as "report only, never writes", and the whole version-baseline design
depends on that: `--report` is the preview you run *before* letting a scan consume the diff. But
`audit-software.sh` creates the inventory before it checks the mode:

```sh
[ -f "$DATA" ] || { printf '{\n  "format": 1,\n  "apps": {}\n}\n' > "$DATA"; echo "created $DATA" >&2; }
```

(Since `switch-to-json` the file is `software.json`; the bug is unchanged.)

So the first `--report` on a machine with no inventory writes one. Observed on 2026-10-06 while
verifying a fresh checkout.

## Goal

`--report` leaves the filesystem untouched in every case, and says something useful when there is
no inventory yet.

## Open questions

| # | Topic | Status | Decision |
|---|--------|--------|----------|
| 1 | With no inventory, should `--report` exit non-zero (a scripting-friendly error) or zero with a hint? | open | |

## Non-goals

- Not a wider rework of mode dispatch — that belongs to `architecture-review`.

## Implementation

The naive fix breaks the other path: `_audit.py` opens the file unconditionally, so simply
guarding the creation makes `--report` crash on a missing file instead. Either hand the helper an
empty inventory in memory, or check for the file in report mode and exit early with a message
pointing at a plain `./audit-software.sh`.

## Done when

- [ ] `--report` against a directory with no `software.toml` creates nothing.
- [ ] It explains what to run instead rather than raising a traceback.
- [ ] A test covers it — currently no test runs the shell script at all.

## Notes

Small, but it is a correctness bug in the one mode whose entire purpose is being side-effect free,
in a tool about to be public.
