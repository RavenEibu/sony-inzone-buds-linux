"""Message catalog entries for texts used outside Python.

bin/inzone-autoswitch (Bash) translates its desktop notifications through
src/inzone_buds_mixer/i18n.py. xgettext cannot read Bash, so the strings are
listed here, exactly as passed to notify(). This file is only scanned by
tools/update-pot.sh and is never imported or installed.
"""

from i18n import tr  # noqa: F401  (documentation of the keyword only)

tr("INZONE Buds connected")
tr("Game and Chat are ready.")
tr("INZONE Buds disconnected")
