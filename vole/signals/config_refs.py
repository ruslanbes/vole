"""Named in a shell/git config — a dependency fact, not a date."""
import re

from vole.signals.base import Fact, SignalMap
from vole.sources.base import ScanContext

# Relative to $HOME. Explicit on purpose: a blanket ~/.config walk would also read
# ~/.config/vole/software.json, which names every entry.
# Only files where a tool name means "this tool is wired in": ignore lists, prompt
# module names and .npmrc (tokens) produce coincidental matches.
CONFIG_FILES = (
    '.zshrc', '.zprofile', '.bash_profile', '.config/fish/config.fish',
    '.gitconfig', '.config/git/config',
    '.config/mise/config.toml',
)
MAX_BYTES = 1024 * 1024


def _read(path) -> str:
    try:
        if not path.is_file() or path.stat().st_size > MAX_BYTES:
            return ''
        return path.read_bytes().decode('utf-8', 'replace')
    except OSError:
        return ''


def collect(ctx: ScanContext) -> SignalMap:
    out: SignalMap = {}
    if not ctx.entries:
        return out
    blob = {}
    for rel in CONFIG_FILES:
        txt = _read(ctx.home / rel)
        if txt:
            blob[rel] = txt
    for name in ctx.entries:
        base = name.split('/')[-1]
        if len(base) < 3:
            continue
        pat = re.compile(rf'(?<![\w-]){re.escape(base)}(?![\w-])')
        for rel, txt in blob.items():
            if pat.search(txt):
                out[name] = [Fact(f'referenced in {rel}')]
                break
    return out
