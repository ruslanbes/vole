"""pipx-managed apps — package identity + versions; expose shim names for bins skip."""
import json
import shutil
import subprocess
from pathlib import Path
from typing import Any, Dict, Iterable, List, Set, Tuple

from vole.sources.base import Installed, ScanContext


def parse_list_json(data: Dict[str, Any]) -> Tuple[List[Installed], Set[str]]:
    """Return (installed packages, exposed binary names on PATH)."""
    installed: List[Installed] = []
    shims: Set[str] = set()
    for _venv_name, body in sorted((data.get('venvs') or {}).items()):
        meta = (body or {}).get('metadata') or {}
        main = meta.get('main_package') or {}
        pkg = main.get('package') or ''
        ver = main.get('package_version') or ''
        if pkg:
            installed.append(Installed('pipx', pkg, [ver] if ver else []))
        for app in main.get('apps') or []:
            if app:
                shims.add(app)
        for dep_apps in (main.get('apps_of_dependencies') or {}).values():
            for app in dep_apps or []:
                if app:
                    shims.add(app)
    return installed, shims


def collect(home: Path) -> Tuple[List[Installed], Set[str]]:
    """Run `pipx list --json`. Empty if pipx is missing or the output is unusable."""
    if not shutil.which('pipx'):
        return [], set()
    try:
        proc = subprocess.run(
            ['pipx', 'list', '--json'],
            capture_output=True, text=True, timeout=60)
        if not proc.stdout.strip():
            return [], set()
        data = json.loads(proc.stdout)
    except (OSError, subprocess.TimeoutExpired, json.JSONDecodeError):
        return [], set()
    if not isinstance(data, dict):
        return [], set()
    return parse_list_json(data)


def discover(ctx: ScanContext) -> Iterable[Installed]:
    items, shims = collect(ctx.home)
    ctx.claimed_bins |= shims
    yield from items
