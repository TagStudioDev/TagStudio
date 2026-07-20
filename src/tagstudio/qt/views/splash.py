# SPDX-FileCopyrightText: (c) TagStudio Contributors
# SPDX-License-Identifier: GPL-3.0-only


import math
import random

import structlog
from PySide6.QtCore import QRect, Qt
from PySide6.QtGui import QColor, QFont, QPainter, QPen, QPixmap
from PySide6.QtWidgets import QSplashScreen, QWidget

from tagstudio.core.constants import BUILD_TYPE, COPYRIGHT, COPYRIGHT_COMPACT, VERSION
from tagstudio.qt.global_settings import Splash
from tagstudio.qt.resource_manager import ResourceManager
from tagstudio.qt.translations import Translations

logger = structlog.get_logger(__name__)


class SplashScreen:
    """The custom splash screen widget for TagStudio."""

    VERSION_STR: str = " ".join(
        [
            f"{Translations['about.version']}",
            f"{VERSION} {(' (' + Translations[BUILD_TYPE] + ')') if BUILD_TYPE else ''}",
        ]
    )
    DEFAULT_SPLASH = Splash.AURORA

    def __init__(
        self,
        resource_manager: ResourceManager,
        screen_width: int,
        splash_name: str,
        device_ratio: float = 1,
    ):
        self.rm = resource_manager
        self.screen_width = screen_width
        self.ratio: float = device_ratio
        self.splash_screen: QSplashScreen | None = None
        if not splash_name or splash_name == Splash.DEFAULT:
            self.splash_name: str = SplashScreen.DEFAULT_SPLASH
        elif splash_name == Splash.RANDOM:
            splash_list = list(Splash)
            splash_list.remove(Splash.DEFAULT)
            splash_list.remove(Splash.RANDOM)
            self.splash_name = random.choice(splash_list)
        else:
            self.splash_name = splash_name

    def get_pixmap(self) -> QPixmap:
        """Get the pixmap used for the splash screen."""
        pixmap = self.rm.get(f"splash_{self.splash_name}")
        assert isinstance(pixmap, QPixmap)
        if not pixmap:
            logger.error("[Splash] Splash screen not found:", splash_name=self.splash_name)
            pixmap = QPixmap(960, 540)
            pixmap.fill(QColor("black"))
        painter = QPainter(pixmap)
        point_size_scale: float = 1.0
        match painter.font().family():
            case "Segoe UI":
                point_size_scale = 0.75
            case _:
                pass

        # TODO: Store any differing data elsewhere and load dynamically instead of hardcoding.
        match self.splash_name:
            case Splash.CLASSIC:
                # Copyright
                font = painter.font()
                font.setPointSize(math.floor(22 * point_size_scale))
                painter.setFont(font)
                pen = QPen(QColor("#809782ff"))
                painter.setPen(pen)
                painter.drawText(
                    QRect(0, -25, 960, 540),
                    int(Qt.AlignmentFlag.AlignBottom | Qt.AlignmentFlag.AlignHCenter),
                    COPYRIGHT,
                )
                # Version
                pen = QPen(QColor("#9782ff"))
                painter.setPen(pen)
                painter.drawText(
                    QRect(0, -50, 960, 540),
                    int(Qt.AlignmentFlag.AlignBottom | Qt.AlignmentFlag.AlignHCenter),
                    SplashScreen.VERSION_STR,
                )

            case Splash.GOO_GEARS:
                # Copyright
                font = painter.font()
                font.setPointSize(math.floor(22 * point_size_scale))
                painter.setFont(font)
                pen = QPen(QColor("#809782ff"))
                painter.setPen(pen)
                painter.drawText(
                    QRect(40, 450, 960, 540),
                    COPYRIGHT_COMPACT,
                )
                # Version
                font = painter.font()
                font.setPointSize(math.floor(22 * point_size_scale))
                painter.setFont(font)
                pen = QPen(QColor("#9782ff"))
                painter.setPen(pen)
                painter.drawText(
                    QRect(40, 420, 960, 540),
                    SplashScreen.VERSION_STR,
                )

            case Splash.NINETY_FIVE:
                # Copyright
                font = QFont()
                font.setFamily("Times")
                font.setPointSize(math.floor(22 * point_size_scale))
                font.setWeight(QFont.Weight.DemiBold)
                font.setStyleHint(QFont.StyleHint.Serif)
                painter.setFont(font)
                pen = QPen(QColor("#000000"))
                painter.setPen(pen)
                painter.drawText(
                    QRect(88, -25, 960, 540),
                    int(Qt.AlignmentFlag.AlignBottom | Qt.AlignmentFlag.AlignLeft),
                    COPYRIGHT,
                )
                # Version
                font.setPointSize(math.floor(22 * point_size_scale))
                painter.setFont(font)
                pen = QPen(QColor("#AA2A0044"))
                painter.setPen(pen)
                painter.drawText(
                    QRect(-30, 25, 960, 540),
                    int(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignRight),
                    SplashScreen.VERSION_STR,
                )

            case Splash.AURORA:
                # Copyright
                font = painter.font()
                font.setPointSize(math.floor(22 * point_size_scale))
                painter.setFont(font)
                pen = QPen(QColor("#907758FF"))
                painter.setPen(pen)
                painter.drawText(
                    QRect(0, -25, 960, 540),
                    int(Qt.AlignmentFlag.AlignBottom | Qt.AlignmentFlag.AlignHCenter),
                    COPYRIGHT,
                )
                # Version
                pen = QPen(QColor("#7758FF"))
                painter.setPen(pen)
                painter.drawText(
                    QRect(0, -50, 960, 540),
                    int(Qt.AlignmentFlag.AlignBottom | Qt.AlignmentFlag.AlignHCenter),
                    SplashScreen.VERSION_STR,
                )

            case _:
                pass

        pixmap.setDevicePixelRatio(self.ratio)
        pixmap = pixmap.scaledToWidth(
            math.floor(min((self.screen_width * self.ratio) / 4, pixmap.width())),  # pyright: ignore[reportCallIssue]
            Qt.TransformationMode.SmoothTransformation,
        )

        return pixmap

    def _build_splash_screen(self):
        """Build the internal splash screen."""
        self.splash_screen = QSplashScreen(self.get_pixmap(), Qt.WindowType.WindowStaysOnTopHint)

    def show(self):
        """Show the splash screen."""
        if not self.splash_screen:
            self._build_splash_screen()
        if self.splash_screen:
            self.splash_screen.show()

    def finish(self, widget: QWidget):
        """Hide the splash screen with this widget is finished displaying."""
        if self.splash_screen:
            self.splash_screen.finish(widget)
