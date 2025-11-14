# Copyright (C) 2025 Travis Abendshien (CyanVoxel).
# Licensed under the GPL-3.0 License.
# Created for TagStudio: https://github.com/CyanVoxel/TagStudio


from typing import TYPE_CHECKING, override

import structlog
from PySide6 import QtGui

from tagstudio.core.library.alchemy.library import Library
from tagstudio.core.library.alchemy.registries.ignored_registry import IgnoredRegistry
from tagstudio.qt.mixed.progress_bar import ProgressWidget
from tagstudio.qt.mixed.remove_ignored_modal import RemoveIgnoredModal
from tagstudio.qt.translations import Translations
from tagstudio.qt.views.fix_ignored_modal_view import FixIgnoredEntriesModalView

# Only import for type checking/autocompletion, will not be imported at runtime.
if TYPE_CHECKING:
    from tagstudio.qt.ts_qt import QtDriver

logger = structlog.get_logger(__name__)


class FixIgnoredEntriesModal(FixIgnoredEntriesModalView):
    def __init__(self, library: "Library", driver: "QtDriver"):
        super().__init__(library, driver)
        self.tracker = IgnoredRegistry(self.lib)

        self.remove_modal = RemoveIgnoredModal(self.driver, self.tracker)
        self.remove_modal.done.connect(
            lambda: (
                self.update_ignored_count(),
                self.driver.update_browsing_state(),
                self.update_driver_widgets(),
                self.refresh_ignored(),
            )
        )

        self.refresh_ignored_button.clicked.connect(self.refresh_ignored)
        self.remove_button.clicked.connect(self.remove_modal.show)
        self.done_button.clicked.connect(self.hide)

        self.update_ignored_count()

    def refresh_ignored(self):
        pw = ProgressWidget(
            cancel_button_text=None,
            minimum=0,
            maximum=self.lib.entries_count,
        )
        pw.setWindowTitle(Translations["library.scan_library.title"])
        pw.update_label(Translations["entries.ignored.scanning"])

        pw.from_iterable_function(
            self.tracker.refresh_ignored_entries,
            None,
            self.set_ignored_count,
            self.update_ignored_count,
            self.remove_modal.refresh_list,
            self.update_driver_widgets,
        )

    def set_ignored_count(self):
        """Sets the ignored_entries_count in the Library to the tracker's value."""
        self.lib.ignored_entries_count = self.tracker.ignored_count

    def update_ignored_count(self):
        """Updates the UI to reflect the Library's current ignored_entries_count."""
        # Indicates that the library is new compared to the last update.
        # NOTE: Make sure set_ignored_count() is called before this!
        if self.tracker.ignored_count > 0 and self.lib.ignored_entries_count < 0:
            self.tracker.reset()

        count: int = self.lib.ignored_entries_count

        self.remove_button.setDisabled(count < 1)

        count_text: str = Translations.format(
            "entries.ignored.ignored_count", count=count if count >= 0 else "—"
        )
        self.ignored_count_label.setText(f"<h3>{count_text}</h3>")

    def update_driver_widgets(self):
        if (
            hasattr(self.driver, "library_info_window")
            and self.driver.library_info_window.isVisible()
        ):
            self.driver.library_info_window.update_cleanup()

    @override
    def showEvent(self, event: QtGui.QShowEvent) -> None:  # type: ignore
        self.update_ignored_count()
        return super().showEvent(event)
