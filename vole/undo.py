"""Undo stack: shadow copies of inventory files before interactive mutations."""
from __future__ import annotations

import datetime as dt
import json
import os
import shutil
from pathlib import Path
from typing import Any, Dict, List, Optional

from vole import inventory, paths
from vole.migrations import FORMAT

DEFAULT_DEPTH = 20
DIFF_LINE_CAP = 40
STACK_NAME = 'stack.json'
DIR_MODE = inventory.DIR_MODE
FILE_MODE = inventory.FILE_MODE

# Inventory basenames tracked in each frame (stable order).
_TRACKED = tuple(f'{name}.json' for name in paths.DATA_FILES)


def undo_dir(data_root=None) -> Path:
    return (Path(data_root) if data_root is not None else paths.data_dir()) / 'undo'


def _stack_path(data_root) -> Path:
    return undo_dir(data_root) / STACK_NAME


def _frame_dir(data_root, frame_id: str) -> Path:
    return undo_dir(data_root) / frame_id


def _load_stack(data_root) -> List[Dict[str, Any]]:
    path = _stack_path(data_root)
    if not path.exists():
        return []
    try:
        data = json.loads(path.read_text(encoding='utf-8'))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError):
        return []
    frames = data.get('frames') if isinstance(data, dict) else None
    if not isinstance(frames, list):
        return []
    return [f for f in frames if isinstance(f, dict) and f.get('id')]


def _save_stack(data_root, frames: List[Dict[str, Any]]) -> None:
    root = undo_dir(data_root)
    root.mkdir(mode=DIR_MODE, parents=True, exist_ok=True)
    path = _stack_path(data_root)
    text = json.dumps({'frames': frames}, indent=2, ensure_ascii=False) + '\n'
    tmp = path.with_suffix(path.suffix + '.tmp')
    fd = os.open(tmp, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, FILE_MODE)
    os.fchmod(fd, FILE_MODE)
    with os.fdopen(fd, 'w', encoding='utf-8') as f:
        f.write(text)
    os.replace(tmp, path)


def _next_id(frames: List[Dict[str, Any]]) -> str:
    n = 0
    for frame in frames:
        try:
            n = max(n, int(frame['id']))
        except (KeyError, TypeError, ValueError):
            continue
    return f'{n + 1:08d}'


def clear(data_root) -> None:
    """Remove the entire undo directory (used by reset / after migrate)."""
    root = undo_dir(data_root)
    if root.exists():
        shutil.rmtree(root)


def depth(data_root) -> int:
    return len(_load_stack(data_root))


def peek(data_root) -> Optional[Dict[str, Any]]:
    frames = _load_stack(data_root)
    return frames[-1] if frames else None


def checkpoint(data_root, label: str, *, depth_limit: int = DEFAULT_DEPTH) -> Dict[str, Any]:
    """Snapshot current inventory files and push a frame. Returns the frame meta."""
    data_root = Path(data_root)
    paths.ensure_data_dir(data_root)
    frames = _load_stack(data_root)
    frame_id = _next_id(frames)
    dest = _frame_dir(data_root, frame_id)
    dest.mkdir(mode=DIR_MODE, parents=True, exist_ok=True)

    files_meta: Dict[str, str] = {}
    for name in _TRACKED:
        src = data_root / name
        if src.exists():
            shutil.copy2(src, dest / name)
            try:
                os.chmod(dest / name, FILE_MODE)
            except OSError:
                pass
            files_meta[name] = 'present'
        else:
            files_meta[name] = 'absent'

    frame = {
        'id': frame_id,
        'format': FORMAT,
        'label': label,
        'at': dt.datetime.now().astimezone().isoformat(timespec='seconds'),
        'files': files_meta,
    }
    frames.append(frame)

    while len(frames) > depth_limit:
        old = frames.pop(0)
        old_dir = _frame_dir(data_root, old['id'])
        if old_dir.exists():
            shutil.rmtree(old_dir)

    _save_stack(data_root, frames)
    return frame


def _frame_matches_current(data_root: Path, frame: Dict[str, Any]) -> bool:
    """True when tracked files are byte-identical to the checkpoint (no-op undo)."""
    src_dir = _frame_dir(data_root, frame['id'])
    files = frame.get('files') or {}
    for name in _TRACKED:
        state = files.get(name, 'absent')
        current = data_root / name
        if state == 'absent':
            if current.exists():
                return False
            continue
        shadow = src_dir / name
        if not current.exists() or not shadow.exists():
            return False
        try:
            if current.read_bytes() != shadow.read_bytes():
                return False
        except OSError:
            return False
    return True


def discard_if_unchanged(data_root, frame: Optional[Dict[str, Any]] = None) -> bool:
    """Drop a checkpoint if inventory matches it (mutation was a no-op).

    Defaults to the newest frame. Returns True when a frame was discarded.
    """
    data_root = Path(data_root)
    frames = _load_stack(data_root)
    if not frames:
        return False
    target = frame or frames[-1]
    # Only discard if it is still the tip (callers finalize right after writing).
    if frames[-1].get('id') != target.get('id'):
        return False
    if not _frame_matches_current(data_root, target):
        return False
    frames.pop()
    _save_stack(data_root, frames)
    src_dir = _frame_dir(data_root, target['id'])
    if src_dir.exists():
        shutil.rmtree(src_dir, ignore_errors=True)
    return True


def _frame_when(frame: Dict[str, Any], data_root) -> str:
    """Local display time for a checkpoint (stored ``at``, else frame dir mtime)."""
    raw = frame.get('at')
    if raw:
        try:
            when = dt.datetime.fromisoformat(raw)
            if when.tzinfo is None:
                when = when.astimezone()
            return when.astimezone().strftime('%Y-%m-%d %H:%M %Z')
        except ValueError:
            pass
    path = _frame_dir(data_root, frame['id'])
    try:
        when = dt.datetime.fromtimestamp(path.stat().st_mtime).astimezone()
        return when.strftime('%Y-%m-%d %H:%M %Z')
    except OSError:
        return 'unknown'


def _fmt_val(value) -> str:
    return json.dumps(value, ensure_ascii=False)


def _entry_diff_lines(cur: Dict[str, Any], chk: Dict[str, Any]) -> List[str]:
    """Compact per-name lines: current → checkpoint (what undo applies)."""
    lines: List[str] = []
    names = sorted(set(cur) | set(chk), key=inventory.name_sort_key)
    for name in names:
        if name not in chk:
            lines.append(f'    - {name}')
        elif name not in cur:
            lines.append(f'    + {name}')
        else:
            a, b = cur[name], chk[name]
            changes = []
            for key in sorted(set(a) | set(b)):
                if a.get(key) == b.get(key):
                    continue
                if key not in b:
                    changes.append(f'{key} {_fmt_val(a[key])} → (cleared)')
                elif key not in a:
                    changes.append(f'{key} (none) → {_fmt_val(b[key])}')
                else:
                    changes.append(
                        f'{key} {_fmt_val(a[key])} → {_fmt_val(b[key])}')
            if changes:
                lines.append(f'    {name}: ' + '; '.join(changes))
    return lines


def _file_diff_lines(data_root: Path, frame: Dict[str, Any],
                     basename: str) -> List[str]:
    state = (frame.get('files') or {}).get(basename, 'absent')
    current = data_root / basename
    shadow = _frame_dir(data_root, frame['id']) / basename

    if state == 'absent':
        if current.exists():
            return [f'  {basename}: remove file']
        return [f'  {basename}: (unchanged)']

    try:
        chk = inventory.load(shadow)
    except (OSError, ValueError):
        return [f'  {basename}: (checkpoint unreadable)']
    cur = inventory.load(current, missing_ok=True)
    body = _entry_diff_lines(cur, chk)
    if not body:
        return [f'  {basename}: (unchanged)']
    return [f'  {basename}:'] + body


def describe_restore(data_root, frame: Dict[str, Any], *,
                     dry_run: bool) -> List[str]:
    """Header + compact inventory diff for dry-run or real undo."""
    data_root = Path(data_root)
    verb = 'would restore' if dry_run else 'restored'
    label = frame.get('label') or 'mutation'
    when = _frame_when(frame, data_root)
    lines = [f'undo: {verb} `{label}` from {when}']

    diff: List[str] = []
    for name in _TRACKED:
        diff.extend(_file_diff_lines(data_root, frame, name))

    if len(diff) > DIFF_LINE_CAP:
        omitted = len(diff) - DIFF_LINE_CAP
        diff = diff[:DIFF_LINE_CAP] + [f'  … and {omitted} more']
    lines.extend(diff)
    return lines


def restore(data_root, *, dry_run: bool = False) -> List[str]:
    """Pop and apply the latest frame. Returns status lines. Raises ValueError."""
    data_root = Path(data_root)
    frames = _load_stack(data_root)
    if not frames:
        raise ValueError('nothing to undo')

    frame = frames[-1]
    frame_format = frame.get('format')
    if frame_format != FORMAT:
        raise ValueError(
            f'checkpoint format {frame_format!r} does not match current '
            f'format {FORMAT} — refuse undo after migrate')

    lines = describe_restore(data_root, frame, dry_run=dry_run)
    if dry_run:
        return lines

    src_dir = _frame_dir(data_root, frame['id'])
    if not src_dir.is_dir():
        raise ValueError(f'undo frame {frame["id"]!r} is missing on disk')

    files = frame.get('files') or {}
    # Stage restores in temps, then replace; delete absents after.
    staged = []
    try:
        for name in _TRACKED:
            state = files.get(name, 'absent')
            target = data_root / name
            if state == 'present':
                shadow = src_dir / name
                if not shadow.exists():
                    raise ValueError(f'undo frame missing file {name}')
                tmp = target.with_suffix(target.suffix + '.undo-tmp')
                shutil.copy2(shadow, tmp)
                try:
                    os.chmod(tmp, FILE_MODE)
                except OSError:
                    pass
                staged.append((tmp, target, 'replace'))
            else:
                staged.append((None, target, 'remove'))

        for tmp, target, action in staged:
            if action == 'replace':
                target.parent.mkdir(mode=DIR_MODE, parents=True, exist_ok=True)
                os.replace(tmp, target)
            elif target.exists():
                target.unlink()
    except OSError:
        for tmp, _target, action in staged:
            if action == 'replace' and tmp is not None:
                try:
                    tmp.unlink()
                except OSError:
                    pass
        raise

    frames.pop()
    _save_stack(data_root, frames)
    shutil.rmtree(src_dir, ignore_errors=True)
    return lines
