#!/usr/bin/env python3
"""Start the mixer until its window is on screen, then quit (needs a display).

Used by tools/emulate-pc.sh to time the cold start under CPU/memory limits.
Uses the repository sources unless SRCDIR points elsewhere (for example the
installed copy). Never talks to the audio system beyond the read-only snapshot
the application takes by itself, and never changes a setting.
"""

from __future__ import annotations

import os
import sys
import tempfile
from pathlib import Path

SRCDIR = os.environ.get("SRCDIR") or str(
    Path(__file__).resolve().parents[1] / "src/inzone_buds_mixer"
)
sys.path.insert(0, SRCDIR)
os.environ.setdefault("INZONE_LANGUAGE", "en")
os.environ["XDG_CONFIG_HOME"] = tempfile.mkdtemp()  # never touch the real autostart entry

import app  # noqa: E402
from gi.repository import GLib  # noqa: E402

application = app.MixerApplication(start_hidden=False)


def watch() -> bool:
    window = application.window
    if window is None:
        return True
    if window.get_mapped():
        GLib.idle_add(application.quit)
        return False
    return True


GLib.timeout_add(20, watch)
GLib.timeout_add_seconds(120, application.quit)  # safety net on very slow limits
raise SystemExit(application.run([sys.argv[0]]))
