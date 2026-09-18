#!/usr/bin/env python3
"""Launch-at-login entry tests; no GTK installation is required."""

from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest


PROJECT_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_DIR / "src/inzone_buds_mixer"))

from autostart import (  # noqa: E402
    autostart_file,
    desktop_entry,
    is_enabled,
    set_enabled,
)


def exec_line(entry: str) -> str:
    return next(line for line in entry.splitlines() if line.startswith("Exec="))


class DesktopEntryTests(unittest.TestCase):
    def test_plain_path_is_not_quoted(self):
        self.assertEqual(
            exec_line(desktop_entry("/home/user/.local/bin/inzone-buds-mixer")),
            "Exec=/home/user/.local/bin/inzone-buds-mixer --hidden",
        )

    def test_reserved_characters_are_quoted_and_escaped(self):
        self.assertEqual(
            exec_line(desktop_entry("/home/my user/bin/inzone-buds-mixer")),
            'Exec="/home/my user/bin/inzone-buds-mixer" --hidden',
        )
        self.assertEqual(
            exec_line(desktop_entry('/opt/a"b$c/mixer')),
            'Exec="/opt/a\\\\"b\\\\$c/mixer" --hidden',
        )
        # A literal backslash needs four backslashes inside quotes.
        self.assertEqual(
            exec_line(desktop_entry("/opt/a\\b/mixer")),
            'Exec="/opt/a\\\\\\\\b/mixer" --hidden',
        )

    def test_percent_is_doubled(self):
        self.assertEqual(
            exec_line(desktop_entry("/opt/100%/mixer")),
            "Exec=/opt/100%%/mixer --hidden",
        )

    @unittest.skipUnless(shutil.which("desktop-file-validate"), "desktop-file-validate missing")
    def test_entry_is_valid(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "io.github.RavenEibu.InzoneBudsMixer.desktop"
            path.write_text(desktop_entry("/home/my user/bin/inzone-buds-mixer"))
            result = subprocess.run(
                ["desktop-file-validate", str(path)], capture_output=True, text=True
            )
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertEqual(result.stdout.strip(), "")


class PreferenceTests(unittest.TestCase):
    def setUp(self):
        self._directory = tempfile.TemporaryDirectory()
        self.path = autostart_file(Path(self._directory.name))

    def tearDown(self):
        self._directory.cleanup()

    def test_enable_and_disable(self):
        self.assertFalse(is_enabled(self.path))
        set_enabled(True, self.path, command="/usr/bin/inzone-buds-mixer")
        self.assertTrue(is_enabled(self.path))
        self.assertIn("Exec=/usr/bin/inzone-buds-mixer --hidden", self.path.read_text())
        set_enabled(False, self.path)
        self.assertFalse(self.path.exists())
        set_enabled(False, self.path)  # disabling twice is harmless

    def test_entry_disabled_by_session_settings(self):
        set_enabled(True, self.path, command="/usr/bin/inzone-buds-mixer")
        for line in ("Hidden=true", "X-GNOME-Autostart-enabled=false"):
            text = desktop_entry("/usr/bin/inzone-buds-mixer").replace(
                "X-GNOME-Autostart-enabled=true", line
            )
            self.path.write_text(text)
            self.assertFalse(is_enabled(self.path), line)


if __name__ == "__main__":
    unittest.main()
