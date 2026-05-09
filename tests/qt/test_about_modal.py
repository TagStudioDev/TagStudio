from pytestqt.qtbot import QtBot

from tagstudio.qt.mixed.about_modal import AboutModal


def test_github_api_unavailable(qtbot: QtBot, mocker) -> None:
    mocker.patch(
        "requests.get",
        side_effect=ConnectionError(
            "Failed to resolve 'api.github.com' ([Errno -3] Temporary failure in name resolution)"
        ),
    )
    modal = AboutModal("/tmp")
    qtbot.addWidget(modal)
