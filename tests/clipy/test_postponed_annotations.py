"""
Tests for commands declared in a module using postponed annotation evaluation.

Under ``from __future__ import annotations`` (PEP 563) every annotation reaches
``inspect.signature`` as a string, so these tests cover the resolution step that
turns them back into real type objects.  The commands must be declared at module
level: a class defined inside a function body is not reachable from the module
globals that annotation resolution looks in.
"""

from __future__ import annotations

from typing import Dict, List, Optional
from unittest.mock import patch

import pytest

import clipy


@clipy.Command
def scalars(option1: int, option2: str = "default", option3: float = 1.5, flag: bool = False):
    """
    A command with scalar arguments.

    Args:
        option1: A required integer
        option2: An optional string
        option3: An optional float
        flag: An optional boolean flag
    """
    return option1, option2, option3, flag


@clipy.Command
def collections(values: list[int], mapping: Dict[str, int] = None):
    """
    A command with collection arguments.

    Args:
        values: A list of integers
        mapping: A mapping of strings to integers
    """
    return values, mapping


@clipy.Command
def optionals(value: Optional[int] = None, names: Optional[List[str]] = None):
    """
    A command with optional arguments.

    Args:
        value: An optional integer
        names: An optional list of strings
    """
    return value, names


def test_scalar_annotations_are_resolved():
    with patch("sys.argv", ["test.py", "--option1", "42"]):
        result = scalars()  # pylint: disable=no-value-for-parameter
        assert result == (42, "default", 1.5, False)


def test_scalar_annotations_are_cast():
    with patch("sys.argv", ["test.py", "--option1", "42", "--option3", "2.5", "--flag"]):
        result = scalars()  # pylint: disable=no-value-for-parameter
        assert result == (42, "default", 2.5, True)


def test_resolved_annotations_are_real_types():
    assert scalars.args["option1"].type is int
    assert scalars.args["option2"].type is str
    assert scalars.args["flag"].type is bool


def test_collection_annotations_are_resolved():
    with patch("sys.argv", ["test.py", "--values", "1", "2", "3"]):
        values, mapping = collections()  # pylint: disable=no-value-for-parameter
        assert values == [1, 2, 3]
        assert mapping is None


def test_dict_annotations_are_resolved():
    with patch("sys.argv", ["test.py", "--values", "1", "--mapping", "a=1", "--mapping", "b=2"]):
        values, mapping = collections()  # pylint: disable=no-value-for-parameter
        assert values == [1]
        assert mapping == {"a": 1, "b": 2}


def test_optional_annotations_are_unwrapped():
    assert optionals.args["value"].type is int

    with patch("sys.argv", ["test.py", "--value", "42"]):
        value, names = optionals()
        assert value == 42
        assert names is None


def test_optional_list_annotations_are_unwrapped():
    with patch("sys.argv", ["test.py", "--names", "alice", "bob"]):
        value, names = optionals()
        assert value is None
        assert names == ["alice", "bob"]


def test_help_renders_with_postponed_annotations(capsys):
    with patch("sys.argv", ["test.py", "--help"]):
        with pytest.raises(SystemExit) as exc_info:
            scalars()  # pylint: disable=no-value-for-parameter

    assert exc_info.value.code == 0
    output = capsys.readouterr().out
    assert "--option1 OPTION1:int" in output
    assert "A required integer" in output


def test_invalid_type_error_renders_with_postponed_annotations(capsys):
    with patch("sys.argv", ["test.py", "--option1", "not-a-number"]):
        with pytest.raises(SystemExit) as exc_info:
            scalars()  # pylint: disable=no-value-for-parameter

    assert exc_info.value.code == 1
    output = capsys.readouterr().out
    assert "expected argument of type: int" in output


def test_unresolvable_annotation_raises_at_decoration():
    class LocalType:  # pylint: disable=too-few-public-methods
        pass

    with pytest.raises(NameError) as exc_info:

        @clipy.Command
        def func(value: LocalType):
            return value

    message = str(exc_info.value)
    assert "from __future__ import annotations" in message
    assert "move that class to module level" in message
