from typing import Dict, List
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


def test_nested_subcommand_no_args():
    class SubCommand(clipy.Command):
        @clipy.Command
        def subsubcmd(self):
            pass

    class MainCommand(clipy.Command):
        subcmd: SubCommand = SubCommand()

    with patch("sys.argv", ["test.py", "subcmd", "subsubcmd"]):
        cmd = MainCommand()
        cmd()  # pylint: disable=missing-kwoa


def test_subcommand_args_no_type():
    class MainCommand(clipy.Command):
        @clipy.Command
        def subcmd(self, option1, option2):
            return int(option1), option2

    with patch("sys.argv", ["test.py", "subcmd", "--option1", "42", "--option2", "hello"]):
        cmd = MainCommand()
        result = cmd()  # pylint: disable=no-value-for-parameter
        assert result == (42, "hello")


def test_nested_subcommand_args():
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


def test_subcommand_optional_args():
    class MainCommand(clipy.Command):
        @clipy.Command
        def subcmd(self, option1: int, option2: str = None):
            return option1, option2

    with patch("sys.argv", ["test.py", "subcmd", "--option1", "42"]):
        cmd = MainCommand()
        result = cmd()  # pylint: disable=no-value-for-parameter
        assert result == (42, None)


def test_subcommand_default_args():
    class MainCommand(clipy.Command):
        @clipy.Command
        def subcmd(self, option1: int, option2: str = "default"):
            return option1, option2

    with patch("sys.argv", ["test.py", "subcmd", "--option1", "42"]):
        cmd = MainCommand()
        result = cmd()  # pylint: disable=no-value-for-parameter
        assert result == (42, "default")


def test_nested_subcommand_default_args():
    class SubCommand(clipy.Command):
        @clipy.Command
        def subsubcmd(self, arg1: str, arg2: int = 100):
            return arg1, arg2

    class MainCommand(clipy.Command):
        subcmd: SubCommand = SubCommand()

    with patch("sys.argv", ["test.py", "subcmd", "subsubcmd", "--arg1", "hello"]):
        cmd = MainCommand()
        result = cmd()  # pylint: disable=no-value-for-parameter
        assert result == ("hello", 100)


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


def test_nested_subcommand_description():
    class SubCommand(clipy.Command):
        @clipy.Command
        def subsubcmd(self):
            """
            This is a nested subcommand description.
            """
            pass

    class MainCommand(clipy.Command):
        subcmd: SubCommand = SubCommand()

    with patch("sys.argv", ["test.py", "subcmd", "subsubcmd"]):
        cmd = MainCommand()
        subcmd = cmd.subcmd
        subsubcmd = subcmd.subsubcmd
        assert subsubcmd.description == "This is a nested subcommand description."


def test_subcommand_named():
    class MainCommand(clipy.Command):
        @clipy.Command(name="custom_subcmd")
        def subcmd(self):
            pass

    with patch("sys.argv", ["test.py", "custom_subcmd"]):
        cmd = MainCommand()
        subcmd = cmd.subcmd
        assert subcmd.name == "custom_subcmd"


def test_nested_subcommand_named():
    class SubCommand(clipy.Command):
        @clipy.Command(name="custom_subsubcmd")
        def subsubcmd(self):
            pass

    class MainCommand(clipy.Command):
        subcmd: SubCommand = SubCommand()

    with patch("sys.argv", ["test.py", "subcmd", "custom_subsubcmd"]):
        cmd = MainCommand()
        subcmd = cmd.subcmd
        subsubcmd = subcmd.subsubcmd
        assert subsubcmd.name == "custom_subsubcmd"


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


def test_nested_subcommand_args_help():
    class SubCommand(clipy.Command):
        @clipy.Command
        def subsubcmd(self, arg1: str, arg2: int):
            """
            This is a test nested subcommand.

            Args:
                arg1: A string argument.
                arg2: An integer argument.
            """
            pass

    class MainCommand(clipy.Command):
        subcmd: SubCommand = SubCommand()

    with patch("sys.argv", ["test.py", "subcmd", "subsubcmd"]):
        cmd = MainCommand()
        subcmd = cmd.subcmd
        subsubcmd = subcmd.subsubcmd
        assert subsubcmd.args["arg1"].help == "A string argument."
        assert subsubcmd.args["arg2"].help == "An integer argument."


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


def test_subcommand_usage():
    class MainCommand(clipy.Command):
        @clipy.Command
        def subcmd(self, option1: int, option2: str = "default"):
            pass

    with patch("sys.argv", ["test.py", "subcmd"]):
        cmd = MainCommand()
        subcmd = cmd.subcmd
        assert subcmd.usage == "subcmd [--option1 <int>] [--option2 <str>]"


def test_nested_subcommand_usage():
    class SubCommand(clipy.Command):
        @clipy.Command
        def subsubcmd(self, arg1: str, arg2: int = 100):
            pass

    class MainCommand(clipy.Command):
        subcmd: SubCommand = SubCommand()

    with patch("sys.argv", ["test.py", "subcmd", "subsubcmd"]):
        cmd = MainCommand()
        subcmd = cmd.subcmd
        subsubcmd = subcmd.subsubcmd
        assert subsubcmd.usage == "subsubcmd [--arg1 <str>] [--arg2 <int>]"


def test_subcommand_positional_args():
    class MainCommand(clipy.Command):
        @clipy.Command
        def subcmd(self, option1: int, option2: str = "default"):
            return option1, option2

    with patch("sys.argv", ["test.py", "subcmd", "42"]):
        cmd = MainCommand()
        result = cmd()  # pylint: disable=no-value-for-parameter
        assert result == (42, "default")


def test_nested_subcommand_positional_args():
    class SubCommand(clipy.Command):
        @clipy.Command
        def subsubcmd(self, arg1: str, arg2: int = 100):
            return arg1, arg2

    class MainCommand(clipy.Command):
        subcmd: SubCommand = SubCommand()

    with patch("sys.argv", ["test.py", "subcmd", "subsubcmd", "hello"]):
        cmd = MainCommand()
        result = cmd()  # pylint: disable=no-value-for-parameter
        assert result == ("hello", 100)


def test_subcommand_positional_and_optional_args():
    class MainCommand(clipy.Command):
        @clipy.Command
        def subcmd(self, option1: int, option2: str = "default"):
            return option1, option2

    with patch("sys.argv", ["test.py", "subcmd", "42"]):
        cmd = MainCommand()
        result = cmd()  # pylint: disable=no-value-for-parameter
        assert result == (42, "default")

    with patch("sys.argv", ["test.py", "subcmd", "42", "hello"]):
        cmd = MainCommand()
        result = cmd()  # pylint: disable=no-value-for-parameter
        assert result == (42, "hello")

    with patch("sys.argv", ["test.py", "subcmd", "42", "--option2", "hello"]):
        cmd = MainCommand()
        result = cmd()  # pylint: disable=no-value-for-parameter
        assert result == (42, "hello")


def test_nested_subcommand_positional_and_optional_args():
    class SubCommand(clipy.Command):
        @clipy.Command
        def subsubcmd(self, arg1: str, arg2: int = 100):
            return arg1, arg2

    class MainCommand(clipy.Command):
        subcmd: SubCommand = SubCommand()

    with patch("sys.argv", ["test.py", "subcmd", "subsubcmd", "hello"]):
        cmd = MainCommand()
        result = cmd()  # pylint: disable=no-value-for-parameter
        assert result == ("hello", 100)

    with patch("sys.argv", ["test.py", "subcmd", "subsubcmd", "hello", "200"]):
        cmd = MainCommand()
        result = cmd()  # pylint: disable=no-value-for-parameter
        assert result == ("hello", 200)

    with patch("sys.argv", ["test.py", "subcmd", "subsubcmd", "hello", "--arg2", "200"]):
        cmd = MainCommand()
        result = cmd()  # pylint: disable=no-value-for-parameter
        assert result == ("hello", 200)


def test_subcommands_list_args():
    class MainCommand(clipy.Command):
        @clipy.Command
        def subcmd(self, arg1: list[str], arg2: int):
            return arg1, arg2

    with patch("sys.argv", ["test.py", "subcmd", "--arg1", "val1", "val2", "val3", "--arg2", "10"]):
        cmd = MainCommand()
        result = cmd()  # pylint: disable=no-value-for-parameter
        assert result == (["val1", "val2", "val3"], 10)

    class MainCommand2(clipy.Command):
        @clipy.Command
        def subcmd(self, arg1: list, arg2: str):  # Test without subscript
            return arg1, arg2

    with patch(
        "sys.argv", ["test.py", "subcmd", "--arg1", "val1", "val2", "val3", "--arg2", "hello"]
    ):
        cmd = MainCommand2()
        result = cmd()  # pylint: disable=no-value-for-parameter
        assert result == (["val1", "val2", "val3"], "hello")


def test_nested_subcommands_list_args():
    class SubCommand(clipy.Command):
        @clipy.Command
        def subsubcmd(self, arg1: list[str], arg2: int):
            return arg1, arg2

    class MainCommand(clipy.Command):
        subcmd: SubCommand = SubCommand()

    with patch(
        "sys.argv",
        ["test.py", "subcmd", "subsubcmd", "--arg1", "val1", "val2", "val3", "--arg2", "10"],
    ):
        cmd = MainCommand()
        result = cmd()  # pylint: disable=no-value-for-parameter
        assert result == (["val1", "val2", "val3"], 10)

    class SubCommand2(clipy.Command):
        @clipy.Command
        def subsubcmd(self, arg1: list, arg2: str):  # Test without subscript
            return arg1, arg2

    class MainCommand2(clipy.Command):
        subcmd: SubCommand2 = SubCommand2()

    with patch(
        "sys.argv",
        ["test.py", "subcmd", "subsubcmd", "--arg1", "val1", "val2", "val3", "--arg2", "hello"],
    ):
        cmd = MainCommand2()
        result = cmd()  # pylint: disable=no-value-for-parameter
        assert result == (["val1", "val2", "val3"], "hello")


def test_subcommand_typing_list_args():
    class MainCommand(clipy.Command):
        @clipy.Command
        def subcmd(self, arg1: List[str], arg2: int):
            return arg1, arg2

    with patch("sys.argv", ["test.py", "subcmd", "--arg1", "val1", "val2", "val3", "--arg2", "10"]):
        cmd = MainCommand()
        result = cmd()  # pylint: disable=no-value-for-parameter
        assert result == (["val1", "val2", "val3"], 10)

    class MainCommand2(clipy.Command):
        @clipy.Command
        def subcmd(self, arg1: List, arg2: str):  # Test without subscript
            return arg1, arg2

    with patch(
        "sys.argv", ["test.py", "subcmd", "--arg1", "val1", "val2", "val3", "--arg2", "hello"]
    ):
        cmd = MainCommand2()
        result = cmd()  # pylint: disable=no-value-for-parameter
        assert result == (["val1", "val2", "val3"], "hello")


def test_subcommand_variable_number_of_args():
    class MainCommand(clipy.Command):
        @clipy.Command
        def subcmd(self, arg1: int, *arg2):
            return arg1, arg2

    with patch("sys.argv", ["test.py", "subcmd", "42", "val1", "val2"]):
        cmd = MainCommand()
        result = cmd()  # pylint: disable=no-value-for-parameter
        assert result == (42, ("val1", "val2"))

    with patch("sys.argv", ["test.py", "subcmd", "42", "--arg2", "val1", "val2"]):
        cmd = MainCommand()
        result = cmd()  # pylint: disable=no-value-for-parameter
        assert result == (42, ("val1", "val2"))

    with patch("sys.argv", ["test.py", "subcmd", "--arg1", "42", "--arg2", "val1", "val2"]):
        cmd = MainCommand()
        result = cmd()  # pylint: disable=no-value-for-parameter
        assert result == (42, ("val1", "val2"))

    with patch("sys.argv", ["test.py", "subcmd", "--arg1", "42", "val1", "val2"]):
        cmd = MainCommand()
        result = cmd()  # pylint: disable=no-value-for-parameter
        assert result == (42, ("val1", "val2"))


def test_subcommand_dict_args():
    class MainCommand(clipy.Command):
        @clipy.Command
        def subcmd(self, arg1: dict, arg2: int):
            return arg1, arg2

    with patch(
        "sys.argv",
        ["test.py", "subcmd", "--arg1", "key1=value1", "--arg1", "key2=value2", "--arg2", "10"],
    ):
        cmd = MainCommand()
        result = cmd()  # pylint: disable=no-value-for-parameter
        assert result == ({"key1": "value1", "key2": "value2"}, 10)

    class MainCommand2(clipy.Command):
        @clipy.Command
        def subcmd(self, arg1: dict[str, str], arg2: int):  # Test with subscripts
            return arg1, arg2

    with patch(
        "sys.argv",
        ["test.py", "subcmd", "--arg1", "key1=value1", "--arg1", "key2=value2", "--arg2", "10"],
    ):
        cmd = MainCommand2()
        result = cmd()  # pylint: disable=no-value-for-parameter
        assert result == ({"key1": "value1", "key2": "value2"}, 10)

    class MainCommand3(clipy.Command):
        @clipy.Command
        def subcmd(self, arg1: dict[str, int], arg2: int):
            return arg1, arg2

    with patch(
        "sys.argv", ["test.py", "subcmd", "--arg1", "key1=1", "--arg1", "key2=2", "--arg2", "10"]
    ):
        cmd = MainCommand3()
        result = cmd()  # pylint: disable=no-value-for-parameter
        assert result == ({"key1": 1, "key2": 2}, 10)


def test_subcommand_typing_dict_args():
    class MainCommand(clipy.Command):
        @clipy.Command
        def subcmd(self, arg1: Dict[str, str], arg2: int):
            return arg1, arg2

    with patch(
        "sys.argv",
        ["test.py", "subcmd", "--arg1", "key1=value1", "--arg1", "key2=value2", "--arg2", "10"],
    ):
        cmd = MainCommand()
        result = cmd()  # pylint: disable=no-value-for-parameter
        assert result == ({"key1": "value1", "key2": "value2"}, 10)

    class MainCommand2(clipy.Command):
        @clipy.Command
        def subcmd(self, arg1: Dict[str, int], arg2: int):
            return arg1, arg2

    with patch(
        "sys.argv", ["test.py", "subcmd", "--arg1", "key1=1", "--arg1", "key2=2", "--arg2", "10"]
    ):
        cmd = MainCommand2()
        result = cmd()  # pylint: disable=no-value-for-parameter
        assert result == ({"key1": 1, "key2": 2}, 10)

    class MainCommand3(clipy.Command):
        @clipy.Command
        def subcmd(self, arg1: Dict, arg2: int):  # Test without subscripts
            return arg1, arg2

    with patch(
        "sys.argv",
        ["test.py", "subcmd", "--arg1", "key1=value1", "--arg1", "key2=value2", "--arg2", "10"],
    ):
        cmd = MainCommand3()
        result = cmd()  # pylint: disable=no-value-for-parameter
        assert result == ({"key1": "value1", "key2": "value2"}, 10)


def test_subcommand_variable_number_of_kwargs():
    class MainCommand(clipy.Command):
        @clipy.Command
        def subcmd(self, arg1: int, **arg2):
            return arg1, arg2

    with patch("sys.argv", ["test.py", "subcmd", "42", "--key1", "value1", "--key2", "value2"]):
        cmd = MainCommand()
        result = cmd()  # pylint: disable=no-value-for-parameter
        assert result == (42, {"key1": "value1", "key2": "value2"})
