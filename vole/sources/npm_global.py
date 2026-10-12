"""npm global packages — via --json so @scope/ names survive."""
import json
import shutil
import subprocess
from typing import Iterable, List

from vole.sources.base import Installed, ScanContext


def parse_ls_json(data) -> List[Installed]:
    """Parse `npm ls -g --depth=0 --json` object → Installed list."""
    out: List[Installed] = []
    for name, meta in (data.get('dependencies') or {}).items():
        ver = (meta or {}).get('version', '') or ''
        out.append(Installed('npm-global', name, [ver] if ver else []))
    return out


def discover(ctx: ScanContext) -> Iterable[Installed]:
    if not shutil.which('npm'):
        return
    try:
        out = subprocess.run(['npm', 'ls', '-g', '--depth=0', '--json'],
                             capture_output=True, text=True, timeout=60)
        data = json.loads(out.stdout) if out.stdout.strip() else {}
    except (OSError, subprocess.TimeoutExpired, json.JSONDecodeError):
        return
    yield from parse_ls_json(data)
