"""
Tests for the clipy module.
"""

from unittest.mock import patch

import pytest

import clipy


def test_command_with_argument_decorator():
    @clipy.command(usage="test.py --arg1 <arg1>", description="Test command")
    @clipy.argument("arg1", help="Test argument", type=int, required=True)
    def func(*_args, arg1, **_kwargs):
        return arg1

    with patch("sys.argv", ["test.py", "--arg1", "42"]):
        result = func()  # pylint: disable=missing-kwoa
        assert result == 42


def test_missing_required_argument():
    @clipy.command(usage="test.py --arg1 <arg1>", description="Test command")
    @clipy.argument("arg1", help="Test argument", type=int, required=True)
    def func(*_args, arg1, **_kwargs):
        return arg1

    with patch("sys.argv", ["test.py"]):
        with pytest.raises(SystemExit):
            func()  # pylint: disable=missing-kwoa


def test_invalid_argument_type():
    @clipy.command(usage="test.py --arg1 <arg1>", description="Test command")
    @clipy.argument("arg1", help="Test argument", type=int, required=True)
    def func(*_args, arg1, **_kwargs):
        return arg1

    with patch("sys.argv", ["test.py", "--arg1", "invalid"]):
        with pytest.raises(SystemExit):
            func()  # pylint: disable=missing-kwoa


def test_multiple_arguments():
    @clipy.command(usage="test.py --arg1 <arg1> --arg2 <arg2>", description="Test command")
    @clipy.argument("arg1", help="Test argument 1", type=int, required=True)
    @clipy.argument("arg2", help="Test argument 2", type=str, required=True)
    def func(*_args, arg1, arg2, **_kwargs):
        return arg1, arg2

    with patch("sys.argv", ["test.py", "--arg1", "42", "--arg2", "hello"]):
        result = func()  # pylint: disable=missing-kwoa
        assert result == (42, "hello")


def test_help_message(capsys):
    @clipy.command(usage="test.py --arg1 <arg1>", description="Test command")
    @clipy.argument("arg1", help="Test argument", type=int, required=True)
    def func(*_args, arg1, **_kwargs):
        arg1 = arg1 + 1

    with patch("sys.argv", ["test.py", "--help"]):
        with pytest.raises(SystemExit):
            func()  # pylint: disable=missing-kwoa

    captured = capsys.readouterr()
    assert "Test argument" in captured.out
    assert "Test command" in captured.out
