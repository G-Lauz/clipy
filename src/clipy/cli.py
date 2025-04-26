import argparse
import functools
from typing import Any, Callable, Dict, List

from .cli_types import CommandDefinition, OptionDefinition


class CLI:
    """
    Wrapper class for a CLI application.

    Attributes:
    :param func: Main function of the CLI application.
    :param usage: Usage string for the CLI application.
    :param description: Description string for the CLI application.
    :param commands: List of `CommandDefinition` instances for the CLI application. Default is an empty list.
    :param global_options: List of `OptionDefinition` instances for the CLI application. Default is an empty list.

    Methods:
    :method register_command: Register a command to the CLI application.
    :method register_global_option: Register a global option to the CLI application.
    :method build_parser: Build an `argparse.ArgumentParser` instance for the CLI application.
    """

    commands: List[CommandDefinition]
    global_options: List[OptionDefinition]
    func: Callable[..., Any]

    def __init__(self, func: Callable[..., Any], usage: str = None, description: str = None):
        self.func = func

        self.usage = usage
        self.description = description

        self.commands = []
        self.global_options = []
        functools.update_wrapper(self, func)

    def register_command(self, command: CommandDefinition):
        self.commands.append(command)

    def register_global_option(self, option: OptionDefinition):
        self.global_options.append(option)

    def build_parser(self) -> argparse.ArgumentParser:
        def format_opt(option: OptionDefinition):
            return f"{'--' if not option.positional else ''}{option.name}"

        def build_command_parser_tree(
            parser: argparse.ArgumentParser, command: CommandDefinition, lvl=0
        ):
            if command.subcommands is None:
                return

            # TODO: Remove lvl - Use Nested subcommands : by inheriting _SubParserAction and creating a custom Namespace ?
            subparsers = parser.add_subparsers(
                dest=command.name if lvl == 0 else f"subcommand{lvl}"
            )

            for subcommand in command.subcommands:
                subp = subparsers.add_parser(
                    subcommand.name,
                    usage=subcommand.usage,
                    description=subcommand.description,
                )
                for option in subcommand.options:
                    # TODO: Use Nested subcommands with a simple add_argument : by inheriting _SubParserAction and creating a custom Namespace ?
                    # subp.add_argument(format_opt(option), **option.kwargs)
                    dest = subcommand.name + "__" + option.name
                    if option.positional:
                        """
                        Show the correct name in the help menu, but the destination should be
                        prepended with the subcommand name (for easier parsing later on).

                        This can be removed once the custom nested subparser is implemented
                        and integrated with argparse
                        """
                        init_name = option.name
                        option = OptionDefinition(dest, option.kwargs, option.positional)
                        subp.add_argument(format_opt(option), **option.kwargs, metavar=init_name)
                    else:
                        subp.add_argument(format_opt(option), **option.kwargs, dest=dest)

                build_command_parser_tree(subp, subcommand, lvl=lvl + 1)

        parser = argparse.ArgumentParser(usage=self.usage, description=self.description)

        for option in self.global_options:
            parser.add_argument(format_opt(option), **option.kwargs)

        tmp_cmd = CommandDefinition("command", subcommands=self.commands)
        build_command_parser_tree(parser, tmp_cmd)

        return parser

    def __call__(self, *args, **kwargs):
        parser = self.build_parser()

        # parsed_args = parser.parse_args()
        # args_dict = vars(parsed_args)

        # TODO: Remove this - Use Nested subcommands : by inheriting _SubParserAction and creating a custom Namespace ?
        args_dict = CLI._parse_nested_commands(parser)

        all_commands: List[CommandDefinition] = []
        while command_name := args_dict.pop("command", None):
            subcommand = args_dict.pop("subcommand", {}) or {}
            command = CommandDefinition(name=command_name, options=args_dict)
            all_commands.append(command)
            args_dict = subcommand

        subcommand = all_commands[-1]
        for command in reversed(all_commands[:-1]):
            subcommand = CommandDefinition(
                name=command.name,
                subcommands=[subcommand],
                options=command.options,
                description=command.description,
                usage=command.usage,
            )

        return self.func(command=subcommand, *args, **kwargs)

    @staticmethod
    def _parse_nested_commands(parser: argparse.ArgumentParser) -> dict:
        """
        This is a temporary solution until we implement a more robust solution.
        TODO: Remove this - Use Nested subcommands : by inheriting _SubParserAction
              and creating a custom Namespace ?
        """
        parsed_args = parser.parse_args()
        args_dict = vars(parsed_args)

        parent = args_dict

        def clean_opts(args_dict: Dict[str, Any], command_name: str):
            return {
                k.replace(command_name + "__", ""): v
                for k, v in args_dict.items()
                if k.startswith(command_name + "__")
            }

        # iterate through the subcommands and build the commands tree
        subcommands = dict(
            sorted({k: v for k, v in args_dict.items() if k.startswith("subcommand") and v}.items())
        )

        for subcommand_name in subcommands.values():
            subcommand_options = clean_opts(args_dict, subcommand_name)

            parent["subcommand"] = {"command": subcommand_name}
            parent["subcommand"].update(subcommand_options)

            parent = parent["subcommand"]

        # Remove the subcommand options from the main command
        main_command_name = args_dict.get("command")
        main_command_options = clean_opts(args_dict, main_command_name)

        return {
            "command": main_command_name,
            "subcommand": args_dict.get("subcommand"),
            **main_command_options,
        }
