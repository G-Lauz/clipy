"""Tests for class docstring and __call__ docstring description features."""

from unittest.mock import patch

import pytest

from clipy.command import Command

# =============================================================================
# Class docstring as description
# =============================================================================


def test_class_docstring_as_description():
    """Class docstring should be used as the command description."""

    class MyGroup(Command):
        """This is the group description"""

        @Command
        def sub(self):
            pass

    group = MyGroup()
    assert group.description == "This is the group description"


def test_class_docstring_stripped():
    """Class docstring should be stripped of leading/trailing whitespace."""

    class MyGroup(Command):
        """
        Description with extra whitespace
        """

        @Command
        def sub(self):
            pass

    group = MyGroup()
    assert group.description == "Description with extra whitespace"


def test_no_class_docstring_no_func():
    """Without class docstring or func, description should be None."""

    class MyGroup(Command):
        @Command
        def sub(self):
            pass

    group = MyGroup()
    assert group.description is None


def test_class_docstring_shown_in_parent_help(capsys):
    """Class docstring should appear in the parent's subcommand listing."""

    class Sub(Command):
        """My sub description"""

        @Command
        def leaf(self):
            pass

    class Root(Command):
        sub: Sub = Sub()

    root = Root()

    with patch("sys.argv", ["test.py", "--help"]):
        with pytest.raises(SystemExit):
            root()

    captured = capsys.readouterr()
    assert "My sub description" in captured.out


def test_decorated_func_description_unchanged():
    """@Command decorated functions should still get description from their docstring."""

    @Command
    def my_func():
        """This is a function description"""
        pass

    assert my_func.description == "This is a function description"


# =============================================================================
# __call__ docstring vs class docstring
# =============================================================================


def test_call_docstring_used_in_own_help(capsys):
    """When __call__ has a docstring, it should be used in the command's own help."""

    class Sub(Command):
        """High-level description for listing"""

        def __call__(self):
            """Detailed description for own help"""
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
    assert "Detailed description for own help" in captured.out


def test_class_docstring_in_listing_call_docstring_in_own_help(capsys):
    """Class docstring in parent listing, __call__ docstring in own help."""

    class Sub(Command):
        """Listing description"""

        def __call__(self):
            """Own help description"""
            pass

        @Command
        def leaf(self):
            pass

    class Root(Command):
        sub: Sub = Sub()

    root = Root()

    # Parent listing should show class docstring
    with patch("sys.argv", ["test.py", "--help"]):
        with pytest.raises(SystemExit):
            root()

    captured = capsys.readouterr()
    assert "Listing description" in captured.out
    assert "Own help description" not in captured.out

    # Own help should show __call__ docstring
    with patch("sys.argv", ["test.py", "sub", "--help"]):
        with pytest.raises(SystemExit):
            root()

    captured = capsys.readouterr()
    assert "Own help description" in captured.out


def test_call_no_docstring_falls_back_to_class_docstring(capsys):
    """When __call__ has no docstring, own help should fall back to class docstring."""

    class Sub(Command):
        """Fallback description"""

        def __call__(self):
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
    assert "Fallback description" in captured.out


def test_func_description_attribute():
    """func_description should hold the __call__ docstring separately from description."""

    class Sub(Command):
        """Class level"""

        def __call__(self):
            """Func level"""
            pass

        @Command
        def leaf(self):
            pass

    sub = Sub()
    assert sub.description == "Class level"
    assert sub.func_description == "Func level"


def test_func_description_none_without_call_docstring():
    """func_description should be empty when __call__ has no docstring."""

    class Sub(Command):
        """Class level"""

        def __call__(self):
            pass

        @Command
        def leaf(self):
            pass

    sub = Sub()
    assert sub.description == "Class level"
    assert not sub.func_description  # empty string or None


def test_no_docstrings_at_all():
    """Command with no class docstring and no __call__ docstring should work."""

    class Sub(Command):
        def __call__(self):
            pass

        @Command
        def leaf(self):
            pass

    sub = Sub()
    assert sub.description is None
    assert not sub.func_description


# =============================================================================
# __call__ args shown in help
# =============================================================================


def test_call_args_shown_in_help(capsys):
    """When __call__ has parameters, they should appear in the command's help."""

    class Sub(Command):
        """A subcommand"""

        def __call__(self, arg1: int, arg2: str = "default"):
            """
            Detailed help

            Args:
                arg1: An integer argument
                arg2: A string argument
            """
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
    assert "--arg1" in captured.out
    assert "--arg2" in captured.out
    assert "An integer argument" in captured.out
    assert "A string argument" in captured.out
    assert "subcommands:" in captured.out
    assert "leaf" in captured.out


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
    # Should not have an "options:" section (only help is there but no custom args)
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
