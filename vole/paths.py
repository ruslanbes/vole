"""Where vole keeps its data."""
import os
from pathlib import Path

DATA_FILES = ('software', 'dropped', 'versions')

def data_dir() -> Path:
    """~/.config/vole, or $VOLE_DATA_DIR when tests (or a user) override it."""
    override = os.environ.get('VOLE_DATA_DIR')
    if override:
        return Path(override).expanduser()
    return Path.home() / '.config' / 'vole'

def software_path(root=None) -> Path:
    return (root or data_dir()) / 'software.json'

def dropped_path(root=None) -> Path:
    return (root or data_dir()) / 'dropped.json'

def versions_path(root=None) -> Path:
    return (root or data_dir()) / 'versions.json'

def ensure_data_dir(root=None) -> Path:
    """Create the data dir owner-only (0700). An existing dir keeps its mode."""
    d = root or data_dir()
    d.mkdir(mode=0o700, parents=True, exist_ok=True)
    return d

def inventory_paths(root=None):
    """The three inventory files, in a stable order."""
    root = root or data_dir()
    return [root / f'{name}.json' for name in DATA_FILES]
