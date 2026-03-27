from __future__ import annotations

import dataclasses
import inspect
from typing import Any


@dataclasses.dataclass
class Argument:
    """
    Represents a single CLI argument with its metadata.

    Attributes:
        name: The argument name as used on the command line.
        type: The Python type used to cast the raw string value.
        help: A human-readable description shown in help output.
        kind: The parameter kind from ``inspect.Parameter`` (e.g. POSITIONAL_ONLY, KEYWORD_ONLY).
        default: The default value, or ``inspect.Parameter.empty`` when required.
    """

    name: str
    type: type
    help: str
    kind: inspect._ParameterKind
    default: Any = inspect.Parameter.empty

    @property
    def is_required(self):
        """
        Check whether the argument has no default value.

        Returns:
            bool: True if the argument must be provided by the user.
        """
        return self.default is inspect.Parameter.empty

    @property
    def is_optional(self):
        """
        Check whether the argument has a default value.

        Returns:
            bool: True if the argument may be omitted by the user.
        """
        return self.default is not inspect.Parameter.empty
