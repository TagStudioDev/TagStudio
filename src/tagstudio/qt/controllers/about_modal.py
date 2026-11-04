# SPDX-FileCopyrightText: (c) TagStudio Contributors
# SPDX-License-Identifier: GPL-3.0-only


from functools import partial
from pathlib import Path
from typing import override

from PySide6.QtCore import QEvent, Qt

from tagstudio.core.constants import VERSION
from tagstudio.core.ts_core import TagStudioCore
from tagstudio.core.utils.ffmpeg_status import FfmpegStatus, FfprobeStatus
from tagstudio.core.utils.ripgrep_status import RipgrepStatus
from tagstudio.core.utils.str_formatting import is_version_outdated
from tagstudio.core.utils.types import unwrap
from tagstudio.i18n.translations import Translations
from tagstudio.qt.controllers.modal_content import ModalContent
from tagstudio.qt.utils.file_opener import open_file
from tagstudio.qt.views.about_modal_view import AboutModalView
from tagstudio.qt.views.styles.palette import ColorType, UiColor, get_ui_color

_WINDOW_WIDTH = 600


class AboutModal(ModalContent):
    """Modal window showing information about TagStudio."""

    def __init__(self, config_path: Path | str) -> None:
        super().__init__()
        self.setLayout(AboutModalView())
        view = self.layout()

        red = get_ui_color(ColorType.PRIMARY, UiColor.RED)
        green = get_ui_color(ColorType.PRIMARY, UiColor.GREEN)
        amber = get_ui_color(ColorType.PRIMARY, UiColor.AMBER)

        # TagStudio Version
        latest_ts_version = unwrap(TagStudioCore.get_most_recent_release_version(), "0.0.0")
        if not is_version_outdated(VERSION, latest_ts_version):
            view.version_content.setText(f"{VERSION}")
        else:
            view.version_content.setText(
                Translations.format(
                    "about.version.latest", built_version=VERSION, latest_version=latest_ts_version
                )
            )

        # Config Path
        view.config_path_content.setText(f"{config_path}")
        view.config_path_content.clicked.connect(lambda: open_file(config_path, file_manager=True))

        missing = Translations["generic.missing"]
        found = Translations["about.module.found"]
        for content, version, location, missing_color in (
            (view.ffmpeg_path_content, FfmpegStatus.version(), FfmpegStatus.which(), red),
            (view.ffprobe_path_content, FfprobeStatus.version(), FfprobeStatus.which(), red),
            (view.ripgrep_path_content, RipgrepStatus.version(), RipgrepStatus.which(), amber),
        ):
            status = f'<span style="color:{missing_color}">{missing}</span>'
            if version is not None:
                status = f'<span style="color:{green}">{found}</span> (' + version + ")"
            content.setText(status)
            if location:
                content.clicked.connect(partial(open_file, location, file_manager=True))
                content.setCursor(Qt.CursorShape.PointingHandCursor)
                content.setToolTip(location)

    @override
    def changeEvent(self, event: QEvent) -> None:
        if event.type() == QEvent.Type.ThemeChange:
            self.layout().set_label_colors()
        super().changeEvent(event)

    @override
    def parent_post_init(self) -> None:
        window = self.window()
        window.resize(_WINDOW_WIDTH, window.sizeHint().height())
        unwrap(self.done_button).setText(Translations["generic.close"])

    @override
    def layout(self) -> AboutModalView:
        layout = super().layout()
        assert isinstance(layout, AboutModalView)
        return layout
