"""Autoscan schedule parsing, next-run, state, and CLI (launchctl mocked)."""
import datetime as dt
import json
import tempfile
import unittest
from pathlib import Path

from vole import autoscan, paths
from tests.test_scan import run_vole


class ParseScheduleTests(unittest.TestCase):
    def test_keywords(self):
        w = autoscan.parse_schedule('weekly')
        self.assertEqual(w.phrase, 'weekly')
        self.assertEqual(w.kind, 'calendar')
        self.assertEqual(w.calendar['Weekday'], 0)
        m = autoscan.parse_schedule('Monthly')
        self.assertEqual(m.phrase, 'monthly')
        self.assertEqual(m.calendar['Day'], 1)

    def test_every(self):
        s = autoscan.parse_schedule('every 10 minutes')
        self.assertEqual(s.phrase, 'every 10 minutes')
        self.assertEqual(s.seconds, 600)
        s = autoscan.parse_schedule('every 1 hour')
        self.assertEqual(s.phrase, 'every 1 hour')
        self.assertEqual(s.seconds, 3600)
        s = autoscan.parse_schedule('every hour')
        self.assertEqual(s.phrase, 'every 1 hour')
        self.assertEqual(s.seconds, 3600)
        s = autoscan.parse_schedule('every day')
        self.assertEqual(s.phrase, 'every 1 day')
        self.assertEqual(s.seconds, 86400)
        s = autoscan.parse_schedule('every 3 days')
        self.assertEqual(s.phrase, 'every 3 days')
        self.assertEqual(s.seconds, 3 * 86400)

    def test_refuse(self):
        with self.assertRaises(ValueError):
            autoscan.parse_schedule('tomorrow')
        with self.assertRaises(ValueError):
            autoscan.parse_schedule('every 0 days')
        with self.assertRaises(ValueError):
            autoscan.parse_schedule('')


class NextRunTests(unittest.TestCase):
    def test_interval_from_now(self):
        sched = autoscan.parse_schedule('every 2 hours')
        now = dt.datetime(2026, 11, 10, 12, 0, tzinfo=dt.timezone.utc)
        nxt = autoscan.next_run_after(sched, None, now=now)
        self.assertEqual(nxt, now + dt.timedelta(hours=2))

    def test_interval_from_last(self):
        sched = autoscan.parse_schedule('every 1 day')
        now = dt.datetime(2026, 11, 10, 12, 0, tzinfo=dt.timezone.utc)
        last = now - dt.timedelta(hours=6)
        nxt = autoscan.next_run_after(sched, last, now=now)
        self.assertEqual(nxt, last + dt.timedelta(days=1))

    def test_weekly_calendar(self):
        sched = autoscan.parse_schedule('weekly')
        # Wednesday 2026-11-11 → next Sunday 09:00 local-as-given tz
        now = dt.datetime(2026, 11, 11, 15, 0, tzinfo=dt.timezone.utc)
        nxt = autoscan.next_run_after(sched, None, now=now)
        self.assertEqual(nxt.weekday(), 6)  # Sunday
        self.assertEqual((nxt.hour, nxt.minute), (9, 0))
        self.assertGreater(nxt, now)


class StateAndPlistTests(unittest.TestCase):
    def test_save_load_roundtrip(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            state = autoscan.default_state(root)
            state['enabled'] = True
            state['schedule'] = 'every 3 days'
            state['program'] = ['/usr/bin/vole']
            autoscan.save_state(state, root)
            loaded = autoscan.load_state(root)
            self.assertTrue(loaded['enabled'])
            self.assertEqual(loaded['schedule'], 'every 3 days')
            self.assertEqual(loaded['program'], ['/usr/bin/vole'])
            text = paths.autoscan_path(root).read_text(encoding='utf-8')
            autoscan.save_state(loaded, root)
            self.assertEqual(paths.autoscan_path(root).read_text(encoding='utf-8'), text)

    def test_build_plist_interval(self):
        sched = autoscan.parse_schedule('every 10 minutes')
        pl = autoscan.build_plist(
            ['/opt/homebrew/bin/vole'], Path('/tmp/vole-data'), sched,
            Path('/tmp/autoscan.log'))
        self.assertEqual(pl['Label'], autoscan.LABEL)
        self.assertEqual(pl['StartInterval'], 600)
        self.assertNotIn('StartCalendarInterval', pl)
        self.assertEqual(
            pl['ProgramArguments'],
            ['/opt/homebrew/bin/vole', '--data-dir',
             str(Path('/tmp/vole-data').resolve()),
             'autoscan', 'run'])

    def test_build_plist_weekly(self):
        sched = autoscan.parse_schedule('weekly')
        pl = autoscan.build_plist(['vole'], Path('/data'), sched, Path('/log'))
        self.assertEqual(pl['StartCalendarInterval']['Weekday'], 0)
        self.assertNotIn('StartInterval', pl)


class CliAutoscanTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.d = Path(self.tmp.name)
        self.addCleanup(self.tmp.cleanup)
        home = Path(self.tmp.name) / 'home'
        self.log = home / 'Library' / 'Logs' / 'vole' / 'autoscan.log'
        self.plist = home / 'Library' / 'LaunchAgents' / f'{autoscan.LABEL}.plist'
        self.env = {
            'VOLE_AUTOSCAN_SKIP_LAUNCHCTL': '1',
            'VOLE_AUTOSCAN_LOG': str(self.log),
            'VOLE_AUTOSCAN_PLIST': str(self.plist),
        }

    def _run(self, *args):
        return run_vole(*args, data_dir=self.d, env=self.env)

    def test_status_off_default(self):
        r = self._run('autoscan')
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn('autoscan: off', r.stdout)
        self.assertIn('schedule: weekly', r.stdout)

    def test_schedule_print_and_set(self):
        r = self._run('autoscan', 'schedule')
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(r.stdout.strip(), 'weekly')

        r = self._run('autoscan', 'schedule', 'every', '3', 'days')
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn('autoscan: on (every 3 days)', r.stdout)
        state = json.loads(paths.autoscan_path(self.d).read_text(encoding='utf-8'))
        self.assertTrue(state['enabled'])
        self.assertEqual(state['schedule'], 'every 3 days')
        self.assertEqual(state['data_dir'], str(self.d.resolve()))
        self.assertTrue(self.plist.exists())

    def test_on_off(self):
        r = self._run('autoscan', 'on')
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn('autoscan: on (weekly)', r.stdout)
        r = self._run('autoscan')
        self.assertIn('autoscan: on', r.stdout)
        self.assertIn('next:', r.stdout)
        r = self._run('autoscan', 'off')
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn('autoscan: off', r.stdout)
        state = json.loads(paths.autoscan_path(self.d).read_text(encoding='utf-8'))
        self.assertFalse(state['enabled'])
        self.assertEqual(state['schedule'], 'weekly')

    def test_bad_schedule(self):
        r = self._run('autoscan', 'schedule', 'soon')
        self.assertEqual(r.returncode, 1)
        self.assertIn('unrecognized', r.stderr)


if __name__ == '__main__':
    unittest.main()
