# SPDX-FileCopyrightText: (c) TagStudio Contributors
# SPDX-License-Identifier: GPL-3.0-only


import math
import time

import structlog
from PySide6.QtCore import QObject, QThreadPool, Signal

from tagstudio.core.library.alchemy.enums import BrowsingState
from tagstudio.core.library.alchemy.library import Library, SearchResult
from tagstudio.core.library.ignore import Ignore
from tagstudio.core.query_lang.util import ParsingError
from tagstudio.core.utils.numeric import clamp
from tagstudio.qt.app_settings import AppSettings
from tagstudio.qt.browsing_history import BrowsingHistory
from tagstudio.qt.selection_state import SelectionState

logger = structlog.get_logger(__name__)


class Navigator(QObject):
    """Moves through the browsing history and searches the library for each state's results."""

    state_updated = Signal()
    search_started = Signal()
    results_found = Signal(SearchResult, float)  # (Results, seconds)
    search_failed = Signal(BaseException)
    page_shown = Signal(object)  # ID of the entry to scroll to, or None
    # (Search ID, results or None, error or None, seconds)
    _search_finished = Signal(int, SearchResult, BaseException, float)

    browsing_history: BrowsingHistory[BrowsingState]

    def __init__(
        self,
        library: Library,
        library_pool: QThreadPool,
        settings: AppSettings,
        selection: SelectionState[int],
    ) -> None:
        super().__init__()
        self._lib = library
        self._library_pool = library_pool
        self._settings = settings
        self._selection = selection

        self.frame_content: list[int] = []  # List of Entry IDs for the shown state
        # State the grid shows results from. Lags behind browsing_history.current during a search.
        self._shown_state: BrowsingState | None = None
        self._search_id: int = 0
        self._is_searching: bool = False
        self._search_finished.connect(self._on_search_finished)
        self.pages_count = 0

        self.reset()

    @property
    def page_size(self) -> int:
        """The max page size setting, or number of current results with infinite scroll on."""
        return (
            len(self.frame_content) if self._settings.infinite_scroll else self._settings.page_size
        )

    @property
    def shown_page_index(self) -> int:
        """The index of the results page the grid shows."""
        return self._shown_state.page_index if self._shown_state is not None else 0

    @property
    def is_searching(self) -> bool:
        """Whether a search query is currently being run on the library."""
        return self._is_searching

    def reset(self, state: BrowsingState | None = None) -> None:
        """Reset the browsing history to the given `state`, or to showing all entries if `None`."""
        self.browsing_history = BrowsingHistory(state or BrowsingState.show_all())
        self._search_id += 1  # Stops search in progress
        self.frame_content.clear()
        self._shown_state = None

    def set_first_visible_entry_id(self, entry_id: int) -> None:
        if self._shown_state is not None:
            self._shown_state.first_visible_entry_id = entry_id

    def go_to_page(self, index: int) -> None:
        if self._is_searching:
            return
        current = self.browsing_history.current
        index = clamp(index, 0, self.pages_count - 1)
        if index != current.page_index:
            self.update_browsing_state(current.with_page_index(index))

    def navigation_callback(self, delta: int) -> None:
        """Callback for the Forwards and Backwards Navigation Buttons next to the search bar."""
        logger.info(
            "navigation_callback",
            delta=delta,
        )

        if self.browsing_history.move(delta):
            self.update_browsing_state()

    def update_browsing_state(
        self, state: BrowsingState | None = None, searches_again: bool = False
    ) -> None:
        """Navigates to a new BrowsingState when state is given, otherwise updates the results."""
        if not self._lib.library_dir:
            logger.info("Library not loaded")
            return

        if state:
            self.browsing_history.push(state)
            # States with the same query/sorting aren't pushed, the only reset the scroll position.
            self.browsing_history.current.first_visible_entry_id = None
        current = self.browsing_history.current
        self.state_updated.emit()

        shown = self._shown_state
        if current is shown:  # Results refresh in case entries were removed from the library
            selected = self._selection.selected
            self._selection.deselect(self._lib.removed_entry_ids(selected))
        only_page_changed = (
            not searches_again
            and not self._is_searching
            and current is not shown  # Refreshing the shown state searches again
            and shown is not None
            and current.with_page_index(0) == shown.with_page_index(0)
        )
        self._search_id += 1
        if not only_page_changed:
            # Search the library
            Ignore.get_patterns(self._lib.library_dir, include_global=True)
            self._search_library(current)
        else:
            self._show_page()

    def _search_library(self, state: BrowsingState) -> None:
        """Search the library with a query and any filters and sorting."""
        search_id = self._search_id
        self._is_searching = True
        self.search_started.emit()

        def is_cancelled() -> bool:
            return search_id != self._search_id

        def search() -> None:
            if is_cancelled():
                return
            results: SearchResult | None = None
            error: Exception | ParsingError | None = None
            start_time = time.time()
            try:
                results = self._lib.search_library(state, page_size=0, is_cancelled=is_cancelled)
            except (Exception, ParsingError) as e:
                error = e
            self._search_finished.emit(search_id, results, error, time.time() - start_time)

        self._library_pool.start(search)

    def _on_search_finished(
        self,
        search_id: int,
        results: SearchResult | None,
        error: Exception | ParsingError | None,
        seconds: float,
    ) -> None:
        if search_id != self._search_id:
            return
        self._is_searching = False
        if results is not None:
            self.frame_content = results.ids
            self.results_found.emit(results, seconds)
            self._show_page()
        elif isinstance(error, ParsingError):
            logger.error("[Navigator] Could not parse the search query", error=error)
            self.search_failed.emit(error)
        else:
            logger.error("[Navigator] Could not search the library", error=error)
            self.search_failed.emit(error)

    def _show_page(self) -> None:
        """Show the current results page."""
        previous = self._shown_state
        current = self.browsing_history.current
        self._shown_state = current

        if current.first_visible_entry_id is not None:
            entry_id = current.first_visible_entry_id
        elif (
            previous is not None
            and current is not previous
            and current.query == previous.query
            and current.page_index == previous.page_index
        ):
            # Keep the selection in view when the same results are only resorted or filtered
            entry_id = self._selection.cursor
        else:
            entry_id = None

        # Update pagination
        page_size = 0 if self._settings.infinite_scroll else self._settings.page_size
        if page_size > 0:
            self.pages_count = math.ceil(len(self.frame_content) / page_size)
        else:
            self.pages_count = 1
        self.page_shown.emit(entry_id)
