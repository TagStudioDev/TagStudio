# SPDX-FileCopyrightText: (c) TagStudio Contributors
# SPDX-License-Identifier: GPL-3.0-only


from typing import override

from PySide6.QtCore import QEvent, Signal
from PySide6.QtWidgets import QWidget

from tagstudio.core.library.alchemy.enums import SortingModeEnum
from tagstudio.i18n.translations import Translations
from tagstudio.qt.views.browsing_controls_view import BrowsingControlsView
from tagstudio.qt.views.styles.tagstudio_style import set_icon_faded


class BrowsingControls(QWidget):
    """A row of view and sort controls for the browsing area."""

    sorting_mode_changed = Signal(SortingModeEnum)
    sorting_direction_changed = Signal(bool)
    thumb_size_changed = Signal(int)
    pagination_changed = Signal(bool, int)  # (infinite scrolling, page size)
    filenames_visible_changed = Signal(bool)

    def __init__(self) -> None:
        super().__init__()
        self.setLayout(BrowsingControlsView())
        self._is_ascending = False
        self.set_sorting_mode(SortingModeEnum.DATE_ADDED)
        self._connect_callbacks()

    @override
    def changeEvent(self, event: QEvent) -> None:
        if event.type() == QEvent.Type.ThemeChange:
            self.layout().set_icons()
            self._set_sort_direction_button()
        super().changeEvent(event)

    @override
    def layout(self) -> BrowsingControlsView:
        layout = super().layout()
        assert isinstance(layout, BrowsingControlsView)
        return layout

    def _connect_callbacks(self) -> None:
        view = self.layout()
        view.sort_direction_button.clicked.connect(self._flip_sort_direction)
        view.sort_mode_combobox.activated.connect(self._on_sort_mode_chosen)
        view.thumb_size_slider.valueChanged.connect(
            lambda: self.thumb_size_changed.emit(self.thumb_size)
        )
        view.show_filenames_action.triggered.connect(self.filenames_visible_changed)
        view.infinite_scroll_action.triggered.connect(self._on_pagination_chosen)
        view.page_size_menu.triggered.connect(self._on_pagination_chosen)

    @property
    def sorting_mode(self) -> SortingModeEnum:
        return self.layout().sort_mode_combobox.currentData()

    @property
    def sorting_direction(self) -> bool:
        return self._is_ascending

    @property
    def thumb_size(self) -> int:
        view = self.layout()
        return view.MIN_THUMB_SIZE + view.thumb_size_slider.value() * view.THUMB_SIZE_STEP

    def set_results_text(self, text: str) -> None:
        self.layout().results_label.setText(text)

    def set_sorting_mode(self, mode: SortingModeEnum) -> None:
        combobox = self.layout().sort_mode_combobox
        combobox.setCurrentIndex(combobox.findData(mode))
        self._set_sort_direction_button()

    def set_pagination_actions_checked(self, is_infinite: bool, page_size: int) -> None:
        """Set which pagination actions in the view options menu are checked."""
        view = self.layout()
        view.infinite_scroll_action.setChecked(is_infinite)
        view.page_size_menu.setEnabled(not is_infinite)
        for action in view.page_size_group.actions():
            action.setChecked(action.data() == page_size)

    def set_show_filenames_action_checked(self, checked: bool) -> None:
        self.layout().show_filenames_action.setChecked(checked)

    def increase_thumb_size(self) -> None:
        slider = self.layout().thumb_size_slider
        slider.setValue(slider.value() + 1)

    def decrease_thumb_size(self) -> None:
        slider = self.layout().thumb_size_slider
        slider.setValue(slider.value() - 1)

    def _flip_sort_direction(self) -> None:
        self._is_ascending = not self._is_ascending
        self._set_sort_direction_button()
        self.sorting_direction_changed.emit(self._is_ascending)

    def _set_sort_direction_button(self) -> None:
        view = self.layout()
        mode = self.sorting_mode
        is_directional = mode != SortingModeEnum.RANDOM
        view.sort_direction_button.setEnabled(is_directional)
        set_icon_faded(view.sort_direction_button, faded=not is_directional)
        ascending_icon, descending_icon = view.sort_direction_icons[mode]
        if self._is_ascending:
            view.sort_direction_button.setIcon(ascending_icon)
            view.sort_direction_button.setToolTip(Translations["sorting.direction.ascending"])
        else:
            view.sort_direction_button.setIcon(descending_icon)
            view.sort_direction_button.setToolTip(Translations["sorting.direction.descending"])

    def _on_sort_mode_chosen(self) -> None:
        self._set_sort_direction_button()
        self.sorting_mode_changed.emit(self.sorting_mode)

    def _on_pagination_chosen(self) -> None:
        view = self.layout()
        is_infinite = view.infinite_scroll_action.isChecked()
        view.page_size_menu.setEnabled(not is_infinite)
        page_size = view.page_size_group.checkedAction().data()
        self.pagination_changed.emit(is_infinite, page_size)
