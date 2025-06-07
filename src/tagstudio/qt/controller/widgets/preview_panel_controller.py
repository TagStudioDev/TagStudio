import typing

from tagstudio.core.library.alchemy.library import Library
from tagstudio.qt.translations import Translations
from tagstudio.qt.view.widgets.preview_panel_view import PreviewPanelView
from tagstudio.qt.widgets.panel import PanelModal

if typing.TYPE_CHECKING:
    from tagstudio.qt.ts_qt import QtDriver


class PreviewPanel(PreviewPanelView):
    def __init__(self, library: Library, driver: "QtDriver"):
        super().__init__(library, driver)

        self.__add_tag_modal = PanelModal(self._tag_search_panel, Translations["tag.add.plural"])
        self.__add_tag_modal.setWindowTitle(Translations["tag.add.plural"])

    def _add_tag_button_callback(self):
        self.__add_tag_modal.show()

    def update_view(self, driver: "QtDriver", update_preview=True):
        """Render the panel widgets with the newest data from the Library.

        Args:
            driver  (QtDriver): List of the IDs of the selected entries.
            update_preview (bool): Should the file preview be updated?
                                   (Only works with one or more items selected)
        """
        self._set_selection(driver.selected, update_preview)
