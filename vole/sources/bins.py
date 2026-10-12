"""~/go/bin and ~/.local/bin."""
import shutil
import subprocess
from pathlib import Path
from typing import Iterable

from vole.sources.base import Installed, ScanContext

def _go_version(binary: Path) -> str:
    if not shutil.which('go'):
        return ''
    try:
        out = subprocess.run(['go', 'version', '-m', str(binary)],
                             capture_output=True, text=True, timeout=10)
    except (OSError, subprocess.TimeoutExpired):
        return ''
    for line in out.stdout.splitlines():
        parts = line.split()
        if len(parts) >= 3 and parts[0] == 'mod':
            return parts[2]
    return ''

def discover(ctx: ScanContext) -> Iterable[Installed]:
    """~/.local/bin names in ctx.claimed_bins (pipx/uv shims) are not listed as local-bin."""
    for rel, source in (('go/bin', 'go-install'), ('.local/bin', 'local-bin')):
        d = ctx.home / rel
        if not d.is_dir():
            continue
        for f in sorted(d.iterdir()):
            # exists() follows symlinks — dangling links are not installed software
            if not f.exists() or not f.is_file():
                continue
            if source == 'local-bin' and f.name in ctx.claimed_bins:
                continue
            ver = _go_version(f) if source == 'go-install' else ''
            yield Installed(source, f.name, [ver] if ver else [])
