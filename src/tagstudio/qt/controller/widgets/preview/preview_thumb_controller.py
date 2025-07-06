from typing import TYPE_CHECKING

from tagstudio.core.library.alchemy.library import Library
from tagstudio.qt.view.widgets.preview.preview_thumb_view import PreviewThumbView

if TYPE_CHECKING:
    from tagstudio.qt.ts_qt import QtDriver


class PreviewThumb(PreviewThumbView):
    def __init__(self, library: Library, driver: "QtDriver"):
        super().__init__(library, driver)
