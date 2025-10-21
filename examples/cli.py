from clipy.command import Command


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


class MainCommand(Command):
    @Command
    def subcmd(self, arg1: dict[str, int], arg2: int):
        print(f"subcmd executed with arg1={arg1} and arg2={arg2}")


if __name__ == "__main__":
    cmd = MainCommand()
    cmd()
