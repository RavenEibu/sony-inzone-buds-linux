#!/usr/bin/env python3
"""Hidden-start and tray fallback tests; no display or hardware needed.

Skipped when PyGObject or GTK4 is not installed, except in CI.
"""

import os
from pathlib import Path
import sys
import unittest


PROJECT_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_DIR / "src/inzone_buds_mixer"))

try:
    import app  # noqa: E402
except (ImportError, ValueError) as error:  # ValueError: GTK 4 typelib missing
    if os.environ.get("INZONE_REQUIRE_GTK_TESTS") == "1":
        raise
    app = None
    SKIP_REASON = f"PyGObject/GTK4 unavailable: {error}"
else:
    SKIP_REASON = ""


class FakeWindow:
    def __init__(self) -> None:
        self.visible = False
        self.presented = 0

    def present(self) -> None:
        self.visible = True
        self.presented += 1

    def get_visible(self) -> bool:
        return self.visible

    def set_tray_available(self, _available: bool) -> None:
        pass


@unittest.skipIf(app is None, SKIP_REASON)
class HiddenStartTests(unittest.TestCase):
    def setUp(self):
        self.application = app.MixerApplication(start_hidden=True)
        self.window = FakeWindow()
        self.application.window = self.window
        self.application._hidden_start_pending = True  # as do_activate sets it

    def test_tray_keeps_the_window_hidden(self):
        self.application._tray_changed(True)
        self.application._finish_hidden_start(False)  # the timeout fires later
        self.assertEqual(self.window.presented, 0)

    def test_window_appears_when_no_tray_arrives(self):
        self.application._finish_hidden_start(False)  # timeout
        self.assertEqual(self.window.presented, 1)

    def test_late_tray_host_is_awaited(self):
        # At login the tray host can appear after the mixer; an early
        # "unavailable" must not show the window before the timeout.
        self.application._tray_changed(False)
        self.assertEqual(self.window.presented, 0)
        self.application._tray_changed(True)
        self.application._finish_hidden_start(False)
        self.assertEqual(self.window.presented, 0)

    def test_window_returns_when_the_tray_disappears(self):
        self.application._tray_changed(True)
        self.application._tray_changed(False)
        self.assertEqual(self.window.presented, 1)

    def test_visible_window_is_not_presented_again(self):
        self.application._finish_hidden_start(False)
        self.application._tray_changed(False)
        self.assertEqual(self.window.presented, 1)


@unittest.skipIf(app is None, SKIP_REASON)
class CommandLineTests(unittest.TestCase):
    def test_hidden_option_is_consumed(self):
        captured = {}

        class Recorder(app.MixerApplication):
            def run(self, arguments):
                captured["arguments"] = arguments
                captured["hidden"] = self.start_hidden
                return 0

        original_argv, original_class = sys.argv, app.MixerApplication
        sys.argv = ["inzone-buds-mixer", "--hidden"]
        app.MixerApplication = Recorder
        try:
            app.main()
        finally:
            sys.argv, app.MixerApplication = original_argv, original_class
        self.assertTrue(captured["hidden"])
        self.assertEqual(captured["arguments"], ["inzone-buds-mixer"])


if __name__ == "__main__":
    unittest.main()
