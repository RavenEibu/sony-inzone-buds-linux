#!/usr/bin/env python3
"""Static checks for GTK/SNI metadata that do not require a graphical session."""

import ast
from pathlib import Path
import unittest
import xml.etree.ElementTree as ET


PROJECT_DIR = Path(__file__).resolve().parents[1]


def assigned_string(path: Path, variable: str) -> str:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    for node in tree.body:
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id == variable:
                    return ast.literal_eval(node.value)
    raise AssertionError(f"{variable} was not found in {path}")


class DesktopIntegrationTests(unittest.TestCase):
    def test_dbus_interfaces_are_valid_xml(self):
        tray_source = PROJECT_DIR / "src/inzone_buds_mixer/tray.py"
        for variable in ("SNI_XML", "DBUSMENU_XML"):
            ET.fromstring(assigned_string(tray_source, variable))

    def test_context_menu_exposes_requested_actions(self):
        source = (PROJECT_DIR / "src/inzone_buds_mixer/tray.py").read_text(
            encoding="utf-8"
        )
        self.assertIn('GLib.Variant("s", "Show Window")', source)
        self.assertIn('GLib.Variant("s", "Quit")', source)
        self.assertIn('MENU_PATH = "/MenuBar"', source)

    def test_color_scheme_uses_portal_without_overriding_gtk(self):
        source = (PROJECT_DIR / "src/inzone_buds_mixer/app.py").read_text(
            encoding="utf-8"
        )
        self.assertIn('gi.require_version("Gdk", "4.0")', source)
        self.assertIn(
            'PORTAL_SETTINGS_INTERFACE = "org.freedesktop.portal.Settings"',
            source,
        )
        self.assertIn("self._portal_color_scheme in (0, 1, 2)", source)
        self.assertNotIn("self._gtk_settings.set_property(", source)

    def test_application_metadata_and_icons_are_valid_xml(self):
        paths = [
            PROJECT_DIR
            / "data/metainfo/io.github.RavenEibu.InzoneBudsMixer.metainfo.xml",
            PROJECT_DIR
            / "data/icons/hicolor/scalable/apps/io.github.RavenEibu.InzoneBudsMixer.svg",
            PROJECT_DIR
            / "data/icons/hicolor/symbolic/apps/io.github.RavenEibu.InzoneBudsMixer-symbolic.svg",
        ]
        for path in paths:
            ET.parse(path)


if __name__ == "__main__":
    unittest.main()
