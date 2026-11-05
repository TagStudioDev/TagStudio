# SPDX-FileCopyrightText: (c) TagStudio Contributors
# SPDX-License-Identifier: GPL-3.0-only


import typing
from enum import IntEnum

from PySide6.QtWidgets import (
    QHBoxLayout,
    QSplitter,
    QVBoxLayout,
    QWidget,
)

from tagstudio.i18n.translations import Translations
from tagstudio.qt.controllers.browsing_area import BrowsingArea
from tagstudio.qt.controllers.browsing_controls import BrowsingControls
from tagstudio.qt.controllers.flat_button import FlatButton
from tagstudio.qt.controllers.inspector import Inspector
from tagstudio.qt.controllers.mode_rail import ModeRail
from tagstudio.qt.controllers.search_bar import SearchBar
from tagstudio.qt.controllers.tagging_panel import TaggingPanel
from tagstudio.qt.controllers.toggle_group import ToggleGroup
from tagstudio.qt.resource_manager import ResourceManager
from tagstudio.qt.views.styles.stylesheets import MED_HEIGHT, PAD, WIN_PAD
from tagstudio.qt.views.styles.tagstudio_style import set_handle_span, set_shown_at_rest
from tagstudio.qt.views.toggle_group_view import Toggle

if typing.TYPE_CHECKING:
    from tagstudio.qt.qt_driver import QtDriver

_SIDE_PANEL_ICON_SIZE = 18


class SidePanelToggle(IntEnum):
    PREVIEW = 0
    FILE_INFO = 1
    TAGS_AND_FIELDS = 2
    TAGGING_PANEL = 3


class MainWindowView(QHBoxLayout):
    PANEL_HANDLE_INSETS = (MED_HEIGHT + PAD, WIN_PAD)  # (Top, Bottom)

    def __init__(self, driver: QtDriver, pixel_ratio: float) -> None:
        super().__init__()
        self.setContentsMargins(0, WIN_PAD, 0, 0)
        self.setSpacing(0)
        rm = ResourceManager()

        self.mode_rail = ModeRail()
        self.search_bar = SearchBar(driver.lib)
        self.browsing_controls = BrowsingControls()
        self.browsing_area = BrowsingArea(driver, pixel_ratio)
        self.inspector = Inspector(driver)
        self.tagging_panel = TaggingPanel(driver.lib)
        self.central_content = QWidget()
        self.central_content.setObjectName("central_content")
        central_content_layout = QVBoxLayout(self.central_content)
        central_content_layout.setContentsMargins(0, 0, 0, 0)
        central_content_layout.setSpacing(PAD)
        central_content_layout.addWidget(self.search_bar)
        central_content_layout.addWidget(self.browsing_controls)
        central_content_layout.addWidget(self.browsing_area)

        # Panel Toggles
        self.inspector_toggles = ToggleGroup(
            [
                Toggle(
                    rm.preview_icon, rm.preview_icon_solid, Translations["panel.inspector.preview"]
                ),
                Toggle(rm.info_outline, rm.info_solid, Translations["panel.inspector.file_info"]),
                Toggle(
                    rm.tags_fields_icon,
                    rm.tags_fields_icon_solid,
                    Translations["panel.inspector.tags_fields"],
                ),
                Toggle(
                    rm.tagging_panel_icon,
                    rm.tagging_panel_icon_solid,
                    Translations["panel.tagging"],
                ),
            ]
        )

        self.side_panel_button = FlatButton(
            rm.right_side_panel_show_icon,
            rm.right_side_panel_collapse_icon,
            _SIDE_PANEL_ICON_SIZE,
        )
        self.side_panel_button.setCheckable(True)
        self.side_panel_button.setChecked(True)
        self.side_panel_button.setToolTip(Translations["panel.toggle"])

        # Side Panel
        self.tagging_panel.setHidden(True)
        self.side_splitter = QSplitter()
        self.side_splitter.setObjectName("side_splitter")
        self.side_splitter.setHandleWidth(WIN_PAD)
        set_handle_span(self.side_splitter, 0, WIN_PAD)
        set_shown_at_rest(self.side_splitter, shown=False)
        self.side_splitter.addWidget(self.inspector)
        self.side_splitter.addWidget(self.tagging_panel)
        self.side_splitter.setStretchFactor(0, 1)
        for index in range(self.side_splitter.count()):
            self.side_splitter.setCollapsible(index, False)  # noqa: FBT003
        self.side_contents = QWidget()
        side_contents_layout = QVBoxLayout(self.side_contents)
        side_contents_layout.setContentsMargins(0, 0, 0, 0)
        side_contents_layout.setSpacing(PAD)
        side_header = QHBoxLayout()
        side_header.setContentsMargins(0, 0, 0, 0)
        side_header.setSpacing(0)
        side_header.addSpacing(MED_HEIGHT + PAD)
        side_header.addStretch()
        side_header.addWidget(self.inspector_toggles)
        side_header.addStretch()
        side_header.addSpacing(MED_HEIGHT + PAD)
        side_contents_layout.addLayout(side_header)
        side_contents_layout.addWidget(self.side_splitter, stretch=1)

        self.side_panel = QWidget()
        side_panel_layout = QHBoxLayout(self.side_panel)
        side_panel_layout.setContentsMargins(0, 0, WIN_PAD, 0)
        side_panel_layout.addWidget(self.side_contents)

        self.content_splitter = QSplitter()
        self.content_splitter.setObjectName("content_splitter")
        self.content_splitter.setHandleWidth(WIN_PAD)
        self.content_splitter.addWidget(self.central_content)
        self.content_splitter.addWidget(self.side_panel)
        self.content_splitter.setStretchFactor(0, 1)
        self.addWidget(self.mode_rail)
        self.addWidget(self.content_splitter)
