#!/usr/bin/env python3
"""Tray menu model tests (the DBusMenu data, not the bus); no display needed.

Skipped when PyGObject is not installed, except in CI.
"""

import os
import sys
import unittest
from pathlib import Path

PROJECT_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_DIR / "src/inzone_buds_mixer"))

try:
    from gi.repository import GLib

    import tray
except (ImportError, ValueError) as error:
    if os.environ.get("INZONE_REQUIRE_GTK_TESTS") == "1":
        raise
    tray = None
    SKIP_REASON = f"PyGObject unavailable: {error}"
else:
    SKIP_REASON = ""

ITEM = tray.StatusNotifierItem if tray else None


@unittest.skipIf(tray is None, SKIP_REASON)
class MenuPropertiesTests(unittest.TestCase):
    def test_root_is_a_submenu(self):
        props = ITEM._all_menu_properties(0)
        self.assertEqual(props["children-display"].get_string(), "submenu")

    def test_labels_and_separator(self):
        labels = {
            item_id: ITEM._all_menu_properties(item_id)["label"].get_string()
            for item_id in (1, 3, 4, 5)
        }
        self.assertEqual(
            labels,
            {1: "Show Window", 3: "Quit", 4: "Center Game/Chat", 5: "Boost Chat 70%"},
        )
        self.assertEqual(ITEM._all_menu_properties(2)["type"].get_string(), "separator")
        self.assertEqual(ITEM._all_menu_properties(99), {})

    def test_requested_properties_are_filtered(self):
        only_label = ITEM._menu_properties(1, ["label"])
        self.assertEqual(list(only_label), ["label"])
        everything = ITEM._menu_properties(1, [])
        self.assertIn("enabled", everything)

    def test_layout_order_matches_the_display_order(self):
        item_id, _props, children = ITEM._menu_layout(0, -1, [])
        self.assertEqual(item_id, 0)
        order = [child.unpack()[0] for child in children]
        self.assertEqual(order, [1, 4, 5, 2, 3])

    def test_layout_without_depth_has_no_children(self):
        self.assertEqual(ITEM._menu_layout(0, 0, [])[2], [])
        self.assertEqual(ITEM._menu_layout(1, -1, [])[2], [])


@unittest.skipIf(tray is None, SKIP_REASON)
class MenuActivationTests(unittest.TestCase):
    def make_item(self):
        calls = []
        item = ITEM.__new__(ITEM)  # skip the D-Bus setup in __init__
        item.on_activate = lambda: calls.append("show")
        item.on_quit = lambda: calls.append("quit")
        item.on_center = lambda: calls.append("center")
        item.on_boost_chat = lambda: calls.append("boost")
        return item, calls

    def run_idle(self):
        context = GLib.MainContext.default()
        while context.iteration(False):
            pass

    def test_each_item_triggers_its_callback(self):
        item, calls = self.make_item()
        for item_id in (1, 3, 4, 5):
            item._activate_menu_item(item_id, "clicked")
        self.run_idle()
        self.assertEqual(sorted(calls), ["boost", "center", "quit", "show"])

    def test_other_events_and_separator_do_nothing(self):
        item, calls = self.make_item()
        item._activate_menu_item(1, "hovered")
        item._activate_menu_item(2, "clicked")
        self.run_idle()
        self.assertEqual(calls, [])

    def test_missing_optional_callbacks_are_ignored(self):
        item, calls = self.make_item()
        item.on_center = None
        item.on_boost_chat = None
        item._activate_menu_item(4, "clicked")
        item._activate_menu_item(5, "clicked")
        self.run_idle()
        self.assertEqual(calls, [])


if __name__ == "__main__":
    unittest.main()
