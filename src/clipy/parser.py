import abc
import argparse

from .argument import Argument


class Parser(abc.ABC):

    @abc.abstractmethod
    def add_argument(self, *args, **kwargs):
        """Add an argument to the parser."""
        pass

    @abc.abstractmethod
    def parse_args(self, args=None):
        """Parse the command line arguments."""
        pass


class ArgparseParser(Parser):

    def __init__(self):
        self.parser = argparse.ArgumentParser()

    def add_argument(self, arg: Argument):
        annotation = arg.type if arg.type is not None else str
        self.parser.add_argument(
            f"--{arg.name}", type=annotation, help=arg.help, default=arg.default
        )

    def parse_args(self):
        parsed_args = self.parser.parse_args()
        return {k: v for k, v in vars(parsed_args).items() if v is not None}
