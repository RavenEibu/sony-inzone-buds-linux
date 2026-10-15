#!/usr/bin/env python3
"""Tests for src/inzone_buds_mixer/i18n.py; no GTK or hardware required."""

from __future__ import annotations

import importlib
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SOURCE_DIR = Path(__file__).resolve().parents[1] / "src/inzone_buds_mixer"
sys.path.insert(0, str(SOURCE_DIR))


def load_i18n(environment: dict[str, str]):
    saved = {key: os.environ.get(key) for key in environment}
    os.environ.update(environment)
    sys.modules.pop("i18n", None)
    try:
        return importlib.import_module("i18n")
    finally:
        for key, value in saved.items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value


class TranslationTests(unittest.TestCase):
    def test_untranslated_strings_are_returned_unchanged(self):
        with tempfile.TemporaryDirectory() as empty:
            i18n = load_i18n({"INZONE_LOCALEDIR": empty, "LANGUAGE": "es"})
            self.assertEqual(i18n.tr("Center"), "Center")

    @unittest.skipUnless(shutil.which("msgfmt"), "msgfmt not installed")
    def test_compiled_catalog_is_used(self):
        with tempfile.TemporaryDirectory() as tmp:
            messages = Path(tmp) / "es/LC_MESSAGES"
            messages.mkdir(parents=True)
            po = Path(tmp) / "es.po"
            po.write_text(
                'msgid ""\nmsgstr ""\n"Content-Type: text/plain; charset=UTF-8\\n"\n\n'
                'msgid "Center"\nmsgstr "Centrar"\n',
                encoding="utf-8",
            )
            subprocess.run(
                ["msgfmt", "-o", str(messages / "inzone-buds-mixer.mo"), str(po)], check=True
            )
            i18n = load_i18n({"INZONE_LOCALEDIR": tmp, "LANGUAGE": "es"})
            self.assertEqual(i18n.tr("Center"), "Centrar")
            self.assertEqual(i18n.tr("Not in the catalog"), "Not in the catalog")


if __name__ == "__main__":
    unittest.main()
