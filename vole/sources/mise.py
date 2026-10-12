"""mise-managed tools — a name may have several versions."""
import shutil
import subprocess
from typing import Dict, Iterable, List

from vole.sources.base import Installed, ScanContext


def parse_ls(text: str) -> List[Installed]:
    """Parse `mise ls --installed` text: ``name version …`` per line."""
    by: Dict[str, List[str]] = {}
    for line in text.splitlines():
        parts = line.split()
        if len(parts) < 2:
            continue
        name, ver = parts[0], parts[1]
        by.setdefault(name, [])
        if ver not in by[name]:
            by[name].append(ver)
    return [Installed('mise', name, vers) for name, vers in sorted(by.items())]


def discover(ctx: ScanContext) -> Iterable[Installed]:
    if not shutil.which('mise'):
        return
    try:
        out = subprocess.run(['mise', 'ls', '--installed'],
                             capture_output=True, text=True, timeout=60)
    except (OSError, subprocess.TimeoutExpired):
        return
    yield from parse_ls(out.stdout)
