from clipy.command import Command


@Command
def greeting(name: str):
    """Greeting the given name"""
    print(f"Hello {name}")


class SubCommand(Command):
    description = "This is a subcommand group"

    @Command
    def subsubcmd1(self):
        """Execute subsubcmd1"""
        print("subsubcmd1 executed")


class NestedCommand(Command):
    subcmd: SubCommand = SubCommand()

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
        return 42

    @Command(name="cmd3")
    def cmd2(self, arg: str, *args):
        """Execute cmd2"""
        print(f"cmd2 executed with {arg}")


class MainCommand(Command):
    def __init__(self):
        super().__init__(name="cli.py")

    @Command
    def subcmd(self, arg1: dict[str, int], arg2: int):
        print(f"subcmd executed with arg1={arg1} and arg2={arg2}")


if __name__ == "__main__":
    cmd = NestedCommand()
    cmd()
