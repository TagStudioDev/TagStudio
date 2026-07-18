# SPDX-FileCopyrightText: (c) TagStudio Contributors
# SPDX-License-Identifier: GPL-3.0-only


from tagstudio.qt.translations import Translations
from tagstudio.qt.views.suggest_box_view import SuggestBoxView


# TODO: Get rid of this class
class TagSuggestBoxView(SuggestBoxView):
    def __init__(self, is_tag_chooser: bool) -> None:
        super().__init__(is_tag_chooser)
        placeholder = (
            f"{Translations['home.search_tags']} {Translations['home.search.how_to_exit']}"
        )
        self.search_field.setPlaceholderText(placeholder)
