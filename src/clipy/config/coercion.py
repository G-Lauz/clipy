"""
Converting decoded configuration values to the types their fields declare.
"""

from __future__ import annotations

from typing import Any

from ..utils import (
    get_dict_key_value_types,
    get_list_inner_type,
    is_config,
    is_dict,
    is_list,
    unwrap_optional,
)
from .error import FieldTypeError

_VALUE_TYPE_NAMES = {
    dict: "object",
    list: "array",
    str: "string",
    bool: "bool",
    int: "int",
    float: "float",
}


def value_type_name(value: Any) -> str:
    """Return a human-readable name for the type of a decoded *value*.

    Args:
        value: A decoded configuration value.

    Returns:
        str: The name to show in an error message.
    """
    if value is None:
        return "null"
    return _VALUE_TYPE_NAMES.get(type(value), type(value).__name__)


def type_name(annotation: Any) -> str:
    """Return a human-readable name for a field *annotation*.

    Args:
        annotation: A resolved type annotation.

    Returns:
        str: The name to show in an error message.
    """
    return getattr(annotation, "__name__", None) or str(annotation)


def join_path(prefix: str, name: str) -> str:
    """Join a dotted field path, omitting the separator at the root.

    Args:
        prefix: The enclosing path, empty at the root.
        name: The field name to append.

    Returns:
        str: The dotted path of the field.
    """
    return f"{prefix}.{name}" if prefix else name


def coerce(value: Any, annotation: Any, path: str) -> Any:
    """Convert a decoded configuration *value* to the type its field declares.

    Args:
        value: The decoded value.
        annotation: The field's resolved type annotation.
        path: Dotted path of the field, used to report errors.

    Returns:
        Any: The converted value.

    Raises:
        ConfigError: If *value* cannot be represented as *annotation*.
    """
    unwrapped = unwrap_optional(annotation)
    is_optional = unwrapped is not annotation

    if value is None:
        if is_optional or annotation is None:
            return None
        raise FieldTypeError(path, type_name(annotation), "null")

    if unwrapped is None or unwrapped is Any:
        return value

    if is_config(unwrapped):
        return unwrapped.from_dict(value, prefix=path)

    if is_list(unwrapped):
        if not isinstance(value, list):
            raise FieldTypeError(path, "list", value_type_name(value))
        item_type = get_list_inner_type(unwrapped)
        return [coerce(item, item_type, f"{path}[{index}]") for index, item in enumerate(value)]

    if is_dict(unwrapped):
        if not isinstance(value, dict):
            raise FieldTypeError(path, "dict", value_type_name(value))
        key_type, item_type = get_dict_key_value_types(unwrapped)
        return {
            coerce(key, key_type, path): coerce(item, item_type, join_path(path, str(key)))
            for key, item in value.items()
        }

    return _coerce_scalar(value, unwrapped, path)


def _coerce_scalar(value: Any, annotation: Any, path: str) -> Any:
    """Convert a scalar *value*, rejecting types the field does not declare."""
    # `bool` is a subclass of `int`, so it has to be settled before the numbers.
    if annotation is bool:
        if not isinstance(value, bool):
            raise FieldTypeError(path, "bool", value_type_name(value))
        return value

    if annotation in (int, float):
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            raise FieldTypeError(path, annotation.__name__, value_type_name(value))
        if annotation is float:
            # An integer is a perfectly good float; the reverse loses information.
            return float(value)
        if isinstance(value, float):
            raise FieldTypeError(path, "int", "float")
        return value

    if annotation is str:
        if not isinstance(value, str):
            raise FieldTypeError(path, "str", value_type_name(value))
        return value

    if isinstance(annotation, type) and isinstance(value, annotation):
        return value

    # Types such as pathlib.Path, Decimal or an Enum are built from the raw value.
    try:
        return annotation(value)
    except (ValueError, TypeError) as error:
        raise FieldTypeError(path, type_name(annotation), value_type_name(value)) from error
