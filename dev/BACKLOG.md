# Backlog

Flat task list. Status values: `backlog` | `ready` | `in_progress` | `blocked` | `done` | `cancelled`.

On cleanup, move shipped work to [`CHANGELOG.md`](../CHANGELOG.md) and clean the backlog — see [`CLEANUP.md`](CLEANUP.md).

Reorder freely. Cancel by setting status to `cancelled`. Unexpected work becomes a new task with its own ID.

## Format

Each task:

```markdown
## <task-id>
- status: backlog
- parent: <optional-related-task-id>
- blocked_by: <optional-task-id>
- goal: One sentence
- done_when: Observable acceptance criteria
- notes: Optional one-liner
```

Detail lives in `dev/tasks/<task-id>.md` when needed.

---

## homebrew-formula
- status: ready
- goal: Users can install vole via a personal Homebrew tap (not core).
- done_when: See `dev/tasks/homebrew-formula.md`.
- notes: Formula exists in tap; bump for new tags; install `completions/_vole` into brew zsh completion dir.

## cli-uninstall
- status: backlog
- goal: Source-specific `vole uninstall` (machine remove); huge; not current version.
- done_when: See `dev/tasks/cli-uninstall.md`.
- notes: OQs open — may later rename `drop`→`uninstall`; keep DROP CANDIDATES language until then.

## cli-undo
- status: done
- goal: `vole undo` restores inventory after the last mutating CLI write.
- done_when: See `dev/tasks/cli-undo.md`.
- notes: Shipped — stack depth 20 under `undo/`; interactive writes+scan; not autoscan; reset wipes.

## cli-autoscan
- status: done
- goal: `vole autoscan` on/off/schedule + status (next run); free-form schedules from CLI.
- done_when: See `dev/tasks/cli-autoscan.md`.
- notes: Shipped — launchd LaunchAgent; weekly default; `schedule` set⇒on; log under `~/Library/Logs/vole/`.

## name-fuzzy-match
- status: backlog
- goal: Auto-resolve unique ≤2-edit name typos; announce assumption.
- done_when: See `dev/tasks/name-fuzzy-match.md`.
- notes: OQs open — after exact/CI; short-name guard; stdlib Levenshtein. Tab 1-edit is separate (shipped).

## name-glob
- status: done
- goal: `*` / `?` multi-name selection for batch why/keep (quoted patterns).
- done_when: See `dev/tasks/name-glob.md`.
- notes: Shipped — `why`/`keep` only; zero→fail; print matches then proceed; `*`/`?` only.

## detect-rosetta-apps
- status: backlog
- goal: On Apple Silicon, scan flags Intel-only (.app) installs that need Rosetta.
- done_when: See `dev/tasks/detect-rosetta-apps.md`.
- notes: OQs open — Spotlight/lipo; report section; .app only; live-only; arm64 host gate.

## source-sdkman
- status: backlog
- goal: Discover SDKMAN!-managed SDKs (Java, Groovy, Kotlin, …) under `~/.sdkman/candidates`.
- done_when: See `dev/tasks/source-sdkman.md`.
- notes: OQs open — filesystem walk proposed; after asdf for first-wins.

## source-intellij-jdks
- status: backlog
- goal: Discover JDKs installed by IntelliJ’s built-in Download JDK (not SDKMAN).
- done_when: See `dev/tasks/source-intellij-jdks.md`.
- notes: OQs open — likely `~/Library/Java/JavaVirtualMachines/`; skip bundled JBR.
