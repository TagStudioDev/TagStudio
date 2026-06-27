# SPDX-FileCopyrightText: (c) TagStudio Contributors
# SPDX-License-Identifier: GPL-3.0-only


import typing
from datetime import datetime as dt
from typing import cast, override

from PySide6.QtCore import QDateTime
from PySide6.QtWidgets import QDateTimeEdit, QLineEdit, QVBoxLayout

from tagstudio.qt.views.panel_modal import PanelWidget
from tagstudio.qt.views.stylesheets.stylesheets import title_line_edit_style

if typing.TYPE_CHECKING:
    from tagstudio.qt.ts_qt import QtDriver

DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S"


QDTF2DTF = {
    "%d": "dd",
    "%m": "MM",
    "%y": "yy",
    "%H": "HH",
    "%M": "mm",
    "%S": "ss",
    "%Y": "yyyy",
    "%I": "hh",
    "%p": "AP",
    "%x": "MM/dd/yy",
}


def qdtf2dtf(dtf: str) -> str:
    out = dtf
    for old, new in QDTF2DTF.items():
        out = out.replace(old, new)
    return out


class DatetimePicker(PanelWidget):
    def __init__(self, driver: "QtDriver", name: str, datetime: dt | str):
        super().__init__()
        self.setMinimumSize(300, 60)
        self.root_layout = QVBoxLayout(self)
        self.root_layout.setContentsMargins(6, 0, 6, 0)

        self.name_field = QLineEdit()
        self.name_field.setStyleSheet(title_line_edit_style())
        self.name_field.setText(name)

        if isinstance(datetime, str):
            datetime = DatetimePicker.string2dt(datetime)
        self.datetime_edit = QDateTimeEdit()
        self.datetime_edit.setCalendarPopup(True)
        self.datetime_edit.setDateTime(DatetimePicker.dt2qdt(datetime))
        # sketchy way to show seconds without showing the day of the week;
        # while also still having localisation
        self.datetime_edit.setDisplayFormat(qdtf2dtf(driver.settings.datetime_format))

        self.initial_value = datetime
        self.root_layout.addWidget(self.name_field)
        self.root_layout.addWidget(self.datetime_edit)

    @override
    def saved_data(self) -> dict[str, str]:
        return {
            "name": self.name_field.text(),
            "value": DatetimePicker.dt2string(DatetimePicker.qdt2dt(self.datetime_edit.dateTime())),
        }

    @override
    def parent_post_init(self):
        self.datetime_edit.setFocus()

    @override
    def reset(self):
        self.datetime_edit.setDateTime(DatetimePicker.dt2qdt(self.initial_value))

    @staticmethod
    def qdt2dt(qdt: QDateTime) -> dt:
        return cast(dt, qdt.toPython())

    @staticmethod
    def dt2qdt(datetime: dt) -> QDateTime:
        return QDateTime.fromSecsSinceEpoch(int(datetime.timestamp()))

    @staticmethod
    def string2dt(datetime_str: str) -> dt:
        return dt.strptime(datetime_str, DATETIME_FORMAT)

    @staticmethod
    def dt2string(datetime: dt) -> str:
        return dt.strftime(datetime, DATETIME_FORMAT)
