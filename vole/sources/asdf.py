"""asdf-managed runtimes — one entry per plugin, several versions."""
import shutil
import subprocess
from typing import Dict, Iterable, List

from vole.sources.base import Installed, ScanContext


def parse_list(text: str) -> List[Installed]:
    """Parse `asdf list` text: plugin names flush-left, versions indented."""
    by: Dict[str, List[str]] = {}
    current = None
    for line in text.splitlines():
        if not line.strip():
            continue
        if line[:1].isspace():
            if current is None:
                continue
            ver = line.strip().lstrip('*').strip()
            if not ver or ver == 'No versions installed':
                continue
            by.setdefault(current, [])
            if ver not in by[current]:
                by[current].append(ver)
        else:
            current = line.strip()
            by.setdefault(current, [])
    return [Installed('asdf', name, vers) for name, vers in sorted(by.items()) if vers]


def discover(ctx: ScanContext) -> Iterable[Installed]:
    if not shutil.which('asdf'):
        return
    try:
        proc = subprocess.run(
            ['asdf', 'list'],
            capture_output=True, text=True, timeout=60)
    except (OSError, subprocess.TimeoutExpired):
        return
    if proc.returncode != 0 and not proc.stdout.strip():
        return
    yield from parse_list(proc.stdout)
