"""Registry of installed-software sources."""
from pathlib import Path
from typing import Dict, List, Tuple

from vole.sources import (
    apps, asdf, bins, brew, cargo, mise, npm_global, ollama, pipx, pnpm_global,
    steam, uv_tool, yarn_global,
)
from vole.sources.base import ScanContext

# Order matters twice: first source wins a name clash, and sources that publish into
# ScanContext (brew, pipx, uv_tool) must run before the ones that read it (apps, bins).
# steam before apps so installed games win the name; apps skips Steam stubs either way.
SOURCES = (
    brew.discover,
    steam.discover,
    apps.discover,
    cargo.discover,
    pipx.discover,
    uv_tool.discover,
    bins.discover,
    npm_global.discover,
    yarn_global.discover,
    pnpm_global.discover,
    mise.discover,
    asdf.discover,
    ollama.discover,
)

def discover_all(home: Path) -> Dict[str, Tuple[str, List[str]]]:
    """{name: (source, versions)} — first source wins if a name appears twice."""
    ctx = ScanContext(home=home)
    installed: Dict[str, Tuple[str, List[str]]] = {}
    for discover in SOURCES:
        for item in discover(ctx):
            if item.name in installed:
                _src, vs = installed[item.name]
                for v in item.versions:
                    if v and v not in vs:
                        vs.append(v)
            else:
                installed[item.name] = (item.source, list(item.versions))
    return installed
