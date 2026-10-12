"""Tests for install.sh. Offline: VOLE_REPO points at this checkout, HOME is a temp dir.

The download path (curl from GitHub) is not covered here.
"""
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from vole import __version__  # noqa: E402


class TestInstall(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.home = self.tmp / 'home'
        self.home.mkdir()
        self.lib = self.home / '.local' / 'share' / 'vole'
        self.bin = self.home / '.local' / 'bin'

    def tearDown(self):
        shutil.rmtree(self.tmp)

    def install(self, path=None, **env):
        e = {
            'PATH': path or os.environ['PATH'],
            'HOME': str(self.home),
            'TMPDIR': tempfile.gettempdir(),
            'VOLE_REPO': str(ROOT),
        }
        e.update(env)
        return subprocess.run(['sh', str(ROOT / 'install.sh')],
                              capture_output=True, text=True, env=e)

    def test_installs_package_and_working_launcher(self):
        r = self.install()
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(sorted(os.listdir(self.lib)), ['vole'])
        self.assertTrue((self.lib / 'vole' / 'cli.py').is_file())
        v = subprocess.run([str(self.bin / 'vole'), '--version'],
                           capture_output=True, text=True)
        self.assertEqual(v.returncode, 0, v.stderr)
        self.assertEqual(v.stdout.strip(), f'vole {__version__}')

    def test_rerun_restores_package_and_keeps_other_files(self):
        self.assertEqual(self.install().returncode, 0)
        (self.lib / 'vole' / 'cli.py').unlink()
        (self.lib / 'notes.txt').write_text('mine')
        r = self.install()
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertTrue((self.lib / 'vole' / 'cli.py').is_file())
        self.assertEqual((self.lib / 'notes.txt').read_text(), 'mine')

    def test_path_hint_only_when_bin_dir_missing_from_path(self):
        r = self.install()
        self.assertIn('is not on your PATH', r.stdout)
        r = self.install(path=f'{self.bin}:{os.environ["PATH"]}')
        self.assertNotIn('is not on your PATH', r.stdout)

    def test_refuses_unsafe_lib_dirs(self):
        cases = {
            '/': 'must not be / or empty',
            'relative/dir': 'must be an absolute path',
            str(self.home): 'must not be your home directory',
            str(self.home) + '/': 'must not be your home directory',
            str(self.home / 'x' / '..' / '..'): 'must not contain . or ..',
            str(self.tmp / 'outside'): 'is outside $HOME',
        }
        for lib, message in cases.items():
            with self.subTest(lib=lib):
                r = self.install(VOLE_INSTALL_LIB=lib)
                self.assertEqual(r.returncode, 1, r.stdout)
                self.assertIn(message, r.stderr)
        self.assertFalse((self.tmp / 'outside').exists())
        self.assertFalse(self.bin.exists())

    def test_root_is_refused_even_with_force(self):
        r = self.install(VOLE_INSTALL_LIB='/', VOLE_INSTALL_FORCE='1')
        self.assertEqual(r.returncode, 1)
        self.assertIn('must not be / or empty', r.stderr)

    def test_force_allows_lib_outside_home(self):
        outside = self.tmp / 'outside'
        r = self.install(VOLE_INSTALL_LIB=str(outside), VOLE_INSTALL_FORCE='1')
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertTrue((outside / 'vole' / 'cli.py').is_file())


if __name__ == '__main__':
    unittest.main()
