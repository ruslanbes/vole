"""Format 1 → 2: remove ``source`` from active software.json entries.

Dropped entries keep any existing ``source``. Live provenance lives on versions.json;
archives get ``source`` copied from versions at drop time (see inventory.attach_drop_source).

Safe to delete this module only after wild installs are past format 2 (raise MIN_FORMAT).
"""
from vole.migrations.types import MigrateContext, Migration


def apply(ctx: MigrateContext) -> None:
    if 'software' not in ctx.present:
        return
    for name, entry in list(ctx.software.items()):
        if 'source' not in entry:
            continue
        updated = dict(entry)
        del updated['source']
        ctx.software[name] = updated


STEP = Migration(target_format=2, id='strip-software-source', apply=apply)
