"""Tokenizer for converting a raw ``argv`` list into a typed token stream."""

from __future__ import annotations

import collections
import dataclasses
import enum
from typing import List


class TokenType(enum.Enum):
    """
    Enumeration of token types recognised by :class:`Tokenizer`.

    Members:
        LONG_OPT: A long option flag starting with ``--`` (e.g. ``--foo``).
        SHORT_OPT: A single short option flag starting with ``-`` (e.g. ``-f``).
        SHORT_OPT_COMBINED: Combined short flags (e.g. ``-abc``).
        POSITIONAL: A bare positional value (no leading ``-``).
        VALUE: An inline value from ``--opt=value`` syntax.
        DOUBLE_HYPHEN: The ``--`` sentinel that ends option parsing.
        END: A synthetic end-of-input marker.
    """

    LONG_OPT = enum.auto()
    SHORT_OPT = enum.auto()
    SHORT_OPT_COMBINED = enum.auto()
    POSITIONAL = enum.auto()
    VALUE = enum.auto()
    DOUBLE_HYPHEN = enum.auto()
    END = enum.auto()


@dataclasses.dataclass
class Token:
    """
    A single lexical unit produced by :class:`Tokenizer`.

    Attributes:
        type: The :class:`TokenType` of this token.
        value: The raw string value extracted from ``argv``.
    """

    type: TokenType
    value: str


class Tokenizer:
    """
    Converts a raw ``argv`` list into a stream of :class:`Token` objects.

    Supports ``--option value``, ``--option=value``, positional arguments,
    short options, the ``--`` sentinel, and push-back buffering.

    Attributes:
        argv: The raw argument list to tokenize.
        index: Current position in :attr:`argv`.
        end_of_options: ``True`` after a ``--`` sentinel is encountered.
        buffered_token: FIFO buffer for tokens that have been pushed back.
    """

    argv: List[str]
    index: int
    end_of_options: bool
    buffered_token: collections.deque

    def __init__(self, argv: List[str]):
        """
        Args:
            argv: The raw argument list to tokenize (e.g. ``sys.argv[1:]``).
        """
        self.argv = argv
        self.index = 0

        self.end_of_options = False
        self.buffered_token = collections.deque()

    def has_next(self) -> bool:
        """
        Check whether more tokens are available.

        Returns:
            bool: True if at least one more token can be produced.
        """
        return self.index < len(self.argv) + len(self.buffered_token) + 1

    def next(self) -> Token:
        """
        Consume and return the next token from the stream.

        Classifies the next item in :attr:`argv` (or from the push-back
        buffer) as the appropriate :class:`TokenType`.

        Returns:
            Token: The next token.  Returns a :attr:`TokenType.END` token
            when the stream is exhausted.
        """
        if self.buffered_token:
            return self.buffered_token.popleft()

        if self.index >= len(self.argv):
            self.index += 1
            return Token(TokenType.END, "<EOF>")

        item = self.argv[self.index]
        self.index += 1

        # Terminate all options parsing, The following is treated as non-option arguments as stated in POSIX:
        # https://sourceware.org/glibc/manual/2.42/html_mono/libc.html#Program-Arguments
        if item == "--":
            self.end_of_options = True
            return Token(TokenType.DOUBLE_HYPHEN, item)

        if self.end_of_options:
            return Token(TokenType.POSITIONAL, item)

        # Handle long options (--option value or --option=value)
        elif item.startswith("--"):
            if "=" in item:
                name, value = item.split("=", 1)

                # Buffer the value token for the next call
                self.buffered_token.append(Token(TokenType.VALUE, value))
                return Token(TokenType.LONG_OPT, name)
            else:
                return Token(TokenType.LONG_OPT, item)

        # Handle short options (-o value or -ovalue or -abc)
        elif item.startswith("-") and len(item) > 1:
            if len(item) > 2:
                # Combined short options like -abc or -ovalue
                return Token(TokenType.SHORT_OPT_COMBINED, item)
            else:
                # Single short option like -a
                return Token(TokenType.SHORT_OPT, item)

        return Token(TokenType.POSITIONAL, item)

    def push_back(self, token: Token):
        """
        Push *token* back to the front of the stream.

        The pushed-back token will be returned by the next call to
        :meth:`next`.

        Args:
            token: The :class:`Token` to push back.
        """
        self.buffered_token.appendleft(token)

    def get_tokens(self) -> list[Token]:
        """
        Consume and return all remaining tokens as a list.

        Returns:
            list[Token]: Every token up to and including the ``END`` token.
        """
        tokens = []
        while self.has_next():
            tokens.append(self.next())
        return tokens

    def reset(self):
        """
        Reset the tokenizer to its initial state.

        Clears :attr:`index`, :attr:`end_of_options`, and
        :attr:`buffered_token` so the same ``argv`` can be re-tokenized.
        """
        self.index = 0
        self.end_of_options = False
        self.buffered_token = collections.deque()
