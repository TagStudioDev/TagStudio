# SPDX-FileCopyrightText: (c) TagStudio Contributors
# SPDX-License-Identifier: GPL-3.0-only


from collections.abc import Hashable
from typing import override

from PySide6.QtWidgets import QWidget

from tagstudio.qt.controllers.banner import Banner
from tagstudio.qt.views.banner_stack_view import BannerStackView


class BannerStack(QWidget):
    """A vertical stack to show zero or more Banner widgets.

    New banners enter visually at the top of the stack.
    Pushing a banner with a `key` matching an existing banner in the stack replaces it in place.
    Pushing one with an new `key` or `None` adds it as an independent banner.
    """

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setLayout(BannerStackView())
        self._by_key: dict[Hashable, Banner] = {}

    def get[T: Banner](self, key: Hashable, kind: type[T]) -> T | None:
        """Return the active banner under `key`, if it's still shown and is a `kind`."""
        banner = self._by_key.get(key)
        return banner if isinstance(banner, kind) else None

    def push(self, banner: Banner, key: Hashable | None = None) -> None:
        """Add `banner` to the top of the stack, replacing any banner sharing `key`."""
        if key is not None:
            existing = self._by_key.pop(key, None)
            if existing is not None:
                existing.hide_banner(force=True)

        banner.stack_key = key
        banner.setParent(self)
        banner.closed.connect(lambda: self._on_banner_closed(banner))
        self.layout().insertWidget(0, banner)
        if key is not None:
            self._by_key[key] = banner

    def _on_banner_closed(self, banner: Banner) -> None:
        if banner.stack_key is not None and self._by_key.get(banner.stack_key) is banner:
            del self._by_key[banner.stack_key]
        self.layout().removeWidget(banner)
        banner.deleteLater()

    @override
    def layout(self) -> BannerStackView:
        return super().layout()  # pyright: ignore[reportReturnType]
