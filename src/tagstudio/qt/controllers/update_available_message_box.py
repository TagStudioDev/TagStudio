# SPDX-FileCopyrightText: (c) TagStudio Contributors
# SPDX-License-Identifier: GPL-3.0-only


import math
from functools import partial

import structlog
from PIL import ImageQt
from PySide6.QtCore import Qt
from PySide6.QtGui import QDesktopServices, QPixmap
from PySide6.QtWidgets import QMessageBox

from tagstudio.core.constants import GITHUB_RELEASE_URL, VERSION
from tagstudio.core.ts_core import TagStudioCore
from tagstudio.core.utils.types import unwrap
from tagstudio.qt.models.palette import ColorType, UiColor, get_ui_color
from tagstudio.qt.resource_manager import ResourceManager
from tagstudio.qt.translations import Translations

logger = structlog.get_logger(__name__)


class UpdateAvailableMessageBox(QMessageBox):
    """A warning dialog for if the TagStudio is not running under the latest release version."""

    def __init__(self):
        super().__init__()

        rm = ResourceManager()
        title = Translations["version_modal.title"]
        self.setWindowTitle(title)
        pixel_ratio = self.devicePixelRatio()
        icon = QPixmap.fromImage(ImageQt.ImageQt(rm.icon)).scaled(
            math.floor(48 * pixel_ratio),
            math.floor(48 * pixel_ratio),
            Qt.AspectRatioMode.IgnoreAspectRatio,
            Qt.TransformationMode.SmoothTransformation,
        )
        icon.setDevicePixelRatio(pixel_ratio)
        self.setIconPixmap(icon)
        self.setWindowModality(Qt.WindowModality.ApplicationModal)
        self.setStyleSheet("QPushButton {padding: 3px 8px;}")

        self.setStandardButtons(
            QMessageBox.StandardButton.Close
            | QMessageBox.StandardButton.Ignore
            | QMessageBox.StandardButton.Ok
        )
        self.setDefaultButton(QMessageBox.StandardButton.Ok)
        self.button(QMessageBox.StandardButton.Ok).setText(Translations["update.view_update"])
        self.button(QMessageBox.StandardButton.Ok).clicked.connect(
            partial(QDesktopServices.openUrl, GITHUB_RELEASE_URL)
        )
        self.button(QMessageBox.StandardButton.Ignore).setText(Translations["generic.dont_remind"])

        red = get_ui_color(ColorType.PRIMARY, UiColor.RED)
        green = get_ui_color(ColorType.PRIMARY, UiColor.GREEN)
        latest_release_version = unwrap(TagStudioCore.get_most_recent_release_version())
        status = Translations.format(
            "version_modal.status",
            installed_version=f"<span style='color:{red}'>{VERSION}</span>",
            latest_release_version=f"<span style='color:{green}'>{latest_release_version}</span>",
        )
        description = Translations.format(
            "version_modal.description", github_url=GITHUB_RELEASE_URL
        )
        self.setText(f"{description}<br><br>{status}")
