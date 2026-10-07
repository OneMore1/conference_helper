"""Check observable arithmetic, pairing failures, and non-overwriting demo setup."""
import csv
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
from demo_case import CASE, build_demo, summarize_csv


class DemoCaseTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.base = Path(temporary.name)
        self.source = CASE / 'materials/results.csv'

    def mutated(self, mutate):
        with self.source.open(encoding='utf-8', newline='') as handle:
            reader = csv.DictReader(handle)
            fields = reader.fieldnames
            rows = list(reader)
        mutate(rows)
        path = self.base / 'results.csv'
        with path.open('w', encoding='utf-8', newline='') as handle:
            writer = csv.DictWriter(handle, fieldnames=fields)
            writer.writeheader()
            writer.writerows(rows)
        return path

    def test_negative_shift_and_units_are_preserved(self):
        summary = {row['condition']: row for row in summarize_csv(self.source)}
        self.assertEqual([summary[c]['difference_mean_pp'] for c in ('clean', 'noise', 'shift')], [1, 4, -1])
        self.assertEqual(summary['shift']['augmented_mean_pct'], 63)
        self.assertEqual(summary['shift']['augmented_sd_pct'], 2)
        self.assertEqual(summary['shift']['difference_sd_pp'], 1)

    def test_missing_or_duplicate_pair_is_rejected(self):
        for mutate in (lambda rows: rows.pop(), lambda rows: rows.append(rows[0].copy())):
            with self.subTest(mutate=mutate):
                with self.assertRaises(ValueError):
                    summarize_csv(self.mutated(mutate))

    def test_inconsistent_split_or_non_synthetic_input_is_rejected(self):
        for key, value in (('split_id', 'different-split'), ('synthetic', 'false')):
            with self.subTest(key=key):
                with self.assertRaises(ValueError):
                    summarize_csv(self.mutated(lambda rows: rows[0].update({key: value})))

    def test_materialization_and_refusal_to_overwrite(self):
        destination = self.base / 'demo with spaces'
        result = build_demo(destination)
        self.assertFalse(result['agent_run_performed'])
        self.assertEqual((destination / 'materials/results.csv').read_bytes(), self.source.read_bytes())
        table = destination / 'outputs/metric-summary.csv'
        with table.open(encoding='utf-8', newline='') as handle:
            rows = list(csv.DictReader(handle))
        self.assertEqual(rows[-1]['difference_mean_pp'], '-1.00')
        before = table.read_bytes()
        with self.assertRaises(FileExistsError):
            build_demo(destination)
        self.assertEqual(table.read_bytes(), before)

    def test_output_inside_source_repository_is_rejected(self):
        with self.assertRaises(ValueError):
            build_demo(ROOT / 'demo-output-that-must-not-be-created')
