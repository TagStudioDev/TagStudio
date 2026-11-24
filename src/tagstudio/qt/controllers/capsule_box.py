# SPDX-FileCopyrightText: (c) TagStudio Contributors
# SPDX-License-Identifier: GPL-3.0-only


from typing import override

from PySide6.QtWidgets import QWidget

from tagstudio.qt.controllers.capsule import Capsule
from tagstudio.qt.views.capsule_box_view import CapsuleBoxView


class CapsuleBox(QWidget):
    """Capsules in a flow layout inside a scrolling inset frame."""

    def __init__(self) -> None:
        super().__init__()
        self._capsules: list[Capsule] = []
        self._are_capsules_clickable = True
        self.setLayout(CapsuleBoxView())

    @override
    def layout(self) -> CapsuleBoxView:
        layout = super().layout()
        assert isinstance(layout, CapsuleBoxView)
        return layout

    def set_capsules(self, capsules: list[Capsule]) -> None:
        """Set the shown capsules."""
        view = self.layout()
        for capsule in self._capsules:
            view.capsule_layout.removeWidget(capsule)
            capsule.hide()
            capsule.deleteLater()

        self._capsules = capsules
        for capsule in capsules:
            capsule.set_clickable(self._are_capsules_clickable)
            view.capsule_layout.addWidget(capsule)
            capsule.show()

    def set_capsules_clickable(self, clickable: bool) -> None:
        self._are_capsules_clickable = clickable
        for capsule in self._capsules:
            capsule.set_clickable(clickable)
