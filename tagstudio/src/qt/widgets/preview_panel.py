# Copyright (C) 2024 Travis Abendshien (CyanVoxel).
# Licensed under the GPL-3.0 License.
# Created for TagStudio: https://github.com/CyanVoxel/TagStudio
import sys
from collections.abc import Callable
from pathlib import Path
import time
import typing
from datetime import datetime as dt

import cv2
import rawpy
import structlog
from PIL import Image, UnidentifiedImageError
from PIL.Image import DecompressionBombError
from PySide6.QtCore import Signal, Qt, QSize
from PySide6.QtGui import QResizeEvent, QAction
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QFrame,
    QSplitter,
    QSizePolicy,
    QMessageBox,
)
from humanfriendly import format_size

from src.core.enums import SettingItems, Theme
from src.core.constants import VIDEO_TYPES, IMAGE_TYPES, RAW_IMAGE_TYPES, TS_FOLDER_NAME
from src.core.library.alchemy.enums import FilterState
from src.core.library.alchemy.fields import (
    TagBoxField,
    DatetimeField,
    FieldTypeEnum,
    Field,
    _FieldID,
    TextField,
)
from src.qt.helpers.file_opener import FileOpenerLabel, FileOpenerHelper, open_file
from src.qt.modals.add_field import AddFieldModal
from src.qt.widgets.thumb_renderer import ThumbRenderer
from src.qt.widgets.fields import FieldContainer
from src.qt.widgets.tag_box import TagBoxWidget
from src.qt.widgets.text import TextWidget
from src.qt.widgets.panel import PanelModal
from src.qt.widgets.text_box_edit import EditTextBox
from src.qt.widgets.text_line_edit import EditTextLine
from src.qt.helpers.qbutton_wrapper import QPushButtonWrapper
from src.qt.widgets.video_player import VideoPlayer
from src.core.library.alchemy.library import Library

if typing.TYPE_CHECKING:
    from src.qt.ts_qt import QtDriver

logger = structlog.get_logger(__name__)


def update_selected_entry(driver: "QtDriver"):
    for grid_idx in driver.selected:
        entry = driver.frame_content[grid_idx]
        # reload entry
        _, entries = driver.lib.search_library(FilterState(id=entry.id))
        logger.info(
            "found item", entries=entries, grid_idx=grid_idx, lookup_id=entry.id
        )
        assert entries, f"Entry not found: {entry.id}"
        driver.frame_content[grid_idx] = entries[0]


class PreviewPanel(QWidget):
    """The Preview Panel Widget."""

    tags_updated = Signal()

    def __init__(self, library: Library, driver: "QtDriver"):
        super().__init__()
        self.is_connected = False
        self.lib = library
        self.driver: QtDriver = driver
        self.initialized = False
        self.is_open: bool = False
        # self.filepath = None
        # self.item = None # DEPRECATED, USE self.selected
        self.common_fields: list = []
        self.mixed_fields: list = []
        self.selected: list[int] = []  # New way of tracking items
        self.tag_callback = None
        self.containers: list[FieldContainer] = []

        self.img_button_size: tuple[int, int] = (266, 266)
        self.image_ratio: float = 1.0

        self.image_container = QWidget()
        image_layout = QHBoxLayout(self.image_container)
        image_layout.setContentsMargins(0, 0, 0, 0)

        self.open_file_action = QAction("Open file", self)
        self.open_explorer_action = QAction("Open file in explorer", self)

        self.preview_img = QPushButtonWrapper()
        self.preview_img.setMinimumSize(*self.img_button_size)
        self.preview_img.setFlat(True)
        self.preview_img.setContextMenuPolicy(Qt.ContextMenuPolicy.ActionsContextMenu)

        self.preview_img.addAction(self.open_file_action)
        self.preview_img.addAction(self.open_explorer_action)
        self.preview_vid = VideoPlayer(driver)
        self.preview_vid.hide()
        self.thumb_renderer = ThumbRenderer()
        self.thumb_renderer.updated.connect(
            lambda ts, i, s: (self.preview_img.setIcon(i))
        )
        self.thumb_renderer.updated_ratio.connect(
            lambda ratio: (
                self.set_image_ratio(ratio),
                self.update_image_size(
                    (
                        self.image_container.size().width(),
                        self.image_container.size().height(),
                    ),
                    ratio,
                ),
            )
        )

        image_layout.addWidget(self.preview_img)
        image_layout.setAlignment(self.preview_img, Qt.AlignmentFlag.AlignCenter)
        image_layout.addWidget(self.preview_vid)
        image_layout.setAlignment(self.preview_vid, Qt.AlignmentFlag.AlignCenter)
        self.image_container.setMinimumSize(*self.img_button_size)
        self.file_label = FileOpenerLabel("Filename")
        self.file_label.setWordWrap(True)
        self.file_label.setTextInteractionFlags(
            Qt.TextInteractionFlag.TextSelectableByMouse
        )
        self.file_label.setStyleSheet("font-weight: bold; font-size: 12px")

        self.dimensions_label = QLabel("Dimensions")
        self.dimensions_label.setWordWrap(True)
        # self.dim_label.setTextInteractionFlags(
        # 	Qt.TextInteractionFlag.TextSelectableByMouse)

        properties_style = (
            f"background-color:{Theme.COLOR_BG.value};"
            f"font-family:Oxanium;"
            f"font-weight:bold;"
            f"font-size:12px;"
            f"border-radius:6px;"
            f"padding-top: 4px;"
            f"padding-right: 1px;"
            f"padding-bottom: 1px;"
            f"padding-left: 1px;"
        )

        self.dimensions_label.setStyleSheet(properties_style)

        self.scroll_layout = QVBoxLayout()
        self.scroll_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.scroll_layout.setContentsMargins(6, 1, 6, 6)

        scroll_container: QWidget = QWidget()
        scroll_container.setObjectName("entryScrollContainer")
        scroll_container.setLayout(self.scroll_layout)

        info_section = QWidget()
        info_layout = QVBoxLayout(info_section)
        info_layout.setContentsMargins(0, 0, 0, 0)
        info_layout.setSpacing(6)

        scroll_area = QScrollArea()
        scroll_area.setObjectName("entryScrollArea")
        scroll_area.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding
        )
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll_area.setWidgetResizable(True)
        scroll_area.setFrameShadow(QFrame.Shadow.Plain)
        scroll_area.setFrameShape(QFrame.Shape.NoFrame)
        # NOTE: I would rather have this style applied to the scroll_area
        # background and NOT the scroll container background, so that the
        # rounded corners are maintained when scrolling. I was unable to
        # find the right trick to only select that particular element.
        scroll_area.setStyleSheet(
            "QWidget#entryScrollContainer{"
            f"background: {Theme.COLOR_BG.value};"
            "border-radius:6px;"
            "}"
        )
        scroll_area.setWidget(scroll_container)

        info_layout.addWidget(self.file_label)
        info_layout.addWidget(self.dimensions_label)
        info_layout.addWidget(scroll_area)

        # keep list of rendered libraries to avoid needless re-rendering
        self.render_libs: set = set()
        self.libs_layout = QVBoxLayout()
        self.fill_libs_widget(self.libs_layout)

        self.libs_flow_container: QWidget = QWidget()
        self.libs_flow_container.setObjectName("librariesList")
        self.libs_flow_container.setLayout(self.libs_layout)
        self.libs_flow_container.setSizePolicy(
            QSizePolicy.Preferred,  # type: ignore
            QSizePolicy.Maximum,  # type: ignore
        )

        # set initial visibility based on settings
        if not self.driver.settings.value(
            SettingItems.WINDOW_SHOW_LIBS, True, type=bool
        ):
            self.libs_flow_container.hide()

        splitter = QSplitter()
        splitter.setOrientation(Qt.Orientation.Vertical)
        splitter.setHandleWidth(12)
        splitter.splitterMoved.connect(
            lambda: self.update_image_size(
                (
                    self.image_container.size().width(),
                    self.image_container.size().height(),
                )
            )
        )

        splitter.addWidget(self.image_container)
        splitter.addWidget(info_section)
        splitter.addWidget(self.libs_flow_container)
        splitter.setStretchFactor(1, 2)

        self.afb_container = QWidget()
        self.afb_layout = QVBoxLayout(self.afb_container)
        self.afb_layout.setContentsMargins(0, 12, 0, 0)

        self.add_field_button = QPushButtonWrapper()
        self.add_field_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.add_field_button.setMinimumSize(96, 28)
        self.add_field_button.setMaximumSize(96, 28)
        self.add_field_button.setText("Add Field")
        self.afb_layout.addWidget(self.add_field_button)
        self.add_field_modal = AddFieldModal(self.lib)
        self.place_add_field_button()
        self.update_image_size(
            (self.image_container.size().width(), self.image_container.size().height())
        )

        root_layout = QHBoxLayout(self)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.addWidget(splitter)

    def remove_field_prompt(self, name: str) -> str:
        return f'Are you sure you want to remove field "{name}"?'

    def fill_libs_widget(self, layout: QVBoxLayout):
        settings = self.driver.settings
        settings.beginGroup(SettingItems.LIBS_LIST)
        lib_items: dict[str, tuple[str, str]] = {}
        for item_tstamp in settings.allKeys():
            val = str(settings.value(item_tstamp, type=str))
            cut_val = val
            if len(val) > 45:
                cut_val = f"{val[0:10]} ... {val[-10:]}"
            lib_items[item_tstamp] = (val, cut_val)

        settings.endGroup()

        new_keys = set(lib_items.keys())
        if new_keys == self.render_libs:
            # no need to re-render
            return

        # sort lib_items by the key
        libs_sorted = sorted(lib_items.items(), key=lambda item: item[0], reverse=True)

        self.render_libs = new_keys
        self._fill_libs_widget(libs_sorted, layout)

    def _fill_libs_widget(
        self, libraries: list[tuple[str, tuple[str, str]]], layout: QVBoxLayout
    ):
        def clear_layout(layout_item: QVBoxLayout):
            for i in reversed(range(layout_item.count())):
                child = layout_item.itemAt(i)
                if child.widget() is not None:
                    child.widget().deleteLater()
                elif child.layout() is not None:
                    clear_layout(child.layout())  # type: ignore

        # remove any potential previous items
        clear_layout(layout)

        label = QLabel("Recent Libraries")
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        row_layout = QHBoxLayout()
        row_layout.addWidget(label)
        layout.addLayout(row_layout)

        def set_button_style(
            btn: QPushButtonWrapper | QPushButton, extras: list[str] | None = None
        ):
            base_style = [
                f"background-color:{Theme.COLOR_BG.value};",
                "border-radius:6px;",
                "text-align: left;",
                "padding-top: 3px;",
                "padding-left: 6px;",
                "padding-bottom: 4px;",
            ]

            full_style_rows = base_style + (extras or [])

            btn.setStyleSheet(
                "QPushButton{"
                f"{''.join(full_style_rows)}"
                "}"
                f"QPushButton::hover{{background-color:{Theme.COLOR_HOVER.value};}}"
                f"QPushButton::pressed{{background-color:{Theme.COLOR_PRESSED.value};}}"
                f"QPushButton::disabled{{background-color:{Theme.COLOR_DISABLED_BG.value};}}"
            )
            btn.setCursor(Qt.CursorShape.PointingHandCursor)

        for item_key, (full_val, cut_val) in libraries:
            button = QPushButton(text=cut_val)
            button.setObjectName(f"path{item_key}")

            lib = Path(full_val)
            if not lib.exists() or not (lib / TS_FOLDER_NAME).exists():
                button.setDisabled(True)
                button.setToolTip("Location is missing")

            def open_library_button_clicked(path):
                return lambda: self.driver.open_library(Path(path))

            button.clicked.connect(open_library_button_clicked(full_val))
            set_button_style(button)
            button_remove = QPushButton("➖")
            button_remove.setCursor(Qt.CursorShape.PointingHandCursor)
            button_remove.setFixedWidth(30)
            set_button_style(button_remove)

            def remove_recent_library_clicked(key: str):
                return lambda: (
                    self.driver.remove_recent_library(key),
                    self.fill_libs_widget(self.libs_layout),
                )

            button_remove.clicked.connect(remove_recent_library_clicked(item_key))

            row_layout = QHBoxLayout()
            row_layout.addWidget(button)
            row_layout.addWidget(button_remove)

            layout.addLayout(row_layout)

    def resizeEvent(self, event: QResizeEvent) -> None:
        self.update_image_size(
            (self.image_container.size().width(), self.image_container.size().height())
        )
        return super().resizeEvent(event)

    def get_preview_size(self) -> tuple[int, int]:
        return (
            self.image_container.size().width(),
            self.image_container.size().height(),
        )

    def set_image_ratio(self, ratio: float):
        # logging.info(f'Updating Ratio to: {ratio} #####################################################')
        self.image_ratio = ratio

    def update_image_size(self, size: tuple[int, int], ratio: float = None):
        if ratio:
            self.set_image_ratio(ratio)
        # self.img_button_size = size
        # logging.info(f'')
        # self.preview_img.setMinimumSize(64,64)

        adj_width: float = size[0]
        adj_height: float = size[1]
        # Landscape
        if self.image_ratio > 1:
            # logging.info('Landscape')
            adj_height = size[0] * (1 / self.image_ratio)
        # Portrait
        elif self.image_ratio <= 1:
            # logging.info('Portrait')
            adj_width = size[1] * self.image_ratio

        if adj_width > size[0]:
            adj_height = adj_height * (size[0] / adj_width)
            adj_width = size[0]
        elif adj_height > size[1]:
            adj_width = adj_width * (size[1] / adj_height)
            adj_height = size[1]

        # adj_width = min(adj_width, self.image_container.size().width())
        # adj_height = min(adj_width, self.image_container.size().height())

        # self.preview_img.setMinimumSize(s)
        # self.preview_img.setMaximumSize(s_max)
        adj_size = QSize(int(adj_width), int(adj_height))
        self.img_button_size = (int(adj_width), int(adj_height))
        self.preview_img.setMaximumSize(adj_size)
        self.preview_img.setIconSize(adj_size)
        self.preview_vid.resizeVideo(adj_size)
        self.preview_vid.setMaximumSize(adj_size)
        self.preview_vid.setMinimumSize(adj_size)
        # self.preview_img.setMinimumSize(adj_size)

    def place_add_field_button(self):
        self.scroll_layout.addWidget(self.afb_container)
        self.scroll_layout.setAlignment(
            self.afb_container, Qt.AlignmentFlag.AlignHCenter
        )

        if self.add_field_modal.is_connected:
            self.add_field_modal.done.disconnect()
        if self.add_field_button.is_connected:
            self.add_field_button.clicked.disconnect()

        # self.afm.done.connect(lambda f: (self.lib.add_field_to_entry(self.selected[0][1], f), self.update_widgets()))
        self.add_field_modal.done.connect(
            lambda items: (
                self.add_field_to_selected(items),
                update_selected_entry(self.driver),
                self.update_widgets(),
            )
        )
        self.add_field_modal.is_connected = True
        self.add_field_button.clicked.connect(self.add_field_modal.show)

    def add_field_to_selected(self, field_list: list):
        """Add list of entry fields to one or more selected items."""
        logger.info("add_field_to_selected", selected=self.selected, fields=field_list)
        for grid_idx in self.selected:
            entry = self.driver.frame_content[grid_idx]
            for field_item in field_list:
                self.lib.add_entry_field_type(
                    entry.id,
                    field_id=field_item.data(Qt.ItemDataRole.UserRole),
                )

    def update_widgets(self) -> bool:
        """
        Render the panel widgets with the newest data from the Library.
        """
        logger.info("update_widgets", selected=self.driver.selected)
        self.is_open = True
        # self.tag_callback = tag_callback if tag_callback else None
        window_title = ""

        # update list of libraries
        self.fill_libs_widget(self.libs_layout)

        if not self.driver.selected:
            if self.selected or not self.initialized:
                self.file_label.setText("No Items Selected")
                self.file_label.setFilePath("")
                self.file_label.setCursor(Qt.CursorShape.ArrowCursor)

                self.dimensions_label.setText("")
                self.preview_img.setContextMenuPolicy(
                    Qt.ContextMenuPolicy.NoContextMenu
                )
                self.preview_img.setCursor(Qt.CursorShape.ArrowCursor)

                ratio = self.devicePixelRatio()
                self.thumb_renderer.render(
                    time.time(),
                    "",
                    (512, 512),
                    ratio,
                    True,
                    update_on_ratio_change=True,
                )
                if self.preview_img.is_connected:
                    self.preview_img.clicked.disconnect()
                for c in self.containers:
                    c.setHidden(True)
            self.preview_img.show()
            self.preview_vid.stop()
            self.preview_vid.hide()
            self.selected = list(self.driver.selected)
            self.add_field_button.setHidden(True)

            # common code
            self.initialized = True
            self.setWindowTitle(window_title)
            self.show()
            return True

        # reload entry and fill it into the grid again
        # TODO - do this more granular
        # TODO - Entry reload is maybe not necessary
        for grid_idx in self.driver.selected:
            entry = self.driver.frame_content[grid_idx]
            _, entries = self.lib.search_library(FilterState(id=entry.id))
            logger.info(
                "found item", entries=entries, grid_idx=grid_idx, lookup_id=entry.id
            )
            self.driver.frame_content[grid_idx] = entries[0]

        if len(self.driver.selected) == 1:
            # 1 Selected Entry
            selected_idx = self.driver.selected[0]
            item = self.driver.frame_content[selected_idx]

            self.preview_img.show()
            self.preview_vid.stop()
            self.preview_vid.hide()

            # If a new selection is made, update the thumbnail and filepath.
            if not self.selected or self.selected != self.driver.selected:
                filepath = self.lib.library_dir / item.path
                self.file_label.setFilePath(filepath)
                ratio = self.devicePixelRatio()
                self.thumb_renderer.render(
                    time.time(),
                    filepath,
                    (512, 512),
                    ratio,
                    update_on_ratio_change=True,
                )
                self.file_label.setText("\u200b".join(str(filepath)))
                self.file_label.setCursor(Qt.CursorShape.PointingHandCursor)

                self.preview_img.setContextMenuPolicy(
                    Qt.ContextMenuPolicy.ActionsContextMenu
                )
                self.preview_img.setCursor(Qt.CursorShape.PointingHandCursor)

                self.opener = FileOpenerHelper(filepath)
                self.open_file_action.triggered.connect(self.opener.open_file)
                self.open_explorer_action.triggered.connect(self.opener.open_explorer)

                # TODO: Do this somewhere else, this is just here temporarily.
                try:
                    image = None
                    if filepath.suffix.lower() in IMAGE_TYPES:
                        image = Image.open(str(filepath))
                    elif filepath.suffix.lower() in RAW_IMAGE_TYPES:
                        try:
                            with rawpy.imread(str(filepath)) as raw:
                                rgb = raw.postprocess()
                                image = Image.new(
                                    "L", (rgb.shape[1], rgb.shape[0]), color="black"
                                )
                        except (
                            rawpy._rawpy.LibRawIOError,
                            rawpy._rawpy.LibRawFileUnsupportedError,
                        ):
                            pass
                    elif filepath.suffix.lower() in VIDEO_TYPES:
                        video = cv2.VideoCapture(str(filepath))
                        if video.get(cv2.CAP_PROP_FRAME_COUNT) <= 0:
                            raise cv2.error("File is invalid or has 0 frames")
                        video.set(cv2.CAP_PROP_POS_FRAMES, 0)
                        success, frame = video.read()
                        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                        image = Image.fromarray(frame)
                        if success:
                            self.preview_img.hide()
                            self.preview_vid.play(
                                filepath, QSize(image.width, image.height)
                            )
                            self.resizeEvent(
                                QResizeEvent(
                                    QSize(image.width, image.height),
                                    QSize(image.width, image.height),
                                )
                            )
                            self.preview_vid.show()

                    # Stats for specific file types are displayed here.
                    if image and filepath.suffix.lower() in (
                        IMAGE_TYPES + VIDEO_TYPES + RAW_IMAGE_TYPES
                    ):
                        self.dimensions_label.setText(
                            f"{filepath.suffix.upper()[1:]}  •  {format_size(filepath.stat().st_size)}\n{image.width} x {image.height} px"
                        )
                    else:
                        self.dimensions_label.setText(
                            f"{filepath.suffix.upper()[1:]}  •  {format_size(filepath.stat().st_size)}"
                        )

                    if not filepath.is_file():
                        raise FileNotFoundError

                except (FileNotFoundError, cv2.error) as e:
                    self.dimensions_label.setText(f"{filepath.suffix.upper()}")
                    logger.error(
                        "Couldn't Render thumbnail", filepath=filepath, error=e
                    )

                except (
                    UnidentifiedImageError,
                    DecompressionBombError,
                ) as e:
                    self.dimensions_label.setText(
                        f"{filepath.suffix.upper()[1:]}  •  {format_size(filepath.stat().st_size)}"
                    )
                    logger.error(
                        "Couldn't Render thumbnail", filepath=filepath, error=e
                    )

                if self.preview_img.is_connected:
                    self.preview_img.clicked.disconnect()
                self.preview_img.clicked.connect(
                    lambda checked=False, pth=filepath: open_file(pth)
                )
                self.preview_img.is_connected = True

            self.selected = self.driver.selected
            logger.info("rendering item fields", item=item, fields=item.tag_box_fields)
            for idx, field in enumerate(item.fields):
                logger.info("write container in update_widgets", idx=idx, field=field)
                self.write_container(idx, field)

            # Hide leftover containers
            if len(self.containers) > len(item.fields):
                for i, c in enumerate(self.containers):
                    if i > (len(item.fields) - 1):
                        c.setHidden(True)

            self.add_field_button.setHidden(False)

        # Multiple Selected Items
        elif len(self.driver.selected) > 1:
            self.preview_img.show()
            self.preview_vid.stop()
            self.preview_vid.hide()
            if self.selected != self.driver.selected:
                self.file_label.setText(f"{len(self.driver.selected)} Items Selected")
                self.file_label.setCursor(Qt.CursorShape.ArrowCursor)
                self.file_label.setFilePath("")
                self.dimensions_label.setText("")

                self.preview_img.setContextMenuPolicy(
                    Qt.ContextMenuPolicy.NoContextMenu
                )
                self.preview_img.setCursor(Qt.CursorShape.ArrowCursor)

                ratio = self.devicePixelRatio()
                self.thumb_renderer.render(
                    time.time(),
                    "",
                    (512, 512),
                    ratio,
                    True,
                    update_on_ratio_change=True,
                )
                if self.preview_img.is_connected:
                    self.preview_img.clicked.disconnect()
                    self.preview_img.is_connected = False

            # fill shared fields from first item
            first_item = self.driver.frame_content[self.driver.selected[0]]
            common_fields = [f for f in first_item.fields]
            mixed_fields = []

            # iterate through other items
            for grid_idx in self.driver.selected[1:]:
                item = self.driver.frame_content[grid_idx]
                item_field_types = {f.type_key for f in item.fields}
                for f in common_fields[:]:
                    if f.type_key not in item_field_types:
                        common_fields.remove(f)
                        mixed_fields.append(f)

            self.common_fields = common_fields
            self.mixed_fields = sorted(mixed_fields, key=lambda x: x.type.order)

            self.selected = list(self.driver.selected)
            logger.info(
                "update_widgets common_fields",
                common_fields=self.common_fields,
            )
            for i, f in enumerate(self.common_fields):
                self.write_container(i, f)

            logger.info(
                "update_widgets mixed_fields",
                mixed_fields=self.mixed_fields,
                start=len(self.common_fields),
            )
            for i, f in enumerate(self.mixed_fields, start=len(self.common_fields)):
                self.write_container(i, f, is_mixed=True)

            # Hide leftover containers
            if len(self.containers) > len(self.common_fields) + len(self.mixed_fields):
                for i, c in enumerate(self.containers):
                    if i > (len(self.common_fields) + len(self.mixed_fields) - 1):
                        c.setHidden(True)

            self.add_field_button.setHidden(False)

        self.initialized = True

        self.setWindowTitle(window_title)
        self.show()
        return True

    def set_tags_updated_slot(self, slot: object):
        """
        Replacement for tag_callback.
        """
        if self.is_connected:
            self.tags_updated.disconnect()

        logger.info("[UPDATE CONTAINER] Setting tags updated slot")
        self.tags_updated.connect(slot)
        self.is_connected = True

    def write_container(self, index: int, field: Field, is_mixed: bool = False):
        """Update/Create data for a FieldContainer.

        :param is_mixed: Relevant when multiple items are selected. If True, field is not present in all selected items
        """
        # Remove 'Add Field' button from scroll_layout, to be re-added later.
        self.scroll_layout.takeAt(self.scroll_layout.count() - 1).widget()
        if len(self.containers) < (index + 1):
            container = FieldContainer()
            self.containers.append(container)
            self.scroll_layout.addWidget(container)
        else:
            container = self.containers[index]

        container.set_copy_callback(None)
        container.set_edit_callback(None)
        container.set_remove_callback(None)

        if isinstance(field, TagBoxField):
            container.set_title(field.type.name)
            container.set_inline(False)
            title = f"{field.type.name} (Tag Box)"

            if not is_mixed:
                inner_container = container.get_inner_widget()
                if isinstance(inner_container, TagBoxWidget):
                    inner_container.set_field(field)
                    inner_container.set_tags(list(field.tags))

                    try:
                        inner_container.updated.disconnect()
                    except RuntimeError:
                        logger.error("Failed to disconnect inner_container.updated")

                else:
                    logger.info(
                        "inner_container is not instance of TagBoxWidget",
                        container=inner_container,
                    )
                    inner_container = TagBoxWidget(
                        field,
                        title,
                        self.driver,
                    )

                    container.set_inner_widget(inner_container)

                # inner_container.field = field
                inner_container.updated.connect(
                    lambda: (
                        self.write_container(index, field),
                        self.update_widgets(),
                    )
                )
                # NOTE: Tag Boxes have no Edit Button (But will when you can convert field types)
                # container.set_remove_callback(lambda: (self.lib.get_entry(item.id).fields.pop(index), self.update_widgets(item)))
                container.set_remove_callback(
                    lambda: self.remove_message_box(
                        prompt=self.remove_field_prompt(field.type.name),
                        callback=lambda: (
                            self.remove_field(field),
                            update_selected_entry(self.driver),
                            # reload entry and its fields
                            self.update_widgets(),
                        ),
                    )
                )
            else:
                text = "<i>Mixed Data</i>"
                title = f"{field.type.name} (Wacky Tag Box)"
                inner_container = TextWidget(title, text)
                container.set_inner_widget(inner_container)

            self.tags_updated.emit()
            # self.dynamic_widgets.append(inner_container)
        elif field.type.type == FieldTypeEnum.TEXT_LINE:
            container.set_title(field.type.name)
            container.set_inline(False)

            # Normalize line endings in any text content.
            if not is_mixed:
                assert isinstance(field.value, (str, type(None)))
                text = field.value or ""
            else:
                text = "<i>Mixed Data</i>"

            title = f"{field.type.name} ({field.type.type.value})"
            inner_container = TextWidget(title, text)
            container.set_inner_widget(inner_container)
            if not is_mixed:
                modal = PanelModal(
                    EditTextLine(field.value),
                    title=title,
                    window_title=f"Edit {field.type.type.value}",
                    save_callback=(
                        lambda content: (
                            self.update_field(field, content),
                            self.update_widgets(),
                        )
                    ),
                )
                if "pytest" in sys.modules:
                    # for better testability
                    container.modal = modal  # type: ignore

                container.set_edit_callback(modal.show)
                container.set_remove_callback(
                    lambda: self.remove_message_box(
                        prompt=self.remove_field_prompt(field.type.type.value),
                        callback=lambda: (
                            self.remove_field(field),
                            self.update_widgets(),
                        ),
                    )
                )

        elif field.type.type == FieldTypeEnum.TEXT_BOX:
            container.set_title(field.type.name)
            # container.set_editable(True)
            container.set_inline(False)
            # Normalize line endings in any text content.
            if not is_mixed:
                assert isinstance(field.value, (str, type(None)))
                text = (field.value or "").replace("\r", "\n")
            else:
                text = "<i>Mixed Data</i>"
            title = f"{field.type.name} (Text Box)"
            inner_container = TextWidget(title, text)
            container.set_inner_widget(inner_container)
            if not is_mixed:
                modal = PanelModal(
                    EditTextBox(field.value),
                    title=title,
                    window_title=f"Edit {field.type.name}",
                    save_callback=(
                        lambda content: (
                            self.update_field(field, content),
                            self.update_widgets(),
                        )
                    ),
                )
                container.set_edit_callback(modal.show)
                container.set_remove_callback(
                    lambda: self.remove_message_box(
                        prompt=self.remove_field_prompt(field.type.name),
                        callback=lambda: (
                            self.remove_field(field),
                            self.update_widgets(),
                        ),
                    )
                )

        elif field.type == DatetimeField:
            # logging.info(f'WRITING DATETIME FOR ITEM {item.id}')
            if not is_mixed:
                try:
                    container.set_title(field.type.name)
                    # container.set_editable(False)
                    container.set_inline(False)
                    # TODO: Localize this and/or add preferences.
                    date = dt.strptime(field.value, "%Y-%m-%d %H:%M:%S")
                    title = f"{field.type.name} (Date)"
                    inner_container = TextWidget(title, date.strftime("%D - %r"))
                    container.set_inner_widget(inner_container)
                except Exception:
                    container.set_title(field.type.name)
                    # container.set_editable(False)
                    container.set_inline(False)
                    title = f"{field.type.name} (Date) (Unknown Format)"
                    inner_container = TextWidget(title, str(field.value))
                    container.set_inner_widget(inner_container)

                # if type(item) == Entry:
                # container.set_remove_callback(lambda: (self.lib.get_entry(item.id).fields.pop(index), self.update_widgets(item)))
                container.set_remove_callback(
                    lambda: self.remove_message_box(
                        prompt=self.remove_field_prompt(field.type.name),
                        callback=lambda: (
                            self.remove_field(field),
                            self.update_widgets(),
                        ),
                    )
                )
            else:
                text = "<i>Mixed Data</i>"
                title = f"{field.type.name} (Wacky Date)"
                inner_container = TextWidget(title, text)
                container.set_inner_widget(inner_container)
        else:
            container.set_title(field.type.name)
            # container.set_editable(False)
            container.set_inline(False)
            title = f"{field.type.name} (Unknown Field Type)"
            inner_container = TextWidget(title, field.type.name)
            container.set_inner_widget(inner_container)
            # if type(item) == Entry:
            # container.set_remove_callback(lambda: (self.lib.get_entry(item.id).fields.pop(index), self.update_widgets(item)))
            container.set_remove_callback(
                lambda: self.remove_message_box(
                    prompt=self.remove_field_prompt(field.type.name),
                    callback=lambda: (
                        self.remove_field(field),
                        self.update_widgets(),
                    ),
                )
            )

        container.edit_button.setHidden(True)
        container.setHidden(False)
        self.place_add_field_button()

    def remove_field(self, field: Field):
        """Remove a field from all selected Entries."""
        logger.info("removing field", field=field, selected=self.selected)
        entry_ids = []
        for grid_idx in self.selected:
            entry = self.driver.frame_content[grid_idx]
            entry_ids.append(entry.id)

        self.lib.remove_entry_field(field, entry_ids)

        # if the field is meta tags, update the badges
        if field.type_key == _FieldID.TAGS_META.value:
            self.driver.update_badges(self.selected)

    def update_field(self, field: Field, content: str) -> None:
        """Remove a field from all selected Entries, given a field object."""
        assert isinstance(
            field, (TextField, DatetimeField, TagBoxField)
        ), f"instance: {type(field)}"
        entry_ids = []
        for grid_idx in self.selected:
            entry = self.driver.frame_content[grid_idx]
            entry_ids.append(entry.id)

        assert entry_ids, "No entries selected"
        self.lib.update_entry_field(
            entry_ids,
            field,
            content,
        )

    def remove_message_box(self, prompt: str, callback: Callable) -> None:
        remove_mb = QMessageBox()
        remove_mb.setText(prompt)
        remove_mb.setWindowTitle("Remove Field")
        remove_mb.setIcon(QMessageBox.Icon.Warning)
        cancel_button = remove_mb.addButton(
            "&Cancel", QMessageBox.ButtonRole.DestructiveRole
        )
        remove_mb.addButton("&Remove", QMessageBox.ButtonRole.RejectRole)
        # remove_mb.setStandardButtons(QMessageBox.StandardButton.Cancel)
        remove_mb.setDefaultButton(cancel_button)
        remove_mb.setEscapeButton(cancel_button)
        result = remove_mb.exec_()
        # logging.info(result)
        if result == 3:  # TODO - what is this magic number?
            callback()
