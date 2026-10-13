"""Last invocation from shell history: zsh, fish, and bash.

zsh EXTENDED_HISTORY and fish carry timestamps. Untimestamped lines (bash, or zsh
without EXTENDED_HISTORY) use a bounded guess: name in the newest N lines → history
file mtime (capped at today). See dev/tasks/persist-last-used.md.
"""
import datetime
import os
import re
from pathlib import Path
from typing import Dict, Iterator, Set, Tuple

from vole.signals.base import Fact, SignalMap
from vole.sources.base import ScanContext

_PREFIXES = ('sudo', 'command', 'time', 'nohup', 'env', 'exec')
_ZSH_EXTENDED = re.compile(r'^: (\d+):\d+;(.*)$', re.M)
# Newest untimestamped lines scanned for bounded-guess dates.
UNTIMESTAMPED_WINDOW = 400


def _read(path: Path) -> str:
    try:
        with open(path, 'rb') as fh:
            return fh.read().decode('utf-8', 'replace')
    except OSError:
        return ''


def _mtime_day(path: Path, today: str) -> str:
    """Local calendar day of path mtime, capped at today. Empty if unreadable."""
    try:
        d = datetime.date.fromtimestamp(path.stat().st_mtime).isoformat()
    except OSError:
        return ''
    return min(d, today)


def _zsh(raw: str) -> Iterator[Tuple[str, str]]:
    """(timestamp, command) from `: <ts>:<duration>;<cmd>` lines."""
    for m in _ZSH_EXTENDED.finditer(raw):
        yield m.group(1), m.group(2)


def _fish(raw: str) -> Iterator[Tuple[str, str]]:
    """(timestamp, command) from fish's `- cmd: …` / `  when: <ts>` records."""
    cmd = None
    for line in raw.splitlines():
        if line.startswith('- cmd: '):
            cmd = line[len('- cmd: '):]
        elif cmd is not None and line.startswith('  when: '):
            yield line[len('  when: '):].strip(), cmd
            cmd = None


def _names(cmdline: str):
    """Command names a history line counts as using (ollama models too)."""
    toks = cmdline.split()
    i = 0
    while i < len(toks) and ('=' in toks[i] or toks[i] in _PREFIXES):
        i += 1
    if i >= len(toks):
        return []
    names = [os.path.basename(toks[i])]
    if names[0] == 'ollama' and i + 1 < len(toks) and toks[i + 1] in ('run', 'show'):
        j = i + 2
        while j < len(toks) and toks[j].startswith('-'):
            j += 1
        if j < len(toks):
            names.append(toks[j])
    return names


def _untimestamped_names(raw: str, window: int = UNTIMESTAMPED_WINDOW) -> Set[str]:
    """Command names in the newest *window* lines that are not zsh EXTENDED_HISTORY."""
    lines = [ln for ln in raw.splitlines() if ln.strip()]
    if window >= 0:
        lines = lines[-window:]
    found: Set[str] = set()
    for line in lines:
        if _ZSH_EXTENDED.match(line):
            continue
        for name in _names(line):
            found.add(name)
    return found


def _note(newest: Dict[str, str], name: str, day: str, today: str) -> None:
    if not day:
        return
    day = min(day, today)
    if day > newest.get(name, ''):
        newest[name] = day


def _apply_timestamped(newest: Dict[str, str], records, today: str) -> None:
    for ts, cmdline in records:
        names = _names(cmdline)
        if not names:
            continue
        try:
            d = datetime.date.fromtimestamp(int(ts)).isoformat()
        except (OverflowError, OSError, ValueError):
            continue
        for name in names:
            _note(newest, name, d, today)


def _apply_guess(newest: Dict[str, str], path: Path, raw: str, today: str) -> None:
    """Bounded guess for names with no timestamped hit yet."""
    guess = _mtime_day(path, today)
    if not guess:
        return
    for name in _untimestamped_names(raw):
        if name not in newest:
            _note(newest, name, guess, today)


def collect(ctx: ScanContext) -> SignalMap:
    today = datetime.date.today().isoformat()
    newest: Dict[str, str] = {}

    zsh_path = ctx.home / '.zsh_history'
    zsh_raw = _read(zsh_path)
    _apply_timestamped(newest, _zsh(zsh_raw), today)
    _apply_guess(newest, zsh_path, zsh_raw, today)

    fish_path = ctx.home / '.local' / 'share' / 'fish' / 'fish_history'
    fish_raw = _read(fish_path)
    _apply_timestamped(newest, _fish(fish_raw), today)

    bash_path = ctx.home / '.bash_history'
    bash_raw = _read(bash_path)
    _apply_guess(newest, bash_path, bash_raw, today)

    if not ctx.entries:
        return {name: [Fact(f'shell {d}', d)] for name, d in newest.items()}
    out: SignalMap = {}
    for name in ctx.entries:
        d = newest.get(name) or newest.get(name.split('/')[-1])
        if d:
            out[name] = [Fact(f'shell {d}', d)]
    return out
