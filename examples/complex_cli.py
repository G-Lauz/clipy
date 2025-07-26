import abc
import argparse
import inspect


def command(func):
    def wrapper(*args, **kwargs):
        parser = argparse.ArgumentParser(description=func.__doc__)
        signature = func.__annotations__
        for name, type_ in signature.items():
            if name != "return":
                parser.add_argument(
                    f"--{name}",
                    type=type_,
                    required=True,
                    help=f"Argument {name} of type {type_.__name__}",
                )

        parsed_args = parser.parse_args()

        return func(**{k: v for k, v in vars(parsed_args).items() if v is not None})

    return wrapper


@command
def greeting(name: str, times: int = 1):
    for _ in range(times):
        print(f"Hello, {name}!")


class SubCommand(abc.ABC):
    """
    Decorator to mark methods as command methods.
    This is used to identify which methods should be treated as commands in a command group.
    """

    def __init__(self, func):
        self.func = func

    def __call__(self, *args, **kwargs):
        return self.func(self, *args, **kwargs)


class CommandGroup(abc.ABC):
    name: str = None

    def __init__(self, name: str = None):
        """
        Initialize the command group with an optional name.
        If no name is provided, it defaults to the class name.
        """
        if name is None:
            self.name = self.__class__.__name__.lower()
        else:
            self.name = name

    def _get_subcommands(self):
        """Retrieve all methods decorated with @command_method in the class."""
        subcommands = {}
        for attr_name in dir(self):
            attr = getattr(self, attr_name)

            if isinstance(attr, SubCommand):
                subcommands[attr_name] = attr
        return subcommands

    def _build_command_tree(self):
        """Build a tree structure of commands and subcommands."""
        command_tree = {}
        subcommands = self._get_subcommands()

        for name, command in subcommands.items():
            if isinstance(command, CommandGroup):
                command_tree[name] = command._build_command_tree()
            else:
                command_tree[name] = command

        return command_tree

    def _pretty_print_tree(self, tree, indent=0):
        for key, value in tree.items():
            if isinstance(value, dict):
                print("  " * indent + str(key) + ":")
                self._pretty_print_tree(value, indent + 1)
            else:
                print("  " * indent + str(key))

    def _build_parser(self, tree, parser=None, parent_dest=None):
        """
        Build the argument parser from the command tree
        """
        if parser is None:
            parser = argparse.ArgumentParser(
                prog=self.name, description=f"Commands for {self.name}"
            )

        # subparsers = parser.add_subparsers(dest='command', required=True)
        # Use different dest names for different levels
        if parent_dest is None:
            dest_name = "command"
        else:
            dest_name = f"{parent_dest}_subcommand"

        subparsers = parser.add_subparsers(dest=dest_name, required=True)

        # print("-" * 40)
        # print(parser)
        # self._pretty_print_tree(tree, indent=1)
        # print("-" * 40)

        for name, command in tree.items():
            if isinstance(command, dict):
                subparser = subparsers.add_parser(name, help=f"Subcommands of {self.name}")
                self._build_parser(command, subparser, parent_dest=dest_name)
            else:
                subparser = subparsers.add_parser(name, help=command.func.__doc__)
                signature = inspect.signature(command.func)
                params = list(signature.parameters.values())[1:]  # Skip first parameter (self)
                for param in params:
                    if param.default is not param.empty:
                        subparser.add_argument(
                            f"--{param.name}",
                            type=param.annotation,
                            default=param.default,
                            help=f"Argument {param.name} of type {param.annotation.__name__}",
                        )
                    else:
                        subparser.add_argument(
                            f"--{param.name}",
                            type=param.annotation,
                            required=True,
                            help=f"Argument {param.name} of type {param.annotation.__name__}",
                        )

        return parser

    def __call__(self, *args, **kwargs):
        print(f"Executing command group: {self.name}")

        print("-" * 40)
        print("Command Tree:")
        cmd_tree = self._build_command_tree()
        self._pretty_print_tree(cmd_tree, indent=1)
        print("-" * 40)

        parser = self._build_parser(cmd_tree)
        parsed_args = parser.parse_args()

        # print(parser)
        # print(f"Parsed: {parsed_args}")

        self._execute_command(cmd_tree, parsed_args)

    def _execute_command(self, tree, args, level=0):
        """Execute the command based on the parsed arguments."""
        # Determine the command attribute name based on the level
        if level == 0:
            command_attr = "command"
            subcommand_attr = "command_subcommand"
        else:
            command_attr = f"command{'_subcommand' * (level + 1)}"
            subcommand_attr = f"command{'_subcommand' * (level + 2)}"

        if not hasattr(args, command_attr) or getattr(args, command_attr) is None:
            return

        command_name = getattr(args, command_attr)

        if command_name in tree:
            cmd = tree[command_name]

            if isinstance(cmd, dict):
                # This is a subcommand group, look for the subcommand
                if hasattr(args, subcommand_attr):
                    subcommand_name = getattr(args, subcommand_attr)

                    # Find the subgroup instance and execute the subcommand
                    for attr_name in dir(self):
                        attr = getattr(self, attr_name)
                        if isinstance(attr, CommandGroup) and attr.name == command_name:
                            if subcommand_name in cmd:
                                subcmd = cmd[subcommand_name]
                                if isinstance(subcmd, dict):
                                    # Further nested command - recursively handle
                                    attr._execute_command(subcmd, args, level + 1)
                                else:
                                    # Direct subcommand - execute it
                                    # Create args for the subcommand, excluding all command attributes
                                    exclude_attrs = [
                                        attr_name
                                        for attr_name in vars(args).keys()
                                        if attr_name.startswith("command")
                                    ]
                                    subcommand_args = {
                                        k: v
                                        for k, v in vars(args).items()
                                        if k not in exclude_attrs
                                    }
                                    subcmd.func(attr, **subcommand_args)
                            break
            else:
                # This is a direct command, execute it
                # Exclude all command-related attributes
                exclude_attrs = [
                    attr_name for attr_name in vars(args).keys() if attr_name.startswith("command")
                ]
                command_args = {k: v for k, v in vars(args).items() if k not in exclude_attrs}
                cmd.func(self, **command_args)


class SubSubGroup(CommandGroup, SubCommand):
    @SubCommand
    def command4(self, arg1: str, arg2: int):
        """Command 4 of the sub-subgroup."""
        print(f"Command 4 executed with arg1={arg1} and arg2={arg2}")


class SubGroup(CommandGroup, SubCommand):
    subsubgroup: SubSubGroup = SubSubGroup()

    @SubCommand
    def command3(self, arg1: str):
        """Command 3 of the subgroup."""
        print(f"Command 3 executed with arg1={arg1}")


class GlobalGroup(CommandGroup):

    subgroup: SubGroup = SubGroup()

    def internal_method(self):
        """Internal method that should not be exposed."""
        print("This is an internal method.")

    @SubCommand
    def command1(self, arg1: str, arg2: int):
        """Command 1 of the group."""
        print(f"Command 1 executed with arg1={arg1} and arg2={arg2}")

    @SubCommand
    def command2(self, arg1: str, arg2: float):
        """Command 2 of the group."""
        print(f"Command 2 executed with arg1={arg1} and arg2={arg2}")


if __name__ == "__main__":
    # greeting() # pylint: disable=no-value-for-parameter

    group = GlobalGroup()
    group()
