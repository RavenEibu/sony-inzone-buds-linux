#!/usr/bin/env python3
"""The mixer window in every shipped language: size limits and text direction.

Needs a display (CI uses xvfb-run). Set INZONE_GALLERY_DIR to also save one PNG
per language, which CI uploads as an artifact for visual review.
Skipped without a display or msgfmt, except with INZONE_REQUIRE_DISPLAY_TESTS=1.
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

PROJECT_DIR = Path(__file__).resolve().parents[1]
PROBE = PROJECT_DIR / "tests/gui_layout_probe.py"
REQUIRED = os.environ.get("INZONE_REQUIRE_DISPLAY_TESTS") == "1"
LANGUAGES = ["en"] + (PROJECT_DIR / "po/LINGUAS").read_text(encoding="utf-8").split()
RTL = {"ar"}


@unittest.skipUnless(shutil.which("msgfmt") or not REQUIRED, "msgfmt not installed")
class LayoutTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        subprocess.run(
            [str(PROJECT_DIR / "tools/compile-translations.sh"), cls.tmp.name], check=True
        )
        cls.gallery = os.environ.get("INZONE_GALLERY_DIR")
        if cls.gallery:
            Path(cls.gallery).mkdir(parents=True, exist_ok=True)

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def probe(self, language: str) -> dict:
        command = [sys.executable, str(PROBE), language]
        if self.gallery:
            command.append(str(Path(self.gallery) / f"mixer-{language}.png"))
        environment = {
            **os.environ,
            "INZONE_LOCALEDIR": self.tmp.name,
            "XDG_DATA_HOME": self.tmp.name,
        }
        result = subprocess.run(
            command, capture_output=True, text=True, env=environment, check=False
        )
        if result.returncode == 3 and not REQUIRED:
            self.skipTest("no display available")
        self.assertEqual(result.returncode, 0, result.stderr[-500:])
        return json.loads(result.stdout.strip().splitlines()[-1])

    def test_every_language_fits_and_has_the_right_direction(self):
        for language in LANGUAGES:
            with self.subTest(language=language):
                info = self.probe(language)
                # Long translations may widen the window a little (French is
                # about 553 px, Hindi about 709 px tall); much more is a bug.
                self.assertLessEqual(info["width"], 600, info)
                self.assertLessEqual(info["height"], 760, info)
                self.assertEqual(info["direction"], 2 if language in RTL else 1, info)


if __name__ == "__main__":
    unittest.main()
