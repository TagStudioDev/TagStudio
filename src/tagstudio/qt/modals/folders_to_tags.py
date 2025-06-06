# Copyright (C) 2025
# Licensed under the GPL-3.0 License.
# Created for TagStudio: https://github.com/CyanVoxel/TagStudio


import math
from collections.abc import Sequence
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, override

import structlog
from PySide6 import QtCore, QtGui
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from tagstudio.core.constants import TAG_ARCHIVED, TAG_FAVORITE
from tagstudio.core.library.alchemy.enums import TagColorEnum
from tagstudio.core.library.alchemy.library import Library
from tagstudio.core.library.alchemy.models import Tag
from tagstudio.core.palette import ColorType, get_tag_color
from tagstudio.qt.flowlayout import FlowLayout
from tagstudio.qt.translations import Translations

if TYPE_CHECKING:
    from tagstudio.qt.ts_qt import QtDriver

logger = structlog.get_logger(__name__)


@dataclass
class BranchData:
    dirs: dict[str, "BranchData"] = field(default_factory=dict)
    files: list[str] = field(default_factory=list)
    tag: Tag | None = None


def add_folders_to_tree(library: Library, tree: BranchData, items: tuple[str, ...]) -> BranchData:
    branch = tree
    parent_tag = None
    for folder in items:
        if folder not in branch.dirs:
            new_tag = Tag(name=folder, parent_tags=({parent_tag} if parent_tag else None))
            library.add_tag(new_tag)
            branch.dirs[folder] = BranchData(tag=new_tag)
        branch = branch.dirs[folder]
        parent_tag = branch.tag
    return branch


def folders_to_tags(library: Library):
    logger.info("Converting folders to Tags")
    tree = BranchData()

    def add_tag_to_tree(items: list[Tag]):
        branch = tree
        for tag in items:
            if tag.name not in branch.dirs:
                branch.dirs[tag.name] = BranchData()
            branch = branch.dirs[tag.name]

    for tag in library.tags:
        reversed_tag = reverse_tag(library, tag, None)
        add_tag_to_tree(reversed_tag)

    for entry in library.get_entries():
        folders = entry.path.parts[0:-1]
        if not folders:
            continue

        tag = add_folders_to_tree(library, tree, folders).tag
        if tag and not entry.has_tag(tag):
            library.add_tags_to_entries(entry.id, tag.id)

    logger.info("Done")


def reverse_tag(library: Library, tag: Tag, items: list[Tag] | None) -> list[Tag]:
    items = items or []
    items.append(tag)

    if not tag.parent_ids:
        items.reverse()
        return items

    for subtag_id in tag.parent_ids:
        subtag = library.get_tag(subtag_id)
    return reverse_tag(library, subtag, items)


# =========== UI ===========


def generate_preview_data(library: Library) -> BranchData:
    tree = BranchData()

    def add_tag_to_tree(items: list[Tag]):
        branch = tree
        for tag in items:
            if tag.name not in branch.dirs:
                branch.dirs[tag.name] = BranchData(tag=tag)
            branch = branch.dirs[tag.name]

    def _add_folders_to_tree(items: Sequence[str]) -> BranchData:
        branch = tree
        for folder in items:
            if folder not in branch.dirs:
                new_tag = Tag(name=folder)
                branch.dirs[folder] = BranchData(tag=new_tag)
            branch = branch.dirs[folder]
        return branch

    for tag in library.tags:
        if tag.id in (TAG_FAVORITE, TAG_ARCHIVED):
            continue
        reversed_tag = reverse_tag(library, tag, None)
        add_tag_to_tree(reversed_tag)

    for entry in library.get_entries():
        folders = entry.path.parts[0:-1]
        if not folders:
            continue

        branch = _add_folders_to_tree(folders)
        if branch:
            has_tag = False
            for tag in entry.tags:
                if tag.name == branch.tag.name:
                    has_tag = True
                    break
            if not has_tag:
                branch.files.append(entry.path.name)

    def cut_branches_adding_nothing(branch: BranchData) -> bool:
        folders = list(branch.dirs.keys())
        for folder in folders:
            cut = cut_branches_adding_nothing(branch.dirs[folder])
            if cut:
                branch.dirs.pop(folder)

        if not branch.tag:
            return False

        if not branch.tag.id:
            return False

        if branch.files:
            return False

        return not bool(branch.dirs)

    cut_branches_adding_nothing(tree)
    return tree


class FoldersToTagsModal(QWidget):
    def __init__(self, library: "Library", driver: "QtDriver"):
        super().__init__()
        self.library = library
        self.driver = driver
        self.count = -1
        self.filename = ""

        self.setWindowTitle(Translations["folders_to_tags.title"])
        self.setWindowModality(Qt.WindowModality.ApplicationModal)
        self.setMinimumSize(640, 640)
        self.root_layout = QVBoxLayout(self)
        self.root_layout.setContentsMargins(6, 6, 6, 6)

        self.title_widget = QLabel(Translations["folders_to_tags.title"])
        self.title_widget.setObjectName("title")
        self.title_widget.setWordWrap(True)
        self.title_widget.setStyleSheet("font-weight:bold;font-size:14px;padding-top: 6px")
        self.title_widget.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.desc_widget = QLabel()
        self.desc_widget.setObjectName("descriptionLabel")
        self.desc_widget.setWordWrap(True)
        self.desc_widget.setText(
            """Creates tags based on your folder structure and applies them to your entries.
            This tree shows all tags to be created and which entries they will be applied to."""
        )
        self.desc_widget.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.open_close_button_w = QWidget()
        self.open_close_button_layout = QHBoxLayout(self.open_close_button_w)

        self.open_all_button = QPushButton(Translations["folders_to_tags.open_all"])
        self.open_all_button.clicked.connect(lambda: self.set_all_branches(False))
        self.close_all_button = QPushButton(Translations["folders_to_tags.close_all"])
        self.close_all_button.clicked.connect(lambda: self.set_all_branches(True))

        self.open_close_button_layout.addWidget(self.open_all_button)
        self.open_close_button_layout.addWidget(self.close_all_button)

        self.scroll_contents = QWidget()
        self.scroll_layout = QVBoxLayout(self.scroll_contents)
        self.scroll_layout.setContentsMargins(6, 0, 6, 0)
        self.scroll_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        self.scroll_area = QScrollArea()
        self.scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOn)
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setFrameShadow(QFrame.Shadow.Plain)
        self.scroll_area.setFrameShape(QFrame.Shape.NoFrame)
        self.scroll_area.setWidget(self.scroll_contents)

        self.apply_button = QPushButton(Translations["generic.apply_alt"])
        self.apply_button.setMinimumWidth(100)
        self.apply_button.clicked.connect(self.on_apply)

        self.showEvent = self.on_open  # type: ignore

        self.root_layout.addWidget(self.title_widget)
        self.root_layout.addWidget(self.desc_widget)
        self.root_layout.addWidget(self.open_close_button_w)
        self.root_layout.addWidget(self.scroll_area)
        self.root_layout.addWidget(self.apply_button, alignment=Qt.AlignmentFlag.AlignCenter)

    def on_apply(self, event):
        folders_to_tags(self.library)
        self.close()
        self.driver.main_window.preview_panel.update_widgets(update_preview=False)

    def on_open(self, event):
        for i in reversed(range(self.scroll_layout.count())):
            self.scroll_layout.itemAt(i).widget().setParent(None)

        data = generate_preview_data(self.library)

        for folder in data.dirs.values():
            test = TreeItem(folder)
            self.scroll_layout.addWidget(test)

    def set_all_branches(self, hidden: bool):
        for i in reversed(range(self.scroll_layout.count())):
            child = self.scroll_layout.itemAt(i).widget()
            if isinstance(child, TreeItem):
                child.set_all_branches(hidden)

    @override
    def keyPressEvent(self, event: QtGui.QKeyEvent) -> None:  # noqa N802
        if event.key() == QtCore.Qt.Key.Key_Escape:
            self.close()
        else:  # Other key presses
            pass
        return super().keyPressEvent(event)


class TreeItem(QWidget):
    def __init__(self, data: BranchData, parent_tag: Tag | None = None):
        super().__init__()

        self.setStyleSheet("QLabel{font-size: 13px}")

        self.root_layout = QVBoxLayout(self)
        self.root_layout.setContentsMargins(20, 0, 0, 0)
        self.root_layout.setSpacing(1)

        self.test = QWidget()
        self.root_layout.addWidget(self.test)

        self.tag_layout = FlowLayout(self.test)

        self.label = QLabel()
        self.tag_layout.addWidget(self.label)
        self.tag_widget = ModifiedTagWidget(data.tag, parent_tag)
        self.tag_widget.bg_button.clicked.connect(lambda: self.hide_show())
        self.tag_layout.addWidget(self.tag_widget)

        self.children_widget = QWidget()
        self.children_layout = QVBoxLayout(self.children_widget)
        self.root_layout.addWidget(self.children_widget)

        self.populate(data)

    def hide_show(self):
        self.children_widget.setHidden(not self.children_widget.isHidden())
        self.label.setText(">" if self.children_widget.isHidden() else "v")

    def populate(self, data: BranchData):
        for folder in data.dirs.values():
            item = TreeItem(folder, data.tag)
            self.children_layout.addWidget(item)
        for file in data.files:
            label = QLabel()
            label.setText("    ->  " + str(file))
            self.children_layout.addWidget(label)

        if data.files or data.dirs:
            self.label.setText("v")
        else:
            self.hide_show()

    def set_all_branches(self, hidden: bool):
        for i in reversed(range(self.children_layout.count())):
            child = self.children_layout.itemAt(i).widget()
            if isinstance(child, TreeItem):
                child.set_all_branches(hidden)

        self.children_widget.setHidden(hidden)
        self.label.setText(">" if self.children_widget.isHidden() else "v")


class ModifiedTagWidget(QWidget):
    """Modified TagWidget that does not search for the Tag's display name in the Library."""

    def __init__(self, tag: Tag, parent_tag: Tag) -> None:
        super().__init__()
        self.tag = tag

        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.base_layout = QVBoxLayout(self)
        self.base_layout.setObjectName("baseLayout")
        self.base_layout.setContentsMargins(0, 0, 0, 0)

        self.bg_button = QPushButton(self)
        self.bg_button.setFlat(True)
        if parent_tag is not None:
            text = f"{tag.name} ({parent_tag.name})".replace("&", "&&")
        else:
            text = tag.name.replace("&", "&&")
        self.bg_button.setText(text)
        self.bg_button.setContextMenuPolicy(Qt.ContextMenuPolicy.ActionsContextMenu)

        self.inner_layout = QHBoxLayout()
        self.inner_layout.setObjectName("innerLayout")
        self.inner_layout.setContentsMargins(2, 2, 2, 2)
        self.bg_button.setLayout(self.inner_layout)
        self.bg_button.setMinimumSize(math.ceil(22 * 1.5), 22)

        self.bg_button.setStyleSheet(
            f"QPushButton{{"
            f"background: {get_tag_color(ColorType.PRIMARY, TagColorEnum.DEFAULT)};"
            f"color: {get_tag_color(ColorType.TEXT, TagColorEnum.DEFAULT)};"
            f"font-weight: 600;"
            f"border-color:{get_tag_color(ColorType.BORDER, TagColorEnum.DEFAULT)};"
            f"border-radius: 6px;"
            f"border-style:inset;"
            f"border-width: {math.ceil(self.devicePixelRatio())}px;"
            f"padding-right: 4px;"
            f"padding-bottom: 1px;"
            f"padding-left: 4px;"
            f"font-size: 13px"
            f"}}"
            f"QPushButton::hover{{"
            f"border-color:{get_tag_color(ColorType.LIGHT_ACCENT, TagColorEnum.DEFAULT)};"
            f"}}"
        )

        self.base_layout.addWidget(self.bg_button)
        self.setMinimumSize(50, 20)
