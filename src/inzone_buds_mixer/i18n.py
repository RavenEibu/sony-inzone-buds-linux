"""Translation lookup for the user-visible strings (gettext).

Language selection, first match wins:

1. ``INZONE_LANGUAGE`` in the environment (``--language`` of the launcher sets it);
2. an uncommented ``: "${INZONE_LANGUAGE:=xx}"`` line in the user config file
   (``~/.config/inzone-buds-mixer/config``, see ``config.example``);
3. the system language (``LANGUAGE``, ``LC_ALL``, ``LC_MESSAGES``, ``LANG``).

``auto`` or an empty value means "use the system language"; ``C`` or ``en``
forces English. A string without a translation is shown unchanged, so English
is always the fallback and no catalog is required at runtime.

Catalogs are looked up in ``$INZONE_LOCALEDIR``, then ``$XDG_DATA_HOME/locale``
(default ``~/.local/share/locale``), then the system locale directory.

Run as a script to translate one message (used by inzone-autoswitch for its
desktop notifications): ``python3 i18n.py "message"``.
"""

from __future__ import annotations

import gettext
import os
import re
import sys
from pathlib import Path

DOMAIN = "inzone-buds-mixer"

_CONFIG_LINE = re.compile(r'^\s*:\s*"\$\{INZONE_LANGUAGE:=([^}]*)\}"')


def _config_file() -> Path:
    override = os.environ.get("INZONE_CONFIG_FILE")
    if override:
        return Path(override)
    config_home = os.environ.get("XDG_CONFIG_HOME") or str(Path.home() / ".config")
    return Path(config_home) / "inzone-buds-mixer" / "config"


def configured_language() -> str:
    """Return the requested language code, or '' for the system language."""
    value = os.environ.get("INZONE_LANGUAGE")
    if value is None:
        value = ""
        try:
            for line in _config_file().read_text(encoding="utf-8").splitlines():
                match = _CONFIG_LINE.match(line)
                if match:
                    value = match.group(1).strip().strip("'\"")
        except OSError:
            pass
    return "" if value.lower() == "auto" else value


def _locale_dirs() -> list[str | None]:
    dirs: list[str | None] = []
    override = os.environ.get("INZONE_LOCALEDIR")
    if override:
        dirs.append(override)
    data_home = os.environ.get("XDG_DATA_HOME") or str(Path.home() / ".local/share")
    dirs.append(str(Path(data_home) / "locale"))
    dirs.append(None)  # gettext's system default
    return dirs


def load_translation(language: str | None = None) -> gettext.NullTranslations:
    """Return the translation for ``language`` (default: the configured one)."""
    if language is None:
        language = configured_language()
    if language in ("C", "POSIX", "en") or language.lower().startswith("en_"):
        return gettext.NullTranslations()
    languages = [language] if language else None
    for localedir in _locale_dirs():
        try:
            return gettext.translation(DOMAIN, localedir=localedir, languages=languages)
        except OSError:
            continue
    return gettext.NullTranslations()


_translation = load_translation()


def tr(message: str) -> str:
    """Return ``message`` translated, or unchanged when there is no catalog."""
    return _translation.gettext(message)


if __name__ == "__main__":
    print(tr(sys.argv[1]) if len(sys.argv) > 1 else "")
