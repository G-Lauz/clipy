[![pre-commit](https://img.shields.io/badge/pre--commit-enabled-brightgreen?logo=pre-commit)](https://github.com/pre-commit/pre-commit)
[![Linting: pylint](https://img.shields.io/badge/linting-pylint-yellowgreen)](https://github.com/PyCQA/pylint)
<!-- [![Tests](https://github.com/G-Lauz/python-project-template/actions/workflows/test.yml/badge.svg)](https://github.com/G-Lauz/python-project-template/actions/workflows/test.yml) -->

# clipy
`clipy` is a Python package for creating command-line interfaces (CLIs) in a pythonic way. Its core philosophy is that a command shouldn't be as different from a Python function.

The key features are:
- **Pythonic API**: The functions and class definitions are the commands and groups.
- **Easy to use**: It's easy to create CLIs with **automatic help generation** and **argument casting**.
- **Support complex CLIs**: You can create complex applications with **deeply nested commands**, **variable number of arguments**, and more.
- **End user friendly**: Given wrong input, it will point out the **exact location of the error** like a compiler would do.

## Quickstart
Install:
```bash
pip install clipyx
```

A simple example:

```python
import clipy

@clipy.Command
def greeting(name: str):
    """
    Greeting the provided name

    Args:
        name: The name to greet
    """
    print(f"Hello There!\nGeneral {name}!")

if __name__ == "__main__":
    greeting()
```

Then enjoy your CLI:

```bash
python greeting.py --help
# usage: greeting [--name <str>]

# Greeting the provided name

# options:
#   --name NAME:str     The name to greet
#   --help              Show this help message and exit.

python greeting.py --name=Kenobi
# Hello There!
# General Kenobi!

python greeting.py Kenobi
# Hello There!
# General Kenobi!

python greeting.py --not-an-arg
# usage: greeting [--name <str>]
# command:
#     $ greeting --not-an-arg
#                ^^^^^^^^^^^^
# greeting: error: unknown argument: --not-an-arg
```
**Supported Python versions**: 3.9 and above.

For more complex examples, like [automatic casting](./examples/typed_cli.py),[ nested commands](./examples/deep_nested_cli.py), [variable number of arguments](./examples/typed_cli.py#L70), and more, check the [examples](./examples/) folder.

## Installation
`clipy` is available on PyPI, you can install it using pip:

```bash
pip install clipyx
```
Otherwise, you can install a specific version from GitHub:

```bash
pip install git+https://github.com/G-Lauz/clipy.git@v1.0.0
```
Or clone the repository and install it manually:

```bash
git clone https://github.com/G-Lauz/clipy.git
cd clipy
pip install .
```

## Why `clipy`?
There are already many CLI libraries in Python, such as [`argparse`](https://docs.python.org/3/library/argparse.html), [Click](https://github.com/pallets/click), [Typer](https://github.com/fastapi/typer), and more. So why do we need another one?

The goal here isn't to replace them, but provide an alternative that emphasizes a different design philosophy. `clipy` is designed to be as close to regular Python code as possible, making it easy to learn and use. You should use `clipy` when you want to focus on the logic of your application rather than the CLI framework.

## Roadmap
- [ ] Support configuration files as arguments (e.g. `json`, `yaml`, etc.).
- [ ] Support short and combined short options (e.g. `-h` for `--help` and `-abc`).
- [ ] Support a wider range of argument types (e.g. `pathlib.Path`, `enum`, etc.).
- See the issue tracker for more details and to contribute.

## Contributing
Contributions are welcome! If you have any ideas, suggestions, or bug reports, please open an issue or submit a pull request on GitHub.

Please read the [`CONTRIBUTING.md`](./CONTRIBUTING.md) to help you get started.

## License
This project is licensed under the MIT License. See the [LICENSE](./LICENSE) file for details.
