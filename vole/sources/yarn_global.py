"""Yarn classic global packages — `yarn global list --json`; Berry is a no-op."""
import json
import re
import shutil
import subprocess
from typing import Iterable, List, Tuple

from vole.sources.base import Installed, ScanContext

# NDJSON info line data: "\"pkg@1.2.3\" has binaries:" or "\"@scope/cli@1.0.0\" has binaries:"
_INFO = re.compile(r'"([^"]+)"\s+has binaries:')


def split_spec(spec: str) -> Tuple[str, str]:
    """Split name@version / @scope/name@version into (name, version)."""
    if spec.startswith('@'):
        # @scope/name@version — version is after the last @
        name, _, ver = spec.rpartition('@')
        return name, ver
    name, _, ver = spec.partition('@')
    return name, ver


def parse_list_ndjson(text: str) -> List[Installed]:
    """Parse Yarn classic `--json` NDJSON stream from `yarn global list`."""
    by = {}
    for line in text.splitlines():
        line = line.strip()
        if not line.startswith('{'):
            continue
        try:
            obj = json.loads(line)
        except json.JSONDecodeError:
            continue
        if obj.get('type') != 'info':
            continue
        data = obj.get('data') or ''
        if not isinstance(data, str):
            continue
        m = _INFO.search(data)
        if not m:
            continue
        name, ver = split_spec(m.group(1))
        if name:
            by[name] = ver
    return [Installed('yarn-global', name, [ver] if ver else [])
            for name, ver in sorted(by.items())]


def discover(ctx: ScanContext) -> Iterable[Installed]:
    if not shutil.which('yarn'):
        return
    try:
        # Classic: works. Berry: typically errors ("global" unsupported) → empty.
        proc = subprocess.run(
            ['yarn', 'global', 'list', '--json', '--depth', '0'],
            capture_output=True, text=True, timeout=60)
    except (OSError, subprocess.TimeoutExpired):
        return
    text = proc.stdout or ''
    if not text.strip():
        return
    # Berry / broken yarn often prints a single non-NDJSON error object or human text.
    yield from parse_list_ndjson(text)
