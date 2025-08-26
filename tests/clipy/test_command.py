from unittest.mock import patch

import pytest

import clipy


def test_command_no_args():
    @clipy.Command
    def func():
        pass

    with patch("sys.argv", ["test.py"]):
        func()  # pylint: disable=missing-kwoa


def test_command_args():
    @clipy.Command
    def func(option1: int, option2: str):
        return option1, option2

    with patch("sys.argv", ["test.py", "--option1", "42", "--option2", "hello"]):
        result = func()  # pylint: disable=no-value-for-parameter
        assert result == (42, "hello")


def test_missing_required_argument():
    @clipy.Command
    def func(option1: int, option2: str):
        return option1, option2

    with patch("sys.argv", ["test.py", "--option1", "42"]):
        with pytest.raises(SystemExit):
            func()  # pylint: disable=no-value-for-parameter


def test_command_args_no_type():
    @clipy.Command
    def func(option1, option2):
        return int(option1), option2

    with patch("sys.argv", ["test.py", "--option1", "42", "--option2", "hello"]):
        result = func()  # pylint: disable=no-value-for-parameter
        assert result == (42, "hello")


def test_command_optional_args():
    @clipy.Command
    def func(option1: int, option2: str = None):
        return option1, option2

    with patch("sys.argv", ["test.py", "--option1", "42"]):
        result = func()  # pylint: disable=no-value-for-parameter
        assert result == (42, None)


def test_command_default_args():
    @clipy.Command
    def func(option1: int, option2: str = "default"):
        return option1, option2

    with patch("sys.argv", ["test.py", "--option1", "42"]):
        result = func()  # pylint: disable=no-value-for-parameter
        assert result == (42, "default")


def test_command_description():
    @clipy.Command
    def func():
        """
        This is a test descrption.
        """
        pass

    with patch("sys.argv", ["test.py"]):
        cmd = func
        assert cmd.description == "This is a test descrption."


def test_command_named():
    @clipy.Command(name="test_command")
    def func():
        pass

    with patch("sys.argv", ["test.py"]):
        cmd = func
        assert cmd.name == "test_command"


def test_command_usage():
    @clipy.Command(name="test.py")
    def func(arg1: int, arg2: str = "default"):  # pylint: disable=unused-argument
        pass

    with patch("sys.argv", ["test.py"]):
        cmd = func
        assert cmd.usage == "test.py [--arg1 <int>] [--arg2 <str>]"


def test_command_args_help():
    @clipy.Command
    def func(arg1: int, arg2: str = "default"):  # enforce Google style docstrings for now
        """
        This is a test command.

        Args:
            arg1: An integer argument.
            arg2:
                A string argument. Defaults to "default".
        """
        pass

    with patch("sys.argv", ["test.py"]):
        cmd = func
        assert cmd.args["arg1"].help == "An integer argument."
        assert cmd.args["arg2"].help == 'A string argument. Defaults to "default".'


def test_command_positional_args():
    @clipy.Command
    def func(arg1: int, arg2: str):
        return arg1, arg2

    with patch("sys.argv", ["test.py", "42", "hello"]):
        result = func()  # pylint: disable=no-value-for-parameter
        assert result == (42, "hello")


def test_command_positional_and_optional_args():
    @clipy.Command
    def func(arg1: int, arg2: str = "default"):
        return arg1, arg2

    with patch("sys.argv", ["test.py", "42"]):
        result = func()  # pylint: disable=no-value-for-parameter
        assert result == (42, "default")

    with patch("sys.argv", ["test.py", "42", "hello"]):
        result = func()  # pylint: disable=no-value-for-parameter
        assert result == (42, "hello")

    with patch("sys.argv", ["test.py", "42", "--arg2", "hello"]):
        result = func()  # pylint: disable=no-value-for-parameter
        assert result == (42, "hello")


def test_command_list_args():
    @clipy.Command
    def func(arg1: list, arg2: int):
        return arg1, arg2

    with patch("sys.argv", ["test.py", "--arg1", "item1", "item2", "--arg2", "42"]):
        result = func()  # pylint: disable=no-value-for-parameter
        assert result == (["item1", "item2"], 42)

    @clipy.Command
    def func2(arg1: int, *arg2):
        return arg1, arg2

    with patch("sys.argv", ["test.py", "42", "item1", "item2"]):
        result = func2()  # pylint: disable=no-value-for-parameter
        assert result == (42, ("item1", "item2"))


def test_command_dict_args():
    @clipy.Command
    def func(arg1: dict, arg2: int):
        return arg1, arg2

    with patch("sys.argv", ["test.py", "--arg1", "key1=value1", "key2=value2", "--arg2", "42"]):
        result = func()  # pylint: disable=no-value-for-parameter
        assert result == ({"key1": "value1", "key2": "value2"}, 42)

    @clipy.Command
    def func2(arg1: int, **arg2):
        return arg1, arg2

    with patch("sys.argv", ["test.py", "42", "--key1", "value1", "--key2", "value2"]):
        result = func2()  # pylint: disable=no-value-for-parameter
        assert result == (42, {"key1": "value1", "key2": "value2"})
