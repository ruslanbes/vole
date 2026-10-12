"""Cargo user installs — `cargo install --list`, else `~/.cargo/bin`."""
import re
import shutil
import subprocess
from pathlib import Path
from typing import Iterable, List

from vole.sources.base import Installed, ScanContext

# "ripgrep v14.1.0:" or "ripgrep 14.1.0:"
_PKG = re.compile(r'^(\S+)\s+v?([^:]+):\s*$')


def parse_install_list(text: str) -> List[Installed]:
    """One Installed per package; binary lines under a package are ignored."""
    out: List[Installed] = []
    for line in text.splitlines():
        if line[:1].isspace():
            continue
        m = _PKG.match(line)
        if not m:
            continue
        name, ver = m.group(1), m.group(2).strip()
        out.append(Installed('cargo', name, [ver] if ver else []))
    return out


def _from_bin_dir(home: Path) -> Iterable[Installed]:
    d = home / '.cargo' / 'bin'
    if not d.is_dir():
        return
    for f in sorted(d.iterdir()):
        if not f.exists() or not f.is_file():
            continue
        yield Installed('cargo', f.name, [])


def discover(ctx: ScanContext) -> Iterable[Installed]:
    if shutil.which('cargo'):
        try:
            proc = subprocess.run(
                ['cargo', 'install', '--list'],
                capture_output=True, text=True, timeout=60)
        except (OSError, subprocess.TimeoutExpired):
            proc = None
        if proc is not None and proc.returncode == 0:
            yield from parse_install_list(proc.stdout)
            return
    yield from _from_bin_dir(ctx.home)
