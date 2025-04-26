import argparse
from unittest.mock import Mock, patch

import pytest

from clipy.cli import CLI
from clipy.cli_types import CommandDefinition, OptionDefinition


def test_cli_initialization():
    mock_func = Mock()
    cli = CLI(mock_func, usage="test usage", description="test description")

    assert cli.func == mock_func
    assert cli.usage == "test usage"
    assert cli.description == "test description"
    assert cli.commands == []
    assert cli.global_options == []


def test_register_command():
    mock_func = Mock()
    cli = CLI(mock_func)
    command = CommandDefinition(name="test", options=[])

    cli.register_command(command)
    assert len(cli.commands) == 1
    assert cli.commands[0] == command


def test_register_global_option():
    mock_func = Mock()
    cli = CLI(mock_func)
    option = OptionDefinition(name="test", kwargs={})

    cli.register_global_option(option)
    assert len(cli.global_options) == 1
    assert cli.global_options[0] == option


def test_build_parser():
    mock_func = Mock()
    cli = CLI(mock_func, usage="test usage", description="test description")

    # Add global option
    global_option = OptionDefinition(name="global", kwargs={"help": "global option"})
    cli.register_global_option(global_option)

    # Add command with option
    command_option = OptionDefinition(name="cmd_opt", kwargs={"help": "command option"})
    command = CommandDefinition(
        name="test", options=[command_option], usage="test usage", description="test description"
    )
    cli.register_command(command)

    parser = cli.build_parser()
    assert isinstance(parser, argparse.ArgumentParser)
    assert parser.usage == "test usage"
    assert parser.description == "test description"


def test_build_parser_with_subcommands():
    mock_func = Mock()
    cli = CLI(mock_func, usage="test usage", description="test description")

    # Add global option
    global_option = OptionDefinition(name="global", kwargs={"help": "global option"})
    cli.register_global_option(global_option)

    # Create the subcommand with a specific option
    subcommand = CommandDefinition(
        name="subcommand",
        usage="subcommand usage",
        description="subcommand description",
        options=[OptionDefinition(name="cmd_opt", kwargs={"help": "command option"})],
    )

    # Register the subcommand with the main command.
    # Usage would be : test subcommand --cmd_opt some_value
    command = CommandDefinition(
        name="test", usage="test usage", description="test description", subcommands=[subcommand]
    )
    cli.register_command(command)

    parser = cli.build_parser()

    main_command = [
        action for action in parser._actions if isinstance(action, argparse._SubParsersAction)
    ][0].choices["test"]
    assert isinstance(main_command, argparse.ArgumentParser)
    assert main_command.usage == "test usage"
    assert main_command.description == "test description"

    sub_command = [
        action for action in main_command._actions if isinstance(action, argparse._SubParsersAction)
    ][0].choices["subcommand"]
    assert isinstance(sub_command, argparse.ArgumentParser)
    assert sub_command.usage == "subcommand usage"
    assert sub_command.description == "subcommand description"

    # TODO: Nested subparsers : change this assert from 'subcommand_cmd_opt' to 'cmd_opt'
    #       when the subcommands implemention is integrated with argparse using custom actions and namespaces
    assert {action.dest for action in sub_command._get_optional_actions()} == set(
        ["subcommand__cmd_opt", "help"]
    )


def test_cli_call():
    mock_func = Mock()
    cli = CLI(mock_func)

    command = CommandDefinition(
        name="test", options=[OptionDefinition(name="opt", kwargs={"help": "test option"})]
    )
    cli.register_command(command)

    with patch("sys.argv", ["prog", "test", "--opt", "value"]):
        cli()
        mock_func.assert_called_once()


def test_cli_call_with_subcommands():
    mock_func = Mock()
    cli = CLI(mock_func)

    command = CommandDefinition(
        name="test",
        subcommands=[
            CommandDefinition(
                name="subcommand",
                options=[OptionDefinition(name="opt", kwargs={"help": "test option"})],
            )
        ],
    )
    cli.register_command(command)

    with patch("sys.argv", ["prog", "test", "subcommand", "--opt", "value"]):
        cli()
        mock_func.assert_called_once()


def test_cli_positional_arg():
    mock_func = Mock()
    cli = CLI(mock_func)

    command = CommandDefinition(
        name="test",
        options=[OptionDefinition(name="opt", positional=True, kwargs={"help": "test option"})],
    )
    cli.register_command(command)

    with patch("sys.argv", ["prog", "test", "value"]):
        cli()
        mock_func.assert_called_once()


def test_cli_help_message(capsys):
    mock_func = Mock()
    cli = CLI(mock_func, description="Test CLI")

    with patch("sys.argv", ["prog", "--help"]):
        with pytest.raises(SystemExit):
            cli()

    captured = capsys.readouterr()
    assert "Test CLI" in captured.out
