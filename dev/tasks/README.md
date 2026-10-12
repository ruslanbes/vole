# Task detail files

Optional deep-dive notes for a backlog item. One file per task ID:

```
dev/tasks/<task-id>.md
```

Use when a task needs examples, sample data, decision notes, or acceptance detail that would clutter `BACKLOG.md`.

Keep `BACKLOG.md` as the index (status, goal, done_when). This folder holds supporting material only.

Task detail files are temporary: remove them on cleanup when the task ships or is cancelled (see [`../CLEANUP.md`](../CLEANUP.md)). This README and the folder stay.

Copy [`TEMPLATE.md`](TEMPLATE.md) → `dev/tasks/<task-id>.md` when creating a new detail file. Do not leave `TEMPLATE.md` copies named as real tasks.
