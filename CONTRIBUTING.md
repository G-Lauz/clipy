# Contributing to Python Project Template

## Contribution guidelines
This template aim to follow the [Google Python Style Guides](https://google.github.io/styleguide/pyguide.html).

Follow the Docstring guidelines from [Sphinx](https://sphinx-rtd-tutorial.readthedocs.io/en/latest/docstrings.html).

This template layout use an [src-layout](https://setuptools.pypa.io/en/latest/userguide/package_discovery.html#src-layout).

Here's the [test layout](https://docs.pytest.org/en/7.1.x/explanation/goodpractices.html#tests-outside-application-code) used for this template.


## Development environment configuration
In the project root:
```bash
python -m venv .venv

# Depend your environment...
.\.venv\Scripts\activate.bat # on Windows
source .venv/bin/activate # on Ubuntu

python -m pip install --upgrade pip
pip install -e .
pip install -r requirements/dev-requirements.txt
pre-commit install
```

## Version number
In order to change the major or the minor version number you may add `(MAJOR)` or `(MINOR)` within your commit message. The patch number will be automaticly handle e.g.
```bash
git commit -m "TICKET-30 (MINOR) release my-features"
```
See [Semantic Versioning](https://semver.org/) for more information about how semantic version work and when you should do a minor or major version.

## Merge
When merging on `dev` or `main` branch please use a `squash merge`.
