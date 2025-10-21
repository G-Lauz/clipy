from __future__ import annotations

import abc
import inspect
from typing import Dict

from .nodes import ArgumentNode, CommandNode


class ASTProcessor(abc.ABC):
    """
    Abstract base class for processing AST nodes.
    Following the Visitor design pattern.
    """

    @abc.abstractmethod
    def process_command(self, node: CommandNode):
        pass

    @abc.abstractmethod
    def process_argument(self, node: ArgumentNode):
        pass


class CommandExecutor(ASTProcessor):
    """
    Concrete AST processor that executes commands represented by the AST nodes.
    """

    def process_command(self, node: CommandNode):
        print(f"Executing command: {node.cmd_instance.name}")

        parsed_args: Dict[str, ArgumentNode] = {}
        positional_args = []
        kwargs = {}

        for child in node.children:
            if isinstance(child, CommandNode):
                child.accept(self)
            elif isinstance(child, ArgumentNode):
                if child.arg_instance.kind == inspect.Parameter.VAR_POSITIONAL:
                    if isinstance(child.value, list):
                        positional_args.extend(child.value)
                    else:
                        positional_args.append(child.value)
                elif child.arg_instance.kind == inspect.Parameter.VAR_KEYWORD:
                    if isinstance(child.value, dict):
                        for key, value in child.value.items():
                            kwargs[key] = value
                else:
                    parsed_args[child.arg_instance.name] = child.value

        print(parsed_args)
        print(positional_args)
        print(kwargs)

        ordered_args = []
        for name in node.cmd_instance.signature.parameters.keys():
            if name in parsed_args:
                ordered_args.append(parsed_args[name])
        ordered_args.extend(positional_args)

        if not node.cmd_instance.is_group:

            # Check if it's a bound method (with self or cls)
            func = node.cmd_instance.func
            signature = node.cmd_instance.signature

            params = list(signature.parameters.values())
            if params and params[0].name in ("self", "cls"):
                # Create a new signature without the first parameter (self/cls)
                signature = inspect.Signature(parameters=params[1:])

                # Use the bound method
                func = func.__get__(node.cmd_instance, type(node.cmd_instance))

            binding = signature.bind(*ordered_args, **kwargs)
            binding.apply_defaults()
            return func(*binding.args, **binding.kwargs)

    def process_argument(self, node: ArgumentNode):
        print(f"Processing argument with value: {node.value}")
