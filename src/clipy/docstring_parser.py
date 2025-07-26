import abc


class DocstringParser(abc.ABC):
    @abc.abstractmethod
    def parse(self, docstring: str) -> dict:
        pass


class GoogleStyleDocstringParser(DocstringParser):
    def parse(self, docstring: str) -> dict:
        """
        Parses a Google-style docstring and returns a dictionary of arguments.

        Args:
            docstring (str): The docstring to parse.

        Returns:
            dict: A dictionary with argument names as keys and their descriptions as values.
        """
        args = {}

        lines = docstring.strip().splitlines()

        in_args_section = False
        in_multiline_description = False
        multiline_description_name = None
        multiline_description = []

        for line in lines:
            stripped_line = line.strip()

            if stripped_line.startswith("Args:"):
                in_args_section = True
                continue

            if not in_args_section:
                continue

            if stripped_line == "" and not in_multiline_description:  # End of section
                in_args_section = False
                continue

            if ":" in stripped_line and not in_multiline_description:
                name, _, description = stripped_line.partition(":")
                name = name.strip()
                description = description.strip()

                if description == "":
                    in_multiline_description = True
                    multiline_description_name = name
                    continue

                args[name] = description
                continue

            if ":" in stripped_line and in_multiline_description:
                args[multiline_description_name] = " ".join(multiline_description)

                in_multiline_description = False
                multiline_description_name = None
                multiline_description = []
                continue

            multiline_description.append(stripped_line)
        else:
            if in_multiline_description:
                args[multiline_description_name] = " ".join(multiline_description)

        return args
