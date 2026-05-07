# Copyright (C) 2025 Travis Abendshien (CyanVoxel).
# Licensed under the GPL-3.0 License.
# Created for TagStudio: https://github.com/CyanVoxel/TagStudio


from collections.abc import Callable

import structlog

from tagstudio.qt.views.field_container_view import FieldContainerView

logger = structlog.get_logger(__name__)

type Callback = Callable[[], None] | None


class FieldContainer(FieldContainerView):
    """A container that holds a field widget and provides some relevant information and controls."""

    def __init__(self, title: str = "Field", inline: bool = True) -> None:
        super().__init__(title, inline)

        self.__copy_callback: Callback = None
        self.__edit_callback: Callback = None
        self.__remove_callback: Callback = None

    def _copy_callback(self) -> None:
        if self.__copy_callback is not None:
            self.__copy_callback()

    def _edit_callback(self) -> None:
        if self.__edit_callback is not None:
            self.__edit_callback()

    def _remove_callback(self) -> None:
        if self.__remove_callback is not None:
            self.__remove_callback()

    def set_copy_callback(self, callback: Callback = None) -> None:
        """Sets the callback to be called when the 'Copy' button is pressed."""
        self.__copy_callback = callback
        self._copy_enabled = callback is not None

    def set_edit_callback(self, callback: Callback = None) -> None:
        """Sets the callback to be called when the 'Edit' button is pressed."""
        self.__edit_callback = callback
        self._edit_enabled = callback is not None

    def set_remove_callback(self, callback: Callback = None) -> None:
        """Sets the callback to be called when the 'Edit' button is pressed."""
        self.__remove_callback = callback
        self._remove_enabled = callback is not None
