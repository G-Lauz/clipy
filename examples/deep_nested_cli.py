"""
Example of creating a CLI command with deeply nested subcommands and custom command names.
"""

import clipy


class SubCommand(clipy.Command):
    """This is a subcommand group."""

    @clipy.Command
    def subsubcmd(self):
        """Execute subsubcmd"""
        print("subsubcmd executed")


class NamedToBeReplaceCommand(clipy.Command):
    """
    A command with a custom name and nested subcommands.
    """

    subcmd: SubCommand = SubCommand()

    def __init__(self):
        super().__init__(name="nestedcmd")

    @clipy.Command(name="cmd")
    def cmd_name_to_be_replaced(self, arg1):
        """
        A command with a custom name

        Args:
            arg1: An argument for the command
        """
        print(f"cmd executed with arg1={arg1}")


if __name__ == "__main__":
    cmd = NamedToBeReplaceCommand()
    cmd()
