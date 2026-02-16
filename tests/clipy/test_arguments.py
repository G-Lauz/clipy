from typing import Dict, List
from unittest.mock import patch

import clipy


def test_optional_args():
    @clipy.Command
    def func(option1: int, option2: str = None):
        return option1, option2

    with patch("sys.argv", ["test.py", "--option1", "42"]):
        result = func()  # pylint: disable=no-value-for-parameter
        assert result == (42, None)


def test_default_args():
    @clipy.Command
    def func(option1: int, option2: str = "default"):
        return option1, option2

    with patch("sys.argv", ["test.py", "--option1", "42"]):
        result = func()  # pylint: disable=no-value-for-parameter
        assert result == (42, "default")


def test_positional_args():
    @clipy.Command
    def func(arg1: int, arg2: str):
        return arg1, arg2

    with patch("sys.argv", ["test.py", "42", "hello"]):
        result = func()  # pylint: disable=no-value-for-parameter
        assert result == (42, "hello")


def test_positional_and_optional_args():
    @clipy.Command
    def func(arg1: int, arg2: str = "default"):
        return arg1, arg2

    with patch("sys.argv", ["test.py", "42"]):
        result = func()  # pylint: disable=no-value-for-parameter
        assert result == (42, "default")

    with patch("sys.argv", ["test.py", "42", "hello"]):
        result = func()  # pylint: disable=no-value-for-parameter
        assert result == (42, "hello")

    with patch("sys.argv", ["test.py", "42", "--arg2", "hello"]):
        result = func()  # pylint: disable=no-value-for-parameter
        assert result == (42, "hello")


def test_list_args():
    @clipy.Command
    def func1(arg1: list[str], arg2: int):
        return arg1, arg2

    with patch("sys.argv", ["test.py", "--arg1", "item1", "item2", "--arg2", "42"]):
        result = func1()  # pylint: disable=no-value-for-parameter
        assert result == (["item1", "item2"], 42)

    @clipy.Command
    def func2(arg1: list, arg2: int):
        return arg1, arg2

    with patch("sys.argv", ["test.py", "--arg1", "item1", "item2", "--arg2", "42"]):
        result = func2()  # pylint: disable=no-value-for-parameter
        assert result == (["item1", "item2"], 42)

    @clipy.Command
    def func3(arg1: List[str], arg2: int):
        return arg1, arg2

    with patch("sys.argv", ["test.py", "--arg1", "item1", "item2", "--arg2", "42"]):
        result = func3()  # pylint: disable=no-value-for-parameter
        assert result == (["item1", "item2"], 42)

    @clipy.Command
    def func4(arg1: List, arg2: int):
        return arg1, arg2

    with patch("sys.argv", ["test.py", "--arg1", "item1", "item2", "--arg2", "42"]):
        result = func4()  # pylint: disable=no-value-for-parameter
        assert result == (["item1", "item2"], 42)


def test_dict_args():
    @clipy.Command
    def func1(arg1: dict, arg2: int):
        return arg1, arg2

    with patch(
        "sys.argv", ["test.py", "--arg1", "key1=value1", "--arg1", "key2=value2", "--arg2", "42"]
    ):
        result = func1()  # pylint: disable=no-value-for-parameter
        assert result == ({"key1": "value1", "key2": "value2"}, 42)

    @clipy.Command
    def func2(arg1: dict[str, str], arg2: int):
        return arg1, arg2

    with patch(
        "sys.argv", ["test.py", "--arg1", "key1=value1", "--arg1", "key2=value2", "--arg2", "42"]
    ):
        result = func2()  # pylint: disable=no-value-for-parameter
        assert result == ({"key1": "value1", "key2": "value2"}, 42)

    @clipy.Command
    def func3(arg1: dict[str, int], arg2: int):
        return arg1, arg2

    with patch("sys.argv", ["test.py", "--arg1", "key1=1", "--arg1", "key2=2", "--arg2", "42"]):
        result = func3()  # pylint: disable=no-value-for-parameter
        assert result == ({"key1": 1, "key2": 2}, 42)

    @clipy.Command
    def func4(arg1: Dict[str, str], arg2: int):
        return arg1, arg2

    with patch(
        "sys.argv", ["test.py", "--arg1", "key1=value1", "--arg1", "key2=value2", "--arg2", "42"]
    ):
        result = func4()  # pylint: disable=no-value-for-parameter
        assert result == ({"key1": "value1", "key2": "value2"}, 42)

    @clipy.Command
    def func5(arg1: Dict[str, int], arg2: int):
        return arg1, arg2

    with patch("sys.argv", ["test.py", "--arg1", "key1=1", "--arg1", "key2=2", "--arg2", "42"]):
        result = func5()  # pylint: disable=no-value-for-parameter
        assert result == ({"key1": 1, "key2": 2}, 42)

    @clipy.Command
    def func6(arg1: Dict, arg2: int):
        return arg1, arg2

    with patch(
        "sys.argv", ["test.py", "--arg1", "key1=value1", "--arg1", "key2=value2", "--arg2", "42"]
    ):
        result = func6()  # pylint: disable=no-value-for-parameter
        assert result == ({"key1": "value1", "key2": "value2"}, 42)


def test_variable_args():
    @clipy.Command
    def func(arg1: int, *arg2):
        return arg1, arg2

    with patch("sys.argv", ["test.py", "42", "item1", "item2"]):
        result = func()  # pylint: disable=no-value-for-parameter
        assert result == (42, ("item1", "item2"))

    with patch("sys.argv", ["test.py", "42", "--arg2", "item1", "item2"]):
        result = func()  # pylint: disable=no-value-for-parameter
        assert result == (42, ("item1", "item2"))

    with patch("sys.argv", ["test.py", "--arg1", "42", "--arg2", "item1", "item2"]):
        result = func()  # pylint: disable=no-value-for-parameter
        assert result == (42, ("item1", "item2"))

    with patch("sys.argv", ["test.py", "--arg1", "42", "item1", "item2"]):
        result = func()  # pylint: disable=no-value-for-parameter
        assert result == (42, ("item1", "item2"))


def test_flag_args():
    @clipy.Command
    def func(arg1: int, verbose: bool = False):
        return arg1, verbose

    with patch("sys.argv", ["test.py", "--arg1", "42", "--verbose"]):
        result = func()  # pylint: disable=no-value-for-parameter
        assert result == (42, True)

    with patch("sys.argv", ["test.py", "--arg1", "42"]):
        result = func()  # pylint: disable=no-value-for-parameter
        assert result == (42, False)


def test_flag_with_explicit_value():
    @clipy.Command
    def func(verbose: bool = False):
        return verbose

    with patch("sys.argv", ["test.py", "--verbose", "True"]):
        result = func()  # pylint: disable=no-value-for-parameter
        assert result is True

    with patch("sys.argv", ["test.py", "--verbose", "False"]):
        result = func()  # pylint: disable=no-value-for-parameter
        assert result is False

    with patch("sys.argv", ["test.py", "--verbose", "1"]):
        result = func()  # pylint: disable=no-value-for-parameter
        assert result is True

    with patch("sys.argv", ["test.py", "--verbose", "0"]):
        result = func()  # pylint: disable=no-value-for-parameter
        assert result is False


def test_argument_definition_order():
    @clipy.Command
    def func1(flag: bool = False, value: int = 0):
        return flag, value

    @clipy.Command
    def func2(value: int = 0, flag: bool = False):
        return value, flag

    argv = ["test.py", "--flag", "--value", "42"]

    with patch("sys.argv", argv):
        result1 = func1()  # pylint: disable=no-value-for-parameter
        assert result1 == (True, 42)

    with patch("sys.argv", argv):
        result2 = func2()  # pylint: disable=no-value-for-parameter
        assert result2 == (42, True)


def test_flag_followed_by_positional():
    @clipy.Command
    def func(name: str, flag: bool = False):
        return name, flag

    with patch("sys.argv", ["test.py", "--flag", "hello"]):
        result = func()  # pylint: disable=no-value-for-parameter
        assert result == ("hello", True)


def test_flag_followed_by_list_positional():
    @clipy.Command
    def func(items: list[str] = [], flag: bool = False):
        return items, flag

    with patch("sys.argv", ["test.py", "--flag", "--items", "a", "b", "c"]):
        result = func()  # pylint: disable=no-value-for-parameter
        assert result == (["a", "b", "c"], True)


def test_variable_kwargs():
    @clipy.Command
    def func(arg1: int, **arg2):
        return arg1, arg2

    with patch("sys.argv", ["test.py", "42", "--key1", "value1", "--key2", "value2"]):
        result = func()  # pylint: disable=no-value-for-parameter
        assert result == (42, {"key1": "value1", "key2": "value2"})
