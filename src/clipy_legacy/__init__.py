"""Core module of Clipy"""

from .cli_types import CommandDefinition, OptionDefinition
from .clipy import argument, command
from .decorators import App, Command, Option

__all__ = [
    "command",
    "argument",
    "Option",
    "Command",
    "App",
    "CommandDefinition",
    "OptionDefinition",
]
