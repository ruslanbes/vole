"""Tests for vole. Stdlib only, Python 3.9+.

    python3 -m unittest discover -s tests
    /usr/bin/python3 -m unittest discover -s tests

Import the package normally. File-only modes run against a temp VOLE_DATA_DIR.
Discovery/signal unit tests use fixtures, not the live machine.
"""
import io
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from vole import scan, inventory, paths, versions as versions_mod  # noqa: E402
from vole.signals import app_state, config_refs, shell_history, spotlight  # noqa: E402
from vole.sources import (  # noqa: E402
    apps, asdf, bins, brew, cargo, mise, npm_global, ollama, pipx, pnpm_global,
    uv_tool, yarn_global,
)
from vole.signals.base import Fact  # noqa: E402
from vole.sources.base import Installed, ScanContext  # noqa: E402

FIXTURES = ROOT / 'tests' / 'fixtures'


def fixture(name):
    return (FIXTURES / name).read_text(encoding='utf-8')


def run_vole(*args, env=None, data_dir=None):
    e = os.environ.copy()
    if env:
        e.update(env)
    if data_dir is not None:
        e['VOLE_DATA_DIR'] = str(data_dir)
    return subprocess.run(
        [sys.executable, '-m', 'vole', *args],
        cwd=str(ROOT), capture_output=True, text=True, env=e)


class TestRenderAndSave(unittest.TestCase):
    def test_rewriting_unchanged_data_is_byte_identical(self):
        for f in ('software.json', 'versions.json'):
            text = fixture(f)
            self.assertEqual(inventory.render(inventory.parse(text)), text, f)

    def test_entries_sort_case_insensitively(self):
        out = inventory.render({'zeta': {}, 'Alpha': {}, 'beta': {}})
        self.assertLess(out.index('Alpha'), out.index('beta'))
        self.assertLess(out.index('beta'), out.index('zeta'))

    def test_awkward_names_are_plain_keys(self):
        names = ('Microsoft Excel', 'zoom.us', 'azure/kubelogin/kubelogin',
                 'iterm2@beta', 'qwen3.8:27b-mlx', 'say "hi"')
        apps = {n: {'why': n} for n in names}
        self.assertEqual(inventory.parse(inventory.render(apps)), apps)

    def test_save_leaves_no_temp_file(self):
        with tempfile.TemporaryDirectory() as d:
            out = Path(d) / 'software.json'
            inventory.save(out, {'a': {'why': 'x'}})
            self.assertEqual(os.listdir(d), ['software.json'])

    def test_files_are_owner_only(self):
        with tempfile.TemporaryDirectory() as d:
            out = Path(d) / 'new' / 'software.json'
            inventory.save(out, {'a': {'why': 'x'}})
            self.assertEqual(out.stat().st_mode & 0o777, 0o600)
            self.assertEqual(out.parent.stat().st_mode & 0o777, 0o700)

    def test_existing_open_file_is_tightened_even_when_unchanged(self):
        with tempfile.TemporaryDirectory() as d:
            out = Path(d) / 'software.json'
            out.write_text(inventory.render({'a': {'why': 'x'}}))
            out.chmod(0o644)
            inventory.save(out, {'a': {'why': 'x'}})
            self.assertEqual(out.stat().st_mode & 0o777, 0o600)

    def test_leftover_temp_file_mode_is_not_inherited(self):
        with tempfile.TemporaryDirectory() as d:
            out = Path(d) / 'software.json'
            stale = Path(d) / 'software.json.tmp'
            stale.write_text('partial')
            stale.chmod(0o644)
            inventory.save(out, {'a': {'why': 'x'}})
            self.assertEqual(out.stat().st_mode & 0o777, 0o600)
            self.assertFalse(stale.exists())

    def test_unchanged_save_does_not_touch_the_file(self):
        with tempfile.TemporaryDirectory() as d:
            out = Path(d) / 'versions.json'
            inventory.save(out, {'jq': {'source': 'brew-formula', 'versions': ['1.7.1']}})
            os.utime(out, (1_000_000_000, 1_000_000_000))
            inventory.save(out, {'jq': {'source': 'brew-formula', 'versions': ['1.7.1']}})
            self.assertEqual(out.stat().st_mtime, 1_000_000_000)
            inventory.save(out, {'jq': {'source': 'brew-formula', 'versions': ['1.8.0']}})
            self.assertNotEqual(out.stat().st_mtime, 1_000_000_000)


class TestParse(unittest.TestCase):
    def test_invalid_json_is_refused(self):
        with self.assertRaises(ValueError):
            inventory.parse('{"format": 1, "apps": {')

    def test_wrong_format_is_refused(self):
        with self.assertRaises(ValueError):
            inventory.parse('{"format": 2, "apps": {}}')


class TestSetField(unittest.TestCase):
    ENTRY = {'source': 'brew-formula', 'why': 'old reason',
             'added': '2026-01-01', 'status': 'active'}

    def test_replace_leaves_other_fields(self):
        out = inventory.set_field(self.ENTRY, 'why', 'new reason')
        self.assertEqual(out['why'], 'new reason')
        self.assertEqual(self.ENTRY['why'], 'old reason')

    def test_empty_value_removes_the_field(self):
        out = inventory.set_field(inventory.set_field(self.ENTRY, 'keep', 'mdm'), 'keep', '')
        self.assertNotIn('keep', out)


class TestCheckApps(unittest.TestCase):
    def test_fixtures_are_clean(self):
        for name, versions_file in (('software.json', False), ('versions.json', True)):
            apps = inventory.parse(fixture(name))
            self.assertEqual(
                inventory.check_apps(apps, name, versions_file=versions_file), [])

    def test_unknown_field(self):
        apps = {'jq': {'source': 'brew-formula', 'why': 'x', 'projects': []}}
        probs = inventory.check_apps(apps, 'software.json')
        self.assertTrue(any('unknown field' in p and 'projects' in p for p in probs))

    def test_unknown_status(self):
        apps = {'jq': {'status': 'archived'}}
        probs = inventory.check_apps(apps, 'software.json')
        self.assertTrue(any('unknown status' in p for p in probs))

    def test_keep_any_string_is_ok(self):
        apps = {'jq': {'keep': 'apple', 'status': 'active'}}
        self.assertEqual(inventory.check_apps(apps, 'software.json'), [])

    def test_versions_wrong_type(self):
        apps = {'jq': {'source': 'brew-formula', 'versions': '1.7.1'}}
        probs = inventory.check_apps(apps, 'versions.json', versions_file=True)
        self.assertTrue(any('versions must be a list' in p for p in probs))

    def test_versions_element_wrong_type(self):
        apps = {'jq': {'versions': [1.7]}}
        probs = inventory.check_apps(apps, 'versions.json', versions_file=True)
        self.assertTrue(any('versions[0] must be a string' in p for p in probs))



class TestVersionDiff(unittest.TestCase):
    def test_added_changed_removed(self):
        prev = {'a': ['1'], 'b': ['2'], 'c': ['3']}
        cur = {'a': ['1'], 'b': ['2.1'], 'd': ['4']}
        changed, added, removed = versions_mod.diff(prev, cur)
        self.assertEqual(changed, [('b', '2', '2.1')])
        self.assertEqual(added, [('d', '4')])
        self.assertEqual(removed, [('c', '3')])

    def test_unchanged_is_empty(self):
        self.assertEqual(versions_mod.diff({'a': ['1']}, {'a': ['1']}), ([], [], []))


class TestBrewCaskroom(unittest.TestCase):
    def tearDown(self):
        brew._resolve_caskroom.cache_clear()

    def test_override_wins(self):
        self.assertEqual(brew.caskroom('/tmp/Custom/Caskroom'),
                         Path('/tmp/Custom/Caskroom'))

    def test_homebrew_prefix_env(self):
        with tempfile.TemporaryDirectory() as d:
            prefix = Path(d) / 'prefix'
            prefix.mkdir()
            brew._resolve_caskroom.cache_clear()
            with mock.patch.dict(os.environ, {'HOMEBREW_PREFIX': str(prefix)}):
                self.assertEqual(brew.caskroom(), prefix / 'Caskroom')

    def test_cask_apps_maps_app_and_symlink_target_to_cask(self):
        with tempfile.TemporaryDirectory() as d:
            real = Path(d) / 'Real Name.app'
            real.mkdir()
            version = Path(d) / 'Caskroom' / 'some-cask' / '1.0'
            version.mkdir(parents=True)
            (version / 'Short.app').symlink_to(real)
            self.assertEqual(brew.cask_apps(Path(d) / 'Caskroom'),
                             {'Short': 'some-cask', 'Real Name': 'some-cask'})

    def test_cask_owned_apps_reads_override_tree(self):
        with tempfile.TemporaryDirectory() as d:
            room = Path(d) / 'Caskroom'
            app = room / 'iterm2' / '3.5.0' / 'iTerm.app'
            app.mkdir(parents=True)
            names = brew.cask_owned_apps(room)
            self.assertIn('iTerm', names)


class TestBrewFormulae(unittest.TestCase):
    def test_version_map_splits_name_and_versions(self):
        self.assertEqual(brew._version_map('ripgrep 14.1.0\njq 1.7.1 1.6\norphan\n'),
                         {'ripgrep': ['14.1.0'], 'jq': ['1.7.1', '1.6']})
        self.assertEqual(brew._version_map(''), {})

    def test_union_keeps_requested_dependencies_and_orphans(self):
        leaves = 'ripgrep\nold-orphan-lib\nuser/tap/tool\n'
        on_request = 'jq\nripgrep\ntool\n'
        self.assertEqual(brew.formula_names(leaves, on_request),
                         ['jq', 'old-orphan-lib', 'ripgrep', 'user/tap/tool'])

    def test_falls_back_to_leaves_when_flag_unsupported(self):
        old_brew = subprocess.CompletedProcess([], 1, stdout='', stderr='Error: invalid option')
        outputs = {
            ('brew', 'list', '--versions'): 'ripgrep 14.1.0\n',
            ('brew', 'list', '--cask', '--versions'): '',
            ('brew', 'leaves'): 'ripgrep\n',
            ('brew', 'list', '--cask'): '',
        }
        with mock.patch.object(brew.shutil, 'which', return_value='/usr/local/bin/brew'), \
                mock.patch.object(brew, '_run', side_effect=lambda a: outputs[tuple(a)]), \
                mock.patch.object(brew.subprocess, 'run', return_value=old_brew), \
                mock.patch.object(brew, 'cask_owned_apps', return_value=set()):
            found = list(brew.discover(ScanContext(Path('/nonexistent'))))
        self.assertEqual(found, [Installed('brew-formula', 'ripgrep', ['14.1.0'])])


class TestAppBundles(unittest.TestCase):
    def test_top_level_and_one_folder_down(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d) / 'Applications'
            for rel in ('Safari.app', 'Utilities/Console Helper.app',
                        'Adobe Photoshop 2026/Adobe Photoshop 2026.app',
                        'Vendor/Suite/Too Deep.app',
                        'Host.app/Embedded.app',
                        'Brave Browser Apps.localized/Revoke.cash.app'):
                (root / rel).mkdir(parents=True)
            names = [p.name for p in apps.app_bundles(Path(d), roots=[root])]
            self.assertEqual(names, ['Host.app', 'Safari.app',
                                     'Adobe Photoshop 2026.app', 'Console Helper.app'])


class TestAppsSource(unittest.TestCase):
    def test_skips_apps_brew_published_as_cask_owned(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d) / 'Applications'
            for name in ('iTerm.app', 'Notes Helper.app'):
                (root / name).mkdir(parents=True)
            ctx = ScanContext(Path(d))
            with mock.patch.object(brew, 'cask_owned_apps', return_value={'iTerm'}), \
                    mock.patch.object(brew.shutil, 'which', return_value=None):
                self.assertEqual(list(brew.discover(ctx)), [])
            with mock.patch.object(apps, 'app_bundles', side_effect=lambda h: sorted(root.glob('*.app'))), \
                    mock.patch.object(apps, '_app_version', return_value=''):
                found = list(apps.discover(ctx))
            self.assertEqual(found, [Installed('app', 'Notes Helper', [])])


class TestBinsSource(unittest.TestCase):
    def test_skips_dangling_symlinks_and_lists_real_files(self):
        with tempfile.TemporaryDirectory() as d:
            home = Path(d)
            bindir = home / '.local' / 'bin'
            bindir.mkdir(parents=True)
            real = bindir / 'good'
            real.write_text('#!/bin/sh\n')
            real.chmod(0o755)
            (bindir / 'dead').symlink_to(home / 'nowhere')
            found = list(bins.discover(ScanContext(home)))
            self.assertEqual(found, [Installed('local-bin', 'good', [])])


class TestCargoSource(unittest.TestCase):
    SAMPLE = (
        'ripgrep v14.1.0:\n'
        '    rg\n'
        'fd-find v10.1.0:\n'
        '    fd\n'
        'cargo-edit v0.12.0:\n'
        '    cargo-add\n'
        '    cargo-rm\n'
    )

    def test_parse_install_list_uses_package_names(self):
        found = cargo.parse_install_list(self.SAMPLE)
        self.assertEqual(found, [
            Installed('cargo', 'ripgrep', ['14.1.0']),
            Installed('cargo', 'fd-find', ['10.1.0']),
            Installed('cargo', 'cargo-edit', ['0.12.0']),
        ])

    def test_parse_empty(self):
        self.assertEqual(cargo.parse_install_list(''), [])

    def test_bin_dir_fallback_when_no_cargo(self):
        with tempfile.TemporaryDirectory() as d:
            home = Path(d)
            bindir = home / '.cargo' / 'bin'
            bindir.mkdir(parents=True)
            (bindir / 'rg').write_text('x')
            (bindir / 'rg').chmod(0o755)
            (bindir / 'dead').symlink_to(home / 'nowhere')
            with mock.patch('vole.sources.cargo.shutil.which', return_value=None):
                found = list(cargo.discover(ScanContext(home)))
            self.assertEqual(found, [Installed('cargo', 'rg', [])])

    def test_no_cargo_and_no_bin_dir(self):
        with tempfile.TemporaryDirectory() as d:
            with mock.patch('vole.sources.cargo.shutil.which', return_value=None):
                self.assertEqual(list(cargo.discover(ScanContext(Path(d)))), [])


class TestPipxSource(unittest.TestCase):
    SAMPLE = {
        'pipx_spec_version': '0.1',
        'venvs': {
            'httpie': {
                'metadata': {
                    'main_package': {
                        'package': 'httpie',
                        'package_version': '3.2.2',
                        'apps': ['http', 'https', 'httpie'],
                        'apps_of_dependencies': {},
                    }
                }
            },
            'ruff': {
                'metadata': {
                    'main_package': {
                        'package': 'ruff',
                        'package_version': '0.6.0',
                        'apps': ['ruff'],
                        'apps_of_dependencies': {'something': ['dep-bin']},
                    }
                }
            },
        },
    }

    def test_parse_package_names_and_shims(self):
        items, shims = pipx.parse_list_json(self.SAMPLE)
        self.assertEqual(items, [
            Installed('pipx', 'httpie', ['3.2.2']),
            Installed('pipx', 'ruff', ['0.6.0']),
        ])
        self.assertEqual(shims, {'http', 'https', 'httpie', 'ruff', 'dep-bin'})

    def test_missing_pipx_is_empty(self):
        with tempfile.TemporaryDirectory() as d:
            with mock.patch('vole.sources.pipx.shutil.which', return_value=None):
                self.assertEqual(pipx.collect(Path(d)), ([], set()))

    def test_local_bin_skips_shims_pipx_published(self):
        with tempfile.TemporaryDirectory() as d:
            home = Path(d)
            bindir = home / '.local' / 'bin'
            bindir.mkdir(parents=True)
            for name in ('http', 'my-script'):
                p = bindir / name
                p.write_text('#!/bin/sh\n')
                p.chmod(0o755)
            ctx = ScanContext(home)
            items, shims = pipx.parse_list_json(self.SAMPLE)
            with mock.patch.object(pipx, 'collect', return_value=(items, shims)):
                self.assertEqual(list(pipx.discover(ctx)), items)
            self.assertIn('http', ctx.claimed_bins)
            found = list(bins.discover(ctx))
            self.assertEqual(found, [Installed('local-bin', 'my-script', [])])


class TestUvToolSource(unittest.TestCase):
    TEXT = (
        'ruff v0.6.0 (/Users/me/.local/share/uv/tools/ruff)\n'
        '- /Users/me/.local/bin/ruff\n'
        'black v24.2.0 (/Users/me/.local/share/uv/tools/black)\n'
        '- /Users/me/.local/bin/black\n'
        '- /Users/me/.local/bin/blackd\n'
    )

    def test_parse_show_paths_text(self):
        items, shims = uv_tool.parse_list_text(self.TEXT)
        self.assertEqual(items, [
            Installed('uv-tool', 'ruff', ['0.6.0']),
            Installed('uv-tool', 'black', ['24.2.0']),
        ])
        self.assertEqual(shims, {'ruff', 'black', 'blackd'})

    def test_parse_json(self):
        items, shims = uv_tool.parse_list_json([
            {
                'name': 'httpie',
                'version': '3.2.2',
                'entrypoints': [
                    {'name': 'http', 'path': '/x/bin/http'},
                    {'name': 'https', 'path': '/x/bin/https'},
                ],
            }
        ])
        self.assertEqual(items, [Installed('uv-tool', 'httpie', ['3.2.2'])])
        self.assertEqual(shims, {'httpie', 'http', 'https'})

    def test_missing_uv_is_empty(self):
        with tempfile.TemporaryDirectory() as d:
            with mock.patch('vole.sources.uv_tool.shutil.which', return_value=None):
                self.assertEqual(uv_tool.collect(Path(d)), ([], set()))


class TestYarnSource(unittest.TestCase):
    SAMPLE = (
        '{"type":"activityStart","data":{"id":0}}\n'
        '{"type":"info","data":"\\"prettier@3.0.0\\" has binaries:"}\n'
        '{"type":"list","data":{"type":"bins-prettier","items":["prettier"]}}\n'
        '{"type":"info","data":"\\"@scope/cli@1.2.3\\" has binaries:"}\n'
        '{"type":"list","data":{"type":"bins-cli","items":["cli"]}}\n'
    )

    def test_parse_ndjson_info_lines(self):
        found = yarn_global.parse_list_ndjson(self.SAMPLE)
        self.assertEqual(found, [
            Installed('yarn-global', '@scope/cli', ['1.2.3']),
            Installed('yarn-global', 'prettier', ['3.0.0']),
        ])

    def test_split_spec(self):
        self.assertEqual(yarn_global.split_spec('prettier@3.0.0'), ('prettier', '3.0.0'))
        self.assertEqual(yarn_global.split_spec('@scope/cli@1.2.3'), ('@scope/cli', '1.2.3'))

    def test_berry_or_empty_is_empty(self):
        self.assertEqual(yarn_global.parse_list_ndjson(''), [])
        self.assertEqual(
            yarn_global.parse_list_ndjson('{"type":"error","data":"Usage Error"}\n'), [])

    def test_missing_yarn_is_empty(self):
        with tempfile.TemporaryDirectory() as d:
            with mock.patch('vole.sources.yarn_global.shutil.which', return_value=None):
                self.assertEqual(list(yarn_global.discover(ScanContext(Path(d)))), [])


class TestPnpmSource(unittest.TestCase):

    SAMPLE = [
        {
            'name': 'global',
            'dependencies': {
                'typescript': {'version': '5.4.0'},
                '@scope/cli': {'version': '1.2.3'},
            },
        }
    ]

    def test_parse_array_of_projects(self):
        found = pnpm_global.parse_list_json(self.SAMPLE)
        self.assertEqual(found, [
            Installed('pnpm-global', '@scope/cli', ['1.2.3']),
            Installed('pnpm-global', 'typescript', ['5.4.0']),
        ])

    def test_parse_single_object(self):
        found = pnpm_global.parse_list_json({
            'dependencies': {'eslint': {'version': '9.0.0'}}
        })
        self.assertEqual(found, [Installed('pnpm-global', 'eslint', ['9.0.0'])])

    def test_parse_empty(self):
        self.assertEqual(pnpm_global.parse_list_json([]), [])
        self.assertEqual(pnpm_global.parse_list_json({}), [])

    def test_missing_pnpm_is_empty(self):
        with tempfile.TemporaryDirectory() as d:
            with mock.patch('vole.sources.pnpm_global.shutil.which', return_value=None):
                self.assertEqual(list(pnpm_global.discover(ScanContext(Path(d)))), [])


class TestAsdfSource(unittest.TestCase):

    SAMPLE = (
        'nodejs\n'
        '  20.11.0\n'
        '  *22.2.0\n'
        'python\n'
        '  3.12.2\n'
        'ruby\n'
        '  No versions installed\n'
    )

    def test_parse_list_groups_versions_per_plugin(self):
        found = asdf.parse_list(self.SAMPLE)
        self.assertEqual(found, [
            Installed('asdf', 'nodejs', ['20.11.0', '22.2.0']),
            Installed('asdf', 'python', ['3.12.2']),
        ])

    def test_parse_empty(self):
        self.assertEqual(asdf.parse_list(''), [])

    def test_missing_asdf_is_empty(self):
        with tempfile.TemporaryDirectory() as d:
            with mock.patch('vole.sources.asdf.shutil.which', return_value=None):
                self.assertEqual(list(asdf.discover(ScanContext(Path(d)))), [])


class TestMiseSource(unittest.TestCase):
    SAMPLE = (
        'node 20.11.0\n'
        'node 22.2.0 ~/src/app/.mise.toml\n'
        'python 3.12.2\n'
        'dangling\n'
    )

    def test_parse_ls_groups_versions_per_tool(self):
        self.assertEqual(mise.parse_ls(self.SAMPLE), [
            Installed('mise', 'node', ['20.11.0', '22.2.0']),
            Installed('mise', 'python', ['3.12.2']),
        ])

    def test_parse_empty(self):
        self.assertEqual(mise.parse_ls(''), [])

    def test_missing_mise_is_empty(self):
        with tempfile.TemporaryDirectory() as d:
            with mock.patch('vole.sources.mise.shutil.which', return_value=None):
                self.assertEqual(list(mise.discover(ScanContext(Path(d)))), [])


class TestNpmSource(unittest.TestCase):
    SAMPLE = {
        'dependencies': {
            '@scope/cli': {'version': '1.2.3'},
            'typescript': {'version': '5.4.0'},
            'no-ver': {},
        }
    }

    def test_parse_ls_json_keeps_scopes(self):
        self.assertEqual(npm_global.parse_ls_json(self.SAMPLE), [
            Installed('npm-global', '@scope/cli', ['1.2.3']),
            Installed('npm-global', 'typescript', ['5.4.0']),
            Installed('npm-global', 'no-ver', []),
        ])

    def test_parse_empty(self):
        self.assertEqual(npm_global.parse_ls_json({}), [])
        self.assertEqual(npm_global.parse_ls_json({'dependencies': None}), [])

    def test_missing_npm_is_empty(self):
        with tempfile.TemporaryDirectory() as d:
            with mock.patch('vole.sources.npm_global.shutil.which', return_value=None):
                self.assertEqual(list(npm_global.discover(ScanContext(Path(d)))), [])


class TestOllamaSource(unittest.TestCase):
    def test_reads_manifest_tree_not_the_cli(self):
        with tempfile.TemporaryDirectory() as d:
            home = Path(d)
            manifest = (home / '.ollama' / 'models' / 'manifests' /
                        'registry.ollama.ai' / 'library' / 'qwen' / '30b')
            manifest.parent.mkdir(parents=True)
            manifest.write_text(json.dumps({
                'config': {'digest': 'sha256:abcdef1234567890'}
            }))
            found = list(ollama.discover(ScanContext(home)))
            self.assertEqual(found, [Installed('ollama', 'qwen:30b', ['abcdef123456'])])


class TestShellHistorySignal(unittest.TestCase):
    def test_reads_extended_history_and_ollama_models(self):
        with tempfile.TemporaryDirectory() as d:
            home = Path(d)
            (home / '.zsh_history').write_bytes(
                b': 1768435200:0;jq .\n'
                b': 1768521600:0;ollama run --verbose qwen:30b\n'
            )
            out = shell_history.collect(ScanContext(home))
            self.assertEqual(out['jq'][0].date, '2026-01-15')
            self.assertEqual(out['qwen:30b'][0].date, '2026-01-16')

    def test_reads_fish_history_and_keeps_newest_across_shells(self):
        with tempfile.TemporaryDirectory() as d:
            home = Path(d)
            (home / '.zsh_history').write_bytes(b': 1768435200:0;jq .\n')
            fish = home / '.local' / 'share' / 'fish'
            fish.mkdir(parents=True)
            (fish / 'fish_history').write_text(
                '- cmd: jq .name package.json\n'
                '  when: 1768608000\n'
                '  paths:\n'
                '    - package.json\n'
                '- cmd: sudo rg TODO\n'
                '  when: 1768521600\n'
                '- cmd: no-when-line\n'
            )
            out = shell_history.collect(ScanContext(home))
            self.assertEqual(out['jq'][0].date, '2026-01-17')
            self.assertEqual(out['rg'][0].date, '2026-01-16')
            self.assertNotIn('no-when-line', out)

    def test_skips_lines_with_out_of_range_timestamps(self):
        with tempfile.TemporaryDirectory() as d:
            home = Path(d)
            (home / '.zsh_history').write_bytes(
                b': 99999999999999999999:0;broken\n'
                b': 1768435200:0;jq .\n'
            )
            out = shell_history.collect(ScanContext(home))
            self.assertNotIn('broken', out)
            self.assertEqual(out['jq'][0].date, '2026-01-15')


class TestSpotlightSignal(unittest.TestCase):
    APPS = [Path('/Applications/A.app'), Path('/Applications/B.app'), Path('/Applications/C.app')]

    @staticmethod
    def proc(stdout, rc=0):
        return subprocess.CompletedProcess([], rc, stdout=stdout, stderr='')

    def test_one_mdls_call_for_many_apps(self):
        out = '2026-09-13 20:24:28 +0000\x00(null)\x002026-10-12 10:57:59 +0000'
        with mock.patch.object(spotlight.subprocess, 'run', return_value=self.proc(out)) as run:
            days = spotlight.last_used(self.APPS)
        self.assertEqual(days, ['2026-09-13', '', '2026-10-12'])
        self.assertEqual(run.call_count, 1)

    def test_falls_back_per_app_when_batch_output_is_garbled(self):
        def fake(args, **_kw):
            paths = args[4:]
            if len(paths) > 1:
                return self.proc('2026-09-13 20:24:28 +0000/Applications/A.app: could not find', 1)
            if paths[0].endswith('B.app'):
                return self.proc('/Applications/B.app: could not find /Applications/B.app.\n', 1)
            return self.proc('2026-09-13 20:24:28 +0000')
        with mock.patch.object(spotlight.subprocess, 'run', side_effect=fake):
            self.assertEqual(spotlight.last_used(self.APPS), ['2026-09-13', '', '2026-09-13'])

    def test_date_is_also_filed_under_owning_cask(self):
        apps_ = [Path('/Applications/iTerm.app')]
        with mock.patch.object(spotlight, 'app_bundles', return_value=apps_), \
                mock.patch.object(spotlight, 'cask_apps', return_value={'iTerm': 'iterm2'}), \
                mock.patch.object(spotlight.subprocess, 'run',
                                  return_value=self.proc('2026-10-01 08:00:00 +0000')):
            out = spotlight.collect(ScanContext(Path('/nonexistent')))
        self.assertEqual(out['iTerm'][0].date, '2026-10-01')
        self.assertEqual(out['iterm2'][0].date, '2026-10-01')


class TestAppStateSignal(unittest.TestCase):
    def test_collect_exact_and_substring(self):
        with tempfile.TemporaryDirectory() as d:
            home = Path(d)
            pref = home / 'Library' / 'Preferences'
            pref.mkdir(parents=True)
            (pref / 'com.googlecode.iterm2.plist').write_text('')
            os.utime(pref / 'com.googlecode.iterm2.plist', (1_768_435_200, 1_768_435_200))
            support = home / 'Library' / 'Application Support' / 'Ripgrep'
            support.mkdir(parents=True)
            os.utime(support, (1_768_435_200, 1_768_435_200))

            # "iterm2" is only a substring of the bundle-id key; "Ripgrep" matches exact.
            out = app_state.collect(ScanContext(home, entries=['iterm2', 'Ripgrep', 'zzz']))
            self.assertEqual(out['iterm2'][0].date, '2026-01-15')
            self.assertEqual(out['Ripgrep'][0].date, '2026-01-15')
            self.assertNotIn('zzz', out)

    def test_lookup_index_matches_full_scan(self):
        state = {
            'comgooglecodeiterm2': [Fact('app state 2026-01-15', '2026-01-15')],
            'iterm': [Fact('app state 2025-01-01', '2025-01-01')],
            'unrelated': [Fact('app state 2026-06-01', '2026-06-01')],
        }
        index = app_state._gram_index(state)
        for name in ('iTerm', 'iterm2', 'nope', 'ab'):
            self.assertEqual(
                app_state.lookup(state, name, index),
                app_state.lookup(state, name),
                name)


class TestConfigRefsSignal(unittest.TestCase):
    def test_reads_listed_files_only(self):
        with tempfile.TemporaryDirectory() as d:
            home = Path(d)
            (home / '.zshrc').write_text('eval "$(zoxide init zsh)"\n')
            (home / '.config' / 'git').mkdir(parents=True)
            (home / '.config' / 'git' / 'config').write_text('[core]\n  pager = delta\n')
            (home / '.config' / 'vole').mkdir()
            (home / '.config' / 'vole' / 'software.json').write_text('{"ripgrep": {}}')
            (home / '.config' / 'stray.txt').write_text('ripgrep')
            out = config_refs.collect(ScanContext(
                home, entries=['zoxide', 'git-delta/delta', 'ripgrep']))
            self.assertEqual(out['zoxide'][0].label, 'referenced in .zshrc')
            self.assertEqual(out['git-delta/delta'][0].label,
                             'referenced in .config/git/config')
            self.assertNotIn('ripgrep', out)

    def test_skips_oversized_files(self):
        with tempfile.TemporaryDirectory() as d:
            home = Path(d)
            (home / '.zshrc').write_text('zoxide ' + 'x' * config_refs.MAX_BYTES)
            self.assertEqual(config_refs.collect(ScanContext(home, entries=['zoxide'])), {})


class TestCLI(unittest.TestCase):
    def setUp(self):
        self.d = Path(tempfile.mkdtemp())
        shutil.copy(FIXTURES / 'software.json', self.d / 'software.json')
        shutil.copy(FIXTURES / 'versions.json', self.d / 'versions.json')

    def tearDown(self):
        shutil.rmtree(self.d)

    def parsed(self, name='software.json'):
        return inventory.load(self.d / name)

    def vole(self, *args):
        return run_vole(*args, data_dir=self.d)

    def test_edit_sets_fields(self):
        r = self.vole('edit', 'jq', '--why', 'JSON on the command line', '--keep', 'in-use')
        self.assertEqual(r.returncode, 0, r.stderr)
        e = self.parsed()['jq']
        self.assertEqual(e['why'], 'JSON on the command line')
        self.assertEqual(e['keep'], 'in-use')

    def test_edit_rejects_unknown_status(self):
        before = (self.d / 'software.json').read_bytes()
        for bad in ('foo', ''):
            r = self.vole('edit', 'jq', '--status', bad)
            self.assertEqual(r.returncode, 2)
            self.assertIn('invalid choice', r.stderr)
        self.assertEqual((self.d / 'software.json').read_bytes(), before)

    def test_write_error_is_reported_without_traceback(self):
        self.d.chmod(0o500)
        try:
            r = self.vole('edit', 'jq', '--why', 'x')
        finally:
            self.d.chmod(0o700)
        self.assertEqual(r.returncode, 1)
        self.assertIn('error:', r.stderr)
        self.assertNotIn('Traceback', r.stderr)
        self.assertEqual(sorted(p.name for p in self.d.iterdir()),
                         ['software.json', 'versions.json'])

    def test_restore_keeps_entry_when_software_write_fails(self):
        self.assertEqual(self.vole('edit', 'alfred', '--status', 'dropped').returncode, 0)
        real_save = inventory.save

        def failing_save(path, apps):
            if Path(path).name == 'software.json':
                raise PermissionError(13, 'Permission denied', str(path))
            return real_save(path, apps)

        from vole import cli
        with mock.patch.object(inventory, 'save', side_effect=failing_save), \
                mock.patch('sys.stdout', io.StringIO()), \
                mock.patch('sys.stderr', io.StringIO()) as err:
            rc = cli.main(['--data-dir', str(self.d), 'restore', 'alfred'])
        self.assertEqual(rc, 1)
        self.assertIn('Permission denied', err.getvalue())
        self.assertIn('alfred', self.parsed('dropped.json'))

    def test_edit_rejects_unknown_name(self):
        r = self.vole('edit', 'kubelogin', '--why', 'x')
        self.assertEqual(r.returncode, 1)
        self.assertIn('azure/kubelogin/kubelogin', r.stderr)

    def test_list_shows_installed(self):
        r = self.vole('list')
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn('5.8,2348', r.stdout)
        self.assertIn('(not in software.json)', r.stdout)

    def test_list_filter(self):
        r = self.vole('list', 'alfred')
        self.assertIn('alfred', r.stdout)
        self.assertNotIn('jq ', r.stdout)

    def test_list_shows_unversioned_installs(self):
        rows = inventory.load(self.d / 'versions.json')
        rows['my-script'] = {'source': 'local-bin', 'versions': []}
        inventory.save(self.d / 'versions.json', rows)
        r = self.vole('list', 'my-script')
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn('my-script', r.stdout)
        self.assertIn('local-bin', r.stdout)

    def test_edit_status_dropped_archives(self):
        r = self.vole('edit', 'alfred', '--status', 'dropped')
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertNotIn('alfred', self.parsed())
        self.assertIn('alfred', self.parsed('dropped.json'))
        self.assertEqual(self.parsed('dropped.json')['alfred']['status'], 'dropped')
        self.assertEqual(self.parsed('dropped.json')['alfred']['archived_by'], 'user')
        self.assertIn('archived', r.stdout)

    def test_drop_aliases_edit_status_dropped(self):
        r = self.vole('drop', 'alfred')
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertNotIn('alfred', self.parsed())
        self.assertIn('alfred', self.parsed('dropped.json'))
        dropped = self.parsed('dropped.json')['alfred']
        self.assertEqual(dropped['status'], 'dropped')
        self.assertEqual(dropped['archived_by'], 'user')
        self.assertIn('archived', r.stdout)

    def test_edit_dropped_entry_in_place(self):
        self.vole('edit', 'alfred', '--status', 'dropped')
        r = self.vole('edit', 'alfred', '--why', 'no longer needed')
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertNotIn('alfred', self.parsed())
        self.assertEqual(self.parsed('dropped.json')['alfred']['why'], 'no longer needed')

    def test_edit_status_active_restores(self):
        self.vole('edit', 'alfred', '--status', 'dropped')
        r = self.vole('edit', 'alfred', '--status', 'active', '--why', 'back')
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn('alfred', self.parsed())
        self.assertNotIn('alfred', self.parsed('dropped.json'))
        self.assertEqual(self.parsed()['alfred']['why'], 'back')
        self.assertEqual(self.parsed()['alfred']['status'], 'active')

    def test_restore(self):
        self.vole('edit', 'alfred', '--status', 'dropped')
        r = self.vole('restore', 'alfred')
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn('alfred', self.parsed())
        self.assertNotIn('alfred', self.parsed('dropped.json'))

    def test_restore_missing_fails(self):
        r = self.vole('restore', 'jq')
        self.assertEqual(r.returncode, 1)
        self.assertIn('dropped.json', r.stderr)

    def test_add_creates(self):
        r = self.vole('add', 'manual-tool', '--source', 'local-bin', '--why', 'hand install')
        self.assertEqual(r.returncode, 0, r.stderr)
        e = self.parsed()['manual-tool']
        self.assertEqual(e['source'], 'local-bin')
        self.assertEqual(e['why'], 'hand install')
        self.assertEqual(e['status'], 'active')

    def test_add_refuses_existing_software(self):
        r = self.vole('add', 'jq', '--source', 'brew-formula')
        self.assertEqual(r.returncode, 1)
        self.assertIn('already', r.stderr)

    def test_add_undrops_from_dropped(self):
        self.vole('edit', 'alfred', '--status', 'dropped')
        r = self.vole('add', 'alfred', '--why', 'need it again')
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn('alfred', self.parsed())
        self.assertNotIn('alfred', self.parsed('dropped.json'))
        self.assertEqual(self.parsed()['alfred']['why'], 'need it again')

    def test_add_requires_source_when_new(self):
        r = self.vole('add', 'brand-new')
        self.assertEqual(r.returncode, 2)
        self.assertIn('--source', r.stderr)

    def test_delete_force(self):
        r = self.vole('delete', 'jq', '--force')
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertNotIn('jq', self.parsed())
        self.assertNotIn('jq', self.parsed('versions.json'))

    def test_delete_from_dropped(self):
        self.vole('edit', 'alfred', '--status', 'dropped')
        r = self.vole('delete', 'alfred', '--force')
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertNotIn('alfred', self.parsed())
        self.assertNotIn('alfred', self.parsed('dropped.json'))

    def test_help_and_bare_invocation(self):
        for args in ((), ('help',)):
            r = self.vole(*args)
            self.assertEqual(r.returncode, 0, r.stderr)
            self.assertIn('usage:', r.stdout)
            self.assertIn('scan', r.stdout)

    def test_version(self):
        from vole import __version__
        r = self.vole('--version')
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(r.stdout.strip(), f'vole {__version__}')

    def test_dry_run_without_inventory_does_not_create(self):
        staging = Path(tempfile.mkdtemp())
        try:
            shutil.copytree(ROOT / 'vole', staging / 'vole')
            data = staging / 'data'
            r = subprocess.run(
                [sys.executable, '-m', 'vole', '--data-dir', str(data),
                 'scan', '--dry-run'],
                cwd=str(staging), capture_output=True, text=True,
                env={**os.environ, 'VOLE_DATA_DIR': str(data)})
            self.assertEqual(r.returncode, 1, r.stderr)
            self.assertFalse(data.exists() or (data / 'software.json').exists())
            self.assertIn('no inventory', r.stderr)
        finally:
            shutil.rmtree(staging)

    def test_reset_force_deletes_inventory_files(self):
        (self.d / 'dropped.json').write_text(
            inventory.render({'x': {'why': 'gone', 'status': 'dropped'}}), encoding='utf-8')
        r = self.vole('reset', '--force')
        self.assertEqual(r.returncode, 0, r.stderr)
        for name in ('software.json', 'dropped.json', 'versions.json'):
            self.assertFalse((self.d / name).exists(), name)
        self.assertIn('deleted', r.stdout)

    def test_reset_cancel_leaves_files(self):
        r = subprocess.run(
            [sys.executable, '-m', 'vole', '--data-dir', str(self.d), 'reset'],
            cwd=str(ROOT), capture_output=True, text=True, input='no\n',
            env={**os.environ, 'VOLE_DATA_DIR': str(self.d)})
        self.assertEqual(r.returncode, 1)
        self.assertIn('cancelled', r.stderr)
        self.assertTrue((self.d / 'software.json').exists())

    def test_reset_yes_confirms(self):
        r = subprocess.run(
            [sys.executable, '-m', 'vole', '--data-dir', str(self.d), 'reset'],
            cwd=str(ROOT), capture_output=True, text=True, input='yes\n',
            env={**os.environ, 'VOLE_DATA_DIR': str(self.d)})
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertFalse((self.d / 'software.json').exists())

    def test_reset_nothing_to_do(self):
        empty = Path(tempfile.mkdtemp())
        try:
            r = run_vole('reset', '--force', data_dir=empty)
            self.assertEqual(r.returncode, 0, r.stderr)
            self.assertIn('nothing to reset', r.stdout)
        finally:
            shutil.rmtree(empty)


def entry(why='because', status='active', source='app', **kw):
    return dict(source=source, why=why, added='2026-01-01', status=status, **kw)


class TestClassify(unittest.TestCase):
    CUTOFF = '2026-04-01'

    def classify(self, entries, installed, facts=None, archived=None, prev_versions=None):
        return scan.classify(entries, archived or {}, installed, facts or {},
                              self.CUTOFF, prev_versions or {})

    def test_new_and_gone(self):
        r = self.classify({'tracked': entry(), 'removed': entry()},
                          {'tracked': ('app', []), 'fresh': ('cargo', [])},
                          facts={'tracked': [Fact('shell 2026-09-01', '2026-09-01')]})
        self.assertEqual(r.new, [('fresh', 'cargo')])
        self.assertEqual(r.gone, ['removed'])
        self.assertEqual(r.stale, [])

    def test_missing_reason(self):
        r = self.classify({'a': entry(why='TODO'), 'b': entry(why=''), 'c': entry()},
                          {'a': ('app', []), 'b': ('app', []), 'c': ('app', [])},
                          facts={n: [Fact('referenced in .zshrc')] for n in 'abc'})
        self.assertEqual(r.todo, ['a', 'b'])

    def test_dropped_but_present(self):
        r = self.classify({'zombie': entry(status='dropped')},
                          {'zombie': ('app', []), 'phoenix': ('app', [])},
                          archived={'phoenix': entry(why='too slow', status='dropped')})
        self.assertEqual(r.resurrected, [
            ('phoenix', 'pruned as dropped (2026-01-01): too slow'),
            ('zombie', 'marked dropped but still installed'),
        ])
        self.assertEqual(r.new, [])

    def test_kept_is_never_stale_but_still_needs_a_reason(self):
        r = self.classify({'mdm-agent': entry(why='TODO', keep='mdm')}, {'mdm-agent': ('app', [])})
        self.assertEqual(r.kept, [('mdm-agent', 'mdm')])
        self.assertEqual(r.todo, ['mdm-agent'])
        self.assertEqual(r.stale, [])

    def test_staleness(self):
        names = ('old', 'recent', 'undated', 'silent', 'odd-status')
        entries = {n: entry() for n in names}
        entries['odd-status'] = entry(status='weird')
        facts = {
            'old': [Fact('shell 2025-12-01', '2025-12-01'), Fact('referenced in .zshrc')],
            'recent': [Fact('shell 2025-12-01', '2025-12-01'), Fact('used 2026-09-01', '2026-09-01')],
            'undated': [Fact('referenced in .gitconfig')],
        }
        installed = {
            'old': ('brew-formula', ['1.7.1']),
            'recent': ('app', []),
            'undated': ('cargo', ['0.1.0']),
            'silent': ('local-bin', []),
            'odd-status': ('npm-global', ['2.0.0']),
        }
        r = self.classify(entries, installed, facts=facts)
        self.assertEqual(r.stale, [
            ('old', 'brew-formula', '1.7.1',
             'no signal since 2025-12-01 (shell 2025-12-01; referenced in .zshrc)'),
            ('silent', 'local-bin', '-',
             'no usage signal at all — needs a manual look'),
        ])

    def test_version_diff_ignores_unversioned(self):
        r = self.classify({}, {'jq': ('brew-formula', ['1.8.0']), 'script': ('local-bin', [])},
                          prev_versions={'jq': {'versions': ['1.7.1']},
                                         'script': {'versions': []},
                                         'gone': {'versions': ['2']}})
        self.assertEqual(r.v_changed, [('jq', '1.7.1', '1.8.0')])
        self.assertEqual(r.v_added, [])
        self.assertEqual(r.v_removed, [('gone', '2')])


class TestRender(unittest.TestCase):
    def render(self, report, **kw):
        args = dict(tracked=1, installed=1, write=True, had_baseline=True)
        args.update(kw)
        return scan.render(report, **args)

    def test_nothing_to_review(self):
        self.assertEqual(self.render(scan.Report()),
                         'tracked: 1   installed: 1\n\nnothing to review.\n')

    def test_long_lists_are_truncated(self):
        r = scan.Report(new=[(f'tool{i:02}', 'cargo') for i in range(45)])
        text = self.render(r, write=False)
        self.assertIn('NEW — not recorded (45):', text)
        self.assertIn('tool39', text)
        self.assertNotIn('tool40', text)
        self.assertIn('… and 5 more', text)

    def test_dry_run_baseline_wording(self):
        text = self.render(scan.Report(), write=False, had_baseline=False, installed=3)
        self.assertIn('VERSIONS: baseline recorded, 3 entries — not written (--dry-run)', text)

    def test_drop_candidates_show_version_and_source(self):
        r = scan.Report(stale=[
            ('jq', 'brew-formula', '1.7.1', 'no usage signal at all — needs a manual look'),
        ])
        text = self.render(r)
        self.assertIn('DROP CANDIDATES (1):', text)
        self.assertRegex(text, r'jq\s+1\.7\.1\s+brew-formula\s+no usage signal')


class TestScanVersions(unittest.TestCase):
    def setUp(self):
        self.d = Path(tempfile.mkdtemp())
        self.home = Path(tempfile.mkdtemp())

    def tearDown(self):
        shutil.rmtree(self.d)
        shutil.rmtree(self.home)

    def scan(self, installed, write=True):
        out = io.StringIO()
        with mock.patch.object(scan, 'discover_all', return_value=installed), \
                mock.patch.object(scan, 'collect_all', return_value={}), \
                mock.patch('sys.stdout', out), mock.patch('sys.stderr', io.StringIO()):
            rc = scan.run(data_root=self.d, home=self.home, write=write)
        self.assertEqual(rc, 0)
        return out.getvalue()

    def test_unversioned_installs_are_recorded(self):
        self.scan({'jq': ('brew-formula', ['1.7.1']), 'my-script': ('local-bin', [])})
        rows = inventory.load(self.d / 'versions.json')
        self.assertEqual(rows['my-script'], {'source': 'local-bin', 'versions': []})
        self.assertEqual(rows['jq']['versions'], ['1.7.1'])

    def test_unversioned_rows_stay_out_of_the_version_diff(self):
        self.scan({'jq': ('brew-formula', ['1.7.1'])})
        report = self.scan({'jq': ('brew-formula', ['1.7.1']), 'my-script': ('local-bin', [])})
        self.assertNotIn('VERSIONS', report)
        report = self.scan({'jq': ('brew-formula', ['1.7.1'])})
        self.assertNotIn('VERSIONS', report)


class TestAutoArchive(unittest.TestCase):
    def setUp(self):
        self.d = Path(tempfile.mkdtemp())
        self.home = Path(tempfile.mkdtemp())
        inventory.save(self.d / 'software.json', {
            'jq': entry(why='JSON', source='brew-formula'),
            'gone-tool': entry(why='old', source='cargo'),
        })

    def tearDown(self):
        shutil.rmtree(self.d)
        shutil.rmtree(self.home)

    def scan(self, installed, write=True):
        out = io.StringIO()
        with mock.patch.object(scan, 'discover_all', return_value=installed), \
                mock.patch.object(scan, 'collect_all', return_value={}), \
                mock.patch('sys.stdout', out), mock.patch('sys.stderr', io.StringIO()):
            rc = scan.run(data_root=self.d, home=self.home, write=write)
        self.assertEqual(rc, 0)
        return out.getvalue()

    def test_write_archives_gone_with_archived_by_scan(self):
        text = self.scan({'jq': ('brew-formula', ['1.7'])})
        self.assertIn('ARCHIVED — no longer installed (1):', text)
        self.assertIn('gone-tool', text)
        soft = inventory.load(self.d / 'software.json')
        arch = inventory.load(self.d / 'dropped.json')
        self.assertNotIn('gone-tool', soft)
        self.assertEqual(arch['gone-tool']['archived_by'], 'scan')
        self.assertEqual(arch['gone-tool']['why'], 'old')

    def test_dry_run_does_not_archive(self):
        text = self.scan({'jq': ('brew-formula', ['1.7'])}, write=False)
        self.assertIn('NO LONGER INSTALLED', text)
        self.assertIn('will archive on next write scan', text)
        self.assertIn('gone-tool', inventory.load(self.d / 'software.json'))
        self.assertFalse((self.d / 'dropped.json').exists())

    def test_scan_archived_reinstall_restores(self):
        self.scan({'jq': ('brew-formula', ['1.7'])})
        text = self.scan({
            'jq': ('brew-formula', ['1.7']),
            'gone-tool': ('cargo', ['1.0']),
        })
        self.assertIn('RESTORED — reinstalled after auto-archive (1):', text)
        self.assertIn('gone-tool', inventory.load(self.d / 'software.json'))
        self.assertNotIn('gone-tool', inventory.load(self.d / 'dropped.json', missing_ok=True))

    def test_legacy_dropped_without_archived_by_restores(self):
        inventory.save(self.d / 'software.json', {'jq': entry(why='JSON', source='brew-formula')})
        inventory.save(self.d / 'dropped.json', {
            'legacy': entry(why='was dropped', status='dropped', source='app'),
        })
        text = self.scan({
            'jq': ('brew-formula', ['1.7']),
            'legacy': ('app', []),
        })
        self.assertIn('RESTORED', text)
        self.assertIn('legacy', inventory.load(self.d / 'software.json'))
        self.assertNotIn('archived_by', inventory.load(self.d / 'software.json')['legacy'])

    def test_user_drop_stays_while_installed(self):
        inventory.save(self.d / 'software.json', {'jq': entry(why='JSON', source='brew-formula')})
        inventory.save(self.d / 'dropped.json', {
            'noise': inventory.mark_user_drop(entry(why='dup', source='app')),
        })
        text = self.scan({
            'jq': ('brew-formula', ['1.7']),
            'noise': ('app', []),
        })
        self.assertIn('DROPPED BUT PRESENT', text)
        self.assertNotIn('RESTORED', text)
        self.assertIn('noise', inventory.load(self.d / 'dropped.json'))
        self.assertNotIn('noise', inventory.load(self.d / 'software.json'))


class TestPaths(unittest.TestCase):
    def test_vole_data_dir_override(self):
        with tempfile.TemporaryDirectory() as d:
            with mock.patch.dict(os.environ, {'VOLE_DATA_DIR': d}):
                self.assertEqual(paths.data_dir(), Path(d))

    def test_new_data_dir_is_owner_only(self):
        with tempfile.TemporaryDirectory() as d:
            created = paths.ensure_data_dir(Path(d) / 'vole')
            self.assertEqual(created.stat().st_mode & 0o777, 0o700)


if __name__ == '__main__':
    unittest.main(verbosity=2)
