from __future__ import annotations

import json
from contextvars import ContextVar, Token
from functools import lru_cache
from pathlib import Path
from typing import Any


Locale = str
_current_locale: ContextVar[Locale] = ContextVar("current_locale", default="ro")


def normalize_locale(value: str | None) -> Locale:
    return "en" if value == "en" else "ro"


def set_current_locale(locale: str | None) -> Token:
    return _current_locale.set(normalize_locale(locale))


def reset_current_locale(token: Token) -> None:
    _current_locale.reset(token)


def get_current_locale() -> Locale:
    return normalize_locale(_current_locale.get())


@lru_cache
def load_messages() -> dict[str, dict[str, Any]]:
    root = Path(__file__).resolve().parents[1]
    locales_dir = root / "locales"
    return {
        "en": json.loads((locales_dir / "en.json").read_text(encoding="utf-8")),
        "ro": json.loads((locales_dir / "ro.json").read_text(encoding="utf-8")),
    }


def get_message(key: str, *, locale: str | None = None, **replacements: str | int) -> str:
    current: Any = load_messages()[normalize_locale(locale or get_current_locale())]

    for segment in key.split("."):
        if not isinstance(current, dict) or segment not in current:
            return key
        current = current[segment]

    if not isinstance(current, str):
        return key

    result = current
    for name, replacement in replacements.items():
        result = result.replace(f"{{{name}}}", str(replacement))
    return result