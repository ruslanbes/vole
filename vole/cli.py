"""argparse entrypoint for the vole CLI."""
import argparse
import collections
import datetime
import json
import shutil
import sys
from pathlib import Path

from vole import __version__, inventory, paths, scan


def _load(path, missing_ok=False):
    try:
        return inventory.load(path, missing_ok=missing_ok)
    except (OSError, ValueError) as e:
        print(f'error: {e}', file=sys.stderr)
        sys.exit(1)


def _print_entry(name, entry, changed=(), removed=(), header=None):
    print(header or name)
    for k in sorted(entry):
        print(('  * ' if k in changed else '    ')
              + f'{k:<8} = {json.dumps(entry[k], ensure_ascii=False)}')
    if removed:
        print('    (removed: ' + ', '.join(removed) + ')')


def _collect_fields(args, keys=inventory.EDITABLE):
    fields = {}
    for key in keys:
        val = getattr(args, key, None)
        if val is not None:
            fields[key] = val
    return fields


def _apply_fields(entry, fields):
    for f, v in fields.items():
        entry = inventory.set_field(entry, f, v)
    return entry


def _near(name, *maps):
    keys = set()
    for m in maps:
        keys.update(m)
    return [k for k in sorted(keys, key=str.lower) if name.lower() in k.lower()]


def _no_entry(cmd, name, where, near_in=(), note=None):
    print(f'{cmd}: no entry named {name!r} in {where}', file=sys.stderr)
    if note:
        print(f'      ({note})', file=sys.stderr)
    near = _near(name, *near_in)
    if near:
        print('      did you mean: ' + ', '.join(near[:6]), file=sys.stderr)


def _apply(cmd, entry, fields):
    """entry with fields set, or None after printing why not."""
    try:
        return _apply_fields(entry, fields)
    except ValueError as e:
        print(f'{cmd}: {e}', file=sys.stderr)
        return None


def _confirm(cmd, force):
    if force:
        return True
    try:
        answer = input("Type 'yes' to confirm: ").strip().lower()
    except EOFError:
        answer = ''
    if answer in ('yes', 'y'):
        return True
    print(f'{cmd}: cancelled', file=sys.stderr)
    return False


class _Inventory:
    """software.json + dropped.json, loaded together for one command."""

    def __init__(self, data_dir):
        self.software = paths.software_path(data_dir)
        self.dropped = paths.dropped_path(data_dir)
        self.apps = _load(self.software, missing_ok=True)
        self.archived = _load(self.dropped, missing_ok=True)

    def where(self, name):
        if name in self.apps:
            return 'software'
        if name in self.archived:
            return 'dropped'
        return None

    def get(self, name):
        return self.apps[name] if name in self.apps else self.archived.get(name)

    def put(self, name, entry):
        """Save in place, in whichever file holds the entry (software for a new one)."""
        if self.where(name) == 'dropped':
            self.archived[name] = entry
            inventory.save(self.dropped, self.archived)
        else:
            self.apps[name] = entry
            inventory.save(self.software, self.apps)

    def archive(self, name, entry):
        inventory.move(name, entry, self.apps, self.software, self.archived, self.dropped)

    def restore(self, name, entry):
        inventory.move(name, entry, self.archived, self.dropped, self.apps, self.software)

    def both_names(self):
        return f'{self.software.name} or {self.dropped.name}'


def cmd_help(parser):
    def _help(_args):
        parser.print_help()
        return 0
    return _help


def cmd_scan(args):
    return scan.run(data_root=args.data_dir, months=args.months, write=not args.dry_run)


def cmd_list(args):
    software = paths.software_path(args.data_dir)
    vpath = paths.versions_path(args.data_dir)
    curated = _load(software, missing_ok=True)
    installed = {k: (e.get('source', ''), sorted(e.get('versions', [])))
                 for k, e in _load(vpath, missing_ok=True).items()}
    if not installed:
        print(f'no {vpath.name} yet — run `vole scan` once to record what is installed')
        return 0

    filt = (args.filter or '').lower()
    rows = []
    for name in sorted(installed, key=str.lower):
        source, vers = installed[name]
        e = curated.get(name)
        status = e.get('status', '') if e else '-'
        keep = (e.get('keep', '') if e else '') or '-'
        why = e.get('why', '') if e else f'(not in {software.name})'
        if filt and filt not in ' '.join((name, source, status, keep, why)).lower():
            continue
        rows.append([name, ', '.join(vers) or '-', source, status, keep, why])

    if not rows:
        print('no matches')
        return 0

    heads = ['NAME', 'VERSION', 'SOURCE', 'STATUS', 'KEEP', 'WHY']
    widths = [max(len(h), max(len(r[i]) for r in rows)) for i, h in enumerate(heads)]
    widths[1] = min(widths[1], 24)
    term = shutil.get_terminal_size((160, 24)).columns
    fixed = sum(widths[:-1]) + 3 * len(heads[:-1])
    widths[-1] = max(20, term - fixed - 1)

    def line(cells):
        out = []
        for i, c in enumerate(cells):
            if len(c) > widths[i]:
                c = c[:widths[i] - 1] + '\u2026'
            out.append(c.ljust(widths[i]) if i < len(cells) - 1 else c)
        return '   '.join(out).rstrip()

    print(line(heads))
    for r in rows:
        print(line(r))
    print()
    by = collections.Counter(r[2] for r in rows)
    kept = sum(1 for r in rows if r[4] != '-')
    todo = sum(1 for r in rows if r[5] in ('TODO', ''))
    print(f'{len(rows)} installed  |  ' + ', '.join(f'{v} {k}' for k, v in by.most_common())
          + f'  |  {kept} kept, {todo} without a reason')
    return 0


def cmd_edit(args):
    inv = _Inventory(args.data_dir)
    if not inv.software.exists() and not inv.dropped.exists():
        print(f'error: no inventory at {inv.software}', file=sys.stderr)
        return 1

    fields = _collect_fields(args)
    if not fields:
        print('edit: nothing to set — pass at least one of '
              + ', '.join('--' + f for f in inventory.EDITABLE), file=sys.stderr)
        return 2

    name = args.name
    where = inv.where(name)
    if where is None:
        _no_entry('edit', name, inv.both_names(), (inv.apps, inv.archived))
        return 1
    before = inv.get(name)
    entry = _apply('edit', before, fields)
    if entry is None:
        return 2
    removed = [f for f, v in fields.items() if v == '' and f in before]

    if fields.get('status') == 'dropped':
        entry = inventory.mark_user_drop(entry)
    elif fields.get('status') == 'active':
        entry = inventory.clear_archive_meta(entry)

    status = entry.get('status')
    if where == 'software' and status == 'dropped':
        inv.archive(name, entry)
        header = f'{name} → archived in {inv.dropped.name}'
    elif where == 'dropped' and status == 'active':
        inv.restore(name, entry)
        header = f'{name} → restored to {inv.software.name}'
    else:
        inv.put(name, entry)
        header = None if where == 'software' else f'{name} (in {inv.dropped.name})'
    _print_entry(name, entry, changed=fields, removed=removed, header=header)
    return 0


def cmd_drop(args):
    """Archive an entry — same as ``edit NAME --status dropped``."""
    return cmd_edit(argparse.Namespace(
        data_dir=args.data_dir, name=args.name,
        status='dropped', why=None, keep=None))


def cmd_restore(args):
    inv = _Inventory(args.data_dir)
    name = args.name
    if name not in inv.archived:
        note = f'already in {inv.software.name}' if name in inv.apps else None
        _no_entry('restore', name, inv.dropped.name, (inv.archived,), note=note)
        return 1
    if name in inv.apps:
        print(f'restore: {name!r} is already in {inv.software.name}', file=sys.stderr)
        return 1

    fields = _collect_fields(args, keys=('why', 'keep'))
    fields['status'] = 'active'
    entry = _apply('restore', inv.archived[name], fields)
    if entry is None:
        return 2
    entry = inventory.clear_archive_meta(entry)
    inv.restore(name, entry)
    _print_entry(name, entry, changed=fields,
                 header=f'{name} → restored to {inv.software.name}')
    return 0


def cmd_add(args):
    inv = _Inventory(args.data_dir)
    name = args.name
    if name in inv.apps:
        print(f'add: {name!r} already in {inv.software.name}', file=sys.stderr)
        return 1

    fields = _collect_fields(args, keys=('why', 'keep'))
    if name in inv.archived:
        changes = dict(fields, status='active')
        if args.source is not None:
            changes['source'] = args.source
        entry = _apply('add', inv.archived[name], changes)
        if entry is None:
            return 2
        entry = inventory.clear_archive_meta(entry)
        inv.restore(name, entry)
        _print_entry(name, entry, changed=changes,
                     header=f'{name} → restored to {inv.software.name} (add)')
        return 0

    if not args.source:
        print('add: --source is required when creating a new entry', file=sys.stderr)
        return 2
    entry = _apply('add', inventory.stub(args.source, datetime.date.today().isoformat()), fields)
    if entry is None:
        return 2
    inv.put(name, entry)
    _print_entry(name, entry, changed={'source', 'why', 'added', 'status', *fields},
                 header=f'{name} → added to {inv.software.name}')
    return 0


def cmd_delete(args):
    inv = _Inventory(args.data_dir)
    vpath = paths.versions_path(args.data_dir)
    versions = _load(vpath, missing_ok=True)
    name = args.name
    where = inv.where(name)
    if where is None:
        _no_entry('delete', name, inv.both_names())
        return 1
    store, path = (inv.apps, inv.software) if where == 'software' else (inv.archived, inv.dropped)

    print(f'This will permanently delete {name!r} from {path.name}'
          + (f' and {vpath.name}' if name in versions else '') + '.')
    if not _confirm('delete', args.force):
        return 1

    del store[name]
    inventory.save(path, store)
    print(f'deleted {name!r} from {path.name}')
    if name in versions:
        del versions[name]
        inventory.save(vpath, versions)
        print(f'deleted {name!r} from {vpath.name}')
    return 0


def cmd_reset(args):
    """Delete software.json, dropped.json and versions.json from the data directory."""
    existing = [p for p in paths.inventory_paths(args.data_dir) if p.exists()]
    if not existing:
        print(f'nothing to reset — no inventory files in {args.data_dir}')
        return 0

    print('This will permanently delete:')
    for p in existing:
        print(f'  {p}')
    if not _confirm('reset', args.force):
        return 1

    for p in existing:
        p.unlink()
        print(f'deleted {p}')
    return 0


def build_parser():
    p = argparse.ArgumentParser(
        prog='vole',
        description='Record why each piece of software on this Mac is installed.')
    p.add_argument('--version', action='version', version=f'vole {__version__}')
    p.add_argument('--data-dir', type=Path, default=None,
                   help='inventory directory (default: ~/.config/vole, or $VOLE_DATA_DIR)')
    sub = p.add_subparsers(dest='command')

    help_p = sub.add_parser('help', help='show this help message')
    help_p.set_defaults(func=cmd_help(p))

    scan = sub.add_parser('scan', help='scan the machine, update inventory, print the report')
    scan.add_argument('--dry-run', action='store_true', help='report only, never write')
    scan.add_argument('--months', type=int, default=6, help='staleness threshold (default 6)')
    scan.set_defaults(func=cmd_scan)

    lst = sub.add_parser('list', help='table of everything installed: version + why')
    lst.add_argument('filter', nargs='?', default='', help='substring filter')
    lst.set_defaults(func=cmd_list)

    edit = sub.add_parser(
        'edit',
        help='set fields on one entry in software.json or dropped.json '
             '(--status dropped archives; --status active restores)')
    edit.add_argument('name')
    for f in inventory.EDITABLE:
        if f == 'status':
            edit.add_argument('--status', default=None, choices=sorted(inventory.STATUSES))
        else:
            edit.add_argument('--' + f, default=None, help='empty string removes the field')
    edit.set_defaults(func=cmd_edit)

    add = sub.add_parser('add', help='create an entry, or restore from dropped.json and set fields')
    add.add_argument('name')
    add.add_argument('--source', default=None,
                     help='required when creating a new entry')
    add.add_argument('--why', default=None)
    add.add_argument('--keep', default=None)
    add.set_defaults(func=cmd_add)

    drop = sub.add_parser('drop', help='archive an entry (alias for edit --status dropped)')
    drop.add_argument('name')
    drop.set_defaults(func=cmd_drop)

    restore = sub.add_parser('restore', help='move an entry from dropped.json back to software.json')
    restore.add_argument('name')
    restore.add_argument('--why', default=None)
    restore.add_argument('--keep', default=None)
    restore.set_defaults(func=cmd_restore)

    delete = sub.add_parser('delete', help='permanently remove an entry from software or dropped')
    delete.add_argument('name')
    delete.add_argument('--force', action='store_true', help='skip the confirmation prompt')
    delete.set_defaults(func=cmd_delete)

    reset = sub.add_parser('reset', help='delete all inventory data (software, dropped, versions)')
    reset.add_argument('--force', action='store_true',
                       help='skip the confirmation prompt')
    reset.set_defaults(func=cmd_reset)

    return p


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    parser = build_parser()
    args = parser.parse_args(argv)
    args.data_dir = args.data_dir or paths.data_dir()

    if args.command is None:
        parser.print_help()
        return 0

    try:
        return args.func(args)
    except OSError as e:
        print(f'error: {e}', file=sys.stderr)
        return 1
