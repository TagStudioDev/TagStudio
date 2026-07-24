---
title: Developing
icon: material/code-braces
---

<!-- SPDX-FileCopyrightText: (c) TagStudio Contributors -->
<!-- SPDX-License-Identifier: GPL-3.0-only -->

# :material-code-braces: Developing

If you wish to develop for TagStudio, you'll need to create a development environment by installing the required dependencies. You have a number of options depending on your level of experience and familiarity with existing Python toolchains.

<!-- prettier-ignore -->
!!! tip "Contributing"
    If you wish to contribute to TagStudio's development, please read our [Contribution Guidelines](contributing.md)!

## Installing Python

Python [3.12](https://www.python.org/downloads) is required to develop for TagStudio. Any version matching "Python 3.12.x" should work, with "x" being any number. Alternatively you can use a tool such as [pyenv](https://github.com/pyenv/pyenv) to install this version of Python without affecting any existing Python installations on your system. Tools such as [uv](#installing-with-uv) can also install Python versions.

<!-- prettier-ignore -->
!!! info "Python Aliases"
    Depending on your system, Python may be called `python`, `py`, `python3`, or `py3`. These instructions use the alias `python` for consistency.

If you already have Python installed on your system, you can check the version by running the following command:

```sh
python --version
```

---

### Installing with pyenv

If you choose to install Python using pyenv, please refer to the following instructions:

1. Follow pyenv's [install instructions](https://github.com/pyenv/pyenv/?tab=readme-ov-file#installation) for your system.
2. Install the appropriate Python version with pyenv by running `pyenv install 3.12` (This will **not** mess with your existing Python installation).
3. Navigate to the repository root folder in your terminal and run `pyenv local 3.12`. You could alternatively use `pyenv shell 3.12` or `pyenv global 3.12` instead to set the Python version for the current terminal session or the entire system respectively, however using `local` is recommended.

---

## Cloning from GitHub

The repository can be cloned/downloaded via `git` in your terminal, or by downloading the zip file from the "Code" button on the [repository page](https://github.com/TagStudioDev/TagStudio).

```sh
git clone https://github.com/TagStudioDev/TagStudio.git
```

## Installing Dependencies

To install the required dependencies, you can use a dependency manager such as [uv](https://docs.astral.sh/uv) (recommended) or [Poetry 2.0](https://python-poetry.org). Alternatively you can create a virtual environment and manually install the dependencies yourself.

### Installing with uv

If using [uv](https://docs.astral.sh/uv), you can install the dependencies for TagStudio with the following command:

```sh
uv pip install -e . --group all
```

TagStudio should now be runnable using the `tagstudio` command.

---

### Installing with Poetry

If using [Poetry](https://python-poetry.org), you can install the dependencies for TagStudio with the following command:

```sh
poetry install --with dev
```

TagStudio should now be runnable using the `tagstudio` command.

---

### Manual Installation

If you choose to manually set up a virtual environment and install dependencies instead of using a dependency manager, please refer to the following instructions:

<!-- prettier-ignore -->
!!! tip "Virtual Environments"
    Learn more about setting up a virtual environment with Python's [official tutorial](https://docs.python.org/3/tutorial/venv.html).

1.  In the root repository directory, create a python virtual environment:

    ```sh
    python -m venv .venv
    ```

2.  Activate your environment:
    - Windows w/Powershell: `.venv\Scripts\Activate.ps1`
    - Windows w/Command Prompt: `.venv\Scripts\activate.bat`
    - Linux/macOS: `source .venv/bin/activate`

    <!-- prettier-ignore -->
    !!! info "Supported Shells"
        Depending on your system, the regular activation script _might_ not work on alternative shells. In this case, refer to the table below for supported shells:

        |      Shell | Script                    |
        | ---------: | :------------------------ |
        |   Bash/ZSH | `.venv/bin/activate`      |
        |       Fish | `.venv/bin/activate.fish` |
        |   CSH/TCSH | `.venv/bin/activate.csh`  |
        | PowerShell | `.venv/bin/activate.ps1`  |

3.  Use the following PIP command to create an editable installation and install the required development dependencies:

    ```sh
    pip install -e . --group all
    ```

4.  TagStudio should now be runnable using the `tagstudio` command.

<!-- prettier-ignore -->
!!! Warning "Linux Library Dependencies"
    If developing TagStudio on Linux, certain libraries are required that may not be included with your distribution. A full list of these can be found [here](install.md#linux).

## Nix & NixOS

If using [Nix](https://nixos.org/), there is a development environment already provided in the [flake](https://wiki.nixos.org/wiki/Flakes) that is accessible with the following command:

```sh
nix develop
```

A reference `.envrc` is provided for use with [direnv](#direnv), see [`contrib/.envrc-nix`](https://github.com/TagStudioDev/TagStudio/blob/main/contrib/.envrc-nix).

## Tooling

### Editor Integration

The entry point for TagStudio is `src/tagstudio/main.py`. You can target this file from your IDE to run or connect a debug session. The example(s) below show off example launch scripts for different IDEs. Here you can also take advantage of [launch arguments](./usage.md/#launch-arguments) to pass your own test [libraries](libraries.md) to use while developing. You can find more editor configurations in [`contrib`](https://github.com/TagStudioDev/TagStudio/tree/main/contrib).

<!-- prettier-ignore -->
=== "VS Code"
    ```json title=".vscode/launch.json"
    {
        "version": "0.2.0",
        "configurations": [
            {
                "name": "TagStudio",
                "type": "python",
                "request": "launch",
                "program": "${workspaceRoot}/src/tagstudio/main.py",
                "console": "integratedTerminal",
                "justMyCode": true,
                "args": ["-o", "~/Documents/Example"]
            }
        ]
    }
    ```

<!-- prettier-ignore -->
!!! tip
    To format the code automatically before each commit, there's a configured action available for the `pre-commit` hook. Install it by running `pre-commit install`. The hook will be executed each time on running `git commit`.

### Ruff

[Ruff](https://github.com/astral-sh/ruff) is a Python linter and code formatter that helps enforce a consistent formatting style across our codebase.

Ruff is installed alongside the `pip install -e . --group all` command, but is also available as a VS Code [extension](https://marketplace.visualstudio.com/items?itemName=charliermarsh.ruff), PyCharm [plugin](https://plugins.jetbrains.com/plugin/20574-ruff), and [more](https://docs.astral.sh/ruff/integrations/).

```sh title="Lint Code"
ruff check

# Apply automatic fixes with
ruff check --fix
```

```sh title="Format Code"
ruff format
```

Ruff should automatically discover the configuration options inside the [pyproject.toml](https://github.com/TagStudioDev/TagStudio/blob/main/pyproject.toml) file. For more information, see the [ruff configuration discovery docs](https://docs.astral.sh/ruff/configuration/#config-file-discovery).

### Pyright

[Pyright](https://github.com/microsoft/pyright) is a static type checker for Python that helps enforce type strictness and prevent easy-to-miss errors across our codebase.

Pyright is installed alongside the `pip install -e . --group all` command, but is also available as VS Code extensions (see the [Pyright](https://marketplace.visualstudio.com/items?itemName=ms-pyright.pyright), [Pylance](https://marketplace.visualstudio.com/items?itemName=ms-python.vscode-pylance), and [basedpyright](https://marketplace.visualstudio.com/items?itemName=detachhead.basedpyright) extensions), a PyCharm [setting](https://www.jetbrains.com/help/pycharm/lsp-tools.html#pyright), or in the form of forks such as [basedpyright](https://docs.basedpyright.com/latest/).

```sh title="Run Checks"
pyright
```

Pyright/basedpyright should automatically discover the configuration options inside the [pyproject.toml](https://github.com/TagStudioDev/TagStudio/blob/main/pyproject.toml) file.

### Pytest

[Pytest](https://github.com/pytest-dev/pytest) runs our Python code against the tests inside the [`tests/`](https://github.com/TagStudioDev/TagStudio/tree/main/tests) directory.

Pytest is installed alongside the `pip install -e . --group all` command.

```sh title="Run Tests"
pytest tests/
```

### pre-commit

There is a [pre-commit](https://pre-commit.com/) configuration that will run through some checks before code is committed. Namely Pyright and Ruff will check your code, catching those nits right away.

Once you have pre-commit installed, just run:

```sh
pre-commit install
```

From there, Git will automatically run through the hooks during commit actions!

### direnv

You can automatically enter this development shell, and keep your user shell, with a tool like [direnv](https://direnv.net/). Some reference `.envrc` files are provided in the repository at [`contrib`](https://github.com/TagStudioDev/TagStudio/tree/main/contrib).

Two currently available are for [Nix](#nix-nixos) and [uv](#installing-with-uv), to use one:

```sh
ln -s .envrc-$variant .envrc
```

You will have to allow usage of it.

<!-- prettier-ignore -->
!!! warning "direnv Security Framework"
    These files are generally a good idea to check, as they execute commands on directory load. direnv has a security framework to only run `.envrc` files you have allowed, and does keep track on if it has changed. So, with that being said, the file may need to be allowed again if modifications are made.

```sh
cat .envrc # You are checking them, right?
direnv allow
```

## Building

To build your own executables of TagStudio, first follow the steps in "[Installing Dependencies](#installing-dependencies)." Once that's complete, run the following PyInstaller command:

```
pyinstaller scripts/tagstudio.spec
```

If you're on Windows or Linux and wish to build a portable executable, then pass the following flag:

```
pyinstaller scripts/tagstudio.spec -- --portable
```

The resulting executable file(s) will be located in a new folder named "dist".
