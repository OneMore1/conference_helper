"""Exercise the release runner using tiny copied suites, never recursively."""
from __future__ import annotations
import contextlib
import io
import json
import os
import shutil
import subprocess
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
import run_checks


FAKE_SUITE = '''import json
import os
import tempfile
import unittest
from pathlib import Path

class TinySuite(unittest.TestCase):
    def test_environment(self):
        suite = Path(__file__).parent.name
        record = dict(suite=suite, tempdir=tempfile.gettempdir(),
                      environment={key: os.environ.get(key) for key in
                                   ('TMP', 'TEMP', 'TMPDIR', 'PYTHONDONTWRITEBYTECODE')})
        with open(os.environ['CHECKS_TEST_LOG'], 'a', encoding='utf-8') as handle:
            handle.write(json.dumps(record) + '\\n')
        with tempfile.TemporaryDirectory() as name:
            child = Path(name)
            (child / 'probe.txt').write_text('temporary', encoding='utf-8')
            self.assertFalse(child.is_relative_to(Path.cwd()))
        if os.environ.get('CHECKS_TEST_FAIL') == suite:
            self.fail('intentional tiny-suite failure')
'''


class ReleaseRunnerTests(unittest.TestCase):
    def setUp(self):
        temporary = run_checks.create_run_workspace(ROOT)
        self.addCleanup(temporary.cleanup)
        self.base = Path(temporary.name)
        self.repo = self.base / 'minimal source'
        (self.repo / 'tools').mkdir(parents=True)
        shutil.copyfile(ROOT / 'tools/run_checks.py', self.repo / 'tools/run_checks.py')
        for folder in ('skills/conference-helper/evals', 'tests'):
            target = self.repo / folder
            target.mkdir(parents=True)
            (target / 'test_tiny.py').write_text(FAKE_SUITE, encoding='utf-8')
        self.log = self.base / 'observations.jsonl'

    def run_entry(self, *arguments, extra_env=None):
        env = dict(os.environ, PYTHONUTF8='1', PYTHONDONTWRITEBYTECODE='1',
                   CHECKS_TEST_LOG=str(self.log))
        env.pop('CHECKS_TEST_FAIL', None)
        env.update(extra_env or {})
        return subprocess.run(
            [sys.executable, str(self.repo / 'tools/run_checks.py'), *map(str, arguments)],
            cwd=self.repo, env=env, capture_output=True, text=True, encoding='utf-8')

    def observations(self):
        return [json.loads(line) for line in self.log.read_text(encoding='utf-8').splitlines()]

    def test_entry_succeeds_with_adverse_temp_environment(self):
        not_directory = self.base / 'temp is a file'
        not_directory.write_text('keep', encoding='utf-8')
        result = self.run_entry(extra_env={
            'TMPDIR': str(self.repo), 'TEMP': str(not_directory),
            'TMP': str(self.base / 'missing directory')})
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        records = self.observations()
        self.assertEqual([record['suite'] for record in records], ['evals', 'tests'])
        self.assertEqual(records[0]['tempdir'], records[1]['tempdir'])
        for record in records:
            directory = Path(record['tempdir'])
            self.assertFalse(directory.is_relative_to(self.repo))
            self.assertFalse(directory.exists(), 'owned workspace must be cleaned up')
            for key in ('TMP', 'TEMP', 'TMPDIR'):
                self.assertEqual(record['environment'][key], str(directory))
            self.assertEqual(record['environment']['PYTHONDONTWRITEBYTECODE'], '1')
        self.assertEqual(not_directory.read_text(encoding='utf-8'), 'keep')
        self.assertEqual(list(self.repo.rglob('__pycache__')), [])

    def test_explicit_root_is_preserved_and_runs_are_isolated(self):
        temp_root = self.base / 'requested root'
        temp_root.mkdir()
        marker = temp_root / 'user-file.txt'
        marker.write_text('preserve', encoding='utf-8')
        for _ in range(2):
            result = self.run_entry('--temp-root', temp_root)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertEqual(list(temp_root.iterdir()), [marker])
        records = self.observations()
        self.assertEqual(len(records), 4)
        self.assertNotEqual(records[0]['tempdir'], records[2]['tempdir'])
        self.assertTrue(all(Path(record['tempdir']).parent == temp_root for record in records))
        self.assertEqual(marker.read_text(encoding='utf-8'), 'preserve')

    def test_explicit_invalid_roots_fail_without_falling_back(self):
        not_directory = self.base / 'file'
        not_directory.write_text('preserve', encoding='utf-8')
        for root, explanation in [
            (self.repo, 'outside the source repository'),
            (self.repo / 'tools', 'outside the source repository'),
            (self.base / 'missing', 'existing directory'),
            (not_directory, 'existing directory'),
        ]:
            with self.subTest(root=root):
                result = self.run_entry('--temp-root', root)
                self.assertEqual(result.returncode, 2)
                self.assertIn('Requested --temp-root is unusable', result.stderr)
                self.assertIn(explanation, result.stderr)
                self.assertNotIn('Traceback', result.stderr)
                self.assertFalse(self.log.exists(), 'no suite should start')
        self.assertFalse((self.base / 'missing').exists())
        self.assertEqual(not_directory.read_text(encoding='utf-8'), 'preserve')

    def test_parent_directory_fallback_uses_owned_child_only(self):
        candidates = [self.repo, self.base / 'missing', self.repo.parent]
        with patch.object(run_checks, 'default_temp_roots', return_value=candidates):
            with run_checks.create_run_workspace(self.repo) as directory:
                created = Path(directory)
                self.assertEqual(created.parent, self.repo.parent)
                self.assertTrue(created.is_dir())
        self.assertFalse(created.exists())
        self.assertTrue(self.repo.is_dir())

    def test_exhausted_defaults_report_temp_root_guidance(self):
        error = io.StringIO()
        with patch.object(run_checks, 'ROOT', self.repo), \
                patch.object(run_checks, 'default_temp_roots', return_value=[self.repo]), \
                patch.object(run_checks.subprocess, 'run') as launch, \
                contextlib.redirect_stderr(error):
            code = run_checks.main([])
        self.assertEqual(code, 2)
        self.assertIn('No usable temporary root', error.getvalue())
        self.assertIn('--temp-root EXISTING_WRITABLE_DIRECTORY', error.getvalue())
        launch.assert_not_called()

    def test_permission_denial_is_rejected_before_tempfile_retry(self):
        with patch.object(Path, 'mkdir', side_effect=PermissionError('mkdir denied')), \
                patch.object(run_checks.tempfile, 'TemporaryDirectory') as temporary:
            with self.assertRaisesRegex(run_checks.TempRootError, 'mkdir denied'):
                run_checks.create_run_workspace(self.repo, self.base)
        temporary.assert_not_called()

    def test_suite_failure_returns_one_and_still_runs_both_suites(self):
        result = self.run_entry('--temp-root', self.base,
                                extra_env={'CHECKS_TEST_FAIL': 'evals'})
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        self.assertIn('intentional tiny-suite failure', result.stderr)
        records = self.observations()
        self.assertEqual([record['suite'] for record in records], ['evals', 'tests'])
        self.assertTrue(all(not Path(record['tempdir']).exists() for record in records))

    def test_runner_does_not_modify_parent_environment(self):
        before = dict(os.environ)
        with patch.object(run_checks, 'ROOT', self.repo), \
                patch.object(run_checks.subprocess, 'run') as launch, \
                contextlib.redirect_stdout(io.StringIO()):
            launch.return_value.returncode = 0
            code = run_checks.main(['--temp-root', str(self.base)])
        self.assertEqual(code, 0)
        self.assertEqual(dict(os.environ), before)
        self.assertEqual(launch.call_count, 2)
        workspace = Path(launch.call_args.kwargs['env']['TEMP'])
        self.assertEqual(workspace.parent, self.base)
        self.assertFalse(workspace.exists())

    def test_launch_error_is_diagnosed_and_workspace_is_cleaned(self):
        before = set(self.base.iterdir())
        error = io.StringIO()
        with patch.object(run_checks, 'ROOT', self.repo), \
                patch.object(run_checks.subprocess, 'run', side_effect=OSError('launch denied')), \
                contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(error):
            code = run_checks.main(['--temp-root', str(self.base)])
        self.assertEqual(code, 2)
        self.assertIn('launch denied', error.getvalue())
        self.assertNotIn('Traceback', error.getvalue())
        self.assertEqual(set(self.base.iterdir()), before)


if __name__ == '__main__':
    unittest.main()
