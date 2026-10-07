"""Routing and evidence-refresh tests. All assessments are synthetic fixtures."""
from __future__ import annotations
import json
import sys
import tempfile
import unittest
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'scripts'))
from init_workspace import initialize
from workflow_state import diagnose
from workflow import render_card

class StageRefreshTests(unittest.TestCase):
    def setUp(self):
        t = tempfile.TemporaryDirectory(); self.addCleanup(t.cleanup)
        self.root = Path(t.name); initialize(self.root, 'synthetic-regression')
        self.state = json.loads((self.root/'project_state.json').read_text(encoding='utf-8'))
        self.stream = self.state['workstreams']['main']; self.a = self.stream['assessments']

    def mark(self, key, status='complete'):
        self.a[key].update(status=status, evidence=['author:synthetic fixture'], note='Synthetic fixture only')

    def route(self, requested=None):
        (self.root/'project_state.json').write_text(json.dumps(self.state),encoding='utf-8')
        return diagnose(self.root, requested)

    def test_question_refresh_routes_topic(self):
        self.mark('manuscript'); self.mark('research_question', 'needs_refresh')
        self.assertEqual(self.route()['recommended_stage'], 'topic')

    def test_literature_refresh_routes_topic_without_invalidating_all_results(self):
        self.mark('manuscript'); self.mark('literature_grounding', 'needs_refresh')
        r = self.route(); self.assertEqual(r['recommended_stage'], 'topic')
        self.assertNotIn('experiments', r['stale_fields'])

    def test_explicit_writing_wins_over_literature_refresh(self):
        self.mark('literature_grounding','needs_refresh')
        r = self.route('writing')
        self.assertEqual(r['active_stage'],'writing'); self.assertEqual(r['recommended_stage'],'topic')

    def test_completed_section_routes_writing(self):
        self.mark('manuscript'); self.a['manuscript']['scope']='section'
        self.assertEqual(self.route()['recommended_stage'], 'writing')

    def test_review_of_section_does_not_enable_submission(self):
        self.mark('manuscript'); self.mark('internal_review'); self.a['internal_review']['scope']='section'
        self.assertEqual(self.route()['recommended_stage'], 'review')

    def test_invalid_scope_rejected(self):
        self.a['manuscript']['scope']='finished-everything'
        self.assertEqual(self.route()['status'],'invalid_state')

    def test_list_scope_rejected(self):
        self.a['manuscript']['scope']=[]
        self.assertEqual(self.route()['status'],'invalid_state')

    def test_list_status_rejected(self):
        self.a['manuscript']['status']=[]
        self.assertEqual(self.route()['status'],'invalid_state')

    def test_legacy_scope_is_compatible(self):
        self.mark('manuscript'); self.a['manuscript'].pop('scope',None)
        self.assertEqual(self.route()['recommended_stage'],'review')

    def test_unknown_source_rejected(self):
        self.mark('manuscript'); self.a['manuscript']['evidence']=['source:UNKNOWN']
        self.assertEqual(self.route()['status'],'invalid_state')

    def test_known_source_resolves(self):
        self.mark('manuscript'); self.a['manuscript']['evidence']=['source:SRC1']
        (self.root/'evidence_ledger.json').write_text(json.dumps({'sources':[{'source_id':'SRC1'}],'claims':[]}),encoding='utf-8')
        self.assertEqual(self.route()['status'],'routed')

    def test_missing_ledger_rejected_when_referenced(self):
        self.mark('manuscript'); self.a['manuscript']['evidence']=['source:SRC1']
        (self.root/'evidence_ledger.json').unlink()
        self.assertEqual(self.route()['status'],'invalid_state')

    def test_receipt_warns_against_resubmission(self):
        self.mark('submission_receipt')
        r = self.route(); self.assertTrue(any('do not resubmit' in s for s in r['warnings']))
        self.assertFalse(r['external_actions_performed'])

    def test_stage_card_is_six_lines(self):
        self.assertEqual(len(render_card(self.route()).splitlines()),6)

    def test_full_manuscript_and_review_prepare_only(self):
        self.mark('manuscript'); self.mark('internal_review')
        r = self.route(); self.assertEqual(r['active_stage'],'submission')
        self.assertFalse(r['assessment_truth_verified_by_script'])
