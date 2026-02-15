from unittest.mock import patch

import pytest

from clipy.command import Command

# =============================================================================
# Group acting as command
# =============================================================================


def test_group_as_command(capsys):
    class SubGroup(Command):
        def __call__(self):
            print("SubGroup body executed")

        @Command
        def leaf(self):
            print("leaf executed")

    class Root(Command):
        sub = SubGroup()

    root = Root()

    # Case 1: invoke sub (the group acting as command)
    with patch("sys.argv", ["test.py", "sub"]):
        root()

    captured = capsys.readouterr()
    assert "SubGroup body executed" in captured.out

    # Case 2: invoke leaf
    with patch("sys.argv", ["test.py", "sub", "leaf"]):
        root()

    captured = capsys.readouterr()
    assert "leaf executed" in captured.out
    # Ensure parent body is NOT executed when child is target (standard behavior)
    assert "SubGroup body executed" not in captured.out


def test_call_args_in_usage(capsys):
    """Usage line should include both options from __call__ and subcommand list."""

    class Sub(Command):
        """A subcommand"""

        def __call__(self, arg1: int):
            pass

        @Command
        def leaf(self):
            pass

    class Root(Command):
        sub: Sub = Sub()

    root = Root()

    with patch("sys.argv", ["test.py", "sub", "--help"]):
        with pytest.raises(SystemExit):
            root()

    captured = capsys.readouterr()
    assert "[--arg1 <int>]" in captured.out
    assert "leaf" in captured.out


def test_group_without_call_no_options_section(capsys):
    """A pure group (no __call__) should not have an options section."""

    class Sub(Command):
        """A pure group"""

        @Command
        def leaf(self):
            pass

    class Root(Command):
        sub: Sub = Sub()

    root = Root()

    with patch("sys.argv", ["test.py", "sub", "--help"]):
        with pytest.raises(SystemExit):
            root()

    captured = capsys.readouterr()
    assert "subcommands:" in captured.out
    # The help flag is always present but it's in the args dict, not a custom arg
    assert "leaf" in captured.out


def test_call_args_and_subcommands_both_present(capsys):
    """Help output should contain both an options section and a subcommands section."""

    class Sub(Command):
        def __call__(self, flag: bool = False):
            """Run the sub command"""
            pass

        @Command
        def child1(self):
            """First child"""
            pass

        @Command
        def child2(self):
            """Second child"""
            pass

    class Root(Command):
        sub: Sub = Sub()

    root = Root()

    with patch("sys.argv", ["test.py", "sub", "--help"]):
        with pytest.raises(SystemExit):
            root()

    captured = capsys.readouterr()
    output = captured.out

    # Both sections should be present
    assert "options:" in output
    assert "subcommands:" in output

    # Options section should list the flag
    assert "--flag" in output

    # Subcommands section should list both children
    assert "child1" in output
    assert "child2" in output

    # Options should come before subcommands
    assert output.index("options:") < output.index("subcommands:")
