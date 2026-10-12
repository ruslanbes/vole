"""Last invocation from shell history: ~/.zsh_history (EXTENDED_HISTORY) and fish.

bash is not read: ~/.bash_history has no timestamps unless HISTTIMEFORMAT is set.
"""
import datetime
import os
import re
from pathlib import Path
from typing import Iterator, Tuple

from vole.signals.base import Fact, SignalMap
from vole.sources.base import ScanContext

_PREFIXES = ('sudo', 'command', 'time', 'nohup', 'env', 'exec')


def _read(path: Path) -> str:
    try:
        with open(path, 'rb') as fh:
            return fh.read().decode('utf-8', 'replace')
    except OSError:
        return ''


def _zsh(raw: str) -> Iterator[Tuple[str, str]]:
    """(timestamp, command) from `: <ts>:<duration>;<cmd>` lines."""
    for m in re.finditer(r'^: (\d+):\d+;(.*)$', raw, re.M):
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


def collect(ctx: ScanContext) -> SignalMap:
    records = list(_zsh(_read(ctx.home / '.zsh_history')))
    records += _fish(_read(ctx.home / '.local' / 'share' / 'fish' / 'fish_history'))
    newest = {}
    for ts, cmdline in records:
        names = _names(cmdline)
        if not names:
            continue
        try:
            d = datetime.date.fromtimestamp(int(ts)).isoformat()
        except (OverflowError, OSError, ValueError):
            continue
        for name in names:
            if d > newest.get(name, ''):
                newest[name] = d
    if not ctx.entries:
        return {name: [Fact(f'shell {d}', d)] for name, d in newest.items()}
    out: SignalMap = {}
    for name in ctx.entries:
        d = newest.get(name) or newest.get(name.split('/')[-1])
        if d:
            out[name] = [Fact(f'shell {d}', d)]
    return out
