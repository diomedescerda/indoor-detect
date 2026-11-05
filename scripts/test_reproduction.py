"""Check that the reproduction verifier detects altered evidence and preserves outputs."""
import csv
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from reproduce import compare_csv


class ReproductionChecks(unittest.TestCase):
    def test_changed_count_and_missing_row_are_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            expected=Path(temp)/'expected.csv';actual=Path(temp)/'actual.csv'
            expected.write_text('mount,tp,f1\nchest,65,0.6190476190476191\n')
            for modified in ('mount,tp,f1\nchest,66,0.6190476190476191\n', 'mount,tp,f1\n'):
                actual.write_text(modified)
                with self.assertRaises(ValueError):compare_csv(actual,expected)

    def test_float_rounding_allowed_but_text_changes_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            expected=Path(temp)/'expected.csv';actual=Path(temp)/'actual.csv'
            expected.write_text('mount,f1\nchest,0.6190476190476191\n')
            actual.write_text('mount,f1\nchest,0.6190476190476192\n')
            self.assertEqual(compare_csv(actual,expected)['rows'],1)
            actual.write_text('mount,f1\nhead,0.6190476190476191\n')
            with self.assertRaises(ValueError):compare_csv(actual,expected)

    def test_existing_output_is_untouched(self):
        with tempfile.TemporaryDirectory() as temp:
            sentinel=Path(temp)/'sentinel';sentinel.write_text('keep')
            result=subprocess.run([sys.executable,str(Path(__file__).with_name('reproduce.py')),'--output',temp],capture_output=True,text=True)
            self.assertNotEqual(result.returncode,0)
            self.assertIn('Output already exists',result.stderr)
            self.assertEqual(sentinel.read_text(),'keep')
            self.assertEqual(list(Path(temp).iterdir()),[sentinel])


if __name__=='__main__':unittest.main()
