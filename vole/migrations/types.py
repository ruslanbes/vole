"""Migration step contract."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Dict, NamedTuple


@dataclass
class MigrateContext:
    """Mutable inventory maps for one data dir. Runner loads/saves around apply."""
    data_dir: Path
    software: Dict
    dropped: Dict
    versions: Dict
    # Which of software/dropped/versions existed on disk before this step.
    present: frozenset


class Migration(NamedTuple):
    """One format N → N+1 transform. ``target_format`` is N+1."""
    target_format: int
    id: str
    apply: Callable[[MigrateContext], None]
