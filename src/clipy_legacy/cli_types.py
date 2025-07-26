import dataclasses
from typing import Any, Dict, List, Optional


@dataclasses.dataclass
class OptionDefinition:
    """
    Definition of a command option.

    Attributes:
    :param name: Name of the option.
    :param kwargs: Keyword arguments to pass to the `add_argument` method of `argparse.ArgumentParser`.
    :param positional: Whether the option is a positional argument. Default is False.
    """

    name: str
    kwargs: Dict[str, Any]
    positional: bool = False


@dataclasses.dataclass
class CommandDefinition:
    """
    Definition of a command.

    Attributes:
    :param name: Name of the command.
    :param usage: Usage string for the command.
    :param description: Description string for the command.
    :param options: List of `OptionDefinition` instances for the command. Default is an empty list.
    :param subcommands: List of `CommandDefinition` instances for subcommands. Default is None.
    """

    name: str
    usage: str = None
    description: str = None
    options: List[OptionDefinition] = None
    subcommands: Optional[List["CommandDefinition"]] = None

    def __post_init__(self):
        if self.options is None:
            self.options = []

    def register_option(self, option: OptionDefinition):
        self.options.append(option)

    def register_subcommand(self, subcommand: "CommandDefinition"):
        self.subcommands.append(subcommand)
