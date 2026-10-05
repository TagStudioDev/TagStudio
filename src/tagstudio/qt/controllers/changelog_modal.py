# SPDX-FileCopyrightText: (c) TagStudio Contributors
# SPDX-License-Identifier: GPL-3.0-only


import math
import re
from pathlib import Path
from typing import override

import structlog
from PySide6.QtCore import QSize, Qt, QTimer, QUrl
from PySide6.QtGui import (
    QColor,
    QDesktopServices,
    QImage,
    QPainter,
    QPalette,
    QPixmap,
    QShowEvent,
    QTextBlockFormat,
    QTextCharFormat,
    QTextCursor,
    QTextDocument,
    QTextFormat,
)
from PySide6.QtNetwork import QNetworkAccessManager, QNetworkReply, QNetworkRequest
from PySide6.QtWidgets import QDialogButtonBox

from tagstudio.core.constants import DOCS_URL, GITHUB_REPO_URL
from tagstudio.core.utils.types import unwrap
from tagstudio.i18n.translations import Translations
from tagstudio.qt.controllers.modal_content import ModalContent
from tagstudio.qt.resource_manager import ResourceManager
from tagstudio.qt.views.changelog_modal_view import ChangelogModalView
from tagstudio.qt.views.modal_view import ModalView
from tagstudio.qt.views.styles.palette import (
    MUTED_PURPLE,
    MUTED_PURPLE_OPAQUE,
    ColorType,
    UiColor,
    get_ui_color,
)

logger = structlog.get_logger(__name__)

_CHANGELOG_NAME = "changelog.md"

# GitHub Reference Patterns
_COMMIT_HASH = re.compile(r"\b[0-9a-f]{40}\b")
_ISSUE_REFERENCE = re.compile(r"(?<![\w/#])#(\d+)\b")
_USER_MENTION = re.compile(r"(?<![\w@/])@([A-Za-z0-9](?:[A-Za-z0-9-]*[A-Za-z0-9])?)")

# Size Constraints
_IMAGE_MAX_HEIGHT = 300
_IMAGE_MAX_WIDTH = 0.8  # % of window width
_WINDOW_MAX_HEIGHT = 900
_WINDOW_WIDTH = 600

# Spacing
# TODO: Use future constants for some of these (currently on dev branch)
_DIVIDER_SPACING = 12
_H3_SPACING = 12
_HEADING_SPACING = 6
_IMAGE_SPACING = 6
_LIST_END_SPACING = 10
_LIST_ITEM_SPACING = 2


class ChangelogModal(ModalContent):
    """Modal that displays the bundled CHANGELOG.MD file with custom styling."""

    def __init__(self) -> None:
        super().__init__()
        self.setMinimumHeight(600)
        self.setLayout(ChangelogModalView())

        self._sections: list[str] = []
        self._loaded_count = 0
        self._is_loading = False
        self._network = QNetworkAccessManager(self)
        self._network.finished.connect(self._on_image_downloaded)
        self._image_widths: dict[str, float] = {}  # The original width of each <img> tag

        path = self._find_changelog()
        if path:
            self._sections = self._split_changelog(path.read_text(encoding="utf-8"))
        else:
            logger.error("[ChangelogModal] Changelog file not found")
            self.layout().text_browser.setPlainText(Translations["changelog.missing"])

        scroll_bar = self.layout().text_browser.verticalScrollBar()
        scroll_bar.valueChanged.connect(self._load_more_if_needed)
        scroll_bar.rangeChanged.connect(self._load_more_if_needed)

        self.layout().view_more_button.clicked.connect(
            lambda: QDesktopServices.openUrl(QUrl(f"{DOCS_URL}/changelog/"))
        )
        # Use default browser to open links (Guard against internal markdown links)
        self.layout().text_browser.anchorClicked.connect(QDesktopServices.openUrl)
        self._load_more_if_needed()

    @staticmethod
    def _find_changelog() -> Path | None:
        """Find the CHANGELOG.MD file."""
        for path in (
            Path(__file__).parents[2] / "resources" / "changelog" / _CHANGELOG_NAME,  # Build
            Path(__file__).parents[4] / "docs" / _CHANGELOG_NAME,  # Source / Dev Environment
        ):
            if path.is_file():
                return path
        return None

    @staticmethod
    def _split_changelog(markdown: str) -> list[str]:
        """Split the changelog into one section per version."""
        # Turn GitHub references into hyperlinks
        markdown = _ISSUE_REFERENCE.sub(rf"[#\1]({GITHUB_REPO_URL}/issues/\1)", markdown)
        markdown = _USER_MENTION.sub(r"[@\1](https://github.com/\1)", markdown)
        markdown = _COMMIT_HASH.sub(
            lambda match: f"[{match[0][:7]}]({GITHUB_REPO_URL}/commit/{match[0]})", markdown
        )
        # Strip everything before the first version (page title, frontmatter, etc.)
        _header, *sections = markdown.split("\n## ")
        # Drop "---" dividers, they'll be added in manually later
        return [f"## {section.rstrip().removesuffix('---').rstrip()}" for section in sections]

    def _load_more_if_needed(self) -> None:
        """Load more markdown sections, if needed."""
        text_browser = self.layout().text_browser
        scroll_bar = text_browser.verticalScrollBar()
        near_bottom = scroll_bar.value() >= scroll_bar.maximum() - scroll_bar.pageStep()
        if self._is_loading or not near_bottom or self._loaded_count >= len(self._sections):
            return

        self._is_loading = True
        section = self._sections[self._loaded_count]
        start = 0
        if self._loaded_count == 0:
            text_browser.setMarkdown(section)
        else:
            cursor = QTextCursor(text_browser.document())
            cursor.movePosition(QTextCursor.MoveOperation.End)
            start = cursor.position()
            cursor.insertMarkdown(f"***\n\n{section}")  # NOTE: Qt reads "---" as YAML frontmatter

        self._separate_images(start)
        self._style_new_blocks(start)
        self._loaded_count += 1
        self._is_loading = False

        # Recheck layout after inserting content in case things have moved
        QTimer.singleShot(0, self._load_more_if_needed)

    def _separate_images(self, start: int) -> None:
        """Separate images into their own blocks.

        Qt tries to merge <img> tags into the markdown block, so this stops it from mangling them.
        """
        document = self.layout().text_browser.document()
        block = document.findBlock(start)
        while block.isValid():
            fragments = block.begin()
            while not fragments.atEnd():
                fragment = fragments.fragment()
                if fragment.charFormat().isImageFormat():
                    if fragment.position() > block.position():
                        cursor = QTextCursor(document)
                        cursor.setPosition(fragment.position())
                        cursor.insertBlock(QTextBlockFormat())
                    break
                fragments += 1
            block = block.next()

    def _style_new_blocks(self, start: int) -> None:
        """Apply styling to the markdown document.

        Args:
            start (int): The starting character position to style onwards from.
        """
        document = self.layout().text_browser.document()
        cursor = QTextCursor(document)
        link_format = QTextCharFormat()
        link_format.setForeground(QColor(get_ui_color(ColorType.PRIMARY, UiColor.BLUE)))
        small_format = QTextCharFormat()
        small_format.setForeground(QColor(MUTED_PURPLE_OPAQUE))
        small_format.setProperty(QTextFormat.Property.FontSizeAdjustment, 1)
        italic_format = QTextCharFormat()
        italic_format.setFontUnderline(False)  # Read "_text_" as italic, not underlined
        italic_format.setFontItalic(True)

        # Loop through each markdown block
        block = document.findBlock(start)
        while block.isValid():
            block_format = block.blockFormat()
            heading_level = block_format.headingLevel()

            images: list[tuple[int, int]] = []  # (position, length) of each image
            links: list[tuple[int, int]] = []  # (position, length) of each link
            smalls: list[tuple[int, int]] = []  # Release dates (<small> tags)
            underlines: list[tuple[int, int]] = []

            # Loop through each markdown block "fragment" (individual styled text sections)
            # and keep track of specific fragments that need special styling later
            fragments = block.begin()
            while not fragments.atEnd():
                fragment = fragments.fragment()
                span = (fragment.position(), fragment.length())
                char_format = fragment.charFormat()
                if char_format.isImageFormat():
                    images.append(span)
                elif char_format.isAnchor():
                    links.append(span)
                elif char_format.fontUnderline():
                    underlines.append(span)
                elif (
                    heading_level == 2
                    and char_format.property(QTextFormat.Property.FontSizeAdjustment) == -1
                ):
                    smalls.append(span)
                fragments += 1

            # Add alignment and spacing to each block
            # NOTE: Neighboring margins aren't additive, only the larger margin is used
            if heading_level == 2 or images:
                block_format.setAlignment(Qt.AlignmentFlag.AlignHCenter)
            if heading_level in (3, 4):
                block_format.setTopMargin(_H3_SPACING if heading_level == 3 else _HEADING_SPACING)
                block_format.setBottomMargin(_HEADING_SPACING)
            if block.textList():
                is_list_end = not block.next().textList()
                block_format.setTopMargin(_LIST_ITEM_SPACING)
                block_format.setBottomMargin(
                    _LIST_END_SPACING if is_list_end else _LIST_ITEM_SPACING
                )
            if block_format.hasProperty(QTextFormat.Property.BlockTrailingHorizontalRulerWidth):
                block_format.setTopMargin(_DIVIDER_SPACING)
                block_format.setBackground(QColor(MUTED_PURPLE))
            if images:
                block_format.setTopMargin(_IMAGE_SPACING)
                block_format.setBottomMargin(_IMAGE_SPACING)
                # Spaces out rows of images that wrap within the same paragraph
                block_format.setLineHeight(
                    _IMAGE_SPACING, QTextBlockFormat.LineHeightTypes.LineDistanceHeight.value
                )
            if block_format != block.blockFormat():
                cursor.setPosition(block.position())
                cursor.setBlockFormat(block_format)

            # Force a specific blue color for links that's always readable on the background
            for position, length in links:
                cursor.setPosition(position)
                cursor.setPosition(position + length, QTextCursor.MoveMode.KeepAnchor)
                cursor.mergeCharFormat(link_format)

            # Apply styling to <small> tags
            for position, length in smalls:
                cursor.setPosition(position)
                cursor.setPosition(position + length, QTextCursor.MoveMode.KeepAnchor)
                cursor.mergeCharFormat(small_format)

            # Use correct italics/underline formatting
            for position, length in underlines:
                cursor.setPosition(position)
                cursor.setPosition(position + length, QTextCursor.MoveMode.KeepAnchor)
                cursor.mergeCharFormat(italic_format)

            # Request image downloads, keep track of their widths, and clear the <img> dimensions
            for position, length in images:
                cursor.setPosition(position)
                cursor.setPosition(position + length, QTextCursor.MoveMode.KeepAnchor)
                image_format = cursor.charFormat().toImageFormat()
                url = image_format.name()
                if url not in self._image_widths:
                    self._image_widths[url] = image_format.width()
                    self._network.get(QNetworkRequest(QUrl(url)))
                image_format.clearProperty(QTextFormat.Property.ImageWidth)
                image_format.clearProperty(QTextFormat.Property.ImageHeight)
                cursor.setCharFormat(image_format)
            block = block.next()

    def _on_image_downloaded(self, reply: QNetworkReply) -> None:
        reply.deleteLater()
        url = reply.request().url()
        image = QImage.fromData(reply.readAll())
        if image.isNull():
            logger.warning(
                "[ChangelogModal] Couldn't load image", url=url, error=reply.errorString()
            )
            return

        width = min(
            self._image_widths[url.toString()] or image.width(),
            _IMAGE_MAX_WIDTH * _WINDOW_WIDTH,
            _IMAGE_MAX_HEIGHT * image.width() / image.height(),
        )
        pixel_ratio = self.devicePixelRatio()
        image.setDevicePixelRatio(pixel_ratio)
        image = image.scaledToWidth(
            round(width * pixel_ratio), Qt.TransformationMode.SmoothTransformation
        )

        document = self.layout().text_browser.document()
        document.addResource(QTextDocument.ResourceType.ImageResource.value, url, image)
        document.markContentsDirty(0, document.characterCount())

    @override
    def parent_post_init(self) -> None:
        window = self.window()
        window.setFixedWidth(_WINDOW_WIDTH)
        window.setMaximumHeight(_WINDOW_MAX_HEIGHT)
        window.setStyleSheet("QLabel {color: white}")

        modal_view = window.layout()
        assert isinstance(modal_view, ModalView)
        close_button = unwrap(self.done_button)
        close_button.setText(Translations["generic.close"])
        modal_view.button_box.addButton(
            self.layout().view_more_button, QDialogButtonBox.ButtonRole.ActionRole
        )

        # NOTE: A lot of the styling is similar to the "About" window, which eventually needs to be
        # refactored to use the Modal class anyway, and can likely share a lot of this code
        pixel_ratio = window.devicePixelRatio()
        background = ResourceManager().about_bg
        background.setDevicePixelRatio(pixel_ratio)
        background = background.scaled(
            QSize(
                math.floor(_WINDOW_WIDTH * pixel_ratio),
                math.floor(_WINDOW_MAX_HEIGHT * pixel_ratio * 0.8),
            ),
            Qt.AspectRatioMode.IgnoreAspectRatio,
            Qt.TransformationMode.SmoothTransformation,
        )

        # NOTE: This stops the bg image from tiling and fills in the rest with a black background
        canvas = QPixmap(background.width(), math.floor(_WINDOW_MAX_HEIGHT * pixel_ratio))
        canvas.setDevicePixelRatio(pixel_ratio)
        canvas.fill(Qt.GlobalColor.black)
        painter = QPainter(canvas)
        painter.drawPixmap(0, 0, background)
        painter.end()

        palette = window.palette()
        palette.setBrush(QPalette.ColorRole.Window, canvas)
        window.setPalette(palette)

    @override
    def showEvent(self, event: QShowEvent) -> None:
        self.layout().text_browser.verticalScrollBar().setValue(0)
        return super().showEvent(event)

    @override
    def layout(self) -> ChangelogModalView:
        return super().layout()  # pyright: ignore[reportReturnType]
