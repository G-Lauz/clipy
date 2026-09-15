"""Utility helpers for inspecting Python type annotations."""

import typing
from typing import Any, Callable, Dict, Tuple, Union, get_args, get_origin

try:  # Python 3.10+ spells unions as `X | Y`, backed by types.UnionType
    from types import UnionType
except ImportError:  # pragma: no cover - Python 3.9
    UnionType = None


def resolve_type_hints(func: Callable) -> Dict[str, Any]:
    """Resolve a callable's annotations into real type objects.

    Under ``from __future__ import annotations`` (PEP 563) every annotation
    reaches :func:`inspect.signature` as a string.  Storing those strings
    verbatim would break casting, help rendering and type introspection, so
    they are resolved once here.

    Args:
        func: The callable whose annotations should be resolved.

    Returns:
        Dict[str, Any]: A mapping of parameter name to resolved type.

    Raises:
        NameError: If an annotation names something that cannot be resolved at
            runtime.  Resolution can only fail when the annotations are
            strings, and a string annotation is unusable, so this is reported
            rather than silently passed through.
    """
    try:
        return typing.get_type_hints(func)
    except NameError as error:
        name = getattr(func, "__qualname__", None) or repr(func)
        raise NameError(
            f"cannot resolve the type annotations of '{name}': {error}. This usually means "
            "the module uses `from __future__ import annotations` and an annotation refers to "
            "a class defined inside a function body or imported only under TYPE_CHECKING; "
            "move that class to module level so it exists at runtime."
        ) from error


def unwrap_optional(annotation: type) -> type:
    """Reduce an optional annotation to the type it wraps.

    ``Optional[T]`` -- equivalently ``Union[T, None]`` or ``T | None`` -- casts
    as ``T``: the command line either supplies a value or the argument falls
    back to its default, so the ``None`` arm is never the target of a cast.

    Args:
        annotation: A Python type annotation to inspect.

    Returns:
        type: The wrapped type for an optional annotation, otherwise
        *annotation* unchanged.  Unions of several non-``None`` types are
        returned unchanged, as they have no single cast target.
    """
    origin = get_origin(annotation)
    if origin is not Union and (UnionType is None or origin is not UnionType):
        return annotation

    args = tuple(arg for arg in get_args(annotation) if arg is not type(None))
    return args[0] if len(args) == 1 else annotation


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


def is_config(annotations: type) -> bool:
    """Check whether *annotations* represents a configuration file type.

    Detection reads the ``__clipy_config__`` marker set by :class:`clipy.Config`.

    Args:
        annotations: A Python type annotation to inspect.

    Returns:
        bool: True if *annotations* is a :class:`clipy.Config` subclass.
    """
    return getattr(annotations, "__clipy_config__", False) is True


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
