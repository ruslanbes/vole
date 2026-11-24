"""Undo stack: checkpoint, restore, depth, reset, autoscan skip."""
import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from vole import inventory, paths, undo
from vole.migrations import FORMAT
from tests.test_scan import run_vole


class UndoStackTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.d = Path(self.tmp.name)
        inventory.save(self.d / 'software.json', {
            'jq': {'why': 'old', 'added': '2026-01-01', 'status': 'active'},
        })

    def test_checkpoint_and_restore(self):
        frame = undo.checkpoint(self.d, 'why')
        self.assertIn('at', frame)
        inventory.save(self.d / 'software.json', {
            'jq': {'why': 'new', 'added': '2026-01-01', 'status': 'active'},
        })
        self.assertEqual(inventory.load(self.d / 'software.json')['jq']['why'], 'new')
        lines = undo.restore(self.d)
        text = '\n'.join(lines)
        self.assertIn('restored', text)
        self.assertIn('from ', text)
        self.assertIn('jq: why "new" → "old"', text)
        self.assertEqual(inventory.load(self.d / 'software.json')['jq']['why'], 'old')
        self.assertEqual(undo.depth(self.d), 0)

    def test_empty_stack(self):
        with self.assertRaises(ValueError) as ctx:
            undo.restore(self.d)
        self.assertIn('nothing to undo', str(ctx.exception))

    def test_dry_run_does_not_pop(self):
        undo.checkpoint(self.d, 'why')
        inventory.save(self.d / 'software.json', {
            'jq': {'why': 'new', 'added': '2026-01-01', 'status': 'active'},
        })
        lines = undo.restore(self.d, dry_run=True)
        text = '\n'.join(lines)
        self.assertIn('would restore', text)
        self.assertIn('from ', text)
        self.assertIn('jq: why "new" → "old"', text)
        self.assertEqual(undo.depth(self.d), 1)
        self.assertEqual(inventory.load(self.d / 'software.json')['jq']['why'], 'new')

    def test_depth_cap(self):
        for i in range(undo.DEFAULT_DEPTH + 3):
            undo.checkpoint(self.d, f'step-{i}', depth_limit=undo.DEFAULT_DEPTH)
            inventory.save(self.d / 'software.json', {
                'jq': {'why': str(i), 'added': '2026-01-01', 'status': 'active'},
            })
        self.assertEqual(undo.depth(self.d), undo.DEFAULT_DEPTH)
        # Oldest frames dropped; undoing DEFAULT_DEPTH times reaches early-but-not-first.
        for _ in range(undo.DEFAULT_DEPTH):
            undo.restore(self.d)
        self.assertEqual(undo.depth(self.d), 0)

    def test_format_mismatch_refuses(self):
        undo.checkpoint(self.d, 'why')
        stack = json.loads((self.d / 'undo' / 'stack.json').read_text(encoding='utf-8'))
        stack['frames'][-1]['format'] = FORMAT - 1 if FORMAT > 1 else 0
        (self.d / 'undo' / 'stack.json').write_text(
            json.dumps(stack, indent=2) + '\n', encoding='utf-8')
        with self.assertRaises(ValueError) as ctx:
            undo.restore(self.d)
        self.assertIn('format', str(ctx.exception))

    def test_restore_absent_file(self):
        undo.checkpoint(self.d, 'purge')
        (self.d / 'versions.json').write_text(
            inventory.render({'jq': {'source': 'brew', 'versions': ['1']}}),
            encoding='utf-8')
        # Pretend versions was absent at checkpoint — already is in files_meta.
        undo.restore(self.d)
        self.assertFalse((self.d / 'versions.json').exists())

    def test_discard_noop_checkpoint(self):
        frame = undo.checkpoint(self.d, 'scan')
        self.assertEqual(undo.depth(self.d), 1)
        # No writes — identical to snapshot.
        self.assertTrue(undo.discard_if_unchanged(self.d, frame))
        self.assertEqual(undo.depth(self.d), 0)

    def test_keep_checkpoint_when_changed(self):
        frame = undo.checkpoint(self.d, 'why')
        inventory.save(self.d / 'software.json', {
            'jq': {'why': 'new', 'added': '2026-01-01', 'status': 'active'},
        })
        self.assertFalse(undo.discard_if_unchanged(self.d, frame))
        self.assertEqual(undo.depth(self.d), 1)


class UndoCliTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.d = Path(self.tmp.name)
        inventory.save(self.d / 'software.json', {
            'jq': {'why': 'old', 'added': '2026-01-01', 'status': 'active'},
            'go': {'why': 'lang', 'added': '2026-01-01', 'status': 'active'},
        })
        inventory.save(self.d / 'versions.json', {
            'jq': {'source': 'brew-formula', 'versions': ['1.7']},
            'go': {'source': 'bins', 'versions': []},
        })

    def test_why_then_undo(self):
        r = run_vole('why', 'jq', 'new reason', data_dir=self.d)
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(inventory.load(self.d / 'software.json')['jq']['why'], 'new reason')
        r = run_vole('undo', data_dir=self.d)
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn('restored', r.stdout)
        self.assertEqual(inventory.load(self.d / 'software.json')['jq']['why'], 'old')

    def test_undo_dry_run(self):
        run_vole('why', 'jq', 'new', data_dir=self.d)
        r = run_vole('undo', '--dry-run', data_dir=self.d)
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn('would restore', r.stdout)
        self.assertIn('from ', r.stdout)
        self.assertIn('jq: why "new" → "old"', r.stdout)
        self.assertEqual(inventory.load(self.d / 'software.json')['jq']['why'], 'new')

    def test_undo_empty(self):
        r = run_vole('undo', data_dir=self.d)
        self.assertEqual(r.returncode, 1)
        self.assertIn('nothing to undo', r.stderr)

    def test_purge_undo(self):
        r = run_vole('purge', 'jq', '--force', data_dir=self.d)
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertNotIn('jq', inventory.load(self.d / 'software.json'))
        r = run_vole('undo', data_dir=self.d)
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn('jq', inventory.load(self.d / 'software.json'))

    def test_glob_why_one_checkpoint(self):
        r = run_vole('why', '*', 'batch', data_dir=self.d)
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(undo.depth(self.d), 1)
        run_vole('undo', data_dir=self.d)
        apps = inventory.load(self.d / 'software.json')
        self.assertEqual(apps['go']['why'], 'lang')
        self.assertEqual(apps['jq']['why'], 'old')

    def test_reset_wipes_undo(self):
        run_vole('why', 'jq', 'new', data_dir=self.d)
        self.assertTrue((self.d / 'undo').exists())
        r = run_vole('reset', '--force', data_dir=self.d)
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertFalse((self.d / 'software.json').exists())
        self.assertFalse((self.d / 'undo').exists())
        r = run_vole('undo', data_dir=self.d)
        self.assertEqual(r.returncode, 1)

    def test_autoscan_run_skips_checkpoint(self):
        with mock.patch('vole.scan.run', return_value=0) as scan_run:
            from vole import autoscan
            autoscan.run_scheduled(self.d)
            scan_run.assert_called_once()
            kwargs = scan_run.call_args.kwargs
            self.assertFalse(kwargs.get('checkpoint', True))


if __name__ == '__main__':
    unittest.main()
