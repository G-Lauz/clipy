import sys
from typing import List

from clipy.ast.parser import Parser
from clipy.ast.tokenizer import Tokenizer
from clipy.command import Command


def pretty_print(node: "CommandNode", indent: int = 0):
    from clipy.ast import ArgumentNode, CommandNode

    node_name = None
    if isinstance(node, CommandNode):
        node_name = "Command: " + node.cmd_instance.name
    elif isinstance(node, ArgumentNode):
        node_name = "Argument: " + node.arg_instance.name

    print("    " * indent + node_name)

    if isinstance(node, CommandNode):
        for child in node.children:
            pretty_print(child, indent + 1)


@Command
def greeting(name: str):
    """Greeting the given name"""
    print(f"Hello {name}")


class SubCommand(Command):
    @Command
    def subsubcmd1(self):
        """Execut subsubcmd1"""
        print("subsubcmd1 executed")


class NestedCommand(Command):
    subcmd: SubCommand = SubCommand()

    @Command
    def cmd1(self, arg: str, arg2: int = 42):
        """Execut cmd1"""
        print(f"cmd1 executed with {arg}")

    @Command(name="cmd3")
    def cmd2(self, arg: str):
        """Execut cmd2"""
        print(f"cmd2 executed with {arg}")


@Command(name="named_cmd")
def func(arg1: int, **arg2):
    return arg1, arg2


if __name__ == "__main__":
    # toeknizer = Tokenizer(sys.argv[1:])
    # tokens = toeknizer.get_tokens()
    # for token in tokens:
    #     print(token)

    # parser = Parser(NestedCommand(), sys.argv[1:])
    # ast_root = parser.parse()

    # pretty_print(ast_root)

    # cmd = NestedCommand()
    # cmd()

    # greeting()

    result = func()
    print(f"func returned: {result}")
