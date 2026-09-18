#!/usr/bin/env python3
"""Unit tests for the GUI's command backend; no GTK installation is required."""

from pathlib import Path
import subprocess
import sys
import unittest


PROJECT_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_DIR / "src/inzone_buds_mixer"))

from audio import (  # noqa: E402
    AudioBackend,
    BackendError,
    chat_boost_plan,
    derive_balance,
    is_endpoint_event,
)


GAME = "alsa_output.usb-Sony_INZONE_Buds-00.pro-output-1"
CHAT = "alsa_output.usb-Sony_INZONE_Buds-00.pro-output-0"
MIC = "alsa_input.usb-Sony_INZONE_Buds-00.pro-input-0"


class FakeRunner:
    def __init__(self) -> None:
        self.commands: list[tuple[str, ...]] = []

    def __call__(self, command):
        command = tuple(command)
        self.commands.append(command)
        responses = {
            ("pactl", "list", "short", "sinks"): f"185\t{GAME}\tPipeWire\n191\t{CHAT}\tPipeWire\n",
            ("pactl", "list", "short", "sources"): f"196\t{MIC}\tPipeWire\n",
            ("pactl", "get-default-sink"): f"{GAME}\n",
            ("pactl", "get-default-source"): f"{MIC}\n",
            ("pactl", "get-sink-volume", GAME): "Volume: front-left: 39322 / 60% / -13.31 dB\n",
            ("pactl", "get-sink-volume", CHAT): "Volume: front-left: 23593 / 36% / -26.55 dB\n",
            ("pactl", "get-source-volume", MIC): "Volume: mono: 52428 / 80% / -5.81 dB\n",
        }
        if command in responses:
            return subprocess.CompletedProcess(command, 0, responses[command], "")
        if command[0] == "inzonectl":
            return subprocess.CompletedProcess(command, 0, "ok\n", "")
        return subprocess.CompletedProcess(command, 1, "", "unexpected command")


class BalanceTests(unittest.TestCase):
    def test_balance_derivation_matches_cli_model(self):
        self.assertEqual(derive_balance(100, 100), 50)
        self.assertEqual(derive_balance(100, 50), 75)
        self.assertEqual(derive_balance(50, 100), 25)
        self.assertEqual(derive_balance(100, 0), 100)
        self.assertEqual(derive_balance(0, 100), 0)


class ChatBoostPlanTests(unittest.TestCase):
    def test_activating_saves_current_volumes_and_targets_30_70(self):
        game, chat, saved = chat_boost_plan(True, None, 55, 40)
        self.assertEqual((game, chat), (30, 70))
        self.assertEqual(saved, (55, 40))

    def test_deactivating_restores_the_saved_volumes(self):
        game, chat, saved = chat_boost_plan(False, (55, 40), 30, 70)
        self.assertEqual((game, chat), (55, 40))
        self.assertIsNone(saved)

    def test_activating_with_unknown_volumes_saves_the_target_itself(self):
        game, chat, saved = chat_boost_plan(True, None, None, None)
        self.assertEqual((game, chat), (30, 70))
        self.assertEqual(saved, (30, 70))

    def test_deactivating_without_a_saved_state_falls_back_to_default(self):
        game, chat, saved = chat_boost_plan(False, None, 30, 70)
        self.assertEqual((game, chat), (30, 70))
        self.assertIsNone(saved)


class EventFilterTests(unittest.TestCase):
    def test_endpoint_and_default_changes_trigger_refresh(self):
        for line in (
            "Event 'change' on sink #3153",
            "Event 'change' on source #52",
            "Event 'new' on card #3087",
            "Event 'remove' on sink #72",
            "Event 'change' on server #4294967295",
        ):
            self.assertTrue(is_endpoint_event(line), line)

    def test_client_and_stream_events_are_ignored(self):
        # Every pactl call emits client events, including the mixer's own
        # reads; reacting to them would make the mixer refresh itself forever.
        for line in (
            "Event 'new' on client #4323",
            "Event 'change' on client #4323",
            "Event 'remove' on client #4323",
            "Event 'change' on sink-input #512",
            "Event 'new' on source-output #77",
            "",
        ):
            self.assertFalse(is_endpoint_event(line), line)


class BackendTests(unittest.TestCase):
    def setUp(self):
        self.runner = FakeRunner()
        self.backend = AudioBackend(
            pactl="pactl",
            inzonectl="inzonectl",
            runner=self.runner,
        )

    def test_snapshot_discovers_endpoints_and_volumes(self):
        snapshot = self.backend.snapshot()
        self.assertTrue(snapshot.connected)
        self.assertEqual(snapshot.game, GAME)
        self.assertEqual(snapshot.chat, CHAT)
        self.assertEqual(snapshot.microphone, MIC)
        self.assertEqual(snapshot.game_volume, 60)
        self.assertEqual(snapshot.chat_volume, 36)
        self.assertEqual(snapshot.microphone_volume, 80)
        self.assertEqual(snapshot.overall_volume, 60)
        self.assertEqual(snapshot.balance, 70)

    def test_mutations_use_inzonectl(self):
        self.backend.set_balance(70, 60)
        self.backend.set_microphone_volume(85)
        self.backend.select_defaults()
        self.backend.set_volumes(30, 70)
        self.assertIn(("inzonectl", "balance", "70", "60"), self.runner.commands)
        self.assertIn(("inzonectl", "volume", "mic", "85"), self.runner.commands)
        self.assertIn(("inzonectl", "default"), self.runner.commands)
        self.assertIn(("inzonectl", "volume", "game", "30"), self.runner.commands)
        self.assertIn(("inzonectl", "volume", "chat", "70"), self.runner.commands)

    def test_failed_command_is_reported(self):
        backend = AudioBackend(
            runner=lambda command: subprocess.CompletedProcess(command, 1, "", "no PipeWire"),
        )
        with self.assertRaisesRegex(BackendError, "no PipeWire"):
            backend.snapshot()


if __name__ == "__main__":
    unittest.main()
