# Contributing to TagStudio

_Last Updated: January 30th, 2025_

Thank you so much for showing interest in contributing to TagStudio! Here are a set of instructions and guidelines for contributing code or documentation to the project. This document will change over time, so make sure that your contributions still line up with the requirements here before submitting a pull request.

## Getting Started

-   Check the [Feature Roadmap](/docs/updates/roadmap.md) page to see what priority features there are, the [FAQ](/README.md/#faq), as well as the open [Issues](https://github.com/TagStudioDev/TagStudio/issues) and [Pull Requests](https://github.com/TagStudioDev/TagStudio/pulls).
-   If you'd like to add a feature that isn't on the feature roadmap or doesn't have an open issue, **PLEASE create a feature request** issue for it discussing your intentions so any feedback or important information can be given by the team first.
    -   We don't want you wasting time developing a feature or making a change that can't/won't be added for any reason ranging from pre-existing refactors to design philosophy differences.
-   **Please don't** create pull requests that consist of large refactors, _especially_ without discussing them with us first. These end up doing more harm than good for the project by continuously delaying progress and disrupting everyone else's work.
-   If you wish to discuss TagStudio further, feel free to join the [Discord Server](https://discord.com/invite/hRNnVKhF2G)

### Contribution Checklist

-   I've read the [Feature Roadmap](/docs/updates/roadmap.md) page
-   I've read the [FAQ](/README.md/#faq), including the "[Features I Likely Won't Add/Pull](/README.md/#features-i-likely-wont-addpull)" section
-   I've checked the open [Issues](https://github.com/TagStudioDev/TagStudio/issues) and [Pull Requests](https://github.com/TagStudioDev/TagStudio/pulls)
-   **I've created a new issue for my feature/fix _before_ starting work on it**, or have at least notified others in the relevant existing issue(s) of my intention to work on it
-   I've set up my development environment including Ruff, Mypy, and PyTest
-   I've read the [Code Guidelines](#code-guidelines) and/or [Documentation Guidelines](#documentation-guidelines)
-   **_I mean it, I've found or created an issue for my feature/fix!_**

> [!NOTE]
> If the fix is small and self-explanatory (i.e. a typo), then it doesn't require an issue to be opened first. Issue tracking is supposed to make our lives easier, not harder. Please use your best judgement to minimize the amount of work involved for everyone involved.

## Creating a Development Environment

### Prerequisites

-   [Python](https://www.python.org/downloads/) 3.12
-   [Ruff](https://github.com/astral-sh/ruff) (Included in `requirements-dev.txt`)
-   [Mypy](https://github.com/python/mypy) (Included in `requirements-dev.txt`)
-   [PyTest](https://docs.pytest.org) (Included in `requirements-dev.txt`)

### Creating a Python Virtual Environment

If you wish to launch the source version of TagStudio outside of your IDE:

> [!IMPORTANT]
> Depending on your system, Python may be called `python`, `py`, `python3`, or `py3`. These instructions use the alias `python3` for consistency. You can check to see which alias your system uses and if it's for the correct Python version by typing `python3 --version` (or whichever alias) into your terminal.

> [!TIP]
> On Linux and macOS, you can launch the `tagstudio.sh` script to skip the following process, minus the `requirements-dev.txt` installation step. _Using the script is fine if you just want to launch the program from source._

1. Make sure you're using the correct Python version:
   -   If the output matches `Python 3.12.x` (where the x is any number) then you're using the correct Python version and can skip to step 2. Otherwise, you can install the correct Python version from the [Python](https://www.python.org/downloads/) website, or you can use a tool like [pyenv](https://github.com/pyenv/pyenv/) to install the correct version without changes to your system:
      1. Follow pyenv's [install instructions](https://github.com/pyenv/pyenv/?tab=readme-ov-file#installation) for your system.
      2. Install the appropriate Python version with pyenv by running `pyenv install 3.12` (This will **not** mess with your existing Python installation).
      3. Navigate to the repository root folder in your terminal and run `pyenv local 3.12`.
      - You could alternatively use `pyenv shell 3.12` or `pyenv global 3.12` instead to set the Python version for the current terminal session or the entire system respectively, however using `local` is recommended.

2. In the root repository directory, create a python virtual environment:  
   `python3 -m venv .venv`
3. Activate your environment:

-   Windows w/Powershell: `.venv\Scripts\Activate.ps1`
-   Windows w/Command Prompt: `.venv\Scripts\activate.bat`
-   Linux/macOS: `source .venv/bin/activate`
       Depending on your system, the regular activation script *might* not work on alternative shells. In this case, refer to the table below for supported shells:
       |Shell   |Script                   |
       |-------:|:------------------------|
       |Bash/ZSH|`.venv/bin/activate`     |
       |Fish    |`.venv/bin/activate.fish`|
       |CSH/TCSH|`.venv/bin/activate.csh` |
       |PWSH    |`.venv/bin/activate.ps1` |
       

4. Install the required packages:

-   `pip install -r requirements.txt`
-   If developing (includes Ruff and Mypy): `pip install -r requirements-dev.txt`

_Learn more about setting up a virtual environment [here](https://docs.python.org/3/tutorial/venv.html)._

### Manually Launching (Outside of an IDE)

If you encounter errors about the Python version, or seemingly vague script errors, [pyenv](https://github.com/pyenv/pyenv/) may solve your issue. See step 1 of [Creating a Python Virtual Environment](#creating-a-python-virtual-environment).

-   **Windows** (start_win.bat)

    -   To launch TagStudio, launch the `start_win.bat` file. You can modify this .bat file or create a shortcut and add one or more additional arguments if desired.

-   **Linux/macOS** (TagStudio.sh)

    -   Run the "TagStudio.sh" script and the program should launch! (Make sure that the script is marked as executable if on Linux). Note that launching from the script from outside of a terminal will not launch a terminal window with any debug or crash information. If you wish to see this information, just launch the shell script directly from your terminal with `./TagStudio.sh`.

    -   **NixOS** (Nix Flake)
        -   Use the provided [Flake](https://nixos.wiki/wiki/Flakes) to create and enter a working environment by running `nix develop`. Then, run the program via `python3 tagstudio/tag_studio.py` from the root directory.

> [!WARNING]
> Support for NixOS is still a work in progress.

-   **Any** (No Scripts)

    -   Alternatively, with the virtual environment loaded, run the python file at `tagstudio\tag_studio.py` from your terminal. If you're in the project's root directory, simply run `python3 tagstudio/tag_studio.py`.

## Workflow Checks

When pushing your code, several automated workflows will check it against predefined tests and style checks. It's _highly recommended_ that you run these checks locally beforehand to avoid having to fight back-and-forth with the workflow checks inside your pull requests.

> [!TIP]
> To format the code automatically before each commit, there's a configured action available for the `pre-commit` hook. Install it by running `pre-commit install`. The hook will be executed each time on running `git commit`.

### [Ruff](https://github.com/astral-sh/ruff)

A Python linter and code formatter. Ruff uses the `pyproject.toml` as its config file and runs whenever code is pushed or pulled into the project.

#### Running Locally

Inside the root repository directory:

-   Lint code with `ruff check`
    -   Some linting suggestions can be automatically formatted with `ruff check --fix`
-   Format code with `ruff format`

Ruff should automatically discover the configuration options inside the [pyproject.toml](https://github.com/TagStudioDev/TagStudio/blob/main/pyproject.toml) file. For more information, see the [ruff configuration discovery docs](https://docs.astral.sh/ruff/configuration/#config-file-discovery).

Ruff is also available as a VS Code [extension](https://marketplace.visualstudio.com/items?itemName=charliermarsh.ruff), PyCharm [plugin](https://plugins.jetbrains.com/plugin/20574-ruff), and [more](https://docs.astral.sh/ruff/integrations/).

### [Mypy](https://github.com/python/mypy)

Mypy is a static type checker for Python. It sure has a lot to say sometimes, but we recommend you take its advice when possible. Mypy also uses the `pyproject.toml` as its config file and runs whenever code is pushed or pulled into the project.

#### Running Locally

-   **First time only:** Move into the `/tagstudio` directory with `cd tagstudio` and run the following:
    -   `mkdir -p .mypy_cache`
    -   `mypy --install-types --non-interactive`
-   Check code by moving into the `/tagstudio` directory with `cd tagstudio` _(if you aren't already inside)_ and running `mypy --config-file ../pyproject.toml .`. _(Don't forget the `.` at the end!)_

Mypy is also available as a VS Code [extension](https://marketplace.visualstudio.com/items?itemName=matangover.mypy), PyCharm [plugin](https://plugins.jetbrains.com/plugin/11086-mypy), and [more](https://plugins.jetbrains.com/plugin/11086-mypy).

### PyTest

-   Run all tests by moving into the `/tagstudio` directory with `cd tagstudio` and running `pytest tests/`.

## Code Style

Most of the style guidelines can be checked, fixed, and enforced via Ruff. Older code may not be adhering to all of these guidelines, in which case _"do as I say, not as I do"..._

-   Do your best to write clear, concise, and modular code.
-   Keep a maximum column with of no more than **100** characters.
-   Code comments should be used to help describe sections of code that can't speak for themselves.
-   Use [Google style](https://google.github.io/styleguide/pyguide.html#s3.8-comments-and-docstrings) docstrings for any classes and functions you add.
    -   If you're modifying an existing function that does _not_ have docstrings, you don't _have_ to add docstrings to it... but it would be pretty cool if you did ;)
-   Imports should be ordered alphabetically.
-   Lists of values should be ordered using their [natural sort order](https://en.wikipedia.org/wiki/Natural_sort_order).
    -   Some files have their methods ordered alphabetically as well (i.e. [`thumb_renderer`](https://github.com/TagStudioDev/TagStudio/blob/main/tagstudio/src/qt/widgets/thumb_renderer.py)). If you're working in a file and notice this, please try and keep to the pattern.
-   When writing text for window titles or form titles, use "[Title Case](https://apastyle.apa.org/style-grammar-guidelines/capitalization/title-case)" capitalization. Your IDE may have a command to format this for you automatically, although some may incorrectly capitalize short prepositions. In a pinch you can use a website such as [capitalizemytitle.com](https://capitalizemytitle.com/) to check.
-   If it wasn't mentioned above, then stick to [**PEP-8**](https://peps.python.org/pep-0008/)!

### Modules & Implementations

-   **Do not** modify legacy library code in the `src/core/library/json/` directory
-   Avoid direct calls to `os`
    -   Use `Pathlib` library instead of `os.path`
    -   Use `platform.system()` instead of `os.name` and `sys.platform`
-   Don't prepend local imports with `tagstudio`, stick to `src`
-   Use the `logger` system instead of `print` statements
-   Avoid nested f-strings
-   Use HTML-like tags inside Qt widgets over stylesheets where possible

### Commit and Pull Request Style

-   Use [Conventional Commits](https://www.conventionalcommits.org/en/v1.0.0) as a guideline for commit messages. This allows us to easily generate changelogs for releases.
    -   See some [examples](https://www.conventionalcommits.org/en/v1.0.0/#examples) of what this looks like in practice.
-   Use clear and concise commit messages. If your commit does too much, either consider breaking it up into smaller commits or providing extra detail in the commit description.
-   Pull requests should have an adequate title and description which clearly outline your intentions and changes/additions. Feel free to provide screenshots, GIFs, or videos, especially for UI changes.
-   Pull requests should ideally be limited to **a single** feature or fix.

> [!IMPORTANT]
> Please do not force push if your PR is open for review!
>
> Force pushing makes it impossible to discern which changes have already been reviewed and which haven't. This means a reviewer will then have to rereview all the already reviewed code, which is a lot of unnecessary work for reviewers.

> [!TIP]
> If you're unsure where to stop the scope of your PR, ask yourself: _"If I broke this up, could any parts of it still be used by the project in the meantime?"_

### Runtime Requirements

-   Final code must function on supported versions of Windows, macOS, and Linux:
    -   Windows: 10, 11
    -   macOS: 12.0+
    -   Linux: _Varies_
-   Final code must **_NOT:_**
    -   Contain superfluous or unnecessary logging statements
    -   Cause unreasonable slowdowns to the program outside of a progress-indicated task
    -   Cause undesirable visual glitches or artifacts on screen

## Documentation Guidelines

Documentation contributions include anything inside of the `docs/` folder, as well as the `README.md` and `CONTRIBUTING.md` files. Documentation inside the `docs/` folder is built and hosted on our static documentation site, [docs.tagstud.io](https://docs.tagstud.io/).

-   Use "[snake_case](https://developer.mozilla.org/en-US/docs/Glossary/Snake_case)" for file and folder names
-   Follow the folder structure pattern
-   Don't add images or other media with excessively large file sizes
-   Provide alt text for all embedded media
-   Use "[Title Case](https://apastyle.apa.org/style-grammar-guidelines/capitalization/title-case)" for title capitalization

## Translation Guidelines

Translations are performed on the TagStudio [Weblate project](https://hosted.weblate.org/projects/tagstudio/).

_Translation guidelines coming soon._
