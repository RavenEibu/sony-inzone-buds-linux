#!/usr/bin/env python3
"""Add xml:lang translations of name, summary and description paragraphs.

Usage: localize-metainfo.py PO_DIR INPUT.xml OUTPUT.xml

Languages come from PO_DIR/LINGUAS; catalogs are compiled with msgfmt into a
temporary directory. Release notes are left in English on purpose.
"""

from __future__ import annotations

import gettext
import subprocess
import sys
import tempfile
import xml.etree.ElementTree as ET
from pathlib import Path

XML_LANG = "{http://www.w3.org/XML/1998/namespace}lang"


def normalize(text: str) -> str:
    """Same whitespace handling as xgettext for XML text."""
    return " ".join(text.split())


def load_catalogs(po_dir: Path, work: Path) -> dict[str, gettext.NullTranslations]:
    catalogs: dict[str, gettext.NullTranslations] = {}
    for lang in (po_dir / "LINGUAS").read_text(encoding="utf-8").split():
        mo = work / f"{lang}.mo"
        subprocess.run(
            ["msgfmt", "-o", str(mo), str(po_dir / f"{lang}.po")], check=True
        )
        with mo.open("rb") as handle:
            catalogs[lang] = gettext.GNUTranslations(handle)
    return catalogs


def add_translations(parent: ET.Element, element: ET.Element, catalogs) -> None:
    source = normalize("".join(element.itertext()))
    if not source:
        return
    position = list(parent).index(element)
    for lang in sorted(catalogs):
        translated = catalogs[lang].gettext(source)
        if translated == source and lang != "en":
            continue
        clone = ET.Element(element.tag, {XML_LANG: lang})
        clone.text = translated
        clone.tail = element.tail
        position += 1
        parent.insert(position, clone)


def main() -> int:
    po_dir, source, destination = (Path(arg) for arg in sys.argv[1:4])
    parser = ET.XMLParser(target=ET.TreeBuilder(insert_comments=True))
    tree = ET.parse(source, parser=parser)
    root = tree.getroot()
    with tempfile.TemporaryDirectory() as tmp:
        catalogs = load_catalogs(po_dir, Path(tmp))
    for tag in ("name", "summary"):
        element = root.find(tag)
        if element is not None:
            add_translations(root, element, catalogs)
    description = root.find("description")
    if description is not None:
        for paragraph in list(description.findall("p")):
            add_translations(description, paragraph, catalogs)
    ET.indent(tree, space="  ")
    tree.write(destination, encoding="utf-8", xml_declaration=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
