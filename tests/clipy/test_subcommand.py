from unittest.mock import patch

import pytest

import clipy


def test_subcommand_no_args():
    class MainCommand(clipy.Command):
        @clipy.Command
        def subcmd(self):
            pass

    with patch("sys.argv", ["test.py"]):
        cmd = MainCommand()
        cmd()  # pylint: disable=missing-kwoa


def test_subcommand_with_args():
    class MainCommand(clipy.Command):
        @clipy.Command
        def subcmd(self, option1: int, option2: str = "default"):
            return option1, option2

    with patch("sys.argv", ["test.py", "subcmd", "--option1", "42"]):
        cmd = MainCommand()
        result = cmd()  # pylint: disable=no-value-for-parameter
        assert result == (42, "default")

    with patch("sys.argv", ["test.py", "subcmd", "42", "hello"]):
        cmd = MainCommand()
        result = cmd()  # pylint: disable=no-value-for-parameter
        assert result == (42, "hello")


def test_named_subcommand():
    class MainCommand(clipy.Command):
        @clipy.Command(name="custom_subcmd")
        def subcmd(self):
            pass

    with patch("sys.argv", ["test.py", "custom_subcmd"]):
        cmd = MainCommand()
        cmd()  # pylint: disable=missing-kwoa

    with patch("sys.argv", ["test.py", "subcmd"]):
        cmd = MainCommand()
        with pytest.raises(SystemExit):
            cmd()  # pylint: disable=missing-kwoa


def test_subcommand_description():
    class MainCommand(clipy.Command):
        @clipy.Command
        def subcmd(self):
            """
            This is a subcommand description.
            """
            pass

    with patch("sys.argv", ["test.py", "subcmd"]):
        cmd = MainCommand()
        subcmd = cmd.subcmd
        assert subcmd.description == "This is a subcommand description."


def test_subcommand_usage():
    class MainCommand(clipy.Command):
        @clipy.Command
        def subcmd(self, option1: int, option2: str = "default"):
            pass

    with patch("sys.argv", ["test.py", "subcmd"]):
        cmd = MainCommand()
        subcmd = cmd.subcmd
        assert subcmd.usage == "subcmd [--option1 <int>] [--option2 <str>]"


def test_command_usage_with_subcommand():
    class MainCommand(clipy.Command):
        @clipy.Command
        def subcmd1(self, option1: int, option2: str = "default"):
            pass

        @clipy.Command
        def subcmd2(self):
            pass

    with patch("sys.argv", ["test.py", "subcmd"]):
        cmd = MainCommand()
        assert cmd.usage == "maincommand { subcmd1, subcmd2 }"


def test_subcommand_args_help():
    class MainCommand(clipy.Command):
        @clipy.Command
        def subcmd(self, option1: int, option2: str):
            """
            This is a test subcommand.

            Args:
                option1: An integer argument.
                option2:
                    A string argument. Defaults to "default".
            """
            pass

    with patch("sys.argv", ["test.py", "subcmd"]):
        cmd = MainCommand()
        subcmd = cmd.subcmd
        assert subcmd.args["option1"].help == "An integer argument."
        assert subcmd.args["option2"].help == 'A string argument. Defaults to "default".'


def test_init_attribute_assignment():
    class MainCommand(clipy.Command):
        def __init__(self):
            super().__init__()
            self.test = "example"

        @clipy.Command
        def subcmd(self):
            return self.test

    with patch("sys.argv", ["test.py", "subcmd"]):
        cmd = MainCommand()
        result = cmd()  # pylint: disable=no-value-for-parameter
        assert result == "example"


def test_nested_subcommand():
    class SubCommand(clipy.Command):
        @clipy.Command
        def subsubcmd(self, arg: str):
            return f"subsubcmd executed with {arg}"

    class MainCommand(clipy.Command):
        subcmd: SubCommand = SubCommand()

    with patch("sys.argv", ["test.py", "subcmd", "subsubcmd", "--arg", "test"]):
        cmd = MainCommand()
        result = cmd()  # pylint: disable=no-value-for-parameter
        assert result == "subsubcmd executed with test"


def test_nested_subcommand_argument_types():
    """Argument types (list, positional, *args, **kwargs) work through nested subcommands."""

    class SubCommand(clipy.Command):
        @clipy.Command
        def list_cmd(self, items: list[str], count: int):
            return items, count

        @clipy.Command
        def positional_cmd(self, arg1: int, arg2: str = "default"):
            return arg1, arg2

        @clipy.Command
        def varargs_cmd(self, arg1: int, *rest):
            return arg1, rest

        @clipy.Command
        def kwargs_cmd(self, arg1: int, **opts):
            return arg1, opts

    class MainCommand(clipy.Command):
        sub: SubCommand = SubCommand()

    with patch(
        "sys.argv",
        ["test.py", "sub", "list_cmd", "--items", "a", "b", "c", "--count", "3"],
    ):
        cmd = MainCommand()
        assert cmd() == (["a", "b", "c"], 3)

    with patch("sys.argv", ["test.py", "sub", "positional_cmd", "42"]):
        cmd = MainCommand()
        assert cmd() == (42, "default")

    with patch("sys.argv", ["test.py", "sub", "varargs_cmd", "42", "x", "y"]):
        cmd = MainCommand()
        assert cmd() == (42, ("x", "y"))

    with patch("sys.argv", ["test.py", "sub", "kwargs_cmd", "42", "--key1", "v1", "--key2", "v2"]):
        cmd = MainCommand()
        assert cmd() == (42, {"key1": "v1", "key2": "v2"})


def test_unknown_subcommand():
    class MainCommand(clipy.Command):
        @clipy.Command
        def subcmd(self):
            pass

    with patch("sys.argv", ["test.py", "unknown"]):
        cmd = MainCommand()
        assert False
        with pytest.raises(SystemExit):
            cmd()  # pylint: disable=missing-kwoa


def test_unknown_argument():
    class MainCommand(clipy.Command):
        @clipy.Command
        def subcmd(self):
            pass

    with patch("sys.argv", ["test.py", "subcmd", "--unknown", "value"]):
        cmd = MainCommand()
        assert False
        with pytest.raises(SystemExit):
            cmd()  # pylint: disable=missing-kwoa
