from __future__ import annotations

import collections
import dataclasses
import enum
from typing import List


class TokenType(enum.Enum):
    LONG_OPT = enum.auto()
    SHORT_OPT = enum.auto()
    SHORT_OPT_COMBINED = enum.auto()
    POSITIONAL = enum.auto()
    VALUE = enum.auto()
    DOUBLE_HYPHEN = enum.auto()
    END = enum.auto()


@dataclasses.dataclass
class Token:
    type: TokenType
    value: str


class Tokenizer:
    argv: List[str]
    index: int
    end_of_options: bool
    buffered_token: collections.deque

    def __init__(self, argv: List[str]):
        self.argv = argv
        self.index = 0

        self.end_of_options = False
        self.buffered_token = collections.deque()

    def has_next(self) -> bool:
        return self.index < len(self.argv) + len(self.buffered_token) + 1

    def next(self) -> Token:
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
        self.buffered_token.appendleft(token)

    def get_tokens(self) -> list[Token]:
        tokens = []
        while self.has_next():
            tokens.append(self.next())
        return tokens

    def reset(self):
        self.index = 0
        self.end_of_options = False
        self.buffered_token = collections.deque()
