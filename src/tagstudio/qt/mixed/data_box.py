# SPDX-FileCopyrightText: (c) TagStudio Contributors
# SPDX-License-Identifier: GPL-3.0-only


import structlog
from PySide6.QtWidgets import QWidget

logger = structlog.get_logger(__name__)


class DataBox(QWidget):
    def __init__(self, title: str) -> None:
        super().__init__()
        self.title: str = title
