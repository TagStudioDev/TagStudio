# Copyright (C) 2025 Travis Abendshien (CyanVoxel).
# Licensed under the GPL-3.0 License.
# Created for TagStudio: https://github.com/CyanVoxel/TagStudio

import typing

import structlog
from PySide6.QtWidgets import (
    QWidget,
)
from src.core.library.alchemy.library import Library

if typing.TYPE_CHECKING:
    from src.qt.ts_qt import QtDriver

logger = structlog.get_logger(__name__)


class RecentLibraries(QWidget):
    """The Recent Libraries Widget."""

    def __init__(self, library: Library, driver: "QtDriver"):
        super().__init__()

    #         # keep list of rendered libraries to avoid needless re-rendering
    #         self.render_libs: set = set()
    #         self.library = library
    #         self.driver = driver
    #         layout = QVBoxLayout()

    #         settings = driver.settings
    #         settings.beginGroup(SettingItems.LIBS_LIST)
    #         lib_items: dict[str, tuple[str, str]] = {}
    #         for item_tstamp in settings.allKeys():
    #             val = str(settings.value(item_tstamp, type=str))
    #             cut_val = val
    #             if len(val) > 45:
    #                 cut_val = f"{val[0:10]} ... {val[-10:]}"
    #             lib_items[item_tstamp] = (val, cut_val)

    #         settings.endGroup()

    #         new_keys = set(lib_items.keys())
    #         if new_keys == self.render_libs:
    #             # no need to re-render
    #             return

    #         # sort lib_items by the key
    #         libs_sorted = sorted(lib_items.items(), key=lambda item: item[0], reverse=True)

    #         self.render_libs = new_keys
    #         self.setLayout(layout)

    #         self._fill_libs_widget(libs_sorted, layout)

    # def _fill_libs_widget(
    #     self,
    #     libraries: list[tuple[str, tuple[str, str]]],
    #     layout: QVBoxLayout,
    # ):
    #     def clear_layout(layout_item: QVBoxLayout):
    #         for i in reversed(range(layout_item.count())):
    #             child = layout_item.itemAt(i)
    #             if child.widget() is not None:
    #                 child.widget().deleteLater()
    #             elif child.layout() is not None:
    #                 clear_layout(child.layout())  # type: ignore


#         # remove any potential previous items
#         clear_layout(layout)

#         label = QLabel()
#         Translations.translate_qobject(label, "generic.recent_libraries")
#         label.setAlignment(Qt.AlignmentFlag.AlignCenter)

#         row_layout = QHBoxLayout()
#         row_layout.addWidget(label)
#         layout.addLayout(row_layout)

#         def set_button_style(
#             btn: QPushButtonWrapper | QPushButton, extras: list[str] | None = None
#         ):
#             base_style = [
#                 f"background-color:{Theme.COLOR_BG.value};",
#                 "border-radius:6px;",
#                 "text-align: left;",
#                 "padding-top: 3px;",
#                 "padding-left: 6px;",
#                 "padding-bottom: 4px;",
#             ]

#             full_style_rows = base_style + (extras or [])

#             btn.setStyleSheet(
#                 "QPushButton{"
#                 f"{''.join(full_style_rows)}"
#                 "}"
#                 f"QPushButton::hover{{background-color:{Theme.COLOR_HOVER.value};}}"
#                 f"QPushButton::pressed{{background-color:{Theme.COLOR_PRESSED.value};}}"
#                 f"QPushButton::disabled{{background-color:{Theme.COLOR_FORBIDDEN_BG.value};}}"
#             )
#             btn.setCursor(Qt.CursorShape.PointingHandCursor)

#         for item_key, (full_val, cut_val) in libraries:
#             button = QPushButton(text=cut_val)
#             button.setObjectName(f"path{item_key}")

#             lib = Path(full_val)
#             if not lib.exists() or not (lib / TS_FOLDER_NAME).exists():
#                 button.setDisabled(True)
#                 Translations.translate_with_setter(button.setToolTip, "library.missing")

#             def open_library_button_clicked(path):
#                 return lambda: self.driver.open_library(Path(path))

#             button.clicked.connect(open_library_button_clicked(full_val))
#             set_button_style(button, ["padding-left: 6px;", "text-align: left;"])
#             button_remove = QPushButton("—")
#             button_remove.setCursor(Qt.CursorShape.PointingHandCursor)
#             button_remove.setFixedWidth(24)
#             set_button_style(button_remove, ["font-weight:bold;", "text-align:center;"])

#             def remove_recent_library_clicked(key: str):
#                 return lambda: (
#                     self.driver.remove_recent_library(key),
#                     self.fill_libs_widget(self.libs_layout),
#                 )

#             button_remove.clicked.connect(remove_recent_library_clicked(item_key))

#             row_layout = QHBoxLayout()
#             row_layout.addWidget(button)
#             row_layout.addWidget(button_remove)

#             layout.addLayout(row_layout)
