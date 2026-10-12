"""Spotlight kMDItemLastUsedDate for .app bundles; also under owning cask name."""
import subprocess
from pathlib import Path
from typing import List

from vole.signals.base import Fact, SignalMap
from vole.sources.apps import app_bundles
from vole.sources.base import ScanContext
from vole.sources.brew import cask_apps

_BATCH = 200


def _mdls(paths: List[Path]) -> List[str]:
    """Raw kMDItemLastUsedDate per path, '' when unknown or on error."""
    try:
        r = subprocess.run(
            ['mdls', '-name', 'kMDItemLastUsedDate', '-raw', *map(str, paths)],
            capture_output=True, text=True, timeout=10 + len(paths))
    except (OSError, subprocess.TimeoutExpired):
        return [''] * len(paths)
    if len(paths) == 1:
        # On failure mdls prints "<path>: could not find …" to stdout.
        return [r.stdout or ''] if r.returncode == 0 else ['']
    # Several paths: values are NUL-separated. One unreadable path aborts the rest and
    # garbles the output, so anything but an exact match means "ask one at a time".
    values = (r.stdout or '').split('\0')
    if r.returncode == 0 and len(values) == len(paths):
        return values
    return [_mdls([p])[0] for p in paths]


def last_used(apps: List[Path]) -> List[str]:
    """YYYY-MM-DD per app ('' when Spotlight has no date)."""
    days = []
    for i in range(0, len(apps), _BATCH):
        for raw in _mdls(apps[i:i + _BATCH]):
            raw = raw.strip()
            days.append(raw.split()[0] if raw and raw != '(null)' else '')
    return days


def collect(ctx: ScanContext) -> SignalMap:
    found: SignalMap = {}
    owners = cask_apps()
    bundles = app_bundles(ctx.home)
    for app, day in zip(bundles, last_used(bundles)):
        if not day:
            continue
        name = app.name[:-4]
        found[name] = [Fact(f'used {day}', day)]
        cask = owners.get(name)
        if cask:
            found[cask] = [Fact(f'used {day}', day)]
    if not ctx.entries:
        return found
    return {n: found[n] for n in ctx.entries if n in found}
