from importlib.metadata import version

from .argument import Argument
from .command import Command
from .config import Config

__version__ = version("clipyx")


__all__ = [
    "Argument",
    "Command",
    "Config",
]
