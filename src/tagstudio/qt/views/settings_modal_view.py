# SPDX-FileCopyrightText: (c) TagStudio Contributors
# SPDX-License-Identifier: GPL-3.0-only


from PySide6.QtCore import Qt
from PySide6.QtGui import QDoubleValidator, QIntValidator
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QStackedLayout,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from tagstudio.core.constants import TAG_FAVORITE
from tagstudio.core.library.alchemy import default_color_groups
from tagstudio.core.library.library_settings import (
    MAX_CACHED_THUMB_RES,
    MIN_CACHED_THUMB_RES,
    MIN_THUMB_CACHE_SIZE,
)
from tagstudio.core.utils.types import unwrap
from tagstudio.i18n.translations import Translations
from tagstudio.qt.controllers.badge import Badge
from tagstudio.qt.controllers.capsule import Capsule
from tagstudio.qt.views.styles.stylesheets import HALF_PAD, MED_HEIGHT, PAD, RADIUS
from tagstudio.qt.views.styles.tag_icons import tag_icon
from tagstudio.qt.views.styles.tagstudio_style import set_joined_edges

_LINE_EDIT_WIDTH = 96
_ROW_HEIGHT = 24


def _create_form_layout(page: QWidget) -> QFormLayout:
    """Create the form layout for a settings page."""
    form_layout = QFormLayout(page)
    form_layout.setContentsMargins(PAD, PAD, PAD, PAD)
    form_layout.setFieldGrowthPolicy(QFormLayout.FieldGrowthPolicy.FieldsStayAtSizeHint)
    return form_layout


def _add_row(form_layout: QFormLayout, label: str, field: QWidget) -> None:
    """Add a setting's row to a settings page."""
    field.setFixedHeight(_ROW_HEIGHT)
    form_layout.addRow(label, field)


def _field_with_preview(field: QWidget, preview: QWidget) -> QWidget:
    """Place a preview beside a setting's field."""
    container = QWidget()
    layout = QHBoxLayout(container)
    layout.setContentsMargins(0, 0, 0, 0)
    layout.setSpacing(PAD)
    layout.addWidget(field)
    layout.addWidget(preview)
    return container


class SettingsModalView(QVBoxLayout):
    def __init__(self) -> None:
        super().__init__()
        self.setContentsMargins(0, PAD, 0, 0)

        self.app_mode_button = QPushButton(Translations["settings.application"])
        self.app_mode_button.setFixedHeight(MED_HEIGHT)
        self.app_mode_button.setProperty("radius", RADIUS)
        self.app_mode_button.setMinimumWidth(120)
        self.app_mode_button.setCheckable(True)
        self.app_mode_button.setChecked(True)
        set_joined_edges(self.app_mode_button, Qt.Edge.RightEdge)
        self.library_mode_button = QPushButton(Translations["settings.library"])
        self.library_mode_button.setFixedHeight(MED_HEIGHT)
        self.library_mode_button.setProperty("radius", RADIUS)
        self.library_mode_button.setMinimumWidth(120)
        self.library_mode_button.setCheckable(True)
        set_joined_edges(self.library_mode_button, Qt.Edge.LeftEdge)
        mode_switch = QHBoxLayout()
        mode_switch.setSpacing(0)
        mode_switch.addStretch(1)
        mode_switch.addWidget(self.app_mode_button)
        mode_switch.addWidget(self.library_mode_button)
        mode_switch.addStretch(1)
        self.addLayout(mode_switch)

        # Tabs
        self.app_tab_widget = QTabWidget()
        self.app_tab_widget.addTab(
            self._build_app_general_settings(), Translations["settings.general"]
        )
        self.app_tab_widget.addTab(
            self._build_appearance_settings(), Translations["settings.appearance"]
        )
        self.app_tab_widget.addTab(
            self._build_localization_settings(), Translations["settings.localization"]
        )
        self.app_tab_widget.addTab(
            self._build_inspector_settings(), Translations["settings.inspector"]
        )
        self.app_tab_widget.addTab(
            self._build_search_box_settings(), Translations["settings.suggest_boxes"]
        )

        self.library_tab_widget = QTabWidget()
        self.library_tab_widget.addTab(
            self._build_library_general_settings(), Translations["settings.general"]
        )
        self.library_tab_widget.addTab(
            self._build_thumbnail_settings(), Translations["settings.thumbnails"]
        )

        self.mode_stack = QStackedLayout()
        self.mode_stack.addWidget(self.app_tab_widget)
        self.mode_stack.addWidget(self.library_tab_widget)
        self.addLayout(self.mode_stack)

        # Restart Label
        self.restart_label = QLabel(Translations["settings.restart_required"])
        self.restart_label.setHidden(True)
        self.restart_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.addStretch(1)
        self.addWidget(self.restart_label)

    def _build_app_general_settings(self) -> QWidget:
        page = QWidget()
        form_layout = _create_form_layout(page)

        # Reopen Library on Start
        self.open_last_lib_checkbox = QCheckBox()
        _add_row(
            form_layout, Translations["settings.open_library_on_start"], self.open_last_lib_checkbox
        )

        return page

    def _build_inspector_settings(self) -> QWidget:
        page = QWidget()
        form_layout = _create_form_layout(page)

        # Tag Click Action
        self.tag_click_action_combobox = QComboBox()
        _add_row(
            form_layout,
            Translations["settings.tag_click_action.label"],
            self.tag_click_action_combobox,
        )

        # Autoplay
        self.autoplay_checkbox = QCheckBox()
        _add_row(form_layout, Translations["settings.autoplay"], self.autoplay_checkbox)
        return page

    def _build_search_box_settings(self) -> QWidget:
        page = QWidget()
        form_layout = _create_form_layout(page)

        # Open Edit Window When Creating a Tag
        self.edit_tag_on_create_checkbox = QCheckBox()
        _add_row(
            form_layout,
            Translations["settings.edit_tag_on_create"],
            self.edit_tag_on_create_checkbox,
        )

        # Open Edit Window When Adding a Field
        self.edit_field_on_add_checkbox = QCheckBox()
        _add_row(
            form_layout, Translations["settings.edit_field_on_add"], self.edit_field_on_add_checkbox
        )
        # Keep Tag/Field Suggest Boxes Open After Adding Items
        self.keep_suggest_boxes_open_checkbox = QCheckBox()
        _add_row(
            form_layout,
            Translations["settings.keep_suggest_boxes_open"],
            self.keep_suggest_boxes_open_checkbox,
        )

        # Don't Create New Items on Enter
        self.dont_create_items_on_enter_checkbox = QCheckBox()
        _add_row(
            form_layout,
            Translations["settings.dont_create_items_on_enter"],
            self.dont_create_items_on_enter_checkbox,
        )

        # Sort Added Tags After Other Results in Suggest Box
        self.sort_added_tags_last_checkbox = QCheckBox()
        _add_row(
            form_layout,
            Translations["settings.sort_added_tags_last"],
            self.sort_added_tags_last_checkbox,
        )

        # Invert Suggest Box Scrolling
        self.invert_suggest_box_scroll_checkbox = QCheckBox()
        _add_row(
            form_layout,
            Translations["settings.invert_suggest_box_scroll"],
            self.invert_suggest_box_scroll_checkbox,
        )

        return page

    def _build_appearance_settings(self) -> QWidget:
        page = QWidget()
        form_layout = _create_form_layout(page)
        favorite_icon = unwrap(tag_icon(TAG_FAVORITE))
        yellow = next(c for c in default_color_groups.standard() if c.slug == "yellow")

        # Dark Mode
        self.theme_combobox = QComboBox()
        _add_row(form_layout, Translations["settings.theme.label"], self.theme_combobox)

        # Pill-Shaped Tags
        self.pill_shaped_tags_checkbox = QCheckBox()
        self.example_tag = Capsule(is_tag=True)
        self.example_tag.set_text(Translations["generic.example"])
        self.example_tag.set_icon(favorite_icon)
        self.example_tag.set_color_group(yellow)
        self.example_tag.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        self.example_tag.layout().button.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        _add_row(
            form_layout,
            Translations["settings.pill_shaped_tags"],
            _field_with_preview(self.pill_shaped_tags_checkbox, self.example_tag),
        )

        # Circular Badges
        self.circular_badges_checkbox = QCheckBox()
        self.example_badge = Badge(favorite_icon)
        self.example_badge.set_color_group(yellow)
        self.example_badge.setChecked(True)
        self.example_badge.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        self.example_badge.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        _add_row(
            form_layout,
            Translations["settings.circular_badges"],
            _field_with_preview(self.circular_badges_checkbox, self.example_badge),
        )

        # Show Filepath
        self.filepath_combobox = QComboBox()
        _add_row(form_layout, Translations["settings.filepath.label"], self.filepath_combobox)
        return page

    def _build_localization_settings(self) -> QWidget:
        page = QWidget()
        form_layout = _create_form_layout(page)

        # Language
        self.language_combobox = QComboBox()
        _add_row(form_layout, Translations["settings.language"], self.language_combobox)

        # Date Format
        self.dateformat_combobox = QComboBox()
        _add_row(form_layout, Translations["settings.dateformat.label"], self.dateformat_combobox)

        # 24-Hour Format
        self.hourformat_checkbox = QCheckBox()
        _add_row(form_layout, Translations["settings.hourformat.label"], self.hourformat_checkbox)

        # Zero-padding
        self.zeropadding_checkbox = QCheckBox()
        _add_row(form_layout, Translations["settings.zeropadding.label"], self.zeropadding_checkbox)
        return page

    def _build_library_general_settings(self) -> QWidget:
        page = QWidget()
        form_layout = _create_form_layout(page)

        # Scan for new files when a library is opened
        self.sync_on_open_checkbox = QCheckBox()
        _add_row(
            form_layout, Translations["settings.scan_files_on_open"], self.sync_on_open_checkbox
        )
        return page

    def _build_thumbnail_settings(self) -> QWidget:
        page = QWidget()
        form_layout = _create_form_layout(page)

        # Generate Thumbnails
        self.generate_thumbs = QCheckBox()
        _add_row(form_layout, Translations["settings.generate_thumbs"], self.generate_thumbs)

        # Thumbnail Cache Size
        self.thumb_cache_size_container = QWidget()
        self.thumb_cache_size_layout = QHBoxLayout(self.thumb_cache_size_container)
        self.thumb_cache_size_layout.setContentsMargins(0, 0, 0, 0)
        self.thumb_cache_size_layout.setSpacing(HALF_PAD)
        self.thumb_cache_size = QLineEdit()
        self.thumb_cache_size.setFixedWidth(_LINE_EDIT_WIDTH)
        self.thumb_cache_size.setAlignment(Qt.AlignmentFlag.AlignRight)
        self.thumb_cache_size_validator = QDoubleValidator(MIN_THUMB_CACHE_SIZE, 1_000_000_000, 2)
        self.thumb_cache_size.setValidator(self.thumb_cache_size_validator)
        self.thumb_cache_size_layout.addWidget(self.thumb_cache_size)
        self.thumb_cache_size_layout.setStretch(1, 2)
        self.thumb_cache_size_layout.addWidget(QLabel("MiB"))
        _add_row(
            form_layout,
            Translations["settings.thumb_cache_size.label"],
            self.thumb_cache_size_container,
        )

        # Cached Thumbnail Resolution
        self.cached_thumb_res_container = QWidget()
        self.cached_thumb_res_layout = QHBoxLayout(self.cached_thumb_res_container)
        self.cached_thumb_res_layout.setContentsMargins(0, 0, 0, 0)
        self.cached_thumb_res_layout.setSpacing(HALF_PAD)
        self.cached_thumb_res = QLineEdit()
        self.cached_thumb_res.setFixedWidth(_LINE_EDIT_WIDTH)
        self.cached_thumb_res.setAlignment(Qt.AlignmentFlag.AlignRight)
        self.cached_thumb_res_validator = QIntValidator(MIN_CACHED_THUMB_RES, MAX_CACHED_THUMB_RES)
        self.cached_thumb_res.setValidator(self.cached_thumb_res_validator)
        self.cached_thumb_res_layout.addWidget(self.cached_thumb_res)
        self.cached_thumb_res_layout.setStretch(1, 2)
        self.cached_thumb_res_layout.addWidget(QLabel("px"))
        _add_row(
            form_layout,
            Translations["settings.cached_thumb_resolution.label"],
            self.cached_thumb_res_container,
        )
        return page
