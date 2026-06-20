"""
Example of creating a CLI command using a simple function.
"""

import clipy


@clipy.Command
def greeting(name: str):
    """
    Greeting the given name

    Args:
        name: The name to greet
    """
    print(f"Hello There!\nGeneral {name}!")


if __name__ == "__main__":
    greeting()  # pylint: disable=no-value-for-parameter
