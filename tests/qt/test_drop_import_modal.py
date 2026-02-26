from pathlib import Path
from unittest.mock import Mock, patch

from PySide6.QtCore import QUrl
from pytestqt.qtbot import QtBot

from tagstudio.qt.mixed.drop_import_modal import DropImportModal
from tagstudio.qt.ts_qt import QtDriver


# /**
#  * Negative test: save_web_file should reject non-file browser URLs.
#  * Test case: HTTP URL with Content-Disposition that is not attachment/inline.
#  * Expected: None is returned and no temporary directory is created.
#  */
def test_save_web_file_non_downloadable_content_disposition_returns_none(
	qtbot: QtBot, qt_driver: QtDriver
):
	modal = DropImportModal(qt_driver)
	qtbot.addWidget(modal)
	modal.temp_dirs = []

	response = Mock()
	response.ok = True
	response.headers = {
		"Content-Disposition": "form-data; name=payload",
		"Content-Type": "text/html",
	}

	request_cm = Mock()
	request_cm.__enter__ = Mock(return_value=response)
	request_cm.__exit__ = Mock(return_value=None)

	with patch("tagstudio.qt.mixed.drop_import_modal.requests.get", return_value=request_cm):
		result = modal.save_web_file(QUrl("https://example.com/some-page"))

	assert result is None
	assert modal.temp_dirs == []


# /**
#  * Positive test: save_web_file should download browser files into a temporary folder.
#  * Test case: HTTP URL with Content-Disposition attachment and filename.
#  * Expected: Downloaded file path is inside a created temp directory and content is written.
#  */
def test_save_web_file_attachment_downloads_to_temp_directory(
	qtbot: QtBot, qt_driver: QtDriver
):
	modal = DropImportModal(qt_driver)
	qtbot.addWidget(modal)
	modal.temp_dirs = []

	response = Mock()
	response.ok = True
	response.headers = {
		"Content-Disposition": 'attachment; filename="browser-file.txt"',
		"Content-Type": "text/plain",
	}
	response.iter_content = Mock(return_value=[b"hello", b" world"])

	request_cm = Mock()
	request_cm.__enter__ = Mock(return_value=response)
	request_cm.__exit__ = Mock(return_value=None)

	with patch("tagstudio.qt.mixed.drop_import_modal.requests.get", return_value=request_cm):
		result = modal.save_web_file(QUrl("https://example.com/file.txt"))

	assert result is not None
	assert result.exists()
	assert result.read_bytes() == b"hello world"
	assert len(modal.temp_dirs) == 1
	assert result.parent == Path(modal.temp_dirs[0].name)

	modal.cleanup_temp_dirs()
	assert not result.exists()
