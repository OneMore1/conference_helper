"""A concise card must retain actionable diagnostics from the routing report."""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'skills/conference-helper/scripts'))
from workflow import render_card


class StatusCardTests(unittest.TestCase):
    def test_evidence_warning_is_visible_without_breaking_card(self):
        report = {'status': 'routed', 'observed_stage': 'writing',
                  'recommended_stage': 'analysis', 'active_stage': 'writing',
                  'workstream': 'main', 'blockers': [], 'stale_fields': ['result_analysis'],
                  'warnings': ['S1: SHA-256 mismatch;\nre-read the source',
                               'Historical submission receipt recorded; do not resubmit.']}
        card = render_card(report)
        self.assertEqual(len(card.splitlines()), 6)
        self.assertIn('S1: SHA-256 mismatch', card)
        self.assertIn('do not resubmit', card)
        self.assertIn('writing', card)
