from __future__ import annotations

import abc
import inspect
from typing import Any, Dict, List, Tuple

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
        parsed_args: Dict[str, ArgumentNode] = {}
        positional_args = []
        kwargs = {}

        # subcommand_return = None
        help_flag = False
        subcommand_path: List[Tuple[CommandNode, Any]] = []

        for child in node.children:
            if isinstance(child, CommandNode):
                path, help_flag = child.accept(self)
                subcommand_path.extend(path)
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

        ordered_args = []
        named_kwargs = {}
        if node.cmd_instance.signature is not None:
            use_keyword = False
            for name, param in node.cmd_instance.signature.parameters.items():
                if name in ("self", "cls"):
                    continue
                if param.kind == inspect.Parameter.VAR_POSITIONAL:
                    use_keyword = True
                    continue
                if param.kind == inspect.Parameter.VAR_KEYWORD:
                    continue
                if name not in parsed_args:
                    if not use_keyword:
                        # A gap in positional args: all subsequent args must be keyword
                        use_keyword = True
                    continue
                if use_keyword or param.kind == inspect.Parameter.KEYWORD_ONLY:
                    named_kwargs[name] = parsed_args[name]
                else:
                    ordered_args.append(parsed_args[name])

        ordered_args.extend(positional_args)
        named_kwargs.update(kwargs)

        # Check for help flag
        if "help" in parsed_args and parsed_args["help"]:
            help_flag = True
            subcommand_path.append((node.cmd_instance, None))
            return subcommand_path, help_flag

        # Determine if we should execute the function
        # We execute if:
        # 1. It's not a group (always has a function)
        # 2. It IS a group, but has a function AND no subcommand was invoked (leaf execution of a hybrid group)
        has_subcommand = any(isinstance(child, CommandNode) for child in node.children)
        should_execute = (not node.cmd_instance.is_group) or (
            node.cmd_instance.func is not None and not has_subcommand
        )

        if should_execute:

            # Check if it's a bound method (with self or cls)
            func = node.cmd_instance.func
            signature = node.cmd_instance.signature

            params = list(signature.parameters.values())
            if params and params[0].name in ("self", "cls"):
                # Create a new signature without the first parameter (self/cls)
                signature = inspect.Signature(parameters=params[1:])

                # Use the bound method
                func = func.__get__(node.cmd_instance, type(node.cmd_instance))

            binding = signature.bind(*ordered_args, **named_kwargs)
            binding.apply_defaults()
            return_value = func(*binding.args, **binding.kwargs)

            subcommand_path.append((node.cmd_instance, return_value))
            return subcommand_path, help_flag

        subcommand_path.append((node.cmd_instance, None))
        return subcommand_path, help_flag

    def process_argument(self, node: ArgumentNode):
        raise NotImplementedError("Argument processing is not implemented.")
