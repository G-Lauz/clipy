from unittest.mock import patch

import pytest

from clipy.command import Command

# =============================================================================
# Function-based command docstrings
# =============================================================================


def test_function_description():
    """@Command decorated functions should get description from their docstring."""

    @Command
    def func():
        """
        This is a test descrption.
        """
        pass

    assert func.description == "This is a test descrption."


def test_function_args_help():
    """Docstring Args section should populate argument help text."""

    @Command
    def func(arg1: int, arg2: str = "default"):
        """
        This is a test command.

        Args:
            arg1: An integer argument.
            arg2:
                A string argument. Defaults to "default".
        """
        pass

    assert func.args["arg1"].help == "An integer argument."
    assert func.args["arg2"].help == 'A string argument. Defaults to "default".'


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


def test_no_class_docstring():
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
