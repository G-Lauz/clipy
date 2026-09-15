"""
Reading configuration files and decoding them by format.
"""

from __future__ import annotations

import json
import os
from typing import Any, Callable, Dict

from .error import ConfigFormatError


def load_json(text: str) -> Any:
    """Decode *text* as JSON.

    Args:
        text: The raw file contents.

    Returns:
        Any: The decoded document.

    Raises:
        ConfigFormatError: If *text* is not well-formed JSON.
    """
    try:
        return json.loads(text)
    except json.JSONDecodeError as error:
        raise ConfigFormatError(f"invalid JSON: {error}") from error


#: Maps a lower-cased file extension to the loader that decodes it.
LOADERS: Dict[str, Callable[[str], Any]] = {".json": load_json}


def load(path: str) -> Any:
    """Read and decode the configuration file at *path*.

    The file extension selects the format.

    Args:
        path: Path to the configuration file.

    Returns:
        Any: The decoded document.

    Raises:
        OSError: If the file cannot be opened.
        ConfigFormatError: If the extension is unsupported or the contents are
            malformed.
    """
    suffix = os.path.splitext(str(path))[1].lower()

    loader = LOADERS.get(suffix)
    if loader is None:
        supported = ", ".join(sorted(LOADERS))
        found = f"'{suffix}'" if suffix else "no extension"
        raise ConfigFormatError(f"unsupported config format: {found} (supported: {supported})")

    with open(path, encoding="utf-8") as handle:
        text = handle.read()

    return loader(text)
