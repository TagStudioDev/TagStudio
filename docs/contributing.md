---
title: Contributing
icon: material/file-plus
---

<!-- SPDX-FileCopyrightText: (c) TagStudio Contributors -->
<!-- SPDX-License-Identifier: GPL-3.0-only -->

# :material-file-plus: Contribution Guidelines

Thank you so much for showing interest in contributing to TagStudio! This page goes over the instructions and guidelines for contributing to the TagStudio. This page will change over time, so make sure that your contributions still line up with the current guidelines before submitting a pull request.

If you wish to discuss TagStudio further, feel free to join the [Discord Server](https://discord.com/invite/hRNnVKhF2G)!

## :material-order-bool-ascending-variant: Contribution Checklist

#### All Contributions

- [x] I've read the Contribution Guidelines (this page) and the [Style Guide](style.md)
- [x] I've read the [FAQ](https://github.com/TagStudioDev/TagStudio/blob/main/README.md#faq)
- [x] I've checked the project's [pull requests](https://github.com/TagStudioDev/TagStudio/pulls) for any existing or conflicting PRs
- [x] I've set up my [development environment](developing.md) including [Ruff](developing.md#ruff), [Pyright](developing.md#pyright), and [Pytest](developing.md#pytest)

#### Feature Additions

- [x] I've read the [Roadmap](roadmap.md) and understand what core features are planned, their priorities, and their scheduled timelines
- [x] I've found an existing [feature request](https://github.com/TagStudioDev/TagStudio/issues) or created my own **_before starting work on a feature_** so that the feature can be discussed beforehand

<!-- prettier-ignore -->
!!! danger "Before Developing Features"
    **PLEASE** open a [feature request](https://github.com/TagStudioDev/TagStudio/issues) or ensure that one already exists **_before you begin work on the feature_**. This allows us to discuss the feature idea beforehand, approve or reject it, and give any specific implementation requirements. We **do not want** to have to close pull requests because they add features that conflict with the project's goals, guidelines, or other planned features.

#### Fixes

- [x] I've found an existing [bug report](https://github.com/TagStudioDev/TagStudio/issues) or created my own for this fix _(as long as the fix is substantial enough to warrant opening a bug report for)_

<!-- prettier-ignore -->
!!! note "Issue Exceptions for Small Fixes"
    If the fix is small and self-explanatory (e.g. a typo), then it doesn't require an issue to be opened first. Issue tracking is supposed to make our lives easier, not harder. Please use your best judgement to minimize the amount of work for everyone involved.

## :material-thumb-down:{.red} Unacceptable Code

The following types of code will **NOT** be accepted to the project:

- Code that does not follow the [Contribution Checklist](#contribution-checklist) or violates the Contribution Guidelines
- Large refactors that have not been discussed with us first
    - These types of refactors end up doing more harm than good for the project by continuously delaying progress and disrupting everyone else's work
- Other people/projects' code that is used without consent or does not have a [compatible license](#licenses)
- Code that you do not understand and/or cannot explain (i.e. "vibe coding")
- Code that adds a drastic amount of complexity with minimal utility

---

## :material-license: Licenses

As of May 2026, the TagStudio project has begun migrating to different licenses for different sections of the codebase where possible. Any new code contributed inside the "core" of TagStudio must be under the [MIT license](https://github.com/TagStudioDev/TagStudio/blob/main/LICENSES/MIT.txt), while any code specific to the Qt frontend is to remain under [GPL-3.0](https://github.com/TagStudioDev/TagStudio/blob/main/LICENSES/GPL-3.0-only.txt) where possible.

<!-- prettier-ignore -->
!!! question "Relicensing Process"
    Existing GPL-3.0 core code is **only** migrated to MIT if all of the original contributors have given their consent, or if the code becomes replaced by a significantly different implementation.

Licensing is now accomplished using the [REUSE](https://reuse.software/spec-3.3/) specification. This means that each file is licensed separately, with text files having a comment header with the license and copyright and other files having this information declared in the [RESUSE.toml](https://github.com/TagStudioDev/TagStudio/blob/main/REUSE.toml) file.

<!-- prettier-ignore-start -->
=== "Python GPL-3.0 Comment"
    ```py
    # SPDX-FileCopyrightText: (c) TagStudio Contributors
    # SPDX-License-Identifier: GPL-3.0-only
    ```
=== "Python MIT Comment"
    ```py
    # SPDX-FileCopyrightText: (c) TagStudio Contributors
    # SPDX-License-Identifier: MIT
    ```
=== "Markdown/HTML Comment"
    ```html
    <!-- SPDX-FileCopyrightText: (c) TagStudio Contributors -->
    <!-- SPDX-License-Identifier: GPL-3.0-only -->
    ```
=== "CSS Comment"
    ```css
    /*
     * SPDX-FileCopyrightText: (c) TagStudio Contributors
     * SPDX-License-Identifier: GPL-3.0-only
     */
    ```
<!-- prettier-ignore-end -->

#### Types of Files That Should Be MIT

- Backend code that supports TagStudio's core systems, irrespective of the frontend used
    - e.g. The database backend for storing TagStudio data, the search query system, database tests, etc.
- Frontend code for the CLI _(to be developed)_
- Platform-agnostic thumbnail extraction, rendering, and caching
- Translations added to an MIT-labeled [Weblate](https://hosted.weblate.org/projects/tagstudio/) component

#### Types of Files That Should Be GPL-3.0

- Code for the Qt frontend
    - e.g. Qt widgets, views, controllers, Qt rendering code, Qt tests, etc.

---

## :material-code-braces-box: Commits and Pull Requests

- Use [Conventional Commits](https://www.conventionalcommits.org/en/v1.0.0) as a guideline for commit messages. This allows us to easily generate changelogs for releases.
    - See some [examples](https://www.conventionalcommits.org/en/v1.0.0/#examples) of what this looks like in practice.
- Use clear and concise commit messages. If your commit does too much, either consider breaking it up into smaller commits or providing extra detail in the commit description.
- Pull requests should have an adequate title and description which clearly outline your intentions and changes/additions. Feel free to provide screenshots, GIFs, or videos, especially for UI changes.
- Pull requests should ideally be limited to a **single** feature or fix.

<!-- prettier-ignore -->
!!! danger "Force Pushing"
    **Please do not force push if your PR is open for review!** Force pushing makes it impossible to discern which changes have already been reviewed and which haven't. This means a reviewer will then have to re-review all the already reviewed code, which is a lot of unnecessary work for reviewers.

<!-- prettier-ignore -->
!!! tip "PR Scope"
    If you're unsure where to stop the scope of your PR, ask yourself: _"If I broke this up, could any parts of it still be used by the project in the meantime?"_

### Workflow Checks

When pushing your code, several automated [workflows](https://github.com/TagStudioDev/TagStudio/tree/main/.github/workflows) will check it against predefined tests and style checks. It's _highly recommended_ that you run these checks locally beforehand to avoid having to fight back-and-forth with the workflow checks inside your pull requests. These checks currently include:

- [Ruff](developing.md#ruff) [`check`](https://docs.astral.sh/ruff/linter) and [`format`](https://docs.astral.sh/ruff/formatter/) (read-only)
- [Pyright](developing.md#pyright) type checking
- [Pytest](developing.md#pytest) tests
- REUSE [license compliance](#licenses)

### Runtime Requirements

Code must function on all of the supported operating systems and versions:

- Windows 10 & 11
- macOS 14.0+
- Common Linux distributions and versions

## :material-file-document: Documentation Guidelines

Documentation contributions include anything inside of the `docs/` folder as well as the `README.md`. Documentation inside the `docs/` folder is built and hosted on our static documentation site, [docs.tagstud.io](https://docs.tagstud.io/).

- Use "[dash-case / kebab-case](https://developer.mozilla.org/en-US/docs/Glossary/Kebab_case)" for file and folder names
- Follow the folder structure pattern
- Don't add images or other media with excessively large file sizes
- Provide alt text for embedded media
- Use "[Title Case](https://apastyle.apa.org/style-grammar-guidelines/capitalization/title-case)" for title capitalization

## :material-translate: Translation Guidelines

Translations are performed on the TagStudio [Weblate project](https://hosted.weblate.org/projects/tagstudio/).

_Translation guidelines coming soon._
