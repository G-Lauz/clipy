from __future__ import annotations

import copy
import dataclasses
import inspect
import sys
from typing import Callable, Dict, List, get_origin

from .argument import Argument
from .ast.error import ParseError
from .ast.parser import Parser
from .ast.processor import CommandExecutor
from .config import LOADERS
from .docstring_parser import GoogleStyleDocstringParser
from .utils import is_config, resolve_type_hints, unwrap_optional


def _display_type_name(argument: Argument) -> str:
    """
    Return the type name shown for *argument* in usage and help output.

    Args:
        argument: The :class:`.Argument` to describe, or ``None`` when the
            parameter has no matching argument.

    Returns:
        str: The type name to display.
    """
    annotation = argument.type if argument is not None else None

    if is_config(annotation):
        return "path"
    if annotation is None:
        return "str"

    origin = get_origin(annotation) or annotation
    return getattr(origin, "__name__", None) or str(annotation)


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

        # Annotations reach `inspect.signature` as strings under PEP 563; resolve them once
        # so everything downstream can rely on `Argument.type` being a real type object.
        type_hints = resolve_type_hints(self.func)

        # Build the list of arguments
        for name, param in parameters.items():
            # TODO: better handling of 'self' and 'cls'
            if name in ("self", "cls"):
                continue

            self._handle_reserved_keyword_error(name)

            annotation = type_hints.get(name, param.annotation)
            if annotation is inspect.Parameter.empty:
                annotation = None

            annotation = unwrap_optional(annotation)

            if is_config(annotation):
                self._handle_config_argument_error(name, annotation, param)

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

            for name in parameters:
                if name in ("self", "cls"):
                    continue

                type_name = _display_type_name((command.args or {}).get(name))

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
                max(len(_display_type_name(arg)) for arg in self.args.values()) if self.args else 0
            )

            for arg in self.args.values():
                arg_str = f"--{arg.name}"

                value_str = ""
                if arg.type != bool:
                    value_str = arg.name.upper()

                type_name = f":{_display_type_name(arg)}"
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

        if has_own_args:
            for arg in self.args.values():
                if is_config(arg.type):
                    help_lines.extend(self._get_config_help(arg))

        if self.is_group:
            if has_own_args:
                help_lines.append("")  # blank line between options and subcommands
            help_lines.append("subcommands:")
            for subcmd in self.subcommands.values():
                desc = subcmd.description if subcmd.description else "No description available."
                help_lines.append(f"  {subcmd.name}: {desc}")

        return "\n".join(help_lines)

    @staticmethod
    def _get_config_help(argument: Argument) -> List[str]:
        """
        Render the fields a configuration argument reads from its file.

        Args:
            argument: The configuration :class:`.Argument` to describe.

        Returns:
            List[str]: The help lines for this configuration, led by a blank
            separator line, or an empty list if it declares no fields.
        """
        fields = argument.type.describe()
        if not fields:
            return []

        formats = ", ".join(sorted(suffix.lstrip(".").upper() for suffix in LOADERS))
        lines = ["", f"config file fields (--{argument.name}, {formats}):"]

        # Nested fields are indented
        max_label_length = max(
            2 * field.depth + len(f"{field.path}:{field.type_name}") for field in fields
        )

        for field in fields:
            label = f"{field.path}:{field.type_name}"
            spaces = max(max_label_length - 2 * field.depth - len(label) + 2, 1)

            default_str = ""
            if not field.required and field.default is not None:
                default_str = f" (default: {field.default})"

            lines.append(
                " " * (2 + 2 * field.depth) + label + " " * spaces + f"{field.help}{default_str}"
            )

        return lines

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

    def _handle_config_argument_error(
        self, name: str, config_type: type, param: inspect.Parameter
    ) -> None:
        """
        Reject a configuration parameter that cannot work, at decoration time.

        Args:
            name: Name of the parameter being declared.
            config_type: The :class:`clipy.Config` subclass it is annotated with.
            param: The :class:`inspect.Parameter` being turned into an argument.

        Raises:
            SyntaxError: If the configuration type or the parameter is unusable.
        """
        if not dataclasses.is_dataclass(config_type):
            raise SyntaxError(
                f"'{config_type.__name__}' subclasses clipy.Config but is not a dataclass, so its "
                f"fields cannot be read. Apply @dataclasses.dataclass to it."
            )

        for field in dataclasses.fields(config_type):
            if field.name in self.RESERVED_KEYWORDS:
                raise SyntaxError(
                    f"'{field.name}' is a reserved keyword argument and cannot be used as a field "
                    f"name in config class '{config_type.__name__}'."
                )

        # A default never passes through the parser, so it would reach the command
        # as a path string where the annotation expects a config object.
        if param.default is not inspect.Parameter.empty and param.default is not None:
            raise SyntaxError(
                f"config argument '{name}' cannot have a default of "
                f"{param.default!r}: a default is passed to the command as-is and is never read "
                f"as a config file. Use '{name}: {config_type.__name__} = None' and handle None, "
                f"or make the argument required."
            )

    def _handle_reserved_keyword_error(self, name: str) -> None:
        if name in self.RESERVED_KEYWORDS:
            function_definition = f"def {self.name}{self.signature}:"
            raise SyntaxError(
                f"'{name}' is a reserved keyword argument for command functions and cannot be used as parameter name in `{function_definition}`."
            )
