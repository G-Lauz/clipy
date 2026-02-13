from unittest.mock import patch

import pytest

from clipy.command import Command


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
    # This is what we want to implement:
    assert "SubGroup body executed" in captured.out

    # Case 2: invoke leaf
    with patch("sys.argv", ["test.py", "sub", "leaf"]):
        root()

    captured = capsys.readouterr()
    assert "leaf executed" in captured.out
    # Ensure parent body is NOT executed when child is target (standard behavior)
    assert "SubGroup body executed" not in captured.out
