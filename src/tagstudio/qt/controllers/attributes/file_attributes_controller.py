import typing

from tagstudio.core.library.alchemy.library import Library
from tagstudio.qt.views.preview_panel.attributes.file_attributes_view import FileAttributesView

if typing.TYPE_CHECKING:
    from tagstudio.qt.ts_qt import QtDriver


class FileAttributes(FileAttributesView):
    """A widget displaying a list of a file's attributes."""

    def __init__(self, library: Library, driver: "QtDriver"):
        super().__init__(library, driver)