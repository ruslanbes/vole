"""Registry of usage / dependency signals."""
from pathlib import Path
from typing import Dict, List

from vole.signals import app_state, config_refs, shell_history, spotlight
from vole.signals.base import Fact
from vole.sources.base import ScanContext

# Every signal is collect(ctx) -> SignalMap keyed by entry name.
SIGNALS = (
    spotlight.collect,
    shell_history.collect,
    app_state.collect,
    config_refs.collect,
)


def collect_all(home: Path, entry_names) -> Dict[str, List[Fact]]:
    """Merge signal facts keyed by entry name."""
    ctx = ScanContext(home=home, entries=tuple(entry_names))
    out: Dict[str, List[Fact]] = {}
    for collect in SIGNALS:
        for name, facts in collect(ctx).items():
            out.setdefault(name, []).extend(facts)
    return out
