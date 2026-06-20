"""Utility helpers for inspecting Python type annotations."""

from typing import Tuple, get_args, get_origin


def is_list(annotations: type) -> bool:
    """Check whether *annotations* represents a list type.

    Args:
        annotations: A Python type annotation to inspect.

    Returns:
        bool: True if *annotations* is ``list`` or a parameterised
        ``List[...]`` / ``list[...]``.
    """
    return get_origin(annotations) == list or annotations == list


def get_list_inner_type(annotations: type) -> type:
    """Return the element type of a list annotation.

    Args:
        annotations: A Python type annotation expected to be a list type.

    Returns:
        type: The inner element type, or ``str`` when no type parameter is
        given or *annotations* is not a list.
    """
    if is_list(annotations):
        inner_types = get_args(annotations)
        return inner_types[0] if inner_types else str
    return str


def is_dict(annotations: type) -> bool:
    """Check whether *annotations* represents a dict type.

    Args:
        annotations: A Python type annotation to inspect.

    Returns:
        bool: True if *annotations* is ``dict`` or a parameterised
        ``Dict[...]`` / ``dict[...]``.
    """
    return get_origin(annotations) == dict or annotations == dict


def get_dict_key_value_types(annotations: type) -> Tuple[type, type]:
    """Return the key and value types of a dict annotation.

    Args:
        annotations: A Python type annotation expected to be a dict type.

    Returns:
        Tuple[type, type]: A ``(key_type, value_type)`` pair.  Both default
        to ``str`` when not parameterised or when *annotations* is not a dict.
    """
    if is_dict(annotations):
        inner_types = get_args(annotations)
        key_type = inner_types[0] if inner_types else str
        value_type = inner_types[1] if len(inner_types) > 1 else str
        return key_type, value_type
    return str, str
