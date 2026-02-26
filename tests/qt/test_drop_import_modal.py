import pytest
from unittest.mock import patch, MagicMock
from PySide6.QtCore import QUrl

from tagstudio.qt.mixed.drop_import_modal import DropImportModal
from tagstudio.qt.ts_qt import QtDriver


@pytest.mark.parametrize(
    "url, response_ok, status_code",
    [
        ("https://fakeurl.com/image.jpg", False, 404),
        ("https://fakeurl.com/file.png", False, 500),
    ],
)
def test_save_web_file_failed_download_returns_none(qtbot, qt_driver: QtDriver, url, response_ok, status_code):
    """
    Tests that DropImportModal.save_web_file() returns None when the download fails (e.g when response.ok is False)
    """

    with patch.object(DropImportModal, "show", lambda self: None): # Dissingage GUI
        modal = DropImportModal(qt_driver)
        qtbot.addWidget(modal)

        fake_response = MagicMock()
        fake_response.ok = response_ok
        fake_response.status_code = status_code

        with patch("tagstudio.qt.mixed.drop_import_modal.requests.get") as mock_get:
            mock_get.return_value.__enter__.return_value = fake_response

            assert modal.save_web_file(QUrl(url)) is None