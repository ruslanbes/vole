"""/Applications and ~/Applications, skipping cask-owned apps and Steam stubs."""
import subprocess
from pathlib import Path
from typing import Iterable, List

from vole.sources.base import Installed, ScanContext
from vole.sources.steam import is_steam_stub


def app_bundles(home: Path, roots: Iterable[Path] = None) -> List[Path]:
    """Top-level .app bundles plus one folder down (Utilities, vendor suites)."""
    found = []
    for base in roots or (Path('/Applications'), home / 'Applications'):
        if not base.is_dir():
            continue
        top = sorted(base.glob('*.app'))
        # "<Browser> Apps.localized" holds Chrome/Brave/Edge web-app shortcuts, not installs.
        nested = sorted(p for p in base.glob('*/*.app')
                        if p.parent.suffix != '.app'
                        and not p.parent.name.endswith(' Apps.localized'))
        found.extend(app for app in top + nested if app.exists())
    return found


def _app_version(app: Path) -> str:
    plist = app / 'Contents' / 'Info.plist'
    try:
        out = subprocess.run(
            ['defaults', 'read', str(plist), 'CFBundleShortVersionString'],
            capture_output=True, text=True, timeout=10)
        return out.stdout.strip() if out.returncode == 0 else ''
    except (OSError, subprocess.TimeoutExpired):
        return ''


def discover(ctx: ScanContext) -> Iterable[Installed]:
    for app in app_bundles(ctx.home):
        name = app.name[:-4]
        if name in ctx.cask_owned_apps:
            continue
        if is_steam_stub(app):
            continue  # installed games come from steam manifests; leftovers stay hidden
        source = 'app-store' if (app / 'Contents' / '_MASReceipt' / 'receipt').exists() else 'app'
        ver = _app_version(app)
        yield Installed(source, name, [ver] if ver else [])
