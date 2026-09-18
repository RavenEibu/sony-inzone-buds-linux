#!/usr/bin/env python3
"""Refresh ordering tests for the GTK application; no display or hardware needed.

Skipped when PyGObject or GTK4 is not installed.
"""

from concurrent.futures import Future
from pathlib import Path
import sys
import unittest


PROJECT_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_DIR / "src/inzone_buds_mixer"))

try:
    import app  # noqa: E402
except (ImportError, ValueError) as error:  # ValueError: GTK 4 typelib missing
    app = None
    SKIP_REASON = f"PyGObject/GTK4 unavailable: {error}"
else:
    SKIP_REASON = ""


class ManualExecutor:
    """Queue work so each test decides when every job finishes."""

    def __init__(self) -> None:
        self.jobs: list[tuple[Future, object, tuple]] = []

    def submit(self, function, *arguments):
        future = Future()
        self.jobs.append((future, function, arguments))
        return future

    def finish_next(self) -> None:
        future, function, arguments = self.jobs.pop(0)
        future.set_result(function(*arguments))

    def shutdown(self, **_kwargs) -> None:
        pass


class FakeWindow:
    def __init__(self) -> None:
        self.applied: list[str] = []
        self.pending_edits = False

    def has_pending_edits(self) -> bool:
        return self.pending_edits

    def apply_snapshot(self, snapshot) -> None:
        self.applied.append(snapshot)

    def show_error(self, message: str) -> None:
        raise AssertionError(message)


class FakeBackend:
    def __init__(self) -> None:
        self.state = "old volumes"

    def snapshot(self) -> str:
        return self.state

    def set_balance(self, _position: int, _maximum: int) -> None:
        self.state = "new volumes"


@unittest.skipIf(app is None, SKIP_REASON)
class RefreshOrderingTests(unittest.TestCase):
    def setUp(self):
        # Run idle callbacks immediately instead of on a GLib main loop.
        self._original_idle_add = app.GLib.idle_add
        app.GLib.idle_add = lambda function, *arguments: function(*arguments)
        self.application = app.MixerApplication()
        self.executor = ManualExecutor()
        self.backend = FakeBackend()
        self.window = FakeWindow()
        self.application._executor = self.executor
        self.application.backend = self.backend
        self.application.window = self.window

    def tearDown(self):
        app.GLib.idle_add = self._original_idle_add

    def test_poll_read_before_a_change_does_not_revert_sliders(self):
        self.application.refresh()  # periodic poll, reads the old state
        self.application.run_audio_action(self.backend.set_balance, 80, 60)
        self.executor.finish_next()  # stale snapshot completes first
        self.assertEqual(self.window.applied, [])
        self.executor.finish_next()  # action completes and queues a refresh
        self.executor.finish_next()
        self.assertEqual(self.window.applied, ["new volumes"])

    def test_poll_during_debounce_does_not_revert_sliders(self):
        self.window.pending_edits = True  # slider moved, commit timer pending
        self.application.refresh()
        self.executor.finish_next()
        self.assertEqual(self.window.applied, [])

    def test_change_during_a_refresh_is_read_again(self):
        # A volume key press arrives while an earlier read is still running.
        self.application.refresh()
        self.backend.state = "volume key change"
        self.application.refresh()
        self.assertEqual(len(self.executor.jobs), 1)
        # A real read may have run before the change, so a second one follows.
        self.executor.finish_next()
        self.assertEqual(len(self.executor.jobs), 1)
        self.executor.finish_next()
        self.assertEqual(self.window.applied[-1], "volume key change")
        self.assertEqual(self.executor.jobs, [])

    def test_idle_poll_is_applied(self):
        self.application.refresh()
        self.executor.finish_next()
        self.assertEqual(self.window.applied, ["old volumes"])


if __name__ == "__main__":
    unittest.main()
