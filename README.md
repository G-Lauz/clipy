[![pre-commit](https://img.shields.io/badge/pre--commit-enabled-brightgreen?logo=pre-commit)](https://github.com/pre-commit/pre-commit)
[![Tests](https://github.com/G-Lauz/python-project-template/actions/workflows/test.yml/badge.svg)](https://github.com/G-Lauz/python-project-template/actions/workflows/test.yml)
[![Linting: pylint](https://img.shields.io/badge/linting-pylint-yellowgreen)](https://github.com/PyCQA/pylint)

# CLIpy
A python package that eases the creation of command line interface tools. It's a simple wrapper around the `argparse` module that simplifies the creation of CLI tools.

## Features

- `@clipy.command` decorator: Adds a command-line parser with usage and description.
- `@clipy.argument` decorator: Adds individual arguments to the command-line parser.
- Simplifies the creation of CLI tools.
- Supports `argparse` arguments.

## Usage

```python
import clipy

@clipy.command()
@clipy.argument("arg1", help="an argument", type=str, required=True)
@clipy.argument("arg2", help="another argument", type=str, required=False)
def main(*_args, arg1, arg2, **_kwargs):
    print("Argument 1:", arg1)
    print("Argument 2:", arg2)

if __name__ == "__main__":
    main()  # pylint: disable=missing-kwoa
```

Then enjoy your CLI tool:

```bash
python script.py --help
python script.py --arg1 value1 --arg2 value2
```

## Installation
```bash
pip install clipyx
```
From Github:
```bash
pip install git+https://github.com/G-Lauz/clipy.git@v0.0.4-pre0
```

Or clone the repository and install it manually:
```bash
git clone https://github.com/G-Lauz/clipy.git
cd clipy
pip install .
```
