"""Synthetic fixtures only: no experiments, citations or conference rules are verified."""
from __future__ import annotations
import copy
import json
import sys
import tempfile
import unittest
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from init_workspace import initialize
from validate_workspace import validate, file_hash

TODAY = date(2026, 9, 29)

class WorkflowTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.work = Path(self.temp.name) / "paper"
        initialize(self.work, "test-paper")
        self.project = self.load("project.json")
        self.project.update(user_request_verbatim="Synthetic request", research_question="Synthetic question")
        self.save("project.json", self.project)
        self.ledger = self.load("evidence_ledger.json")

    def load(self, name):
        return json.loads((self.work / name).read_text(encoding="utf-8"))

    def save(self, name, data):
        (self.work / name).write_text(json.dumps(data, indent=2), encoding="utf-8")

    def run_check(self, stage="ideation", baseline=None):
        return validate(self.work, stage, baseline, TODAY)

    def evidence(self, kind="local_result", claim_type="empirical", author=False):
        path = self.work / "results" / "synthetic-proof.txt"
        path.write_text("TEST FIXTURE, NOT RESEARCH EVIDENCE", encoding="utf-8")
        source = {"source_id": "S1", "kind": kind,
                  "locator": "results/synthetic-proof.txt" if kind == "local_result" else "author-supplied record #1",
                  "location_detail": "Synthetic fixture, paragraph 1",
                  "verification": "author_confirmed" if author else "read",
                  "checked_on": TODAY.isoformat(),
                  "sha256": file_hash(path) if kind == "local_result" else None}
        claim = {"claim_id": "C1", "text": "Synthetic test assertion only", "claim_type": claim_type,
                 "use_in_manuscript": "reported_result", "status": "author_confirmed" if author else "supported",
                 "evidence_ids": ["S1"], "scope": {}}
        self.ledger = {"schema_version": "0.1", "sources": [source], "claims": [claim]}
        self.save("evidence_ledger.json", self.ledger)

    def submission(self):
        self.evidence()
        self.project["target_venue"] = {"name": "TEST ONLY", "year": 2027, "track": "synthetic"}
        self.save("project.json", self.project)
        venue = self.load("venue_profile.json")
        url = "https://example.invalid/test-policy"
        venue.update(conference="TEST ONLY", year=2027, track="synthetic", checked_on=TODAY.isoformat(),
                     official_sources=[{"url": url, "location_detail": "Synthetic policy fixture", "checked_on": TODAY.isoformat()}],
                     deadlines=[{"name": "Synthetic deadline", "datetime": "2026-10-10T23:59:00-12:00",
                                 "original_text": "Test fixture only", "source_url": url}],
                     manual_preflight_completed=True)
        for check in venue["checks"]:
            check.update(status="pass", detail="Synthetic test-only declaration", evidence="Synthetic fixture", source_url=url)
        path = self.work / "artifacts" / "synthetic-manuscript.txt"
        path.write_text("TEST ONLY; NOT A MANUSCRIPT", encoding="utf-8")
        venue["prepared_artifacts"] = [{"path": "artifacts/synthetic-manuscript.txt", "sha256": file_hash(path)}]
        self.save("venue_profile.json", venue)
        return venue

    def test_minimal_ideation_passes(self):
        self.assertEqual(self.run_check()["errors"], [])

    def test_initialization_refuses_overwrite(self):
        original = (self.work / "project.json").read_bytes()
        with self.assertRaises(FileExistsError):
            initialize(self.work, "different-id")
        self.assertEqual((self.work / "project.json").read_bytes(), original)

    def test_invalid_project_id(self):
        with self.assertRaises(ValueError):
            initialize(Path(self.temp.name) / "new", "../outside")

    def test_missing_question_is_reported(self):
        self.project["research_question"] = ""
        self.save("project.json", self.project)
        self.assertTrue(any("research_question" in e for e in self.run_check()["errors"]))

    def test_malformed_json_is_reported(self):
        (self.work / "evidence_ledger.json").write_text("not json")
        self.assertEqual(self.run_check()["structural_status"], "needs_attention")

    def test_duplicate_source_is_rejected(self):
        self.evidence()
        self.ledger["sources"].append(copy.deepcopy(self.ledger["sources"][0]))
        self.save("evidence_ledger.json", self.ledger)
        self.assertTrue(any("duplicate source" in e for e in self.run_check()["errors"]))

    def test_missing_evidence_id_is_rejected(self):
        self.evidence()
        self.ledger["claims"][0]["evidence_ids"] = ["MISSING"]
        self.save("evidence_ledger.json", self.ledger)
        self.assertTrue(any("unknown evidence" in e for e in self.run_check()["errors"]))

    def test_unread_source_cannot_support_result(self):
        self.evidence()
        self.ledger["sources"][0]["verification"] = "unread"
        self.save("evidence_ledger.json", self.ledger)
        self.assertTrue(any("has not been read" in e for e in self.run_check()["errors"]))

    def test_hypothesis_cannot_be_reported_result(self):
        self.evidence(claim_type="hypothesis")
        self.assertTrue(any("cannot be a reported result" in e for e in self.run_check()["errors"]))

    def test_proposed_cannot_be_reported_result(self):
        self.evidence()
        self.ledger["claims"][0]["status"] = "proposed"
        self.save("evidence_ledger.json", self.ledger)
        self.assertTrue(any("cannot be a reported result" in e for e in self.run_check()["errors"]))

    def test_theory_with_proof_record_is_allowed(self):
        self.evidence(claim_type="theoretical")
        self.assertEqual(self.run_check("writing")["errors"], [])

    def test_author_confirmed_fact_is_not_discarded(self):
        self.evidence(kind="author_statement", author=True)
        self.assertEqual(self.run_check("writing")["errors"], [])
        self.assertEqual(self.run_check()["scientific_verification"], "not_performed")

    def test_missing_local_file_is_rejected(self):
        self.evidence()
        (self.work / "results" / "synthetic-proof.txt").unlink()
        self.assertTrue(any("file not found" in e for e in self.run_check()["errors"]))

    def test_changed_evidence_hash_is_rejected(self):
        self.evidence()
        (self.work / "results" / "synthetic-proof.txt").write_text("CHANGED")
        self.assertTrue(any("SHA-256 mismatch" in e for e in self.run_check()["errors"]))

    def test_path_escape_is_rejected(self):
        self.evidence()
        self.ledger["sources"][0]["locator"] = "../outside.txt"
        self.save("evidence_ledger.json", self.ledger)
        self.assertTrue(any("inside the workspace" in e for e in self.run_check()["errors"]))

    def test_no_search_results_do_not_establish_novelty(self):
        (self.work / "evidence" / "search.md").write_text("No results; synthetic fixture")
        self.project["novelty_assessment"].update(status="differentiated", delta="Synthetic delta", search_log="evidence/search.md")
        self.save("project.json", self.project)
        self.assertTrue(any("zero results" in e for e in self.run_check()["errors"]))

    def test_changed_author_baseline_is_flagged(self):
        baseline = self.work / "author-approved-project.json"
        baseline.write_text(json.dumps(self.project))
        self.project["constraints"]["compute_budget"] = "Changed without recorded reapproval"
        self.save("project.json", self.project)
        self.assertTrue(any("baseline change in constraints" in e for e in self.run_check(baseline=baseline)["errors"]))

    def test_complete_synthetic_submission_records_pass_structure_only(self):
        self.submission()
        report = self.run_check("submission")
        self.assertEqual(report["errors"], [])
        self.assertEqual(report["submission_action"], "not_performed")
        self.assertEqual(report["online_policy_verification"], "not_performed")

    def test_stale_policy_record_is_flagged(self):
        venue = self.submission()
        venue["checked_on"] = "2026-09-01"
        self.save("venue_profile.json", venue)
        self.assertTrue(any("same-day" in e for e in self.run_check("submission")["errors"]))

    def test_timezone_missing_is_rejected(self):
        venue = self.submission()
        venue["deadlines"][0]["datetime"] = "2026-10-10T23:59:00"
        self.save("venue_profile.json", venue)
        self.assertTrue(any("UTC offset" in e for e in self.run_check("submission")["errors"]))

    def test_wrong_venue_year_is_rejected(self):
        venue = self.submission()
        venue["year"] = 2026
        self.save("venue_profile.json", venue)
        self.assertTrue(any("does not match" in e for e in self.run_check("submission")["errors"]))

    def test_preflight_requires_manual_review_record(self):
        venue = self.submission()
        venue["manual_preflight_completed"] = False
        self.save("venue_profile.json", venue)
        self.assertTrue(any("manual_preflight_completed" in e for e in self.run_check("submission")["errors"]))

if __name__ == "__main__":
    unittest.main()
