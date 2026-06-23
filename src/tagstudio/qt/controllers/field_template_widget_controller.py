# SPDX-FileCopyrightText: (c) TagStudio Contributors
# SPDX-License-Identifier: GPL-3.0-only

from tagstudio.core.library.alchemy.fields import BaseFieldTemplate
from tagstudio.qt.translations import FIELD_TYPE_KEYS, Translations
from tagstudio.qt.views.field_template_widget_view import FieldTemplateWidgetView


class FieldTemplateWidget(FieldTemplateWidgetView):
    def __init__(self) -> None:
        super().__init__()

        self.__field_template: BaseFieldTemplate | None = None

    def set_field_template(self, field_template: BaseFieldTemplate | None) -> None:
        self.__field_template = field_template

        if field_template is None:
            return

        field_name_key: str = FIELD_TYPE_KEYS.get(field_template.class_name, "field_type.unknown")
        self._bg_button.setText(f"{field_template.name} ({Translations[field_name_key]})")
