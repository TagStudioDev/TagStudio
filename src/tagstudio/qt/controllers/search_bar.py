# SPDX-FileCopyrightText: (c) TagStudio Contributors
# SPDX-License-Identifier: GPL-3.0-only


import re
from typing import override

from PySide6.QtCore import QEvent, QObject, QPoint, Signal
from PySide6.QtWidgets import QSizePolicy, QWidget

from tagstudio.core.library.alchemy.library import Library
from tagstudio.core.media_types import MediaTypes
from tagstudio.core.query_lang.file_groups import SEARCH
from tagstudio.qt.views.search_bar_view import SearchBarView
from tagstudio.qt.views.styles.tagstudio_style import set_icon_faded


class SearchBar(QWidget):
    """A search field with navigation buttons."""

    search_submitted = Signal(str)
    navigation_requested = Signal(int)
    show_hidden_entries_changed = Signal(bool)

    def __init__(self, library: Library) -> None:
        super().__init__()
        self.setObjectName("search_bar")
        self.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)
        self._lib = library
        self.setLayout(SearchBarView())
        self._connect_callbacks()
        self.set_nav_buttons_enabled(False)

    @override
    def changeEvent(self, event: QEvent) -> None:
        if event.type() == QEvent.Type.ThemeChange:
            self.layout().set_button_icons()
        super().changeEvent(event)

    @override
    def eventFilter(self, watched: QObject, event: QEvent) -> bool:
        if event.type() in (QEvent.Type.Enter, QEvent.Type.Leave):
            self.layout().set_options_hovered(event.type() == QEvent.Type.Enter)
        return super().eventFilter(watched, event)

    @override
    def layout(self) -> SearchBarView:
        layout = super().layout()
        assert isinstance(layout, SearchBarView)
        return layout

    @property
    def show_hidden_entries(self) -> bool:
        """Whether to show entries tagged with "is_hidden" tags."""
        return self.layout().show_hidden_entries_action.isChecked()

    def set_nav_buttons_enabled(self, enabled: bool) -> None:
        """Enable the back and forward navigation buttons."""
        for button in (self.layout().back_button, self.layout().forward_button):
            button.setEnabled(enabled)
            set_icon_faded(button, faded=False)

    def set_history_available(self, can_go_back: bool, can_go_forward: bool) -> None:
        """Enable the back and forward buttons by whether there's history in their direction."""
        view = self.layout()
        for button, is_available in (
            (view.back_button, can_go_back),
            (view.forward_button, can_go_forward),
        ):
            button.setEnabled(is_available)
            set_icon_faded(button, faded=not is_available)

    def set_query(self, query: str) -> None:
        self.layout().search_field.setText(query)

    def _connect_callbacks(self) -> None:
        view = self.layout()
        view.back_button.clicked.connect(lambda: self.navigation_requested.emit(-1))
        view.forward_button.clicked.connect(lambda: self.navigation_requested.emit(1))
        view.options_action.triggered.connect(self._show_options_menu)
        view.options_button.installEventFilter(self)
        view.options_menu.aboutToShow.connect(lambda: view.set_options_menu_open(True))
        view.options_menu.aboutToHide.connect(lambda: view.set_options_menu_open(False))
        view.show_hidden_entries_action.toggled.connect(self.show_hidden_entries_changed)
        view.show_hidden_entries_action.toggled.connect(view.update_options_icon)
        view.search_field.returnPressed.connect(self._submit)
        view.search_field.textChanged.connect(self._update_completions)

    def _show_options_menu(self) -> None:
        view = self.layout()
        field = view.search_field
        right_edge = QPoint(field.width() - view.options_menu.sizeHint().width(), field.height())
        view.options_menu.popup(field.mapToGlobal(right_edge))

    def _submit(self) -> None:
        self.search_submitted.emit(self.layout().search_field.text())

    def _update_completions(self, text: str) -> None:
        completion_list_model = self.layout().search_field_completion_list
        matches = re.search(
            r"((?:.* )?)(mediatype|filetype|path|tag|tag_id):(\"?[A-Za-z0-9\ \t]+\"?)?", text
        )

        completion_list: list[str] = []
        if len(text) < 3:
            completion_list = [
                "mediatype:",
                "filetype:",
                "path:",
                "tag:",
                "tag_id:",
                "special:untagged",
            ]
            completion_list_model.setStringList(completion_list)

        if not matches:
            return

        query_type: str
        query_value: str | None
        prefix, query_type, query_value = matches.groups()

        if not query_value:
            return

        if query_type == "tag":
            completion_list = list(map(lambda x: prefix + "tag:" + x.name, self._lib.tags))
        elif query_type == "tag_id":
            completion_list = list(map(lambda x: prefix + "tag_id:" + str(x.id), self._lib.tags))
        elif query_type == "path":
            completion_list = list(
                map(lambda x: prefix + "path:" + x, self._lib.get_paths(limit=100))
            )
        elif query_type == "mediatype":
            completion_list = []
            for group in MediaTypes.all_groups:
                for alias in group.name_aliases:
                    if " " in alias:
                        completion_list.append(f'{prefix}mediatype:"{alias}"')
                    else:
                        completion_list.append(f"{prefix}mediatype:{alias}")
                        completion_list.append(f'{prefix}mediatype:"{alias}"')
        elif query_type == "filetype":
            extensions_list: set[str] = set()
            for group in MediaTypes.all_groups:
                extensions_list |= group.context_sets.get(SEARCH, set())
            completion_list = list(
                map(lambda x: prefix + "filetype:" + x.replace(".", ""), extensions_list)
            )

        update_completion_list: bool = (
            completion_list != completion_list_model.stringList() or completion_list_model == []
        )
        if update_completion_list:
            completion_list_model.setStringList(completion_list)
