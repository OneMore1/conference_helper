"""Real Windows long-path CLI regressions; synthetic owned fixtures only."""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
from path_utils import display_path, io_path
from local_files import workspace_file_path


def padded_path(base: Path, characters: int) -> Path:
    """Build an exact logical length using ordinary short path components."""
    path = base
    while len(display_path(path)) < characters:
        remaining = characters - len(display_path(path)) - 1
        width = min(60, remaining)
        if remaining - width == 1:
            width -= 1
        if width < 1:
            raise ValueError('Fixture cannot append an empty component')
        path /= ('层级 空格' + 'x' * width)[:width]
    return io_path(path)


@unittest.skipUnless(os.name == 'nt', 'Windows filesystem and import-path behavior')
class WindowsPathTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp_base = io_path(tempfile.gettempdir())
        cls.temp = tempfile.TemporaryDirectory(prefix='windows-runtime-', dir=cls.temp_base)
        cls.fixture = io_path(cls.temp.name)
        if not cls.fixture.is_relative_to(cls.temp_base):
            raise RuntimeError('Temporary fixture escaped the selected writable root')

        def cleanup():
            # The entire tree was created by this class; normalize before both
            # checking and deleting it so long descendants remain addressable.
            if not io_path(cls.temp.name).is_relative_to(cls.temp_base):
                raise RuntimeError('Refusing to clean a relocated fixture')
            cls.temp.cleanup()
        cls.addClassCleanup(cleanup)
        source = io_path(ROOT)
        relative_files = [p.relative_to(source) for p in source.rglob('*')
                          if p.is_file() and '__pycache__' not in p.parts and p.suffix != '.pyc']
        cls.longest_relative = max(relative_files, key=lambda p: len(str(p)))
        skill_name = 'conference-helper'
        parent_length = 450 - len(str(cls.longest_relative)) - len(skill_name) - 2
        cls.installed = padded_path(cls.fixture / '安装 中文', parent_length) / skill_name
        shutil.copytree(source, cls.installed, ignore=shutil.ignore_patterns('__pycache__', '*.pyc'))
        cls.environment = dict(os.environ, PYTHONUTF8='1', PYTHONDONTWRITEBYTECODE='1')

    def cli(self, script: Path, *arguments, expected=0):
        result = subprocess.run([sys.executable, '-B', str(script), *map(str, arguments)],
                                env=self.environment, cwd=self.fixture,
                                capture_output=True, encoding='utf-8', errors='replace', timeout=30)
        self.assertEqual(result.returncode, expected, result.stdout + '\n' + result.stderr)
        self.assertNotIn('Traceback', result.stderr)
        return result

    def workspace(self, label):
        return padded_path(self.fixture / ('工作区 ' + label), 430)

    def exercise_workflow(self, script, label):
        workspace = self.workspace(label)
        # Workspace and draft arguments intentionally use the ordinary spelling;
        # the executable entry point must normalize them internally.
        plain_workspace = display_path(workspace)
        self.cli(script, '--help')
        self.cli(script, 'init', plain_workspace, '--project-id', label)
        state = json.loads((workspace / 'project_state.json').read_text(encoding='utf-8'))
        self.assertEqual(state['schema_version'], '0.2')
        self.assertEqual(json.loads(self.cli(script, 'status', plain_workspace, '--format', 'json').stdout)['revision'], 0)
        state['workstreams']['main']['assessments']['experiments']['status'] = 'not_started'
        draft = workspace / 'synthetic-state-draft.json'
        draft.write_text(json.dumps(state), encoding='utf-8')
        self.cli(script, 'record', plain_workspace, '--input', display_path(draft), '--expected-revision', '0')
        status = json.loads(self.cli(script, 'status', plain_workspace, '--format', 'json').stdout)
        self.assertEqual(status['revision'], 1)
        self.assertEqual(status['active_stage'], 'intake')
        checked = json.loads(self.cli(script, 'check', plain_workspace).stdout)
        self.assertEqual(checked['structural_status'], 'pass')
        self.assertEqual(len(list((workspace / 'artifacts/state_history').glob('*.json'))), 1)
        self.assertFalse((workspace / '.workflow-state.lock').exists())

    def test_drive_spellings_and_dot_components_have_one_io_representation(self):
        normal = Path(display_path(self.fixture))
        self.assertEqual(io_path(normal), io_path(self.fixture))
        self.assertEqual(io_path(normal / 'unused/../record.json'), io_path(self.fixture / 'record.json'))
        self.assertTrue(str(io_path(normal)).startswith('\\\\?\\'))

    def test_unc_spellings_are_equivalent_without_network_access(self):
        normal = r'\\synthetic-server\synthetic-share\folder\record.json'
        extended = r'\\?\UNC\synthetic-server\synthetic-share\folder\record.json'
        self.assertEqual(io_path(normal, resolve=False), io_path(extended, resolve=False))
        self.assertEqual(display_path(io_path(normal, resolve=False)), normal)

    def test_nonfilesystem_device_namespaces_are_rejected(self):
        for value in (r'\\.\pipe\synthetic', r'\\?\GLOBALROOT\Device\Synthetic',
                      r'\\?\Volume{synthetic}\record.json', r'\\?\relative-file'):
            with self.subTest(path=value), self.assertRaisesRegex(ValueError, 'filesystem'):
                io_path(value)

    def test_containment_still_rejects_parent_escape_with_mixed_spellings(self):
        for root in (self.fixture, Path(display_path(self.fixture))):
            with self.subTest(root=str(root)), self.assertRaisesRegex(ValueError, 'inside the workspace'):
                workspace_file_path(root, '../outside.txt')
        self.assertEqual(workspace_file_path(Path(display_path(self.fixture)), 'inside.txt'),
                         io_path(self.fixture / 'inside.txt'))

    def test_all_deep_entrypoints_can_import_siblings_for_help(self):
        self.assertEqual(len(display_path(self.installed / self.longest_relative)), 450)
        self.assertTrue((self.installed / self.longest_relative).is_file())
        for filename in ('workflow.py', 'workflow_state.py', 'init_workspace.py', 'validate_workspace.py'):
            with self.subTest(script=filename):
                self.cli(self.installed / 'scripts' / filename, '--help')

    def test_short_source_entrypoint_operates_on_plain_deep_workspace_argument(self):
        self.exercise_workflow(ROOT / 'scripts/workflow.py', 'short-entry')

    def test_extended_deep_entrypoint_operates_on_plain_deep_workspace_argument(self):
        self.exercise_workflow(self.installed / 'scripts/workflow.py', 'deep-entry')

    def test_plain_deep_script_is_either_loadable_or_stops_at_python_entry_boundary(self):
        script = display_path(self.installed / 'scripts/workflow.py')
        result = subprocess.run([sys.executable, '-B', script, '--help'],
                                env=self.environment, cwd=self.fixture,
                                capture_output=True, encoding='utf-8', errors='replace', timeout=30)
        if result.returncode == 0:
            self.assertIn('usage:', result.stdout)
        else:
            # This process has not reached any package code. The short source
            # entry point tested above remains available without a user prefix.
            self.assertIn("can't open file", result.stderr)
            self.assertNotIn('Traceback', result.stderr)

    def test_deep_legacy_entrypoints_initialize_diagnose_and_validate(self):
        scripts = self.installed / 'scripts'
        workspace = self.workspace('legacy')
        self.cli(scripts / 'init_workspace.py', display_path(workspace), '--project-id', 'legacy')
        diagnosed = json.loads(self.cli(scripts / 'workflow_state.py', 'diagnose', display_path(workspace)).stdout)
        self.assertEqual(diagnosed['status'], 'routed')
        checked = json.loads(self.cli(scripts / 'validate_workspace.py', display_path(workspace), '--stage', 'intake').stdout)
        self.assertEqual(checked['structural_status'], 'pass')


if __name__ == '__main__':
    unittest.main()
