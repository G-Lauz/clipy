from __future__ import annotations

import inspect
import sys
from typing import Callable, Dict

from .argument import Argument
from .ast.parser import Parser
from .ast.processor import CommandExecutor
from .docstring_parser import GoogleStyleDocstringParser


class Command:
    name: str = None
    description: str = None

    func: Callable
    is_group: bool

    args: Dict[str, Argument]
    subcommands: Dict[str, "Command"]

    def __init__(self, func: Callable = None, *, name: str = None):
        # If func is None, we're being used as @Command(name="...") and need to return a decorator
        self._deferred_init = False
        if func is None:
            self._deferred_init = True
            self._pending_name = name
            return

        self.name = name
        if name is None and self.name is None:
            self.name = func.__name__ if func is not None else self.__class__.__name__

        self.func = func

        self.is_group = False
        if self.func is None:
            self.is_group = True

        self.args = self.get_args()
        self.subcommands = self.get_subcommands()
        self.usage = self._get_usage(self.signature.parameters)

    def __call__(self, *args, **kwargs):
        # If we're in deferred init mode, the first call receives the function
        if self._deferred_init:
            func = args[0]
            return Command(func, name=self._pending_name)

        print(f"{self.name} is being called.")

        cmd_tree = self.build_command_tree()
        print("Command Tree:")
        print(cmd_tree)

        argv = sys.argv[1:]  # get command line arguments excluding script name
        parser = Parser(self, argv)
        ast_root = parser.parse()

        visitor = CommandExecutor()
        return ast_root.accept(visitor)

        # if self.func is not None:
        #     return self.func(*args, **kwargs)

        # print("The function doesn't exist, most probably because its a group.")
        # return None

    def get_args(self) -> Dict[str, Argument]:
        # If it's a group there is no need to set description and signature yet
        if self.is_group:
            return None

        self.description = self.func.__doc__.strip() if self.func.__doc__ else None
        args_help = GoogleStyleDocstringParser().parse(self.description) if self.description else {}

        self.signature = inspect.signature(self.func)
        parameters = self.signature.parameters

        # Build the list of arguments
        args = {}
        for name, param in parameters.items():
            # TODO: better handling of 'self' and 'cls'
            if name in ("self", "cls"):
                continue

            annotation = (
                param.annotation if param.annotation is not inspect.Parameter.empty else None
            )

            argument = Argument(
                name=name,
                type=annotation,
                default=param.default,
                help=args_help.get(name, "No description available."),
                kind=param.kind,
            )
            args[name] = argument

        return args

    def get_subcommands(self) -> Dict[str, "Command"]:
        if not self.is_group:
            return None

        # get class members
        cls_members = dir(self)

        subcommands = {}

        for member in cls_members:
            obj = getattr(self, member)
            if isinstance(obj, Command):
                subcommands[member] = obj

        return subcommands

    def build_command_tree(self, level=0):
        indent = "  " * level
        tree_str = f"{indent}- {self.name}\n"
        if self.is_group:
            for subcmd_name, subcmd in self.subcommands.items():
                tree_str += subcmd.build_command_tree(level + 1)
        return tree_str

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
