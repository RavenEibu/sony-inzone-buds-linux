#!/usr/bin/env python3
"""Tests for tools/inzone-hid-analyze and the capture --changes-only filter."""

from __future__ import annotations

import importlib.util
import subprocess
import sys
import tempfile
import unittest
from importlib.machinery import SourceFileLoader
from pathlib import Path

PROJECT_DIR = Path(__file__).resolve().parents[1]


def load(name: str, relative: str):
    path = PROJECT_DIR / relative
    loader = SourceFileLoader(name, str(path))
    spec = importlib.util.spec_from_file_location(name, path, loader=loader)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


analyze = load("inzone_hid_analyze", "tools/inzone-hid-analyze")
capture = load("inzone_hid_capture_for_analyze", "tools/inzone-hid-capture")

SAMPLE = """\
2026-10-15T18:00:00.000  id=  2  len=  5  02 14 04 50 00
2026-10-15T18:00:01.000  id=  2  len=  5  02 14 04 50 00
2026-10-15T18:00:02.000  id=  2  len=  5  02 14 04 4b 00
2026-10-15T18:00:03.000  id=  7  len=  2  07 01
not a report line
2026-10-15T18:00:04.000  id=  2  len=  9  02 14 04 4b 00 01 02 03 04
"""


class ParseTests(unittest.TestCase):
    def test_skips_noise_and_inconsistent_lines(self):
        records = list(analyze.parse_lines(SAMPLE.splitlines() + ["x  id=  2  len=  9  02 00"]))
        self.assertEqual(len(records), 5)

    def test_find_pattern_returns_following_byte(self):
        hits = list(analyze.find_pattern(bytes([2, 0x14, 4, 0x50]), bytes([0x14, 4])))
        self.assertEqual(hits, [(1, 0x50)])
        end_hit = list(analyze.find_pattern(bytes([0x14, 4]), bytes([0x14, 4])))
        self.assertEqual(end_hit, [(0, None)])


class AnalyzeTests(unittest.TestCase):
    def test_counts_changes_and_hits(self):
        records = list(analyze.parse_lines(SAMPLE.splitlines()))
        counts, offsets, changes, hits = analyze.analyze(records, bytes([0x14, 4]))
        self.assertEqual(counts, {2: 4, 7: 1})
        self.assertEqual(sorted(offsets[2]), [3, 5])
        self.assertEqual(len(changes), 2)
        self.assertEqual(changes[0][2], [(3, 0x50, 0x4B)])
        self.assertEqual([hit[3] for hit in hits], [0x50, 0x50, 0x4B, 0x4B])

    def test_cli_reports_and_rejects_empty_input(self):
        tool = str(PROJECT_DIR / "tools/inzone-hid-analyze")
        with tempfile.TemporaryDirectory() as tmp:
            good = Path(tmp) / "good.log"
            good.write_text(SAMPLE, encoding="utf-8")
            result = subprocess.run(
                [sys.executable, tool, str(good), "--find", "14 04"],
                capture_output=True, text=True, check=False,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("Pattern hits (4)", result.stdout)
            empty = Path(tmp) / "empty.log"
            empty.write_text("nothing\n", encoding="utf-8")
            result = subprocess.run(
                [sys.executable, tool, str(empty)], capture_output=True, text=True, check=False
            )
            self.assertEqual(result.returncode, 1)


class ChangeFilterTests(unittest.TestCase):
    def test_drops_repeats_per_report_id(self):
        change_filter = capture.ChangeFilter()
        self.assertTrue(change_filter.is_new(bytes([2, 1])))
        self.assertFalse(change_filter.is_new(bytes([2, 1])))
        self.assertTrue(change_filter.is_new(bytes([7, 1])))
        self.assertTrue(change_filter.is_new(bytes([2, 2])))
        self.assertTrue(change_filter.is_new(bytes([2, 1])))


if __name__ == "__main__":
    unittest.main()
