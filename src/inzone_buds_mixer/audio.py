"""PipeWire/PulseAudio backend for INZONE Buds Mixer.

The graphical application intentionally reuses ``inzonectl`` for mutations.
Endpoint discovery and volume reads live here so the UI can remain a small,
testable GTK layer.
"""

from __future__ import annotations

from dataclasses import dataclass
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
from typing import Callable, Sequence


GAME_SUFFIX = ".pro-output-1"
CHAT_SUFFIX = ".pro-output-0"
MIC_SUFFIX = ".pro-input-0"
PERCENT_RE = re.compile(r"\b(\d{1,3})%")
# Only endpoint, card and default-device changes matter. Client events are
# excluded because every pactl call, including the mixer's own reads, emits
# them; sink-input and source-output events are per-application streams.
AUDIO_EVENT_RE = re.compile(r"^Event '(new|change|remove)' on (sink|source|card|server) #")


def is_endpoint_event(line: str) -> bool:
    """Return whether a ``pactl subscribe`` line can change the mixer state."""
    return AUDIO_EVENT_RE.match(line) is not None


class BackendError(RuntimeError):
    """A user-facing audio backend failure."""


@dataclass(frozen=True)
class AudioSnapshot:
    connected: bool
    game: str | None
    chat: str | None
    microphone: str | None
    game_volume: int | None
    chat_volume: int | None
    microphone_volume: int | None
    default_sink: str | None
    default_source: str | None

    @property
    def overall_volume(self) -> int:
        values = [value for value in (self.game_volume, self.chat_volume) if value is not None]
        return max(values, default=50)

    @property
    def balance(self) -> int:
        return derive_balance(self.game_volume, self.chat_volume)


CHAT_BOOST_TARGET = (30, 70)
# Reads back from pactl can be off by a rounding step from what was requested.
CHAT_BOOST_TOLERANCE = 1


def chat_boost_plan(
    active: bool,
    saved: tuple[int, int] | None,
    target: tuple[int, int] | None,
    game: int | None,
    chat: int | None,
) -> tuple[int | None, int | None, tuple[int, int] | None, tuple[int, int] | None]:
    """Decide the Boost Chat toggle's target volumes and new saved/target state.

    ``active`` is the toggle button's new state, ``saved`` the volumes to
    restore on deactivation, and ``target`` the volumes this toggle set the
    last time it activated (used to detect a manual change since). ``game``
    and ``chat`` are the current actual volumes.

    Turning it on saves the current volumes (defaulting to the boost target
    itself when unknown) and targets Game 30% / Chat 70%. Turning it off
    restores the saved volumes only if the current volumes still match what
    boost set; if the user changed them since, they are left alone (a ``None``
    pair, meaning: send no command).
    """
    if active:
        saved = (
            game if game is not None else CHAT_BOOST_TARGET[0],
            chat if chat is not None else CHAT_BOOST_TARGET[1],
        )
        return (*CHAT_BOOST_TARGET, saved, CHAT_BOOST_TARGET)

    if (
        target is not None
        and game is not None
        and chat is not None
        and abs(game - target[0]) <= CHAT_BOOST_TOLERANCE
        and abs(chat - target[1]) <= CHAT_BOOST_TOLERANCE
    ):
        game, chat = saved or CHAT_BOOST_TARGET
        return (game, chat, None, None)
    return (None, None, None, None)


def derive_balance(game: int | None, chat: int | None) -> int:
    """Return the 0=Chat, 50=center, 100=Game position for two volumes."""
    if game is None or chat is None or (game == 0 and chat == 0):
        return 50
    if game >= chat:
        return 100 - round((chat / game) * 50)
    return round((game / chat) * 50)


Runner = Callable[[Sequence[str]], subprocess.CompletedProcess[str]]


def _run_command(command: Sequence[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        list(command),
        check=False,
        capture_output=True,
        text=True,
        timeout=5,
    )


def _find_inzonectl() -> str:
    override = os.environ.get("INZONECTL")
    if override:
        return override
    found = shutil.which("inzonectl")
    if found:
        return found

    candidates = [
        Path(sys.argv[0]).resolve().parent / "inzonectl",
        Path.home() / ".local/bin/inzonectl",
    ]
    for candidate in candidates:
        if candidate.is_file() and os.access(candidate, os.X_OK):
            return str(candidate)
    return "inzonectl"


class AudioBackend:
    def __init__(
        self,
        *,
        pactl: str | None = None,
        inzonectl: str | None = None,
        runner: Runner | None = None,
    ) -> None:
        self.pactl = pactl or os.environ.get("PACTL", "pactl")
        self.inzonectl = inzonectl or _find_inzonectl()
        self._runner = runner or _run_command

    def _run(self, *command: str) -> str:
        try:
            result = self._runner(command)
        except (OSError, subprocess.TimeoutExpired) as error:
            raise BackendError(str(error)) from error
        if result.returncode != 0:
            message = result.stderr.strip() or result.stdout.strip() or "command failed"
            raise BackendError(message)
        return result.stdout

    @staticmethod
    def _endpoint(output: str, suffix: str) -> str | None:
        for line in output.splitlines():
            fields = line.split()
            if len(fields) >= 2 and fields[1].endswith(suffix):
                return fields[1]
        return None

    def _volume(self, target: str | None, *, source: bool = False) -> int | None:
        if not target:
            return None
        operation = "get-source-volume" if source else "get-sink-volume"
        try:
            output = self._run(self.pactl, operation, target)
        except BackendError:
            return None
        match = PERCENT_RE.search(output)
        return min(int(match.group(1)), 100) if match else None

    def snapshot(self) -> AudioSnapshot:
        sinks = self._run(self.pactl, "list", "short", "sinks")
        sources = self._run(self.pactl, "list", "short", "sources")
        game = self._endpoint(sinks, GAME_SUFFIX)
        chat = self._endpoint(sinks, CHAT_SUFFIX)
        microphone = self._endpoint(sources, MIC_SUFFIX)

        try:
            default_sink = self._run(self.pactl, "get-default-sink").strip() or None
        except BackendError:
            default_sink = None
        try:
            default_source = self._run(self.pactl, "get-default-source").strip() or None
        except BackendError:
            default_source = None

        return AudioSnapshot(
            connected=all((game, chat, microphone)),
            game=game,
            chat=chat,
            microphone=microphone,
            game_volume=self._volume(game),
            chat_volume=self._volume(chat),
            microphone_volume=self._volume(microphone, source=True),
            default_sink=default_sink,
            default_source=default_source,
        )

    def set_balance(self, position: int, maximum: int) -> None:
        self._run(self.inzonectl, "balance", str(position), str(maximum))

    def set_volumes(self, game: int, chat: int) -> None:
        self._run(self.inzonectl, "volume", "game", str(game))
        self._run(self.inzonectl, "volume", "chat", str(chat))

    def set_microphone_volume(self, volume: int) -> None:
        self._run(self.inzonectl, "volume", "mic", str(volume))

    def select_defaults(self) -> None:
        self._run(self.inzonectl, "default")

    def activate_profile(self) -> None:
        self._run(self.inzonectl, "profile")
