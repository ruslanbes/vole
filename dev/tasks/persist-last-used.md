# Persist last-used dates across scans

- **Task ID:** `persist-last-used`
- **Status:** done
- **Related:** staleness / DROP CANDIDATES (`scan.py` classify), PRIVACY.md, ADR-008

## Problem

Usage signals are recomputed every scan from live sources and **never saved**. Inventory only
keeps hand-written fields (`why` / `keep` / …). If shell history rotates (HISTSIZE / new
machine / truncated file) or Spotlight forgets a date, tomorrow’s scan can report
“no usage signal at all” for a tool that was clearly used last week.

That makes DROP CANDIDATES brittle: activity evidence is only as durable as the OS history
files vole happens to still see.

## Goal

Record a **last-used** date per inventory entry (and keep it across scans):

- Each write-mode scan merges live dated signals into the stored value.
- **Update** only when a newly observed date is **strictly newer** than the stored one.
- **No update** when there is no dated signal, or only an equal/older date.
- Staleness uses `effective = max(stored, live)` (missing stored = just live).
- DROP CANDIDATES with a known date: `no signal since <last_used> …` (effective date).
- `scan --dry-run` never writes last-used.
- Privacy: store a single date per name, not history lines.

## Open questions

| # | Topic | Status | Decision |
|---|--------|--------|----------|
| 1 | Where to store? | locked | Additive `"last_used": "YYYY-MM-DD"` on `software.json`; carry into `dropped.json` on archive. No migration/rewrite needed (ADR-008). Not in `versions.json` |
| 2 | Which signals feed the date? | locked | Any `Fact` with a non-empty `date` (shell, Spotlight, app-state). Config-ref stays undated — blocks “no signal at all,” does not bump `last_used` |
| 3 | Classify vs write order? | locked | Live newest → `effective = max(stored, live)` for staleness → on write, persist `effective` when newer than stored. Dry-run uses the same effective date but does not save |
| 4 | New stubs / first sighting? | locked | Same merge as existing entries: missing `last_used` is just empty stored. If the first scan already sees a dated signal, that becomes stored on write. No special “wait until second scan” rule |
| 5 | Shell history heuristics? | locked | Prefer real timestamps (zsh `EXTENDED_HISTORY`, fish). Survive truncation via storage (absence must not rewind). **Untimestamped hits → bounded guess (C)** — dogfood; see below. Cap future dates at today |
| 6 | Report / list UX? | locked | DROP CANDIDATES show `no signal since <last_used>` using the effective date. No full list column required for v1 |
| 7 | Manual override / clear? | locked | No CLI to edit `last_used` in v1 (derived field) |

## History heuristics (locked)

1. **Prefer real timestamps.** zsh `: <epoch>:…;` and fish `when:` as today.
2. **Survive truncation via storage.** Once `last_used` is written, a later scan with no shell hit must **not** clear or rewind it.
3. **Untimestamped hits — bounded guess (C).** Newest `UNTIMESTAMPED_WINDOW` (400) lines; date = history file mtime capped at today. Only fills names with no timestamped hit.
4. **Clock skew.** Cap any derived or parsed date at today.
5. **Name matching.** Current basename / ollama-model rules; write `last_used` only for inventory entry names.
6. **Multi-machine sync.** Out of scope.

## Non-goals

- Not storing full history snippets or per-signal timelines.
- Not auto-dropping when stale (still report-only DROP CANDIDATES).
- Not changing `--months` meaning beyond “compare against effective last-used.”
- Not a format version bump (additive field).
- Not a CLI to set/clear `last_used`.

## Done when

- [x] Write-mode scan persists `last_used` when a newer dated signal is seen (including first sighting with live signal + missing stored).
- [x] Equal/older/missing live dates leave the stored value unchanged.
- [x] Dry-run does not write `last_used`.
- [x] DROP CANDIDATES with an effective date use `no signal since <last_used> …`; history rotation alone does not wipe a prior date.
- [x] Untimestamped history path implements bounded guess (C) with a fixed newest-*N* window + file mtime.
- [x] Tests: newer updates; older ignored; absent keeps stored; first sighting writes live date; dry-run no write; DROP wording.
- [x] PRIVACY.md / README: last-used date stored locally; bash guess called out as approximate.

## Notes

Shipped: `inventory.ENTRY_FIELDS` + `last_used`; `scan.effective_last_used` / `apply_last_used`;
`shell_history` reads bash + untimestamped zsh window.
