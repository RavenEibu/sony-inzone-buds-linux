#!/usr/bin/env python3
"""Translation catalogs and language selection; no GTK or hardware required."""

from __future__ import annotations

import importlib
import os
import re
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

PROJECT_DIR = Path(__file__).resolve().parents[1]
SOURCE_DIR = PROJECT_DIR / "src/inzone_buds_mixer"
PO_DIR = PROJECT_DIR / "po"
sys.path.insert(0, str(SOURCE_DIR))

HAVE_MSGFMT = shutil.which("msgfmt") is not None
FIELD = re.compile(r"\{[a-z]+\}")


def read_po(path: Path) -> dict[str, str]:
    """Parse a simple .po file (no plurals/contexts) into {msgid: msgstr}."""
    entries: dict[str, str] = {}
    msgid = msgstr = None
    target = None

    def flush():
        if msgid:
            entries[msgid] = msgstr or ""

    def unquote(line: str) -> str:
        return bytes(line.strip()[1:-1], "utf-8").decode("unicode_escape").encode(
            "latin-1"
        ).decode("utf-8")

    for line in path.read_text(encoding="utf-8").splitlines():
        if line.startswith("msgid "):
            flush()
            msgid, msgstr, target = unquote(line[6:]), None, "id"
        elif line.startswith("msgstr "):
            msgstr, target = unquote(line[7:]), "str"
        elif line.startswith('"'):
            if target == "id":
                msgid += unquote(line)
            elif target == "str":
                msgstr += unquote(line)
    flush()
    return entries


def fresh_i18n(environment: dict[str, str | None]):
    saved = {key: os.environ.get(key) for key in environment}
    for key, value in environment.items():
        if value is None:
            os.environ.pop(key, None)
        else:
            os.environ[key] = value
    sys.modules.pop("i18n", None)
    try:
        return importlib.import_module("i18n")
    finally:
        for key, value in saved.items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value


class CatalogTests(unittest.TestCase):
    def test_every_language_is_complete_and_keeps_placeholders(self):
        template = read_po(PO_DIR / "inzone-buds-mixer.pot")
        template.pop("", None)
        self.assertGreater(len(template), 30)
        languages = sorted(PO_DIR.glob("*.po"))
        self.assertGreaterEqual(len(languages), 10)
        for path in languages:
            entries = read_po(path)
            entries.pop("", None)
            self.assertEqual(set(entries), set(template), f"{path.name}: stale or missing")
            for msgid, msgstr in entries.items():
                self.assertTrue(msgstr, f"{path.name}: empty translation of {msgid!r}")
                self.assertEqual(
                    sorted(FIELD.findall(msgid)),
                    sorted(FIELD.findall(msgstr)),
                    f"{path.name}: placeholders differ in {msgid!r}",
                )

    def test_linguas_lists_every_catalog(self):
        listed = (PO_DIR / "LINGUAS").read_text(encoding="utf-8").split()
        self.assertEqual(sorted(listed), sorted(p.stem for p in PO_DIR.glob("*.po")))

    @unittest.skipUnless(HAVE_MSGFMT, "msgfmt not installed")
    def test_every_catalog_compiles(self):
        with tempfile.TemporaryDirectory() as tmp:
            subprocess.run(
                [str(PROJECT_DIR / "tools/compile-translations.sh"), tmp], check=True
            )
            compiled = {p.parent.parent.name for p in Path(tmp).glob("*/LC_MESSAGES/*.mo")}
            self.assertEqual(compiled, {p.stem for p in PO_DIR.glob("*.po")})


@unittest.skipUnless(HAVE_MSGFMT, "msgfmt not installed")
class LanguageSelectionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        cls.locale_dir = cls.tmp.name
        subprocess.run(
            [str(PROJECT_DIR / "tools/compile-translations.sh"), cls.locale_dir], check=True
        )

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def env(self, **extra):
        base = {
            "XDG_DATA_HOME": self.locale_dir,  # never pick up the user's installed catalogs
            "INZONE_LOCALEDIR": self.locale_dir,
            "INZONE_LANGUAGE": None,
            "INZONE_CONFIG_FILE": "/nonexistent/config",
            "LANGUAGE": None,
            "LC_ALL": None,
            "LC_MESSAGES": None,
            "LANG": "C",
        }
        base.update(extra)
        return base

    def test_system_language_is_used_automatically(self):
        i18n = fresh_i18n(self.env(LANGUAGE="es"))
        self.assertEqual(i18n.tr("Quit"), "Salir")
        i18n = fresh_i18n(self.env(LANGUAGE="de"))
        self.assertEqual(i18n.tr("Quit"), "Beenden")

    def test_regional_variant_falls_back_to_the_language(self):
        i18n = fresh_i18n(self.env(LANGUAGE="fr_CA.UTF-8"))
        self.assertEqual(i18n.tr("Quit"), "Quitter")

    def test_environment_override_beats_the_system_language(self):
        i18n = fresh_i18n(self.env(LANGUAGE="es", INZONE_LANGUAGE="ru"))
        self.assertEqual(i18n.tr("Quit"), "Выход")

    def test_config_file_override(self):
        with tempfile.TemporaryDirectory() as tmp:
            config = Path(tmp) / "config"
            config.write_text(
                '# : "${INZONE_LANGUAGE:=fr}"\n: "${INZONE_LANGUAGE:=pt}"\n', encoding="utf-8"
            )
            i18n = fresh_i18n(self.env(LANGUAGE="es", INZONE_CONFIG_FILE=str(config)))
            self.assertEqual(i18n.tr("Quit"), "Sair")
            # The environment still wins over the config file.
            i18n = fresh_i18n(
                self.env(LANGUAGE="es", INZONE_CONFIG_FILE=str(config), INZONE_LANGUAGE="id")
            )
            self.assertEqual(i18n.tr("Quit"), "Keluar")

    def test_auto_en_and_unknown_languages(self):
        config = self.env(LANGUAGE="es")
        self.assertEqual(fresh_i18n({**config, "INZONE_LANGUAGE": "auto"}).tr("Quit"), "Salir")
        self.assertEqual(fresh_i18n({**config, "INZONE_LANGUAGE": "en"}).tr("Quit"), "Quit")
        self.assertEqual(fresh_i18n({**config, "INZONE_LANGUAGE": "C"}).tr("Quit"), "Quit")
        self.assertEqual(fresh_i18n({**config, "INZONE_LANGUAGE": "tlh"}).tr("Quit"), "Quit")

    def test_explicit_language_sets_the_text_direction(self):
        i18n = fresh_i18n(self.env())

        def direction(language):
            environment = {k: v for k, v in self.env().items() if v is not None}
            if language is not None:
                environment["INZONE_LANGUAGE"] = language
            with mock.patch.dict(os.environ, environment):
                if language is None:
                    os.environ.pop("INZONE_LANGUAGE", None)
                return i18n.explicit_text_direction()

        self.assertIsNone(direction(None))
        for language, expected in (("ar", "rtl"), ("ar_EG.UTF-8", "rtl"), ("he", "rtl"),
                                   ("es", "ltr"), ("en", "ltr"), ("zh_CN", "ltr")):
            self.assertEqual(direction(language), expected, language)
        # "auto" leaves the decision to GTK and the system locale.
        self.assertIsNone(direction("auto"))

    def test_formatted_messages_keep_their_fields(self):
        i18n = fresh_i18n(self.env(INZONE_LANGUAGE="zh_CN"))
        text = i18n.tr("Audio control error: {message}").format(message="boom")
        self.assertIn("boom", text)
        self.assertNotIn("{", text)

    def test_script_mode_translates_for_the_bash_notifications(self):
        environment = {k: v for k, v in os.environ.items() if k not in ("LANGUAGE",)}
        environment.update(INZONE_LOCALEDIR=self.locale_dir, INZONE_LANGUAGE="es")
        result = subprocess.run(
            [sys.executable, str(SOURCE_DIR / "i18n.py"), "Game and Chat are ready."],
            capture_output=True, text=True, env=environment, check=True,
        )
        self.assertEqual(result.stdout.strip(), "Juego y Chat están listos.")

    def test_all_languages_translate_the_notification_texts(self):
        for lang in (p.stem for p in PO_DIR.glob("*.po")):
            i18n = fresh_i18n(self.env(INZONE_LANGUAGE=lang))
            for text in ("INZONE Buds connected", "INZONE Buds disconnected"):
                self.assertNotEqual(i18n.tr(text), text, f"{lang}: {text}")


if __name__ == "__main__":
    unittest.main()
