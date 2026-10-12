"""Newest mtime across Library dirs an app touches when it runs."""
import datetime
import os
import re
from pathlib import Path
from typing import Dict, List

from vole.signals.base import Fact, SignalMap
from vole.sources.base import ScanContext

# Substring matches require len(norm(name)) > 4; index Library keys by every 5-gram.
_GRAM = 5


def norm(s):
    return re.sub(r'[^a-z0-9]', '', s.lower())


def _scan(home: Path):
    """Normalised Library-folder name → newest YYYY-MM-DD."""
    by_key = {}
    for sub in ('Library/Application Support', 'Library/Containers',
                'Library/Preferences', 'Library/Saved Application State'):
        d = home / sub
        if not d.is_dir():
            continue
        for e in os.listdir(d):
            try:
                ts = datetime.date.fromtimestamp((d / e).stat().st_mtime).isoformat()
            except OSError:
                continue
            keys = {norm(e), norm(re.sub(r'\.(plist|savedState)$', '', e).split('.')[-1])}
            for k in keys:
                if k and ts > by_key.get(k, ''):
                    by_key[k] = ts
    return by_key


def _gram_index(keys) -> Dict[str, List[str]]:
    """5-gram → Library keys containing that gram (each key listed once per gram)."""
    idx: Dict[str, List[str]] = {}
    for bk in keys:
        if len(bk) < _GRAM:
            continue
        seen = set()
        for i in range(len(bk) - _GRAM + 1):
            gram = bk[i:i + _GRAM]
            if gram in seen:
                continue
            seen.add(gram)
            idx.setdefault(gram, []).append(bk)
    return idx


def lookup(state_map: SignalMap, name: str, index=None):
    """Find an app-state fact for an entry name (exact norm, then substring).

    ``index`` is the 5-gram map from ``_gram_index``; without it, falls back to a
    full scan (same answers, slower).
    """
    k = norm(name)
    if k in state_map:
        return state_map[k]
    if len(k) <= _GRAM - 1:
        return []
    if index is None:
        candidates = state_map
    else:
        candidates = {bk: state_map[bk] for bk in index.get(k[:_GRAM], ())}
    matches = [facts for bk, facts in candidates.items() if k in bk]
    if matches:
        return max(matches, key=lambda f: f[0].date or '')
    return []


def collect(ctx: ScanContext) -> SignalMap:
    by_key = _scan(ctx.home)
    state = {k: [Fact(f'app state {d}', d)] for k, d in by_key.items()}
    if not ctx.entries:
        return state
    index = _gram_index(state)
    out: SignalMap = {}
    for name in ctx.entries:
        facts = lookup(state, name, index)
        if facts:
            out[name] = facts
    return out
