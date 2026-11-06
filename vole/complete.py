"""Shell-completion helpers (Tab only — not resolve-time fuzzy)."""
from typing import Iterable, List

from vole.inventory import name_sort_key


def edit_distance(a: str, b: str) -> int:
    """Levenshtein distance (code points)."""
    if a == b:
        return 0
    if not a:
        return len(b)
    if not b:
        return len(a)
    # Ensure b is the shorter row for memory; algorithm is fine either way.
    prev = list(range(len(b) + 1))
    for i, ca in enumerate(a, 1):
        cur = [i]
        for j, cb in enumerate(b, 1):
            ins = cur[j - 1] + 1
            delete = prev[j] + 1
            sub = prev[j - 1] + (0 if ca == cb else 1)
            cur.append(min(ins, delete, sub))
        prev = cur
    return prev[-1]


def within_edit_distance(a: str, b: str, max_d: int = 1) -> bool:
    if abs(len(a) - len(b)) > max_d:
        return False
    return edit_distance(a, b) <= max_d


def completion_names(query: str, names: Iterable[str], *, max_edits: int = 1,
                     edit_min_len: int = 3) -> List[str]:
    """Names for Tab completion: CI prefix match, plus ≤max_edits typos when query long enough."""
    q = query or ''
    ql = q.lower()
    out = []
    seen = set()
    for name in names:
        if name in seen:
            continue
        nl = name.lower()
        if not ql or nl.startswith(ql):
            seen.add(name)
            out.append(name)
            continue
        if (max_edits > 0 and len(ql) >= edit_min_len
                and within_edit_distance(nl, ql, max_edits)):
            seen.add(name)
            out.append(name)
    return sorted(out, key=name_sort_key)
