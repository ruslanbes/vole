"""Diff installed versions against the previous baseline."""
from typing import Dict, List

from vole.inventory import name_sort_key

Versions = Dict[str, List[str]]   # name -> sorted version list

def fmt(vs: List[str]) -> str:
    return ', '.join(vs) if vs else '(none)'

def diff(prev: Versions, current: Versions):
    """Return (changed, added, removed) as lists of display tuples."""
    changed, added, removed = [], [], []
    for name in sorted(current, key=name_sort_key):
        vs = sorted(current[name])
        old = prev.get(name)
        if old is None:
            added.append((name, fmt(vs)))
        elif sorted(old) != vs:
            changed.append((name, fmt(sorted(old)), fmt(vs)))
    for name in sorted(prev, key=name_sort_key):
        if name not in current:
            removed.append((name, fmt(sorted(prev[name]))))
    return changed, added, removed
