"""Translation lookup for the user-visible strings (gettext).

Without a compiled catalog for the user's language every string is returned
unchanged, so English is the fallback and nothing is required at runtime.
Catalogs are looked up in ``$INZONE_LOCALEDIR``, then ``$XDG_DATA_HOME/locale``
(default ``~/.local/share/locale``), then the system default.
"""

from __future__ import annotations

import gettext
import os
from pathlib import Path

DOMAIN = "inzone-buds-mixer"


def _locale_dir() -> str | None:
    override = os.environ.get("INZONE_LOCALEDIR")
    if override:
        return override
    data_home = os.environ.get("XDG_DATA_HOME") or str(Path.home() / ".local/share")
    user_dir = Path(data_home) / "locale"
    return str(user_dir) if user_dir.is_dir() else None


_translation = gettext.translation(DOMAIN, localedir=_locale_dir(), fallback=True)


def tr(message: str) -> str:
    """Return ``message`` translated, or unchanged when there is no catalog."""
    return _translation.gettext(message)
