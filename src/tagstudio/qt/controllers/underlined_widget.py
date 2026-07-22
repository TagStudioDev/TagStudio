# SPDX-FileCopyrightText: (c) TagStudio Contributors
# SPDX-License-Identifier: GPL-3.0-only


from typing import override

from PySide6.QtWidgets import QWidget

from tagstudio.qt.views.underlined_widget_view import UnderlinedWidgetView


class UnderlinedWidget(QWidget):
    def __init__(self, widget: QWidget) -> None:
        super().__init__()
        self.setLayout(UnderlinedWidgetView(widget))

    def toggle_underline(self, is_hidden: bool) -> None:
        self.layout().underline.setHidden(is_hidden)

    @property
    def widget(self) -> QWidget:
        return self.layout().itemAt(0).widget()

    @override
    def layout(self) -> UnderlinedWidgetView:
        return super().layout()  # pyright: ignore[reportReturnType]
