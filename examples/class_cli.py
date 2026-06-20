"""
Example of creating a CLI command using a class.
This allow commands to maintain state and have more complex behavior.
"""

import clipy


class GreetingCommand(clipy.Command):
    def __call__(self, name: str):
        """
        Greet the given name

        Args:
            name: The name to greet
        """
        print(f"Hello There!\nGeneral {name}!")


if __name__ == "__main__":
    cmd = GreetingCommand()
    cmd()
