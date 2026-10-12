"""Homebrew formulae and casks."""
import functools
import os
import shutil
import subprocess
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Set, Union

from vole.sources.base import Installed, ScanContext

# Known prefixes when env / `brew --prefix` are unavailable (Apple Silicon, Intel).
_FALLBACK_PREFIXES = (Path('/opt/homebrew'), Path('/usr/local'))


def _run(args) -> str:
    try:
        return subprocess.run(args, capture_output=True, text=True, timeout=120).stdout
    except (OSError, subprocess.TimeoutExpired):
        return ''


def _version_map(text):
    """'name v1 v2' lines from `brew list --versions` → {name: [versions]}."""
    out = {}
    for line in text.splitlines():
        parts = line.split()
        if len(parts) >= 2:
            out[parts[0]] = parts[1:]
    return out


@functools.lru_cache(maxsize=1)
def _resolve_caskroom() -> Path:
    """HOMEBREW_PREFIX → `brew --prefix` → first existing known path."""
    env = os.environ.get('HOMEBREW_PREFIX', '').strip()
    if env:
        return Path(env) / 'Caskroom'
    if shutil.which('brew'):
        prefix = _run(['brew', '--prefix']).strip()
        if prefix:
            return Path(prefix) / 'Caskroom'
    for prefix in _FALLBACK_PREFIXES:
        candidate = prefix / 'Caskroom'
        if candidate.is_dir():
            return candidate
    return _FALLBACK_PREFIXES[0] / 'Caskroom'


def caskroom(override: Optional[Union[str, Path]] = None) -> Path:
    """Homebrew Caskroom root (Apple Silicon, Intel, or custom prefix)."""
    if override is not None:
        return Path(override)
    return _resolve_caskroom()


def cask_apps(caskroom_path=None) -> Dict[str, str]:
    """{app name: owning cask} from one Caskroom walk — including symlink targets."""
    root = caskroom(caskroom_path)
    owners: Dict[str, str] = {}
    if not root.is_dir():
        return owners
    for version_dir in sorted(root.glob('*/*/')):
        if not version_dir.is_dir():
            continue
        cask = version_dir.parent.name
        for app in version_dir.glob('*.app'):
            if not app.exists():
                continue
            owners.setdefault(app.name[:-4], cask)
            if app.is_symlink():
                tgt = os.path.basename(os.path.realpath(app))
                if tgt.endswith('.app'):
                    owners.setdefault(tgt[:-4], cask)
    return owners


def cask_owned_apps(caskroom_path=None) -> Set[str]:
    """App names already tracked as a cask — including symlink targets."""
    return set(cask_apps(caskroom_path))

def formula_names(leaves_text: str, on_request_text: str) -> List[str]:
    """Union of `brew leaves` and `brew list --installed-on-request`, deduped by short name.

    leaves alone hides formulae you asked for that something else depends on (jq, openssl);
    on-request alone hides orphaned dependencies. Full tap names from leaves win.
    """
    by_short = {}
    for text in (leaves_text, on_request_text):
        for line in text.splitlines():
            name = line.strip()
            if name:
                by_short.setdefault(name.rsplit('/', 1)[-1], name)
    return sorted(by_short.values(), key=str.lower)


def _on_request() -> str:
    """Empty on Homebrew builds without `list --installed-on-request`."""
    try:
        proc = subprocess.run(['brew', 'list', '--formula', '--installed-on-request'],
                              capture_output=True, text=True, timeout=120)
    except (OSError, subprocess.TimeoutExpired):
        return ''
    return proc.stdout if proc.returncode == 0 else ''


def discover(ctx: ScanContext) -> Iterable[Installed]:
    ctx.cask_owned_apps |= cask_owned_apps()
    if not shutil.which('brew'):
        return
    formula_vers = _version_map(_run(['brew', 'list', '--versions']))
    cask_vers = _version_map(_run(['brew', 'list', '--cask', '--versions']))
    # brew leaves prints tapped formulae by full name; brew list --versions the short one
    for name in formula_names(_run(['brew', 'leaves']), _on_request()):
        short = name.rsplit('/', 1)[-1]
        vs = formula_vers.get(name) or formula_vers.get(short) or []
        yield Installed('brew-formula', name, list(vs))
    for name in _run(['brew', 'list', '--cask']).splitlines():
        name = name.strip()
        if not name:
            continue
        yield Installed('brew-cask', name, list(cask_vers.get(name) or []))
