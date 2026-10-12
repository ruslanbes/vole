"""pnpm global packages — `pnpm list -g --depth 0 --json`."""
import json
import shutil
import subprocess
from typing import Any, Dict, Iterable, List, Union

from vole.sources.base import Installed, ScanContext


def parse_list_json(data: Union[Dict[str, Any], List[Any]]) -> List[Installed]:
    """Accept pnpm's array-of-projects or a single project/npm-shaped object."""
    projects: List[Dict[str, Any]]
    if isinstance(data, list):
        projects = [p for p in data if isinstance(p, dict)]
    elif isinstance(data, dict):
        projects = [data]
    else:
        return []

    by: Dict[str, str] = {}
    for proj in projects:
        for name, meta in (proj.get('dependencies') or {}).items():
            if not name:
                continue
            ver = ''
            if isinstance(meta, dict):
                ver = (meta.get('version') or '') or ''
            elif isinstance(meta, str):
                ver = meta
            # First mention wins within pnpm output; keep a version if we find one.
            if name not in by or (ver and not by[name]):
                by[name] = ver
    return [Installed('pnpm-global', name, [ver] if ver else [])
            for name, ver in sorted(by.items())]


def discover(ctx: ScanContext) -> Iterable[Installed]:
    if not shutil.which('pnpm'):
        return
    try:
        proc = subprocess.run(
            ['pnpm', 'list', '-g', '--depth', '0', '--json'],
            capture_output=True, text=True, timeout=60)
        if not proc.stdout.strip():
            return
        data = json.loads(proc.stdout)
    except (OSError, subprocess.TimeoutExpired, json.JSONDecodeError):
        return
    yield from parse_list_json(data)
