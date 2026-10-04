# SPDX-FileCopyrightText: (c) TagStudio Contributors
# SPDX-License-Identifier: GPL-3.0-only


from tagstudio.qt.views.layouts.flow_layout import FlowLayout


class ColorDataView(FlowLayout):
    """The layout used for a ColorData widget."""

    def __init__(self) -> None:
        super().__init__()
        self.enable_grid_optimizations(value=True)
        self.setContentsMargins(0, 0, 0, 0)
