import abc
from typing import Dict, Tuple


class DocstringParser(abc.ABC):
    """
    Abstract base class for docstring parsers.

    Subclasses implement language/style-specific parsing logic to extract
    the function description and per-argument help strings.
    """

    @abc.abstractmethod
    def parse(self, docstring: str) -> Tuple[Dict[str, str], str]:
        """
        Parse a raw docstring into its component parts.

        Args:
            docstring: The raw docstring text to parse.

        Returns:
            Tuple[Dict[str, str], str]: A tuple of ``(args_dict, description)``
            where *args_dict* maps parameter names to their help text and
            *description* is the overall function description.
        """
        pass


class GoogleStyleDocstringParser(DocstringParser):
    """Minimal parser for Google-style docstrings.

    Recognises an ``Args:`` section and extracts per-argument descriptions,
    including multi-line continuations.
    """

    def parse(self, docstring: str) -> Tuple[Dict[str, str], str]:
        """Parse a Google-style docstring and return its components.

        Args:
            docstring: The raw docstring text to parse.

        Returns:
            Tuple[Dict[str, str], str]: A tuple of ``(args_dict, description)``
            where *args_dict* maps parameter names to their help text and
            *description* is the overall function description.
        """
        args_dict: Dict[str, str] = {}

        lines = docstring.splitlines()

        # Find the start of the Args: section (if any)
        args_start_idx = None
        for i, line in enumerate(lines):
            if line.strip().startswith("Args:"):
                args_start_idx = i
                break

        # Build the overall description (everything before the Args: section)
        if args_start_idx is not None:
            desc_lines = lines[:args_start_idx]
            args_lines = lines[args_start_idx + 1 :]
        else:
            desc_lines = lines
            args_lines = []

        # Clean description: strip leading/trailing blank lines and join
        description = "\n".join([l.rstrip() for l in desc_lines]).strip()

        # Parse args section
        in_multiline_description = False
        multiline_name = None
        multiline_parts = []

        for line in args_lines:
            stripped = line.strip()

            # blank line ends the args section
            if stripped == "":
                if in_multiline_description:
                    args_dict[multiline_name] = " ".join(p for p in multiline_parts if p)
                    in_multiline_description = False
                    multiline_name = None
                    multiline_parts = []
                break

            # Detect a new arg line (simple heuristic: contains ':' after name)
            if ":" in stripped and not in_multiline_description:
                name, _, desc = stripped.partition(":")
                name = name.split("(")[0].strip()  # handle "arg (type): desc" format
                desc = desc.strip()
                if desc == "":
                    in_multiline_description = True
                    multiline_name = name
                    multiline_parts = []
                else:
                    args_dict[name] = desc
                continue

            # If we are currently collecting a multiline description
            if in_multiline_description:
                # If this line looks like the start of another arg (e.g., "param: ..."),
                # finalize current multiline and handle the new param on the same iteration.
                if ":" in stripped and stripped.split(":", 1)[0].isidentifier():
                    args_dict[multiline_name] = " ".join(p for p in multiline_parts if p)
                    in_multiline_description = False
                    multiline_name = None
                    # process this line as a new arg line
                    name, _, desc = stripped.partition(":")
                    name = name.strip()
                    desc = desc.strip()
                    if desc == "":
                        in_multiline_description = True
                        multiline_name = name
                        multiline_parts = []
                    else:
                        args_dict[name] = desc
                    continue

                # otherwise keep collecting the multiline description
                multiline_parts.append(stripped)
                continue

            # Lines here are ignored (not in args section or unexpected format)

        # If file ended while still in multiline description, finalize it
        if in_multiline_description and multiline_name is not None:
            args_dict[multiline_name] = " ".join(p for p in multiline_parts if p)

        return args_dict, description
