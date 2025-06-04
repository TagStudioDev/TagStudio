from collections.abc import Callable
from datetime import datetime as dt
from typing import cast

from PySide6.QtCore import QDateTime, QLocale
from PySide6.QtWidgets import QDateTimeEdit, QVBoxLayout

from tagstudio.qt.widgets.panel import PanelWidget

DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S"


class DatetimePicker(PanelWidget):
    def __init__(self, datetime: dt | str):
        super().__init__()
        self.root_layout = QVBoxLayout(self)
        self.root_layout.setContentsMargins(6, 0, 6, 0)

        if isinstance(datetime, str):
            datetime = DatetimePicker.string2dt(datetime)
        self.datetime_edit = QDateTimeEdit()
        self.datetime_edit.setCalendarPopup(True)
        self.datetime_edit.setDateTime(DatetimePicker.dt2qdt(datetime))
        # sketchy way to show seconds without showing the day of the week;
        # while also still having localisation
        self.datetime_edit.setDisplayFormat(
            QLocale.system()
            .dateTimeFormat(QLocale.FormatType.ShortFormat)
            .replace("HH:mm", "HH:mm:ss")
        )

        self.initial_value = datetime
        self.root_layout.addWidget(self.datetime_edit)

    def get_content(self):
        return DatetimePicker.dt2string(DatetimePicker.qdt2dt(self.datetime_edit.dateTime()))

    def reset(self):
        self.datetime_edit.setDateTime(DatetimePicker.dt2qdt(self.initial_value))

    def add_callback(self, callback: Callable, event: str = "returnPressed"):
        if event == "returnPressed":
            pass
        else:
            raise ValueError(f"unknown event type: {event}")

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
