"""uv tool installs — `uv tool list`, with shim names for bins skip."""
import json
import re
import shutil
import subprocess
from pathlib import Path
from typing import Any, Iterable, List, Set, Tuple, Union

from vole.sources.base import Installed, ScanContext

# "ruff v0.3.0" or "ruff v0.3.0 (/path)" or "ruff v0.3.0 (>=1.0)"
_TOOL = re.compile(r'^(\S+)\s+v([^\s(]+)')


def parse_list_text(text: str) -> Tuple[List[Installed], Set[str]]:
    """Parse `uv tool list` / `uv tool list --show-paths` human output."""
    installed: List[Installed] = []
    shims: Set[str] = set()
    for raw in text.splitlines():
        line = raw.rstrip()
        if not line.strip() or line.strip().lower() == 'no tools installed':
            continue
        stripped = line.lstrip()
        if stripped.startswith('-'):
            path = stripped[1:].strip()
            if path:
                shims.add(Path(path).name)
            continue
        m = _TOOL.match(line)
        if not m:
            continue
        name, ver = m.group(1), m.group(2)
        installed.append(Installed('uv-tool', name, [ver] if ver else []))
        # Best-effort when --show-paths is absent: package name often matches the binary.
        shims.add(name)
    return installed, shims


def parse_list_json(data: Union[List[Any], dict]) -> Tuple[List[Installed], Set[str]]:
    """Parse `uv tool list --output-format=json` when the uv build supports it."""
    rows = data if isinstance(data, list) else []
    installed: List[Installed] = []
    shims: Set[str] = set()
    for row in rows:
        if not isinstance(row, dict):
            continue
        name = row.get('name') or ''
        ver = row.get('version') or ''
        if not name:
            continue
        installed.append(Installed('uv-tool', name, [ver] if ver else []))
        shims.add(name)
        for ep in row.get('entrypoints') or row.get('executables') or []:
            if isinstance(ep, dict):
                n = ep.get('name') or (Path(ep['path']).name if ep.get('path') else '')
            elif isinstance(ep, str):
                n = Path(ep).name
            else:
                n = ''
            if n:
                shims.add(n)
    return installed, shims


def collect(home: Path) -> Tuple[List[Installed], Set[str]]:
    if not shutil.which('uv'):
        return [], set()
    # Prefer JSON when this uv supports it (newer builds).
    try:
        proc = subprocess.run(
            ['uv', 'tool', 'list', '--output-format=json'],
            capture_output=True, text=True, timeout=60)
        if proc.returncode == 0 and proc.stdout.strip().startswith(('[', '{')):
            data = json.loads(proc.stdout)
            return parse_list_json(data)
    except (OSError, subprocess.TimeoutExpired, json.JSONDecodeError):
        pass
    try:
        proc = subprocess.run(
            ['uv', 'tool', 'list', '--show-paths'],
            capture_output=True, text=True, timeout=60)
    except (OSError, subprocess.TimeoutExpired):
        return [], set()
    # "No tools installed" is often on stderr with empty stdout — treat as empty.
    text = proc.stdout or ''
    if not text.strip():
        return [], set()
    return parse_list_text(text)


def discover(ctx: ScanContext) -> Iterable[Installed]:
    items, shims = collect(ctx.home)
    ctx.claimed_bins |= shims
    yield from items
