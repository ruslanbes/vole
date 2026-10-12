"""Discover → signal → classify → maybe write → print."""
import collections
import datetime
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Tuple

from vole import inventory, paths, versions as versions_mod
from vole.signals import collect_all
from vole.signals.base import Fact
from vole.sources import discover_all

Installed = Dict[str, Tuple[str, List[str]]]   # name -> (source, versions)


@dataclass
class Report:
    new: List[Tuple[str, str]] = field(default_factory=list)          # (name, source)
    gone: List[str] = field(default_factory=list)
    todo: List[str] = field(default_factory=list)
    kept: List[Tuple[str, str]] = field(default_factory=list)         # (name, keep reason)
    stale: List[Tuple[str, str, str, str]] = field(default_factory=list)  # name, source, version, reason
    resurrected: List[Tuple[str, str]] = field(default_factory=list)  # (name, reason)
    archived_now: List[str] = field(default_factory=list)             # gone → dropped this write scan
    restored_now: List[str] = field(default_factory=list)             # auto-restored this write scan
    v_changed: List[Tuple[str, str, str]] = field(default_factory=list)
    v_added: List[Tuple[str, str]] = field(default_factory=list)
    v_removed: List[Tuple[str, str]] = field(default_factory=list)

    def versions_moved(self) -> bool:
        return bool(self.v_changed or self.v_added or self.v_removed)

    def empty(self) -> bool:
        return not (self.new or self.gone or self.todo or self.stale or self.resurrected
                    or self.archived_now or self.restored_now or self.versions_moved())


def classify(entries: Dict, archived: Dict, installed: Installed,
             facts: Dict[str, List[Fact]], cutoff: str, prev_versions: Dict) -> Report:
    """Pure: no I/O. cutoff is YYYY-MM-DD; older dated signals make an entry stale."""
    r = Report()

    for name, (src, _vs) in sorted(installed.items()):
        if name in archived:
            a = archived[name]
            r.resurrected.append((name, 'pruned as dropped (' + a.get('added', '') + '): '
                                        + a.get('why', '')[:70]))
        elif name not in entries:
            r.new.append((name, src))

    for name, kv in sorted(entries.items()):
        status = kv.get('status', '')
        if status == 'dropped':
            if name in installed:
                r.resurrected.append((name, 'marked dropped but still installed'))
            continue
        if name not in installed:
            r.gone.append(name)
            continue
        if kv.get('why', '') in ('', 'TODO'):
            r.todo.append(name)
        kept = kv.get('keep', '')
        if kept:
            r.kept.append((name, kept))
            continue
        labels, newest = [], None
        for fact in facts.get(name, []):
            labels.append(fact.label)
            if fact.date:
                newest = max(newest or '', fact.date)
        src, vs = installed[name]
        ver = ', '.join(sorted(vs)) or '-'
        if newest and newest < cutoff:
            r.stale.append((name, src, ver,
                            f'no signal since {newest} ({"; ".join(labels)})'))
        elif not labels and status == 'active':
            r.stale.append((name, src, ver,
                            'no usage signal at all — needs a manual look'))

    # versions.json records every installed name; the diff only covers detectable versions,
    # so unversioned installs never show up as "+ (none)" / "- gone".
    prev = {k: sorted(e.get('versions', [])) for k, e in prev_versions.items()
            if e.get('versions')}
    current = {n: sorted(vs) for n, (_s, vs) in installed.items() if vs}
    r.v_changed, r.v_added, r.v_removed = versions_mod.diff(prev, current)
    return r


def apply_auto_moves(entries: Dict, archived: Dict, installed: Installed, report: Report) -> None:
    """Archive gone entries; restore non-sticky dropped that are installed again.

    Mutates entries, archived, and report in place. Call only on write scans.
    """
    for name in list(report.gone):
        if name not in entries:
            continue
        entry = inventory.mark_scan_drop(entries[name])
        archived[name] = entry
        del entries[name]
        report.archived_now.append(name)
    report.gone = []

    still: List[Tuple[str, str]] = []
    for name, why in report.resurrected:
        if name in archived:
            if inventory.sticky_drop(archived[name]):
                still.append((name, why))
                continue
            entries[name] = inventory.clear_archive_meta(archived[name])
            del archived[name]
            report.restored_now.append(name)
        elif name in entries and entries[name].get('status') == 'dropped':
            if inventory.sticky_drop(entries[name]):
                still.append((name, why))
                continue
            entries[name] = inventory.clear_archive_meta(entries[name])
            report.restored_now.append(name)
        else:
            still.append((name, why))
    report.resurrected = still


def render(r: Report, *, tracked: int, installed: int, write: bool, had_baseline: bool) -> str:
    out = [f'tracked: {tracked}   installed: {installed}']

    def section(title, rows, limit=None):
        out.append('')
        out.append(title)
        shown = rows if limit is None else rows[:limit]
        out.extend(shown)
        if limit is not None and len(rows) > limit:
            out.append(f'  … and {len(rows) - limit} more')

    if r.new:
        section(f"NEW — {'stubs added' if write else 'not recorded'} ({len(r.new)}):",
                [f'  {n:<40} {s}' for n, s in r.new], limit=40)
    if r.archived_now:
        section(f'ARCHIVED — no longer installed ({len(r.archived_now)}):',
                [f'  {n}' for n in r.archived_now])
    elif r.gone:
        section(f'NO LONGER INSTALLED ({len(r.gone)}) — will archive on next write scan:',
                [f'  {n}' for n in r.gone])
    if r.restored_now:
        section(f'RESTORED — reinstalled after auto-archive ({len(r.restored_now)}):',
                [f'  {n}' for n in r.restored_now])
    if r.todo:
        section(f'MISSING A REASON ({len(r.todo)}):', [f'  {n}' for n in r.todo], limit=40)
    if r.kept:
        by = collections.Counter(k for _, k in r.kept)
        section(f'KEEP ({len(r.kept)}): '
                + ', '.join(f'{v} {k}' for k, v in sorted(by.items(), key=lambda x: -x[1])), [])
    if not had_baseline:
        section(f'VERSIONS: baseline recorded, {installed} entries'
                + ('' if write else ' — not written (--dry-run)'), [])
    elif r.versions_moved():
        n = len(r.v_changed) + len(r.v_added) + len(r.v_removed)
        section(f'VERSIONS ({n} changed since last scan'
                + ('' if write else '; --dry-run, so the baseline is unchanged') + '):',
                [f'  {name:<34} {old}  ->  {newv}' for name, old, newv in r.v_changed]
                + [f'  {name:<34} + {ver}' for name, ver in r.v_added]
                + [f'  {name:<34} - gone (was {old})' for name, old in r.v_removed])
    if r.resurrected:
        section(f'DROPPED BUT PRESENT ({len(r.resurrected)}):',
                [f'  {n:<40} {why}' for n, why in r.resurrected])
    if r.stale:
        section(f'DROP CANDIDATES ({len(r.stale)}):',
                [f'  {n:<28} {ver:<16} {src:<14} {why}'
                 for n, src, ver, why in r.stale])
    if r.empty():
        section('nothing to review.', [])
    return '\n'.join(out) + '\n'


def run(data_root: Path = None, home: Path = None, months: int = 6, write: bool = True) -> int:
    data_root = data_root or paths.data_dir()
    home = Path(home or Path.home())
    software = paths.software_path(data_root)
    dropped = paths.dropped_path(data_root)
    vpath = paths.versions_path(data_root)

    if not software.exists():
        if not write:
            print(f'no inventory at {software} — run `vole scan` once (without --dry-run)',
                  file=sys.stderr)
            return 1
        paths.ensure_data_dir(data_root)
        inventory.save(software, {})
        print(f'created {software}', file=sys.stderr)

    try:
        entries = inventory.load(software)
        archived = inventory.load(dropped, missing_ok=True)
        prev_versions = inventory.load(vpath, missing_ok=True)
    except (OSError, ValueError) as e:
        print(f'error: {e}', file=sys.stderr)
        return 1

    # Shape warnings (no dedicated check command) — scan continues.
    shape_problems = (
        inventory.check_apps(entries, software.name)
        + inventory.check_apps(archived, dropped.name)
        + inventory.check_apps(prev_versions, vpath.name, versions_file=True)
    )
    if shape_problems:
        print(f'INVENTORY SHAPE ({len(shape_problems)}):', file=sys.stderr)
        for msg in shape_problems:
            print(f'  {msg}', file=sys.stderr)

    installed = discover_all(home)
    today = datetime.date.today()
    cutoff = (today - datetime.timedelta(days=months * 30)).isoformat()
    facts = collect_all(home, list(entries) + list(archived) + list(installed))
    report = classify(entries, archived, installed, facts, cutoff, prev_versions)

    had_baseline = vpath.exists()
    if write:
        apply_auto_moves(entries, archived, installed, report)
        if report.new:
            for name, src in report.new:
                entries[name] = inventory.stub(src, today.isoformat())
        inventory.save(software, entries)
        inventory.save(dropped, archived)
        inventory.save(vpath, {n: {'source': s, 'versions': sorted(vs)}
                               for n, (s, vs) in installed.items()})

    print(render(report, tracked=len(entries), installed=len(installed),
                 write=write, had_baseline=had_baseline), end='')
    return 0
