"""Tiny translation layer: English source strings, one catalog module per language.

The language follows the usual gettext variables (LANGUAGE, LC_ALL, LC_MESSAGES, LANG).
To add a language, add `locales/<code>.py` exposing a CATALOG dict and list it in
_LANGUAGES. Keys are the exact English strings passed to `_()`.
"""
from __future__ import annotations

import importlib
import os

_LANGUAGES = {"fr"}


def _detect() -> str:
    for var in ("LANGUAGE", "LC_ALL", "LC_MESSAGES", "LANG"):
        value = os.environ.get(var, "")
        if value and value not in ("C", "POSIX"):
            return value.split(":")[0].split(".")[0].split("_")[0].lower()
    return "en"


LANG = _detect()
_CATALOG: dict[str, str] = (
    importlib.import_module(f".locales.{LANG}", __package__).CATALOG if LANG in _LANGUAGES else {}
)


def _(text: str) -> str:
    return _CATALOG.get(text, text)
