"""Ollama models from the on-disk manifest tree (not `ollama list`)."""
import json
from pathlib import Path
from typing import Iterable

from vole.sources.base import Installed, ScanContext

def _digest(manifest: Path) -> str:
    try:
        data = json.loads(manifest.read_text(encoding='utf-8'))
        return data['config']['digest'].split(':')[-1][:12]
    except (OSError, KeyError, IndexError, json.JSONDecodeError, TypeError):
        return ''

def discover(ctx: ScanContext) -> Iterable[Installed]:
    root = ctx.home / '.ollama' / 'models' / 'manifests'
    if not root.is_dir():
        return
    for f in sorted(root.rglob('*')):
        if not f.is_file():
            continue
        rel = f.relative_to(root).as_posix()
        # manifests/<registry>/<namespace>/<model>/<tag>
        parts = rel.split('/')
        if len(parts) < 3:
            continue
        rest = parts[1:]                       # drop registry host
        if rest[0] == 'library':
            rest = rest[1:]
        if len(rest) < 2:
            continue
        tag = rest[-1]
        model = '/'.join(rest[:-1])
        name = f'{model}:{tag}'
        dig = _digest(f)
        yield Installed('ollama', name, [dig] if dig else [])
