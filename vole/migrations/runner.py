"""Apply pending inventory migrations for a data directory."""
from __future__ import annotations

import json
import shutil
from pathlib import Path
from typing import Dict, List, Optional, Sequence, Tuple

from vole import inventory, paths
from vole.migrations import FORMAT, MIN_FORMAT, STEPS
from vole.migrations.types import MigrateContext, Migration

_KIND = ('software', 'dropped', 'versions')


def _path_for(data_dir: Path, kind: str) -> Path:
    return {
        'software': paths.software_path(data_dir),
        'dropped': paths.dropped_path(data_dir),
        'versions': paths.versions_path(data_dir),
    }[kind]


def _read_format_and_apps(path: Path) -> Tuple[int, Dict]:
    text = path.read_text(encoding='utf-8')
    try:
        data = json.loads(text)
    except json.JSONDecodeError as e:
        raise ValueError(f'{path.name}: not valid JSON ({e})') from None
    if not isinstance(data, dict) or not isinstance(data.get('apps'), dict):
        raise ValueError(f'{path.name}: not a vole inventory (no "apps" object)')
    fmt = data.get('format')
    if not isinstance(fmt, int):
        raise ValueError(f'{path.name}: missing or invalid format {fmt!r}')
    return fmt, data['apps']


def _steps_by_target(steps: Sequence[Migration]) -> Dict[int, Migration]:
    out: Dict[int, Migration] = {}
    expected = 2
    for step in steps:
        if step.target_format != expected:
            raise RuntimeError(
                f'migration registry gap: expected target_format {expected}, '
                f'got {step.target_format} ({step.id})')
        out[step.target_format] = step
        expected += 1
    return out


def apply_pending(data_dir, *, steps: Optional[Sequence[Migration]] = None,
                  min_format: Optional[int] = None,
                  code_format: Optional[int] = None) -> List[str]:
    """Migrate inventory files in ``data_dir`` up to ``code_format``.

    Returns ids of steps applied. No-op if no inventory files exist.
    """
    data_dir = Path(data_dir)
    step_list = STEPS if steps is None else steps
    floor = MIN_FORMAT if min_format is None else min_format
    target = FORMAT if code_format is None else code_format
    by_target = _steps_by_target(step_list)

    present_kinds = []
    formats = []
    maps = {'software': {}, 'dropped': {}, 'versions': {}}
    for kind in _KIND:
        path = _path_for(data_dir, kind)
        if not path.exists():
            continue
        fmt, apps = _read_format_and_apps(path)
        present_kinds.append(kind)
        formats.append(fmt)
        maps[kind] = apps

    if not present_kinds:
        return []

    if len(set(formats)) != 1:
        raise ValueError(
            f'inventory format mismatch among {", ".join(present_kinds)}: {formats}')

    fmt = formats[0]
    if fmt > target:
        raise ValueError(
            f'inventory format {fmt} is newer than this vole ({target}); upgrade vole')
    if fmt < floor:
        raise ValueError(
            f'inventory format {fmt} is older than this vole can migrate '
            f'(minimum {floor}); restore a bak or use an intermediate vole release')

    applied: List[str] = []
    present = frozenset(present_kinds)
    while fmt < target:
        step = by_target.get(fmt + 1)
        if step is None:
            raise ValueError(
                f'no migration from format {fmt} to {fmt + 1} '
                f'(code format {target})')
        # Bak each present file at the pre-step format.
        for kind in present_kinds:
            src = _path_for(data_dir, kind)
            bak = src.with_name(f'{src.name}.format{fmt}.bak')
            shutil.copy2(src, bak)
        ctx = MigrateContext(
            data_dir=data_dir,
            software=maps['software'],
            dropped=maps['dropped'],
            versions=maps['versions'],
            present=present,
        )
        step.apply(ctx)
        new_fmt = step.target_format
        for kind in present_kinds:
            inventory.save(
                _path_for(data_dir, kind),
                {'software': ctx.software, 'dropped': ctx.dropped,
                 'versions': ctx.versions}[kind],
                format=new_fmt)
        maps['software'] = ctx.software
        maps['dropped'] = ctx.dropped
        maps['versions'] = ctx.versions
        applied.append(step.id)
        fmt = new_fmt
    return applied
