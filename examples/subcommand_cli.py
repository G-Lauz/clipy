"""
Example of creating a CLI command with subcommands using a class-based approach.
This allows for grouping related commands together and maintaining shared state if needed.
"""

import clipy


class SalutationsCommand(clipy.Command):
    def __call__(self, name: str):
        """
        Generic salutation to the given name

        Args:
            name: The name to greet
        """
        print(f"Generic salutation to {name}!")

    @clipy.Command
    def greeting(self, name: str):
        """
        Greet the given name

        Args:
            name: The name to greet
        """
        print(f"Hello There!\nGeneral {name}!")

    @clipy.Command
    def farewell(self, name: str):
        """
        Say goodbye to the given name

        Args:
            name: The name to say goodbye to
        """
        print(f"Goodbye, {name}!")


if __name__ == "__main__":
    cmd = SalutationsCommand()
    cmd()
