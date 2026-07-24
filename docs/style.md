---
title: Style Guide
icon: material/sign-text
---

<!-- SPDX-FileCopyrightText: (c) TagStudio Contributors -->
<!-- SPDX-License-Identifier: GPL-3.0-only -->

<!-- prettier-ignore -->
!!! abstract "Prerequisite Reading"
    This guide assumes you've read the [Developing](developing.md) and [Contributing](contributing.md) pages first.

# :material-sign-text: Style Guide

## :material-script-text: General Principles

- Write **clear**, **concise**, and **modular** code.
- If the purpose of a peice of code is not obvious, a **short comment** should help explain it.
- Remember to follow the rest of the [contribution guidelines](contributing.md)!

---

## :material-text-box-check: Formatting

Linting in Python files is mostly taken care of by [ruff](developing.md#ruff) and is based on the rules declared in `pyproject.toml` and `.editorconfig`.

TagStudio provides an [EditorConfig](https://editorconfig.org/#example-file) file ([`.editorconfig`](https://github.com/TagStudioDev/TagStudio/blob/main/.editorconfig)) along with a [Prettier](https://prettier.io/) config file ([`.prettierrc.toml`](https://github.com/TagStudioDev/TagStudio/blob/main/.prettierrc.toml)) for formatting files other than .py files (Markdown, JSON, YAML, HTML, CSS, etc.). If editing these types of files it's recommended that you use a formatter that supports EditorConfig or has its settings matched to the EditorConfig and Prettier configs. Lastly, please pay attention to the `prettier-ignore` flags in present in some files if you are not using Prettier, as formatting these sections will break formatting used elsewhere such as the [MkDocs site](https://docs.tagstud.io/).

### :material-code-braces-box: Syntax Guidelines

- Python files should always follow the [**PEP 8**]() style guide conventions, unless specifically allowed otherwise.
    - The most notable exception in our project is the line length limit of **100** characters, which is enforced via ruff.
    - Internal Qt methods also use `camelCase` instead of `snake_case`, so overrides of those are commonly seen in the codebase.
- Classes and attributes considered to be "[private](https://docs.python.org/3/tutorial/classes.html#private-variables)" should be prepended with a **single underscore** (e.g. `_internal_method()`).
    - If _functionally necessary_, an attribute name may be prepended with a double underscore to trigger "[name mangling](https://docs.python.org/3/reference/expressions.html#private-name-mangling)" (e.g. `__mangled_method()`).
- Classes and methods should contain [Google style](https://google.github.io/styleguide/pyguide.html#s3.8-comments-and-docstrings) docstrings _(this style is enforced via ruff)_.
- Lists and JSON keys should be ordered by their [natural sort order](https://en.wikipedia.org/wiki/Natural_sort_order) unless otherwise specified or readily indicated.
- Some files have some or all of their attributes sorted. Please respect any established patterns like these in files you modify.

---

## :material-filter-cog: Modules & Systems

### :fontawesome-brands-python: Python Modules

- Use `Pathlib` library instead of `os.path`
- Use `platform.system()` instead of `os.name` or `sys.platform`
- Avoid nested f-strings

### :material-tag: TagStudio Systems

- Translation keys can be accessed via bracket notation (e.g. `Translations["translation_key"]`) or with the `Translations.format()` method when a value needs to be passed to a placeholder in the translation.
- Use HTML-like tags inside strings over explicit stylesheets where possible. The `Style` class provides several handy methods for formatting text with these.
- Use the `format` method in the stylesheets class to format text headers.

---

## :material-folder-file: Project Layout

### :material-engine: Core <small>Backend</small>

Code that is integral to the core functionality of TagStudio and is UI-independent belongs under the `core/` directory. It's possible that some code that serves the UI can go here, as long as its purpose is to serve _any_ UI and is independent from Qt (e.g. file preview rendering).

```yaml title="Core Backend Directory Example"
core/
│
├── library/ # The TagStudio library system
│   │
│   ├── alchemy/ # Current SQLite backend w/ SQLAlchemy ORM
│   │
│   ├── json/ # Read-only legacy JSON library system, kept for migrations
│   │
│   ├── query_lang/ # The query parser
│   │
│   │   # Library files that do not involve the SQLAlchemy ORM
│   │   # NOTE: Future Non-SQLAlchemy library files will be placed here
│   ├── refresh.py
│   └── ...
│
└── utils/ # Utility classes and functions for the core
```

<!-- prettier-ignore -->
!!! danger "Read-Only Legacy Code"
    **Do not modify** legacy library code in the `src/core/library/json/` directory!

---

### :material-button-cursor: App UI <small>Frontend</small>

The application UI code is stored in the `qt/` directory, and contains all code specific to the Qt frontend. Qt widgets are built using an [MVC](https://www.geeksforgeeks.org/software-engineering/mvc-framework-introduction/) pattern, which is described in-depth below:

#### MVC Pattern

- **Models** are usually just objects from the [library](#core-backend).
    - The **controller** interacts with these, the _view_ does **not**.
- **Views** are Qt layout classes that **_only_** contain the **layout** and **styling** for one or more widgets.
    - Class names are appended with `View`, and filenames appended with `_view`.
    - Not to be used standalone, but as the layouts for one or more controllers.
    - Some logic is acceptable in these classes if it serves to modularize the layout and allows controllers to influence how the layout is initialized.
    - **Reusable Layouts**
        - If a layout class is **_not meant_** to act as a view but instead be a generic layout, it belongs in the `views/layouts/` directory and the file should be appended with `_layout`.
    - **Styling Classes**
        - If a class is purely a source of reusable styling, it belongs in the `views/styles/` directory.

- **Controllers** are complete widgets or base classes for complete widgets.
    - Controller files simply take on the name of the final widget they create.
        - This also creates naming parity with other widgets that simply extend existing Qt widgets with additional logic.

```yaml title="Qt Frontend Directory Example"
qt/
│
├── controllers/ # Widgets implementing views or extending other widgets
│   ├── tag_suggest_box.py # Extends from `suggest_box.py`
│   ├── suggest_box.py # Implements `suggest_box_view.py`
│   ├── main_window.py
│   └── ...
│
├── mixed/ # Files yet to be refactored into controllers and views
│
├── views/ # Everything related to widget layouts and appearances
│   │
│   ├── layouts/ # Layouts meant to be reused on their own inside other layouts
│   │   ├── flow_layout.py
│   │   └── ...
│   │
│   ├── styles/ # Classes specific for styling
│   │   ├── palette.py
│   │   ├── stylesheets.py
│   │   └── ...
│   │
│   │   # Views (layouts) that get implemented by controllers (widgets)
│   ├── main_window_view.py
│   ├── suggest_box_view.py
│   └── ...
│
│   # Frontend classes that aren't related to widgets, like managers
├── resource_manager.py
├── cache_manager.py
├── ts_qt.py # Qt Driver
└── ...
```

<!-- prettier-ignore -->
!!! warning "Pre-MVC UI Code"
    **Do not add** new files to the `qt/mixed/` directory! These files have yet to to be refactored per the current MVC style guidelines and the directory will be **removed** once those migrations have concluded.

Observe the following key aspects of the example below:

- The **view** extends from a Qt layout class, and the **controller** simply extends from QWidget.
- The **controller** is just called `MyCoolWidget` instead of `MyCoolWidgetController` as it will be directly used by other code.
- The **view's** widgets that are intended to be controlled by the controller are **public**, while the **controller's** methods are largely **private**.

<!-- prettier-ignore -->
!!! example "MVC-Separated Widget Example"

    ```py title="views/my_cool_widget_view.py"
    class MyCoolWidgetView(QVBoxLayout):
        def __init__(self):
            super().__init__()
            self.button = QPushButton()
            self.color_dropdown = QComboBox()

            self.addWidget(self.button)
            self.addWidget(self.color_dropdown)
    ```

    ```py title="controllers/my_cool_widget.py"
    class MyCoolWidget(QWidget):
        def __init__(self):
            super().__init__()
            self.setLayout(MyCoolWidgetView())
            self._connect_callbacks()

        def _connect_callbacks(self):
            self.layout().button.clicked.connect(self._button_click_callback)
            self.layout().color_dropdown.currentIndexChanged.connect(
            lambda idx: self._color_dropdown_callback(self.color_dropdown.itemData(idx)))

        def _button_click_callback(self):
            print("Button was clicked!")

        def _color_dropdown_callback(self, color: Color):
            print(f"The selected color is now: {color}")
    ```

<!-- prettier-ignore -->
!!! tip "Tip for Logic Placement"
    A good rule of thumb is: If there's **conditional logic** after a widget has been created, it should probably go in a **controller**.

---

## :material-file-document: Documentation

Documentation contributions include anything inside the `docs/` folder as well as the `README.md`. Documentation inside the `docs/` folder is built and hosted on our static documentation site, [docs.tagstud.io](https://docs.tagstud.io/). Some files such as the `CHANGELOG.md`, `CONTRIBUTING.md`, and `STYLE.md` are symlinked in the repo root from the `docs/` folder.

- Use "[dash-case / kebab-case](https://developer.mozilla.org/en-US/docs/Glossary/Kebab_case)" for file and folder names
- Follow the folder structure pattern
- Don't add images or other media with excessively large file sizes
- Provide alt text for embedded media
- Use "[Title Case](https://apastyle.apa.org/style-grammar-guidelines/capitalization/title-case)" for title capitalization

---

## :material-translate: Translations

Translations are performed on the TagStudio [Weblate project](https://hosted.weblate.org/projects/tagstudio/).

- Do not change text inside placeholders
- Do not change the style tags inside translations
- Use the glossary for term definitions
