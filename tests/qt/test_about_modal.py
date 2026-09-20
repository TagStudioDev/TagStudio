# SPDX-FileCopyrightText: (c) TagStudio Contributors
# SPDX-License-Identifier: GPL-3.0-only


from pytestqt.qtbot import QtBot

from tagstudio.qt.mixed.about_modal import AboutModal


def test_github_api_unavailable(qtbot: QtBot, mocker) -> None:
    mocker.patch(
        "requests.get",
        side_effect=ConnectionError(
            "Emulating a failure with 'api.github.com' ([Errno 0] This should be handled)"
        ),
    )
    modal = AboutModal("/tmp")
    qtbot.addWidget(modal)
