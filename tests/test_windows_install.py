"""Installer regressions using real paths and isolated, removable fixtures.

Set CONFERENCE_INSTALL_TEST_ROOT to place fixtures in a specific writable root.
Only fixture creation, verification and cleanup use extended Windows paths;
the CLI under test receives an ordinary --project path, including spaces/Unicode.
"""
from __future__ import annotations

import fnmatch
import importlib.util
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / 'skills' / 'conference-helper'
INSTALLER = ROOT / 'tools' / 'install_skill.py'
NAME = SOURCE.name

_spec = importlib.util.spec_from_file_location('windows_install_under_test', INSTALLER)
installer = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(installer)


def ordinary_path(value: str | Path) -> Path:
    """Test-side path identity, independent of the production path helper."""
    text = os.fspath(value)
    if os.name == 'nt':
        if text.startswith('\\\\?\\UNC\\'):
            text = '\\\\' + text[8:]
        elif text.startswith('\\\\?\\'):
            text = text[4:]
    return Path(os.path.abspath(text))


def fixture_io(value: str | Path) -> Path:
    """Allow the verifier and cleanup to see every deep fixture file."""
    path = ordinary_path(value)
    if os.name != 'nt':
        return path
    text = str(path)
    return Path('\\\\?\\UNC\\' + text[2:] if text.startswith('\\\\') else '\\\\?\\' + text)


def identity(value: str | Path) -> str:
    return os.path.normcase(str(ordinary_path(value)))


def expected_source_files() -> dict[Path, bytes]:
    """Fail loudly on traversal errors; do not infer missing files via rglob."""
    result = {}
    root = fixture_io(SOURCE)

    def raise_walk_error(error: OSError) -> None:
        raise error

    def included(name: str) -> bool:
        return not any(fnmatch.fnmatch(name, pattern)
                       for pattern in ('__pycache__', '*.pyc', '.DS_Store'))

    for directory, directories, filenames in os.walk(root, onerror=raise_walk_error):
        directories[:] = [name for name in directories if included(name)]
        for filename in filenames:
            if included(filename):
                path = Path(directory) / filename
                result[path.relative_to(root)] = path.read_bytes()
    if Path('SKILL.md') not in result or Path('LICENSE') not in result:
        raise AssertionError('The canonical source manifest lacks SKILL.md or LICENSE.')
    return result


# Run the actual entry point while disallowing registry access, shell/child
# processes and ctypes calls that could be used to change machine settings.
# This guard does not change the installer arguments or normalize --project.
CLI_GUARD = r'''
import runpy
import sys

def reject_system_changes(event, arguments):
    forbidden = ('subprocess.Popen', 'os.system', 'os.exec', 'os.posix_spawn',
                 'os.spawn', 'ctypes.dlopen', 'ctypes.dlsym', 'ctypes.call_function')
    if event.startswith('winreg.') or event in forbidden:
        raise RuntimeError('Installer attempted a system-settings or process action: ' + event)

sys.addaudithook(reject_system_changes)
entry = sys.argv[1]
sys.argv = sys.argv[1:]
runpy.run_path(entry, run_name='__main__')
'''


class WindowsInstallerTests(unittest.TestCase):
    def setUp(self):
        parent = Path(os.environ.get('CONFERENCE_INSTALL_TEST_ROOT', tempfile.gettempdir()))
        parent = ordinary_path(parent)
        fixture_io(parent).mkdir(parents=True, exist_ok=True)
        self.base = ordinary_path(tempfile.mkdtemp(prefix='win-install-', dir=fixture_io(parent)))
        self.addCleanup(self.cleanup_fixture, parent, self.base)
        self.files = expected_source_files()

    @staticmethod
    def cleanup_fixture(parent: Path, root: Path) -> None:
        # Check the absolute target before recursive deletion; delete only this
        # test's uniquely named directory, through one filesystem API.
        parent_key, root_key = identity(parent), identity(root)
        if root_key == parent_key or os.path.commonpath([parent_key, root_key]) != parent_key:
            raise AssertionError('Refusing to clean outside the test fixture root.')
        if not ordinary_path(root).name.startswith('win-install-'):
            raise AssertionError('Refusing to clean a directory not owned by this test.')
        if fixture_io(root).exists():
            shutil.rmtree(fixture_io(root))

    def assert_installed_files(self, root: Path, overrides=None) -> None:
        expected = dict(self.files)
        expected.update(overrides or {})
        for relative, data in expected.items():
            with self.subTest(file=str(relative)):
                # Read every source-derived path directly. A truncated installed
                # tree enumeration must never make a missing file look present.
                actual = fixture_io(root / relative).read_bytes()
                self.assertEqual(actual, data, str(relative))

    def cli(self, project: Path, backup=False):
        project = ordinary_path(project)
        self.assertFalse(str(project).startswith('\\\\?\\'))
        command = [sys.executable, '-c', CLI_GUARD, str(INSTALLER), '--project', str(project)]
        if backup:
            command.append('--backup-existing')
        return subprocess.run(command, capture_output=True, text=True, encoding='utf-8',
                              env=dict(os.environ, PYTHONUTF8='1', PYTHONDONTWRITEBYTECODE='1'),
                              timeout=90)

    def project_with_longest_file(self, length: int) -> Path:
        relative = max(self.files, key=lambda path: len(str(path)))
        suffix = Path('.agents') / 'skills' / NAME / relative
        desired_project_length = length - len(str(suffix)) - 1
        project = self.base / ('中文 项目 ' + str(length))
        if len(str(project)) > desired_project_length:
            self.skipTest('Fixture root is too long to construct the requested path length.')
        while len(str(project)) < desired_project_length:
            remaining = desired_project_length - len(str(project))
            if remaining == 1:
                project = project.with_name(project.name + 'x')
            else:
                segment_length = min(60, remaining - 1)
                project /= '层' + 'x' * (segment_length - 1)
        self.assertEqual(max(len(str(project / '.agents' / 'skills' / NAME / p))
                             for p in self.files), length)
        return project

    def test_git_source_explicit_path_installs_every_file(self):
        destination = self.base / '普通 中文 项目' / '.agents' / 'skills' / NAME
        result = installer.install(destination, source=SOURCE)
        self.assertEqual(identity(result['path']), identity(destination))
        self.assertIsNone(result['backup'])
        self.assert_installed_files(destination)

    def test_cli_needs_no_system_setting_changes(self):
        project = self.base / '无系统修改 中文 项目'
        result = self.cli(project)
        self.assertEqual(result.returncode, 0, result.stderr)
        payload = json.loads(result.stdout)
        self.assertEqual(payload['status'], 'installed')
        self.assert_installed_files(project / '.agents' / 'skills' / NAME)

    @unittest.skipUnless(os.name == 'nt', 'Real Windows MAX_PATH regression')
    def test_plain_project_paths_install_refuse_and_backup_at_three_depths(self):
        for length in (260, 320, 450):
            with self.subTest(longest_file_path=length):
                project = self.project_with_longest_file(length)
                destination = project / '.agents' / 'skills' / NAME
                first = self.cli(project)
                self.assertEqual(first.returncode, 0, first.stderr)
                result = json.loads(first.stdout)
                self.assertEqual(identity(result['path']), identity(destination))
                self.assert_installed_files(destination)

                local_license = self.files[Path('LICENSE')] + b'\nLOCAL LICENSE NOTE\n'
                marker = b'Local content must survive refused and backed-up upgrades.\n'
                fixture_io(destination / 'LICENSE').write_bytes(local_license)
                fixture_io(destination / 'local-marker.txt').write_bytes(marker)
                old_files = {Path('LICENSE'): local_license, Path('local-marker.txt'): marker}

                refused = self.cli(project)
                self.assertEqual(refused.returncode, 2, refused.stdout + refused.stderr)
                self.assertEqual(json.loads(refused.stderr)['status'], 'error')
                self.assert_installed_files(destination, old_files)

                upgraded = self.cli(project, backup=True)
                self.assertEqual(upgraded.returncode, 0, upgraded.stderr)
                result = json.loads(upgraded.stdout)
                backup = Path(result['backup'])
                self.assertEqual(identity(result['path']), identity(destination))
                self.assert_installed_files(destination)
                self.assertFalse(fixture_io(destination / 'local-marker.txt').exists())
                self.assert_installed_files(backup, old_files)
                self.assertNotEqual(os.path.commonpath([identity(backup), identity(destination.parent)]),
                                    identity(destination.parent))

    @unittest.skipUnless(os.name == 'nt', 'Extended Windows path aliases')
    def test_same_source_in_plain_and_extended_forms_is_rejected(self):
        for extended_destination in (False, True):
            with self.subTest(extended_destination=extended_destination):
                source = self.base / str(extended_destination) / NAME
                shutil.copytree(fixture_io(SOURCE), fixture_io(source),
                                ignore=shutil.ignore_patterns('__pycache__', '*.pyc', '.DS_Store'))
                destination_arg = fixture_io(source) if extended_destination else source
                source_arg = source if extended_destination else fixture_io(source)
                with self.assertRaisesRegex(ValueError, '(?i)overlap'):
                    installer.install(destination_arg, backup_existing=True, source=source_arg)
                self.assert_installed_files(source)

    def test_final_rename_failure_restores_old_installation(self):
        project = (self.project_with_longest_file(450) if os.name == 'nt'
                   else self.base / 'rollback 中文 项目')
        destination = project / '.agents' / 'skills' / NAME
        installer.install(destination, source=SOURCE)
        marker = b'Preserve this local marker when promotion fails.\n'
        local_license = self.files[Path('LICENSE')] + b'\nLOCAL BEFORE FAILURE\n'
        fixture_io(destination / 'local-marker.txt').write_bytes(marker)
        fixture_io(destination / 'LICENSE').write_bytes(local_license)
        # Patch the public Path methods: Python 3.10's pathlib accessor caches
        # os.rename, so patching os.rename itself does not intercept Path.rename.
        original_rename, original_replace = Path.rename, Path.replace
        injected = False

        def intercept(original):
            def rename(self_path, target, *args, **kwargs):
                nonlocal injected
                if not injected and identity(target) == identity(destination):
                    injected = True
                    raise OSError('Synthetic failure promoting the completed installation.')
                return original(self_path, target, *args, **kwargs)
            return rename

        with mock.patch.object(Path, 'rename', new=intercept(original_rename)), \
                mock.patch.object(Path, 'replace', new=intercept(original_replace)):
            with self.assertRaisesRegex(OSError, 'Synthetic failure'):
                installer.install(destination, backup_existing=True, source=SOURCE)
        self.assertTrue(injected, 'The final rename failure injection was not exercised.')
        self.assert_installed_files(destination, {Path('LICENSE'): local_license,
                                                 Path('local-marker.txt'): marker})
        # A subsequent upgrade also proves a failure did not leave a stale lock.
        result = installer.install(destination, backup_existing=True, source=SOURCE)
        self.assert_installed_files(destination)
        self.assert_installed_files(Path(result['backup']), {Path('LICENSE'): local_license,
                                                           Path('local-marker.txt'): marker})


if __name__ == '__main__':
    unittest.main()
