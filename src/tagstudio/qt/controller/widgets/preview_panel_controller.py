import typing
from warnings import catch_warnings

from tagstudio.core.library.alchemy.library import Library
from tagstudio.qt.modals.add_field import AddFieldModal
from tagstudio.qt.modals.tag_search import TagSearchModal
from tagstudio.qt.view.widgets.preview_panel_view import PreviewPanelView

if typing.TYPE_CHECKING:
    from tagstudio.qt.ts_qt import QtDriver


class PreviewPanel(PreviewPanelView):
    def __init__(self, library: Library, driver: "QtDriver"):
        super().__init__(library, driver)

        self.__add_field_modal = AddFieldModal(self.lib)
        self.__add_tag_modal = TagSearchModal(self.lib, is_tag_chooser=True)

    def _add_field_button_callback(self):
        self.__add_field_modal.show()

    def _add_tag_button_callback(self):
        self.__add_tag_modal.show()

    def _set_selection_callback(self, selected: list[int]):
        with catch_warnings(record=True):
            self.__add_field_modal.done.disconnect()
            self.__add_tag_modal.tsp.tag_chosen.disconnect()

        self.__add_field_modal.done.connect(
            lambda f: (
                self._fields.add_field_to_selected(f),
                (self._fields.update_from_entry(selected[0]) if len(selected) == 1 else ()),
            )
        )
        self.__add_tag_modal.tsp.tag_chosen.connect(
            lambda t: (
                self._fields.add_tags_to_selected(t),
                (self._fields.update_from_entry(selected[0]) if len(selected) == 1 else ()),
            )
        )
