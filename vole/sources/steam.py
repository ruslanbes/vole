"""Steam games from appmanifests; ignore leftover ~/Applications stubs."""
import re
from pathlib import Path
from typing import Dict, Iterable, List, Optional

from vole.sources.base import Installed, ScanContext

_STEAM_RUN = re.compile(r'steam://run/(\d+)')
_KV = re.compile(r'"([^"]+)"\s+"([^"]*)"')


def is_steam_stub(app: Path) -> bool:
    """True for Steam’s thin ~/Applications launcher (run.sh → steam://run/<id>)."""
    run = app / 'Contents' / 'MacOS' / 'run.sh'
    if not run.is_file():
        return False
    try:
        return 'steam://run/' in run.read_text(encoding='utf-8', errors='replace')
    except OSError:
        return False


def _kv_first(text: str, keys: frozenset) -> Dict[str, str]:
    """First occurrence of each quoted key (AppState / libraryfolders fields)."""
    out: Dict[str, str] = {}
    for key, val in _KV.findall(text):
        if key in keys and key not in out:
            out[key] = val
    return out


def parse_manifest(text: str) -> Optional[Installed]:
    """One appmanifest_*.acf → Installed, or None if incomplete / not fully installed."""
    fields = _kv_first(text, frozenset({'name', 'appid', 'buildid', 'StateFlags'}))
    name = (fields.get('name') or '').strip()
    if not name:
        return None
    # Steam StateFlags is a bitmask; bit 2 (value 4) = Fully Installed.
    try:
        flags = int(fields.get('StateFlags') or '0')
    except ValueError:
        flags = 0
    if flags & 4 == 0:
        return None
    build = (fields.get('buildid') or '').strip()
    return Installed('steam', name, [build] if build else [])


def library_roots(home: Path) -> List[Path]:
    """Steam library roots from libraryfolders.vdf (plus the default Support path)."""
    default = home / 'Library' / 'Application Support' / 'Steam'
    found: List[Path] = []
    seen = set()
    for vdf in (
        default / 'config' / 'libraryfolders.vdf',
        default / 'steamapps' / 'libraryfolders.vdf',
    ):
        if not vdf.is_file():
            continue
        try:
            text = vdf.read_text(encoding='utf-8', errors='replace')
        except OSError:
            continue
        for key, val in _KV.findall(text):
            if key != 'path' or not val:
                continue
            root = Path(val)
            key_s = str(root)
            if key_s in seen:
                continue
            seen.add(key_s)
            found.append(root)
    if default.is_dir():
        key_s = str(default)
        if key_s not in seen:
            found.insert(0, default)
    return found


def discover(ctx: ScanContext) -> Iterable[Installed]:
    seen_names = set()
    for root in library_roots(ctx.home):
        apps_dir = root / 'steamapps'
        if not apps_dir.is_dir():
            continue
        for manifest in sorted(apps_dir.glob('appmanifest_*.acf')):
            try:
                text = manifest.read_text(encoding='utf-8', errors='replace')
            except OSError:
                continue
            item = parse_manifest(text)
            if item is None or item.name in seen_names:
                continue
            seen_names.add(item.name)
            yield item
