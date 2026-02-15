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


def test_command_args_no_type():
    @clipy.Command
    def func(option1, option2):
        return int(option1), option2

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


def test_named_command():
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
