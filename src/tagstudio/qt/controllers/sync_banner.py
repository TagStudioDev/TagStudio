# SPDX-FileCopyrightText: (c) TagStudio Contributors
# SPDX-License-Identifier: GPL-3.0-only


from enum import Enum, auto

from PySide6.QtCore import Signal

from tagstudio.i18n.translations import Translations
from tagstudio.qt.controllers.banner import Banner


class SyncStage(Enum):
    PREPARING = auto()
    SCANNING = auto()
    REPAIRING = auto()
    SAVING_NEW_ENTRIES = auto()
    UPDATING = auto()
    DISABLED = auto()
    NEW_FILES = auto()
    UNLINKED = auto()
    RELINKED = auto()
    COMPLETE = auto()


class SyncBanner(Banner):
    """A banner showing sync progress for a library."""

    KEY = "sync"  # Used to identify this banner from a BannerStack
    refresh_requested = Signal()
    review_requested = Signal()
    settings_requested = Signal()

    @property
    def is_awaiting_refresh(self) -> bool:
        """Whether the banner is asking the user to manually refresh the library view."""
        return self.stage is SyncStage.NEW_FILES

    def set_preparing(self) -> None:
        self._show_progress(SyncStage.PREPARING, Translations["library.sync.preparing"])

    def set_scanning(self, searched_count: int, found_count: int) -> None:
        self._show_progress(
            SyncStage.SCANNING,
            Translations.format(
                "library.sync.scanning",
                searched_count=f"{searched_count:n}",
                found_count=f"{found_count:n}",
            ),
        )

    def set_repairing(self) -> None:
        self._show_progress(SyncStage.REPAIRING, Translations["library.sync.repairing"])

    def set_saving_new_entries(self, idx: int, total: int) -> None:
        self._show_progress(
            SyncStage.SAVING_NEW_ENTRIES,
            Translations.format("entries.running.dialog.new_entries", total=f"{total:n}"),
            idx,
            total,
        )

    def set_updating(self, idx: int, total: int) -> None:
        self._show_progress(
            SyncStage.UPDATING,
            Translations.format("library.sync.updating.label", idx=f"{idx:n}", total=f"{total:n}"),
            idx,
            total,
        )

    def set_disabled_notice(self) -> None:
        self._show_notice(
            SyncStage.DISABLED,
            Translations.format(
                "library.sync.disabled_notice",
                sync_setting=Translations["settings.scan_files_on_open"],
            ),
            Translations["library.sync.open_settings"],
            action=self.settings_requested,
        )

    def set_unlinked(self, count: int, relinked_count: int = 0) -> None:
        self._show_notice(
            SyncStage.UNLINKED,
            self._unlinked_text(count, relinked_count),
            Translations["entries.unlinked.review"],
            action=self.review_requested,
        )

    def finish(self, new_count: int, unlinked_count: int, relinked_count: int) -> None:
        """Show whichever notice stage fits the sync's final results."""
        # New files count with a "Refresh" button
        if new_count:
            text = Translations.format(
                "library.sync.new_files_banner.plural"
                if new_count != 1
                else "library.sync.new_files_banner.singular",
                count=f"{new_count:n}",
            )
            text += self._count_suffix(relinked_count, "library.sync.relinked_suffix")
            if relinked_count:
                text += self._count_suffix(unlinked_count, "library.sync.remaining_unlinked_suffix")
            self._show_notice(
                SyncStage.NEW_FILES,
                text,
                Translations["entries.generic.refresh_alt"],
                action=self.refresh_requested,
            )
        # Unlinked entries count with a "Review" button
        elif unlinked_count:
            self.set_unlinked(unlinked_count, relinked_count)
        # Relinked entries count
        elif relinked_count:
            text = Translations.format(
                "library.sync.relinked_banner.plural"
                if relinked_count != 1
                else "library.sync.relinked_banner.singular",
                count=f"{relinked_count:n}",
            )
            text += self._count_suffix(unlinked_count, "library.sync.remaining_unlinked_suffix")
            self._show_notice(
                SyncStage.RELINKED,
                text,
                Translations["entries.generic.refresh_alt"],
                action=self.refresh_requested,
            )
        else:
            self._show_fleeting_notice(SyncStage.COMPLETE, Translations["library.sync.complete"])

    def _unlinked_text(self, count: int, relinked_count: int) -> str:
        text = Translations.format(
            "library.sync.unlinked_banner.plural"
            if count != 1
            else "library.sync.unlinked_banner.singular",
            count=f"{count:n}",
        )
        return text + self._count_suffix(relinked_count, "library.sync.relinked_suffix")

    def _count_suffix(self, count: int, translation_key: str) -> str:
        """Build a count suffix (e.g. " (3 Still Unlinked)") or "" if the `count` is 0."""
        if not count:
            return ""
        return " " + Translations.format(translation_key, count=f"{count:n}")
