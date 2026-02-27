from unittest.mock import patch

import pytest

import clipy

# =============================================================================
# Reserved Keyword Argument Error
# =============================================================================


def test_reserved_keyword_as_parameter_name_raises(capsys):
    with pytest.raises(SyntaxError) as exc_info:

        @clipy.Command
        def func(help: str):
            return help

    assert "reserved keyword argument" in str(exc_info.value)
    assert "def func(help: str):" in str(exc_info.value)


# =============================================================================
# UnknownArgumentError
# =============================================================================


def test_unknown_argument_raises(capsys):
    @clipy.Command
    def func(arg1: int):
        return arg1

    with patch("sys.argv", ["test.py", "--unknown", "42"]):
        with pytest.raises(SystemExit) as exc_info:
            func()  # pylint: disable=no-value-for-parameter

    assert exc_info.value.code == 1
    output = capsys.readouterr().out
    assert "usage:" in output
    assert "command:" in output
    assert "$ func --unknown 42" in output
    assert "^" * len("--unknown") in output
    assert "error:" in output
    assert "unknown argument" in output


# =============================================================================
# MissingRequiredArgumentError
# =============================================================================


def test_missing_required_argument_raises(capsys):
    @clipy.Command
    def func(arg1: int, arg2: str):
        return arg1, arg2

    with patch("sys.argv", ["test.py", "--arg1", "42"]):
        with pytest.raises(SystemExit) as exc_info:
            func()  # pylint: disable=no-value-for-parameter

    assert exc_info.value.code == 1

    output = capsys.readouterr().out
    assert "usage:" in output
    assert "command:" not in output
    assert "error:" in output
    assert "missing required argument" in output


# =============================================================================
# UnexpectedPositionalArgumentError
# =============================================================================


def test_too_many_positional_arguments_raises(capsys):
    @clipy.Command
    def func(arg1: int):
        return arg1

    with patch("sys.argv", ["test.py", "42", "extra"]):
        with pytest.raises(SystemExit) as exc_info:
            func()  # pylint: disable=no-value-for-parameter

    assert exc_info.value.code == 1

    output = capsys.readouterr().out
    assert "usage:" in output
    assert "command:" in output
    assert "$ func 42 extra" in output
    assert "^" * len("extra") in output
    assert "error:" in output
    assert "unexpected positional argument" in output


def test_unexpected_positional_for_no_args_command_raises(capsys):
    @clipy.Command
    def func():
        pass

    with patch("sys.argv", ["test.py", "something"]):
        with pytest.raises(SystemExit) as exc_info:
            func()

    assert exc_info.value.code == 1

    output = capsys.readouterr().out
    assert "usage:" in output
    assert "command:" in output
    assert "$ func something" in output
    assert "^" * len("something") in output
    assert "error:" in output
    assert "unexpected positional argument" in output


# =============================================================================
# MissingRequiredValueError
# =============================================================================


def test_option_without_value_raises(capsys):
    @clipy.Command
    def func(arg1: int):
        return arg1

    with patch("sys.argv", ["test.py", "--arg1"]):
        with pytest.raises(SystemExit) as exc_info:
            func()  # pylint: disable=no-value-for-parameter

    assert exc_info.value.code == 1

    output = capsys.readouterr().out
    assert "usage:" in output
    assert "command:" in output
    assert "error:" in output
    assert "missing required value" in output


# =============================================================================
# InvalidArgumentTypeError
# =============================================================================


def test_invalid_type_for_int_raises(capsys):
    @clipy.Command
    def func(arg1: int):
        return arg1

    with patch("sys.argv", ["test.py", "--arg1", "not_a_number"]):
        with pytest.raises(SystemExit) as exc_info:
            func()  # pylint: disable=no-value-for-parameter

    assert exc_info.value.code == 1

    output = capsys.readouterr().out
    assert "usage:" in output
    assert "command:" in output
    assert "$ func --arg1 not_a_number" in output
    assert "^" * len("not_a_number") in output
    assert "error:" in output
    assert "expected argument of type" in output


def test_invalid_type_positional_raises(capsys):
    @clipy.Command
    def func(arg1: int):
        return arg1

    with patch("sys.argv", ["test.py", "not_a_number"]):
        with pytest.raises(SystemExit) as exc_info:
            func()  # pylint: disable=no-value-for-parameter

    assert exc_info.value.code == 1

    output = capsys.readouterr().out
    assert "usage:" in output
    assert "command:" in output
    assert "$ func not_a_number" in output
    assert "^" * len("not_a_number") in output
    assert "error:" in output
    assert "expected argument of type" in output


# =============================================================================
# UnexpectedValueFormatError (dict key=value format)
# =============================================================================


def test_dict_arg_without_equals_raises(capsys):
    @clipy.Command
    def func(arg1: dict[str, str]):
        return arg1

    with patch("sys.argv", ["test.py", "--arg1", "badformat"]):
        with pytest.raises(SystemExit) as exc_info:
            func()  # pylint: disable=no-value-for-parameter

    assert exc_info.value.code == 1

    output = capsys.readouterr().out
    assert "usage:" in output
    assert "command:" in output
    assert "$ func --arg1 badformat" in output
    assert "^" * len("badformat") in output
    assert "error:" in output
    assert "expected value format" in output


# =============================================================================
# Subcommand error handling
# =============================================================================


def test_unknown_subcommand_raises(capsys):
    class MainCommand(clipy.Command):
        @clipy.Command
        def subcmd(self):
            pass

    with patch("sys.argv", ["test.py", "nonexistent"]):
        cmd = MainCommand()
        with pytest.raises(SystemExit) as exc_info:
            cmd()

    assert exc_info.value.code == 1

    output = capsys.readouterr().out
    assert "usage:" in output
    assert "command:" in output
    assert "$ maincommand nonexistent" in output
    assert "^" * len("nonexistent") in output
    assert "error:" in output
    assert "unexpected positional argument" in output


def test_subcommand_unknown_argument_raises(capsys):
    class MainCommand(clipy.Command):
        @clipy.Command
        def subcmd(self, arg1: int):
            return arg1

    with patch("sys.argv", ["test.py", "subcmd", "--unknown", "42"]):
        cmd = MainCommand()
        with pytest.raises(SystemExit) as exc_info:
            cmd()

    assert exc_info.value.code == 1

    output = capsys.readouterr().out
    assert "usage:" in output
    assert "command:" in output
    assert "$ maincommand subcmd --unknown 42" in output
    assert "^" * len("--unknown") in output
    assert "error:" in output
    assert "unknown argument" in output


# =============================================================================
# Subcommand name conflict
# =============================================================================


def test_subcommand_name_conflict_raises():
    with pytest.raises(ValueError, match="subcommand name conflict"):

        class ConflictCommand(clipy.Command):
            @clipy.Command(name="cmd2")
            def cmd1(self):
                pass

            @clipy.Command
            def cmd2(self):
                pass

        ConflictCommand()
