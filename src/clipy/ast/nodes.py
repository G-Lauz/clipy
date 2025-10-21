from __future__ import annotations

import abc
from typing import TYPE_CHECKING, Any, List

if TYPE_CHECKING:
    from clipy import Argument, Command

    from .processor import ASTProcessor


class ASTNode(abc.ABC):
    @abc.abstractmethod
    def accept(self, visitor: ASTProcessor):
        pass


class CommandNode(ASTNode):
    cmd_instance: Command
    children: List[ASTNode]

    def __init__(self, cmd_instance: Command):
        self.cmd_instance = cmd_instance
        self.children = []

    def add_child(self, child: ASTNode):
        self.children.append(child)

    def accept(self, visitor: ASTProcessor) -> Any:
        return visitor.process_command(self)


class ArgumentNode(ASTNode):
    arg_instance: Argument

    def __init__(self, arg_instance: Argument, value: Any = None):
        self.arg_instance = arg_instance
        self.value = value

    def accept(self, visitor: ASTProcessor) -> Any:
        return visitor.process_argument(self)
