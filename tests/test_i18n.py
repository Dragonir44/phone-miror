"""Every string passed to _() has a translation, with the same {placeholders}."""
import ast
import string
from pathlib import Path

from phone_mirror.locales import fr

PACKAGE = Path(__file__).resolve().parent.parent / "phone_mirror"


def used_strings():
    for f in PACKAGE.glob("*.py"):
        for node in ast.walk(ast.parse(f.read_text())):
            if (isinstance(node, ast.Call) and getattr(node.func, "id", None) == "_"
                    and node.args and isinstance(node.args[0], ast.Constant)):
                yield node.args[0].value


def fields(text):
    return {f[1] for f in string.Formatter().parse(text) if f[1]}


def test_french_catalog_is_complete():
    used = set(used_strings())
    assert not used - fr.CATALOG.keys(), "missing translations"
    assert not fr.CATALOG.keys() - used, "unused translations"


def test_french_placeholders_match():
    for source, translation in fr.CATALOG.items():
        assert translation, source
        assert fields(source) == fields(translation), source
