# Contributing to TagStudio

_Last Updated: March 8th, 2025_

Thank you so much for showing interest in contributing to TagStudio! Here are a set of instructions and guidelines for contributing code or documentation to the project. This document will change over time, so make sure that your contributions still line up with the requirements here before submitting a pull request.

## Getting Started

-   Check the [Feature Roadmap](/docs/updates/roadmap.md) page to see what priority features there are, the [FAQ](/README.md/#faq), as well as the project's [Issues](https://github.com/TagStudioDev/TagStudio/issues) and [Pull Requests](https://github.com/TagStudioDev/TagStudio/pulls).
-   If you'd like to add a feature that isn't on the feature roadmap or doesn't have an open issue, **PLEASE create a feature request** issue for it discussing your intentions so any feedback or important information can be given by the team first.
    -   We don't want you wasting time developing a feature or making a change that can't/won't be added for any reason ranging from pre-existing refactors to design philosophy differences.
-   **Please don't** create pull requests that consist of large refactors, _especially_ without discussing them with us first. These end up doing more harm than good for the project by continuously delaying progress and disrupting everyone else's work.
-   If you wish to discuss TagStudio further, feel free to join the [Discord Server](https://discord.com/invite/hRNnVKhF2G)!

### Contribution Checklist

-   I've read the [Feature Roadmap](/docs/updates/roadmap.md) page
-   I've read the [FAQ](/README.md/#faq), including the "[Features I Likely Won't Add/Pull](/README.md/#features-i-likely-wont-addpull)" section
-   I've checked the project's [Issues](https://github.com/TagStudioDev/TagStudio/issues) and [Pull Requests](https://github.com/TagStudioDev/TagStudio/pulls)
-   **I've created a new issue for my feature/fix _before_ starting work on it**, or have at least notified others in the relevant existing issue(s) of my intention to work on it
-   I've set up my development environment including Ruff, Mypy, and PyTest
-   I've read the [Code Guidelines](#code-guidelines) and/or [Documentation Guidelines](#documentation-guidelines)
-   **_I mean it, I've found or created an issue for my feature/fix!_**

> [!NOTE]
> If the fix is small and self-explanatory (i.e. a typo), then it doesn't require an issue to be opened first. Issue tracking is supposed to make our lives easier, not harder. Please use your best judgement to minimize the amount of work for everyone involved.

## Creating a Development Environment

If you wish to develop for TagStudio, you'll need to create a development environment by installing the required dependencies. You have a number of options depending on your level of experience and familiarly with existing Python toolchains.

If you know what you're doing and have developed for Python projects in the past, you can get started quickly with the "Brief Instructions" below. Otherwise, please see the full instructions on the documentation website for "[Creating a Development Environment](https://docs.tagstud.io/install/#creating-a-development-environment)".

### Brief Instructions

1.  Have [Python 3.12](https://www.python.org/downloads/) and PIP installed. Also have [FFmpeg](https://ffmpeg.org/download.html) installed if you wish to have audio/video playback and thumbnails.
2.  Clone the repository to the folder of your choosing:
    ```
    git clone https://github.com/TagStudioDev/TagStudio.git
    ```
3.  Use a dependency manager such as [uv](https://docs.astral.sh/uv/) or [Poetry 2.0](https://python-poetry.org/blog/category/releases/) to install the required dependencies, or alternatively create and activate a [virtual environment](https://docs.tagstud.io/install/#manual-installation) with `venv`.

4.  If using a virtual environment instead of a dependency manager, install an editable version of the program and development dependencies with the following PIP command:

    ```
    pip install -e ".[dev]"
    ```

    Otherwise, modify the command above for use with your dependency manager of choice. For example if using uv, you may use this:

    ```
    uv pip install -e ".[dev]"
    ```

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

-   **(First time only)** Run the following:
    -   `mkdir -p .mypy_cache`
    -   `mypy --install-types --non-interactive`
-   You can now check code by running `mypy --config-file pyproject.toml .` in the repository root. _(Don't forget the "." at the end!)_

Mypy is also available as a VS Code [extension](https://marketplace.visualstudio.com/items?itemName=matangover.mypy), PyCharm [plugin](https://plugins.jetbrains.com/plugin/11086-mypy), and [more](https://plugins.jetbrains.com/plugin/11086-mypy).

### PyTest

-   Run all tests by running `pytest tests/` in the repository root.

## Code Style

Most of the style guidelines can be checked, fixed, and enforced via Ruff. Older code may not be adhering to all of these guidelines, in which case _"do as I say, not as I do"..._

-   Do your best to write clear, concise, and modular code.
-   Keep a maximum column with of no more than **100** characters.
-   Code comments should be used to help describe sections of code that can't speak for themselves.
-   Use [Google style](https://google.github.io/styleguide/pyguide.html#s3.8-comments-and-docstrings) docstrings for any classes and functions you add.
    -   If you're modifying an existing function that does _not_ have docstrings, you don't _have_ to add docstrings to it... but it would be pretty cool if you did ;)
-   Imports should be ordered alphabetically.
-   Lists of values should be ordered using their [natural sort order](https://en.wikipedia.org/wiki/Natural_sort_order).
    -   Some files have their methods ordered alphabetically as well (i.e. [`thumb_renderer`](https://github.com/TagStudioDev/TagStudio/blob/main/src/tagstudio/qt/widgets/thumb_renderer.py)). If you're working in a file and notice this, please try and keep to the pattern.
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
> Force pushing makes it impossible to discern which changes have already been reviewed and which haven't. This means a reviewer will then have to re-review all the already reviewed code, which is a lot of unnecessary work for reviewers.

> [!TIP]
> If you're unsure where to stop the scope of your PR, ask yourself: _"If I broke this up, could any parts of it still be used by the project in the meantime?"_

### Runtime Requirements

-   Final code must function on supported versions of Windows, macOS, and Linux:
    -   Windows: 10, 11
    -   macOS: 13.0+
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
