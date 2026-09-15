"""
Errors raised while reading a configuration file.
"""

from typing import Sequence


class ConfigError(Exception):
    """Base class for errors raised while reading a configuration file."""


class ConfigReadError(ConfigError):
    """Exception raised when a configuration file cannot be opened."""

    def __init__(self, detail: str) -> None:
        """
        Args:
            detail: Human-readable reason the file could not be read.
        """
        super().__init__(detail)
        self.detail = detail


class ConfigFormatError(ConfigError):
    """Exception raised when a file cannot be decoded as a configuration."""

    def __init__(self, detail: str) -> None:
        """
        Args:
            detail: Human-readable description of what made the file unreadable.
        """
        super().__init__(detail)
        self.detail = detail


class UnknownFieldError(ConfigError):
    """Exception raised for a configuration key with no matching field."""

    def __init__(self, field: str, suggestions: Sequence[str] = ()) -> None:
        """
        Args:
            field: Dotted path of the offending key.
            suggestions: Field names close enough to be likely intended.
        """
        self.field = field
        self.suggestions = tuple(suggestions)

        message = f"unknown field '{field}'"
        if self.suggestions:
            candidates = " or ".join(f"'{name}'" for name in self.suggestions)
            message += f"; did you mean {candidates}?"

        super().__init__(message)


class MissingFieldError(ConfigError):
    """Exception raised when a configuration omits fields that have no default."""

    def __init__(self, fields: Sequence[str]) -> None:
        """
        Args:
            fields: Dotted paths of the fields that were not supplied.
        """
        self.fields = tuple(fields)

        plural = "s" if len(self.fields) > 1 else ""
        names = ", ".join(f"'{name}'" for name in sorted(self.fields))

        super().__init__(f"missing required field{plural} {names}")


class FieldTypeError(ConfigError):
    """Exception raised when a configuration value does not match its field's type."""

    def __init__(self, field: str, expected: str, got: str) -> None:
        """
        Args:
            field: Dotted path of the offending field.
            expected: Name of the type the field declares.
            got: Name of the type actually found in the file.
        """
        self.field = field
        self.expected = expected
        self.got = got

        super().__init__(f"field '{field}': expected {expected}, got {got}")
