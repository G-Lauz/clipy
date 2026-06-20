"""
Example of creating CLI commands with typed arguments,
including collections such as lists and dictionaries,
as well as variable-length arguments and keyword arguments.
"""

import clipy


class TypedCommand(clipy.Command):
    """
    A collection of typed CLI commands
    """

    @clipy.Command
    def cmd1(self, arg1, arg2: str, arg3: int, arg4: float, arg5: bool = False):
        """
        A command with various typed arguments

        Args:
            arg1: A positional argument without type annotation
            arg2: A required string argument
            arg3: A required integer argument
            arg4: A required float argument
            arg5: An optional boolean flag
        """
        print(f"arg1={arg1}, arg2={arg2}, arg3={arg3}, arg4={arg4}, arg5={arg5}")

    @clipy.Command
    def cmd2(self, arg: list[str]):
        """
        A command with a list argument

        Args:
            arg: A list of strings
        """
        print(f"arg={arg}")

    @clipy.Command
    def cmd3(self, *args):
        """
        A command with variable-length integer arguments

        Args:
            *args: A variable number of integer arguments
        """
        print(f"args={args}")

    @clipy.Command
    def cmd4(self, arg: dict[str, int]):
        """
        A command with a dictionary argument

        Args:
            arg: A dictionary mapping strings to integers
        """
        print(f"arg={arg}")

    @clipy.Command
    def cmd5(self, **kwargs):
        """
        A command with variable-length keyword arguments

        Args:
            **kwargs: A variable number of keyword arguments mapping strings to strings
        """
        print(f"kwargs={kwargs}")

    @clipy.Command
    def cmd6(self, *args, **kwargs):
        """
        A command with untyped variable-length arguments

        Args:
            *args: A variable number of positional arguments
            **kwargs: A variable number of keyword arguments
        """
        print(f"args={args}, kwargs={kwargs}")


if __name__ == "__main__":
    cmd = TypedCommand()
    cmd()
