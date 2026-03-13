from importlib.metadata import version

from .argument import Argument
from .command import Command

__version__ = version("clipyx")


__all__ = [
    "Argument",
    "Command",
]
