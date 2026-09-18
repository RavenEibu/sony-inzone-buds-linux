"""Launch-at-login entry for INZONE Buds Mixer.

Writes or removes an XDG autostart desktop entry, which GNOME, KDE Plasma and
other desktops run when the session starts. Kept free of GTK so it can be
tested without a graphical environment.
"""

from __future__ import annotations

import os
from pathlib import Path
import shutil


APP_ID = "io.github.RavenEibu.InzoneBudsMixer"
HIDDEN_OPTION = "--hidden"
# Characters that require quoting an Exec argument (Desktop Entry spec).
_RESERVED = set(" \t\n\"'\\><~|&;$*?#()`")
_ESCAPED_IN_QUOTES = set('"`$\\')


def autostart_file(config_home: Path | None = None) -> Path:
    if config_home is None:
        config_home = Path(os.environ.get("XDG_CONFIG_HOME") or Path.home() / ".config")
    return config_home / "autostart" / f"{APP_ID}.desktop"


def launcher_command() -> str:
    """Return the absolute launcher path when known.

    The session may start autostart entries before ~/.local/bin is in PATH, so
    the launcher exports its own path for this purpose.
    """
    return (
        os.environ.get("INZONE_BUDS_MIXER_COMMAND")
        or shutil.which("inzone-buds-mixer")
        or "inzone-buds-mixer"
    )


def _exec_argument(argument: str) -> str:
    argument = argument.replace("%", "%%")
    if not any(character in _RESERVED for character in argument):
        return argument
    escaped = "".join(
        "\\" + character if character in _ESCAPED_IN_QUOTES else character
        for character in argument
    )
    return f'"{escaped}"'


def desktop_entry(command: str) -> str:
    exec_line = " ".join(_exec_argument(part) for part in (command, HIDDEN_OPTION))
    # Exec is also a string value, whose own escaping doubles backslashes.
    exec_line = exec_line.replace("\\", "\\\\")
    return (
        "[Desktop Entry]\n"
        "Type=Application\n"
        "Name=INZONE Buds Mixer\n"
        "Comment=Start INZONE Buds Mixer in the tray\n"
        f"Exec={exec_line}\n"
        f"Icon={APP_ID}\n"
        "Terminal=false\n"
        "X-GNOME-Autostart-enabled=true\n"
    )


def is_enabled(path: Path | None = None) -> bool:
    path = path or autostart_file()
    try:
        lines = {line.strip() for line in path.read_text(encoding="utf-8").splitlines()}
    except OSError:
        return False
    # Session settings may disable an entry instead of deleting it.
    return not {"Hidden=true", "X-GNOME-Autostart-enabled=false"} & lines


def set_enabled(enabled: bool, path: Path | None = None, command: str | None = None) -> None:
    path = path or autostart_file()
    if not enabled:
        path.unlink(missing_ok=True)
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + ".tmp")
    temporary.write_text(desktop_entry(command or launcher_command()), encoding="utf-8")
    temporary.replace(path)
