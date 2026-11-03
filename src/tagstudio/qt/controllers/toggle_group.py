# SPDX-FileCopyrightText: (c) TagStudio Contributors
# SPDX-License-Identifier: GPL-3.0-only


from functools import partial
from typing import override

from PySide6.QtCore import QEvent, Signal
from PySide6.QtWidgets import QWidget

from tagstudio.qt.views.toggle_group_view import Toggle, ToggleGroupView


class ToggleGroup(QWidget):
    """A row of joined buttons with toggle behavior."""

    toggled = Signal(int, bool)  # (button index, on/off)

    def __init__(self, toggles: list[Toggle]) -> None:
        super().__init__()
        self.setLayout(ToggleGroupView(toggles))
        for index, button in enumerate(self.layout().buttons):
            button.toggled.connect(partial(self.toggled.emit, index))

    @override
    def changeEvent(self, event: QEvent) -> None:
        if event.type() == QEvent.Type.ThemeChange:
            self.layout().set_icons()
        super().changeEvent(event)

    @override
    def layout(self) -> ToggleGroupView:
        layout = super().layout()
        assert isinstance(layout, ToggleGroupView)
        return layout

    def is_checked(self, index: int) -> bool:
        return self.layout().buttons[index].isChecked()

    def set_checked(self, index: int, checked: bool) -> None:
        self.layout().buttons[index].setChecked(checked)
