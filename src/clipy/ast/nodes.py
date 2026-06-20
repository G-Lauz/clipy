"""AST node definitions for the CLI argument parser."""

from __future__ import annotations

import abc
from typing import TYPE_CHECKING, Any, List

if TYPE_CHECKING:
    from clipy import Argument, Command

    from .processor import ASTProcessor


class ASTNode(abc.ABC):
    """
    Abstract base class for all nodes in the CLI parse tree.

    Implements the Visitor pattern by requiring subclasses to define
    :meth:`accept`.
    """

    @abc.abstractmethod
    def accept(self, visitor: ASTProcessor):
        """
        Accept a visitor and dispatch to the appropriate processing method.

        Args:
            visitor: An :class:`.ASTProcessor` instance that will process
                this node.

        Returns:
            Any: The result produced by the visitor.
        """
        pass


class CommandNode(ASTNode):
    """
    AST node representing a parsed command invocation.

    Attributes:
        cmd_instance: The :class:`.Command` that this node corresponds to.
        children: Ordered list of child nodes (subcommand or argument nodes).
    """

    cmd_instance: Command
    children: List[ASTNode]

    def __init__(self, cmd_instance: Command):
        """
        Args:
            cmd_instance: The :class:`.Command` bound to this node.
        """
        self.cmd_instance = cmd_instance
        self.children = []

    def add_child(self, child: ASTNode):
        """
        Append *child* to the list of child nodes.

        Args:
            child: The :class:`.ASTNode` to add.
        """
        self.children.append(child)

    def accept(self, visitor: ASTProcessor) -> Any:
        """
        Dispatch to :meth:`.ASTProcessor.process_command`.

        Args:
            visitor: The visitor to dispatch to.

        Returns:
            Any: The value returned by the visitor.
        """
        return visitor.process_command(self)


class ArgumentNode(ASTNode):
    """
    AST node representing a parsed argument and its value.

    Attributes:
        arg_instance: The :class:`.Argument` descriptor for this node.
        value: The parsed, type-cast value for the argument.
    """

    arg_instance: Argument

    def __init__(self, arg_instance: Argument, value: Any = None):
        """
        Args:
            arg_instance: The :class:`.Argument` this node represents.
            value: The parsed value; ``None`` when no value was provided.
        """
        self.arg_instance = arg_instance
        self.value = value

    def accept(self, visitor: ASTProcessor) -> Any:
        """
        Dispatch to :meth:`.ASTProcessor.process_argument`.

        Args:
            visitor: The visitor to dispatch to.

        Returns:
            Any: The value returned by the visitor.
        """
        return visitor.process_argument(self)
