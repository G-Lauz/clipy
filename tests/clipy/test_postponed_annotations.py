"""
Tests for commands declared in a module using postponed annotation evaluation.

Under ``from __future__ import annotations`` (PEP 563) every annotation reaches
``inspect.signature`` as a string, so these tests cover the resolution step that
turns them back into real type objects.  The commands must be declared at module
level: a class defined inside a function body is not reachable from the module
globals that annotation resolution looks in.
"""

from __future__ import annotations

import dataclasses
import json
from typing import Dict, List, Optional
from unittest.mock import patch

import pytest

import clipy


@dataclasses.dataclass
class Nested(clipy.Config):
    """
    Nested settings.

    Args:
        lr: Learning rate
    """

    lr: float = 0.001


@dataclasses.dataclass
class Settings(clipy.Config):
    """
    Settings for a run.

    Args:
        name: Run name
        epochs: Number of epochs
        nested: Nested settings
    """

    name: str
    epochs: int = 10
    nested: Nested = dataclasses.field(default_factory=Nested)


@clipy.Command
def configured(config: Settings, verbose: bool = False):
    """
    A command taking a config file.

    Args:
        config: Path to the config file
        verbose: Print progress
    """
    return config, verbose


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


def test_config_annotation_is_resolved(tmp_path):
    # Without resolution `is_config` would not recognise the string annotation,
    # and the command would silently receive the path instead of a config.
    assert configured.args["config"].type is Settings

    path = tmp_path / "config.json"
    path.write_text(json.dumps({"name": "run-1", "nested": {"lr": 0.5}}), encoding="utf-8")

    with patch("sys.argv", ["test.py", "--config", str(path)]):
        config, verbose = configured()  # pylint: disable=no-value-for-parameter
        assert config == Settings(name="run-1", nested=Nested(lr=0.5))
        assert verbose is False


def test_config_field_annotations_are_resolved(tmp_path):
    path = tmp_path / "config.json"
    path.write_text(json.dumps({"name": "run-1", "epochs": 50}), encoding="utf-8")

    with patch("sys.argv", ["test.py", "--config", str(path)]):
        config, _ = configured()  # pylint: disable=no-value-for-parameter
        assert isinstance(config.epochs, int)
        assert isinstance(config.nested, Nested)


def test_config_help_renders_with_postponed_annotations(capsys):
    with patch("sys.argv", ["test.py", "--help"]):
        with pytest.raises(SystemExit):
            configured()  # pylint: disable=no-value-for-parameter

    output = capsys.readouterr().out
    assert "[--config <path>]" in output
    assert "config file fields (--config, JSON):" in output
    assert "nested.lr:float" in output


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
