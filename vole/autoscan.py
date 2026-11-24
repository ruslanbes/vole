"""Scheduled background scans via a user LaunchAgent (macOS launchd)."""
from __future__ import annotations

import datetime as dt
import json
import os
import plistlib
import re
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from vole import inventory, paths, scan

LABEL = 'com.ruslanbes.vole.autoscan'
DEFAULT_SCHEDULE = 'weekly'
FILE_MODE = inventory.FILE_MODE
DIR_MODE = inventory.DIR_MODE

_SCHEDULE_HELP = 'weekly | monthly | every [n] minute(s)|hour(s)|day(s)'
# "every hour" / "every 3 days" — count defaults to 1.
_EVERY = re.compile(r'^every(?:\s+(\d+))?\s+(minutes?|hours?|days?)$', re.I)


class Schedule:
    """Normalized schedule ready for launchd + next-run math."""

    __slots__ = ('phrase', 'kind', 'seconds', 'calendar')

    def __init__(self, phrase: str, kind: str,
                 seconds: Optional[int] = None,
                 calendar: Optional[Dict[str, int]] = None):
        self.phrase = phrase
        self.kind = kind  # 'interval' | 'calendar'
        self.seconds = seconds
        self.calendar = calendar


def parse_schedule(text: str) -> Schedule:
    """Parse a free-form schedule phrase. Raises ValueError with examples on failure."""
    raw = ' '.join((text or '').split())
    if not raw:
        raise ValueError(f'empty schedule — try: {_SCHEDULE_HELP}')
    low = raw.lower()
    if low == 'weekly':
        # Sunday 09:00 local (launchd Weekday 0 = Sunday).
        return Schedule('weekly', 'calendar',
                        calendar={'Weekday': 0, 'Hour': 9, 'Minute': 0})
    if low == 'monthly':
        return Schedule('monthly', 'calendar',
                        calendar={'Day': 1, 'Hour': 9, 'Minute': 0})
    m = _EVERY.match(low)
    if not m:
        raise ValueError(f'unrecognized schedule {raw!r} — try: {_SCHEDULE_HELP}')
    n = int(m.group(1) or '1')
    if n < 1:
        raise ValueError(f'schedule count must be ≥ 1 — try: {_SCHEDULE_HELP}')
    unit = m.group(2).lower()
    if unit.startswith('minute'):
        seconds = n * 60
        stem = 'minute'
    elif unit.startswith('hour'):
        seconds = n * 3600
        stem = 'hour'
    else:
        seconds = n * 86400
        stem = 'day'
    phrase = f'every {n} {stem}' + ('' if n == 1 else 's')
    return Schedule(phrase, 'interval', seconds=seconds)


def log_path() -> Path:
    override = os.environ.get('VOLE_AUTOSCAN_LOG')
    if override:
        return Path(override)
    return Path.home() / 'Library' / 'Logs' / 'vole' / 'autoscan.log'


def plist_path() -> Path:
    override = os.environ.get('VOLE_AUTOSCAN_PLIST')
    if override:
        return Path(override)
    return Path.home() / 'Library' / 'LaunchAgents' / f'{LABEL}.plist'


def state_path(data_root=None) -> Path:
    return paths.autoscan_path(data_root)


def default_state(data_root: Path) -> Dict[str, Any]:
    return {
        'enabled': False,
        'schedule': DEFAULT_SCHEDULE,
        'data_dir': str(Path(data_root).resolve()),
        'program': [],
        'last_run': None,
    }


def load_state(data_root=None) -> Dict[str, Any]:
    path = state_path(data_root)
    root = Path(data_root) if data_root is not None else paths.data_dir()
    if not path.exists():
        return default_state(root)
    try:
        data = json.loads(path.read_text(encoding='utf-8'))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as e:
        raise ValueError(f'{path.name}: not valid autoscan state ({e})') from None
    if not isinstance(data, dict):
        raise ValueError(f'{path.name}: not a vole autoscan state object')
    state = default_state(root)
    state.update(data)
    state['enabled'] = bool(state.get('enabled'))
    if not state.get('schedule'):
        state['schedule'] = DEFAULT_SCHEDULE
    if not state.get('data_dir'):
        state['data_dir'] = str(root.resolve())
    if not isinstance(state.get('program'), list):
        state['program'] = []
    return state


def save_state(state: Dict[str, Any], data_root=None) -> None:
    path = state_path(data_root)
    ordered = {
        'data_dir': state.get('data_dir'),
        'enabled': bool(state.get('enabled')),
        'last_run': state.get('last_run'),
        'program': list(state.get('program') or []),
        'schedule': state.get('schedule') or DEFAULT_SCHEDULE,
    }
    text = json.dumps(ordered, indent=2, ensure_ascii=False) + '\n'
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


def resolve_program() -> List[str]:
    """Absolute argv prefix that launches this vole install."""
    argv0 = Path(sys.argv[0]).expanduser()
    try:
        resolved = argv0.resolve()
    except OSError:
        resolved = argv0
    if resolved.name == 'vole' and resolved.is_file():
        return [str(resolved)]
    which = shutil.which('vole')
    if which:
        return [str(Path(which).resolve())]
    return [sys.executable, '-m', 'vole']


def _parse_last_run(value) -> Optional[dt.datetime]:
    if not value:
        return None
    try:
        parsed = dt.datetime.fromisoformat(value)
    except (TypeError, ValueError):
        return None
    if parsed.tzinfo is None:
        parsed = parsed.astimezone()
    return parsed


def next_run_after(sched: Schedule, last_run: Optional[dt.datetime],
                   now: Optional[dt.datetime] = None) -> dt.datetime:
    """Next fire time in local timezone."""
    now = now or dt.datetime.now().astimezone()
    if now.tzinfo is None:
        now = now.astimezone()
    if sched.kind == 'interval':
        assert sched.seconds is not None
        base = last_run if last_run is not None else now
        if base.tzinfo is None:
            base = base.astimezone()
        nxt = base + dt.timedelta(seconds=sched.seconds)
        while nxt <= now:
            nxt += dt.timedelta(seconds=sched.seconds)
        return nxt
    assert sched.calendar is not None
    return _next_calendar(sched.calendar, last_run, now)


def _next_calendar(cal: Dict[str, int], last_run: Optional[dt.datetime],
                   now: dt.datetime) -> dt.datetime:
    """Next local datetime matching Day / Weekday + Hour + Minute."""
    hour = int(cal.get('Hour', 0))
    minute = int(cal.get('Minute', 0))
    start = now
    if last_run is not None:
        lr = last_run if last_run.tzinfo else last_run.astimezone()
        candidate = lr.replace(hour=hour, minute=minute, second=0, microsecond=0)
        if candidate <= lr:
            start = max(now, lr + dt.timedelta(seconds=1))
        else:
            start = max(now, lr)
    # Search up to ~400 days ahead.
    day = start.date()
    for _ in range(400):
        candidate = dt.datetime(
            day.year, day.month, day.day, hour, minute, tzinfo=now.tzinfo)
        ok = candidate > now and (last_run is None or candidate > last_run)
        if ok:
            if 'Weekday' in cal and candidate.weekday() != _launchd_weekday(cal['Weekday']):
                ok = False
            if 'Day' in cal and candidate.day != int(cal['Day']):
                ok = False
        if ok:
            return candidate
        day += dt.timedelta(days=1)
    return now + dt.timedelta(days=7)


def _launchd_weekday(value: int) -> int:
    """launchd Weekday 0=Sunday … 6=Saturday → datetime.weekday() Mon=0."""
    # Sunday=0 → 6, Monday=1 → 0, …
    return (int(value) - 1) % 7


def build_plist(program: List[str], data_dir: Path, sched: Schedule,
                stdout_log: Path) -> Dict[str, Any]:
    """launchd plist dict (not yet serialized)."""
    args = list(program) + ['--data-dir', str(Path(data_dir).resolve()),
                            'autoscan', 'run']
    plist: Dict[str, Any] = {
        'Label': LABEL,
        'ProgramArguments': args,
        'RunAtLoad': False,
        'StandardOutPath': str(stdout_log),
        'StandardErrorPath': str(stdout_log),
    }
    if sched.kind == 'interval':
        plist['StartInterval'] = int(sched.seconds)
    else:
        plist['StartCalendarInterval'] = dict(sched.calendar)
    return plist


def write_plist(plist: Dict[str, Any], path: Optional[Path] = None) -> Path:
    path = path or plist_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, 'wb') as f:
        plistlib.dump(plist, f, sort_keys=False)
    return path


def _launchctl(args: List[str]) -> Tuple[int, str]:
    """Run launchctl; returns (returncode, combined output). Overridable in tests."""
    if os.environ.get('VOLE_AUTOSCAN_SKIP_LAUNCHCTL') == '1':
        return 0, ''
    try:
        proc = subprocess.run(
            ['launchctl', *args],
            capture_output=True, text=True, check=False)
    except FileNotFoundError as e:
        raise OSError('launchctl not found — autoscan requires macOS launchd') from e
    out = ((proc.stdout or '') + (proc.stderr or '')).strip()
    return proc.returncode, out


def agent_domain() -> str:
    return f'gui/{os.getuid()}'


def load_agent(plist: Path) -> None:
    domain = agent_domain()
    # Idempotent: boot out any previous instance, then bootstrap.
    _launchctl(['bootout', f'{domain}/{LABEL}'])
    code, out = _launchctl(['bootstrap', domain, str(plist)])
    if code != 0:
        # Older fallback.
        _launchctl(['unload', str(plist)])
        code2, out2 = _launchctl(['load', str(plist)])
        if code2 != 0:
            raise OSError(out or out2 or f'launchctl bootstrap failed ({code})')


def unload_agent(plist: Optional[Path] = None) -> None:
    path = plist or plist_path()
    domain = agent_domain()
    _launchctl(['bootout', f'{domain}/{LABEL}'])
    _launchctl(['unload', str(path)])


def ensure_log_dir() -> Path:
    path = log_path()
    path.parent.mkdir(mode=DIR_MODE, parents=True, exist_ok=True)
    return path


def enable(data_root: Path, schedule_phrase: Optional[str] = None,
           program: Optional[List[str]] = None) -> Dict[str, Any]:
    """Write state + plist and load the LaunchAgent. Returns updated state."""
    state = load_state(data_root)
    phrase = schedule_phrase or state.get('schedule') or DEFAULT_SCHEDULE
    sched = parse_schedule(phrase)
    prog = list(program) if program is not None else resolve_program()
    data_abs = Path(data_root).resolve()
    log = ensure_log_dir()
    plist = build_plist(prog, data_abs, sched, log)
    write_plist(plist)
    load_agent(plist_path())
    state.update({
        'enabled': True,
        'schedule': sched.phrase,
        'data_dir': str(data_abs),
        'program': prog,
    })
    save_state(state, data_root)
    return state


def disable(data_root: Path) -> Dict[str, Any]:
    """Unload the agent and mark disabled; keep schedule for next on."""
    try:
        unload_agent()
    except OSError:
        pass
    state = load_state(data_root)
    state['enabled'] = False
    save_state(state, data_root)
    return state


def format_local(when: dt.datetime) -> str:
    if when.tzinfo is None:
        when = when.astimezone()
    return when.astimezone().strftime('%Y-%m-%d %H:%M %Z')


def status_lines(data_root: Path, now: Optional[dt.datetime] = None) -> List[str]:
    """Human status lines for `vole autoscan`."""
    state = load_state(data_root)
    enabled = bool(state.get('enabled'))
    phrase = state.get('schedule') or DEFAULT_SCHEDULE
    lines = [
        f"autoscan: {'on' if enabled else 'off'}",
        f'schedule: {phrase}',
    ]
    try:
        sched = parse_schedule(phrase)
    except ValueError:
        sched = None
    if enabled and sched is not None:
        last = _parse_last_run(state.get('last_run'))
        nxt = next_run_after(sched, last, now=now)
        lines.append(f'next:     {format_local(nxt)}')
        if last is not None:
            lines.append(f'last:     {format_local(last)}')
    prog = state.get('program') or []
    if prog:
        bin_path = Path(prog[0])
        if not bin_path.exists():
            lines.append(f'warning: pinned vole binary missing: {bin_path}')
    lines.append(f'log:      {log_path()}')
    return lines


def record_run(data_root: Path, when: Optional[dt.datetime] = None) -> None:
    state = load_state(data_root)
    when = when or dt.datetime.now().astimezone()
    state['last_run'] = when.isoformat(timespec='seconds')
    save_state(state, data_root)


def run_scheduled(data_root: Path) -> int:
    """Agent entry: write-mode scan, then stamp last_run."""
    code = scan.run(data_root=data_root, months=6, write=True)
    record_run(data_root)
    return int(code)
