from __future__ import annotations

import copy
import inspect
import sys
from typing import Callable, Dict, List

from .argument import Argument
from .ast.error import ParseError
from .ast.parser import Parser
from .ast.processor import CommandExecutor
from .docstring_parser import GoogleStyleDocstringParser


class Command:
    """
    Turns a function or a class into a runnable CLI command.

    Can be used as a plain decorator, a parameterised decorator, or as a
    base class.  Subcommands are discovered automatically from class
    attributes that are themselves ``Command`` instances or methods decorated
    with ``@Command``.
    """

    name: str = None
    description: str = None

    func: Callable
    is_group: bool

    args: Dict[str, Argument]
    subcommands: Dict[str, "Command"]

    RESERVED_KEYWORDS = {"help"}

    _user_call: Callable = None

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        # If the subclass overrides __call__, save it and remove it so that
        # Command.__call__ (the dispatch logic) stays reachable through method resolution order.
        if "__call__" in cls.__dict__:
            cls._user_call = cls.__dict__["__call__"]
            del cls.__call__

    def __init__(self, func: Callable = None, *, name: str = None):
        """
        Turns a function or a method into a runnable CLI command.

        Args:
            func: The function to wrap as a command.  Optional when using
                ``@Command(name="...")`` syntax or when using inheritance.
            name: The command name to use on the CLI.  Defaults to the
                function name or class name if not provided.  When set,
                overrides the default name and prevents automatic naming of
                subcommands based on their attribute names.
        """
        # If func is None AND we're being called directly on Command class (not a subclass),
        # we're being used as @Command(name="...") and need to return a decorator
        self._deferred_init = False
        if func is None and self.__class__ == Command:
            self._deferred_init = True
            self._pending_name = name
            return

        self.id = hash(self)

        self.enforce_name = name is not None
        self.name = name
        if name is None and self.name is None:
            self.name = func.__name__ if func is not None else self.__class__.__name__.lower()

        self.func = func

        # Check if the subclass defined __call__ (saved as _user_call by __init_subclass__)
        if self.func is None and self.__class__._user_call is not None:
            self.func = self.__class__._user_call.__get__(self, self.__class__)

        self.subcommands = self.get_subcommands()

        self.is_group = bool(self.subcommands)
        if self.func is None:
            self.is_group = True

        self.signature = None
        self.args = self.get_args()

        # Store the func-level description (from __call__ or decorated func docstring)
        self.func_description = self.description

        # Use class docstring as the high-level description (shown in subcommand listings)
        if self.__class__ is not Command and self.__class__.__doc__:
            self.description = self.__class__.__doc__.strip()
        # If no class docstring, keep the func description
        elif not self.description:
            self.description = None

        self.usage = self._get_usage()

    def __get__(self, instance, owner):
        if instance is None:
            return self

        cmd = copy.copy(self)
        if cmd.func:
            cmd.func = cmd.func.__get__(instance, owner)
            cmd.signature = inspect.signature(cmd.func)
        return cmd

    def __call__(self, *args, **kwargs):
        # If we're in deferred init mode, the first call receives the function
        if self._deferred_init:
            func = args[0]
            return Command(func, name=self._pending_name)

        try:
            argv = sys.argv[1:]  # get command line arguments excluding script name
            parser = Parser(self, argv)
            ast_root = parser.parse()
        except ParseError as error:
            self._handle_parsing_error(error, argv, parser.command_tree)

        visitor = CommandExecutor()
        command_path, help_flag = ast_root.accept(visitor)

        # TODO: this require annotation because the data structure is too generic.
        # The first command in the path is the one executed
        command_node: "Command" = command_path[0][0] if command_path else None

        # Reverse to root-first order for usage display
        path = [cmd for cmd, _ in reversed(command_path)] if command_path else []

        # If empty command path, show root command help
        if help_flag:
            command_node = command_node if command_node else ast_root

        # If the resolved target is a non-callable group, display usage and exit
        is_non_callable = command_node and command_node.is_group and command_node.func is None

        if is_non_callable or help_flag:
            print(command_node.get_help(command_path=path))
            sys.exit(0)

        return command_path[0][1] if command_path else None

    def get_args(self) -> Dict[str, Argument]:
        args = {}

        # add help argument
        help_argument = Argument(
            name="help",
            type=bool,
            help="Show this help message and exit.",
            kind=inspect.Parameter.KEYWORD_ONLY,
        )

        # If it's a group AND has no function, there is no need to set description and signature
        if self.is_group and self.func is None:
            args["help"] = help_argument
            return args

        docstring = self.func.__doc__.strip() if self.func.__doc__ else None
        args_help, self.description = (
            GoogleStyleDocstringParser().parse(docstring) if docstring else ({}, "")
        )

        self.signature = inspect.signature(self.func)
        parameters = self.signature.parameters

        # Build the list of arguments
        for name, param in parameters.items():
            # TODO: better handling of 'self' and 'cls'
            if name in ("self", "cls"):
                continue

            self._handle_reserved_keyword_error(name)

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

        args["help"] = help_argument  # Should be the last argument
        return args

    def get_subcommands(self) -> Dict[str, "Command"]:
        # get class members
        cls_members = dir(self)

        subcommands = {}

        for member in cls_members:
            obj = getattr(self, member)
            if isinstance(obj, Command):
                # Override the default class name of an attribute command with the attribute name
                obj.name = member if not obj.enforce_name else obj.name

                if obj.name in subcommands:
                    existing = subcommands[obj.name]
                    raise ValueError(
                        f"subcommand name conflict: '{obj.name}' is already defined by "
                        f"'{existing.func.__name__}', cannot be reused by '{member}'"
                    )

                subcommands[obj.name] = obj

        return subcommands

    def _get_usage(self, command_path: List[Command] = None) -> str:
        command_path_str = [cmd.name for cmd in command_path] if command_path else [self.name]
        usage_parts = command_path_str

        command = command_path[-1] if command_path else self

        has_own_args = command.func is not None and command.signature is not None

        if has_own_args:
            parameters: Dict[str, inspect.Parameter] = command.signature.parameters

            for name, param in parameters.items():
                if name in ("self", "cls"):
                    continue

                # Get the type name from annotation
                if param.annotation is not inspect.Parameter.empty:
                    type_name = param.annotation.__name__
                else:
                    type_name = "str"  # default type

                # All parameters are optional (wrapped in [])
                usage_parts.append(f"[--{name} <{type_name}>]")

        if command.is_group:
            possible_cmd_str = ["{"]
            for subcmd_name in command.subcommands.keys():
                possible_cmd_str.append(f"{subcmd_name},")
            possible_cmd_str[-1] = possible_cmd_str[-1][:-1]  # Remove trailing comma
            possible_cmd_str.append("}")
            usage_parts.append(" ".join(possible_cmd_str))

        return " ".join(usage_parts)

    def get_help(self, command_path: List[Command] = None) -> str:
        help_lines = [f"usage: {self._get_usage(command_path)}\n"]

        # Prefer the func-level description (e.g. __call__ docstring) for detailed help,
        # fall back to the high-level class docstring
        detail = self.func_description or self.description
        if detail:
            help_lines.append(f"{detail}\n")

        has_own_args = self.func is not None and self.signature is not None

        if has_own_args:
            help_lines.append("options:")

            # Get the max length of argument names for formatting
            max_arg_length = max(len(arg.name) for arg in self.args.values()) if self.args else 0
            max_type_length = (
                max(
                    len(arg.type.__name__) if arg.type is not None else 3
                    for arg in self.args.values()
                )
                if self.args
                else 0
            )

            for arg in self.args.values():
                arg_str = f"--{arg.name}"

                value_str = ""
                if arg.type != bool:
                    value_str = arg.name.upper()

                type_name = f":{arg.type.__name__}" if arg.type is not None else ":str"
                if arg.type == bool:
                    type_name = ""

                default_str = ""
                if arg.is_optional:
                    default_str = f" (default: {arg.default})" if arg.default is not None else ""

                spaces = (
                    2 * max_arg_length + max_type_length + 7 - len(arg_str + value_str + type_name)
                )
                spaces = max(spaces, 1)  # Ensure at least 1 spaces between description

                help_lines.append(
                    " " * 2
                    + arg_str
                    + " "
                    + value_str
                    + type_name
                    + " " * spaces
                    + f"{arg.help}{default_str}"
                )

        if self.is_group:
            if has_own_args:
                help_lines.append("")  # blank line between options and subcommands
            help_lines.append("subcommands:")
            for subcmd in self.subcommands.values():
                desc = subcmd.description if subcmd.description else "No description available."
                help_lines.append(f"  {subcmd.name}: {desc}")

        return "\n".join(help_lines)

    def _handle_parsing_error(
        self, error: ParseError, argv: List[str], command_tree: List[Command]
    ) -> None:
        token = error.token.value if error.token else None

        print(f"usage: {self._get_usage(command_tree)}")

        if token:
            print("command:")
            joined_argv = " ".join([self.name] + argv)
            token_position = joined_argv.find(token)
            if token_position != -1:
                underline = " " * token_position + "^" * len(token)
                print(4 * " " + "$ " + joined_argv)
                print(6 * " " + underline)

        print(f"{self.name}: error: {error.message}")
        sys.exit(1)

    def _handle_reserved_keyword_error(self, name: str) -> None:
        if name in self.RESERVED_KEYWORDS:
            function_definition = f"def {self.name}{self.signature}:"
            raise SyntaxError(
                f"'{name}' is a reserved keyword argument for command functions and cannot be used as parameter name in `{function_definition}`."
            )
