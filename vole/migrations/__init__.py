"""Ordered inventory migrations (ADR-008: each step bumps format by 1).

Add a module ``m00N_<id>.py`` exporting a ``Migration``, append it to ``STEPS``.
``FORMAT`` is 1 when ``STEPS`` is empty, else the last step’s ``target_format``.

Retiring a step: delete its module, remove it from ``STEPS``, and raise ``MIN_FORMAT``
to the first format this build can still migrate *from* (document in the module
docstring / STATUS before deleting).
"""
from vole.migrations.m002_strip_software_source import STEP as _m002
from vole.migrations.types import Migration, MigrateContext

# Oldest on-disk format this build will still migrate forward from.
MIN_FORMAT = 1

STEPS: tuple = (_m002,)

FORMAT = STEPS[-1].target_format if STEPS else 1

__all__ = ['FORMAT', 'MIN_FORMAT', 'STEPS', 'Migration', 'MigrateContext', 'apply_pending']


def apply_pending(data_dir, *, steps=None, min_format=None, code_format=None):
    """Apply pending migrations. Returns list of step ids applied."""
    from vole.migrations.runner import apply_pending as _apply
    return _apply(data_dir, steps=steps, min_format=min_format, code_format=code_format)
