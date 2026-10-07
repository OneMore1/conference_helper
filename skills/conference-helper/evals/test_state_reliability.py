"""Synthetic regressions for evidence freshness and recoverable state errors."""
from __future__ import annotations

import copy
import json
import os
import subprocess
import sys
import tempfile
import unittest
from datetime import date
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
from init_workspace import initialize
from validate_workspace import validate
from workflow_state import commit, diagnose, digest, init_state, ledger_sources, validate_state
from path_utils import display_path


class StateReliabilityTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.root = Path(temp.name) / 'paper'
        initialize(self.root, 'synthetic-reliability')
        self.state = self.load('project_state.json')
        self.stream = self.state['workstreams']['main']
        self.a = self.stream['assessments']
        project = self.load('project.json')
        project.update(user_request_verbatim='Synthetic request',
                       research_question='Synthetic question')
        self.save('project.json', project)

    def load(self, name):
        return json.loads((self.root / name).read_text(encoding='utf-8'))

    def save(self, name, value):
        (self.root / name).write_text(json.dumps(value), encoding='utf-8')

    def mark(self, field, evidence=None):
        self.a[field].update(status='complete',
                             evidence=evidence or ['author:synthetic fixture'],
                             note='Synthetic fixture only')

    def ready(self):
        for field in ('literature_grounding', 'experiments', 'result_analysis',
                      'evidence_gaps', 'manuscript', 'internal_review'):
            self.mark(field)

    def source(self):
        path = self.root / 'results' / 'synthetic.txt'
        path.write_text('SYNTHETIC V1', encoding='utf-8')
        source = {'source_id': 'S1', 'kind': 'local_result',
                  'locator': 'results/synthetic.txt', 'sha256': digest(path),
                  'verification': 'read', 'checked_on': date.today().isoformat(),
                  'location_detail': 'Synthetic fixture only'}
        self.save('evidence_ledger.json', {'sources': [source], 'claims': []})
        self.a['result_analysis']['evidence'] = ['source:S1']
        return path, source

    def route(self, requested=None, workstream=None):
        self.save('project_state.json', self.state)
        return diagnose(self.root, requested, workstream)

    def assert_analysis_stale(self, report):
        self.assertEqual(report['status'], 'routed')
        self.assertEqual(report['recommended_stage'], 'analysis')
        self.assertEqual(report['effective_status']['result_analysis'], 'needs_refresh')
        self.assertIn('manuscript', report['stale_fields'])
        self.assertIn('internal_review', report['stale_fields'])
        self.assertNotIn('experiments', report['stale_fields'])
        self.assertNotIn('literature_grounding', report['stale_fields'])
        self.assertFalse(report['assessment_truth_verified_by_script'])

    def test_source_hash_change_invalidates_dependent_work(self):
        self.ready(); path, _ = self.source()
        self.assertEqual(self.route()['recommended_stage'], 'submission')
        path.write_text('SYNTHETIC V2', encoding='utf-8')
        report = self.route()
        self.assert_analysis_stale(report)
        self.assertTrue(any('source:S1: SHA-256 mismatch' in w for w in report['warnings']))
        self.assertTrue(any('S1: SHA-256 mismatch' in e for e in validate(self.root, 'writing')['errors']))

    def test_missing_source_file_invalidates_dependent_work(self):
        self.ready(); path, _ = self.source(); path.unlink()
        report = self.route()
        self.assert_analysis_stale(report)
        self.assertTrue(any('file not found' in w for w in report['warnings']))

    def test_illegal_source_paths_are_stale_without_reading_outside(self):
        self.ready(); _, source = self.source()
        for locator in ('../outside.txt', str(self.root.parent / 'outside.txt'), [], '\x00'):
            with self.subTest(locator=repr(locator)):
                source['locator'] = locator
                self.save('evidence_ledger.json', {'sources': [source], 'claims': []})
                with patch('local_files.file_hash') as hasher:
                    self.assert_analysis_stale(self.route())
                    self.assertTrue(validate(self.root, 'writing')['errors'])
                    hasher.assert_not_called()

    def test_only_selected_workstream_source_files_are_checked(self):
        self.ready(); path, _ = self.source()
        self.state['workstreams']['other'] = copy.deepcopy(self.stream)
        self.mark('result_analysis')
        path.unlink()
        main = self.route()
        self.assertEqual(main['recommended_stage'], 'submission')
        self.assertEqual(main['stale_fields'], [])
        self.assertFalse(any('source:S1' in w for w in main['warnings']))
        other = self.route(workstream='other')
        self.assert_analysis_stale(other)

    def test_unused_source_file_does_not_add_staleness(self):
        self.ready(); path, _ = self.source(); self.mark('result_analysis')
        path.unlink()
        self.assertEqual(self.route()['stale_fields'], [])

    def test_unselected_unknown_source_does_not_block_current_route(self):
        self.ready()
        self.state['workstreams']['other'] = copy.deepcopy(self.stream)
        self.state['workstreams']['other']['assessments']['result_analysis']['evidence'] = ['source:UNKNOWN']
        self.assertEqual(self.route()['recommended_stage'], 'submission')
        self.assertEqual(self.route(workstream='other')['status'], 'invalid_state')
        with self.assertRaisesRegex(ValueError, 'unknown ledger source'):
            commit(self.root, self.state, 0)

    def test_unreferenced_duplicate_sources_do_not_block_current_route(self):
        self.ready(); _, source = self.source()
        unrelated = dict(source, source_id='OTHER')
        self.save('evidence_ledger.json', {'sources': [source, unrelated, copy.deepcopy(unrelated)], 'claims': []})
        self.assertEqual(self.route()['recommended_stage'], 'submission')
        with self.assertRaisesRegex(ValueError, 'duplicate source_id: OTHER'):
            commit(self.root, self.state, 0)

    def test_source_change_preserves_explicit_task_and_historical_receipt(self):
        self.ready(); path, _ = self.source(); self.mark('submission_receipt')
        path.unlink()
        report = self.route(requested='writing')
        self.assert_analysis_stale(report)
        self.assertEqual(report['active_stage'], 'writing')
        self.assertEqual(report['effective_status']['submission_receipt'], 'complete')

    def test_source_missing_hash_is_compatible_but_final_preflight_requires_it(self):
        self.ready(); _, source = self.source(); del source['sha256']
        self.save('evidence_ledger.json', {'sources': [source], 'claims': []})
        self.assertEqual(self.route()['stale_fields'], [])
        self.assertFalse(any('SHA-256' in e for e in validate(self.root, 'writing')['errors']))
        self.assertTrue(any('S1: SHA-256 required' in e for e in validate(self.root, 'submission')['errors']))

    def test_uppercase_source_hash_matches(self):
        self.ready(); _, source = self.source(); source['sha256'] = source['sha256'].upper()
        self.save('evidence_ledger.json', {'sources': [source], 'claims': []})
        self.assertEqual(self.route()['stale_fields'], [])
        self.assertEqual(validate(self.root, 'writing')['errors'], [])

    def test_bad_source_hash_is_diagnosed_by_both_entry_points(self):
        self.ready(); _, source = self.source(); source['sha256'] = 'z' * 64
        self.save('evidence_ledger.json', {'sources': [source], 'claims': []})
        self.assert_analysis_stale(self.route())
        self.assertIn('S1: invalid SHA-256', validate(self.root, 'writing')['errors'])

    def test_unreadable_evidence_is_reported_by_both_entry_points(self):
        self.ready(); self.source()
        with patch('local_files.file_hash', side_effect=PermissionError('synthetic denied read')):
            report = self.route()
            self.assert_analysis_stale(report)
            self.assertTrue(any('cannot read file' in w for w in report['warnings']))
            self.assertTrue(any('cannot read file' in e for e in validate(self.root, 'writing')['errors']))

    def test_public_and_author_sources_do_not_imply_independent_verification(self):
        self.ready()
        self.save('evidence_ledger.json', {'sources': [
            {'source_id': 'P1', 'kind': 'public_paper', 'locator': 'https://example.invalid/paper'},
            {'source_id': 'A1', 'kind': 'author_statement', 'locator': 'author confirmation'}], 'claims': []})
        self.a['result_analysis']['evidence'] = ['source:P1', 'source:A1']
        with patch('workflow_state.check_local_file') as check:
            report = self.route()
            check.assert_not_called()
        self.assertEqual(report['stale_fields'], [])
        self.assertFalse(report['assessment_truth_verified_by_script'])

    def test_duplicate_source_ids_are_rejected_instead_of_selecting_one(self):
        self.ready(); _, source = self.source()
        self.save('evidence_ledger.json', {'sources': [source, copy.deepcopy(source)], 'claims': []})
        report = self.route()
        self.assertEqual(report['status'], 'invalid_state')
        self.assertTrue(any('duplicate source_id: S1' in e for e in report['errors']))
        self.assertTrue(any('duplicate source_id: S1' in e for e in validate(self.root, 'writing')['errors']))
        with self.assertRaisesRegex(ValueError, 'duplicate source_id'):
            commit(self.root, self.state, 0)

    def test_invalid_source_registry_shapes_have_context(self):
        self.mark('manuscript', ['source:S1'])
        for sources in ({}, [None], [{'source_id': []}]):
            with self.subTest(sources=sources):
                self.save('evidence_ledger.json', {'sources': sources, 'claims': []})
                report = self.route()
                self.assertEqual(report['status'], 'invalid_state')
                self.assertTrue(any('ledger.sources' in e or 'unknown ledger source S1' in e for e in report['errors']))

    def test_not_started_without_note_can_be_committed_and_diagnosed(self):
        self.a['experiments']['status'] = 'not_started'
        del self.a['experiments']['note']
        self.assertEqual(validate_state(self.state, self.root), [])
        self.assertEqual(commit(self.root, self.state, 0)['revision'], 1)
        report = diagnose(self.root)
        self.assertEqual(report['status'], 'routed')
        self.assertEqual(report['assessment_basis']['experiments']['note'], '')

    def test_declared_text_fields_reject_nontext_values(self):
        original = copy.deepcopy(self.state)
        for path in (('updated_at',), ('workstreams', 'main', 'latest_request'),
                     ('workstreams', 'main', 'assessments', 'experiments', 'note'),
                     ('workstreams', 'main', 'assessments', 'experiments', 'assessed_by')):
            with self.subTest(path=path):
                draft = copy.deepcopy(original); target = draft
                for key in path[:-1]: target = target[key]
                target[path[-1]] = []
                errors = validate_state(draft, self.root)
                self.assertTrue(any(path[-1] in e and 'text' in e for e in errors), errors)

    def test_wrong_state_types_return_validation_errors(self):
        cases = [('active_workstream', []), ('active_workstream', {}),
                 ('workstreams', []), ('workstreams', {'main': []})]
        for key, value in cases:
            with self.subTest(key=key, value=value):
                draft = copy.deepcopy(self.state); draft[key] = value
                self.assertTrue(validate_state(draft, self.root))
        for key, value in [('requested_stage', []), ('assessments', []), ('artifacts', {}),
                           ('gaps', [{'id': 'G1', 'reason': 'Synthetic', 'priority': [], 'status': {}}]),
                           ('invalidations', [{'reason': 'Synthetic', 'affected_fields': [{}], 'status': []}])]:
            with self.subTest(key=key, value=value):
                draft = copy.deepcopy(self.state); draft['workstreams']['main'][key] = value
                self.assertTrue(validate_state(draft, self.root))
        self.assertEqual(validate_state([], self.root), ['state: JSON root must be an object'])

    def test_invalid_json_types_produce_cli_diagnostics_without_traceback(self):
        self.state['active_workstream'] = []
        self.save('project_state.json', self.state)
        result = subprocess.run([sys.executable, '-B', str(ROOT / 'scripts/workflow_state.py'),
                                 'diagnose', str(self.root)], capture_output=True, text=True,
                                env=dict(os.environ, PYTHONDONTWRITEBYTECODE='1', PYTHONUTF8='1'))
        self.assertEqual(result.returncode, 2)
        self.assertEqual(json.loads(result.stdout)['status'], 'invalid_state')
        self.assertNotIn('Traceback', result.stderr)

    def test_invalid_commit_draft_does_not_mutate_state_or_leave_lock(self):
        before = (self.root / 'project_state.json').read_bytes()
        self.state['workstreams'] = []
        with self.assertRaisesRegex(ValueError, 'workstreams'):
            commit(self.root, self.state, 0)
        self.assertEqual(before, (self.root / 'project_state.json').read_bytes())
        self.assertFalse((self.root / '.workflow-state.lock').exists())

    def test_corrupt_current_workstreams_get_a_recovery_error(self):
        broken = copy.deepcopy(self.state); broken['workstreams'] = None
        self.save('project_state.json', broken)
        before = (self.root / 'project_state.json').read_bytes()
        with self.assertRaisesRegex(ValueError, 'restore the state'):
            commit(self.root, self.state, 0)
        self.assertEqual(before, (self.root / 'project_state.json').read_bytes())
        self.assertFalse((self.root / '.workflow-state.lock').exists())

    def test_concept_change_refreshes_related_literature_without_question_restart(self):
        self.ready(); self.mark('concept'); self.mark('research_question')
        path = self.root / 'method.txt'; path.write_text('SYNTHETIC V1', encoding='utf-8')
        self.stream['artifacts'] = [{'id': 'M1', 'path': 'method.txt', 'sha256': digest(path)}]
        self.a['concept']['evidence'] = ['artifact:M1']
        path.write_text('SYNTHETIC V2', encoding='utf-8')
        report = self.route('writing')
        self.assertIn('literature_grounding', report['stale_fields'])
        self.assertIn('experiment_plan', report['stale_fields'])
        self.assertNotIn('research_question', report['stale_fields'])
        self.assertEqual(report['active_stage'], 'writing')
        self.assertEqual(report['effective_status']['literature_grounding'], 'needs_refresh')

    def test_wrong_workspace_enums_are_errors_not_type_exceptions(self):
        self.ready(); _, source = self.source()
        project = self.load('project.json')
        project['stage'] = []; project['contribution_type'] = {}
        project['novelty_assessment']['status'] = []
        self.save('project.json', project)
        source['kind'] = []; source['verification'] = {}
        self.save('evidence_ledger.json', {'sources': [source], 'claims': [
            {'claim_id': 'C1', 'text': 'Synthetic claim', 'claim_type': [],
             'use_in_manuscript': {}, 'status': [], 'evidence_ids': ['S1']}]})
        report = validate(self.root)
        self.assertEqual(report['structural_status'], 'needs_attention')
        for fragment in ('stage:', 'contribution_type', 'novelty_assessment.status',
                         'source kind', 'verification', 'claim_type', 'use_in_manuscript'):
            self.assertTrue(any(fragment in e for e in report['errors']), fragment)

    def directory_link(self, link, target):
        """Use a real Windows junction without requiring symlink privileges."""
        target.mkdir(parents=True, exist_ok=True)
        if os.name == 'nt':
            result = subprocess.run(['cmd.exe', '/d', '/c', 'mklink', '/J', str(link), str(target)],
                                    capture_output=True, text=True)
            if result.returncode:
                self.skipTest(f'Windows junction creation unavailable: {result.stderr.strip()}')
        else:
            try:
                link.symlink_to(target, target_is_directory=True)
            except OSError as exc:
                self.skipTest(f'Directory symlink creation unavailable: {exc}')

        def remove_link():
            # Remove the link itself before TemporaryDirectory recursively cleans
            # up its owned fixture tree. Never recurse through a junction.
            if os.path.lexists(link):
                if os.name == 'nt':
                    os.rmdir(link)
                else:
                    link.unlink()
        self.addCleanup(remove_link)
        self.assertEqual(link.resolve(), target.resolve())

    def test_real_history_directory_link_cannot_write_outside_workspace(self):
        target = self.root.parent / 'outside-paper-history'
        self.directory_link(self.root / 'artifacts/state_history', target)
        marker = target / 'untouched.txt'; marker.write_text('SYNTHETIC GUARD', encoding='utf-8')
        before = (self.root / 'project_state.json').read_bytes()
        with self.assertRaisesRegex(ValueError, 'inside the workspace.*state_history'):
            commit(self.root, self.state, 0)
        self.assertEqual(before, (self.root / 'project_state.json').read_bytes())
        self.assertEqual([p.name for p in target.iterdir()], ['untouched.txt'])
        self.assertEqual(marker.read_text(encoding='utf-8'), 'SYNTHETIC GUARD')
        self.assertFalse((self.root / '.workflow-state.lock').exists())

    def test_real_artifacts_parent_link_cannot_write_outside_workspace(self):
        target = self.root.parent / 'outside-artifacts'
        (self.root / 'artifacts').rmdir()  # Only succeeds for the empty fixture directory.
        self.directory_link(self.root / 'artifacts', target)
        before = (self.root / 'project_state.json').read_bytes()
        with self.assertRaisesRegex(ValueError, 'inside the workspace'):
            commit(self.root, self.state, 0)
        self.assertEqual(before, (self.root / 'project_state.json').read_bytes())
        self.assertEqual(list(target.iterdir()), [])
        self.assertFalse((self.root / '.workflow-state.lock').exists())

    def test_directory_link_within_workspace_keeps_normal_commit_working(self):
        target = self.root / 'history-storage'
        self.directory_link(self.root / 'artifacts/state_history', target)
        self.assertEqual(commit(self.root, self.state, 0)['revision'], 1)
        self.assertEqual(len(list(target.glob('revision-000000-*.json'))), 1)
        self.assertEqual(diagnose(self.root)['revision'], 1)

    def test_all_transaction_paths_are_checked_before_lock_creation(self):
        original_resolve = Path.resolve
        outside = self.root.parent / 'outside-record.json'
        outside.write_text('SYNTHETIC GUARD', encoding='utf-8')
        before = (self.root / 'project_state.json').read_bytes()
        for escaped in ('project_state.json', '.workflow-state.lock', '.project_state-'):
            with self.subTest(escaped=escaped):
                def redirected(path, *args, **kwargs):
                    path = Path(display_path(path))
                    if path.parent == self.root and (path.name == escaped or
                                                    escaped == '.project_state-' and path.name.startswith(escaped)):
                        return outside
                    return original_resolve(path, *args, **kwargs)
                with patch.object(Path, 'resolve', redirected):
                    with self.assertRaisesRegex(ValueError, 'inside the workspace'):
                        commit(self.root, self.state, 0)
                self.assertEqual(before, (self.root / 'project_state.json').read_bytes())
                self.assertEqual(outside.read_text(encoding='utf-8'), 'SYNTHETIC GUARD')
                self.assertFalse((self.root / '.workflow-state.lock').exists())
                self.assertFalse((self.root / 'artifacts/state_history').exists())

    def test_core_record_reads_refuse_resolved_paths_outside_workspace(self):
        original_resolve = Path.resolve
        original_read = Path.read_text
        outside = self.root.parent / 'outside-record.json'
        outside.write_text('{}', encoding='utf-8')
        for escaped in ('project_state.json', 'project.json', 'evidence_ledger.json', 'venue_profile.json'):
            with self.subTest(escaped=escaped):
                def redirected(path, *args, **kwargs):
                    path = Path(display_path(path))
                    if path == self.root / escaped:
                        return outside
                    return original_resolve(path, *args, **kwargs)
                def guarded_read(path, *args, **kwargs):
                    if Path(display_path(path)) == outside:
                        self.fail('Read escaped the workspace boundary')
                    return original_read(path, *args, **kwargs)
                with patch.object(Path, 'resolve', redirected), patch.object(Path, 'read_text', guarded_read):
                    if escaped == 'project_state.json':
                        with self.assertRaisesRegex(ValueError, 'inside the workspace'):
                            diagnose(self.root)
                    elif escaped == 'evidence_ledger.json':
                        with self.assertRaisesRegex(ValueError, 'inside the workspace'):
                            ledger_sources(self.root)
                    report = validate(self.root, 'submission')
                    if escaped != 'project_state.json':
                        self.assertTrue(any(escaped in e and 'inside the workspace' in e
                                            for e in report['errors']), report['errors'])

    def test_legacy_state_initialization_checks_output_boundary(self):
        (self.root / 'project_state.json').unlink()
        original_resolve = Path.resolve
        outside = self.root.parent / 'outside-state.json'
        def redirected(path, *args, **kwargs):
            path = Path(display_path(path))
            return outside if path == self.root / 'project_state.json' else original_resolve(path, *args, **kwargs)
        with patch.object(Path, 'resolve', redirected):
            with self.assertRaisesRegex(ValueError, 'inside the workspace'):
                init_state(self.root)
        self.assertFalse(outside.exists())
        self.assertFalse((self.root / 'project_state.json').exists())


if __name__ == '__main__':
    unittest.main()
