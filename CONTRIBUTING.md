# Contributing
Thanks you for your interest in contributing to `clipy`. We welcome contributions of all kinds, including bug reports, feature requests, documentation improvements, writing tests, and code contributions.

Here are some guidelines to help you get started:

## Project Structure
This project use an [**src-layout**](https://setuptools.pypa.io/en/latest/userguide/package_discovery.html#src-layout) for the source code and a [**tests-outside layout**](https://docs.pytest.org/en/7.1.x/explanation/goodpractices.html#tests-outside-application-code). As shown in this simple example:
```.
├── examples/
├── src/
│   └── clipy/
└── tests/
```

## Branching Strategy
Three type of branches are used in this project:
| Branch | Purpose |
| --- | --- |
| `main` | The stable branch, which contains the latest stable release. |
| `dev` | The development branch, which contains the latest changes and features that are being developed. |
| others | The experimental branches, which are used for testing major breaking changes or big refactors. |

## Coding Style
This project aim to follow the [**Google Python Style Guides**](https://google.github.io/styleguide/pyguide.html). We also try to follow the [**Google Docstring guidelines**](https://google.github.io/styleguide/pyguide.html#381-docstrings)

**Key points**:
- Prefer clarity over cleverness.
- Use descriptive variable and function names.
- Use type hints whenever possible.
- Use docstrings to document public functions and classes.

Code quality is enforce by `pre-commit` hooks, which run, among other things, `black`, `isort`, and `pylint` on the codebase before each commit when the hooks are installed. You can also run these tools manually to check your code before committing:
```bash
pre-commit run --all-files
```

## Development Environment Configuration
It is highly recommended to use a virtual environment for development to avoid dependency conflicts. Here's how you can set up a virtual environment using `venv`:

In the project root:
```bash
python -m venv .venv

# Activate your environment
.\.venv\Scripts\activate.bat # on Windows
source .venv/bin/activate # on Ubuntu

# Install dependencies
python -m pip install --upgrade pip
pip install -e .
pip install -r requirements/dev-requirements.txt

# Install pre-commit hooks
pre-commit install
```

## Pull Request Guidelines
A pull request should follow these guidelines to ensure a smooth review process:
- The pull request should include a clear and descriptive title and description of the changes made.
- The pull request should reference any related issues when applicable.
- The pull request should be focused on a single feature or bug fix to make it easier to review.
- The pull request should include unit tests for new features or to cover any bug fixes.
- The pull request should pass all tests and linters.
- The pull request should be based on the latest `dev` or the appropriate experimental branch to avoid merge conflicts.

### Opening a Pull Request
1. Fork the repository and create a new branch for your feature or bug fix.
2. Make your changes.
3. Include unit tests for new features or to cover any bug fixes.
4. Make sure all tests and linters pass (usually handled by `pre-commit` hooks).
5. Commit with a clear and descriptive message.
6. Open a pull request targeting the `dev` branch or the appropriate experimental branch.

## Version Number
> **Help wanted:** The current scheme/pipeline for versioning doesn't seems right, so if you have any suggestion please open an issue or a pull request.

Version bump are derived from commit message. Those message should be used only for commits that are merged from `dev` to `main`. In order to bump a version number you may add the appropriate tag within your commit message. The patch number will be automaticly handle.

| Tag | Meaning |
| --- | --- |
| `(MAJOR)` | This change introduce a breaking change or a significant modification. |
| `(MINOR)` | This change introduces a new feature or enhancement. |
| none | This change are the patch version, which include bug fixes, documentation updates, and other minor changes. |

Example:
```bash
git commit -m "(MINOR) release my-features"
```
See [Semantic Versioning](https://semver.org/) for more information about how semantic version work and when you should do a minor or major version.

## Merge
When merging on `dev` or `main` branch please use a `squash and merge` merge to keep the ocmmit history clean.
