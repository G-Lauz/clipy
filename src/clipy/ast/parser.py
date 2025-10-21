from __future__ import annotations

import inspect
from typing import TYPE_CHECKING, List

from ..utils import get_dict_key_value_types, get_list_inner_type, is_dict, is_list
from .nodes import ArgumentNode, CommandNode
from .tokenizer import Token, Tokenizer, TokenType

if TYPE_CHECKING:
    from clipy import Command


class Parser:
    tokenizer: Tokenizer

    def __init__(self, root_command: Command, argv: List[str]):
        self.tokenizer = Tokenizer(argv)
        self.root = root_command

        self.current_token = None

    def _get_next_token(self):
        self.current_token = self.tokenizer.next()
        return self.current_token

    def parse(self) -> CommandNode:
        self.tokenizer.reset()

        return self._recursive_parse(self.root)

    def _recursive_parse(self, command: Command) -> CommandNode:
        command_node = CommandNode(command)

        num_args = len(command.args) if command.args else 0
        args_parsed = 0

        while self.current_token is None or self.current_token.type != TokenType.END:
            token = self._get_next_token()

            print(
                f"Processing token: {token.type} ({token.value}) for command {command_node.cmd_instance.name}"
            )

            if token.type in [TokenType.LONG_OPT, TokenType.SHORT_OPT]:
                self._handle_option(token, command_node)
                args_parsed += 1

            elif token.type == TokenType.SHORT_OPT_COMBINED:
                self._handle_combined_options(token, command_node)

            elif token.type == TokenType.DOUBLE_HYPHEN:
                # Do nothing, all subsequent token will be positional,
                # which is handled by TokenType.POSITIONAL
                continue

            elif token.type == TokenType.POSITIONAL:

                # Check if there are subcommands
                found_command = False
                if command_node.cmd_instance.is_group:
                    sub_cmd = command_node.cmd_instance.subcommands.get(token.value, None)
                    if sub_cmd:
                        # Found a subcommand, create a new CommandNode and recurse
                        subcommand_node = self._recursive_parse(sub_cmd)
                        command_node.add_child(subcommand_node)
                        found_command = True
                        return command_node

                if found_command:
                    continue

                # It's an argument for the current command
                if command_node.cmd_instance.args is None:
                    raise ValueError(
                        f"Unexpected positional argument: {token.value} for command {command_node.cmd_instance.name}"
                    )

                # check if an argument is a var-positional
                has_varargs_argument = command_node.cmd_instance.args and any(
                    arg.kind == inspect.Parameter.VAR_POSITIONAL
                    for arg in command_node.cmd_instance.args.values()
                )

                if args_parsed >= num_args and not has_varargs_argument:
                    raise ValueError(
                        f"Too many arguments provided for command {command_node.cmd_instance.name}"
                    )

                # Get the next expected argument
                arg_names = list(command_node.cmd_instance.args.keys())
                for child in command_node.children:
                    if isinstance(child, ArgumentNode):
                        if child.arg_instance.name in arg_names:
                            arg_names.remove(child.arg_instance.name)
                arg_name = arg_names[0]

                argument = command_node.cmd_instance.args.get(arg_name)

                if argument is None:
                    raise ValueError(
                        f"Unexpected positional argument: {token.value} for command {command_node.cmd_instance.name}"
                    )

                if argument.kind == inspect.Parameter.VAR_POSITIONAL:
                    values = [argument.type(token.value) if argument.type else token.value]

                    token_is_part_of_the_list = True
                    while token_is_part_of_the_list:
                        value_token = self._get_next_token()

                        token_is_part_of_the_list = (
                            value_token.type == TokenType.VALUE
                            or value_token.type == TokenType.POSITIONAL
                        )
                        if not token_is_part_of_the_list:
                            # Push back the token for further processing
                            self.tokenizer.push_back(value_token)
                        else:
                            # Cast the value to the appropriate inner type
                            value = (
                                argument.type(value_token.value)
                                if argument.type
                                else value_token.value
                            )
                            values.append(value)

                    option_node = ArgumentNode(argument, values)
                    command_node.add_child(option_node)

                else:
                    # Cast the value to the appropriate type
                    value = argument.type(token.value) if argument.type else token.value
                    argument_node = ArgumentNode(argument, value)
                    command_node.add_child(argument_node)
                    args_parsed += 1

            elif token.type == TokenType.END:
                continue

            else:
                # Unexpected token type
                raise ValueError(f"Unexpected token type: {token.type}")

        self.check_expected_args(command_node)
        return command_node

    def _handle_option(self, token: Token, command_node: CommandNode):

        # Check if there's a var-keyword argument to capture unknown options
        has_varkwargs_argument = command_node.cmd_instance.args and any(
            arg.kind == inspect.Parameter.VAR_KEYWORD
            for arg in command_node.cmd_instance.args.values()
        )

        # Check if the option exists in the command
        opt_name = token.value.lstrip("-")
        argument = command_node.cmd_instance.args.get(opt_name, None)
        if argument is None and not has_varkwargs_argument:
            raise ValueError(
                f"Unknown option: {token.value} for command {command_node.cmd_instance.name}"
            )

        if argument is None:  # This means we have a **kwargs argument to capture unknown options
            # select the **kwargs argument
            for arg in command_node.cmd_instance.args.values():
                if arg.kind == inspect.Parameter.VAR_KEYWORD:
                    argument = arg
                    break

        if is_list(argument.type) or argument.kind == inspect.Parameter.VAR_POSITIONAL:
            inner_type = get_list_inner_type(argument.type)
            values = []

            token_is_part_of_the_list = True
            while token_is_part_of_the_list:
                value_token = self._get_next_token()

                token_is_part_of_the_list = (
                    value_token.type == TokenType.VALUE or value_token.type == TokenType.POSITIONAL
                )
                if not token_is_part_of_the_list:
                    # Push back the token for further processing
                    self.tokenizer.push_back(value_token)
                else:
                    # Cast the value to the appropriate inner type
                    value = inner_type(value_token.value) if inner_type else value_token.value
                    values.append(value)

            option_node = ArgumentNode(argument, values)
            command_node.add_child(option_node)

        elif is_dict(argument.type):
            key_type, value_type = get_dict_key_value_types(argument.type)
            dict_value = {}

            # Check if there's already a value for the dict argument
            existing_node = None
            for child in command_node.children:
                if isinstance(child, ArgumentNode) and child.arg_instance.name == argument.name:
                    existing_node = child
                    dict_value = child.value
                    break

            value_token = self._get_next_token()
            if value_token.type != TokenType.VALUE:
                raise ValueError(f"Option {token.value} requires a value")

            # Expect key=value format
            if "=" not in value_token.value:
                raise ValueError(
                    f"Expected key=value format for dict argument {argument.name}, got: {value_token.value}"
                )

            key_str, val_str = value_token.value.split("=", 1)

            # Cast key and value to appropriate types
            key = key_type(key_str) if key_type else key_str
            val = value_type(val_str) if value_type else val_str
            dict_value[key] = val

            if existing_node:
                existing_node.value = dict_value
            else:
                option_node = ArgumentNode(argument, dict_value)
                command_node.add_child(option_node)

        elif argument.kind == inspect.Parameter.VAR_KEYWORD:

            # Check if there's already a value for the dict argument
            existing_node = None
            for child in command_node.children:
                if isinstance(child, ArgumentNode) and child.arg_instance.name == argument.name:
                    existing_node = child
                    dict_value = child.value
                    break

            value_token = self._get_next_token()
            if value_token.type != TokenType.VALUE:
                raise ValueError(f"Option {token.value} requires a value")

            # Assume the **kwargs dictionnary to be of type dict[str, Any]
            value = argument.type(value_token.value) if argument.type else value_token.value

            if existing_node:
                existing_node.value[opt_name] = value
            else:
                option_node = ArgumentNode(argument, {opt_name: value})
                command_node.add_child(option_node)

        elif argument.type != bool:
            # Expected the next token to be a value
            value_token = self._get_next_token()
            if value_token.type != TokenType.VALUE:
                raise ValueError(f"Option {token.value} requires a value")

            # Cast the value to the appropriate type
            value = argument.type(value_token.value) if argument.type else value_token.value

            option_node = ArgumentNode(argument, value)
            command_node.add_child(option_node)

        else:
            # For flags (boolean options)
            if argument.type == bool:
                flag_node = ArgumentNode(
                    argument, True
                )  # TODO: handle false case, store_action, invert? etc
                command_node.add_child(flag_node)

    def _handle_combined_options(self, token, command_node: CommandNode):
        # TODO: implement handling of combined short options
        pass

    def check_expected_args(self, command_node: CommandNode) -> None:
        provided_args = set()
        for child in command_node.children:
            if isinstance(child, ArgumentNode):
                provided_args.add(child.arg_instance.name)

        if command_node.cmd_instance.args is None:
            return

        expected_args = set()
        for arg_name, arg in command_node.cmd_instance.args.items():
            if arg.is_required:
                expected_args.add(arg_name)

        missing_args = expected_args - provided_args
        if missing_args:
            raise ValueError(f"Missing required arguments: {', '.join(missing_args)}")
