"""Parse error exceptions raised during CLI argument parsing."""

from typing import Optional

from .tokenizer import Token


class ParseError(Exception):
    """Exception raised for errors in the parsing process."""

    def __init__(self, message: str, token: Optional[Token] = None) -> None:
        """
        Args:
            message: Human-readable description of the error.
            token: The :class:`.Token` that caused the error, or ``None``.
        """
        super().__init__(message)
        self.message = message
        self.token = token


class UnexpectedPositionalArgumentError(ParseError):
    """Exception raised for unexpected positional arguments."""

    def __init__(self, token: Token) -> None:
        """
        Args:
            token: The unexpected positional :class:`.Token`.
        """
        message = f"unexpected positional argument: {token.value}"
        super().__init__(message, token)


class TooManyArgumentsError(ParseError):
    """Exception raised for too many arguments provided."""

    def __init__(self) -> None:
        message = "too many arguments provided"
        super().__init__(message, None)


class UnknownArgumentError(ParseError):
    """Exception raised for unknown arguments."""

    def __init__(self, token: Token) -> None:
        """
        Args:
            token: The unrecognised option :class:`.Token`.
        """
        message = f"unknown argument: {token.value}"
        super().__init__(message, token)


class MissingRequiredValueError(ParseError):
    """Exception raised for missing required values."""

    def __init__(self, token: Token):
        """
        Args:
            token: The option :class:`.Token` whose value was absent.
        """
        message = f"missing required value for: {token.value}"
        super().__init__(message, token)


class MissingRequiredArgumentError(ParseError):
    """Exception raised for missing required arguments."""

    def __init__(self, missing_args: set):
        """
        Args:
            missing_args: Set of argument names that were not supplied.
        """
        sorted_missing_args = sorted(missing_args)
        message = f"missing required arguments: {', '.join(sorted_missing_args)}"
        super().__init__(message, None)


class UnexpectedValueFormatError(ParseError):
    """Exception raised for unexpected value format."""

    def __init__(self, expected_format: str, token: Token) -> None:
        """
        Args:
            expected_format: Description of the format that was expected.
            token: The :class:`.Token` whose value did not match.
        """
        message = f"expected value format: {expected_format}, but got: {token.value}"
        super().__init__(message, token)


class InvalidArgumentTypeError(ParseError):
    """Exception raised for invalid argument types."""

    def __init__(self, expected_type: str, token: Token) -> None:
        """
        Args:
            expected_type: Name of the type that was expected.
            token: The :class:`.Token` whose value could not be cast.
        """
        message = f"expected argument of type: {expected_type}, but got: {token.value}"
        super().__init__(message, token)


# Internal error
class UnknownTokenTypeError(ParseError):
    """Exception raised for unexpected token types."""

    def __init__(self, token: Token) -> None:
        """
        Args:
            token: The :class:`.Token` with an unrecognised type.
        """
        message = f"unexpected token type: {token.type}"
        super().__init__(message, token)
