import abc
import argparse
import inspect
from typing import Callable, Dict, List, Tuple

from .argument import Argument
from .utils import get_dict_key_value_types, get_list_inner_type, is_dict, is_list


class Parser(abc.ABC):

    @abc.abstractmethod
    def add_argument(self, *args, **kwargs):
        """Add an argument to the parser."""
        pass

    @abc.abstractmethod
    def parse_args(self, args=None) -> Tuple[Dict[str, any], List[str], Dict[str, any]]:
        """Parse the command line arguments."""
        pass


class ArgparseParser(Parser):

    _signature: List[Argument]

    def __init__(self):
        self.parser = argparse.ArgumentParser()
        self._signature = []

        self.varargs = None

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
        elif is_dict(annotation):
            key_type, value_type = get_dict_key_value_types(annotation)

            help = (
                arg.help or ""
            ) + " (Dictionary entry as `key=value`, can be used multiple times)"
            default = arg.default if arg.default is not inspect.Parameter.empty else None

            self.parser.add_argument(
                f"--{arg.name}",
                dest=arg.name,
                action="append",
                type=self._parse_key_value(key_type, value_type),
                help=help,
                default=default,
            )
        elif arg.kind == inspect.Parameter.VAR_POSITIONAL:
            self.varargs = arg.name
            self.parser.add_argument(
                f"--{arg.name}",
                dest=arg.name,
                nargs="+",
                type=annotation,  # Default to str
                help=arg.help,
                default=arg.default,
            )
        else:
            self.parser.add_argument(
                f"--{arg.name}", dest=arg.name, type=annotation, help=arg.help, default=arg.default
            )

        # We assume the argument are added in the positional order
        self._signature.append(arg)

    def _parse_key_value(self, key_type: type, value_type: type) -> Callable:
        def wrapper(entry: str) -> Tuple[any, any]:
            if "=" not in entry:
                self.parser.error(f"Invalid dictionary entry: {entry}. Expected format key=value")

            key, value = entry.split("=", 1)
            try:
                return key_type(key), value_type(value)
            except ValueError as ve:
                self.parser.error(f"Invalid types in dictionary entry: {entry}. Error: {ve}")

        return wrapper

    def _parse_dict(self, entries: List[Tuple[str]], kv_type: Tuple[type]) -> Dict[any, any]:
        key_type, value_type = get_dict_key_value_types(kv_type)

        # check if list[str] instead of list[tuple[str]] and adjust format
        if entries and isinstance(entries[0], str):
            parser = self._parse_key_value(key_type, value_type)
            parsed_entries = []
            for entry in entries:
                key, value = parser(entry)
                parsed_entries.append((key, value))
            entries = parsed_entries

        adict = {}
        for key, value in entries:
            adict[key_type(key)] = value_type(value)
        return adict

    def parse_args(self) -> Tuple[Dict[str, any], List[str], Dict[str, any]]:
        parsed_args = self.parser.parse_args()
        positional_args = parsed_args.positional_args[:]

        kwargs = {}
        for arg in self._signature:
            value = getattr(parsed_args, arg.name)

            if arg.name == self.varargs:
                continue  # ignore varargs for the moment

            # Argument not provide as named argument (--name)
            # Check positional arguments
            if value == arg.default or value is None:
                if positional_args:
                    if is_list(arg.type):
                        value = positional_args
                        positional_args = []
                        kwargs[arg.name] = list(value)
                    elif is_dict(arg.type):
                        value = positional_args
                        positional_args = []
                        kwargs[arg.name] = self._parse_dict(value, arg.type)
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
                elif is_dict(arg.type):
                    kwargs[arg.name] = self._parse_dict(value, arg.type)
                else:
                    kwargs[arg.name] = arg.type(value) if arg.type else value

        if self.varargs:
            value = getattr(parsed_args, self.varargs)
            if value is not None and value is not inspect.Parameter.empty:
                positional_args.extend(list(value))

        return kwargs, positional_args, None
