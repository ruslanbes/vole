"""Inventory migration runner tests."""
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from vole import inventory, paths  # noqa: E402
from vole.migrations import apply_pending  # noqa: E402
from vole.migrations.types import Migration, MigrateContext  # noqa: E402


def _write(path: Path, apps: dict, fmt: int = 1):
    path.write_text(json.dumps({'format': fmt, 'apps': apps}, indent=2) + '\n')


def _mark(ctx: MigrateContext) -> None:
    """Test step 1→2: set a marker on every software entry."""
    for name, entry in list(ctx.software.items()):
        updated = dict(entry)
        updated['migrated'] = 'yes'
        ctx.software[name] = updated


STEP_2 = Migration(target_format=2, id='test-mark', apply=_mark)


class TestApplyPending(unittest.TestCase):
    def setUp(self):
        self.d = Path(tempfile.mkdtemp())

    def tearDown(self):
        shutil.rmtree(self.d)

    def test_empty_dir_is_noop(self):
        self.assertEqual(apply_pending(self.d, steps=(STEP_2,), code_format=2), [])

    def test_already_current_is_noop(self):
        _write(self.d / 'software.json', {'jq': {'why': 'x'}}, fmt=1)
        self.assertEqual(apply_pending(self.d, steps=(), code_format=1), [])

    def test_applies_step_writes_bak_and_bumps(self):
        soft = self.d / 'software.json'
        _write(soft, {'jq': {'why': 'JSON', 'status': 'active'}}, fmt=1)
        applied = apply_pending(self.d, steps=(STEP_2,), code_format=2, min_format=1)
        self.assertEqual(applied, ['test-mark'])
        bak = self.d / 'software.json.format1.bak'
        self.assertTrue(bak.is_file())
        bak_data = json.loads(bak.read_text())
        self.assertEqual(bak_data['format'], 1)
        self.assertNotIn('migrated', bak_data['apps']['jq'])
        data = json.loads(soft.read_text())
        self.assertEqual(data['format'], 2)
        self.assertEqual(data['apps']['jq']['migrated'], 'yes')

    def test_touches_all_present_files(self):
        _write(self.d / 'software.json', {'jq': {'why': 'x'}}, fmt=1)
        _write(self.d / 'dropped.json', {}, fmt=1)
        _write(self.d / 'versions.json', {'jq': {'source': 'brew-formula', 'versions': ['1']}},
               fmt=1)

        def bump_only(ctx: MigrateContext) -> None:
            pass

        step = Migration(target_format=2, id='noop', apply=bump_only)
        apply_pending(self.d, steps=(step,), code_format=2)
        for name in ('software.json', 'dropped.json', 'versions.json'):
            self.assertEqual(json.loads((self.d / name).read_text())['format'], 2)
            self.assertTrue((self.d / f'{name}.format1.bak').is_file())

    def test_refuses_newer_format(self):
        _write(self.d / 'software.json', {}, fmt=9)
        with self.assertRaises(ValueError) as ctx:
            apply_pending(self.d, steps=(), code_format=1)
        self.assertIn('newer', str(ctx.exception))

    def test_refuses_below_min_format(self):
        _write(self.d / 'software.json', {}, fmt=1)
        with self.assertRaises(ValueError) as ctx:
            apply_pending(self.d, steps=(STEP_2,), code_format=2, min_format=2)
        self.assertIn('older', str(ctx.exception))

    def test_refuses_format_mismatch(self):
        _write(self.d / 'software.json', {}, fmt=1)
        _write(self.d / 'dropped.json', {}, fmt=2)
        with self.assertRaises(ValueError) as ctx:
            apply_pending(self.d, steps=(STEP_2,), code_format=2)
        self.assertIn('mismatch', str(ctx.exception))


class TestStripSoftwareSource(unittest.TestCase):
    def setUp(self):
        self.d = Path(tempfile.mkdtemp())

    def tearDown(self):
        shutil.rmtree(self.d)

    def test_m002_strips_active_keeps_dropped(self):
        soft = self.d / 'software.json'
        drop = self.d / 'dropped.json'
        _write(soft, {
            'jq': {'why': 'JSON', 'status': 'active', 'source': 'brew-formula',
                   'added': '2026-01-01'},
            'old': {'why': 'gone', 'status': 'active', 'source': 'cargo',
                    'added': '2026-01-01'},
        }, fmt=1)
        _write(drop, {
            'archived': {'why': 'x', 'status': 'dropped', 'source': 'app',
                         'added': '2026-01-01'},
        }, fmt=1)
        from vole.migrations import STEPS
        applied = apply_pending(self.d, steps=STEPS, code_format=2, min_format=1)
        self.assertEqual(applied, ['strip-software-source'])
        soft_apps = json.loads(soft.read_text())['apps']
        self.assertNotIn('source', soft_apps['jq'])
        self.assertNotIn('source', soft_apps['old'])
        self.assertEqual(json.loads(soft.read_text())['format'], 2)
        drop_apps = json.loads(drop.read_text())['apps']
        self.assertEqual(drop_apps['archived']['source'], 'app')
        self.assertEqual(json.loads(drop.read_text())['format'], 2)


class TestMigrateCLI(unittest.TestCase):
    def setUp(self):
        self.d = Path(tempfile.mkdtemp())

    def tearDown(self):
        shutil.rmtree(self.d)

    def test_migrate_strips_and_bumps(self):
        _write(self.d / 'software.json', {'jq': {'why': 'TODO', 'status': 'active',
                                                  'source': 'brew-formula',
                                                  'added': '2026-01-01'}}, fmt=1)
        env = {**os.environ, 'VOLE_DATA_DIR': str(self.d)}
        r = subprocess.run(
            [sys.executable, '-m', 'vole', '--data-dir', str(self.d), 'migrate'],
            cwd=str(ROOT), capture_output=True, text=True, env=env)
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn('now at format 2', r.stdout)
        data = json.loads((self.d / 'software.json').read_text())
        self.assertEqual(data['format'], 2)
        self.assertNotIn('source', data['apps']['jq'])

    def test_migrate_already_current(self):
        inventory.save(self.d / 'software.json',
                       {'jq': {'why': 'TODO', 'status': 'active', 'added': '2026-01-01'}})
        env = {**os.environ, 'VOLE_DATA_DIR': str(self.d)}
        r = subprocess.run(
            [sys.executable, '-m', 'vole', '--data-dir', str(self.d), 'migrate'],
            cwd=str(ROOT), capture_output=True, text=True, env=env)
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn('already at format 2', r.stdout)


if __name__ == '__main__':
    unittest.main()
