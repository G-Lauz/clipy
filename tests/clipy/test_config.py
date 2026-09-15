"""
Tests for configuration files declared as typed command arguments.
"""

import dataclasses
import json
from typing import Dict, List, Optional
from unittest.mock import patch

import pytest

import clipy


@dataclasses.dataclass
class OptimConfig(clipy.Config):
    """
    Optimizer settings.

    Args:
        lr: Learning rate
        momentum: SGD momentum
    """

    lr: float = 0.001
    momentum: float = 0.9


@dataclasses.dataclass
class TrainConfig(clipy.Config):
    """
    Training settings.

    Args:
        name: Run name
        epochs: Number of training epochs
        tags: Labels for the run
        limits: Named numeric limits
        note: An optional free-form note
        optim: Optimizer settings
    """

    name: str
    epochs: int = 10
    tags: List[str] = dataclasses.field(default_factory=list)
    limits: Dict[str, int] = dataclasses.field(default_factory=dict)
    note: Optional[str] = None
    optim: OptimConfig = dataclasses.field(default_factory=OptimConfig)


@dataclasses.dataclass
class FillingConfig(clipy.Config):
    """
    A configuration whose values fill the command's own parameters.

    Args:
        epochs: Number of training epochs
    """

    epochs: int = 7

    @classmethod
    def contribute(cls, instance, cli_values):
        return {"epochs": instance.epochs}


@dataclasses.dataclass
class DeferringConfig(clipy.Config):
    """
    A configuration that yields to anything given on the command line.

    Args:
        epochs: Number of training epochs
    """

    epochs: int = 7

    @classmethod
    def contribute(cls, instance, cli_values):
        if "epochs" in cli_values:
            return {}
        return {"epochs": instance.epochs}


def write_config(tmp_path, data, name="config.json"):
    """Write *data* as a config file and return its path."""
    path = tmp_path / name
    path.write_text(json.dumps(data), encoding="utf-8")
    return str(path)


# ============================================================================
# Loading
# ============================================================================


def test_config_as_long_option(tmp_path):
    @clipy.Command
    def func(config: TrainConfig, verbose: bool = False):
        return config, verbose

    path = write_config(tmp_path, {"name": "run-1", "epochs": 50})

    with patch("sys.argv", ["test.py", "--config", path, "--verbose"]):
        config, verbose = func()  # pylint: disable=no-value-for-parameter
        assert config == TrainConfig(name="run-1", epochs=50)
        assert verbose is True


def test_config_as_explicit_assignment(tmp_path):
    @clipy.Command
    def func(config: TrainConfig):
        return config

    path = write_config(tmp_path, {"name": "run-1"})

    with patch("sys.argv", ["test.py", f"--config={path}"]):
        assert func().name == "run-1"  # pylint: disable=no-value-for-parameter


def test_config_as_positional(tmp_path):
    @clipy.Command
    def func(config: TrainConfig):
        return config

    path = write_config(tmp_path, {"name": "run-1"})

    with patch("sys.argv", ["test.py", path]):
        assert func().name == "run-1"  # pylint: disable=no-value-for-parameter


def test_config_argument_name_follows_the_parameter(tmp_path):
    @clipy.Command
    def func(settings: TrainConfig):
        return settings

    path = write_config(tmp_path, {"name": "run-1"})

    with patch("sys.argv", ["test.py", "--settings", path]):
        assert func().name == "run-1"  # pylint: disable=no-value-for-parameter


def test_optional_config_defaults_to_none():
    @clipy.Command
    def func(config: TrainConfig = None):
        return config

    with patch("sys.argv", ["test.py"]):
        assert func() is None


def test_config_on_a_subcommand(tmp_path):
    class Group(clipy.Command):
        """A group of commands."""

        @clipy.Command
        def train(self, config: TrainConfig):
            """
            Train a model.

            Args:
                config: Path to the config file
            """
            return config

    path = write_config(tmp_path, {"name": "run-1"})

    with patch("sys.argv", ["test.py", "train", "--config", path]):
        assert Group()().name == "run-1"


# ============================================================================
# Field values
# ============================================================================


def test_defaults_are_used_for_absent_keys(tmp_path):
    @clipy.Command
    def func(config: TrainConfig):
        return config

    path = write_config(tmp_path, {"name": "run-1"})

    with patch("sys.argv", ["test.py", "--config", path]):
        config = func()  # pylint: disable=no-value-for-parameter
        assert config.epochs == 10
        assert config.tags == []
        assert config.note is None
        assert config.optim == OptimConfig()


def test_nested_config_is_constructed(tmp_path):
    @clipy.Command
    def func(config: TrainConfig):
        return config

    path = write_config(tmp_path, {"name": "run-1", "optim": {"lr": 0.5, "momentum": 0.1}})

    with patch("sys.argv", ["test.py", "--config", path]):
        config = func()  # pylint: disable=no-value-for-parameter
        assert config.optim == OptimConfig(lr=0.5, momentum=0.1)


def test_partially_specified_nested_config_keeps_its_defaults(tmp_path):
    @clipy.Command
    def func(config: TrainConfig):
        return config

    path = write_config(tmp_path, {"name": "run-1", "optim": {"lr": 0.5}})

    with patch("sys.argv", ["test.py", "--config", path]):
        config = func()  # pylint: disable=no-value-for-parameter
        assert config.optim.lr == 0.5
        assert config.optim.momentum == 0.9


def test_collection_fields(tmp_path):
    @clipy.Command
    def func(config: TrainConfig):
        return config

    path = write_config(
        tmp_path, {"name": "run-1", "tags": ["a", "b"], "limits": {"cpu": 2, "gpu": 1}}
    )

    with patch("sys.argv", ["test.py", "--config", path]):
        config = func()  # pylint: disable=no-value-for-parameter
        assert config.tags == ["a", "b"]
        assert config.limits == {"cpu": 2, "gpu": 1}


def test_integer_widens_to_float(tmp_path):
    @clipy.Command
    def func(config: TrainConfig):
        return config

    path = write_config(tmp_path, {"name": "run-1", "optim": {"lr": 1}})

    with patch("sys.argv", ["test.py", "--config", path]):
        lr = func().optim.lr  # pylint: disable=no-value-for-parameter
        assert lr == 1.0
        assert isinstance(lr, float)


def test_null_is_accepted_for_an_optional_field(tmp_path):
    @clipy.Command
    def func(config: TrainConfig):
        return config

    path = write_config(tmp_path, {"name": "run-1", "note": None})

    with patch("sys.argv", ["test.py", "--config", path]):
        assert func().note is None  # pylint: disable=no-value-for-parameter


# ============================================================================
# Policy
# ============================================================================


def test_additive_policy_leaves_command_parameters_alone(tmp_path):
    @clipy.Command
    def func(config: TrainConfig, epochs: int = 1):
        return config.epochs, epochs

    path = write_config(tmp_path, {"name": "run-1", "epochs": 50})

    with patch("sys.argv", ["test.py", "--config", path]):
        # The config's own `epochs` field never reaches the command's `epochs`.
        assert func() == (50, 1)  # pylint: disable=no-value-for-parameter


def test_policy_can_fill_a_command_parameter(tmp_path):
    @clipy.Command
    def func(config: FillingConfig, epochs: int = 1):  # pylint: disable=unused-argument
        return epochs

    path = write_config(tmp_path, {"epochs": 50})

    with patch("sys.argv", ["test.py", "--config", path]):
        assert func() == 50  # pylint: disable=no-value-for-parameter


def test_policy_can_satisfy_a_required_parameter(tmp_path):
    @clipy.Command
    def func(config: FillingConfig, epochs: int):  # pylint: disable=unused-argument
        return epochs

    path = write_config(tmp_path, {"epochs": 50})

    # `epochs` is required and never appears on the command line; the config
    # supplies it before the missing-argument check runs.
    with patch("sys.argv", ["test.py", "--config", path]):
        assert func() == 50  # pylint: disable=no-value-for-parameter


def test_policy_can_see_what_the_command_line_supplied(tmp_path):
    @clipy.Command
    def func(config: DeferringConfig, epochs: int = 1):  # pylint: disable=unused-argument
        return epochs

    path = write_config(tmp_path, {"epochs": 50})

    with patch("sys.argv", ["test.py", "--config", path, "--epochs", "3"]):
        assert func() == 3  # pylint: disable=no-value-for-parameter

    with patch("sys.argv", ["test.py", "--config", path]):
        assert func() == 50  # pylint: disable=no-value-for-parameter


# ============================================================================
# Errors
# ============================================================================


def run_expecting_exit(argv, command):
    """Invoke *command* with *argv* and return its exit code."""
    with patch("sys.argv", argv):
        with pytest.raises(SystemExit) as exc_info:
            command()
    return exc_info.value.code


def test_unknown_field_suggests_a_close_match(tmp_path, capsys):
    @clipy.Command
    def func(config: TrainConfig):
        return config

    path = write_config(tmp_path, {"name": "run-1", "epoch": 5})

    assert run_expecting_exit(["test.py", "--config", path], func) == 1
    output = capsys.readouterr().out
    assert "unknown field 'epoch'" in output
    assert "did you mean 'epochs'?" in output
    assert "^" * len(path) in output


def test_missing_required_field(tmp_path, capsys):
    @clipy.Command
    def func(config: TrainConfig):
        return config

    path = write_config(tmp_path, {"epochs": 5})

    assert run_expecting_exit(["test.py", "--config", path], func) == 1
    output = capsys.readouterr().out
    assert "missing required field" in output
    assert "name" in output
    assert "^" * len(path) in output


def test_nested_field_type_error_reports_a_dotted_path(tmp_path, capsys):
    @clipy.Command
    def func(config: TrainConfig):
        return config

    path = write_config(tmp_path, {"name": "run-1", "optim": {"lr": "fast"}})

    assert run_expecting_exit(["test.py", "--config", path], func) == 1
    output = capsys.readouterr().out
    assert "field 'optim.lr'" in output
    assert "expected float, got string" in output


def test_bool_is_rejected_for_an_int_field(tmp_path, capsys):
    @clipy.Command
    def func(config: TrainConfig):
        return config

    path = write_config(tmp_path, {"name": "run-1", "epochs": True})

    assert run_expecting_exit(["test.py", "--config", path], func) == 1
    assert "expected int, got bool" in capsys.readouterr().out


def test_null_is_rejected_for_a_required_field(tmp_path, capsys):
    @clipy.Command
    def func(config: TrainConfig):
        return config

    path = write_config(tmp_path, {"name": None})

    assert run_expecting_exit(["test.py", "--config", path], func) == 1
    assert "expected str, got null" in capsys.readouterr().out


def test_non_object_document_is_rejected(tmp_path, capsys):
    @clipy.Command
    def func(config: TrainConfig):
        return config

    path = write_config(tmp_path, [1, 2])

    assert run_expecting_exit(["test.py", "--config", path], func) == 1
    assert "expected TrainConfig, got array" in capsys.readouterr().out


def test_malformed_json(tmp_path, capsys):
    @clipy.Command
    def func(config: TrainConfig):
        return config

    path = tmp_path / "broken.json"
    path.write_text('{"name": }', encoding="utf-8")

    assert run_expecting_exit(["test.py", "--config", str(path)], func) == 1
    output = capsys.readouterr().out
    assert "invalid JSON" in output
    assert "line 1 column 10" in output


def test_missing_file(tmp_path, capsys):
    @clipy.Command
    def func(config: TrainConfig):
        return config

    path = str(tmp_path / "nope.json")

    assert run_expecting_exit(["test.py", "--config", path], func) == 1
    output = capsys.readouterr().out
    assert f"config file '{path}': No such file or directory" in output
    assert "^" * len(path) in output


def test_unsupported_format(tmp_path, capsys):
    @clipy.Command
    def func(config: TrainConfig):
        return config

    path = tmp_path / "config.yaml"
    path.write_text("name: run-1", encoding="utf-8")

    assert run_expecting_exit(["test.py", "--config", str(path)], func) == 1
    output = capsys.readouterr().out
    assert "unsupported config format: '.yaml'" in output
    assert "supported: .json" in output


# ============================================================================
# Help
# ============================================================================


def test_help_lists_the_config_fields(capsys):
    @clipy.Command
    def func(config: TrainConfig):
        """
        Do a thing.

        Args:
            config: Path to the config file
        """
        return config

    assert run_expecting_exit(["test.py", "--help"], func) == 0
    output = capsys.readouterr().out

    assert "--config CONFIG:path" in output
    assert "config file fields (--config, JSON):" in output
    assert "name:str" in output
    assert "epochs:int" in output
    assert "(default: 10)" in output
    assert "Number of training epochs" in output
    # Nested fields are listed under their parent, by dotted path.
    assert "optim:OptimConfig" in output
    assert "optim.lr:float" in output
    assert "Learning rate" in output


def test_usage_shows_a_path_not_the_config_class(capsys):
    @clipy.Command
    def func(config: TrainConfig):
        return config

    assert run_expecting_exit(["test.py", "--help"], func) == 0
    output = capsys.readouterr().out
    assert "[--config <path>]" in output
    assert "TrainConfig" not in output.splitlines()[0]


def test_help_works_when_the_config_is_malformed(tmp_path, capsys):
    @clipy.Command
    def func(config: TrainConfig):
        return config

    path = tmp_path / "broken.json"
    path.write_text('{"name": }', encoding="utf-8")

    assert run_expecting_exit(["test.py", "--config", str(path), "--help"], func) == 0
    output = capsys.readouterr().out
    assert "options:" in output
    assert "invalid JSON" not in output


# ============================================================================
# Declaration errors
# ============================================================================


def test_config_class_without_dataclass_is_rejected():
    class Undecorated(clipy.Config):  # pylint: disable=too-few-public-methods
        name: str = "x"

    with pytest.raises(SyntaxError) as exc_info:

        @clipy.Command
        def func(config: Undecorated):
            return config

    assert "is not a dataclass" in str(exc_info.value)
    assert "@dataclasses.dataclass" in str(exc_info.value)


def test_config_field_named_help_is_rejected():
    @dataclasses.dataclass
    class WithHelp(clipy.Config):
        help: str = "x"

    with pytest.raises(SyntaxError) as exc_info:

        @clipy.Command
        def func(config: WithHelp):
            return config

    assert "reserved keyword" in str(exc_info.value)


def test_config_argument_with_a_non_none_default_is_rejected():
    with pytest.raises(SyntaxError) as exc_info:

        @clipy.Command
        def func(config: TrainConfig = "defaults.json"):
            return config

    assert "cannot have a default" in str(exc_info.value)


# ============================================================================
# Used without a CLI
# ============================================================================


def test_config_errors_render_themselves(tmp_path):
    # The parser prefixes these with the file path, so each one must read
    # correctly on its own and must not name the file itself.
    with pytest.raises(clipy.config.ConfigError) as exc_info:
        TrainConfig.from_dict({"name": "run-1", "epoch": 5})
    assert str(exc_info.value) == "unknown field 'epoch'; did you mean 'epochs'?"

    with pytest.raises(clipy.config.ConfigError) as exc_info:
        TrainConfig.from_dict({})
    assert str(exc_info.value) == "missing required field 'name'"

    with pytest.raises(clipy.config.ConfigError) as exc_info:
        TrainConfig.from_dict({"name": "run-1", "optim": {"lr": "fast"}})
    assert str(exc_info.value) == "field 'optim.lr': expected float, got string"

    with pytest.raises(clipy.config.ConfigError) as exc_info:
        TrainConfig.from_file(str(tmp_path / "nope.json"))
    assert str(exc_info.value) == "No such file or directory"


def test_reading_a_missing_file_raises_a_config_error(tmp_path):
    # Callers outside a CLI catch one exception family, never OSError as well.
    with pytest.raises(clipy.config.ConfigError):
        TrainConfig.from_file(str(tmp_path / "nope.json"))


def test_config_can_be_built_directly(tmp_path):
    path = write_config(tmp_path, {"name": "run-1", "optim": {"lr": 0.5}})

    config = TrainConfig.from_file(path)
    assert config == TrainConfig(name="run-1", optim=OptimConfig(lr=0.5))
    assert TrainConfig.from_dict({"name": "run-2"}).name == "run-2"
