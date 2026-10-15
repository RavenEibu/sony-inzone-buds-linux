#!/usr/bin/env python3
"""Validate config/wireplumber/51-inzone-buds.conf with PipeWire's own parser.

Uses ``spa-json-dump`` (shipped with PipeWire) to parse the SPA-JSON file, then
checks the structure and that the rules match the node names the dongle
produces. Skipped when spa-json-dump is missing, except when
INZONE_REQUIRE_SPA_JSON=1 (set in the dedicated CI job).
"""

from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import unittest
from pathlib import Path

CONFIG = Path(__file__).resolve().parents[1] / "config/wireplumber/51-inzone-buds.conf"
SPA_JSON_DUMP = shutil.which("spa-json-dump")

if SPA_JSON_DUMP is None and os.environ.get("INZONE_REQUIRE_SPA_JSON") == "1":
    raise SystemExit("spa-json-dump is required but not installed")


def matches(pattern: str, value: str) -> bool:
    """WirePlumber string match: '~' prefix means regex (unanchored), else exact."""
    if pattern.startswith("~"):
        return re.search(pattern[1:], value) is not None
    return pattern == value


@unittest.skipUnless(SPA_JSON_DUMP, "spa-json-dump not installed")
class WirePlumberConfigTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        result = subprocess.run(
            [SPA_JSON_DUMP, str(CONFIG)], capture_output=True, text=True, check=False
        )
        if result.returncode != 0:
            raise AssertionError(f"spa-json-dump failed: {result.stderr}")
        cls.config = json.loads(result.stdout)

    def test_has_both_rule_sections(self):
        self.assertIn("device.profile.priority.rules", self.config)
        self.assertIn("monitor.alsa.rules", self.config)

    def test_every_rule_has_matches_and_actions(self):
        for section in ("device.profile.priority.rules", "monitor.alsa.rules"):
            for rule in self.config[section]:
                self.assertTrue(rule["matches"], section)
                self.assertIn("update-props", rule["actions"], section)

    def test_profile_rule_targets_pc_mode_and_prefers_pro_audio(self):
        (rule,) = self.config["device.profile.priority.rules"]
        (match,) = rule["matches"]
        self.assertEqual(match["device.vendor.id"], "0x054c")
        self.assertEqual(match["device.product.id"], "0x0ec2")
        self.assertEqual(rule["actions"]["update-props"]["priorities"], ["pro-audio"])

    def test_node_rules_match_real_node_names_only_once_each(self):
        nodes = {
            "alsa_output.usb-Sony_INZONE_Buds-00.pro-output-0": "INZONE Chat",
            "alsa_output.usb-Sony_INZONE_Buds-00.pro-output-1": "INZONE Game",
            "alsa_input.usb-Sony_INZONE_Buds-00.pro-input-0": "INZONE Microphone",
        }
        for node_name, nick in nodes.items():
            hits = []
            for rule in self.config["monitor.alsa.rules"]:
                for match in rule["matches"]:
                    if matches(match["alsa.components"], "USB054c:0ec2") and matches(
                        match["node.name"], node_name
                    ):
                        hits.append(rule["actions"]["update-props"])
            self.assertEqual(len(hits), 1, node_name)
            self.assertEqual(hits[0]["node.nick"], nick)

    def test_rules_do_not_match_other_devices(self):
        other = "alsa_output.pci-0000_00_1f.3.analog-stereo"
        for rule in self.config["monitor.alsa.rules"]:
            for match in rule["matches"]:
                self.assertFalse(matches(match["node.name"], other))

    def test_game_and_mic_outrank_chat(self):
        priorities = {
            rule["actions"]["update-props"]["node.nick"]: rule["actions"]["update-props"][
                "priority.session"
            ]
            for rule in self.config["monitor.alsa.rules"]
        }
        self.assertGreater(priorities["INZONE Game"], priorities["INZONE Chat"])


if __name__ == "__main__":
    unittest.main()
