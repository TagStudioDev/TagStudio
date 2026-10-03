# SPDX-FileCopyrightText: (c) TagStudio Contributors
# SPDX-License-Identifier: GPL-3.0-only


from PySide6.QtWidgets import QLayout, QVBoxLayout


class BannerStackView(QVBoxLayout):
    def __init__(self) -> None:
        super().__init__()
        self.setContentsMargins(0, 0, 0, 0)
        self.setSpacing(0)
        self.setSizeConstraint(QLayout.SizeConstraint.SetMinAndMaxSize)
