"""Installed-software discovery contract."""
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, NamedTuple, Sequence, Set


class Installed(NamedTuple):
    source: str
    name: str
    versions: List[str]   # may be empty — version is best-effort


@dataclass
class ScanContext:
    """Shared state for one scan. Sources run in registry order; earlier ones publish
    facts that later ones read. Signals then read ``entries`` (inventory ∪ installed)."""
    home: Path
    cask_owned_apps: Set[str] = field(default_factory=set)   # filled by brew, read by apps
    claimed_bins: Set[str] = field(default_factory=set)      # filled by pipx/uv, read by bins
    entries: Sequence[str] = ()                              # set before signals run

# A source is any callable: discover(ctx: ScanContext) -> Iterable[Installed]
