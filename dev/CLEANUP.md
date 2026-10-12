# Cleanup runbook

Related: [BACKLOG.md](BACKLOG.md), [STATUS.md](STATUS.md), [tasks/README.md](tasks/README.md), [RELEASE.md](RELEASE.md)

Run on demand when finished or cancelled work should leave the living backlog.

## 1. Clean the backlog

In [BACKLOG.md](BACKLOG.md):

- **Remove** entries whose work is fully captured in [CHANGELOG.md](../CHANGELOG.md) (`[Unreleased]` or a dated section).
- Create missing CHANGELOG entries in the `[Unreleased]` section if needed.
- Keep `backlog` / `ready` / `in_progress` / `blocked` items.
- Remove cancelled tasks and their detail files.
- Do **not** leave stale `done` rows after cleanup — the changelog is the archive of shipped work.

## 2. Analyze and cleanup task detail files

Per [tasks/README.md](tasks/README.md): delete `dev/tasks/<task-id>.md` for tasks that are done or cancelled.

Keep the `dev/tasks/` folder and `tasks/README.md`. Behavior should live in CHANGELOG, ADRs, and layer READMEs or other project docs — not in deleted specs.

### 2.1 Handling detailed task docs

- Task docs are temporary artifacts. Clean them up here.
- Read each detailed task doc.
- Check if any durable docs (`dev/README.md`, ADRs, layer READMEs, other project docs) reference the task doc.
- Extract important architectural decisions and contracts, summaries of diagrams and tables, and user-facing behavior.
- Check if that info is covered where it belongs: process/ground rules in `dev/README.md`; product/architecture in ADRs or layer READMEs (or other docs you maintain).
- If those docs have gaps, move the extracted material there. Create new durable docs if needed; review them before commit.

## 3. Refresh session status

Update [STATUS.md](STATUS.md):

- Set **Current focus** / **Active task** to what’s next.
- Clear or shorten **Session notes** for the cleaned work.
- Confirm **Blockers** is accurate.
