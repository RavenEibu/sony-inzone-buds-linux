#!/usr/bin/env python3
"""Build the mixer window in one language and report its size (needs a display).

Usage: gui_layout_probe.py LANGUAGE [PNG_PATH]
Prints one JSON object: {"width", "height", "direction"}. Run by
tests/test_gui_layouts.py in a separate process because the language is fixed
when the i18n module is imported.
"""

from __future__ import annotations

import json
import os
import sys
import tempfile
from pathlib import Path

PROJECT_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_DIR / "src/inzone_buds_mixer"))
os.environ["INZONE_LANGUAGE"] = sys.argv[1]
os.environ.setdefault("GSK_RENDERER", "cairo")
os.environ["XDG_CONFIG_HOME"] = tempfile.mkdtemp()

import app  # noqa: E402
from audio import AudioSnapshot  # noqa: E402
from gi.repository import GLib, Gtk  # noqa: E402


class FakeApplication(Gtk.Application):
    tray_available = True

    def __init__(self):
        super().__init__(application_id="io.github.RavenEibu.InzoneBudsMixerProbe")

    def refresh(self):
        pass

    def run_audio_action(self, operation, *arguments):
        pass


class FakeBackend:
    pass


def main() -> int:
    app.apply_language_direction()
    if not Gtk.init_check():
        print("no display", file=sys.stderr)
        return 3
    window = app.MixerWindow(FakeApplication(), FakeBackend())
    window.apply_snapshot(
        AudioSnapshot(True, "g", "c", "m", 70, 30, 90, "g", "m")
    )
    window.set_tray_available(True)
    window.present()
    context = GLib.MainContext.default()
    for _ in range(80):
        context.iteration(False)
    width, height = window.get_width(), window.get_height()
    if len(sys.argv) > 2:
        paintable = Gtk.WidgetPaintable.new(window)
        snapshot = Gtk.Snapshot()
        paintable.snapshot(snapshot, width, height)
        texture = window.get_native().get_renderer().render_texture(snapshot.to_node(), None)
        texture.save_to_png(sys.argv[2])
    print(json.dumps({"width": width, "height": height, "direction": int(window.get_direction())}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
