import abc
import argparse
from typing import List, get_args, get_origin

from .argument import Argument
from .utils import get_list_inner_type, is_list


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

    _signature: List[Argument]

    def __init__(self):
        self.parser = argparse.ArgumentParser()
        self._signature = []

        self.parser.add_argument("positional_args", nargs="*")  # catch-all for positional mapping

    def add_argument(self, arg: Argument):
        annotation = arg.type if arg.type is not None else str

        if is_list(annotation):
            inner_type = get_list_inner_type(annotation)

            self.parser.add_argument(
                f"--{arg.name}",
                dest=arg.name,
                nargs="+",
                type=inner_type,
                help=arg.help,
                default=arg.default,
            )
        else:
            self.parser.add_argument(
                f"--{arg.name}", dest=arg.name, type=annotation, help=arg.help, default=arg.default
            )

        # We assume the argument are added in the positional order
        self._signature.append(arg)

    def parse_args(self):
        parsed_args = self.parser.parse_args()
        positional_args = parsed_args.positional_args[:]

        kwargs = {}
        for arg in self._signature:
            value = getattr(parsed_args, arg.name)

            # Argument not provide as named argument (--name)
            # Check positional arguments
            if value == arg.default:
                if positional_args:
                    if is_list(arg.type):
                        value = positional_args
                        positional_args = []
                        kwargs[arg.name] = list(value)
                    else:
                        value = positional_args.pop(0)
                        kwargs[arg.name] = arg.type(value) if arg.type else value
                elif arg.is_optional:
                    kwargs[arg.name] = arg.default
                else:
                    self.parser.error(f"Missing required argument: {arg.name}")
            else:
                if is_list(arg.type):
                    kwargs[arg.name] = list(value)
                else:
                    kwargs[arg.name] = arg.type(value) if arg.type else value

        return kwargs
