"""Synthetic routing tests; not evidence of scientific assessment quality."""
from __future__ import annotations
import copy
import hashlib
import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
from init_workspace import initialize
from workflow_state import diagnose, commit, init_state, validate_state, digest

class StateRouterTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(); self.addCleanup(self.tmp.cleanup)
        self.work = Path(self.tmp.name) / 'project'
        initialize(self.work, 'synthetic-test')
        self.state = json.loads((self.work / 'project_state.json').read_text())
        self.stream = self.state['workstreams']['main']

    def save(self):
        (self.work / 'project_state.json').write_text(json.dumps(self.state), encoding='utf-8')

    def mark(self, field, status='complete', note='Synthetic assessment, not research evidence'):
        self.stream['assessments'][field].update(status=status, note=note,
            evidence=['author:synthetic test fixture, statement 1'], assessed_by='author', confidence='high')

    def route(self, requested=None, workstream=None):
        self.save(); return diagnose(self.work, requested, workstream)

    def test_empty_state_routes_intake(self):
        self.assertEqual(self.route()['active_stage'], 'intake')

    def test_question_in_progress_routes_topic(self):
        self.mark('research_question', 'in_progress')
        self.assertEqual(self.route()['active_stage'], 'topic')

    def test_specific_question_routes_ideation(self):
        self.mark('research_question')
        self.assertEqual(self.route()['active_stage'], 'ideation')

    def test_concept_routes_design(self):
        self.mark('concept')
        self.assertEqual(self.route()['active_stage'], 'design')

    def test_plan_routes_execution(self):
        self.mark('experiment_plan')
        self.assertEqual(self.route()['active_stage'], 'execution')

    def test_partial_results_route_analysis(self):
        self.mark('experiments', 'in_progress')
        self.assertEqual(self.route()['active_stage'], 'analysis')

    def test_existing_manuscript_does_not_hide_unanalyzed_results(self):
        self.mark('manuscript'); self.mark('experiments')
        report = self.route()
        self.assertEqual(report['observed_stage'], 'writing')
        self.assertEqual(report['recommended_stage'], 'analysis')

    def test_draft_alone_routes_review_not_topic_restart(self):
        self.mark('manuscript')
        self.assertEqual(self.route()['recommended_stage'], 'review')

    def test_analysis_followed_by_gap_assessment(self):
        self.mark('result_analysis')
        self.assertEqual(self.route()['recommended_stage'], 'supplement')

    def test_analysis_and_resolved_gaps_route_writing(self):
        self.mark('result_analysis'); self.mark('evidence_gaps')
        self.assertEqual(self.route()['recommended_stage'], 'writing')

    def test_blocking_gap_prevents_ready_looking_draft(self):
        self.mark('manuscript'); self.mark('internal_review')
        self.stream['gaps'] = [{'id':'G1','reason':'synthetic missing comparison',
                               'priority':'blocking','status':'open'}]
        self.assertEqual(self.route()['recommended_stage'], 'supplement')

    def test_deferred_blocking_gap_still_visible(self):
        self.stream['gaps'] = [{'id':'G1','reason':'synthetic missing comparison',
                               'priority':'blocking','status':'deferred'}]
        self.assertEqual(len(self.route()['blockers']), 1)

    def test_optional_gap_does_not_force_more_experiments(self):
        self.mark('result_analysis'); self.mark('evidence_gaps')
        self.stream['gaps'] = [{'id':'G1','reason':'synthetic optional extension',
                               'priority':'optional','status':'open'}]
        self.assertEqual(self.route()['recommended_stage'], 'writing')

    def test_explicit_writing_task_is_preserved(self):
        self.mark('experiments')
        report=self.route('writing')
        self.assertEqual(report['active_stage'], 'writing')
        self.assertEqual(report['recommended_stage'], 'analysis')

    def test_reviewed_manuscript_routes_submission_preparation_only(self):
        self.mark('manuscript'); self.mark('internal_review')
        r=self.route(); self.assertEqual(r['active_stage'], 'submission')
        self.assertFalse(r['external_actions_performed'])
        self.assertIn('not submission', r['submission_action'])

    def test_explicit_rebuttal(self):
        self.assertEqual(self.route('rebuttal')['active_stage'], 'rebuttal')

    def test_complete_without_source_fails(self):
        self.stream['assessments']['manuscript']['status']='complete'
        self.assertEqual(self.route()['status'], 'invalid_state')

    def test_not_applicable_requires_reason(self):
        self.stream['assessments']['experiments']['status']='not_applicable'
        self.assertEqual(self.route()['status'], 'invalid_state')

    def test_theory_can_skip_experimental_dimension(self):
        self.stream['assessments']['experiments'].update(status='not_applicable', note='Proof-based contribution')
        self.mark('result_analysis'); self.mark('evidence_gaps')
        self.assertEqual(self.route()['active_stage'], 'writing')

    def test_file_presence_alone_does_not_mark_stage_complete(self):
        path=self.work/'manuscript'/'paper.pdf'; path.write_text('synthetic file, not PDF')
        self.stream['artifacts']=[{'id':'PAPER','path':'manuscript/paper.pdf','sha256':digest(path)}]
        self.assertEqual(self.route()['active_stage'], 'intake')

    def test_changed_evidence_invalidates_dependents(self):
        path=self.work/'results'/'r.txt'; path.write_text('TEST ONLY')
        self.stream['artifacts']=[{'id':'R1','path':'results/r.txt','sha256':digest(path)}]
        self.mark('experiments'); self.mark('result_analysis'); self.mark('manuscript')
        self.stream['assessments']['result_analysis']['evidence']=['artifact:R1']
        path.write_text('CHANGED TEST INPUT')
        r=self.route()
        self.assertEqual(r['recommended_stage'], 'analysis')
        self.assertIn('manuscript', r['stale_fields'])
        self.assertNotIn('research_question', r['stale_fields'])

    def test_explicit_invalidation_scope(self):
        self.mark('manuscript')
        self.stream['invalidations']=[{'reason':'synthetic new analysis version',
                     'affected_fields':['result_analysis'],'status':'open'}]
        self.assertEqual(self.route()['recommended_stage'], 'analysis')

    def test_path_escape_rejected(self):
        self.stream['artifacts']=[{'id':'R1','path':'../outside.txt'}]
        self.assertEqual(self.route()['status'], 'invalid_state')

    def test_unknown_artifact_reference_rejected(self):
        self.mark('manuscript')
        self.stream['assessments']['manuscript']['evidence']=['artifact:MISSING']
        self.assertEqual(self.route()['status'], 'invalid_state')

    def test_workstream_isolation(self):
        self.state['workstreams']['second']=copy.deepcopy(self.stream)
        self.mark('experiments')
        self.assertEqual(self.route(workstream='main')['active_stage'], 'analysis')
        self.assertEqual(self.route(workstream='second')['active_stage'], 'intake')

    def test_commit_increments_revision_preserves_history(self):
        self.mark('research_question')
        result=commit(self.work,self.state,0)
        self.assertEqual(result['revision'],1)
        self.assertEqual(len(list((self.work/'artifacts/state_history').glob('*.json'))),1)

    def test_stale_update_refused_without_overwrite(self):
        commit(self.work,self.state,0)
        before=(self.work/'project_state.json').read_bytes()
        with self.assertRaises(ValueError): commit(self.work,self.state,0)
        self.assertEqual(before,(self.work/'project_state.json').read_bytes())
        self.assertFalse((self.work/'.workflow-state.lock').exists())

    def test_diagnosis_has_no_write_side_effect(self):
        self.save(); before=(self.work/'project_state.json').read_bytes()
        diagnose(self.work)
        self.assertEqual(before,(self.work/'project_state.json').read_bytes())

    def test_migration_does_not_overwrite_existing_state(self):
        with self.assertRaises(FileExistsError): init_state(self.work)

    def test_migration_does_not_infer_progress_from_legacy_stage(self):
        (self.work/'project_state.json').unlink()
        p=json.loads((self.work/'project.json').read_text()); p['stage']='submission'
        (self.work/'project.json').write_text(json.dumps(p))
        init_state(self.work)
        self.assertEqual(diagnose(self.work)['active_stage'],'intake')

    def test_workstream_cannot_be_silently_removed(self):
        self.state['workstreams']['second']=copy.deepcopy(self.stream)
        self.save(); del self.state['workstreams']['second']
        with self.assertRaises(ValueError): commit(self.work,self.state,0)

if __name__=='__main__': unittest.main()
