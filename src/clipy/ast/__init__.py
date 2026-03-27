"""AST-based parsing and execution pipeline for CLI argument processing."""

from __future__ import annotations

from .nodes import ArgumentNode, CommandNode
from .parser import Parser
from .processor import ASTProcessor, CommandExecutor

__all__ = [
    "CommandNode",
    "ArgumentNode",
    "Parser",
    "ASTProcessor",
    "CommandExecutor",
]
