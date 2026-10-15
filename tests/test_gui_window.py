#!/usr/bin/env python3
"""MixerWindow behavior with a fake backend; needs a display.

Skipped when PyGObject/GTK4 or a display is unavailable, except where
INZONE_REQUIRE_DISPLAY_TESTS=1 (CI runs this file under xvfb-run).
"""

from __future__ import annotations

import os
import sys
import tempfile
import unittest
from pathlib import Path

PROJECT_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_DIR / "src/inzone_buds_mixer"))

# Never touch the real launch-at-login entry.
_CONFIG_HOME = tempfile.mkdtemp()
os.environ["XDG_CONFIG_HOME"] = _CONFIG_HOME
os.environ.setdefault("INZONE_LANGUAGE", "en")
os.environ.setdefault("GSK_RENDERER", "cairo")

REQUIRED = os.environ.get("INZONE_REQUIRE_DISPLAY_TESTS") == "1"

try:
    import app
    from audio import AudioSnapshot
    from gi.repository import Gdk, GLib, Gtk

    Gtk.init_check()
    # init_check() returns a bool or a tuple depending on the PyGObject version.
    HAVE_DISPLAY = Gdk.Display.get_default() is not None
    SKIP_REASON = "" if HAVE_DISPLAY else "no display available"
except (ImportError, ValueError) as error:
    app = None
    HAVE_DISPLAY = False
    SKIP_REASON = f"PyGObject/GTK4 unavailable: {error}"

if REQUIRED and not HAVE_DISPLAY:
    raise SystemExit(f"a display is required: {SKIP_REASON}")


def snapshot(connected=True, game=50, chat=50, mic=80, sink="game", source="mic"):
    return AudioSnapshot(
        connected=connected,
        game="game" if connected else None,
        chat="chat" if connected else None,
        microphone="mic" if connected else None,
        game_volume=game if connected else None,
        chat_volume=chat if connected else None,
        microphone_volume=mic if connected else None,
        default_sink=sink,
        default_source=source,
    )


class FakeBackend:
    def __init__(self):
        self.calls = []

    def set_balance(self, position, maximum):
        self.calls.append(("balance", position, maximum))

    def set_volumes(self, game, chat):
        self.calls.append(("volumes", game, chat))

    def set_microphone_volume(self, volume):
        self.calls.append(("mic", volume))

    def select_defaults(self):
        self.calls.append(("defaults",))


if app is not None:

    class FakeApplication(Gtk.Application):
        def __init__(self):
            super().__init__(application_id="io.github.RavenEibu.InzoneBudsMixerTest")
            self.tray_available = False
            self.refreshed = 0
            self.quit_calls = 0

        def refresh(self):
            self.refreshed += 1

        def run_audio_action(self, operation, *arguments):
            operation(*arguments)

        def quit(self):
            self.quit_calls += 1


@unittest.skipIf(app is None or not HAVE_DISPLAY, SKIP_REASON)
class WindowTests(unittest.TestCase):
    def setUp(self):
        self.application = FakeApplication()
        self.backend = FakeBackend()
        self.window = app.MixerWindow(self.application, self.backend)

    def tearDown(self):
        self.window.destroy()

    def test_connected_snapshot_fills_controls_and_enables_them(self):
        self.window.apply_snapshot(snapshot(game=40, chat=20, mic=90))
        window = self.window
        self.assertEqual(window.overall_scale.get_value(), 40)
        self.assertEqual(window.mic_scale.get_value(), 90)
        self.assertEqual(window.overall_value.get_label(), "40%")
        self.assertEqual(window.mic_value.get_label(), "90%")
        self.assertIn("connected", window.status.get_label())
        self.assertTrue(window.center_button.get_sensitive())
        self.assertTrue(window.defaults_button.get_sensitive())
        self.assertIn("Game 40%", window.endpoint_status.get_label())
        self.assertIn("Chat 20%", window.endpoint_status.get_label())
        self.assertIn("Default output: Game", window.endpoint_status.get_label())

    def test_disconnected_snapshot_disables_controls(self):
        self.window.apply_snapshot(snapshot(connected=False, sink="other", source="other"))
        self.assertFalse(self.window.center_button.get_sensitive())
        self.assertFalse(self.window.boost_chat_button.get_sensitive())
        self.assertIn("unavailable", self.window.status.get_label())
        self.assertIn("another device", self.window.endpoint_status.get_label())

    def test_unknown_volumes_show_a_dash(self):
        self.window.apply_snapshot(snapshot(game=None, chat=None))
        self.assertIn("Game —%", self.window.endpoint_status.get_label())

    def test_error_and_recovery_css_classes(self):
        self.window.show_error("boom")
        self.assertIn("boom", self.window.status.get_label())
        self.assertTrue(self.window.status.has_css_class("error"))
        self.window.apply_snapshot(snapshot())
        self.assertFalse(self.window.status.has_css_class("error"))

    def test_tray_status_text(self):
        self.window.set_tray_available(True)
        self.assertIn("active", self.window.tray_status.get_label())
        self.window.set_tray_available(False)
        self.assertIn("unavailable", self.window.tray_status.get_label())

    def test_close_hides_only_when_a_tray_exists(self):
        self.assertFalse(self.window._close_requested(self.window))
        self.application.tray_available = True
        self.window.present()
        self.assertTrue(self.window._close_requested(self.window))
        self.assertFalse(self.window.get_visible())

    def test_center_commits_even_when_already_centered(self):
        self.window.apply_snapshot(snapshot(game=100, chat=99))
        self.window.center_balance()
        self.assertEqual(self.backend.calls, [("balance", 50, 100)])

    def test_balance_slider_commits_after_the_debounce(self):
        self.window.apply_snapshot(snapshot(game=50, chat=50))
        self.window.balance_scale.set_value(80)
        self.assertTrue(self.window.has_pending_edits())
        self.assertEqual(self.backend.calls, [])
        self.window._commit_balance()
        self.assertEqual(self.backend.calls, [("balance", 80, 50)])

    def test_microphone_slider_commits_the_value(self):
        self.window.apply_snapshot(snapshot())
        self.window.mic_scale.set_value(35)
        self.window._commit_microphone()
        self.assertEqual(self.backend.calls, [("mic", 35)])

    def test_boost_chat_applies_and_restores(self):
        self.window.apply_snapshot(snapshot(game=60, chat=40))
        self.window.boost_chat_button.set_active(True)
        self.assertEqual(self.backend.calls[-1], ("volumes", 30, 70))
        self.assertFalse(self.window.has_pending_edits())
        self.window.apply_snapshot(snapshot(game=30, chat=70))
        self.window.boost_chat_button.set_active(False)
        self.assertEqual(self.backend.calls[-1], ("volumes", 60, 40))

    def test_select_defaults_button_calls_the_backend(self):
        self.window._select_defaults(None)
        self.assertEqual(self.backend.calls, [("defaults",)])

    def test_autostart_switch_writes_and_removes_the_entry(self):
        entry = Path(_CONFIG_HOME) / "autostart" / f"{app.APP_ID}.desktop"
        self.window._autostart_toggled(Gtk.Switch(active=True), None)
        self.assertTrue(entry.exists())
        self.window._autostart_toggled(Gtk.Switch(active=False), None)
        self.assertFalse(entry.exists())

    def test_window_stays_compact(self):
        self.window.apply_snapshot(snapshot())
        self.window.present()
        context = GLib.MainContext.default()
        for _ in range(50):
            context.iteration(False)
        # Long translations may widen the fixed-size window a little (French
        # is about 553 px); a regression to something much wider is a bug.
        self.assertLessEqual(self.window.get_width(), 600)
        self.assertLessEqual(self.window.get_height(), 760)


if __name__ == "__main__":
    unittest.main()
