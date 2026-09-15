"""
The :class:`Config` base class, and the policy that governs how a file's
values relate to the command's own parameters.
"""

from __future__ import annotations

import dataclasses
import difflib
from typing import Any, Dict, List

from ..docstring_parser import GoogleStyleDocstringParser
from ..utils import is_config, resolve_type_hints, unwrap_optional
from .coercion import coerce, join_path, type_name, value_type_name
from .error import (
    ConfigFormatError,
    ConfigReadError,
    FieldTypeError,
    MissingFieldError,
    UnknownFieldError,
)
from .loader import load


@dataclasses.dataclass
class FieldInfo:
    """
    A configuration field flattened for display in help output.

    Attributes:
        path: Dotted path of the field, matching the paths used in errors.
        type_name: Name of the type the field declares.
        help: Description taken from the configuration class' docstring.
        default: The field's default, or ``None`` when it has none.
        required: Whether the field must appear in the file.
        depth: Nesting level, zero for a field of the outermost configuration.
    """

    path: str
    type_name: str
    help: str
    default: Any
    required: bool
    depth: int


class Config:
    """Base class for configuration files, and the additive merge policy.

    Subclass this and apply :func:`dataclasses.dataclass` to describe a file's
    fields, then annotate a command parameter with the result::

        @dataclasses.dataclass
        class TrainConfig(clipy.Config):
            name: str
            epochs: int = 10

        @clipy.Command
        def train(config: TrainConfig):
            ...

    How a file's values relate to the command's *other* parameters is decided
    by :meth:`contribute`. This class implement an additive policy which doesn't
    make any modification to existing parameters: a configuration's fields are a
    namespace of their own.

    Different policies could be implement as a subclass overriding that one method.
    """

    # Read by `clipy.utils.is_config`.
    __clipy_config__ = True

    # This class must declare no *annotated* attributes: `@dataclass` collects
    # annotations from base classes, so any added here would silently become a
    # field of every user configuration.

    @classmethod
    def contribute(cls, instance: Config, cli_values: Dict[str, Any]) -> Dict[str, Any]:
        """Return the values this configuration supplies to the command's parameters.

        The base class implement an additive policy which supplies none:
        a configuration's fields are a namespace of their own.

        Overriding this method in a subclass lets a configuration file fill the command's
        parameters, deciding for itself what to do about a parameter the command line also
        supplied.

        Args:
            instance: The configuration built from the file.
            cli_values: Values already parsed from the command line for this
                command, keyed by parameter name.

        Returns:
            Dict[str, Any]: Parameter values contributed by this configuration,
            keyed by parameter name.
        """
        # pylint: disable=unused-argument
        return {}

    @classmethod
    def from_file(cls, path: str) -> Config:
        """Build a configuration from a file on disk.

        Args:
            path: Path to the configuration file.  Its extension selects the
                format.

        Returns:
            Config: An instance of *cls* populated from the file.

        Raises:
            ConfigError: If the file cannot be opened, or cannot be read as a
                configuration for *cls*.
        """
        try:
            data = load(path)
        except OSError as error:
            raise ConfigReadError(error.strerror or str(error)) from error

        return cls.from_dict(data)

    @classmethod
    def from_dict(cls, data: Any, prefix: str = "") -> Config:
        """Build a configuration from an already-decoded mapping.

        Args:
            data: The decoded configuration mapping.
            prefix: Dotted path of *data* within an enclosing configuration,
                used to report nested errors.

        Returns:
            Config: An instance of *cls* populated from *data*.

        Raises:
            ConfigError: If *data* does not describe a valid *cls*.
        """
        if not dataclasses.is_dataclass(cls):
            raise ConfigFormatError(
                f"'{cls.__name__}' is not a dataclass; apply @dataclasses.dataclass to it"
            )

        if not isinstance(data, dict):
            raise FieldTypeError(prefix or "<root>", cls.__name__, value_type_name(data))

        hints = cls._field_types()
        fields = {field.name: field for field in dataclasses.fields(cls) if field.init}

        for key in data:
            if key not in fields:
                raise UnknownFieldError(
                    join_path(prefix, key), difflib.get_close_matches(key, list(fields))
                )

        kwargs = {}
        missing: List[str] = []
        for name, field in fields.items():
            if name in data:
                kwargs[name] = coerce(data[name], hints.get(name), join_path(prefix, name))
            elif field.default is dataclasses.MISSING and (
                field.default_factory is dataclasses.MISSING
            ):
                missing.append(join_path(prefix, name))

        if missing:
            raise MissingFieldError(missing)

        return cls(**kwargs)

    @classmethod
    def describe(cls, prefix: str = "", depth: int = 0) -> List[FieldInfo]:
        """Flatten this configuration's fields for display, nested ones included.

        Args:
            prefix: Dotted path of this configuration within an enclosing one.
            depth: Nesting level of this configuration.

        Returns:
            List[FieldInfo]: One entry per field, in declaration order, each
            nested configuration followed immediately by its own fields.
        """
        docstring = cls.__doc__.strip() if cls.__doc__ else None
        field_help, _ = GoogleStyleDocstringParser().parse(docstring) if docstring else ({}, "")
        hints = cls._field_types()

        described: List[FieldInfo] = []
        for field in dataclasses.fields(cls):
            if not field.init:
                continue

            annotation = unwrap_optional(hints.get(field.name))
            path = join_path(prefix, field.name)
            has_default = not (
                field.default is dataclasses.MISSING
                and field.default_factory is dataclasses.MISSING
            )

            described.append(
                FieldInfo(
                    path=path,
                    type_name=type_name(annotation),
                    help=field_help.get(field.name, "No description available."),
                    default=None if field.default is dataclasses.MISSING else field.default,
                    required=not has_default,
                    depth=depth,
                )
            )

            if is_config(annotation):
                described.extend(annotation.describe(path, depth + 1))

        return described

    @classmethod
    def _field_types(cls) -> Dict[str, Any]:
        """Return each field's resolved type, caching the result on the class."""
        # Look the cache up on this exact class rather than through inheritance,
        # so a subclass never reuses the fields resolved for its parent.
        cached = cls.__dict__.get("__clipy_field_types__")
        if cached is None:
            cached = resolve_type_hints(cls)
            cls.__clipy_field_types__ = cached
        return cached
