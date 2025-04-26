from clipy.cli import CLI
from clipy.cli_types import CommandDefinition, OptionDefinition
from clipy.decorators import App, Command, Option


def test_option_decorator():
    @Option("test_option", help="Test option", type=int, required=True)
    def func():
        pass

    assert isinstance(func, CLI)
    assert len(func.global_options) == 1
    assert isinstance(func.global_options[0], OptionDefinition)
    assert func.global_options[0].name == "test_option"
    assert func.global_options[0].kwargs == {"help": "Test option", "type": int, "required": True}


def test_command_decorator():
    @Command("test_cmd", usage="test usage", description="test description")
    def func():
        pass

    assert isinstance(func, CLI)
    assert len(func.commands) == 1
    assert isinstance(func.commands[0], CommandDefinition)
    assert func.commands[0].name == "test_cmd"
    assert func.commands[0].usage == "test usage"
    assert func.commands[0].description == "test description"


def test_command_with_options():
    test_option = Option("test_option", help="Test option", type=str)

    @Command(
        "test_cmd", usage="test usage", description="test desc", options=[test_option.definition]
    )
    def func():
        pass

    assert isinstance(func, CLI)
    assert len(func.commands[0].options) == 1
    assert func.commands[0].options[0].name == "test_option"


def test_command_with_subcommands():
    test_subcommand = Command("test", "This is a test subcommand", "This is a test subcommand")

    @App(usage="test app usage", description="test app description")
    @Command(
        "test_cmd",
        "This is a test command",
        "This is a test command",
        subcommands=[test_subcommand.definition],
    )
    def func():
        pass

    assert isinstance(func, CLI)
    assert len(func.commands[0].subcommands) == 1
    assert func.commands[0].subcommands[0].name == "test"


def test_app_decorator():
    @App(usage="test app usage", description="test app description")
    def func():
        pass

    assert isinstance(func, CLI)
    assert func.usage == "test app usage"
    assert func.description == "test app description"


def test_multiple_decorators():
    @App(usage="app usage", description="app description")
    @Option("global_opt", help="Global option")
    @Command("cmd1", usage="cmd1 usage", description="cmd1 description")
    def func():
        pass

    assert isinstance(func, CLI)
    assert func.usage == "app usage"
    assert func.description == "app description"
    assert len(func.global_options) == 1
    assert len(func.commands) == 1


def test_option_properties():
    option = Option("test_opt", help="Test help")
    assert option.name == "test_opt"
    assert option.kwargs == {"help": "Test help"}


def test_command_register_option():
    cmd = Command("test_cmd")
    option = Option("test_opt", help="Test help")
    cmd.register_option(option.definition)

    assert len(cmd.definition.options) == 1
    assert cmd.definition.options[0].name == "test_opt"


def test_ensure_cli_wrapper():
    def plain_func():
        pass

    wrapped = App.ensure_cli_wrapper(plain_func)
    assert isinstance(wrapped, CLI)

    # Test wrapping already wrapped function
    double_wrapped = App.ensure_cli_wrapper(wrapped)
    assert double_wrapped is wrapped


def test_command_dynamic_properties():
    cmd = Command("cmd1", usage="cmd1 usage", description="cmd1 description")
    cmd2 = Command("cmd2", usage="cmd2 usage", description="cmd2 description")

    assert cmd.name == cmd.definition.name
    assert cmd.usage == cmd.definition.usage
    assert cmd.description == cmd.definition.description

    assert cmd2.name == "cmd2"
    assert cmd2.usage == "cmd2 usage"
    assert cmd2.description == "cmd2 description"
