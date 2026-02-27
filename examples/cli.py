from clipy.command import Command


@Command
def greeting(name: str):
    """Greeting the given name"""
    print(f"Hello {name}")


class SubCommand(Command):
    """This is a subcommand group"""

    def __call__(self, arg1: int):
        """
        Docstring for __call__

        Args:
            arg1: An integer argument for the subcommand
        """
        print(f"SubCommand executed with arg1={arg1}")

    @Command
    def subsubcmd1(self):
        """Execute subsubcmd1"""
        print("subsubcmd1 executed")


class SuperSubCommand(Command):
    """This super command is both a command and a group."""

    def __call__(self):
        print("This super command is both a command and a group.")

    @Command
    def subsubcmd2(self):
        """Execute subsubcmd2"""
        print("subsubcmd2 executed")


class NestedCommand(Command):
    subcmd: SubCommand = SubCommand()
    subcmd2: SuperSubCommand = SuperSubCommand()

    def __init__(self):
        super().__init__()
        self.test = "example"

    @Command
    def cmd1(self, pos1, pos2, arg: str, arg2: int = 42):
        """
        Execute cmd1

        Args:
            pos1: The first positional argument
            pos2: The second positional argument
            arg: A required string argument
            arg2: An optional integer argument
        """
        print(f"cmd1 executed with {arg}")
        print(self.test)
        return 42

    @Command(name="cmd3")
    def cmd2(self, arg: str, *args):
        """Execute cmd2"""
        print(f"cmd2 executed with {arg}")

    # @Command
    # def cmd3(self):
    #     """Execute cmd3"""
    #     assert (
    #         False
    #     ), "Should resolve name conflict and raise an error instead of executing this method"
    #     print("cmd3 executed")

    @Command
    def cmd4(self, alist: list[str] = [], flag: bool = False):
        """Execute cmd4"""
        print(f"cmd4 executed with flag={flag} and alist={alist}")

    # @Command
    # def cmd5(self, arg1, help: str):
    #     """Execute cmd5"""
    #     print(f"cmd5 executed with arg1={arg1}")


class MainCommand(Command):
    def __init__(self):
        super().__init__(name="cli.py")

    @Command
    def subcmd(self, arg1: dict[str, int], arg2: int):
        print(f"subcmd executed with arg1={arg1} and arg2={arg2}")


if __name__ == "__main__":
    cmd = NestedCommand()
    cmd()
