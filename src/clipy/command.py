import abc
import inspect
import pathlib
import sys
from typing import Dict

from .argument import Argument
from .docstring_parser import GoogleStyleDocstringParser
from .parser import ArgparseParser


class Command(abc.ABC):

    args: Dict[str, Argument]

    def __init__(self, func=None, *, name=None):
        self.name = self._get_name(name)

        self.signature = None
        self.usage = None
        self.description = None
        self.parser = None

        self.args = {}

        self.func = func

        if func is None:
            return  # The decorator has been called with arguments, not a function

        self._init_command()

    def __call__(self, func=None):
        if self.func is None:
            self.func = func
            self._init_command()
            return self

        parsed_args = self.parser.parse_args()
        self._check_for_empty_args(parsed_args)

        binding = self.signature.bind(**parsed_args)
        binding.apply_defaults()
        return self.func(*binding.args, **binding.kwargs)

    def _init_command(self):
        self.description = self.func.__doc__.strip() if self.func.__doc__ else None
        args_help = GoogleStyleDocstringParser().parse(self.description) if self.description else {}

        self.signature = inspect.signature(self.func)
        parameters = self.signature.parameters

        self.usage = self._get_usage(parameters)

        # Build the list of Arguments
        for name, param in parameters.items():
            annotation = (
                param.annotation if param.annotation is not inspect.Parameter.empty else None
            )

            arg = Argument(
                name=name, type=annotation, default=param.default, help=args_help.get(name)
            )
            self.args[name] = arg

        # Build the parser
        self.parser = ArgparseParser()
        for arg in self.args.values():
            self.parser.add_argument(arg)

    def _check_for_empty_args(self, parsed_args):
        missing_args = []
        for arg, value in parsed_args.items():
            if value is inspect.Parameter.empty:
                missing_args.append(arg)

        if missing_args:
            print(f"Missing required arguments: {', '.join(missing_args)}")
            print(f"Usage: {self.usage}")
            sys.exit(1)

    def _get_name(self, name=None):
        if name:
            return name

        script = pathlib.Path(sys.argv[0])
        return script.stem

    def _get_usage(self, parameters: Dict[str, inspect.Parameter]) -> str:
        usage_parts = [self.name]

        for name, param in parameters.items():
            # Get the type name from annotation
            if param.annotation is not inspect.Parameter.empty:
                type_name = param.annotation.__name__
            else:
                type_name = "str"  # default type

            # All parameters are optional (wrapped in [])
            usage_parts.append(f"[--{name} <{type_name}>]")

        return " ".join(usage_parts)
