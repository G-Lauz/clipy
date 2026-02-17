from __future__ import annotations

import inspect
from typing import TYPE_CHECKING, List

from ..utils import get_dict_key_value_types, get_list_inner_type, is_dict, is_list
from .error import (
    InvalidArgumentTypeError,
    MissingRequiredArgumentError,
    MissingRequiredValueError,
    ParseError,
    TooManyArgumentsError,
    UnexpectedPositionalArgumentError,
    UnexpectedValueFormatError,
    UnknownArgumentError,
    UnknownTokenTypeError,
)
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

        self.command_tree: List[Command] = []

    def _get_next_token(self):
        self.current_token = self.tokenizer.next()
        return self.current_token

    def _consume_value(self) -> Token:
        """Consume the next token, expecting it to be a value for an option.

        Values arrive as VALUE tokens (from --opt=val syntax) or as
        POSITIONAL tokens (from --opt val syntax). Anything else means
        no value was provided.
        """
        token = self._get_next_token()
        if token.type not in (TokenType.VALUE, TokenType.POSITIONAL):
            raise MissingRequiredValueError(token)
        return token

    def parse(self) -> CommandNode:
        self.tokenizer.reset()

        try:
            command_node = self._recursive_parse(self.root)
        except ParseError as error:
            raise error from error
        finally:
            self.command_tree.append(self.root)

        return command_node

    def _recursive_parse(self, command: Command) -> CommandNode:
        command_node = CommandNode(command)

        num_args = len(command.args) if command.args else 0
        args_parsed = 0

        while self.current_token is None or self.current_token.type != TokenType.END:
            token = self._get_next_token()

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
                if command_node.cmd_instance.is_group:
                    if self._try_handle_subcommand(token, command_node):
                        return command_node

                args_parsed += self._handle_positional(token, command_node, args_parsed, num_args)

            elif token.type == TokenType.END:
                continue

            else:
                # Unexpected token type
                raise UnknownTokenTypeError(token)

        self.check_expected_args(command_node)
        return command_node

    def _try_handle_subcommand(self, token: Token, command_node: CommandNode) -> bool:
        """Try to match the token as a subcommand name.

        If a subcommand is found, recursively parse it and attach it to the
        command node. Returns True if a subcommand was matched, False otherwise.
        """
        sub_cmd = command_node.cmd_instance.subcommands.get(token.value, None)
        if sub_cmd is None:
            return False

        try:
            subcommand_node = self._recursive_parse(sub_cmd)
            command_node.add_child(subcommand_node)
        except ParseError as error:
            raise error from error
        finally:
            self.command_tree.append(sub_cmd)

        return True

    def _handle_positional(
        self, token: Token, command_node: CommandNode, args_parsed: int, num_args: int
    ) -> int:
        """Handle a positional argument token.

        Returns 1 if a regular positional was consumed (to increment the
        caller's counter), or 0 for VAR_POSITIONAL arguments.
        """
        if command_node.cmd_instance.args is None:
            raise UnexpectedPositionalArgumentError(token)

        # check if an argument is a var-positional
        has_varargs_argument = command_node.cmd_instance.args and any(
            arg.kind == inspect.Parameter.VAR_POSITIONAL
            for arg in command_node.cmd_instance.args.values()
        )

        if args_parsed >= num_args and not has_varargs_argument:
            raise TooManyArgumentsError()

        # Get the next expected argument
        arg_names = list(command_node.cmd_instance.args.keys())
        for child in command_node.children:
            if isinstance(child, ArgumentNode):
                if child.arg_instance.name in arg_names:
                    arg_names.remove(child.arg_instance.name)
        arg_name = arg_names[0]

        # Ignore help argument here, which a special case
        # TODO: we should handle colision with help use by the user as parameter name
        if arg_name == "help":
            if len(arg_names) > 1:
                arg_name = arg_names[1]
            else:
                raise UnexpectedPositionalArgumentError(token)

        argument = command_node.cmd_instance.args.get(arg_name)

        if argument is None:
            raise UnexpectedPositionalArgumentError(token)

        if argument.kind == inspect.Parameter.VAR_POSITIONAL:
            try:
                values = [argument.type(token.value) if argument.type else token.value]
            except (ValueError, TypeError) as error:
                raise InvalidArgumentTypeError(
                    argument.type.__name__ if argument.type else "str", token
                ) from error

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
                    try:
                        value = (
                            argument.type(value_token.value) if argument.type else value_token.value
                        )
                    except (ValueError, TypeError) as error:
                        raise InvalidArgumentTypeError(
                            argument.type.__name__ if argument.type else "str", value_token
                        ) from error
                    values.append(value)

            option_node = ArgumentNode(argument, values)
            command_node.add_child(option_node)
            return 0

        # Cast the value to the appropriate type
        try:
            value = argument.type(token.value) if argument.type else token.value
        except (ValueError, TypeError) as error:
            raise InvalidArgumentTypeError(
                argument.type.__name__ if argument.type else "str", token
            ) from error
        argument_node = ArgumentNode(argument, value)
        command_node.add_child(argument_node)
        return 1

    def _handle_option(self, token: Token, command_node: CommandNode):

        # Check if there's a var-keyword argument to capture unknown options
        has_varkwargs_argument = command_node.cmd_instance.args and any(
            arg.kind == inspect.Parameter.VAR_KEYWORD
            for arg in command_node.cmd_instance.args.values()
        )

        # Check if the option exists in the command
        opt_name = token.value.lstrip("-")
        argument = None
        if command_node.cmd_instance.args is not None:
            argument = command_node.cmd_instance.args.get(opt_name, None)

        if argument is None and not has_varkwargs_argument:
            raise UnknownArgumentError(token)

        if argument is None:  # This means we have a **kwargs argument to capture unknown options
            # select the **kwargs argument
            if command_node.cmd_instance.args is not None:
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

            value_token = self._consume_value()
            if "=" not in value_token.value:
                raise UnexpectedValueFormatError("key=value", value_token)

            key_str, val_str = value_token.value.split("=", 1)

            # Cast key and value to appropriate types
            key = key_type(key_str) if key_type else key_str
            try:
                val = value_type(val_str) if value_type else val_str
            except (ValueError, TypeError) as error:
                raise InvalidArgumentTypeError(
                    value_type.__name__ if value_type else "str", value_token
                ) from error

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

            value_token = self._consume_value()

            # Assume the **kwargs dictionary to be of type dict[str, Any]
            try:
                value = argument.type(value_token.value) if argument.type else value_token.value
            except (ValueError, TypeError) as error:
                raise InvalidArgumentTypeError(
                    argument.type.__name__ if argument.type else "str", value_token
                ) from error

            if existing_node:
                existing_node.value[opt_name] = value
            else:
                option_node = ArgumentNode(argument, {opt_name: value})
                command_node.add_child(option_node)

        elif argument.type != bool:
            # Expected the next token to be a value
            value_token = self._consume_value()

            # Cast the value to the appropriate type
            try:
                value = argument.type(value_token.value) if argument.type else value_token.value
            except (ValueError, TypeError) as error:
                raise InvalidArgumentTypeError(
                    argument.type.__name__ if argument.type else "str", value_token
                ) from error

            option_node = ArgumentNode(argument, value)
            command_node.add_child(option_node)

        else:
            # For flags (boolean options)
            flag_value = True

            # Peek at the next token: if it's a boolean literal, consume it
            # as the explicit value for this flag.
            next_token = self._get_next_token()
            if next_token.type in (
                TokenType.VALUE,
                TokenType.POSITIONAL,
            ) and next_token.value.lower() in ("true", "false", "1", "0"):
                flag_value = next_token.value.lower() in ("true", "1")
            else:
                # Not a boolean literal - push back for further processing
                self.tokenizer.push_back(next_token)

            flag_node = ArgumentNode(argument, flag_value)
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
        missing_args = missing_args - {"help"}
        if missing_args and "help" not in provided_args:
            raise MissingRequiredArgumentError(missing_args)
