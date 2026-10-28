"""Read and write the JSON inventory. Stdlib only, Python 3.9+."""
import json
import os
import sys
from pathlib import Path
from typing import Dict, List, Optional

from vole.migrations import FORMAT

FILE_MODE = 0o600
DIR_MODE = 0o700
EDITABLE = ('why', 'keep', 'status')
STATUSES = frozenset({'active', 'dropped'})
# Who archived an entry into dropped.json. Missing = legacy / non-sticky (scan may restore).
ARCHIVED_BY_USER = 'user'
ARCHIVED_BY_SCAN = 'scan'
ARCHIVED_BY = frozenset({ARCHIVED_BY_USER, ARCHIVED_BY_SCAN})
# software / dropped entries — keep is free-form; archived_by / last_used are additive.
# ``source`` is allowed on *dropped* rows (copied from versions at archive time), not on active.
ENTRY_FIELDS = frozenset({
    'source', 'why', 'added', 'status', 'keep', 'archived_by', 'last_used',
})
VERSION_FIELDS = frozenset({'source', 'versions'})


def name_sort_key(name: str):
    """Case-insensitive name order (phone-book); tie-break on original spelling."""
    return (name.lower(), name)


def resolve_name(query: str, *maps):
    """Resolve an inventory name for CLI verbs (not ``add`` / ``list``).

    1. Exact (case-sensitive) hit → that key.
    2. Else case-insensitive (``query.lower() == name.lower()``): unique hit → that key;
       several hits → ambiguous.

    Returns ``(canonical, None)`` on success, ``(None, [hits…])`` when ambiguous,
    ``(None, None)`` when missing.
    """
    ordered: List[str] = []
    seen = set()
    for m in maps:
        if not m:
            continue
        for key in m:
            if key not in seen:
                seen.add(key)
                ordered.append(key)
    if query in seen:
        return query, None
    folded = query.lower()
    hits = [key for key in ordered if key.lower() == folded]
    if len(hits) == 1:
        return hits[0], None
    if len(hits) > 1:
        return None, hits
    return None, None


def render(apps, format: Optional[int] = None):
    """Serialise deterministically: entries sorted by name case-insensitively,
    fields sorted, two-space indent. Same data always gives the same bytes."""
    fmt = FORMAT if format is None else format
    ordered = {name: {k: apps[name][k] for k in sorted(apps[name])}
               for name in sorted(apps, key=name_sort_key)}
    return json.dumps({'format': fmt, 'apps': ordered}, indent=2, ensure_ascii=False) + '\n'

def parse(text, label='inventory'):
    try:
        data = json.loads(text)
    except json.JSONDecodeError as e:
        raise ValueError(f'{label}: not valid JSON ({e})') from None
    if not isinstance(data, dict) or not isinstance(data.get('apps'), dict):
        raise ValueError(f'{label}: not a vole inventory (no "apps" object)')
    if data.get('format') != FORMAT:
        raise ValueError(f'{label}: unsupported format {data.get("format")!r}, expected {FORMAT}')
    return data['apps']

def load(path, missing_ok=False):
    path = Path(path)
    if missing_ok and not path.exists():
        return {}
    with open(path, encoding='utf-8') as f:
        return parse(f.read(), path.name)

def save(path, apps, format: Optional[int] = None):
    """The only writer. Temp file + os.replace so an interrupted run cannot truncate.

    Leaves the file untouched (same mtime) when the rendered text is already on disk.
    Files are owner-only (0600): they hold personal notes.
    """
    path = Path(path)
    text = render(apps, format=format)
    try:
        if path.read_text(encoding='utf-8') == text:
            if path.stat().st_mode & 0o077:
                os.chmod(path, FILE_MODE)
            return
    except (OSError, UnicodeDecodeError):
        pass
    path.parent.mkdir(mode=DIR_MODE, parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + '.tmp')
    try:
        fd = os.open(tmp, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, FILE_MODE)
        # O_CREAT keeps the mode of a leftover temp file; force it.
        os.fchmod(fd, FILE_MODE)
        with os.fdopen(fd, 'w', encoding='utf-8') as f:
            f.write(text)
        os.replace(tmp, path)
    except OSError:
        try:
            tmp.unlink()
        except OSError:
            pass
        raise

def move(name, entry, src, src_path, dst, dst_path):
    """Move an entry between two loaded files and save both.

    The destination is written first: if the second write fails, the entry is in both files
    rather than in neither.
    """
    dst[name] = entry
    save(dst_path, dst)
    del src[name]
    save(src_path, src)


def set_field(entry, key, value):
    if '\n' in value or '\r' in value:
        raise ValueError('value must be a single line')
    out = dict(entry)
    if value == '':
        out.pop(key, None)
    else:
        out[key] = value
    return out

def stub(today):
    """New active software row — no source (live source lives on versions.json)."""
    return {'why': 'TODO', 'added': today, 'status': 'active'}


def attach_drop_source(entry: Dict, name: str, versions: Dict, *, warn: bool = True) -> Dict:
    """Copy ``source`` from versions onto a drop/archive entry; omit if missing."""
    out = dict(entry)
    row = versions.get(name) if versions else None
    src = (row or {}).get('source') if isinstance(row, dict) else None
    if src:
        out['source'] = src
    else:
        out.pop('source', None)
        if warn:
            print(f'warning: no versions source for {name!r} — archived without source',
                  file=sys.stderr)
    return out


def check_apps(apps: Dict, label: str, *, versions_file: bool = False) -> List[str]:
    """Return human-readable shape problems for a loaded apps map. Empty = ok."""
    problems: List[str] = []
    allowed = VERSION_FIELDS if versions_file else ENTRY_FIELDS
    for name in sorted(apps, key=name_sort_key):
        entry = apps[name]
        where = f'{label}: {name!r}'
        if not isinstance(entry, dict):
            problems.append(f'{where}: entry must be an object, got {type(entry).__name__}')
            continue
        for key in sorted(entry):
            if key not in allowed:
                problems.append(f'{where}: unknown field {key!r}')
        if versions_file:
            if 'versions' in entry:
                vers = entry['versions']
                if not isinstance(vers, list):
                    problems.append(
                        f'{where}: versions must be a list, got {type(vers).__name__}')
                else:
                    for i, v in enumerate(vers):
                        if not isinstance(v, str):
                            problems.append(
                                f'{where}: versions[{i}] must be a string, '
                                f'got {type(v).__name__}')
            if 'source' in entry and not isinstance(entry['source'], str):
                problems.append(
                    f'{where}: source must be a string, got {type(entry["source"]).__name__}')
            continue
        for key in ('source', 'why', 'added', 'keep', 'last_used'):
            if key in entry and not isinstance(entry[key], str):
                problems.append(
                    f'{where}: {key} must be a string, got {type(entry[key]).__name__}')
        if 'status' in entry:
            st = entry['status']
            if not isinstance(st, str):
                problems.append(
                    f'{where}: status must be a string, got {type(st).__name__}')
            elif st not in STATUSES:
                problems.append(
                    f'{where}: unknown status {st!r} (expected active or dropped)')
        status = entry.get('status', 'active')
        if status != 'dropped' and 'source' in entry:
            problems.append(
                f'{where}: source on active software is obsolete '
                f'(use versions.json; copied onto dropped at archive time)')
        if 'archived_by' in entry:
            ab = entry['archived_by']
            if not isinstance(ab, str):
                problems.append(
                    f'{where}: archived_by must be a string, got {type(ab).__name__}')
            elif ab not in ARCHIVED_BY:
                problems.append(
                    f'{where}: unknown archived_by {ab!r} (expected user or scan)')
    return problems


def sticky_drop(entry) -> bool:
    """True when a manual drop must not auto-restore."""
    return entry.get('archived_by') == ARCHIVED_BY_USER


def mark_user_drop(entry: Dict) -> Dict:
    """Copy entry as a user-sticky archive."""
    out = dict(entry)
    out['status'] = 'dropped'
    out['archived_by'] = ARCHIVED_BY_USER
    return out


def mark_scan_drop(entry: Dict) -> Dict:
    """Copy entry as a scan archive (reinstall may auto-restore)."""
    out = dict(entry)
    out['status'] = 'dropped'
    out['archived_by'] = ARCHIVED_BY_SCAN
    return out


def clear_archive_meta(entry: Dict) -> Dict:
    """Copy entry restored to active software (no archived_by / source)."""
    out = dict(entry)
    out['status'] = 'active'
    out.pop('archived_by', None)
    out.pop('source', None)
    return out
