"""Usage / dependency signal contract.

A signal is any callable ``collect(ctx: ScanContext) -> SignalMap``. Facts are keyed by
entry name (from ``ctx.entries``). Dated facts contribute to "newest activity";
dependency facts only stop an entry looking like it has no signal at all.
"""
from typing import Dict, List, NamedTuple, Optional


class Fact(NamedTuple):
    label: str                 # e.g. "shell 2026-01-02" or "referenced in .zshrc"
    date: Optional[str] = None # YYYY-MM-DD when it is a dated fact

SignalMap = Dict[str, List[Fact]]   # entry name -> facts
