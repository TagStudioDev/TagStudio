# SPDX-FileCopyrightText: (c) TagStudio Contributors
# SPDX-License-Identifier: GPL-3.0-only

from typing import override

from PySide6.QtCore import QEvent, Qt
from PySide6.QtGui import QAction, QEnterEvent

from tagstudio.core.library.alchemy.fields import BaseFieldTemplate
from tagstudio.qt.translations import FIELD_TYPE_KEYS, Translations
from tagstudio.qt.views.field_template_widget_view import FieldTemplateWidgetView


class FieldTemplateWidget(FieldTemplateWidgetView):
    def __init__(self) -> None:
        super().__init__()

        self.__field_template: BaseFieldTemplate | None = None
        self.has_remove: bool = False

        # Add actions
        edit_action = QAction(self)
        edit_action.setText(Translations["generic.edit"])
        edit_action.triggered.connect(self.on_edit.emit)
        self.addAction(edit_action)

        self.setContextMenuPolicy(Qt.ContextMenuPolicy.ActionsContextMenu)

    def set_field_template(self, field_template: BaseFieldTemplate | None) -> None:
        self.__field_template = field_template

        if field_template is None:
            return

        field_name_key: str = FIELD_TYPE_KEYS.get(field_template.class_name, "field_type.unknown")
        self._bg_button.setText(f"{field_template.name} ({Translations[field_name_key]})")

    @override
    def enterEvent(self, event: QEnterEvent) -> None:
        if self.has_remove:
            self._delete_button.setHidden(False)
        self.update()
        return super().enterEvent(event)

    @override
    def leaveEvent(self, event: QEvent) -> None:
        if self.has_remove:
            self._delete_button.setHidden(True)
        self.update()
        return super().leaveEvent(event)
