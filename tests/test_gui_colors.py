#!/usr/bin/env python3
"""Dark/light detection logic of MixerApplication; no display needed.

Skipped when PyGObject/GTK4 is not installed, except in CI.
"""

from __future__ import annotations

import os
import sys
import unittest
from pathlib import Path

PROJECT_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_DIR / "src/inzone_buds_mixer"))
os.environ.setdefault("INZONE_LANGUAGE", "en")

try:
    import app
    from gi.repository import GLib
except (ImportError, ValueError) as error:
    if os.environ.get("INZONE_REQUIRE_GTK_TESTS") == "1":
        raise
    app = None
    SKIP_REASON = f"PyGObject/GTK4 unavailable: {error}"
else:
    SKIP_REASON = ""


class FakeSettings:
    def __init__(self, **properties):
        self.properties = properties

    def find_property(self, name):
        return name in self.properties

    def get_property(self, name):
        return self.properties[name]

    def set_property(self, name, value):
        self.properties[name] = value


class FakeWindow:
    def __init__(self):
        self.classes = set()

    def add_css_class(self, name):
        self.classes.add(name)

    def remove_css_class(self, name):
        self.classes.discard(name)


def make_application(portal=None, settings=None, window=None):
    instance = app.MixerApplication.__new__(app.MixerApplication)  # no GApplication setup
    instance._portal_color_scheme = portal
    instance._gtk_settings = settings
    instance._applying_color_scheme = False
    instance.window = window
    return instance


@unittest.skipIf(app is None, SKIP_REASON)
class DarkModeDetectionTests(unittest.TestCase):
    def test_portal_value_wins(self):
        # 1 = dark, 2 = light, 0 = no preference (GNOME's light mode).
        stale = FakeSettings(**{"gtk-application-prefer-dark-theme": True})
        self.assertTrue(make_application(1, stale)._detect_dark_mode())
        self.assertFalse(make_application(2, stale)._detect_dark_mode())
        self.assertFalse(make_application(0, stale)._detect_dark_mode())

    def test_without_settings_it_is_light(self):
        self.assertFalse(make_application(None, None)._detect_dark_mode())

    def test_gtk_interface_color_scheme(self):
        dark = FakeSettings(**{"gtk-interface-color-scheme": 2})
        light = FakeSettings(**{"gtk-interface-color-scheme": 3, "gtk-theme-name": "Adwaita-dark"})
        self.assertTrue(make_application(None, dark)._detect_dark_mode())
        self.assertFalse(make_application(None, light)._detect_dark_mode())

    def test_theme_name_and_dark_preference_fallbacks(self):
        named = FakeSettings(**{"gtk-interface-color-scheme": 0, "gtk-theme-name": "Some-Dark"})
        self.assertTrue(make_application(None, named)._detect_dark_mode())
        preferred = FakeSettings(
            **{"gtk-theme-name": "Plain", "gtk-application-prefer-dark-theme": True}
        )
        self.assertTrue(make_application(None, preferred)._detect_dark_mode())
        plain = FakeSettings(**{"gtk-theme-name": "Plain"})
        self.assertFalse(make_application(None, plain)._detect_dark_mode())


@unittest.skipIf(app is None, SKIP_REASON)
class ApplyColorSchemeTests(unittest.TestCase):
    def test_css_class_follows_the_detected_scheme(self):
        window = FakeWindow()
        application = make_application(1, None, window)
        application._apply_detected_color_scheme()
        self.assertEqual(window.classes, {"inzone-dark"})
        application._portal_color_scheme = 2
        application._apply_detected_color_scheme()
        self.assertEqual(window.classes, {"inzone-light"})
        self.assertFalse(application._applying_color_scheme)

    def test_portal_syncs_a_stale_dark_preference(self):
        settings = FakeSettings(**{"gtk-application-prefer-dark-theme": True})
        make_application(2, settings, FakeWindow())._apply_detected_color_scheme()
        self.assertFalse(settings.properties["gtk-application-prefer-dark-theme"])

    def test_it_never_forces_dark_from_the_gtk_fallback(self):
        settings = FakeSettings(
            **{"gtk-application-prefer-dark-theme": False, "gtk-theme-name": "X-dark"}
        )
        make_application(None, settings, FakeWindow())._apply_detected_color_scheme()
        self.assertFalse(settings.properties["gtk-application-prefer-dark-theme"])

    def test_reentrant_calls_are_ignored(self):
        window = FakeWindow()
        application = make_application(1, None, window)
        application._applying_color_scheme = True
        application._apply_detected_color_scheme()
        self.assertEqual(window.classes, set())


@unittest.skipIf(app is None, SKIP_REASON)
class PortalValueTests(unittest.TestCase):
    def test_nested_variants_are_unwrapped(self):
        inner = GLib.Variant("u", 1)
        wrapped = GLib.Variant("v", GLib.Variant("v", inner))
        self.assertEqual(app.MixerApplication._unpack_portal_value(wrapped), 1)
        self.assertEqual(app.MixerApplication._unpack_portal_value(inner), 1)


if __name__ == "__main__":
    unittest.main()
